/* dsp.c — pool di voci, motori Sound e Bass, modelli VA e FM, inviluppi, LFO, matrice, filtro e
 * catena d'uscita (specifica 20, §1, §4–§6, §8–§10). Il Reed Piano sta in rp.c, gli effetti in
 * fx.c, il riverbero in reverb.c.
 */
#include "dsp_int.h"

/* ---------------------------------------------------------------- inizializzazione ---- */

static void lfo_start(dsp_lfo_t *l, uint32_t *rng)
{
    l->phase = 0.0f;
    l->a = rnd_bi(rng);
    l->b = rnd_bi(rng);
    l->done = 0;
}

void dsp_init(dsp_t *d, float fs, uint32_t seed)
{
    memset(d, 0, sizeof *d);
    if (fs < 8000.0f) fs = 8000.0f;
    if (fs > (float)DSP_FS_MAX) fs = (float)DSP_FS_MAX;
    d->fs = fs;
    d->inv_fs = 1.0f / fs;
    float dt = (float)DSP_BLOCK / fs;
    d->k_sm5 = 1.0f - expf(-dt / 0.005f);
    d->k_sm20 = 1.0f - expf(-dt / 0.020f);
    d->rng = seed ? seed : 1u;
    d->bpm = 120.0f;
    d->master = 75;
    d->bass_vol = 75;
    d->vel_sense = 1;
    d->g_master = (75.0f / 99.0f) * (75.0f / 99.0f);
    d->g_bass = d->g_master;
    for (int e = 0; e < DSP_ENGINES; e++) {
        dsp_eng_t *E = &d->eng[e];
        snd_patch_init(E->p, SND_MODEL_VA);
        for (int i = 0; i < DSP_NPAR; i++) E->sm[i] = (float)E->p[i];
        E->max_voices = e == DSP_BASS ? 1 : DSP_VOICES;       /* SND-022 */
        E->last_note = -1;
        for (int n = 0; n < 4; n++) lfo_start(&E->lfo[n], &d->rng);
        fx_reset(&E->fx[0]);
        fx_reset(&E->fx[1]);
        fx_delay_reset(&E->dly);
    }
    rev_reset(&d->rev, fs);
}

void dsp_reseed(dsp_t *d, uint32_t seed) { d->rng = seed ? seed : 1u; }

void dsp_set_bank(dsp_t *d, const smp_bank_t *bank) { d->bank = bank; }

/* ---------------------------------------------------------------- inviluppi (§8.1) ---- */

static float env_run(dsp_env_t *e, const uint8_t *patch, int n, float tscale, float s_mod, float dt)
{
    const uint8_t *p = &patch[SND_P_E(n, 0)];
    switch (e->stage) {
    case DSP_ENV_ATT:
        e->level += dt / (curve_i(CURVE_T_ATT, p[0]) * tscale);
        if (e->level >= 1.0f) {
            e->level = 1.0f;
            e->t = 0.0f;
            e->stage = p[1] ? DSP_ENV_HOLD : DSP_ENV_DEC;
        }
        break;
    case DSP_ENV_HOLD:
        e->t += dt;
        if (e->t >= curve_i(CURVE_T_HOLD, p[1]) * tscale) e->stage = DSP_ENV_DEC;
        break;
    case DSP_ENV_DEC: {
        float s = clampf(((float)p[3] + s_mod) * (1.0f / 127.0f), 0.0f, 1.0f);
        e->level = s + (e->level - s) * expf(-DSP_LN60 * dt / (curve_i(CURVE_T_DEC, p[2]) * tscale));
        break;
    }
    case DSP_ENV_REL:
        e->level *= expf(-DSP_LN60 * dt / (curve_i(CURVE_T_DEC, p[4]) * tscale));
        if (e->level < 1e-5f) { e->level = 0.0f; e->stage = DSP_ENV_IDLE; }
        break;
    default: break;
    }
    return e->level;
}

/* ---------------------------------------------------------------- LFO (§8.2) ---- */

static float lfo_value(const dsp_lfo_t *l, int shape)
{
    float p = l->phase;
    switch (shape) {
    case SND_LFO_SINE: return sin_cyc(p);
    case SND_LFO_TRI:  return p < 0.25f ? 4.0f * p : p < 0.75f ? 2.0f - 4.0f * p : 4.0f * p - 4.0f;
    case SND_LFO_SQU:  return p < 0.5f ? 1.0f : -1.0f;
    case SND_LFO_SAW:  return 2.0f * p - 1.0f;         /* sale piano, scende di colpo */
    case SND_LFO_SAWN: return 1.0f - 2.0f * p;
    case SND_LFO_RAND: return l->a + (l->b - l->a) * p;  /* raccordato linearmente */
    case SND_LFO_SH:   return l->a;                      /* a gradini */
    default: return 0.0f;
    }
}

static void lfo_advance(dsp_lfo_t *l, int mode, float f, float dt, uint32_t *rng)
{
    if (l->done) return;
    l->phase += f * dt;
    if (l->phase >= 1.0f) {
        if (mode == SND_LFOM_ONESHOT) { l->phase = 0.99999f; l->done = 1; return; }
        l->phase -= floorf(l->phase);
        l->a = l->b;
        l->b = rnd_bi(rng);
    }
}

static void engine_lfos(dsp_t *d, dsp_eng_t *E, float dt)
{
    for (int n = 0; n < 4; n++) {
        int mode = E->p[SND_P_L(n + 1, 2)];
        if (mode != SND_LFOM_FREE && mode != SND_LFOM_MONO) continue;
        int shape = E->p[SND_P_L(n + 1, 0)];
        float f = curve(CURVE_F_LFO, E->sm[SND_P_L(n + 1, 1)] + E->lfo_mod[n] * 127.0f);
        E->lfo_out[n] = lfo_value(&E->lfo[n], shape);
        lfo_advance(&E->lfo[n], mode, f, dt, &d->rng);
    }
}

/* ---------------------------------------------------------------- matrice (§8.3) ---- */

static float amt_curve(float r)
{
    float x = r < 64.0f ? (r - 64.0f) / 64.0f : (r - 64.0f) / 63.0f;
    return x < 0.0f ? -x * x : x * x;                    /* quadratica, ±1 agli estremi (SND-420) */
}

