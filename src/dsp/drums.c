/* drums.c — kit di batteria sintetizzato in stile CR-78 (drums.h). Tutto a campione, float a 32 bit.
 * Inviluppi esponenziali moltiplicativi e coefficienti dei filtri calcolati una volta al colpo: nel
 * ciclo per campione niente expf né cosf, salvo il seno da tabella degli oscillatori. */
#include "drums.h"
#include "dsp_int.h"

/* durata massima e pan di ogni strumento */
static const float DUR[DRUM_COUNT] STAME_ROM = {
    1.2f, 0.15f, 0.6f, 0.6f, 0.3f, 1.0f, 1.5f, 0.9f, 0.15f, 0.5f, 0.6f, 4.0f, 0.1f, 0.1f
};
static const float PAN[DRUM_COUNT] STAME_ROM = {
    0.0f, -0.15f, -0.05f, -0.1f, 0.25f, -0.3f, 0.25f, 0.3f, 0.35f, -0.25f, 0.2f, 0.15f, 0.0f, 0.0f
};

void drums_init(drums_t *k, float fs, uint32_t seed)
{
    memset(k, 0, sizeof *k);
    k->fs = fs;
    k->inv_fs = 1.0f / fs;
    k->rng = seed ? seed : 1u;
    k->gain = 0.36f;
}

void drums_volume(drums_t *k, uint8_t v)
{
    float x = (float)(v > 99 ? 99 : v) / 99.0f;
    k->gain = x * x;
}

void drums_all_off(drums_t *k)
{
    for (int i = 0; i < DRUM_VOICES; i++) k->v[i].on = 0;
}

/* moltiplicatore per campione di un inviluppo che decade con costante di tempo tau */
static float decay(const drums_t *k, float tau) { return expf(-k->inv_fs / tau); }

/* passa-banda a 2 poli: coefficienti per frequenza f e Q */
static void bp_set(const drums_t *k, drum_voice_t *v, float f, float q)
{
    float w = DSP_TWO_PI * f * k->inv_fs, r = 1.0f - DSP_PI * f / q * k->inv_fs;
    if (r < 0.0f) r = 0.0f;
    v->c0 = 1.0f - r;
    v->c1 = 2.0f * r * cosf(w);
    v->c2 = r * r;
}

void drums_hit(drums_t *k, uint8_t inst, uint8_t vel)
{
    if (inst >= DRUM_COUNT || vel == 0) return;
    if (inst == DRUM_CLOSED_HAT)                                  /* il chiuso strozza l'aperto */
        for (int i = 0; i < DRUM_VOICES; i++)
            if (k->v[i].on && k->v[i].inst == DRUM_OPEN_HAT) k->v[i].d1 = decay(k, 0.006f);
    drum_voice_t *v = NULL;
    for (int i = 0; i < DRUM_VOICES && !v; i++) if (!k->v[i].on) v = &k->v[i];
    if (!v) {                                                      /* ruba la più vecchia */
        v = &k->v[0];
        for (int i = 1; i < DRUM_VOICES; i++) if (k->v[i].t > v->t) v = &k->v[i];
    }
    memset(v, 0, sizeof *v);
    v->on = 1;
    v->inst = inst;
    float x = (float)vel / 127.0f;
    v->amp = x * sqrtf(x);
    float th = (PAN[inst] + 1.0f) * 0.25f * DSP_PI;               /* potenza costante */
    v->gl = cosf(th);
    v->gr = sinf(th);
    v->e1 = v->e2 = v->e3 = 1.0f;
    switch (inst) {
    case DRUM_KICK: v->d1 = decay(k, 0.32f); v->d2 = decay(k, 0.03f); v->d3 = decay(k, 0.002f); break;
    case DRUM_SNARE: v->d1 = decay(k, 0.06f); v->d2 = decay(k, 0.12f); bp_set(k, v, 3000.0f, 0.9f); break;
    case DRUM_CLOSED_HAT: v->d1 = decay(k, 0.035f); v->ha = onepole_a(6500.0f, k->inv_fs); break;
    case DRUM_OPEN_HAT: v->d1 = decay(k, 0.35f); v->ha = onepole_a(6500.0f, k->inv_fs); break;
    case DRUM_MARACAS: v->d1 = decay(k, 0.025f); v->ha = onepole_a(4500.0f, k->inv_fs); break;
    case DRUM_CYMBAL: v->d1 = decay(k, 0.9f); v->ha = onepole_a(6000.0f, k->inv_fs); break;
    case DRUM_CLAP: v->d1 = decay(k, 0.004f); v->d2 = decay(k, 0.11f); v->e2 = 0.0f; bp_set(k, v, 1100.0f, 1.2f); break;
    case DRUM_RIMSHOT: v->d1 = decay(k, 0.012f); v->d2 = decay(k, 0.004f); break;
    case DRUM_TOM_LO: v->d1 = decay(k, 0.25f); v->d2 = decay(k, 0.04f); break;
    case DRUM_TOM_HI: v->d1 = decay(k, 0.2f); v->d2 = decay(k, 0.04f); break;
    case DRUM_CONGA: v->d1 = decay(k, 0.12f); v->d2 = decay(k, 0.04f); break;
    case DRUM_COWBELL: v->d1 = decay(k, 0.09f); bp_set(k, v, 1000.0f, 1.0f); break;
    default: v->d1 = decay(k, 0.011f); break;                     /* clic del metronomo */
    }
}

