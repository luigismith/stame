/* fx.c — gli slot FX1 e FX2 di ogni motore (specifica 20, §10.2–§10.4).
 *
 * Chorus, ensemble e flanger leggono la stessa linea modulata, che registra sempre l'ingresso:
 * così al cambio di tipo non c'è niente di vecchio da svuotare. Anche il delay registra sempre
 * l'ingresso (con il feedback solo quando è attivo). Al cambio di tipo i due effetti suonano
 * insieme per 10 ms in dissolvenza incrociata (SND-507).
 */
#include "dsp_int.h"

#define LMASK (DSP_FX_LINE - 1)
#define DMASK (DSP_DELAY_N - 1)

void fx_reset(dsp_fx_t *fx)
{
    memset(fx, 0, sizeof *fx);
    fx->xf = 1.0f;
}

void fx_delay_reset(dsp_delay_t *dl) { memset(dl, 0, sizeof *dl); }

/* campione scritto dly campioni fa (dly ≥ 1, frazionario), con w = posizione della prossima scrittura */
static inline float tap(const float *buf, uint32_t mask, uint32_t w, float dly)
{
    int di = (int)dly;
    float fr = dly - (float)di;
    float a = buf[(w - (uint32_t)di) & mask], b = buf[(w - (uint32_t)di - 1u) & mask];
    return a + fr * (b - a);
}

/* parametri dello slot per il blocco: P1…P6 smussati in raw, rate già in Hz */
typedef struct {
    float p[6];
    float rate, d2;
} fxpar_t;

/* stato per campione del phaser: coefficiente dell'all-pass interpolato nel blocco */
typedef struct { float a0, da; } phz_t;

static float allpass_coef(float fc, float inv_fs)
{
    float t = tanf(DSP_PI * clampf(fc, 20.0f, 20000.0f) * inv_fs);
    return (t - 1.0f) / (t + 1.0f);
}

/* un campione dell'effetto `type` sul canale ch; x = ingresso, restituisce l'uscita dello slot */
static inline float fx_one(dsp_t *d, dsp_fx_t *fx, int type, const fxpar_t *q, int ch, float x, int i,
                           const phz_t *phz, float *fl_wet)
{
    float ms = d->fs * 0.001f;
    switch (type) {
    case SND_FX_CHORUS: {
        float off = ch ? 0.5f * q->p[2] / 127.0f : 0.0f;                    /* PHASE 0–180° */
        float m = (0.5f + 4.5f * q->d2) * ms;
        float dly = 7.0f * ms + m * sin_cyc(fx->lfo[SND_FX_CHORUS] + off);
        float wet = tap(fx->line[ch], LMASK, fx->lw, dly);
        return x * (1.0f - 0.5f * q->d2) + wet * 0.5f * q->d2;
    }
    case SND_FX_ENSEMBLE: {
        float slow = 3.0f * ms * q->d2, fast = 0.6f * ms * q->p[3] / 127.0f;
        float base = ch ? 1.0f / 6.0f : 0.0f, wet = 0.0f;
        for (int j = 0; j < 3; j++) {
            float o = base + (float)j / 3.0f;
            float dly = 10.0f * ms + slow * sin_cyc(fx->lfo[SND_FX_ENSEMBLE] + o) + fast * sin_cyc(fx->lfo2 + o);
            wet += tap(fx->line[ch], LMASK, fx->lw, dly);
        }
        return x * (1.0f - 0.5f * q->d2) + wet * (1.0f / 3.0f) * 0.5f * q->d2;
    }
    case SND_FX_PHASER: {
        float a = phz[ch].a0 + phz[ch].da * (float)(i + 1);
        float fb = 0.9f * q->p[2] / 127.0f;
        float u = x + fb * fx->pfb[ch];
        for (int s = 0; s < 6; s++) {
            float *st = fx->ap[ch][s];
            float y = a * u + st[0] - a * st[1];
            st[0] = u;
            st[1] = y;
            u = y;
        }
        fx->pfb[ch] = u;
        return x * (1.0f - 0.5f * q->d2) + u * 0.5f * q->d2;
    }
    case SND_FX_FLANGER: {
        float off = ch ? 0.5f * q->p[3] / 127.0f : 0.0f;
        float lfo = 0.5f + 0.5f * sin_cyc(fx->lfo[SND_FX_FLANGER] + off);
        float dly = (0.3f + 7.7f * q->d2 * lfo) * ms;
        if (dly < 1.0f) dly = 1.0f;
        float wet = tap(fx->line[ch], LMASK, fx->lw, dly);
        fl_wet[ch] = wet;
        return x * (1.0f - 0.5f * q->d2) + wet * 0.5f * q->d2;
    }
    case SND_FX_DRIVE: {                                                     /* 2× sovracampionato */
        float g = expf(36.0f * q->p[0] / 127.0f * 0.115129f);                /* 0…+36 dB */
        float ng = 1.0f / tanh_f(g);
        float mid = 0.5f * (fx->drv[ch] + x);
        fx->drv[ch] = x;
        float w = 0.5f * (tanh_f(g * mid) + tanh_f(g * x)) * ng;
        return x + q->d2 * (w - x);
    }
    case SND_FX_TREMOLO: {
        if (q->rate <= 0.0f) return x;                                       /* RATE 0: inudibile (SND-510) */
        float off = ch ? 0.5f * q->p[2] / 127.0f : 0.0f;
        float c = sin_cyc(fx->lfo[SND_FX_TREMOLO] + off + 0.25f);                          /* cos φ, fase iniziale 0 */
        return x * (1.0f - q->d2 * (1.0f - c) * 0.5f);
    }
    default: return x;
    }
}

