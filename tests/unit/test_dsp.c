/* test_dsp.c — test del synth (specifica 20, §14.2) e determinismo (SND-005, SND-801). */
#include "test.h"
#include "../../src/dsp/dsp.h"
#include "../../src/dsp/curves.h"
#include "../../src/dsp/inc.h"
#include <math.h>
#include <string.h>

#define FS 48000
#define MAXN (FS * 2)

static dsp_t D, D2;                        /* 2,6 MB l'uno: statici */
static float L1[MAXN], R1[MAXN], L2[MAXN], R2[MAXN];

static void render(dsp_t *d, float *l, float *r, int n)
{
    for (int i = 0; i + DSP_BLOCK <= n; i += DSP_BLOCK) dsp_render16(d, l + i, r + i, NULL, NULL);
}

static void skip(dsp_t *d, int n)
{
    float l[DSP_BLOCK], r[DSP_BLOCK];
    for (int i = 0; i < n; i += DSP_BLOCK) dsp_render16(d, l, r, NULL, NULL);
}

static double rms(const float *x, int n)
{
    double s = 0;
    for (int i = 0; i < n; i++) s += (double)x[i] * (double)x[i];
    return sqrt(s / n);
}

static float peak(const float *x, int n)
{
    float p = 0;
    for (int i = 0; i < n; i++) if (fabsf(x[i]) > p) p = fabsf(x[i]);
    return p;
}

/* frequenza dagli attraversamenti dello zero in salita, interpolati */
static double freq(const float *x, int n)
{
    double t0 = -1, t1 = 0;
    int k = 0;
    for (int i = 1; i < n; i++)
        if (x[i - 1] < 0.0f && x[i] >= 0.0f) {
            double t = i - 1 + (double)x[i - 1] / ((double)x[i - 1] - (double)x[i]);
            if (t0 < 0) t0 = t; else { t1 = t; k++; }
        }
    return k > 0 ? k / (t1 - t0) * FS : 0;
}

static double cents(double f, double ref) { return 1200.0 * log2(f / ref); }
static double hz(double note) { return 440.0 * pow(2.0, (note - 69.0) / 12.0); }

static void fresh(dsp_t *d, int model)
{
    dsp_init(d, FS, 12345);
    uint8_t p[DSP_NPAR];
    snd_patch_init(p, model);
    dsp_load_patch(d, DSP_SOUND, p, 0);
    dsp_set_master_volume(d, 99);
}

/* FM con il solo operatore 1 a livello pieno: un seno puro alla nota */
static void sine_patch(uint8_t *p)
{
    snd_patch_init(p, SND_MODEL_FM);
    p[SND_P_FMALG] = 7;
    p[SND_P_O(1, 3)] = 127;
    p[SND_P_O(1, 4)] = 0;
    for (int o = 2; o <= 4; o++) p[SND_P_O(o, 3)] = 0;
}

/* T-SND-01, T-SND-02 */
static void test_pitch(void)
{
    for (int note = 24; note <= 108; note += 12) {
        fresh(&D, SND_MODEL_VA);
        dsp_note_on(&D, DSP_SOUND, (uint8_t)note, 100);
        skip(&D, 4800);
        render(&D, L1, R1, FS);
        double c = cents(freq(L1, FS), hz(note));
        CHECKM(fabs(c) < 0.1, "T-SND-01 nota %d: %.3f cent", note, c);
    }
    for (int det = 0; det <= 127; det += 127) {
        fresh(&D, SND_MODEL_VA);
        dsp_setpar(&D, DSP_SOUND, SND_P_O(1, 2), (uint8_t)det);
        D.eng[0].sm[SND_P_O(1, 2)] = (float)det;
        dsp_note_on(&D, DSP_SOUND, 60, 100);
        skip(&D, 4800);
        render(&D, L1, R1, FS);
        double atteso = det == 0 ? -100.0 : 100.0 * 63.0 / 64.0;
        double c = cents(freq(L1, FS), hz(60));
        CHECKM(fabs(c - atteso) < 0.5, "T-SND-02 DETUNE %d: %.2f cent, attesi %.2f", det, c, atteso);
    }
}