static void matrix_eval(const uint8_t *p, const float *sm, const float *src, float *dst)
{
    float amt[8];
    int s[8], t[8];
    for (int i = 0; i < 8; i++) {
        s[i] = p[SND_P_M(i + 1, 0)];
        t[i] = p[SND_P_M(i + 1, 1)];
        amt[i] = amt_curve(sm[SND_P_M(i + 1, 2)]);
    }
    /* SND-421: prima gli slot che puntano a MOD7/MOD8, con le quantità non modulate */
    float m7 = 0.0f, m8 = 0.0f;
    for (int i = 0; i < 8; i++) {
        if (t[i] == SND_MD_MOD7) m7 += src[s[i]] * amt[i];
        else if (t[i] == SND_MD_MOD8) m8 += src[s[i]] * amt[i];
    }
    float a7 = clampf(amt[6] + m7, -1.0f, 1.0f), a8 = clampf(amt[7] + m8, -1.0f, 1.0f);
    for (int i = 0; i < 8; i++) {
        if (t[i] == SND_MD_OFF || t[i] == SND_MD_MOD7 || t[i] == SND_MD_MOD8) continue;
        float a = i == 6 ? a7 : i == 7 ? a8 : amt[i];
        dst[t[i]] += src[s[i]] * a;
    }
}

/* ---------------------------------------------------------------- controllo per voce ---- */

static bool newest_of(const dsp_t *d, const dsp_voice_t *v)
{
    for (int i = 0; i < DSP_VOICES; i++) {
        const dsp_voice_t *w = &d->voice[i];
        if (w != v && w->state != DSP_V_FREE && w->engine == v->engine && w->age > v->age) return false;
    }
    return true;
}

/* calcola gli obiettivi del blocco per la voce (frequenza di controllo, SND-040) */
static void voice_control(dsp_t *d, dsp_voice_t *v, const uint8_t *p, const float *sm, bool is_tail)
{
    dsp_eng_t *E = &d->eng[v->engine];
    const float dt = (float)DSP_BLOCK * d->inv_fs;
    int model = p[SND_P_MODEL];

    /* 1. sorgenti: inviluppi e LFO del blocco, con le modulazioni del blocco precedente */
    float env[4], lfo[4];
    for (int n = 0; n < 4; n++) {
        float ts = expf(4.0f * 0.693147f * clampf(v->mod_envt[n], -2.0f, 2.0f));   /* SND-403 */
        env[n] = env_run(&v->env[n], p, n + 1, ts, v->mod_envs[n] * 127.0f, dt);
    }
    for (int n = 0; n < 4; n++) {
        int mode = p[SND_P_L(n + 1, 2)], shape = p[SND_P_L(n + 1, 0)];
        if (mode == SND_LFOM_FREE || mode == SND_LFOM_MONO) { lfo[n] = E->lfo_out[n]; continue; }
        float f = curve(CURVE_F_LFO, sm[SND_P_L(n + 1, 1)] + v->mod_lfo[n] * 127.0f);
        lfo[n] = lfo_value(&v->lfo[n], shape);
        lfo_advance(&v->lfo[n], mode, f, dt, &d->rng);
    }

    /* 2. matrice */
    float src[SND_MS_COUNT] = { 0 };
    src[SND_MS_KEYTRACK] = ((float)v->note - 60.0f) / 60.0f;
    src[SND_MS_VELOCITY] = v->v;
    src[SND_MS_RANDOM] = v->rnd;
    for (int n = 0; n < 4; n++) { src[SND_MS_LFO1 + n] = lfo[n]; src[SND_MS_ENV1 + n] = env[n]; }
    src[SND_MS_WHEEL] = E->wheel;
    src[SND_MS_BEND] = E->bend;
    float dst[SND_MD_COUNT] = { 0 };
    matrix_eval(p, sm, src, dst);
    for (int n = 0; n < 4; n++) {
        v->mod_envt[n] = dst[SND_MD_ENV1T + 2 * n];
        v->mod_envs[n] = dst[SND_MD_ENV1S + 2 * n];
        v->mod_lfo[n] = dst[SND_MD_LFO1 + n];
    }
    if (!is_tail && newest_of(d, v))                     /* SND-422: LFO condivisi */
        for (int n = 0; n < 4; n++) E->lfo_mod[n] = dst[SND_MD_LFO1 + n];

    /* 3. intonazione (SND-201…203) */
    float glide_raw = sm[SND_P_GLIDE] + dst[SND_MD_GLIDE] * 127.0f;
    if (glide_raw > 0.5f && v->glide != 0.0f) {
        v->glide *= expf(-DSP_LN60 * dt / curve(CURVE_T_GLIDE, glide_raw));
        if (fabsf(v->glide) < 1e-4f) v->glide = 0.0f;
    } else v->glide = 0.0f;
    float bend = E->bend * (float)p[SND_P_BENDRANGE];
    float pitch = (float)v->note + bend + v->glide + dst[SND_MD_PITCH] * 12.0f;

    if (model == SND_MODEL_RP) {                         /* SND-360: in RP solo PITCH, VOLUME, PAN */
        v->inc[0] = pitch;                               /* rp_render legge l'altezza da qui */
    } else if (model == SND_MODEL_SMP) {                 /* SND-373: passo di lettura del campione */
        v->inc[0] = smp_ratio(d, v, sm, pitch);
    } else {
        for (int o = 0; o < 4; o++) {
            float semi = sm[SND_P_O(o + 1, 1)] - 64.0f;
            float det = (sm[SND_P_O(o + 1, 2)] - 64.0f) / 64.0f;
            float po;
            if (o == 3 && p[SND_P_O4KT] == 0)            /* O4 FIXED (SND-202) */
                po = 60.0f + semi + det + dst[SND_MD_PITCH] * 12.0f + dst[SND_MD_OSC1 + 9] * 12.0f;
            else
                po = pitch + semi + det + dst[SND_MD_OSC1 + 3 * o] * 12.0f;
            v->inc[o] = clampf(note_hz(po) * d->inv_fs, 0.0f, 0.49f);
        }
    }

    /* 4. sorgenti del modello */
    if (model == SND_MODEL_VA) {
        for (int o = 0; o < 4; o++) {
            int shape = p[SND_P_O(o + 1, 0)];
            v->og_t[o] = shape == SND_SHAPE_OFF ? 0.0f
                       : curve(CURVE_G_OSC, sm[SND_P_O(o + 1, 4)] + dst[SND_MD_GAIN1 + 3 * o] * 127.0f);
            float pwmod = dst[o == 3 ? SND_MD_PW4FB : SND_MD_PW1 + 3 * o];
            v->duty_t[o] = clampf((sm[SND_P_O(o + 1, 3)] + pwmod * 127.0f) / 127.0f, 0.0f, 1.0f);
        }
    } else if (model == SND_MODEL_FM) {                  /* SND-302, SND-315 */
        for (int o = 0; o < 4; o++) {
            float lv = sm[SND_P_O(o + 1, 3)] + dst[SND_MD_GAIN1 + 3 * o] * 127.0f;
            if (o < 3) lv += dst[SND_MD_PW1 + 3 * o] * 127.0f;
            lv = clampf(lv, 0.0f, 127.0f) / 127.0f;
            float s = sm[SND_P_O(o + 1, 4)] / 127.0f;
            v->og_t[o] = lv * lv * ((1.0f - s) + s * v->v);
        }
        v->duty_t[3] = clampf(sm[SND_P_O4FB] + dst[SND_MD_PW4FB] * 127.0f, 0.0f, 127.0f);   /* feedback raw */
    }
    v->noise_t = model == SND_MODEL_RP ? 0.0f
               : clampf((sm[SND_P_NOISE] + dst[SND_MD_NOISE] * 127.0f) / 127.0f, 0.0f, 1.0f);

    /* 5. filtro (SND-210…213) e passa-alto di tastiera (SND-215) */
    if (model != SND_MODEL_RP && p[SND_P_FTYPE] != SND_FT_OFF) {
        float c = sm[SND_P_CUTOFF] + 127.0f * env[0] * sm[SND_P_FENV] / 127.0f + sm[SND_P_FVELO] * v->v * 0.5f
                + (sm[SND_P_FKT] / 127.0f) * 1.058f * ((float)v->note - 60.0f) + dst[SND_MD_CUTOFF] * 127.0f;
        float f = clampf(curve(CURVE_F_CUT, c), 10.0f, 0.45f * d->fs);
        float g = tanf(DSP_PI * f * d->inv_fs);
        float k = curve(CURVE_K_RES, sm[SND_P_RESONANCE] + dst[SND_MD_Q] * 127.0f);
        if (k < 0.002f) k = -0.04f;                      /* al massimo auto-oscilla (SND-212) */
        float a1 = 1.0f / (1.0f + g * (g + k));
        v->t_a1 = a1;
        v->t_a2 = g * a1;
        v->t_a3 = g * g * a1;
        v->t_k = k;
    }
    if (model != SND_MODEL_RP && p[SND_P_HIGHPASS] > 0) {
        float f = curve(CURVE_F_HP, sm[SND_P_HIGHPASS])
                * expf((sm[SND_P_HPKT] / 127.0f) * ((float)v->note - 60.0f) * DSP_LN2_12);
        v->hp_a = onepole_a(clampf(f, 5.0f, 0.45f * d->fs), d->inv_fs);
    } else v->hp_a = 0.0f;

    /* 6. ampiezza e pan (SND-220, SND-221) */
    float amp;
    float gvol = curve(CURVE_G_VOL, sm[SND_P_GAIN] + dst[SND_MD_VOLUME] * 127.0f);
    if (model == SND_MODEL_RP) amp = gvol;               /* l'inviluppo lo fa il modello (SND-360) */
    else {
        float s = sm[SND_P_GVELO] / 127.0f;
        amp = env[1] * gvol * ((1.0f - s) + s * v->v * v->v);
    }
    float th = clampf(sm[SND_P_PAN] + dst[SND_MD_PAN] * 127.0f, 0.0f, 127.0f) / 127.0f * (0.5f * DSP_PI);
    v->gl_t = amp * cosf(th);
    v->gr_t = amp * sinf(th);
}