static inline float bp(drum_voice_t *v, float x)
{
    float y = v->c0 * x + v->c1 * v->bp1 - v->c2 * v->bp2;
    v->bp2 = v->bp1;
    v->bp1 = y;
    return y;
}

/* un campione dello strumento */
static float sample(drums_t *k, drum_voice_t *v)
{
    float inv = k->inv_fs, n = rnd_bi(&k->rng), y = 0.0f;
    switch (v->inst) {
    case DRUM_KICK:
        v->ph += (45.0f + 110.0f * v->e2) * inv;
        y = sin_cyc(v->ph) * v->e1 + 0.25f * n * v->e3;
        break;
    case DRUM_SNARE:
        v->ph += 185.0f * inv;
        v->ph2 += 330.0f * inv;
        y = 0.7f * (0.55f * sin_cyc(v->ph) + 0.3f * sin_cyc(v->ph2)) * v->e1 + 1.6f * bp(v, n) * v->e2;
        break;
    case DRUM_CLOSED_HAT: case DRUM_OPEN_HAT: case DRUM_MARACAS: case DRUM_CYMBAL:
        v->hp += v->ha * (n - v->hp);
        y = (n - v->hp) * v->e1 * (v->inst == DRUM_CYMBAL ? 0.6f : 0.8f);
        break;
    case DRUM_CLAP: {                                             /* tre colpi a 10 ms, poi la coda */
        float t = v->t;
        if ((t >= 0.010f && t - inv < 0.010f) || (t >= 0.020f && t - inv < 0.020f)) v->e1 = 1.0f;
        if (t >= 0.020f && v->e2 == 0.0f) v->e2 = 0.6f;
        y = 2.2f * bp(v, n) * (v->e1 + v->e2);
        break;
    }
    case DRUM_RIMSHOT:
        v->ph += 1700.0f * inv;
        y = 0.6f * sin_cyc(v->ph) * v->e1 + 0.5f * n * v->e2;
        break;
    case DRUM_TOM_LO: case DRUM_TOM_HI: case DRUM_CONGA: {
        float f0 = v->inst == DRUM_TOM_LO ? 90.0f : v->inst == DRUM_TOM_HI ? 150.0f : 330.0f;
        v->ph += f0 * (1.0f + 0.35f * v->e2) * inv;
        y = sin_cyc(v->ph) * v->e1;
        break;
    }
    case DRUM_COWBELL:
        v->ph += 540.0f * inv;
        v->ph2 += 800.0f * inv;
        y = 1.5f * bp(v, (tanh_f(3.0f * sin_cyc(v->ph)) + tanh_f(3.0f * sin_cyc(v->ph2))) * 0.3f * v->e1);
        break;
    default:
        v->ph += (v->inst == DRUM_CLICK_ACCENT ? 2500.0f : 1600.0f) * inv;
        y = sin_cyc(v->ph) * v->e1;
        break;
    }
    v->e1 *= v->d1;
    v->e2 *= v->d2;
    v->e3 *= v->d3;
    return y;
}

void drums_render16(drums_t *k, float *L, float *R)
{
    for (int i = 0; i < DRUM_VOICES; i++) {
        drum_voice_t *v = &k->v[i];
        if (!v->on) continue;
        float gl = v->gl * v->amp * k->gain, gr = v->gr * v->amp * k->gain;
        for (int s = 0; s < 16; s++) {
            float y = sample(k, v);
            L[s] += y * gl;
            R[s] += y * gr;
            v->t += k->inv_fs;
        }
        v->bp1 = undenorm(v->bp1);
        v->bp2 = undenorm(v->bp2);
        v->hp = undenorm(v->hp);
        if (v->t >= DUR[v->inst] || (v->e1 < 1e-4f && v->e2 < 1e-4f && v->inst != DRUM_CLAP)) v->on = 0;
    }
}
