/* reverb.c — riverbero unico a mandata (specifica 20, §10.5; SND-530).
 *
 * Rete di 8 linee con feedback (FDN) e matrice di Hadamard, due diffusori all-pass in ingresso,
 * passa-alto all'ingresso (REVHP), passa-basso in ogni linea (REVLP), RT60 e lunghezze da REVSIZE.
 * Le lunghezze scorrono piano verso il nuovo valore, così un cambio di suono non fa clic.
 * I parametri sono quelli del Sound (SND-012). Uscita solo wet.
 */
#include "dsp_int.h"

/* lunghezze delle linee a 48 kHz con REVSIZE 127 (numeri primi, 32–92 ms) */
static const float BASE[DSP_REV_LINES] = { 1559.0f, 1949.0f, 2347.0f, 2753.0f, 3163.0f, 3571.0f, 3989.0f, 4409.0f };
static const uint32_t AP_LEN[2] = { 347, 563 };          /* diffusori, a 48 kHz */

static float target_len(const dsp_t *d, int i, float size)
{
    float scale = 0.5f + 0.5f * size / 127.0f;
    return BASE[i] * scale * d->fs / 48000.0f;
}

void rev_reset(dsp_reverb_t *r, float fs)
{
    memset(r, 0, sizeof *r);
    r->size = 100.0f;
    r->lpr = 120.0f;
    r->hpr = 10.0f;
    float scale = (0.5f + 0.5f * 100.0f / 127.0f) * fs / 48000.0f;
    for (int i = 0; i < DSP_REV_LINES; i++) r->len[i] = BASE[i] * scale;
}

static inline float rd(const float *buf, uint32_t w, float dly)
{
    int di = (int)dly;
    float fr = dly - (float)di;
    float a = buf[(w - (uint32_t)di) & (DSP_REV_N - 1)], b = buf[(w - (uint32_t)di - 1u) & (DSP_REV_N - 1)];
    return a + fr * (b - a);
}

void rev_process(dsp_t *d, const float *inL, const float *inR, float *outL, float *outR)
{
    dsp_reverb_t *r = &d->rev;
    const dsp_eng_t *S = &d->eng[DSP_SOUND];
    r->size = S->sm[SND_P_REVSIZE];
    r->lpr = S->sm[SND_P_REVLP];
    r->hpr = S->sm[SND_P_REVHP];

    float rt60 = curve(CURVE_T_REV, r->size);
    float alp = onepole_a(curve(CURVE_F_REVLP, r->lpr), d->inv_fs);
    float ahp = onepole_a(curve(CURVE_F_REVHP, r->hpr), d->inv_fs);
    float g[DSP_REV_LINES];
    for (int i = 0; i < DSP_REV_LINES; i++) {
        r->len[i] += (target_len(d, i, r->size) - r->len[i]) * 0.002f;      /* scorrono, niente clic */
        g[i] = expf(-DSP_LN60 * r->len[i] * d->inv_fs / rt60);               /* −60 dB in RT60 */
    }
    float modinc = 0.37f * d->inv_fs;

    for (int n = 0; n < DSP_BLOCK; n++) {
        /* passa-alto all'ingresso e diffusori all-pass (uno per canale) */
        float x[2] = { inL[n], inR[n] };
        for (int c = 0; c < 2; c++) {
            r->hp_z[c] += ahp * (x[c] - r->hp_z[c]);
            float u = x[c] - r->hp_z[c];
            float *ap = r->ap[c];
            uint32_t L = AP_LEN[c];
            float z = ap[(r->apw - L) & (DSP_REV_AP_N - 1)];
            float v = u + 0.6f * z;
            ap[r->apw & (DSP_REV_AP_N - 1)] = v;
            x[c] = z - 0.6f * v;
        }
        r->apw++;

        /* uscite delle linee, due modulate piano */
        float o[DSP_REV_LINES];
        float m = sin_cyc(r->mod) * 6.0f;
        for (int i = 0; i < DSP_REV_LINES; i++) {
            float dly = r->len[i] + (i == 0 ? m : i == 5 ? -m : 0.0f);
            float y = rd(r->line[i], r->w, dly);
            r->lp[i] += alp * (y - r->lp[i]);
            o[i] = r->lp[i] * g[i];
        }
        r->mod += modinc;
        if (r->mod >= 1.0f) r->mod -= 1.0f;

        /* matrice di Hadamard 8×8 (trasformata veloce), normalizzata */
        float h[DSP_REV_LINES];
        for (int i = 0; i < DSP_REV_LINES; i++) h[i] = o[i];
        for (int len = 1; len < DSP_REV_LINES; len <<= 1)
            for (int i = 0; i < DSP_REV_LINES; i += len << 1)
                for (int j = i; j < i + len; j++) {
                    float a = h[j], b = h[j + len];
                    h[j] = a + b;
                    h[j + len] = a - b;
                }
        for (int i = 0; i < DSP_REV_LINES; i++) {
            float fbk = h[i] * 0.353553391f;                                 /* 1/√8 */
            r->line[i][r->w & (DSP_REV_N - 1)] = fbk + x[i & 1];
        }
        r->w++;

        outL[n] = (o[0] + o[2] + o[4] + o[6]) * 0.5f;
        outR[n] = (o[1] + o[3] + o[5] + o[7]) * 0.5f;
    }
    for (int i = 0; i < DSP_REV_LINES; i++) r->lp[i] = undenorm(r->lp[i]);
    for (int c = 0; c < 2; c++) r->hp_z[c] = undenorm(r->hp_z[c]);
}
