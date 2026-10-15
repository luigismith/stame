/* vetrina_dsp.c — applica al motore audio i comandi della vetrina (vet_snd_t), sulla Flip e nel render. */
#include "vetrina_dsp.h"

void vet_snd_apply(motore_t *m, const vet_snd_t *e)
{
    dsp_t *d = m->d;
    dsp_engine eng = e->engine ? DSP_BASS : DSP_SOUND;
    switch (e->type) {
    case VS_NOTE_ON:     mot_note(m, e->engine, e->a, e->b); break;
    case VS_NOTE_OFF:    mot_note(m, e->engine, e->a, 0); break;
    case VS_CHORD_START: mot_chord_start(m); break;
    case VS_PATCH:
        if (e->engine) dsp_load_patch(d, DSP_BASS, vet_bass_patch[e->a % VET_N_BASSES], 0);
        else dsp_load_patch(d, DSP_SOUND, vet_sound_patch[e->a % VET_N_SOUNDS], 0);
        break;
    case VS_PARAM:       dsp_setpar(d, eng, e->a, e->b); break;
    case VS_MASTER:      dsp_set_master_volume(d, e->a); break;
    case VS_BASS_VOL:    dsp_set_bass_volume(d, e->a); break;
    case VS_ALL_OFF:     mot_all_off(m); break;
    case VS_BPM:         mot_bpm(m, e->a); break;
    case VS_PERF:        mot_perf(m, e->a, e->b); break;
    case VS_BEAT:        mot_beat(m, e->a, e->b); break;
    case VS_METER:       mot_meter(m, e->a); break;
    case VS_BEAT_ON:     mot_beat_on(m, e->a != 0); break;
    case VS_BEAT_VOL:    mot_beat_volume(m, e->a); break;
    case VS_TRANSPOSE:   mot_transpose(m, (int8_t)e->a); break;
    case VS_LOOP:        mot_loop(m, e->a); break;
    default: break;
    }
}

void vet_snd_render(motore_t *m, vet_t *v, float *L, float *R, uint32_t n)
{
    for (uint32_t i = 0; i + DSP_BLOCK <= n; i += DSP_BLOCK) {
        vet_snd_t e;
        while (vet_snd_peek(v, &e) && vet_snd_due(m, &e)) {
            vet_snd_pop(v, &e);
            vet_snd_apply(m, &e);
        }
        mot_render(m, L + i, R + i, DSP_BLOCK);
    }
}

void vet_snd_init(motore_t *m, dsp_t *d, uint32_t fs, uint32_t seed)
{
    dsp_init(d, (float)fs, seed);
    dsp_load_patch(d, DSP_SOUND, vet_sound_patch[2], 0);
    dsp_load_patch(d, DSP_BASS, vet_bass_patch[0], 0);
    mot_init(m, d, fs, seed);
}