/* T-SND-04 */
static void test_pulse(void)
{
    const int pw[3] = { 0, 64, 127 };
    for (int k = 0; k < 3; k++) {
        fresh(&D, SND_MODEL_VA);
        uint8_t p[DSP_NPAR];
        dsp_get_patch(&D, DSP_SOUND, p);
        p[SND_P_O(1, 0)] = SND_SHAPE_PULSE;
        p[SND_P_O(1, 3)] = (uint8_t)pw[k];
        dsp_load_patch(&D, DSP_SOUND, p, 0);
        dsp_note_on(&D, DSP_SOUND, 60, 100);
        skip(&D, 4800);
        render(&D, L1, R1, FS);
        double r = rms(L1, FS);
        if (pw[k] == 64) CHECKM(r > 0.05, "T-SND-04 PW 64: rms %.4f", r);
        else CHECKM(r < 3.16e-5, "T-SND-04 PW %d: rms %.2e", pw[k], r);
    }
}

/* T-SND-06: −3 dB a f_cut ±5 % (seno puro, rapporto con il filtro spento) */
static double gain_at(int cut, double note)
{
    uint8_t p[DSP_NPAR];
    double r[2];
    for (int k = 0; k < 2; k++) {
        dsp_init(&D, FS, 7);
        dsp_set_master_volume(&D, 99);
        sine_patch(p);
        p[SND_P_FTYPE] = k ? SND_FT_LP : SND_FT_OFF;
        p[SND_P_CUTOFF] = (uint8_t)cut;
        int n = (int)floor(note);
        p[SND_P_O(1, 2)] = (uint8_t)(64 + (int)lround((note - n) * 64.0));
        dsp_load_patch(&D, DSP_SOUND, p, 0);
        dsp_note_on(&D, DSP_SOUND, (uint8_t)n, 100);
        skip(&D, 4800);
        render(&D, L1, R1, 9600);
        r[k] = rms(L1, 9600);
    }
    return r[1] / r[0];
}

static void test_filter(void)
{
    for (int cut = 16; cut <= 112; cut += 16) {
        double fc = (double)dsp_curves[CURVE_F_CUT][cut];
        double nc = 69.0 + 12.0 * log2(fc / 440.0);
        double prev_n = nc - 3.0, prev_g = 20.0 * log10(gain_at(cut, prev_n)), f3 = 0;
        for (double n = nc - 2.5; n <= nc + 3.0; n += 0.5) {
            double g = 20.0 * log10(gain_at(cut, n));
            if (prev_g > -3.0103 && g <= -3.0103) {
                double t = (prev_g + 3.0103) / (prev_g - g);
                f3 = hz(prev_n + t * (n - prev_n));
                break;
            }
            prev_n = n;
            prev_g = g;
        }
        CHECKM(f3 > 0 && fabs(f3 / fc - 1.0) < 0.05, "T-SND-06 CUTOFF %d: −3 dB a %.1f Hz, f_cut %.1f Hz", cut, f3, fc);
    }
}

/* T-SND-07: Q 127 senza ingresso, 60 s */
static void test_selfosc(void)
{
    fresh(&D, SND_MODEL_VA);
    uint8_t p[DSP_NPAR];
    dsp_get_patch(&D, DSP_SOUND, p);
    p[SND_P_O(1, 0)] = SND_SHAPE_OFF;
    p[SND_P_RESONANCE] = 127;
    p[SND_P_CUTOFF] = 64;
    dsp_load_patch(&D, DSP_SOUND, p, 0);
    dsp_note_on(&D, DSP_SOUND, 60, 100);
    float pk = 0;
    bool finite = true;
    for (int s = 0; s < 60; s++) {
        render(&D, L1, R1, FS);
        for (int i = 0; i < FS; i++) if (!isfinite(L1[i])) finite = false;
        if (s >= 50) { float q = peak(L1, FS); if (q > pk) pk = q; }
    }
    float th = 64.0f / 127.0f * 1.5707963f;
    float lp = pk / (0.25f * cosf(th));
    CHECKM(finite, "T-SND-07: NaN o infinito");
    CHECKM(lp >= 0.5f && lp <= 1.0f, "T-SND-07: picco del passa-basso %.3f", (double)lp);
}

