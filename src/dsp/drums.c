/* drums.c — kit di batteria: campioni del kit scelto, ricette dei kit sintetizzati della libreria, o
 * sintesi in stile CR-78 (drums.h). Tutto a campione, float a 32 bit. Inviluppi esponenziali
 * moltiplicativi e coefficienti dei filtri calcolati una volta al colpo: nel ciclo per campione niente
 * expf né cosf, salvo il seno da tabella degli oscillatori. Le voci a campione leggono con
 * interpolazione lineare al passo rate / fs. */
#include "drums.h"
#include "dsp_int.h"

/* rapporti dei sei oscillatori a onda quadra del metallo (SND-540), sulla frequenza del tono: il
 * charleston analogico (205,3 · 304,4 · 369,6 · 522,7 · 540 · 800 Hz), il campanaccio (540 e 800 Hz), i
 * modi di una piastra circolare (campane, gong, incudini) e un piatto più fitto */
static const float METAL_R[DK_METAL_SETS][6] STAME_ROM = {
    { 1.0f, 1.4827082f, 1.8002922f, 2.5460302f, 2.6302971f, 3.8967365f },
    { 1.0f, 1.4814815f, 0.0f, 0.0f, 0.0f, 0.0f },
    { 1.0f, 2.7560000f, 5.4040000f, 8.9330000f, 13.344000f, 18.640000f },
    { 1.0f, 1.1834000f, 1.4227000f, 1.7781000f, 2.2468000f, 2.9327000f },
};
static const uint8_t METAL_N[DK_METAL_SETS] STAME_ROM = { 6, 2, 6, 6 };

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
    k->fx_a = 1.0f - expf(-16.0f / (0.015f * fs));           /* 15 ms, a blocchi di 16 */
    k->prog_g = 1.0f;
    k->prog_step = 16.0f / (0.005f * fs);                     /* il Drop: da 1 a 0 in 5 ms */
}

void drums_drop(drums_t *k, bool on) { k->prog_mute = on; }

void drums_fx(drums_t *k, uint8_t drive, int8_t filt)
{
    k->drive_t = (float)(drive > 10 ? 10 : drive) / 10.0f;
    k->fpos_t = (float)(filt < -10 ? -10 : filt > 10 ? 10 : filt) / 10.0f;
}

void drums_volume(drums_t *k, uint8_t v)
{
    float x = (float)(v > 99 ? 99 : v) / 99.0f;
    k->gain = x * x;
}

void drums_set_kit(drums_t *k, const smp_bank_t *bank, const smp_set_t *kit)
{
    k->bank = kit ? bank : NULL;
    k->kit = bank ? kit : NULL;
}

void drums_set_synth(drums_t *k, const drum_kit_t *kit) { k->syn = kit; }

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

/* una voce della ricetta r (SND-540): inviluppi, attacco, colpi del battimani e filtro, al colpo */
static void rec_start(const drums_t *k, drum_voice_t *v, const drum_rec_t *r)
{
    v->r = r;
    v->amp *= r->gain;
    v->ep = v->et = v->en = v->ec = v->eg = 1.0f;
    v->dp = decay(k, r->tp > 0.0f ? r->tp : 1e-4f);
    v->dt = decay(k, r->ta > 0.0f ? r->ta : 1e-4f);
    v->dn_tail = decay(k, r->tn > 0.0f ? r->tn : 1e-4f);
    v->dc = decay(k, 0.0012f);
    v->dg = 1.0f;
    if (r->bursts > 1) {                                       /* il battimani: colpi brevi ogni 9,5 ms, poi la coda */
        v->dn = decay(k, 0.0035f);
        v->burst_n = (uint8_t)(r->bursts - 1);
        v->burst_t = 0.0095f;
    } else v->dn = v->dn_tail;
    if (r->att > 0.0f) { v->a = 0.0f; v->a_inc = k->inv_fs / r->att; } else v->a = 1.0f;
    v->qb = (float)r->bits;
    v->qi = r->bits ? 1.0f / (float)r->bits : 0.0f;
    /* passi senza salto di pitch, il rumore e il filtro solo se servono, i passi del metallo */
    v->inc0 = clampf(r->f0 * k->inv_fs, 0.0f, 0.45f);
    v->inc2 = clampf(r->f0 * r->r2 * k->inv_fs, 1e-6f, 0.45f);
    v->use_n = r->noise != 0.0f || r->click != 0.0f;
    v->use_f = r->noise != 0.0f || r->osc == DK_METAL || (r->flags & DK_ALL);
    if (r->osc == DK_METAL) {
        int set = (int)r->r2 < 0 ? 0 : (int)r->r2 >= DK_METAL_SETS ? DK_METAL_SETS - 1 : (int)r->r2;
        v->nmet = METAL_N[set];
        for (int i = 0; i < v->nmet; i++) v->minc[i] = clampf(r->f0 * METAL_R[set][i] * k->inv_fs, 1e-6f, 0.45f);
    }
    /* filtro a variabili di stato trapezoidale: coefficienti una volta, qui */
    float g = tanf(DSP_PI * clampf(r->fc, 20.0f, 0.45f * k->fs) * k->inv_fs);
    v->fk = 1.0f / (r->q > 0.05f ? r->q : 0.05f);
    v->f1 = 1.0f / (1.0f + g * (g + v->fk));
    v->f2 = g * v->f1;
    v->f3 = g * v->f2;
}