/* ---------------------------------------------------------------- oscillatori VA (§5) ---- */

static inline float blep(float t, float dt)
{
    if (t < dt) { t /= dt; return t + t - t * t - 1.0f; }
    if (t > 1.0f - dt) { t = (t - 1.0f) / dt; return t * t + t + t + 1.0f; }
    return 0.0f;
}

static inline float blamp(float t, float dt)
{
    if (t < dt) { float x = 1.0f - t / dt; return x * x * x * (1.0f / 6.0f); }
    if (t > 1.0f - dt) { float x = 1.0f + (t - 1.0f) / dt; return x * x * x * (1.0f / 6.0f); }
    return 0.0f;
}

static inline float osc_va(int shape, float t, float dt, float duty)
{
    switch (shape) {
    case SND_SHAPE_SAW:
        return 2.0f * t - 1.0f - blep(t, dt);
    case SND_SHAPE_PULSE: {
        float y = (t < duty ? 1.0f : -1.0f) + blep(t, dt);
        float t2 = t - duty;
        if (t2 < 0.0f) t2 += 1.0f;
        y -= blep(t2, dt);
        return y - (2.0f * duty - 1.0f);                 /* senza componente continua (SND-251) */
    }
    case SND_SHAPE_TRI: {
        float y = t < 0.5f ? 4.0f * t - 1.0f : 3.0f - 4.0f * t;
        float t2 = t + 0.5f;
        if (t2 >= 1.0f) t2 -= 1.0f;
        return y + 8.0f * dt * (blamp(t, dt) - blamp(t2, dt));
    }
    default: return 0.0f;
    }
}

static inline float pink_step(float *b, float w)
{
    b[0] = 0.99765f * b[0] + w * 0.0990460f;
    b[1] = 0.96300f * b[1] + w * 0.2965164f;
    b[2] = 0.57000f * b[2] + w * 1.0526913f;
    return (b[0] + b[1] + b[2] + w * 0.1848f) * 0.25f;
}

/* filtro SVF in topologia TPT; lo stato del passa-banda satura oltre ±0,8 e resta sotto ±1,05 (SND-212) */
static inline float sat1(float x)
{
    if (x > 0.8f) { float u = x - 0.8f; return 0.8f + u / (1.0f + 4.0f * u); }
    if (x < -0.8f) { float u = -0.8f - x; return -0.8f - u / (1.0f + 4.0f * u); }
    return x;
}

/* ---------------------------------------------------------------- rendering di una voce ---- */

static const uint8_t FM_MODS[8][4] = {     /* SND-310: bit j = l'operatore j+1 modula l'operatore i+1 */
    { 0x2, 0x4, 0x8, 0 },                  /* 1: 4 → 3 → 2 → 1 */
    { 0xE, 0, 0, 0 },                      /* 2: 2, 3, 4 → 1 */
    { 0x4, 0x8, 0, 0 },                    /* 3: 4 → 2, 3 → 1 */
    { 0x2, 0xC, 0, 0 },                    /* 4: 4 → 2, 3 → 2, 2 → 1 */
    { 0x2, 0, 0x8, 0 },                    /* 5: 4 → 3, 2 → 1 */
    { 0x6, 0, 0x8, 0 },                    /* 6: 4 → 3 → 1, 2 → 1 */
    { 0x8, 0x8, 0x8, 0 },                  /* 7: 4 → 1, 4 → 2, 4 → 3 */
    { 0, 0, 0, 0 },                        /* 8: nessuna modulazione */
};
static const uint8_t FM_CARRIERS[8] = { 0x1, 0x1, 0x3, 0x1, 0x5, 0x1, 0x7, 0xF };