/* T-SND-08: tempi degli inviluppi (dallo stato della voce, interpolato in scala logaritmica) */
static double env_time(int stage_par, int raw)
{
    fresh(&D, SND_MODEL_VA);
    uint8_t p[DSP_NPAR];
    dsp_get_patch(&D, DSP_SOUND, p);
    p[SND_P_E(2, 0)] = stage_par == 0 ? (uint8_t)raw : 0;
    p[SND_P_E(2, 1)] = 0;
    p[SND_P_E(2, 2)] = stage_par == 2 ? (uint8_t)raw : 64;
    p[SND_P_E(2, 3)] = stage_par == 2 ? 0 : 127;
    p[SND_P_E(2, 4)] = stage_par == 4 ? (uint8_t)raw : 64;
    dsp_load_patch(&D, DSP_SOUND, p, 0);
    dsp_note_on(&D, DSP_SOUND, 60, 100);
    const dsp_voice_t *v = &D.voice[0];
    for (int i = 0; i < DSP_VOICES; i++) if (D.voice[i].state != DSP_V_FREE) v = &D.voice[i];
    const double dt = (double)DSP_BLOCK / FS;
    float l[DSP_BLOCK], r[DSP_BLOCK];
    if (stage_par == 0) {
        for (int b = 1; b < 20000; b++) {
            dsp_render16(&D, l, r, NULL, NULL);
            if (v->env[1].stage != DSP_ENV_ATT) {
                /* il livello ha superato 1 in questo blocco: frazione lineare */
                return b * dt;
            }
        }
        return 0;
    }
    while (v->env[1].stage == DSP_ENV_ATT) dsp_render16(&D, l, r, NULL, NULL);
    if (stage_par == 4) { skip(&D, 960); dsp_note_off(&D, DSP_SOUND, 60); }
    double t = 0, prev = (double)v->env[1].level;
    for (int b = 0; b < 200000; b++) {
        dsp_render16(&D, l, r, NULL, NULL);
        double lv = (double)v->env[1].level;
        if (lv <= 1e-3) return t + dt * log(1e-3 / prev) / log(lv / prev);
        t += dt;
        prev = lv;
    }
    return 0;
}

static void test_env(void)
{
    const int raw[5] = { 0, 32, 64, 96, 127 };
    for (int k = 1; k < 5; k++) {                       /* attacco: da 32 (0,5 ms sta sotto un blocco) */
        double t = env_time(0, raw[k]), att = (double)dsp_curves[CURVE_T_ATT][raw[k]];
        CHECKM(fabs(t / att - 1.0) < 0.05, "T-SND-08 A %d: %.4f s, atteso %.4f", raw[k], t, att);
    }
    for (int k = 0; k < 5; k++) {
        double att = (double)dsp_curves[CURVE_T_DEC][raw[k]];
        double t = env_time(2, raw[k]);
        CHECKM(fabs(t / att - 1.0) < 0.05, "T-SND-08 D %d: %.4f s, atteso %.4f", raw[k], t, att);
        t = env_time(4, raw[k]);
        CHECKM(fabs(t / att - 1.0) < 0.05, "T-SND-08 R %d: %.4f s, atteso %.4f", raw[k], t, att);
    }
}

