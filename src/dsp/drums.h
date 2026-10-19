/* drums.h — il kit di batteria (specifica 10, ACC-212; 20, SND-535 e SND-537; QA-SND-30).
 *
 * Due strade per ogni strumento: un campione del kit scelto (un set del banco di campioni, §7b: la
 * zona ha per nota l'id dello strumento) oppure, se il kit non lo ha o non c'è nessun kit, la sintesi
 * in stile CR-78 (il kit «Chip»). Cassa, rullante, charleston chiuso e aperto, battimani, rimshot,
 * tom bassi e alti, campanaccio, maracas, conga, piatto, e i due clic del metronomo. Rende un bus
 * stereo che il chiamante passa a dsp_render16 (drum_L, drum_R). C11 puro, niente heap.
 *
 * Sul bus, prima dell'uscita, l'FX della drum machine (40 MIDI-135, 20 SND-538): un drive sovracampionato
 * 2× e un filtro a variabili di stato, passa-basso a sinistra e passa-alto a destra. I clic del
 * metronomo non ci passano. Spento (drive 0 e filtro 0) il bus esce com'è.
 */
#ifndef STAME_DSP_DRUMS_H
#define STAME_DSP_DRUMS_H
#include "../core/stame_base.h"
#include "smp.h"

/* id degli strumenti, nell'ordine dei tasti di ACC-212 (C … B), più i clic del metronomo (ACC-207) */
enum { DRUM_KICK, DRUM_RIMSHOT, DRUM_SNARE, DRUM_CLAP, DRUM_CLOSED_HAT, DRUM_TOM_LO, DRUM_OPEN_HAT,
       DRUM_TOM_HI, DRUM_MARACAS, DRUM_CONGA, DRUM_COWBELL, DRUM_CYMBAL, DRUM_CLICK_ACCENT, DRUM_CLICK,
       DRUM_COUNT };

#define DRUM_VOICES 10

typedef struct {
    uint8_t on, inst;
    float t;                    /* secondi dall'attacco */
    float amp, ph, ph2;         /* livello, fasi degli oscillatori */
    float e1, e2, e3, d1, d2, d3;   /* inviluppi esponenziali e loro moltiplicatori per campione */
    float bp1, bp2, hp;         /* stati dei filtri del rumore */
    float c0, c1, c2, ha;       /* coefficienti del passa-banda e del passa-alto, calcolati al colpo */
    float gl, gr;               /* guadagni L e R */
    const smp_zone_t *z;        /* campione del kit, oppure NULL: sintesi */
    uint32_t idx;               /* posizione nel campione, intera e frazionaria */
    float frac, inc;
} drum_voice_t;

typedef struct {
    float fs, inv_fs;
    float gain;                 /* volume del beat 0…1 (curva di g_master) */
    uint32_t rng;
    const smp_bank_t *bank;     /* banco e kit in uso (NULL = tutto sintesi) */
    const smp_set_t *kit;
    drum_voice_t v[DRUM_VOICES];
    /* FX del bus: valori attuali, che seguono i bersagli a blocchi (15 ms), e stati */
    float fx_a;                 /* coefficiente per blocco dell'inseguimento */
    float drive, drive_t;       /* drive 0…1 */
    float fpos, fpos_t;         /* filtro −1 (passa-basso chiuso) … 0 (spento) … +1 (passa-alto aperto) */
    float drv_prev[2];          /* ultimo campione all'ingresso del drive, per il campione di mezzo */
    float ic1[2], ic2[2];       /* stati del filtro */
} drums_t;

void drums_init(drums_t *k, float fs, uint32_t seed);
/* il kit a campioni (un set del banco) per i colpi successivi; NULL = kit sintetizzato */
void drums_set_kit(drums_t *k, const smp_bank_t *bank, const smp_set_t *kit);
void drums_hit(drums_t *k, uint8_t inst, uint8_t vel);
void drums_volume(drums_t *k, uint8_t v);          /* 0…99 */
/* FX del bus: drive 0…10, filtro −10 (passa-basso a 150 Hz) … 0 (spento) … +10 (passa-alto a 3 kHz) */
void drums_fx(drums_t *k, uint8_t drive, int8_t filt);
/* somma 16 frame del kit in L e R (che il chiamante azzera) */
void drums_render16(drums_t *k, float *L, float *R);
void drums_all_off(drums_t *k);

#endif