static void fxpar(const dsp_eng_t *E, int base, int type, fxpar_t *q)
{
    for (int k = 0; k < 6; k++) q->p[k] = E->sm[base + 1 + k];
    q->rate = curve(CURVE_F_FX_RATE, q->p[0]);
    q->d2 = q->p[1] / 127.0f;
    if (type == SND_FX_TREMOLO && q->p[0] < 0.5f) q->rate = 0.0f;           /* RATE 0: guadagno 1 (SND-510) */
}

static void lfo_step(dsp_t *d, dsp_fx_t *fx, int type, const fxpar_t *q)
{
    float inc = q->rate * d->inv_fs * (float)DSP_BLOCK;
    if (type == SND_FX_TREMOLO) {
        fx->lfo[SND_FX_TREMOLO] += inc;
        fx->lfo[SND_FX_TREMOLO] -= floorf(fx->lfo[SND_FX_TREMOLO]);
        return;
    }
    if (type <= SND_FX_OFF || type > SND_FX_FLANGER) return;
    fx->lfo[type] += inc;
    fx->lfo[type] -= floorf(fx->lfo[type]);
    if (type == SND_FX_ENSEMBLE) {
        fx->lfo2 += curve(CURVE_F_FX_RATE, q->p[2]) * 4.0f * d->inv_fs * (float)DSP_BLOCK;
        fx->lfo2 -= floorf(fx->lfo2);
    }
}

static void phaser_coefs(dsp_t *d, dsp_fx_t *fx, const fxpar_t *q, phz_t *phz)
{
    for (int ch = 0; ch < 2; ch++) {
        float off = ch ? 0.5f * q->p[3] / 127.0f : 0.0f;
        float s0 = sin_cyc(fx->lfo[SND_FX_PHASER] + off);
        float s1 = sin_cyc(fx->lfo[SND_FX_PHASER] + off + q->rate * d->inv_fs * (float)DSP_BLOCK);
        /* spazzata 200 Hz – 4 kHz; DEPTH ne regola l'ampiezza */
        float a0 = allpass_coef(200.0f * powf(20.0f, 0.5f + 0.5f * q->d2 * s0), d->inv_fs);
        float a1 = allpass_coef(200.0f * powf(20.0f, 0.5f + 0.5f * q->d2 * s1), d->inv_fs);
        phz[ch].a0 = a0;
        phz[ch].da = (a1 - a0) / (float)DSP_BLOCK;
    }
}

/* ---- delay (SND-520…524), solo FX2 ---- */
static float delay_target(const dsp_t *d, float time_raw)
{
    int r = (int)(time_raw + 0.5f);
    float s;
    if (r <= 2) s = 60.0f / d->bpm / (float)(1 << r);                       /* 1/4, 1/8, 1/16 */
    else s = curve(CURVE_T_DELAY, time_raw);
    return clampf(s * d->fs, 1.0f, (float)(DSP_DELAY_N - 8));
}