/* T-SND-09: frequenza degli LFO (LFO FREE del motore) */
static void test_lfo(void)
{
    const int raw[5] = { 0, 32, 64, 96, 127 };
    for (int k = 0; k < 5; k++) {
        fresh(&D, SND_MODEL_VA);
        dsp_setpar(&D, DSP_SOUND, SND_P_L(1, 1), (uint8_t)raw[k]);
        dsp_setpar(&D, DSP_SOUND, SND_P_L(1, 2), SND_LFOM_FREE);
        D.eng[0].sm[SND_P_L(1, 1)] = (float)raw[k];
        double f = (double)dsp_curves[CURVE_F_LFO][raw[k]];
        int blocks = (int)(FS / DSP_BLOCK * (f < 1.0 ? 70.0 : 10.0));
        float l[DSP_BLOCK], r[DSP_BLOCK];
        double cyc = 0;
        float last = D.eng[0].lfo[0].phase, start = last;
        for (int b = 0; b < blocks; b++) {
            dsp_render16(&D, l, r, NULL, NULL);
            float ph = D.eng[0].lfo[0].phase;
            if (ph < last) cyc += 1.0;
            last = ph;
        }
        cyc += (double)last - (double)start;
        double fm = cyc / (blocks * (double)DSP_BLOCK / FS);
        CHECKM(fabs(fm / f - 1.0) < 0.01, "T-SND-09 rate %d: %.4f Hz, atteso %.4f", raw[k], fm, f);
    }
}

/* un accordo di prova: restituisce il numero di campioni resi */
static int chord(dsp_t *d, float *l, float *r)
{
    dsp_note_on(d, DSP_SOUND, 57, 90);
    dsp_note_on(d, DSP_SOUND, 61, 90);
    dsp_note_on(d, DSP_SOUND, 64, 90);
    render(d, l, r, FS / 2);
    dsp_note_off(d, DSP_SOUND, 61);
    render(d, l + FS / 2, r + FS / 2, FS / 2);
    return FS;
}

/* T-SND-15, T-SND-18: intensità 0 = bypass entro −90 dB */
static void test_fx_zero(void)
{
    fresh(&D, SND_MODEL_VA);
    int n = chord(&D, L1, R1);
    for (int type = SND_FX_CHORUS; type <= SND_FX_DELAY; type++) {
        fresh(&D2, SND_MODEL_VA);
        uint8_t p[DSP_NPAR];
        dsp_get_patch(&D2, DSP_SOUND, p);
        int base = type == SND_FX_DELAY ? SND_P_FX2TYPE : SND_P_FX1TYPE;
        p[base] = (uint8_t)type;
        for (int k = 1; k <= 6; k++) p[base + k] = 90;
        p[base + 2] = 0;                                 /* P2 = intensità */
        if (type == SND_FX_TREMOLO) p[base + 1] = 0;      /* e RATE 0 */
        dsp_load_patch(&D2, DSP_SOUND, p, 0);
        chord(&D2, L2, R2);
        float diff = 0;
        for (int i = 0; i < n; i++) {
            float a = fabsf(L1[i] - L2[i]), b = fabsf(R1[i] - R2[i]);
            if (a > diff) diff = a;
            if (b > diff) diff = b;
        }
        CHECKM(diff < 3.16e-5f, "T-SND-18 tipo %d: differenza %.2e", type, (double)diff);
    }
}

/* T-SND-22: FX lock */
static void test_fxlock(void)
{
    uint8_t a[DSP_NPAR], b[DSP_NPAR], c[DSP_NPAR];
    for (int i = 0; i < DSP_NPAR; i++) { a[i] = (uint8_t)(i % 3); b[i] = (uint8_t)(i % 5 + 1); }
    snd_patch_clamp(a);
    snd_patch_clamp(b);
    dsp_init(&D, FS, 1);
    dsp_load_patch(&D, DSP_SOUND, a, 0);
    dsp_load_patch(&D, DSP_SOUND, b, DSP_LOAD_FXLOCK);
    dsp_get_patch(&D, DSP_SOUND, c);
    int locked = 0, ok = 1;
    for (int i = 0; i < DSP_NPAR; i++) {
        bool m = (i >= SND_P_FX1TYPE && i <= SND_P_REVHP) || (i >= SND_P_FTYPE && i <= SND_P_FKT);
        if (m) { locked++; if (c[i] != a[i]) ok = 0; }
        else if (c[i] != b[i]) ok = 0;
    }
    CHECK_EQ(locked, 24);
    CHECKM(ok, "T-SND-22: campi della maschera sovrascritti o altri campi persi");
}