/* rende 16 campioni della voce e li somma nel bus del motore; restituisce il picco */
static float voice_render(dsp_t *d, dsp_voice_t *v, const uint8_t *p, const float *sm, float *bl, float *br,
                          float fade, float fstep)
{
    int model = p[SND_P_MODEL];
    float src[DSP_BLOCK];
    const float k16 = 1.0f / (float)DSP_BLOCK;

    if (model == SND_MODEL_RP) {
        rp_render(d, v, p, sm, v->inc[0], src);
    } else {
        float og[4], dog[4];
        for (int o = 0; o < 4; o++) { og[o] = v->og[o]; dog[o] = (v->og_t[o] - v->og[o]) * k16; }
        float ng = v->noise_g, dng = (v->noise_t - v->noise_g) * k16;
        bool pink = p[SND_P_PINK] != 0;
        if (model == SND_MODEL_VA) {
            int shape[4];
            float duty[4], dduty[4];                                  /* PWM interpolata come og: a gradini ronzava */
            for (int o = 0; o < 4; o++) {
                shape[o] = p[SND_P_O(o + 1, 0)];
                duty[o] = v->duty[o];
                dduty[o] = (v->duty_t[o] - duty[o]) * k16;
            }
            bool sync = p[SND_P_O4SYNC] != 0;
            for (int i = 0; i < DSP_BLOCK; i++) {
                float x = 0.0f;
                for (int o = 0; o < 4; o++) {
                    if (shape[o] == SND_SHAPE_OFF) continue;
                    x += og[o] * osc_va(shape[o], v->ph[o], v->inc[o], duty[o]);
                    v->ph[o] += v->inc[o];
                    if (v->ph[o] >= 1.0f) {
                        v->ph[o] -= 1.0f;
                        /* hard sync: l'OSC4 riparte con l'OSC3 alla posizione frazionaria del reset
                         * (SND-253; la correzione BLEP del salto non c'è ancora) */
                        if (o == 2 && sync) v->ph[3] = v->ph[2] / v->inc[2] * v->inc[3];
                    }
                    og[o] += dog[o];
                    duty[o] += dduty[o];
                }
                if (ng > 0.0f || dng > 0.0f) {
                    float w = rnd_bi(&d->rng);
                    x += ng * (pink ? pink_step(v->pink, w) : w);
                }
                ng += dng;
                src[i] = 1.5f * tanh_f(x * (1.0f / 1.5f));          /* SND-265 */
            }
            for (int o = 0; o < 4; o++) v->duty[o] = v->duty_t[o];
        } else if (model == SND_MODEL_SMP) {                         /* campionatore (§7b) */
            smp_render(v, src);
        } else {                                                     /* FM (§6) */
            int alg = p[SND_P_FMALG] & 7;
            const uint8_t *mods = FM_MODS[alg];
            uint8_t car = FM_CARRIERS[alg];
            float beta = 0.75f * v->duty_t[3] / 127.0f;              /* SND-304, in cicli */
            for (int i = 0; i < DSP_BLOCK; i++) {
                float o[4];
                o[3] = og[3] * sin_cyc(v->ph[3] + beta * (v->fb1 + v->fb2) * 0.5f);
                v->fb2 = v->fb1;
                v->fb1 = o[3];
                for (int k = 2; k >= 0; k--) {
                    float m = 0.0f;
                    for (int j = k + 1; j < 4; j++) if (mods[k] >> j & 1) m += o[j];
                    o[k] = og[k] * sin_cyc(v->ph[k] + 2.0f * m);        /* I_max = 4π = 2 cicli (SND-303) */
                }
                float x = 0.0f;
                for (int k = 0; k < 4; k++) {
                    if (car >> k & 1) x += o[k];
                    v->ph[k] += v->inc[k];
                    if (v->ph[k] >= 1.0f) v->ph[k] -= 1.0f;
                    og[k] += dog[k];
                }
                if (ng > 0.0f || dng > 0.0f) {
                    float w = rnd_bi(&d->rng);
                    x += ng * (pink ? pink_step(v->pink, w) : w);
                }
                ng += dng;
                src[i] = x;
            }
        }
        for (int o = 0; o < 4; o++) v->og[o] = v->og_t[o];
        v->noise_g = v->noise_t;

        /* filtro con coefficienti interpolati nel blocco */
        int ft = p[SND_P_FTYPE];
        if (ft != SND_FT_OFF) {
            float a1 = v->f_a1, a2 = v->f_a2, a3 = v->f_a3, k = v->f_k;
            float da1 = (v->t_a1 - a1) * k16, da2 = (v->t_a2 - a2) * k16, da3 = (v->t_a3 - a3) * k16;
            float dk = (v->t_k - k) * k16;
            float ic1 = v->ic1, ic2 = v->ic2;
            for (int i = 0; i < DSP_BLOCK; i++) {
                a1 += da1; a2 += da2; a3 += da3; k += dk;
                float x = src[i];
                float v3 = x - ic2;
                float v1 = a1 * ic1 + a2 * v3;
                float v2 = ic2 + a2 * ic1 + a3 * v3;
                ic1 = sat1(2.0f * v1 - ic1);
                ic2 = 2.0f * v2 - ic2;
                src[i] = ft == SND_FT_LP ? v2 : ft == SND_FT_BP ? v1 : x - k * v1 - v2;
            }
            v->ic1 = undenorm(ic1);
            v->ic2 = undenorm(ic2);
            v->f_a1 = v->t_a1; v->f_a2 = v->t_a2; v->f_a3 = v->t_a3; v->f_k = v->t_k;
        }
        if (v->hp_a > 0.0f) {
            float lp = v->hp_lp, a = v->hp_a;
            for (int i = 0; i < DSP_BLOCK; i++) { lp += a * (src[i] - lp); src[i] -= lp; }
            v->hp_lp = undenorm(lp);
        }
    }

    /* VCA, pan e dissolvenza (slot di coda) */
    float gl = v->gl, gr = v->gr, dgl = (v->gl_t - gl) * k16, dgr = (v->gr_t - gr) * k16, pk = 0.0f;
    for (int i = 0; i < DSP_BLOCK; i++) {
        gl += dgl;
        gr += dgr;
        float s = src[i] * fade;
        fade -= fstep;
        if (fade < 0.0f) fade = 0.0f;
        float l = s * gl, r = s * gr;
        bl[i] += l;
        br[i] += r;
        float a = fabsf(l) + fabsf(r);
        if (a > pk) pk = a;
    }
    v->gl = v->gl_t;
    v->gr = v->gr_t;
    return pk;
}

