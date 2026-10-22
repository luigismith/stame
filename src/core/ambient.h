/* ambient.h — il modulo AMBIENT: Stame che suona quasi da solo (specifica 10, §10.9; 40, MIDI-143).
 *
 * Due parti. L'armonia sceglie gli accordi: una tavolozza per atmosfera e per modo (maggiore o minore)
 * nella tonalità di Key, e da un accordo al prossimo preferisce quelli con più note in comune, così il
 * giro si muove piano. Chi la usa preme i tasti dello strumento con l'accordo che esce (tasto, tipo ed
 * estensioni): voicing, basso, Perform e plancia restano quelli di sempre. Se chi suona mette un suo
 * accordo, il giro riparte da quello.
 * Le note sparse cadono sopra l'accordo: fino a sei voci, ognuna con il suo periodo (lunghezze che non
 * hanno multipli comuni piccoli, come i nastri di Eno), che a ogni giro suonano una nota dell'accordo o
 * della pentatonica della tonalità vicina a quella di prima. Le usa il thread audio, a tick esatti.
 * C11 puro, niente heap, deterministico a parità di seme: il generatore è ripetibile nei test.
 */
#ifndef STAME_AMBIENT_H
#define STAME_AMBIENT_H
#include "stame_base.h"

enum { AMB_FLOAT, AMB_DUSK, AMB_DEEP, AMB_GLASS, AMB_DRONE, AMB_TIDE, AMB_MOODS };
#define AMB_DENS_MAX    10      /* densità delle note sparse: 0 = nessuna */
#define AMB_MOTION_MAX  10      /* movimento: 0 = l'accordo non cambia mai */
#define AMB_VAR_MAX     99
#define AMB_VOICES      6

/* un accordo da premere: tasto 0…11 (classe della fondamentale, prima del transpose), tipi (bit ACC_DIM…
 * ACC_SUS di acc.h) ed estensioni (bit ACC_E6…ACC_E9), con la velocity */
typedef struct { uint8_t key, types, exts, vel; } amb_chord_t;

typedef struct {
    uint8_t  mood, var, tonic, minor;
    int8_t   cur, prev;             /* voci della tavolozza in corso e di prima; −1 = un accordo di chi suona */
    uint16_t pcs;                   /* classi dell'accordo in corso */
    uint32_t rng;
} amb_harm_t;

/* l'armonia con l'atmosfera, la variazione (0…99, il seme del giro) e la tonalità */
void amb_harm_init(amb_harm_t *h, int mood, int var, int tonic, bool minor);
/* il primo accordo: quello di casa dell'atmosfera */
amb_chord_t amb_harm_first(amb_harm_t *h);
/* il prossimo, a caso fra le voci della tavolozza ma con più peso a quelle con note in comune */
amb_chord_t amb_harm_next(amb_harm_t *h);
/* l'accordo di chi suona (classi prima del transpose) diventa quello in corso: il giro riparte da lì */
void amb_harm_follow(amb_harm_t *h, uint16_t pcs);
/* le classi di un accordo, come le suona il motore degli accordi (acc_chord_mask) */
uint16_t amb_chord_pcs(amb_chord_t c);
/* quanti quarti dura un accordo con il movimento m (0 = per sempre); salt sceglie le battute in più o in meno */
uint16_t amb_chord_beats(int motion, uint32_t salt);
const char *amb_mood_name(int mood);

/* ---- le note sparse, nel thread audio ---- */
typedef struct {
    uint32_t next, off;             /* prossimo giro e fine della nota che suona, in tick */
    uint16_t period;                /* tick fra due giri */
    uint8_t  note;                  /* nota che suona, 0xFF = nessuna */
    uint8_t  last;                  /* ultima nota suonata: la prossima le sta vicino */
} amb_voice_t;

typedef struct {
    uint8_t  on, dens, mood, tonic, minor;
    uint16_t chord;                 /* classi dell'ultimo accordo che suonava (dopo il transpose) */
    uint32_t rng;
    amb_voice_t v[AMB_VOICES];
} amb_bloom_t;

typedef struct { uint8_t note, vel; } amb_ev_t;     /* vel 0 = note-off */

void amb_bloom_init(amb_bloom_t *b, uint32_t seed);
/* accese o spente, densità, atmosfera (il registro) e tonalità (la pentatonica, dopo il transpose), al tick t.
 * Accese da spente, la prima nota cade entro un quarto; spente, le note che suonano finiscono da sole */
void amb_bloom_set(amb_bloom_t *b, bool on, int dens, int mood, int tonic, bool minor, uint32_t t);
/* un'idea nuova: il seme e i periodi ripartono da var */
void amb_bloom_seed(amb_bloom_t *b, int var, uint32_t t);
/* gli eventi del tick t. chord = classi che suonano adesso (0 = tiene l'ultimo); busy[n] ≠ 0 = la nota n è già
 * tenuta da un'altra sorgente e non si ripete. Restituisce quanti (al più max) */
int amb_bloom_run(amb_bloom_t *b, uint32_t t, uint16_t chord, const uint8_t busy[128], amb_ev_t *out, int max);
/* Panic: le note si dimenticano senza note-off (le ha già spente chi chiama) */
void amb_bloom_forget(amb_bloom_t *b);

#endif