/* T-SND-30, T-SND-31, T-SND-33 */
static void test_pool(void)
{
    fresh(&D, SND_MODEL_VA);
    for (int k = 0; k < 17; k++) { dsp_note_on(&D, DSP_SOUND, (uint8_t)(40 + k), 100); skip(&D, 16); }
    CHECK_EQ(dsp_voices_active(&D), 16);
    bool first = false, last = false;
    for (int i = 0; i < DSP_VOICES; i++) {
        if (D.voice[i].note == 40 && D.voice[i].state != DSP_V_FREE) first = true;
        if (D.voice[i].note == 56 && D.voice[i].state != DSP_V_FREE) last = true;
    }
    CHECKM(!first && last, "T-SND-30: la 17ª nota deve rubare la più vecchia");
    CHECK_EQ((int)D.steals, 1);

    fresh(&D, SND_MODEL_VA);
    dsp_note_on(&D, DSP_BASS, 36, 100);
    skip(&D, 16);
    for (int k = 0; k < 16; k++) { dsp_note_on(&D, DSP_SOUND, (uint8_t)(60 + k), 100); skip(&D, 16); }
    bool bass = false;
    for (int i = 0; i < DSP_VOICES; i++)
        if (D.voice[i].engine == DSP_BASS && D.voice[i].note == 36 && D.voice[i].state == DSP_V_HELD) bass = true;
    CHECKM(bass, "T-SND-31: la voce del basso tenuta non va rubata");

    fresh(&D, SND_MODEL_RP);
    dsp_note_on(&D, DSP_SOUND, 60, 120);
    dsp_note_on(&D, DSP_SOUND, 64, 120);
    skip(&D, 4800);
    dsp_all_sound_off(&D);
    float l[DSP_BLOCK], r[DSP_BLOCK];
    dsp_render16(&D, l, r, NULL, NULL);
    CHECKM(peak(l, DSP_BLOCK) == 0.0f && peak(r, DSP_BLOCK) == 0.0f, "T-SND-33: silenzio entro un blocco");
    CHECK_EQ(dsp_voices_active(&D), 0);
}

/* T-SND-32: lo stealing non fa clic */
static void test_steal_click(void)
{
    fresh(&D, SND_MODEL_VA);
    uint8_t p[DSP_NPAR];
    sine_patch(p);
    p[SND_P_FTYPE] = SND_FT_OFF;
    dsp_load_patch(&D, DSP_SOUND, p, 0);
    dsp_set_max_voices(&D, DSP_SOUND, 1);
    dsp_note_on(&D, DSP_SOUND, 45, 127);
    skip(&D, 4800);
    render(&D, L1, R1, 480);
    dsp_note_on(&D, DSP_SOUND, 52, 127);
    render(&D, L1 + 480, R1 + 480, 960);
    /* il salto massimo tra due campioni non deve superare quello del seno più 0,05 */
    double w = 2.0 * 3.14159265 * hz(52) / FS;
    float jump = 0;
    for (int i = 481; i < 1440; i++) { float j = fabsf(L1[i] - L1[i - 1]); if (j > jump) jump = j; }
    float lim = (float)(w * (double)peak(L1, 1440)) + 0.05f;
    CHECKM(jump <= lim, "T-SND-32: salto %.4f oltre %.4f", (double)jump, (double)lim);
}

