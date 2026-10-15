/* smp.c — lettura del banco di campioni e voce campionata (smp.h; specifica 20, §7b).
 *
 * Lettura a 4 punti (Hermite) con il passo in campioni dato dalla voce (v->inc[0]): il rapporto
 * fra la frequenza di registrazione e quella di uscita per l'intervallo dalla nota di registrazione.
 * Il loop è un salto all'indietro: la dissolvenza al punto di giunzione è già nel campione, la
 * mette lo strumento che costruisce il banco (tools/campioni.py).
 */
#include "dsp_int.h"

static uint32_t rd32(const uint8_t *p) { return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24; }
static uint16_t rd16(const uint8_t *p) { return (uint16_t)(p[0] | p[1] << 8); }
static float rdf(const uint8_t *p) { uint32_t u = rd32(p); float f; memcpy(&f, &u, sizeof f); return f; }

bool smp_bank_parse(smp_bank_t *b, const void *blob, size_t n)
{
    const uint8_t *p = (const uint8_t *)blob;
    memset(b, 0, sizeof *b);
    if (!p || n < SMP_HEADER || ((uintptr_t)p & 1u)) return false;
    if (memcmp(p, "STMP", 4) != 0 || rd16(p + 4) != SMP_VERSION) return false;
    uint16_t ns = rd16(p + 6), nz = rd16(p + 8);
    uint32_t data_off = rd32(p + 12), data_n = rd32(p + 16);
    if (ns > SMP_SETS_MAX || nz > SMP_ZONES_MAX) return false;
    size_t hdr = SMP_HEADER + (size_t)ns * SMP_SET_REC + (size_t)nz * SMP_ZONE_REC;
    if (data_off < hdr || (data_off & 1u) || (size_t)data_off + (size_t)data_n * 2u > n) return false;
    const int16_t *data = (const int16_t *)(const void *)(p + data_off);

    const uint8_t *r = p + SMP_HEADER;
    for (int i = 0; i < ns; i++, r += SMP_SET_REC) {
        smp_set_t *s = &b->sets[i];
        memcpy(s->name, r, SMP_NAME - 1);
        s->name[SMP_NAME - 1] = 0;
        s->first = rd16(r + 24);
        s->n = rd16(r + 26);
        s->flags = rd16(r + 28);
        if ((uint32_t)s->first + s->n > nz) return false;
    }
    for (int i = 0; i < nz; i++, r += SMP_ZONE_REC) {
        smp_zone_t *z = &b->zones[i];
        uint32_t off = rd32(r);
        z->len = rd32(r + 4);
        z->loop_start = rd32(r + 8);
        z->loop_end = rd32(r + 12);
        z->rate = rd32(r + 16);
        z->gain = rdf(r + 20);
        z->root = r[24]; z->lo = r[25]; z->hi = r[26]; z->vel_lo = r[27];
        if (z->len < 4 || off > data_n || z->len > data_n - off) return false;
        if (z->loop_end && (z->loop_end > z->len || z->loop_start + 4 > z->loop_end)) return false;
        if (z->rate < 8000u || z->rate > 96000u || !(z->gain >= 0.0f && z->gain <= 16.0f)) return false;
        z->data = data + off;
    }
    b->n_sets = ns;
    b->n_zones = nz;
    return true;
}

static bool same_name(const char *a, const char *b)
{
    for (int i = 0; i < SMP_NAME; i++) {
        if (a[i] != b[i]) return false;
        if (a[i] == 0) return true;
    }
    return true;
}

const smp_set_t *smp_set_find(const smp_bank_t *b, const char *name)
{
    if (!b || !name) return NULL;
    for (int i = 0; i < b->n_sets; i++)
        if (same_name(b->sets[i].name, name)) return &b->sets[i];
    return NULL;
}

const smp_set_t *smp_set_at(const smp_bank_t *b, int idx)
{
    return b && idx >= 0 && idx < b->n_sets ? &b->sets[idx] : NULL;
}

