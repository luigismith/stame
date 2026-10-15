/* rp.c — modello Reed Piano (specifica 20, §7; SND-350…361).
 *
 * Lamella: tre risonatori a 2 poli (modi di una trave a sbalzo) eccitati da un impulso.
 * Pickup non lineare, clank, rumori del martelletto e dello smorzatore, tono. Il tremolo è
 * dell'oggetto RP del motore (dsp.c). Lo schema è di Stame [V → QA-SND-15].
 */
#include "dsp_int.h"

static const float MODE_RATIO[3] = { 1.0f, 6.267f, 17.55f };
static const float MODE_T60_DIV[3] = { 1.0f, 6.0f, 20.0f };

/* risonatore a 2 poli con ampiezza a dell'onda all'impulso unitario */
static void res_set(dsp_res_t *r, float f, float t60, float a, const dsp_t *d)
{
    float w = DSP_TWO_PI * f * d->inv_fs;
    float rr = expf(-DSP_LN60 * d->inv_fs / (t60 > 1e-4f ? t60 : 1e-4f));
    r->b1 = 2.0f * rr * cosf(w);
    r->b2 = rr * rr;
    r->gain = a * sinf(w);
}

static inline float res_tick(dsp_res_t *r, float x)
{
    float y = r->b1 * r->y1 - r->b2 * r->y2 + r->gain * x;
    r->y2 = r->y1;
    r->y1 = y;
    return y;
}

/* passa-banda a 2 poli: coefficienti da frequenza e Q, guadagno circa unitario al centro */
static void bp_coef(float f, float q, const dsp_t *d, float *b1, float *b2)
{
    float w = DSP_TWO_PI * f * d->inv_fs;
    float r = expf(-DSP_PI * (f / q) * d->inv_fs);
    *b1 = 2.0f * r * cosf(w);
    *b2 = r * r;
}

static float hz(float semi) { return note_hz(semi); }

void rp_note_on(dsp_t *d, dsp_voice_t *v, const float *sm)
{
    dsp_rp_voice_t *rp = &v->rp;
    float s = sm[SND_P_RPVELCURVE] / 127.0f;
    float h = (1.0f - s) + s * v->v;                                      /* brillantezza del colpo */
    rp->amp = (1.0f - s) + s * powf(v->v, 1.5f);                          /* SND-351 */
    float t60 = curve(CURVE_T_RP_DECAY, sm[SND_P_RPDECAY]) * powf(2.0f, -((float)v->note - 60.0f) / 24.0f);
    float f0 = hz((float)v->note);
    const float amp[3] = { 1.0f, 0.08f * h, 0.02f * h };
    for (int m = 0; m < 3; m++) {
        rp->t60[m] = t60 / MODE_T60_DIV[m];
        float f = f0 * MODE_RATIO[m];
        if (f < 0.45f * d->fs) res_set(&rp->mode[m], f, rp->t60[m], amp[m], d);
        else rp->mode[m].gain = rp->mode[m].b1 = rp->mode[m].b2 = 0.0f;
    }
    /* clank (SND-354) */
    float kt = powf(2.0f, (sm[SND_P_RPCKT] / 127.0f) * ((float)v->note - 60.0f) / 48.0f);
    float c = sm[SND_P_RPCLANCURVE] / 127.0f;
    float ca = 0.3f * sm[SND_P_RPCLANK] / 127.0f * ((1.0f - c) + c * v->v * v->v);
    const float cf[2] = { 2100.0f, 3400.0f };
    for (int k = 0; k < 2; k++) {
        float f = cf[k] * kt;
        if (f < 0.45f * d->fs) res_set(&rp->clank[k], f, 0.060f, ca, d);
        else rp->clank[k].gain = 0.0f;
    }
    rp->x = 1.0f;                                                         /* impulso al primo campione */
    /* martelletto (SND-355) */
    rp->hammer = 1.0f;
    rp->hp_amp = 0.3f * sm[SND_P_RPHAMMER] / 127.0f * v->v;
    bp_coef(2000.0f, 1.0f, d, &rp->hb1, &rp->hb2);
    rp->keyoff = 0.0f;
    rp->silence = 0.0f;
}

void rp_note_off(dsp_t *d, dsp_voice_t *v, const float *sm)
{
    dsp_rp_voice_t *rp = &v->rp;
    float tr = curve(CURVE_T_RP_RELEASE, sm[SND_P_RPRELEASE]);        /* SND-353 */
    for (int m = 0; m < 3; m++) if (rp->t60[m] > tr) rp->t60[m] = tr;
    rp->keyoff = 1.0f;                                                    /* rumore dello smorzatore */
    rp->kof_amp = 0.2f * sm[SND_P_RPKEYOFF] / 127.0f;
    bp_coef(400.0f, 0.7f, d, &rp->kb1, &rp->kb2);
}

static inline float phi(float u, float hp) { return u / sqrtf(u * u + hp * hp); }