/* revisione del 15/10/2026, SND-026: accordo tenuto e cambio a una patch mono. Riparte una voce sola,
 * sull'ultima nota tenuta, e al rilascio non resta niente acceso; anche con GLIDEMODE cambiato a mano */
static int held_voices(const dsp_t *d)
{
    int h = 0;
    for (int i = 0; i < DSP_VOICES; i++) if (d->voice[i].state == DSP_V_HELD) h++;
    return h;
}

static void test_mono_switch(void)
{
    static const uint8_t ACC[3] = { 60, 64, 67 };
    fresh(&D, SND_MODEL_VA);
    for (int i = 0; i < 3; i++) dsp_note_on(&D, DSP_SOUND, ACC[i], 100);
    skip(&D, 480);
    uint8_t p[DSP_NPAR];
    snd_patch_init(p, SND_MODEL_VA);
    p[SND_P_GLIDEMODE] = SND_GLIDE_MONO;
    dsp_load_patch(&D, DSP_SOUND, p, 0);
    int note = -1;
    for (int i = 0; i < DSP_VOICES; i++) if (D.voice[i].state == DSP_V_HELD) note = D.voice[i].note;
    CHECKM(held_voices(&D) == 1 && note == 67, "una voce sola, sull'ultima nota: %d voci, nota %d", held_voices(&D), note);
    for (int i = 0; i < 3; i++) dsp_note_off(&D, DSP_SOUND, ACC[i]);
    CHECKM(held_voices(&D) == 0, "note bloccate: %d", held_voices(&D));

    fresh(&D, SND_MODEL_VA);
    for (int i = 0; i < 3; i++) dsp_note_on(&D, DSP_SOUND, ACC[i], 100);
    dsp_setpar(&D, DSP_SOUND, SND_P_GLIDEMODE, SND_GLIDE_MONO);
    for (int i = 0; i < 3; i++) dsp_note_off(&D, DSP_SOUND, ACC[i]);
    CHECKM(held_voices(&D) == 0, "GLIDEMODE cambiato con l'accordo tenuto: %d note bloccate", held_voices(&D));
}

/* T-SND-14: Reed Piano, T60 della nota singola */
static void test_rp(void)
{
    const int dec[2] = { 0, 127 };
    for (int k = 0; k < 2; k++) {
        fresh(&D, SND_MODEL_RP);
        uint8_t p[DSP_NPAR];
        dsp_get_patch(&D, DSP_SOUND, p);
        p[SND_P_RPDECAY] = (uint8_t)dec[k];
        p[SND_P_RPCLANK] = 0;
        p[SND_P_RPHAMMER] = 0;
        p[SND_P_RPHEIGHT] = 0;
        dsp_load_patch(&D, DSP_SOUND, p, 0);
        dsp_note_on(&D, DSP_SOUND, 60, 100);
        double t60 = (double)dsp_curves[CURVE_T_RP_DECAY][dec[k]];
        int win = FS / 100, nwin = (int)(t60 * 1.2 * 100) + 10;
        double ref = 0, ta = -1, tb = -1;
        for (int w = 0; w < nwin; w++) {
            render(&D, L1, R1, win);
            double db = 20.0 * log10(rms(L1, win) + 1e-12);
            if (w == 2) ref = db;
            if (w > 2 && ta < 0 && db <= ref - 10.0) ta = w * 0.01;
            if (w > 2 && tb < 0 && db <= ref - 40.0) { tb = w * 0.01; break; }
        }
        double m = tb > ta && ta > 0 ? 60.0 * (tb - ta) / 30.0 : 0;
        CHECKM(fabs(m / t60 - 1.0) < 0.10, "T-SND-14 RPDECAY %d: T60 %.3f s, atteso %.3f", dec[k], m, t60);
    }
}

/* Revisione del 16/10/2026: il pickup del Reed Piano non lascia componente continua (con DISTANCE alto
 * Φ(A·x+d) − Φ(d) ne produceva fino al 60 % del valore medio), e una ribattuta più piano della
 * stessa nota non scala la coda che suona ancora: A sta sul colpo (SND-351) */
