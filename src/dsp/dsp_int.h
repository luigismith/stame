/* dsp_int.h — parti comuni interne del modulo dsp (non per i chiamanti). */
#ifndef STAME_DSP_INT_H
#define STAME_DSP_INT_H
#include "dsp.h"
#include "curves.h"
#include <math.h>

#define DSP_PI     3.14159265358979f
#define DSP_TWO_PI 6.28318530717959f
#define DSP_LN60   6.90775527898214f    /* ln(1000): −60 dB */
#define DSP_LN2_12 0.0577622650466621f  /* ln(2) / 12 */

static inline float clampf(float x, float a, float b) { return x < a ? a : x > b ? b : x; }

/* xorshift32 (SND-005): mai rand() */
static inline uint32_t xs32(uint32_t *s)
{
    uint32_t x = *s;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    return *s = x;
}
/* valore uniforme in [−1, 1) */
static inline float rnd_bi(uint32_t *s) { return (float)(int32_t)xs32(s) * (1.0f / 2147483648.0f); }

/* tanh veloce (Padé 3/2 con limite): errore < 0,2 % fino a |x| = 3, poi satura a ±1 */
static inline float tanh_f(float x)
{
    if (x > 3.0f) return 1.0f;
    if (x < -3.0f) return -1.0f;
    float x2 = x * x;
    return x * (27.0f + x2) / (27.0f + 9.0f * x2);
}

/* frequenza della nota MIDI p (anche frazionaria) */
static inline float note_hz(float p) { return 440.0f * expf((p - 69.0f) * DSP_LN2_12); }

/* seno da tabella (SND-306): x in cicli, qualunque segno */
extern const float dsp_sin_tab[2049];
static inline float sin_cyc(float x)
{
    x -= floorf(x);
    float f = x * 2048.0f;
    int i = (int)f;
    if (i > 2047) i = 2047;
    float t = f - (float)i;
    return dsp_sin_tab[i] + t * (dsp_sin_tab[i + 1] - dsp_sin_tab[i]);
}

/* stati dei filtri: sotto 1e−15 si azzerano una volta per blocco (SND-703) */
static inline float undenorm(float x) { return (x > -1e-15f && x < 1e-15f) ? 0.0f : x; }

/* coefficiente di un passa-basso a un polo a frequenza f */
static inline float onepole_a(float f, float inv_fs)
{
    float a = 1.0f - expf(-DSP_TWO_PI * f * inv_fs);
    return clampf(a, 0.0f, 1.0f);
}

/* fx.c */
void fx_reset(dsp_fx_t *fx);
void fx_delay_reset(dsp_delay_t *dl);
/* elabora uno slot su 16 frame in place; slot 0 = FX1, 1 = FX2 (con il delay) */
void fx_process(dsp_t *d, dsp_eng_t *E, int slot, float *L, float *R);

/* reverb.c */
void rev_reset(dsp_reverb_t *r, float fs);
void rev_process(dsp_t *d, const float *inL, const float *inR, float *outL, float *outR);

/* rp.c: modello Reed Piano (§7); p e sm sono la patch della voce (del motore o della coda) */
void rp_note_on(dsp_t *d, dsp_voice_t *v, const float *sm);
void rp_note_off(dsp_t *d, dsp_voice_t *v, const float *sm);
/* rende 16 campioni mono della voce in out[]; restituisce il picco */
float rp_render(dsp_t *d, dsp_voice_t *v, const uint8_t *p, const float *sm, float pitch_semi, float *out);
bool rp_done(const dsp_voice_t *v);

/* smp.c: modello SMP (§7b); la zona si sceglie alla nota, il passo di lettura a ogni blocco */
void smp_note_on(dsp_t *d, dsp_voice_t *v, const uint8_t *p);
float smp_ratio(const dsp_t *d, const dsp_voice_t *v, const float *sm, float pitch_semi);
/* rende 16 campioni mono in out[]; dopo la fine di un one-shot scrive zeri e segna ended */
void smp_render(dsp_voice_t *v, float *out);

#endif
