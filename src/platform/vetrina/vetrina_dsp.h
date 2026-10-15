/* vetrina_dsp.h — ponte fra la vetrina e il synth (specifica 20). */
#ifndef STAME_VETRINA_DSP_H
#define STAME_VETRINA_DSP_H
#include "vetrina.h"
#include "../../dsp/dsp.h"

/* synth pronto con le patch iniziali della vetrina */
void vet_snd_init(dsp_t *d, float fs, uint32_t seed);
/* applica un comando della vetrina al synth (dal thread che possiede il dsp) */
void vet_snd_apply(dsp_t *d, const vet_snd_t *e);

#endif