static void test_rp_dc(void)
{
    fresh(&D, SND_MODEL_RP);
    uint8_t p[DSP_NPAR];
    dsp_get_patch(&D, DSP_SOUND, p);
    p[SND_P_RPHEIGHT] = 64; p[SND_P_RPDISTANCE] = 127; p[SND_P_RPDECAY] = 127;
    p[SND_P_RPCLANK] = 0; p[SND_P_RPHAMMER] = 0;
    dsp_load_patch(&D, DSP_SOUND, p, 0);
    dsp_note_on(&D, DSP_SOUND, 48, 100);
    render(&D, L1, R1, FS / 2);
    double mean = 0, mabs = 0;
    for (int i = FS / 4; i < FS / 2; i++) { mean += (double)L1[i]; mabs += fabs((double)L1[i]); }
    mean /= FS / 4; mabs /= FS / 4;
    CHECKM(mabs > 0.01 && fabs(mean) < 0.05 * mabs, "RP: continua %.4f su |x| medio %.4f", mean, mabs);

    fresh(&D, SND_MODEL_RP);
    dsp_get_patch(&D, DSP_SOUND, p);
    p[SND_P_RPVELCURVE] = 127; p[SND_P_RPCLANK] = 0; p[SND_P_RPHAMMER] = 0;
    dsp_load_patch(&D, DSP_SOUND, p, 0);
    dsp_note_on(&D, DSP_SOUND, 48, 127);
    render(&D, L1, R1, FS / 10);
    float before = 0, last = L1[FS / 10 - 1];
    for (int i = FS / 10 - 2000; i < FS / 10; i++) { float j = fabsf(L1[i] - L1[i - 1]); if (j > before) before = j; }
    dsp_note_on(&D, DSP_SOUND, 48, 10);                     /* ribattuta piano: la coda non deve saltare */
    render(&D, L1, R1, 256);
    float after = fabsf(L1[0] - last);
    for (int i = 1; i < 256; i++) { float j = fabsf(L1[i] - L1[i - 1]); if (j > after) after = j; }
    CHECKM(after < 1.5f * before + 1e-3f, "RP ribattuta: salto %.4f contro %.4f in regime", (double)after, (double)before);
}

/* Revisione del 16/10/2026: chorus, ensemble e flanger con RATE e DEPTH al massimo su un seno. L'LFO
 * scorre per campione, quindi l'uscita è un seno con un Doppler di ±35 % al più: la derivata seconda
 * resta quella di un seno. Con l'LFO fermo per blocco il ritardo saltava fino a 5 campioni ogni 16. */
static void test_fx_smooth(void)
{
    const int types[3] = { SND_FX_CHORUS, SND_FX_ENSEMBLE, SND_FX_FLANGER };
    for (int k = 0; k < 3; k++) {
        fresh(&D, SND_MODEL_FM);
        uint8_t p[DSP_NPAR];
        sine_patch(p);
        p[SND_P_FX1TYPE] = (uint8_t)types[k];
        for (int j = 1; j <= 6; j++) p[SND_P_FX1TYPE + j] = 127;
        if (types[k] == SND_FX_FLANGER) p[SND_P_FX1TYPE + 3] = 0;   /* senza feedback: un seno pulito */
        dsp_load_patch(&D, DSP_SOUND, p, 0);
        dsp_note_on(&D, DSP_SOUND, 81, 100);
        skip(&D, FS);
        int n = FS / 4;
        render(&D, L1, R1, n);
        float d2 = 0;
        for (int i = 2; i < n; i++) { float s = fabsf(L1[i] - 2.0f * L1[i - 1] + L1[i - 2]); if (s > d2) d2 = s; }
        float a = peak(L1, n), w = 6.2831853f * 880.0f * 1.4f / (float)FS;
        CHECKM(a > 0.05f && d2 < 1.5f * a * w * w, "FX %d: derivata seconda %.4f su ampiezza %.3f (limite %.4f)",
               types[k], (double)d2, (double)a, (double)(1.5f * a * w * w));
    }
}