/* ---------------------------------------------------------------- allocazione (§1.3) ---- */

static int engine_voices(const dsp_t *d, int e)
{
    int n = 0;
    for (int i = 0; i < DSP_VOICES; i++) if (d->voice[i].state != DSP_V_FREE && d->voice[i].engine == e) n++;
    return n;
}

/* sposta la voce in una coda con la copia della patch corrente: fade_s > 0 la dissolve in quel tempo
 * (2 ms per lo stealing, SND-024), fade_s = 0 la lascia finire il rilascio */
static void to_tail(dsp_t *d, dsp_voice_t *v, float fade_s)
{
    int best = 0;
    for (int i = 0; i < DSP_TAILS; i++) {
        if (!d->tail[i].on) { best = i; break; }
        if (d->tail[i].age < d->tail[best].age) best = i;
    }
    dsp_tail_t *t = &d->tail[best];
    t->v = *v;
    memcpy(t->p, d->eng[v->engine].p, DSP_NPAR);
    memcpy(t->sm, d->eng[v->engine].sm, sizeof t->sm);
    t->on = 1;
    t->fade = 1.0f;
    t->step = fade_s > 0.0f ? 1.0f / (fade_s * d->fs) : 0.0f;
    t->age = ++d->age;
}

static dsp_voice_t *oldest(dsp_t *d, int e, int state)
{
    dsp_voice_t *best = NULL;
    for (int i = 0; i < DSP_VOICES; i++) {
        dsp_voice_t *v = &d->voice[i];
        if (v->state != state || (e >= 0 && v->engine != e)) continue;
        if (!best || v->age < best->age) best = v;
    }
    return best;
}

/* SND-023: restituisce la voce per la nota; *reuse = stessa nota già in suono sul motore */
static dsp_voice_t *alloc_voice(dsp_t *d, int e, uint8_t note, bool *reuse)
{
    *reuse = false;
    for (int i = 0; i < DSP_VOICES; i++) {                                  /* 1 */
        dsp_voice_t *v = &d->voice[i];
        if (v->state != DSP_V_FREE && v->engine == e && v->note == note) { *reuse = true; return v; }
    }
    dsp_voice_t *v = NULL;
    if (engine_voices(d, e) >= d->eng[e].max_voices) {                      /* 2 */
        v = oldest(d, e, DSP_V_RELEASED);
        if (!v) v = oldest(d, e, DSP_V_HELD);
    }
    if (!v)
        for (int i = 0; i < DSP_VOICES && !v; i++) if (d->voice[i].state == DSP_V_FREE) v = &d->voice[i];   /* 3 */
    if (!v) {                                                               /* 4 */
        for (int i = 0; i < DSP_VOICES; i++) {
            dsp_voice_t *w = &d->voice[i];
            if (w->state == DSP_V_RELEASED && (!v || w->peak < v->peak)) v = w;
        }
    }
    if (!v) v = oldest(d, DSP_SOUND, DSP_V_HELD);                           /* 5 */
    if (!v) return NULL;
    if (v->state != DSP_V_FREE) { to_tail(d, v, 0.002f); d->steals++; }
    return v;
}

static void voice_start(dsp_t *d, dsp_voice_t *v, int e, uint8_t note, uint8_t vel, bool reuse, bool legato_env,
                        float glide)
{
    dsp_eng_t *E = &d->eng[e];
    int model = E->p[SND_P_MODEL];
    if (reuse && model == SND_MODEL_SMP && v->state != DSP_V_FREE) {
        /* il campione riparte da capo: la voce vecchia sfuma in coda in 2 ms invece di saltare (clic) */
        to_tail(d, v, 0.002f);
        reuse = false;
    }
    if (!reuse) {
        memset(v, 0, sizeof *v);
        for (int o = 0; o < 4; o++)                       /* SND-252, SND-305 */
            v->ph[o] = model == SND_MODEL_VA ? (rnd_bi(&d->rng) + 1.0f) * 0.5f : 0.0f;
        if (model == SND_MODEL_VA && E->p[SND_P_O4SYNC]) v->ph[3] = 0.0f;
        v->ic1 = 1e-3f;                                   /* innesco per l'auto-oscillazione */
    } else if (model == SND_MODEL_FM) {
        for (int o = 0; o < 4; o++) v->ph[o] = 0.0f;
    }
    v->state = DSP_V_HELD;
    v->engine = (uint8_t)e;
    v->note = note;
    v->vel = vel;
    v->v = (float)vel / 127.0f;
    v->sustained = 0;
    v->age = ++d->age;
    v->rnd = rnd_bi(&d->rng);
    v->glide = glide;
    v->quiet = 0.0f;
    if (legato_env) {                                     /* POLY LEGATO: niente attacco (SND-204) */
        const dsp_voice_t *src = NULL;
        for (int i = 0; i < DSP_VOICES; i++) {
            const dsp_voice_t *w = &d->voice[i];
            if (w != v && w->state == DSP_V_HELD && w->engine == e && (!src || w->age > src->age)) src = w;
        }
        for (int n = 0; n < 4; n++) {
            v->env[n].level = src ? src->env[n].level : v->env[n].level;
            v->env[n].stage = DSP_ENV_DEC;
        }
    } else {
        for (int n = 0; n < 4; n++) { v->env[n].stage = DSP_ENV_ATT; v->env[n].t = 0.0f; }   /* dal livello corrente */
    }
    for (int n = 0; n < 4; n++) {
        int mode = E->p[SND_P_L(n + 1, 2)];
        if (mode == SND_LFOM_RESET || mode == SND_LFOM_ONESHOT) lfo_start(&v->lfo[n], &d->rng);
    }
    if (model == SND_MODEL_RP) rp_note_on(d, v, E->sm);
    else if (model == SND_MODEL_SMP) smp_note_on(d, v, E->p);
}

static void voice_release(dsp_t *d, dsp_voice_t *v)
{
    if (v->state != DSP_V_HELD) return;
    v->state = DSP_V_RELEASED;
    v->sustained = 0;
    for (int n = 0; n < 4; n++) if (v->env[n].stage != DSP_ENV_IDLE) v->env[n].stage = DSP_ENV_REL;
    if (d->eng[v->engine].p[SND_P_MODEL] == SND_MODEL_RP) rp_note_off(d, v, d->eng[v->engine].sm);
}

