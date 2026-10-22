/* beat.h — Beat, kit e metronomo (specifica 10, §10.3–§10.4; ACC-207…210, ACC-218; 20, SND-537, SND-541).
 *
 * Un Beat è una battuta di 4/4 su griglia di 1/16 (24 tick), in loop finché suona, e ha un kit del
 * catalogo: uno dei quattro a campioni (un set del banco, SND-537), il «Chip» sintetizzato di sempre o
 * uno dei kit sintetizzati della libreria (SND-541). La specifica dà un solo pattern provvisorio per
 * tutti i Beat dell'originale (ACC-210, contenuto ignoto); i Beat della vetrina sono pattern di Stame.
 * Il metronomo clicca sui battiti con l'accento sul primo (ACC-207, TV-112).
 */
#ifndef STAME_BEAT_H
#define STAME_BEAT_H
#include "stame_base.h"
#include "../dsp/drums.h"

enum { BEAT_M_OFF, BEAT_M_METRONOME, BEAT_M_PATTERN };    /* come ui_beat_mode_t */
enum { METER_2_4, METER_3_4, METER_4_4, METER_6_8 };      /* metriche del metronomo (ACC-206, ACC-208) */
#define BEAT_COUNT 65                                      /* 0 = provvisorio di ACC-210, 1…64 della vetrina (ACC-218) */
/* il catalogo dei kit (SND-541): i quattro a campioni, il Chip, poi la libreria sintetizzata nell'ordine di
 * drum_kits[] (DK_KIT_*). L'ordine dei primi cinque non cambia: K1 e la demo li contano così */
enum { KIT_STUDIO, KIT_JAZZ, KIT_808, KIT_TECHNO, KIT_CHIP, KIT_SYNTH0 };
#define KIT_COUNT (KIT_SYNTH0 + DRUM_SYNTH_KITS)
#define KIT_SYN(dk) (KIT_SYNTH0 + (dk))                    /* il kit DK_KIT_* della libreria nel catalogo */

typedef struct { uint8_t inst, vel; } beat_hit_t;

/* colpi del passo s (0…15) del Beat b; restituisce quanti (al massimo max) */
int beat_hits(int b, int s, beat_hit_t *out, int max);
/* lo stesso per il fill del Beat b (MIDI-133, T4 tenuto): una battuta di riempimento nello stesso kit */
int beat_fill_hits(int b, int s, beat_hit_t *out, int max);
/* tick della battuta (192, 288, 384, 288) e fra due clic (la semiminima; la croma in 6/8) */
uint32_t meter_bar(int meter);
uint32_t meter_click(int meter);
/* clic del metronomo a pos tick dalla battuta 1: CLICK_ACCENT sul primo battito (in 6/8 anche sul
 * quarto), CLICK sugli altri (ACC-207) */
int metro_hits(int meter, uint32_t pos, beat_hit_t *out, int max);
const char *beat_name(int b);
/* il kit i del catalogo (0…KIT_COUNT-1; MIDI-135, SND-541): set del banco (NULL = sintetizzato),
 * etichetta, stile («samples», «classic» per il Chip, quello della libreria) e ricetta (NULL = campioni o
 * Chip). Fuori dai limiti: NULL e "" */
const char *beat_kit_name(int i);
const char *beat_kit_label(int i);
const char *beat_kit_style(int i);
const drum_kit_t *beat_kit_synth(int i);
/* il kit del Beat b, indice del catalogo (SND-537, ACC-218) */
int beat_kit_of(int b);
/* nome del set del banco che fa da kit al Beat b; NULL = kit sintetizzato */
const char *beat_kit(int b);

#endif
