/* vetrina_dsp.c — applica al synth i comandi della vetrina (vet_snd_t), sulla Flip e nel render. */
#include "vetrina_dsp.h"

void vet_snd_apply(dsp_t *d, const vet_snd_t *e)
{
    dsp_engine eng = e->engine ? DSP_BASS : DSP_SOUND;
    switch (e->type) {
    case VS_NOTE_ON:     dsp_note_on(d, eng, e->a, e->b); break;
    case VS_NOTE_OFF:    dsp_note_off(d, eng, e->a); break;
    case VS_CHORD_START: dsp_chord_start(d, eng); break;
    case VS_PATCH:
        if (e->engine) dsp_load_patch(d, DSP_BASS, vet_bass_patch[e->a % VET_N_BASSES], 0);
        else dsp_load_patch(d, DSP_SOUND, vet_sound_patch[e->a % VET_N_SOUNDS], 0);
        break;
    case VS_PARAM:       dsp_setpar(d, eng, e->a, e->b); break;
    case VS_MASTER:      dsp_set_master_volume(d, e->a); break;
    case VS_BASS_VOL:    dsp_set_bass_volume(d, e->a); break;
    case VS_ALL_OFF:     dsp_all_notes_off(d); break;
    default: break;
    }
}

void vet_snd_init(dsp_t *d, float fs, uint32_t seed)
{
    dsp_init(d, fs, seed);
    dsp_load_patch(d, DSP_SOUND, vet_sound_patch[2], 0);
    dsp_load_patch(d, DSP_BASS, vet_bass_patch[0], 0);
}