static dsp_voice_t *mono_voice(dsp_t *d, int e)
{
    dsp_voice_t *best = NULL;
    for (int i = 0; i < DSP_VOICES; i++) {
        dsp_voice_t *v = &d->voice[i];
        if (v->state != DSP_V_FREE && v->engine == e && (!best || v->age > best->age)) best = v;
    }
    return best;
}

static void held_push(dsp_eng_t *E, uint8_t note)
{
    for (int i = 0; i < E->n_held; i++) if (E->held[i] == note) return;
    if (E->n_held == STAME_COUNT(E->held)) {
        memmove(E->held, E->held + 1, STAME_COUNT(E->held) - 1);
        E->n_held--;
    }
    E->held[E->n_held++] = note;
}

static void held_remove(dsp_eng_t *E, uint8_t note)
{
    for (int i = 0; i < E->n_held; i++)
        if (E->held[i] == note) {
            memmove(E->held + i, E->held + i + 1, (size_t)(E->n_held - i - 1));
            E->n_held--;
            return;
        }
}

/* ---------------------------------------------------------------- eventi (§1.4) ---- */

void dsp_note_on(dsp_t *d, dsp_engine e, uint8_t note, uint8_t vel)
{
    if (e >= DSP_ENGINES || note > 127) return;
    if (vel == 0) { dsp_note_off(d, e, note); return; }
    if (!d->vel_sense) vel = 100;                         /* SND-222 */
    dsp_eng_t *E = &d->eng[e];
    int mode = E->p[SND_P_GLIDEMODE];
    bool first = E->n_held == 0;
    if (first)                                            /* LFO MONO: primo tasto dopo il silenzio */
        for (int n = 0; n < 4; n++)
            if (E->p[SND_P_L(n + 1, 2)] == SND_LFOM_MONO) lfo_start(&E->lfo[n], &d->rng);
    float glide = 0.0f;
    if (E->p[SND_P_GLIDE] > 0 && E->last_note >= 0) glide = (float)E->last_note - (float)note;

    if (mode == SND_GLIDE_MONO || mode == SND_GLIDE_MONO_LEGATO) {
        dsp_voice_t *v = mono_voice(d, e);
        if (v) {
            float g = E->p[SND_P_GLIDE] > 0 ? (float)v->note + v->glide - (float)note : 0.0f;
            bool legato = mode == SND_GLIDE_MONO_LEGATO && !first && v->state == DSP_V_HELD;
            if (legato) {                                 /* stessa voce, inviluppi avanti */
                v->note = note;
                v->glide = g;
                v->age = ++d->age;
            } else {
                voice_start(d, v, e, note, vel, true, false, g);
            }
        } else {
            bool reuse;
            v = alloc_voice(d, e, note, &reuse);
            if (v) voice_start(d, v, e, note, vel, reuse, false, glide);
        }
    } else {
        bool reuse;
        dsp_voice_t *v = alloc_voice(d, e, note, &reuse);
        if (v) voice_start(d, v, e, note, vel, reuse, mode == SND_GLIDE_POLY_LEGATO && !first, glide);
    }
    held_push(E, note);
    E->last_note = note;
}

void dsp_note_off(dsp_t *d, dsp_engine e, uint8_t note)
{
    if (e >= DSP_ENGINES) return;
    dsp_eng_t *E = &d->eng[e];
    held_remove(E, note);
    int mode = E->p[SND_P_GLIDEMODE];
    if (mode == SND_GLIDE_MONO || mode == SND_GLIDE_MONO_LEGATO) {
        dsp_voice_t *v = mono_voice(d, e);
        /* voci tenute rimaste da un cambio di modo con un accordo tenuto: si rilasciano con la loro nota */
        for (int i = 0; i < DSP_VOICES; i++) {
            dsp_voice_t *w = &d->voice[i];
            if (w == v || w->state != DSP_V_HELD || w->engine != e || w->note != note) continue;
            if (E->sustain) w->sustained = 1; else voice_release(d, w);
        }
        if (!v || v->note != note || v->state != DSP_V_HELD) return;
        if (E->n_held > 0 && !E->sustain) {               /* torna all'ultima nota ancora tenuta */
            uint8_t back = E->held[E->n_held - 1];
            float g = E->p[SND_P_GLIDE] > 0 ? (float)v->note + v->glide - (float)back : 0.0f;
            if (mode == SND_GLIDE_MONO_LEGATO) { v->note = back; v->glide = g; }
            else voice_start(d, v, e, back, v->vel, true, false, g);
            return;
        }
        if (E->sustain) v->sustained = 1; else voice_release(d, v);
        return;
    }
    for (int i = 0; i < DSP_VOICES; i++) {
        dsp_voice_t *v = &d->voice[i];
        if (v->state != DSP_V_HELD || v->engine != e || v->note != note) continue;
        if (E->sustain) v->sustained = 1; else voice_release(d, v);
    }
}

void dsp_chord_start(dsp_t *d, dsp_engine e)
{
    if (e >= DSP_ENGINES) return;
    dsp_eng_t *E = &d->eng[e];
    for (int n = 0; n < 4; n++)
        if (E->p[SND_P_L(n + 1, 2)] == SND_LFOM_MONO) lfo_start(&E->lfo[n], &d->rng);
}

void dsp_pitch_bend(dsp_t *d, dsp_engine e, int16_t v)
{
    if (e < DSP_ENGINES) d->eng[e].bend = clampf((float)v / 8192.0f, -1.0f, 1.0f);
}

void dsp_mod_wheel(dsp_t *d, dsp_engine e, uint8_t v)
{
    if (e < DSP_ENGINES) d->eng[e].wheel = (float)(v > 127 ? 127 : v) / 127.0f;
}

void dsp_sustain(dsp_t *d, dsp_engine e, bool on)
{
    if (e >= DSP_ENGINES) return;
    d->eng[e].sustain = on;
    if (on) return;
    for (int i = 0; i < DSP_VOICES; i++) {                /* SND-205 */
        dsp_voice_t *v = &d->voice[i];
        if (v->engine == e && v->state == DSP_V_HELD && v->sustained) voice_release(d, v);
    }
}

void dsp_reset_controllers(dsp_t *d, dsp_engine e)
{
    if (e >= DSP_ENGINES) return;
    d->eng[e].bend = 0.0f;
    d->eng[e].wheel = 0.0f;
    dsp_sustain(d, e, false);
}