float rp_render(dsp_t *d, dsp_voice_t *v, const uint8_t *p, const float *sm, float pitch_semi, float *out)
{
    dsp_rp_voice_t *rp = &v->rp;

    /* coefficienti del blocco: altezza (bend, matrice PITCH) e smorzamento correnti */
    float f0 = hz(pitch_semi);
    for (int m = 0; m < 3; m++) {
        float f = f0 * MODE_RATIO[m];
        if (f >= 0.45f * d->fs || rp->mode[m].gain == 0.0f) continue;
        float w = DSP_TWO_PI * f * d->inv_fs;
        float rr = expf(-DSP_LN60 * d->inv_fs / rp->t60[m]);
        rp->mode[m].b1 = 2.0f * rr * cosf(w);
        rp->mode[m].b2 = rr * rr;
    }
    int type = p[SND_P_RPICKUP];
    float hp = (1.5f - 1.3f * sm[SND_P_RPHEIGHT] / 127.0f)
             * powf(2.0f, (sm[SND_P_RPKT] / 127.0f) * ((float)v->note - 60.0f) / 24.0f);
    if (type == SND_PICKUP_MELLOW) hp *= 1.3f;
    if (type == SND_PICKUP_SHARP) hp *= 0.7f;
    if (hp < 0.05f) hp = 0.05f;
    float dd = 0.8f * sm[SND_P_RPDISTANCE] / 127.0f;
    float phi_d = type == SND_PICKUP_ODD ? 0.6f * sinf(2.5f * dd / hp) : phi(dd, hp);
    float a_mel = onepole_a(1200.0f, d->inv_fs), a_sh = onepole_a(2000.0f, d->inv_fs), a_tone = onepole_a(800.0f, d->inv_fs);
    float tone = expf(((sm[SND_P_RPTONE] - 64.0f) / 64.0f) * 12.0f * 0.115129f) - 1.0f;   /* ±12 dB sugli acuti */
    float vol = curve(CURVE_G_VOL, sm[SND_P_RPVOL]);
    float k_h = expf(-d->inv_fs / 0.008f), k_k = expf(-d->inv_fs / 0.025f);
    /* normalizzazione: con il pickup lineare il colpo pieno vale circa ±1 */
    float norm = sqrtf(dd * dd + hp * hp);
    norm = norm * norm / (hp * hp) * norm;
    if (type == SND_PICKUP_ODD) norm = hp / 1.5f;

    float pk = 0.0f;
    for (int i = 0; i < DSP_BLOCK; i++) {
        float ex = rp->x;
        rp->x = 0.0f;
        float x = res_tick(&rp->mode[0], ex) + res_tick(&rp->mode[1], ex) + res_tick(&rp->mode[2], ex);
        float u = rp->amp * x + dd;
        float y = type == SND_PICKUP_ODD ? 0.6f * sinf(2.5f * u / hp) - phi_d : phi(u, hp) - phi_d;
        y *= norm;
        if (type == SND_PICKUP_MELLOW) { rp->mel_z += a_mel * (y - rp->mel_z); y = rp->mel_z; }
        else if (type == SND_PICKUP_SHARP) { rp->mel_z += a_sh * (y - rp->mel_z); y += (y - rp->mel_z); }   /* +6 dB sopra 2 kHz */
        y += res_tick(&rp->clank[0], ex) + res_tick(&rp->clank[1], ex);
        if (rp->hammer > 1e-4f) {
            float n = rnd_bi(&d->rng) * rp->hammer * rp->hp_amp;
            float b = rp->hb1 * rp->hy1 - rp->hb2 * rp->hy2 + n * 0.3f;
            rp->hy2 = rp->hy1; rp->hy1 = b;
            y += b;
            rp->hammer *= k_h;
        }
        if (rp->keyoff > 1e-4f) {
            float n = rnd_bi(&d->rng) * rp->keyoff * rp->kof_amp;
            float b = rp->kb1 * rp->ky1 - rp->kb2 * rp->ky2 + n * 0.2f;
            rp->ky2 = rp->ky1; rp->ky1 = b;
            y += b;
            rp->keyoff *= k_k;
        }
        rp->tone_z += a_tone * (y - rp->tone_z);                            /* tilt: acuti sopra 800 Hz */
        y += tone * (y - rp->tone_z);
        y *= vol;
        out[i] = y;
        float a = fabsf(y);
        if (a > pk) pk = a;
    }
    for (int m = 0; m < 3; m++) { rp->mode[m].y1 = undenorm(rp->mode[m].y1); rp->mode[m].y2 = undenorm(rp->mode[m].y2); }
    rp->silence = pk < 3.2e-5f ? rp->silence + 1.0f : 0.0f;
    return pk;
}

bool rp_done(const dsp_voice_t *v)
{
    return v->state == DSP_V_RELEASED && v->rp.silence >= 2.0f && v->rp.keyoff < 1e-3f;
}
