/* drums.h — il kit di batteria (specifica 10, ACC-212; 20, SND-535, SND-537 e SND-540…SND-543; QA-SND-30).
 *
 * Tre strade per ogni strumento: un campione del kit scelto (un set del banco di campioni, §7b: la
 * zona ha per nota l'id dello strumento); oppure la ricetta di un kit sintetizzato della libreria
 * (drum_kits.c, generato da tools/kits.py: tono, rumore e clic con i loro inviluppi, filtro, drive e
 * riduzione di campionamento); oppure, se non c'è né l'uno né l'altro, la sintesi in stile CR-78 di
 * sempre (il kit «Chip»). Cassa, rullante, charleston chiuso e aperto, battimani, rimshot, tom bassi e
 * alti, campanaccio, maracas, conga, piatto, e i due clic del metronomo, che restano quelli di sempre.
 * Rende un bus stereo che il chiamante passa a dsp_render16 (drum_L, drum_R). C11 puro, niente heap.
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
#define DRUM_KIT_INST 12        /* strumenti di un kit: DRUM_KICK … DRUM_CYMBAL (i clic non sono del kit) */

/* ---- la ricetta di uno strumento sintetizzato (SND-540). Il tono (seno, quadra, FM o metallo) ha un
 * salto di pitch f = f0 · (1 + pa · e^(−t/tp)) e decade con ta; il rumore (bianco, tenuto per nhold
 * campioni) decade con tn, a colpi se bursts > 1; il clic è un millisecondo di rumore. Il filtro prende
 * il rumore, anche il tono con DK_ALL, sempre il metallo. Poi drive (tanh), riduzione di campionamento
 * (hold) e di bit (bits livelli per lato), attacco lineare e gain. Tempi in secondi, frequenze in Hz ---- */
enum { DK_NONE, DK_SINE, DK_SQUARE, DK_FM, DK_METAL };       /* forma del tono */
enum { DK_LP, DK_BP, DK_HP };                                /* filtro */
#define DK_ALL 0x01u                                         /* il filtro prende anche il tono */
#define DK_METAL_SETS 4         /* rapporti del metallo (r2): charleston analogico, campanaccio, campana, piatto */

typedef struct {
    uint8_t osc, flt, flags, bursts;
    uint8_t hold, nhold;        /* tieni un campione dell'uscita ogni hold, del rumore ogni nhold (0, 1 = niente) */
    uint16_t bits;              /* livelli per lato della quantizzazione, 0 = niente */
    float f0, pa, tp;           /* tono: frequenza, salto di pitch e sua costante di tempo */
    float ta, tone;             /* tono: costante di tempo e livello */
    float r2, l2;               /* secondo parziale: rapporto e livello (seno, quadra); modulante: rapporto e indice
                                 * in cicli (FM); set di rapporti (metallo) */
    float fc, q;                /* filtro */
    float tn, noise;            /* rumore: costante di tempo e livello */
    float click, drive;         /* clic d'attacco; drive (0 = pulito) */
    float att, dur;             /* attacco lineare; durata (gli ultimi 4 ms sfumano) */
    float pan, gain;            /* −1…+1; guadagno pareggiato da tools/kits.py */
} drum_rec_t;

/* un kit sintetizzato della libreria: nome, stile e i dodici strumenti nell'ordine di ACC-212 */
typedef struct { const char *name, *style; drum_rec_t r[DRUM_KIT_INST]; } drum_kit_t;

#include "drum_kits.h"          /* DRUM_SYNTH_KITS e gli indici DK_KIT_* (generato da tools/kits.py) */
extern const drum_kit_t drum_kits[DRUM_SYNTH_KITS];