void dsp_all_notes_off(dsp_t *d)
{
    for (int e = 0; e < DSP_ENGINES; e++) { d->eng[e].sustain = 0; d->eng[e].n_held = 0; }
    for (int i = 0; i < DSP_VOICES; i++) voice_release(d, &d->voice[i]);
}

void dsp_all_sound_off(dsp_t *d)
{
    for (int i = 0; i < DSP_VOICES; i++) memset(&d->voice[i], 0, sizeof d->voice[i]);
    for (int i = 0; i < DSP_TAILS; i++) d->tail[i].on = 0;
    for (int e = 0; e < DSP_ENGINES; e++) { d->eng[e].sustain = 0; d->eng[e].n_held = 0; }
}

/* ---------------------------------------------------------------- parametri (§2) ---- */

void dsp_setpar(dsp_t *d, dsp_engine e, uint8_t idx, uint8_t raw)
{
    if (e >= DSP_ENGINES || idx >= DSP_NPAR) return;    /* SND-032 */
    if (raw > snd_par_max[idx]) raw = snd_par_max[idx];
    d->eng[e].p[idx] = raw;
}

static bool fx_locked(int i)                             /* SND-125: i 24 campi della maschera */
{
    return (i >= SND_P_FX1TYPE && i <= SND_P_REVHP) || (i >= SND_P_FTYPE && i <= SND_P_FKT);
}

void dsp_load_patch(dsp_t *d, dsp_engine e, const uint8_t p[DSP_NPAR], uint32_t flags)
{
    if (e >= DSP_ENGINES) return;
    dsp_eng_t *E = &d->eng[e];
    /* SND-112: le voci in suono passano in coda con la patch vecchia. Le tenute si dissolvono in
     * 10 ms e ripartono con la patch nuova; quelle in rilascio finiscono il loro rilascio. */
    struct { uint8_t note, vel, sus; uint32_t age; } held[DSP_VOICES];
    int nh = 0;
    for (int i = 0; i < DSP_VOICES; i++) {
        dsp_voice_t *v = &d->voice[i];
        if (v->state == DSP_V_FREE || v->engine != e) continue;
        if (v->state == DSP_V_HELD) {
            held[nh].note = v->note; held[nh].vel = v->vel; held[nh].sus = v->sustained; held[nh].age = v->age; nh++;
            to_tail(d, v, 0.010f);
        } else to_tail(d, v, 0.0f);
        v->state = DSP_V_FREE;
    }
    for (int i = 0; i < DSP_NPAR; i++) {
        if ((flags & DSP_LOAD_FXLOCK) && fx_locked(i)) continue;
        uint8_t v = p[i] > snd_par_max[i] ? snd_par_max[i] : p[i];
        E->p[i] = v;
        /* un cambio di suono vale subito per le voci, che ripartono con la patch nuova; i parametri
         * degli effetti e del riverbero scorrono in 5 ms, perché un salto del tap o del guadagno fa clic */
        bool fx_par = i > SND_P_FX1TYPE && i <= SND_P_REVHP && i != SND_P_FX2TYPE;
        if (!fx_par) E->sm[i] = (float)v;
    }
    int mode = E->p[SND_P_GLIDEMODE];
    if ((mode == SND_GLIDE_MONO || mode == SND_GLIDE_MONO_LEGATO) && nh > 1) {
        /* patch mono con un accordo tenuto (SND-026): riparte una voce sola, sull'ultima nota tenuta.
         * Ripartire tutte lasciava note bloccate, perché il note-off mono guarda una voce sola. */
        int keep = 0;
        for (int k = 1; k < nh; k++) if (held[k].age > held[keep].age) keep = k;
        if (E->n_held > 0)
            for (int k = 0; k < nh; k++) if (held[k].note == E->held[E->n_held - 1]) keep = k;
        held[0] = held[keep];
        nh = 1;
    }
    for (int k = 0; k < nh; k++) {
        bool reuse;
        dsp_voice_t *v = alloc_voice(d, e, held[k].note, &reuse);
        if (!v) continue;
        voice_start(d, v, e, held[k].note, held[k].vel, reuse, false, 0.0f);
        v->sustained = held[k].sus;
    }
}

void dsp_get_patch(const dsp_t *d, dsp_engine e, uint8_t out[DSP_NPAR])
{
    if (e < DSP_ENGINES) memcpy(out, d->eng[e].p, DSP_NPAR);
}

void dsp_set_max_voices(dsp_t *d, dsp_engine e, uint8_t n)
{
    if (e < DSP_ENGINES) d->eng[e].max_voices = (uint8_t)(n < 1 ? 1 : n > DSP_VOICES ? DSP_VOICES : n);
}

void dsp_set_bpm(dsp_t *d, float bpm) { d->bpm = clampf(bpm, 20.0f, 400.0f); }
void dsp_set_master_volume(dsp_t *d, uint8_t v) { d->master = v > 99 ? 99 : v; }
void dsp_set_bass_volume(dsp_t *d, uint8_t v) { d->bass_vol = v > 99 ? 99 : v; }
void dsp_set_velocity_sense(dsp_t *d, bool on) { d->vel_sense = on; }

int dsp_voices_active(const dsp_t *d)
{
    int n = 0;
    for (int i = 0; i < DSP_VOICES; i++) if (d->voice[i].state != DSP_V_FREE) n++;
    return n;
}

/* ---------------------------------------------------------------- rendering (§10) ---- */

/* soft clip senza latenza: lineare fino a ±0,89, poi cubico fino a ±1 (SND-046) */
static inline float soft_clip(float x)
{
    float a = fabsf(x);
    if (a <= 0.89f) return x;
    float u = (a - 0.89f) / 0.165f;
    float y = u >= 1.0f ? 1.0f : 0.89f + 0.11f * (1.5f * u - 0.5f * u * u * u);
    return x < 0.0f ? -y : y;
}

static void engine_smooth(const dsp_t *d, dsp_eng_t *E)
{
    for (int i = 0; i < DSP_NPAR; i++) {
        float k = i >= SND_P_RPHEIGHT ? d->k_sm20 : d->k_sm5;
        float t = (float)E->p[i], dl = t - E->sm[i];
        E->sm[i] = (dl > -1e-3f && dl < 1e-3f) ? t : E->sm[i] + dl * k;    /* chiude, senza coda denormale */
    }
}

