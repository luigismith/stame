/* drums.h — il kit di batteria (specifica 10, ACC-212; 20, SND-535 e SND-537; QA-SND-30).
 *
 * Due strade per ogni strumento: un campione del kit scelto (un set del banco di campioni, §7b: la
 * zona ha per nota l'id dello strumento) oppure, se il kit non lo ha o non c'è nessun kit, la sintesi
 * in stile CR-78 (il kit «Chip»). Cassa, rullante, charleston chiuso e aperto, battimani, rimshot,
 * tom bassi e alti, campanaccio, maracas, conga, piatto, e i due clic del metronomo. Rende un bus
 * stereo che il chiamante passa a dsp_render16 (drum_L, drum_R). C11 puro, niente heap.
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
} drums_t;

void drums_init(drums_t *k, float fs, uint32_t seed);
/* il kit a campioni (un set del banco) per i colpi successivi; NULL = kit sintetizzato */
void drums_set_kit(drums_t *k, const smp_bank_t *bank, const smp_set_t *kit);
void drums_hit(drums_t *k, uint8_t inst, uint8_t vel);
void drums_volume(drums_t *k, uint8_t v);          /* 0…99 */
/* somma 16 frame del kit in L e R (che il chiamante azzera) */
void drums_render16(drums_t *k, float *L, float *R);
void drums_all_off(drums_t *k);

#endif