const smp_zone_t *smp_zone_for(const smp_bank_t *b, const smp_set_t *s, int note, int vel)
{
    if (!b || !s) return NULL;
    const smp_zone_t *best = NULL;
    for (int i = 0; i < s->n; i++) {
        const smp_zone_t *z = &b->zones[s->first + i];
        if (note < z->lo || note > z->hi || z->vel_lo > vel) continue;
        if (!best || z->vel_lo > best->vel_lo) best = z;
    }
    return best;
}

/* ---------------------------------------------------------------- la voce ---- */

void smp_note_on(dsp_t *d, dsp_voice_t *v, const uint8_t *p)
{
    dsp_smp_voice_t *s = &v->smp;
    const smp_set_t *set = smp_set_at(d->bank, p[SND_P_RPHEIGHT]);          /* SMPSET */
    s->z = smp_zone_for(d->bank, set, v->note, v->vel);
    s->looping = (uint8_t)(s->z && s->z->loop_end && p[SND_P_RPDISTANCE] == 0);   /* SMPLOOP */
    s->frac = 0.0f;
    s->ended = (uint8_t)(s->z == NULL);
    if (s->z) {                                                           /* SMPSTART: fino al 25 % */
        uint32_t start = (uint32_t)((float)s->z->len * 0.25f * (float)p[SND_P_RPKT] / 127.0f);
        if (s->looping && start > s->z->loop_start) start = s->z->loop_start;
        if (start + 4 >= s->z->len) start = 0;
        s->idx = start;
    } else s->idx = 0;
}

/* rapporto di lettura della voce: altezza in semitoni MIDI (con bend, glide e matrice) */
float smp_ratio(const dsp_t *d, const dsp_voice_t *v, const float *sm, float pitch_semi)
{
    const smp_zone_t *z = v->smp.z;
    if (!z) return 0.0f;
    float tune = (sm[SND_P_RPDECAY] - 64.0f) / 64.0f * 0.5f;              /* SMPTUNE: ±50 cent */
    float semi = pitch_semi + tune - (float)z->root;
    return clampf((float)z->rate * d->inv_fs * expf(semi * DSP_LN2_12), 0.0f, 16.0f);
}

void smp_render(dsp_voice_t *v, float *out)
{
    dsp_smp_voice_t *s = &v->smp;
    const smp_zone_t *z = s->z;
    if (!z || s->ended) { memset(out, 0, DSP_BLOCK * sizeof out[0]); return; }
    const int16_t *x = z->data;
    const uint32_t len = z->len, ls = z->loop_start, le = s->looping ? z->loop_end : 0u;
    const float inc = v->inc[0], g = z->gain * (1.0f / 32768.0f);
    uint32_t i = s->idx;
    float f = s->frac;
    int k = 0;
    for (; k < DSP_BLOCK; k++) {
        if (le) { if (i >= le) i -= le - ls; }                            /* il loop viene prima della fine */
        else if (i + 2 >= len) { s->ended = 1; break; }
        uint32_t i1 = i + 1 < len ? i + 1 : len - 1, i2 = i + 2 < len ? i + 2 : len - 1;
        float xm = (float)x[i ? i - 1 : 0], x0 = (float)x[i], x1 = (float)x[i1], x2 = (float)x[i2];
        float c1 = 0.5f * (x1 - xm);
        float c2 = xm - 2.5f * x0 + 2.0f * x1 - 0.5f * x2;
        float c3 = 0.5f * (x2 - xm) + 1.5f * (x0 - x1);
        out[k] = (((c3 * f + c2) * f + c1) * f + x0) * g;
        f += inc;
        uint32_t a = (uint32_t)f;
        i += a;
        f -= (float)a;
    }
    for (; k < DSP_BLOCK; k++) out[k] = 0.0f;
    s->idx = i;
    s->frac = f;
}
