/* inventa.h — la batteria che si inventa con le tre manopole del pad (sezione 40, MIDI-139; 10, ACC-215).
 *
 * Un loop di due battute in sedicesimi (32 passi) per cinque parti: cassa, rullante (o battimani o
 * rimshot, secondo lo stile), charleston chiuso, charleston aperto e percussioni. Ogni stile dà a ogni
 * passo di ogni parte una priorità da 0 (mai) a 9 (sempre: lo scheletro dello stile); la densità di una
 * parte, da 0 a 10, fa suonare i passi con priorità almeno 10 − densità, quindi 0 tace e 10 suona tutto.
 * La variazione sposta le priorità di una quantità pseudocasuale ripetibile, che cresce con il numero:
 * 0 è lo stile com'è, ogni scatto un'idea nuova, e tornando indietro si ritrova quella di prima. Nelle
 * ultime quattro sedicesimi della seconda battuta la variazione fa una piccola chiusa. Lo scheletro non
 * si sposta mai. C11 puro, niente heap: lo usano il thread audio (motore) e la plancia (la griglia).
 */
#ifndef STAME_INVENTA_H
#define STAME_INVENTA_H
#include "stame_base.h"
#include "beat.h"

enum { INV_KICK, INV_SNARE, INV_HAT, INV_OPEN, INV_PERC, INV_PARTS };
#define INV_STEPS    32         /* due battute di 4/4 in sedicesimi */
#define INV_GROOVES  34         /* i dieci del 18/10/2026, i venti di genere del 19/10/2026, i quattro trance del 22/10/2026 (ACC-215) */
#define INV_DENS_MAX 10
#define INV_VAR_MAX  99

typedef struct {
    uint8_t groove, var;
    uint8_t inst[INV_PARTS];            /* strumento di drums.h per ogni parte */
    uint8_t lv[INV_PARTS][INV_STEPS];   /* priorità in sedicesimi di livello: 0 = mai, 144 = scheletro */
} inv_t;

/* lo stile groove (0…INV_GROOVES-1, fuori dai limiti si riporta dentro) con la variazione var */
void inv_build(inv_t *g, int groove, int var);
/* colpi del passo step (0…31) con le densità delle cinque parti (0…10); fill = T4 tenuto: tre punti di
 * densità in più e il rullante e le percussioni che chiudono la battuta. Restituisce quanti (al più max) */
int inv_hits(const inv_t *g, const uint8_t dens[INV_PARTS], int step, bool fill, beat_hit_t *out, int max);
const char *inv_groove_name(int groove);
/* kit di beat.h (beat_kit_name) che lo stile usa se non se ne sceglie uno a mano */
int inv_groove_kit(int groove);
/* lo stile più vicino a un Beat di beat.h, per cominciare dal Beat che si stava usando */
int inv_groove_of_beat(int beat);
/* una variazione nuova a caso ma ripetibile, diversa da var (il tasto «nuova idea» di m2) */
int inv_var_next(int var, uint32_t salt);

#endif