typedef struct {
    uint8_t on, inst;
    uint8_t prog;               /* colpo del Beat o del loop, che il Drop zittisce (SND-539); 0 = suonato dal vivo */
    float t;                    /* secondi dall'attacco */
    float amp, ph, ph2;         /* livello, fasi degli oscillatori */
    float e1, e2, e3, d1, d2, d3;   /* inviluppi esponenziali e loro moltiplicatori per campione */
    float bp1, bp2, hp;         /* stati dei filtri del rumore */
    float c0, c1, c2, ha;       /* coefficienti del passa-banda e del passa-alto, calcolati al colpo */
    float gl, gr;               /* guadagni L e R */
    const smp_zone_t *z;        /* campione del kit, oppure NULL: sintesi */
    uint32_t idx;               /* posizione nel campione, intera e frazionaria */
    float frac, inc;
    /* ricetta di un kit sintetizzato (SND-540), oppure NULL */
    const drum_rec_t *r;
    float ep, dp, et, dt, en, dn, ec, dc, eg, dg;   /* inviluppi di pitch, tono, rumore, clic e generale (il chiuso strozza) */
    float dn_tail;              /* il rumore dopo l'ultimo colpo del battimani */
    float a, a_inc;             /* attacco */
    float burst_t;              /* quando parte il prossimo colpo di rumore */
    uint8_t burst_n, hc, nc;    /* colpi che restano; contatori della riduzione di campionamento */
    float held, nheld, qb, qi;  /* campioni tenuti; livelli della quantizzazione e il loro inverso */
    float s1, s2, f1, f2, f3, fk;   /* filtro a variabili di stato: stati e coefficienti */
    float inc0, inc2;           /* passi del tono e del secondo parziale senza salto di pitch */
    uint8_t use_n, use_f, nmet; /* serve il rumore; serve il filtro; oscillatori del metallo */
    float mph[6], minc[6];      /* fasi e passi del metallo */
} drum_voice_t;

typedef struct {
    float fs, inv_fs;
    float gain;                 /* volume del beat 0…1 (curva di g_master) */
    uint32_t rng;
    const smp_bank_t *bank;     /* banco e kit in uso (NULL = tutto sintesi) */
    const smp_set_t *kit;
    const drum_kit_t *syn;      /* kit sintetizzato della libreria (NULL = il Chip di sempre) */
    drum_voice_t v[DRUM_VOICES];
    /* FX del bus: valori attuali, che seguono i bersagli a blocchi (15 ms), e stati */
    float fx_a;                 /* coefficiente per blocco dell'inseguimento */
    float drive, drive_t;       /* drive 0…1 */
    float fpos, fpos_t;         /* filtro −1 (passa-basso chiuso) … 0 (spento) … +1 (passa-alto aperto) */
    float drv_prev[2];          /* ultimo campione all'ingresso del drive, per il campione di mezzo */
    float ic1[2], ic2[2];       /* stati del filtro */
    /* Drop: i colpi programmati tacciono (rampa di 5 ms, poi le loro voci si spengono) */
    uint8_t prog_mute;
    float prog_g, prog_step;
} drums_t;

void drums_init(drums_t *k, float fs, uint32_t seed);
/* il kit a campioni (un set del banco) per i colpi successivi; NULL = kit sintetizzato */
void drums_set_kit(drums_t *k, const smp_bank_t *bank, const smp_set_t *kit);
/* il kit sintetizzato della libreria per i colpi successivi (SND-541); NULL = il Chip. Un kit a campioni
 * scelto con drums_set_kit ha la precedenza dove ha lo strumento */
void drums_set_synth(drums_t *k, const drum_kit_t *kit);
void drums_hit(drums_t *k, uint8_t inst, uint8_t vel);
/* colpo programmato (Beat, loop): come drums_hit, ma durante il Drop non suona */
void drums_hit_prog(drums_t *k, uint8_t inst, uint8_t vel);
/* Drop (SND-539): on = i colpi programmati tacciono, quelli suonati dal vivo e i clic no */
void drums_drop(drums_t *k, bool on);
void drums_volume(drums_t *k, uint8_t v);          /* 0…99 */
/* FX del bus: drive 0…10, filtro −10 (passa-basso a 150 Hz) … 0 (spento) … +10 (passa-alto a 3 kHz) */
void drums_fx(drums_t *k, uint8_t drive, int8_t filt);
/* somma 16 frame del kit in L e R (che il chiamante azzera) */
void drums_render16(drums_t *k, float *L, float *R);
void drums_all_off(drums_t *k);

#endif