static void delay_block(dsp_t *d, dsp_eng_t *E, const fxpar_t *q, bool active, float *L, float *R, float *outL,
                        float *outR)
{
    dsp_delay_t *dl = &E->dly;
    float tgt = delay_target(d, q->p[0]);
    float k50 = 1.0f - expf(-d->inv_fs / 0.050f);
    float fb = q->p[2] / 127.0f, mix = q->d2, spread = q->p[4] / 127.0f;
    float alp = onepole_a(curve(CURVE_F_DLYLP, q->p[3]), d->inv_fs);
    float fhp = curve(CURVE_F_DLYHP, q->p[5]);
    float ahp = fhp > 0.0f ? onepole_a(fhp, d->inv_fs) : 0.0f;
    if (dl->t_cur < 1.0f) dl->t_cur = tgt;
    for (int i = 0; i < DSP_BLOCK; i++) {
        dl->t_cur += (tgt - dl->t_cur) * k50;                               /* come un nastro */
        float wl = tap(dl->buf[0], DMASK, dl->w, dl->t_cur);
        float wr = tap(dl->buf[1], DMASK, dl->w, dl->t_cur);
        float in_l = L[i], in_r = R[i];
        if (active) {
            /* nel loop: passa-basso, passa-alto, soft clip; SPREAD incrocia i canali */
            dl->lp[0] += alp * (wl - dl->lp[0]);
            dl->lp[1] += alp * (wr - dl->lp[1]);
            float fl = dl->lp[0], fr = dl->lp[1];
            if (ahp > 0.0f) {
                dl->hp[0] += ahp * (fl - dl->hp[0]);
                dl->hp[1] += ahp * (fr - dl->hp[1]);
                fl -= dl->hp[0];
                fr -= dl->hp[1];
            }
            float cl = (1.0f - spread) * fl + spread * fr, cr = (1.0f - spread) * fr + spread * fl;
            dl->buf[0][dl->w & DMASK] = tanh_f(in_l + fb * cl);
            dl->buf[1][dl->w & DMASK] = tanh_f(in_r + fb * cr);
            outL[i] = in_l + mix * wl;                                       /* il dry resta a 1 (SND-522) */
            outR[i] = in_r + mix * wr;
        } else {
            dl->buf[0][dl->w & DMASK] = in_l;
            dl->buf[1][dl->w & DMASK] = in_r;
            outL[i] = in_l;
            outR[i] = in_r;
        }
        dl->w++;
    }
    for (int c = 0; c < 2; c++) { dl->lp[c] = undenorm(dl->lp[c]); dl->hp[c] = undenorm(dl->hp[c]); }
}

void fx_process(dsp_t *d, dsp_eng_t *E, int slot, float *L, float *R)
{
    dsp_fx_t *fx = &E->fx[slot];
    int base = slot ? SND_P_FX2TYPE : SND_P_FX1TYPE;
    int type = E->p[base];
    if (slot == 0 && type > SND_FX_TREMOLO) type = SND_FX_TREMOLO;         /* SND-502 */
    if (type != fx->type) {
        fx->old = fx->type;
        fx->type = (uint8_t)type;
        fx->xf = 0.0f;
        if (type == SND_FX_TREMOLO) fx->lfo[SND_FX_TREMOLO] = 0.0f;                        /* fase iniziale 0 */
        if (type == SND_FX_PHASER) { memset(fx->ap, 0, sizeof fx->ap); fx->pfb[0] = fx->pfb[1] = 0.0f; }
    }
    fxpar_t q;
    fxpar(E, base, type, &q);
    int old = fx->xf < 1.0f ? fx->old : type;
    fxpar_t qo = q;
    if (old != type) fxpar(E, base, old, &qo);

    float dlL[DSP_BLOCK], dlR[DSP_BLOCK];
    bool uses_delay = slot == 1;
    if (uses_delay) {
        bool on = type == SND_FX_DELAY || old == SND_FX_DELAY;
        delay_block(d, E, &q, on, L, R, dlL, dlR);
    }

    phz_t phz[2] = { { 0 } }, phzo[2] = { { 0 } };
    if (type == SND_FX_PHASER) phaser_coefs(d, fx, &q, phz);
    if (old == SND_FX_PHASER && old != type) phaser_coefs(d, fx, &qo, phzo);

    float xstep = 1.0f / (0.010f * d->fs);
    for (int i = 0; i < DSP_BLOCK; i++) {
        float in[2] = { L[i], R[i] };
        float y[2], fl_wet[2] = { 0.0f, 0.0f };
        for (int ch = 0; ch < 2; ch++) {
            float yn = type == SND_FX_DELAY ? (ch ? dlR[i] : dlL[i])
                     : fx_one(d, fx, type, &q, ch, in[ch], i, phz, fl_wet);
            if (fx->xf < 1.0f && old != type) {
                float yo = old == SND_FX_DELAY ? (ch ? dlR[i] : dlL[i])
                         : fx_one(d, fx, old, &qo, ch, in[ch], i, phzo, fl_wet);
                yn = yo + (yn - yo) * fx->xf;
            }
            y[ch] = yn;
        }
        /* la linea modulata registra l'ingresso, più il feedback se suona il flanger */
        float ffb = (type == SND_FX_FLANGER) ? 0.9f * q.p[2] / 127.0f : 0.0f;
        fx->line[0][fx->lw & LMASK] = in[0] + ffb * fl_wet[0];
        fx->line[1][fx->lw & LMASK] = in[1] + ffb * fl_wet[1];
        fx->lw++;
        if (fx->xf < 1.0f) { fx->xf += xstep; if (fx->xf > 1.0f) fx->xf = 1.0f; }
        L[i] = y[0];
        R[i] = y[1];
    }
    lfo_step(d, fx, type, &q);
    if (old != type) lfo_step(d, fx, old, &qo);
    for (int ch = 0; ch < 2; ch++) {
        fx->pfb[ch] = undenorm(fx->pfb[ch]);
        for (int s = 0; s < 6; s++) { fx->ap[ch][s][0] = undenorm(fx->ap[ch][s][0]); fx->ap[ch][s][1] = undenorm(fx->ap[ch][s][1]); }
    }
}
