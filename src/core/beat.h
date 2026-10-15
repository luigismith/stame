/* beat.h — Beat e metronomo (specifica 10, §10.3–§10.4; ACC-207…210; 20, SND-537).
 *
 * Un Beat è una battuta di 4/4 su griglia di 1/16 (24 tick), in loop finché suona, e ha un kit: il
 * set del banco di campioni che suona i suoi colpi (SND-537), oppure nessuno per il kit sintetizzato
 * «Chip». La specifica dà un solo pattern provvisorio per tutti i Beat dell'Orchid (ACC-210,
 * contenuto ignoto); i Beat della vetrina sono pattern di Stame. Il metronomo clicca sui battiti con
 * l'accento sul primo (ACC-207, TV-112).
 */
#ifndef STAME_BEAT_H
#define STAME_BEAT_H
#include "stame_base.h"

enum { BEAT_M_OFF, BEAT_M_METRONOME, BEAT_M_PATTERN };    /* come ui_beat_mode_t */
enum { METER_2_4, METER_3_4, METER_4_4, METER_6_8 };      /* metriche del metronomo (ACC-206, ACC-208) */
#define BEAT_COUNT 13                                      /* 0 = provvisorio di ACC-210, 1…12 della vetrina */

typedef struct { uint8_t inst, vel; } beat_hit_t;

/* colpi del passo s (0…15) del Beat b; restituisce quanti (al massimo max) */
int beat_hits(int b, int s, beat_hit_t *out, int max);
/* tick della battuta (192, 288, 384, 288) e fra due clic (la semiminima; la croma in 6/8) */
uint32_t meter_bar(int meter);
uint32_t meter_click(int meter);
/* clic del metronomo a pos tick dalla battuta 1: CLICK_ACCENT sul primo battito (in 6/8 anche sul
 * quarto), CLICK sugli altri (ACC-207) */
int metro_hits(int meter, uint32_t pos, beat_hit_t *out, int max);
const char *beat_name(int b);
/* nome del set del banco che fa da kit al Beat b (SND-537); NULL = kit sintetizzato */
const char *beat_kit(int b);

#endif