/* tremolo dell'oggetto RP del motore, prima di FX1 (SND-357) */
static void rp_tremolo(dsp_t *d, dsp_eng_t *E, float *L, float *R)
{
    float depth = E->sm[SND_P_RPTREMOLO] / 127.0f;
    float f = curve(CURVE_F_RP_TREM, E->sm[SND_P_RPTREMRATE]);
    float off = 0.5f * E->sm[SND_P_RPTSTEREO] / 127.0f;              /* in cicli: π = mezzo ciclo */
    float inc = f * d->inv_fs;
    for (int i = 0; i < DSP_BLOCK; i++) {
        float gl = 1.0f - depth * (1.0f - sin_cyc(E->trem_ph + 0.25f)) * 0.5f;
        float gr = 1.0f - depth * (1.0f - sin_cyc(E->trem_ph + off + 0.25f)) * 0.5f;
        L[i] *= gl;
        R[i] *= gr;
        E->trem_ph += inc;
        if (E->trem_ph >= 1.0f) E->trem_ph -= 1.0f;
    }
}

void dsp_render16(dsp_t *d, float *L, float *R, const float *drum_L, const float *drum_R)
{
    float bus[DSP_ENGINES][2][DSP_BLOCK];
    memset(bus, 0, sizeof bus);
    const float dt = (float)DSP_BLOCK * d->inv_fs;

    for (int e = 0; e < DSP_ENGINES; e++) {
        engine_smooth(d, &d->eng[e]);
        engine_lfos(d, &d->eng[e], dt);
    }

    for (int i = 0; i < DSP_VOICES; i++) {
        dsp_voice_t *v = &d->voice[i];
        if (v->state == DSP_V_FREE) continue;
        dsp_eng_t *E = &d->eng[v->engine];
        voice_control(d, v, E->p, E->sm, false);
        v->peak = voice_render(d, v, E->p, E->sm, bus[v->engine][0], bus[v->engine][1], 1.0f, 0.0f);
        int model = d->eng[v->engine].p[SND_P_MODEL];
        bool done;
        if (model == SND_MODEL_RP) done = rp_done(v);
        else {
            done = v->env[1].stage == DSP_ENV_IDLE;
            if (v->state == DSP_V_RELEASED && v->peak < 3.2e-5f) done = true;   /* −90 dBFS (SND-021) */
        }
        if (model == SND_MODEL_SMP && v->smp.ended) { done = true; v->state = DSP_V_RELEASED; }   /* one-shot finito */
        if (done && v->state != DSP_V_HELD) v->state = DSP_V_FREE;
    }
    for (int i = 0; i < DSP_TAILS; i++) {
        dsp_tail_t *t = &d->tail[i];
        if (!t->on) continue;
        voice_control(d, &t->v, t->p, t->sm, true);
        float pk = voice_render(d, &t->v, t->p, t->sm, bus[t->v.engine][0], bus[t->v.engine][1], t->fade, t->step);
        if (t->step > 0.0f) {
            t->fade -= t->step * (float)DSP_BLOCK;
            if (t->fade <= 0.0f) t->on = 0;
        } else {                                          /* coda naturale: fino alla fine del rilascio */
            bool done = t->p[SND_P_MODEL] == SND_MODEL_RP ? rp_done(&t->v)
                      : t->v.env[1].stage == DSP_ENV_IDLE || pk < 3.2e-5f || t->v.smp.ended;
            if (done) t->on = 0;
        }
    }

    /* motori: −12 dB, tremolo RP, FX1 → FX2, volume del basso, mandate al riverbero (§10.1) */
    float send_l[DSP_BLOCK] = { 0 }, send_r[DSP_BLOCK] = { 0 };
    float gb0 = d->g_bass, gb1 = ((float)d->bass_vol / 99.0f) * ((float)d->bass_vol / 99.0f);
    for (int e = 0; e < DSP_ENGINES; e++) {
        dsp_eng_t *E = &d->eng[e];
        float *bl = bus[e][0], *br = bus[e][1];
        for (int i = 0; i < DSP_BLOCK; i++) { bl[i] *= 0.25f; br[i] *= 0.25f; }   /* SND-045 */
        if (E->p[SND_P_MODEL] == SND_MODEL_RP && E->p[SND_P_RPTREMOLO] > 0) rp_tremolo(d, E, bl, br);
        fx_process(d, E, 0, bl, br);
        fx_process(d, E, 1, bl, br);
        if (e == DSP_BASS) {                                                    /* SND-453 */
            float g = gb0, dg = (gb1 - gb0) / (float)DSP_BLOCK;
            for (int i = 0; i < DSP_BLOCK; i++) { g += dg; bl[i] *= g; br[i] *= g; }
        }
        float s = E->sm[SND_P_REVSEND] / 127.0f;                               /* SND-531 */
        if (s > 0.0f)
            for (int i = 0; i < DSP_BLOCK; i++) { send_l[i] += bl[i] * s; send_r[i] += br[i] * s; }
    }
    d->g_bass = gb1;

    float wet_l[DSP_BLOCK], wet_r[DSP_BLOCK];
    rev_process(d, send_l, send_r, wet_l, wet_r);

    /* somma, batteria, master, soft clip, scope (SND-535, SND-536, SND-033) */
    float gm0 = d->g_master, gm1 = ((float)d->master / 99.0f) * ((float)d->master / 99.0f);
    float gm = gm0, dgm = (gm1 - gm0) / (float)DSP_BLOCK;
    for (int i = 0; i < DSP_BLOCK; i++) {
        float l = bus[0][0][i] + bus[1][0][i] + wet_l[i];
        float r = bus[0][1][i] + bus[1][1][i] + wet_r[i];
        if (drum_L) l += drum_L[i];
        if (drum_R) r += drum_R[i];
        gm += dgm;
        l = soft_clip(l * gm);
        r = soft_clip(r * gm);
        L[i] = l;
        R[i] = r;
        d->scope_acc += 0.5f * (l + r);
        if (++d->scope_n == 4) {
            float s = d->scope_acc * 0.25f * 32767.0f;
            d->scope[d->scope_wr % DSP_SCOPE_N] = (int16_t)clampf(s, -32767.0f, 32767.0f);
            d->scope_wr = d->scope_wr + 1u;
            d->scope_acc = 0.0f;
            d->scope_n = 0;
        }
    }
    d->g_master = gm1;
}

size_t dsp_scope_read(dsp_t *d, float *dst, size_t max)
{
    uint32_t w = d->scope_wr;
    size_t n = max < DSP_SCOPE_N ? max : DSP_SCOPE_N;
    for (size_t i = 0; i < n; i++)
        dst[i] = (float)d->scope[(w - (uint32_t)n + (uint32_t)i) % DSP_SCOPE_N] / 32767.0f;
    return n;
}