/* SND-005, SND-801: stessi ingressi, stessa uscita bit per bit; e uscita sempre finita e entro ±1 */
static void test_determinism(void)
{
    for (int model = 0; model < 3; model++) {
        fresh(&D, model);
        fresh(&D2, model);
        chord(&D, L1, R1);
        chord(&D2, L2, R2);
        CHECKM(!memcmp(L1, L2, sizeof(float) * FS) && !memcmp(R1, R2, sizeof(float) * FS),
               "SND-005 modello %d: due render diversi", model);
        bool ok = true;
        for (int i = 0; i < FS; i++) if (!isfinite(L1[i]) || fabsf(L1[i]) > 1.0f) ok = false;
        CHECKM(ok, "modello %d: uscita non finita o fuori da ±1", model);
        CHECKM(rms(L1, FS) > 1e-3, "modello %d: l'accordo non suona (rms %.2e)", model, rms(L1, FS));
    }
}

/* T-SND-20, T-SND-21: file .inc dell'editor dell'originale */
static void test_inc(void)
{
    static char a[4096], b[4096], c[8192];
    uint8_t p[DSP_NPAR], q[DSP_NPAR];
    snd_patch_init(p, SND_MODEL_RP);
    p[SND_P_RPKEYOFF] = 0x10;
    p[SND_P_CUTOFF] = 0x5A;
    size_t n = snd_inc_write(p, a, sizeof a);
    CHECK_EQ((long)n, SND_INC_SIZE);
    CHECK(!memcmp(a, "0x02,\t//0 TREBLE_VER\r\n0x01,\t//1 TREBLE_MODEL\r\n", 46));
    CHECK(!memcmp(a + n - 24, "0x00,\t//134 TREBLE_RPTSTEREO", 24) || !memcmp(a + n - 28, "0x00,\t//134 TREBLE_RPTSTEREO", 28));
    CHECK(a[n - 1] == 'O');                                /* niente a capo dopo l'ultima riga */
    CHECK_EQ(snd_inc_read(a, n, q), 0);
    CHECK(!memcmp(p, q, DSP_NPAR));
    size_t m = snd_inc_write(q, b, sizeof b);
    CHECKM(m == n && !memcmp(a, b, n), "T-SND-20: riscrittura diversa");

    /* tollerante: LF, esadecimale minuscolo, spazi al posto del TAB, prefisso BASS_, a capo finale */
    size_t k = 0;
    for (size_t i = 0; i < n; i++) {
        char ch = a[i];
        if (ch == '\r') continue;
        if (ch == '\t') ch = ' ';
        if (ch >= 'A' && ch <= 'F' && i > 0 && (a[i - 1] == 'x' || a[i - 2] == 'x')) ch = (char)(ch - 'A' + 'a');
        c[k++] = ch;
    }
    c[k++] = '\n';
    CHECK_EQ(snd_inc_read(c, k, q), 0);
    CHECK(!memcmp(p, q, DSP_NPAR));
    memcpy(b, a, n);
    for (size_t i = 0; i + 8 < n; i++) if (!memcmp(b + i, "//5 TREBLE", 10)) { b[i + 2] = '6'; break; }
    CHECKM(snd_inc_read(b, n, q) == -2, "T-SND-21: indice incoerente accettato");
    CHECKM(snd_inc_read(a, n / 2, q) < 0, "T-SND-21: file troncato accettato");
}

void test_dsp(void)
{
    test_inc();
    test_pitch();
    test_pulse();
    test_filter();
    test_selfosc();
    test_env();
    test_lfo();
    test_fx_zero();
    test_fxlock();
    test_pool();
    test_steal_click();
    test_mono_switch();
    test_rp();
    test_rp_dc();
    test_fx_smooth();
    test_determinism();
}