static void hit(drums_t *k, uint8_t inst, uint8_t vel, uint8_t prog);

void drums_hit(drums_t *k, uint8_t inst, uint8_t vel) { hit(k, inst, vel, 0); }

void drums_hit_prog(drums_t *k, uint8_t inst, uint8_t vel)
{
    if (!k->prog_mute) hit(k, inst, vel, 1);
}

static void hit(drums_t *k, uint8_t inst, uint8_t vel, uint8_t prog)
{
    if (inst >= DRUM_COUNT || vel == 0) return;
    if (inst == DRUM_CLOSED_HAT)                                  /* il chiuso strozza l'aperto */
        for (int i = 0; i < DRUM_VOICES; i++)
            if (k->v[i].on && k->v[i].inst == DRUM_OPEN_HAT) k->v[i].d1 = k->v[i].dg = decay(k, 0.006f);
    drum_voice_t *v = NULL;
    for (int i = 0; i < DRUM_VOICES && !v; i++) if (!k->v[i].on) v = &k->v[i];
    if (!v) {                                                      /* ruba la più vecchia */
        v = &k->v[0];
        for (int i = 1; i < DRUM_VOICES; i++) if (k->v[i].t > v->t) v = &k->v[i];
    }
    memset(v, 0, sizeof *v);
    v->on = 1;
    v->inst = inst;
    v->prog = prog;
    float x = (float)vel / 127.0f;
    v->amp = x * sqrtf(x);
    float th = (PAN[inst] + 1.0f) * 0.25f * DSP_PI;               /* potenza costante */
    v->gl = cosf(th);
    v->gr = sinf(th);
    v->e1 = v->e2 = v->e3 = 1.0f;
    v->z = k->kit ? smp_zone_for(k->bank, k->kit, inst, vel) : NULL;
    if (v->z) {                                                    /* campione: l'inviluppo è nel file */
        v->d1 = v->d2 = v->d3 = 1.0f;                              /* d1 scende solo se lo strozza il chiuso */
        v->inc = (float)v->z->rate * k->inv_fs;
        return;
    }
    if (k->syn && inst < DRUM_KIT_INST) {                          /* kit sintetizzato della libreria */
        const drum_rec_t *r = &k->syn->r[inst];
        th = (clampf(r->pan, -1.0f, 1.0f) + 1.0f) * 0.25f * DSP_PI;
        v->gl = cosf(th);
        v->gr = sinf(th);
        rec_start(k, v, r);
        return;
    }
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

/* PolyBLEP di un gradino alla fase t (0…1) con il passo dt: l'onda quadra senza aliasing (SND-250) */
static inline float blep(float t, float dt)
{
    if (t < dt) { t /= dt; return t + t - t * t - 1.0f; }
    if (t > 1.0f - dt) { t = (t - 1.0f) / dt; return t * t + t + t + 1.0f; }
    return 0.0f;
}

/* onda quadra ±1 alla fase ph (0…1) e passo dt (< 0,5) */
static inline float square(float ph, float dt)
{
    float y = ph < 0.5f ? 1.0f : -1.0f, p2 = ph + 0.5f;
    if (p2 >= 1.0f) p2 -= 1.0f;
    return y + blep(ph, dt) - blep(p2, dt);
}

/* avanza una fase in [0, 1) di un passo inc in [0; 0,45] */
static inline float step(float ph, float inc)
{
    ph += inc;
    return ph >= 1.0f ? ph - 1.0f : ph;
}

/* un campione della ricetta (SND-540): tono, rumore e clic; filtro, drive, riduzioni, attacco, sfumata.
 * Senza salto di pitch i passi sono quelli calcolati al colpo; rumore e filtro solo se la ricetta li usa */
static float rec_sample(drums_t *k, drum_voice_t *v)
{
    const drum_rec_t *r = v->r;
    float inv = k->inv_fs, n = v->use_n ? rnd_bi(&k->rng) : 0.0f, sc = 1.0f, y_t = 0.0f;
    float inc = v->inc0, i2 = v->inc2;
    if (r->pa != 0.0f) {
        sc = 1.0f + r->pa * v->ep;
        inc = clampf(r->f0 * sc * inv, 0.0f, 0.45f);
        i2 = clampf(inc * r->r2, 1e-6f, 0.45f);
    }
    switch (r->osc) {
    case DK_SINE:
        y_t = sin_cyc(v->ph);
        if (r->l2 != 0.0f) { y_t += r->l2 * sin_cyc(v->ph2); v->ph2 = step(v->ph2, i2); }
        v->ph = step(v->ph, inc);
        break;
    case DK_SQUARE:
        y_t = square(v->ph, inc);
        if (r->l2 != 0.0f) { y_t += r->l2 * square(v->ph2, i2); v->ph2 = step(v->ph2, i2); }
        v->ph = step(v->ph, inc);
        break;
    case DK_FM:                                                    /* l'indice decade con il tono */
        y_t = sin_cyc(v->ph + r->l2 * v->et * sin_cyc(v->ph2));
        v->ph2 = step(v->ph2, i2);
        v->ph = step(v->ph, inc);
        break;
    case DK_METAL:
        if (v->nmet == 2) {                                        /* il campanaccio: due quadre limitate in banda */
            for (int i = 0; i < 2; i++) {
                float mi = sc == 1.0f ? v->minc[i] : clampf(v->minc[i] * sc, 1e-6f, 0.45f);
                y_t += square(v->mph[i], mi);
                v->mph[i] = step(v->mph[i], mi);
            }
            y_t *= 0.5f;
        } else {                                                   /* sei quadre semplici: il ripiegamento finisce nel */
            for (int i = 0; i < 6; i++) {                          /* fruscio del passa-alto, e costano un terzo */
                float mi = sc == 1.0f ? v->minc[i] : clampf(v->minc[i] * sc, 1e-6f, 0.45f);
                y_t += v->mph[i] < 0.5f ? 1.0f : -1.0f;
                v->mph[i] = step(v->mph[i], mi);
            }
            y_t *= 1.0f / 6.0f;
        }
        break;
    default: break;
    }
    y_t *= r->tone * v->et;
    float y = y_t;
    if (v->use_f) {
        if (r->nhold > 1) {                                        /* rumore tenuto: il canale di rumore dei chip */
            if (v->nc == 0) v->nheld = n;
            if (++v->nc >= r->nhold) v->nc = 0;
        }
        float x = r->noise * v->en * (r->nhold > 1 ? v->nheld : n);
        if (r->osc == DK_METAL || (r->flags & DK_ALL)) { x += y_t; y = 0.0f; }
        float v3 = x - v->s2, v1 = v->f1 * v->s1 + v->f2 * v3, v2 = v->s2 + v->f2 * v->s1 + v->f3 * v3;
        v->s1 = 2.0f * v1 - v->s1;
        v->s2 = 2.0f * v2 - v->s2;
        y += r->flt == DK_LP ? v2 : r->flt == DK_BP ? v->fk * v1 : x - v->fk * v1 - v2;
    }
    y += r->click * v->ec * n;
    if (r->drive > 0.0f) y = tanh_f((1.0f + r->drive) * y);
    if (r->hold > 1) {                                             /* meno campioni: l'aliasing dei campionatori vecchi */
        if (v->hc == 0) v->held = y;
        if (++v->hc >= r->hold) v->hc = 0;
        y = v->held;
    }
    if (r->bits) y = floorf(y * v->qb + 0.5f) * v->qi;             /* meno bit */
    if (v->a < 1.0f) { y *= v->a; v->a += v->a_inc; if (v->a > 1.0f) v->a = 1.0f; }
    float rest = r->dur - v->t;
    if (rest < 0.004f) y *= rest > 0.0f ? rest * 250.0f : 0.0f;   /* gli ultimi 4 ms sfumano: niente clic alla fine */
    y *= v->eg;
    v->ep *= v->dp;
    v->et *= v->dt;
    v->en *= v->dn;
    v->ec *= v->dc;
    v->eg *= v->dg;
    if (v->burst_n && v->t + inv >= v->burst_t) {                  /* il colpo dopo del battimani */
        v->en = 1.0f;
        v->burst_t += 0.0095f;
        if (--v->burst_n == 0) v->dn = v->dn_tail;
    }
    return y;
}

/* un campione dello strumento */
static float sample(drums_t *k, drum_voice_t *v)
{
    if (v->r) return rec_sample(k, v);
    if (v->z) {                                                    /* dal kit: lettura lineare */
        const smp_zone_t *z = v->z;
        uint32_t i = v->idx;
        if (i + 1 >= z->len) { v->on = 0; return 0.0f; }
        float y = ((float)z->data[i] + v->frac * ((float)z->data[i + 1] - (float)z->data[i]))
                * z->gain * (1.0f / 32768.0f) * v->e1;
        v->frac += v->inc;
        uint32_t a = (uint32_t)v->frac;
        v->idx = i + a;
        v->frac -= (float)a;
        v->e1 *= v->d1;
        return y;
    }
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

/* FX del bus (SND-538), su 16 frame in place. Drive: tanh con il campione di mezzo (2×, come il DRIVE
 * degli FX del suono), guadagno fino a +18 dB e uscita normalizzata perché un picco di 0,5 resti 0,5,
 * mescolato con la radice della quantità. Filtro: SVF trapezoidale con Q 1, frequenza esponenziale fra
 * 20 kHz e 150 Hz (passa-basso) o fra 20 Hz e 3 kHz (passa-alto); a ±0 è trasparente, quindi il
 * passaggio fra i due modi non fa clic. Coefficienti una volta per blocco. */
#define DRIVE_REF 0.5f

static void bus_fx(drums_t *k, float *L, float *R)
{
    k->drive += k->fx_a * (k->drive_t - k->drive);
    k->fpos += k->fx_a * (k->fpos_t - k->fpos);
    if (fabsf(k->drive - k->drive_t) < 1e-4f) k->drive = k->drive_t;
    if (fabsf(k->fpos - k->fpos_t) < 1e-4f) k->fpos = k->fpos_t;
    float *ch[2] = { L, R };
    if (k->drive == 0.0f && k->fpos == 0.0f) {                     /* spento: il bus esce com'è */
        for (int c = 0; c < 2; c++) { k->drv_prev[c] = ch[c][15]; k->ic1[c] = k->ic2[c] = 0.0f; }
        return;
    }
    float dr = k->drive, mix = sqrtf(dr);
    float g = expf(dr * 2.0723266f);                               /* 10^(0,9 · dr) */
    float norm = DRIVE_REF / tanh_f(g * DRIVE_REF);
    float p = k->fpos, a1 = 0.0f, a2 = 0.0f, a3 = 0.0f;
    if (p != 0.0f) {
        float fc = p < 0.0f ? 20000.0f * expf(p * 4.8978398f)       /* ln(20000 / 150) */
                            : 20.0f * expf(p * 5.0106353f);          /* ln(3000 / 20) */
        float gg = tanf(DSP_PI * clampf(fc, 10.0f, 0.45f * k->fs) * k->inv_fs);
        a1 = 1.0f / (1.0f + gg * (gg + 1.0f));
        a2 = gg * a1;
        a3 = gg * a2;
    }
    for (int c = 0; c < 2; c++) {
        float *x = ch[c];
        for (int s = 0; s < 16; s++) {
            float y = x[s];
            if (dr > 0.0f) {
                float mid = 0.5f * (k->drv_prev[c] + y);
                k->drv_prev[c] = y;
                float w = 0.5f * (tanh_f(g * mid) + tanh_f(g * y)) * norm;
                y += mix * (w - y);
            } else k->drv_prev[c] = y;
            if (p != 0.0f) {
                float v3 = y - k->ic2[c];
                float v1 = a1 * k->ic1[c] + a2 * v3;
                float v2 = k->ic2[c] + a2 * k->ic1[c] + a3 * v3;
                k->ic1[c] = 2.0f * v1 - k->ic1[c];
                k->ic2[c] = 2.0f * v2 - k->ic2[c];
                y = p < 0.0f ? v2 : y - v1 - v2;
            }
            x[s] = y;
        }
        k->ic1[c] = undenorm(k->ic1[c]);
        k->ic2[c] = undenorm(k->ic2[c]);
    }
}

void drums_render16(drums_t *k, float *L, float *R)
{
    float bl[16] = { 0 }, br[16] = { 0 };                         /* il bus con l'FX; i clic vanno diretti */
    float pl[16] = { 0 }, pr[16] = { 0 };                         /* i colpi programmati, che il Drop zittisce */
    bool prog = false;
    for (int i = 0; i < DRUM_VOICES; i++) {
        drum_voice_t *v = &k->v[i];
        if (!v->on) continue;
        float gl = v->gl * v->amp * k->gain, gr = v->gr * v->amp * k->gain;
        bool clic = v->inst >= DRUM_CLICK_ACCENT;
        if (v->prog && !clic) prog = true;
        float *ol = clic ? L : v->prog ? pl : bl, *or_ = clic ? R : v->prog ? pr : br;
        for (int s = 0; s < 16; s++) {
            float y = sample(k, v);
            ol[s] += y * gl;
            or_[s] += y * gr;
            v->t += k->inv_fs;
        }
        v->bp1 = undenorm(v->bp1);
        v->bp2 = undenorm(v->bp2);
        v->hp = undenorm(v->hp);
        if (v->z) { if (v->e1 < 1e-4f) v->on = 0; }                /* la fine del campione la segna sample() */
        else if (v->r) {                                           /* ricetta: la sua durata, o tutto spento */
            v->s1 = undenorm(v->s1);                               /* niente denormali (SND-703): il clic e il */
            v->s2 = undenorm(v->s2);                               /* salto di pitch arrivano a 1e−38 in 0,1 s */
            v->ep = undenorm(v->ep);
            v->ec = undenorm(v->ec);
            v->et = undenorm(v->et);
            v->en = undenorm(v->en);
            if (v->t >= v->r->dur || v->eg < 1e-4f ||
                (v->et < 1e-4f && v->en < 1e-4f && !v->burst_n && v->a >= 1.0f)) v->on = 0;
        }
        else if (v->t >= DUR[v->inst] || (v->e1 < 1e-4f && v->e2 < 1e-4f && v->inst != DRUM_CLAP)) v->on = 0;
    }
    /* Drop: i colpi programmati sfumano in 5 ms; a zero le loro voci si spengono, così le code non
     * tornano al rilascio */
    float g0 = k->prog_g;
    if (!k->prog_mute && g0 == 0.0f) g0 = 1.0f;       /* dopo un Drop finito non resta una voce vecchia: il primo colpo è pieno */
    float g1 = clampf(k->prog_mute ? g0 - k->prog_step : g0 + k->prog_step, 0.0f, 1.0f);
    if (prog) {
        float g = g0, dg = (g1 - g0) / 16.0f;
        for (int s = 0; s < 16; s++) { g += dg; bl[s] += pl[s] * g; br[s] += pr[s] * g; }
    }
    k->prog_g = g1;
    if (g1 == 0.0f)
        for (int i = 0; i < DRUM_VOICES; i++) if (k->v[i].prog && k->v[i].inst < DRUM_CLICK_ACCENT) k->v[i].on = 0;
    bus_fx(k, bl, br);
    for (int s = 0; s < 16; s++) { L[s] += bl[s]; R[s] += br[s]; }
}
