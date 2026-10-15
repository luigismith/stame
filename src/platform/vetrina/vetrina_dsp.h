/* vetrina_dsp.h — ponte fra la vetrina e il motore audio (core/motore, specifica 20). */
#ifndef STAME_VETRINA_DSP_H
#define STAME_VETRINA_DSP_H
#include "vetrina.h"
#include "../../dsp/dsp.h"
#include "../../core/motore.h"

/* synth e motore pronti con le patch iniziali della vetrina */
void vet_snd_init(motore_t *m, dsp_t *d, uint32_t fs, uint32_t seed);
/* applica un comando della vetrina al motore (dal thread che lo possiede) */
void vet_snd_apply(motore_t *m, const vet_snd_t *e);
/* true se il comando va applicato prima del prossimo blocco: subito, o al suo tick (mot_due) */
static inline bool vet_snd_due(const motore_t *m, const vet_snd_t *e) { return !e->timed || mot_due(m, e->at); }
/* n campioni (multiplo di 16) presi dalla coda della vetrina, ogni comando al suo blocco (render, prove) */
void vet_snd_render(motore_t *m, vet_t *v, float *L, float *R, uint32_t n);

#endif
