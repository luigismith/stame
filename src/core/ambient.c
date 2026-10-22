/* ambient.c — il modulo AMBIENT (ambient.h). Tavolozze, periodi e registri sono di Stame. */
#include "ambient.h"
#include "acc.h"

#define TB(t) (uint8_t)(1u << ACC_##t)                /* bit di un tipo */
#define EB(e) (uint8_t)(1u << ACC_##e)                /* bit di un'estensione */
#define M7  EB(E7MAJ)
#define m7  EB(E7MIN)
#define N9  EB(E9)
#define E6  EB(E6)

/* una voce della tavolozza: semitoni sopra la tonica, tipo, estensioni, peso (0 = vuota) */
typedef struct { uint8_t deg, types, exts, w; } pal_t;
#define PAL_N 6

/* [atmosfera][0 maggiore, 1 minore]: la prima voce è casa. Accordi di quattro o cinque note, quasi tutti nella
 * scala della tonalità: maj9, m9, sus con la nona (sus4 e 9, le quarte che luccicano), add9, 6/9 */
static const pal_t PAL[AMB_MOODS][2][PAL_N] STAME_ROM = {
    {   /* Float: aperto, sospeso; il II maggiore dà un filo di lidio */
        { { 0, TB(MAJ), M7 | N9, 3 }, { 5, TB(MAJ), M7 | N9, 3 }, { 9, TB(MIN), m7 | N9, 2 },
          { 7, TB(SUS), N9, 2 }, { 4, TB(MIN), m7, 1 }, { 2, TB(MAJ), N9, 1 } },
        { { 0, TB(MIN), m7 | N9, 3 }, { 3, TB(MAJ), M7 | N9, 3 }, { 8, TB(MAJ), M7, 3 },
          { 10, TB(SUS), N9, 2 }, { 5, TB(MIN), m7 | N9, 2 }, { 5, TB(MAJ), N9, 1 } } },
    {   /* Dusk: il tramonto, malinconico e caldo; in maggiore casa è il relativo minore */
        { { 9, TB(MIN), m7 | N9, 3 }, { 5, TB(MAJ), M7, 3 }, { 0, TB(MAJ), N9, 2 },
          { 4, TB(MIN), m7, 2 }, { 2, TB(MIN), m7 | N9, 2 }, { 7, TB(SUS), 0, 1 } },
        { { 0, TB(MIN), m7 | N9, 3 }, { 8, TB(MAJ), M7, 3 }, { 5, TB(MIN), m7, 2 },
          { 3, TB(MAJ), N9, 2 }, { 7, TB(MIN), m7, 2 }, { 10, TB(MAJ), E6 | N9, 1 } } },
    {   /* Deep: scuro e lento; in minore il II bemolle frigio, raro */
        { { 9, TB(MIN), N9, 3 }, { 5, TB(MAJ), M7, 2 }, { 4, TB(MIN), m7, 2 },
          { 2, TB(MIN), m7 | N9, 2 }, { 0, TB(MAJ), M7, 1 }, { 7, TB(SUS), 0, 1 } },
        { { 0, TB(MIN), N9, 3 }, { 8, TB(MAJ), M7, 2 }, { 5, TB(MIN), m7 | N9, 2 },
          { 0, TB(MIN), m7, 2 }, { 10, TB(SUS), 0, 1 }, { 1, TB(MAJ), M7, 1 } } },
    {   /* Glass: sus con la nona sui gradi dove stanno nella scala: quarte e seconde di vetro */
        { { 0, TB(SUS), N9, 3 }, { 7, TB(SUS), N9, 3 }, { 9, TB(SUS), N9, 3 },
          { 2, TB(SUS), N9, 2 }, { 5, TB(MAJ), N9, 2 }, { 4, TB(MIN), m7, 1 } },
        { { 0, TB(SUS), N9, 3 }, { 10, TB(SUS), N9, 3 }, { 5, TB(SUS), N9, 2 },
          { 3, TB(MAJ), N9, 2 }, { 8, TB(MAJ), M7, 1 }, { 7, TB(MIN), m7, 1 } } },
    {   /* Drone: la tonica non si muove, cambiano solo i colori sopra */
        { { 0, TB(MAJ), N9, 3 }, { 0, TB(SUS), N9, 3 }, { 0, TB(MAJ), M7, 2 },
          { 0, TB(MAJ), E6 | N9, 2 }, { 0, TB(MAJ), M7 | N9, 2 }, { 0, TB(SUS), 0, 1 } },
        { { 0, TB(MIN), N9, 3 }, { 0, TB(SUS), N9, 3 }, { 0, TB(MIN), m7, 2 },
          { 0, TB(MIN), m7 | N9, 2 }, { 0, TB(MIN), E6, 1 }, { 0, TB(SUS), 0, 1 } } },
    {   /* Tide: due accordi che vanno e vengono come la marea, ogni tanto un terzo */
        { { 0, TB(MAJ), M7 | N9, 4 }, { 5, TB(MAJ), M7 | N9, 4 }, { 9, TB(MIN), m7 | N9, 1 },
          { 0, 0, 0, 0 }, { 0, 0, 0, 0 }, { 0, 0, 0, 0 } },
        { { 0, TB(MIN), m7 | N9, 4 }, { 8, TB(MAJ), M7 | N9, 4 }, { 5, TB(MIN), m7 | N9, 1 },
          { 0, 0, 0, 0 }, { 0, 0, 0, 0 }, { 0, 0, 0, 0 } } },
};

static const char *const MOOD_NAME[AMB_MOODS] = { "Float", "Dusk", "Deep", "Glass", "Drone", "Tide" };

/* registro delle note sparse per atmosfera: da lo a hi compresi */
static const uint8_t REG_LO[AMB_MOODS] STAME_ROM = { 72, 67, 55, 76, 64, 69 };
static const uint8_t REG_HI[AMB_MOODS] STAME_ROM = { 96, 91, 79, 100, 88, 93 };

/* i giri delle sei voci in crome: numeri primi, così i periodi non si ritrovano allineati che dopo ore */
static const uint8_t GIRO[AMB_VOICES] STAME_ROM = { 23, 29, 31, 37, 41, 43 };

/* quarti per accordo secondo il movimento, 0 = per sempre */
static const uint8_t BEATS[AMB_MOTION_MAX + 1] STAME_ROM = { 0, 64, 48, 40, 32, 24, 16, 12, 8, 6, 4 };

static uint32_t xs(uint32_t *r)
{
    uint32_t x = *r ? *r : 0x2545F491u;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    *r = x;
    return x;
}

static int clampi(int v, int a, int b) { return v < a ? a : v > b ? b : v; }

static int popcount12(uint16_t x)
{
    int n = 0;
    for (; x; x &= (uint16_t)(x - 1)) n++;
    return n;
}

const char *amb_mood_name(int mood) { return mood >= 0 && mood < AMB_MOODS ? MOOD_NAME[mood] : ""; }

uint16_t amb_chord_pcs(amb_chord_t c)
{
    uint16_t rel = 0;
    for (int t = 0; t < ACC_TYPE_COUNT; t++)
        if (c.types >> t & 1u) rel |= acc_chord_mask(t, c.exts, false);
    if (!c.types) rel = 1;                                        /* senza tipo: la nota sola */
    uint32_t r = (uint32_t)rel << (c.key % 12u);
    return (uint16_t)((r | r >> 12) & 0xFFFu);
}

uint16_t amb_chord_beats(int motion, uint32_t salt)
{
    static const int8_t PIU[5] = { -4, 0, 0, 4, 8 };             /* gli accordi lunghi durano una battuta in più o in meno */
    int b = BEATS[clampi(motion, 0, AMB_MOTION_MAX)];
    if (b >= 16) b += PIU[salt % 5u];
    return (uint16_t)b;
}

static const pal_t *pal(const amb_harm_t *h) { return PAL[h->mood % AMB_MOODS][h->minor ? 1 : 0]; }

static amb_chord_t chord_of(const amb_harm_t *h, int i)
{
    const pal_t *p = &pal(h)[i];
    amb_chord_t c = { (uint8_t)((h->tonic + p->deg) % 12u), p->types, p->exts, 0 };
    return c;
}

void amb_harm_init(amb_harm_t *h, int mood, int var, int tonic, bool minor)
{
    h->mood = (uint8_t)clampi(mood, 0, AMB_MOODS - 1);
    h->var = (uint8_t)clampi(var, 0, AMB_VAR_MAX);
    h->tonic = (uint8_t)(((tonic % 12) + 12) % 12);
    h->minor = minor ? 1u : 0u;
    h->cur = h->prev = -1;
    h->pcs = 0;
    h->rng = 0x9E3779B9u * (uint32_t)(h->var + 1) ^ (uint32_t)h->mood << 20 ^ (uint32_t)h->tonic << 8 ^ h->minor;
    xs(&h->rng);
}

static amb_chord_t take(amb_harm_t *h, int i)
{
    amb_chord_t c = chord_of(h, i);
    c.vel = (uint8_t)(64 + xs(&h->rng) % 21u);                    /* tocco morbido, mai uguale */
    h->prev = h->cur;
    h->cur = (int8_t)i;
    h->pcs = amb_chord_pcs(c);
    return c;
}

amb_chord_t amb_harm_first(amb_harm_t *h) { return take(h, 0); }

amb_chord_t amb_harm_next(amb_harm_t *h)
{
    const pal_t *p = pal(h);
    uint32_t score[PAL_N], tot = 0;
    for (int i = 0; i < PAL_N; i++) {
        score[i] = 0;
        if (!p[i].w || i == h->cur) continue;
        int common = popcount12((uint16_t)(h->pcs & amb_chord_pcs(chord_of(h, i))));
        score[i] = p[i].w * (2u + 2u * (uint32_t)common);
        if (i == h->prev) score[i] = score[i] / 2u ? score[i] / 2u : 1u;   /* tornare indietro si può, meno */
        tot += score[i];
    }
    if (!tot) return take(h, h->cur >= 0 ? h->cur : 0);           /* una tavolozza di una voce sola */
    uint32_t r = xs(&h->rng) % tot;
    int i = 0;
    while (i < PAL_N - 1 && r >= score[i]) r -= score[i++];
    return take(h, i);
}

void amb_harm_follow(amb_harm_t *h, uint16_t pcs)
{
    h->prev = h->cur;
    h->cur = -1;
    h->pcs = pcs & 0xFFFu;
    for (int i = 0; i < PAL_N; i++)                               /* l'accordo è della tavolozza: non lo ripete subito */
        if (pal(h)[i].w && amb_chord_pcs(chord_of(h, i)) == h->pcs) h->cur = (int8_t)i;
}

/* ---- le note sparse ---- */

static int voices(int dens) { return dens <= 0 ? 0 : 1 + (dens - 1) * (AMB_VOICES - 1) / 9; }

/* il giro della voce i: più denso, più corto (fino a poco più della metà) */
static uint32_t period(int i, int dens)
{
    int scala = 100 - 5 * clampi(dens - 1, 0, 9);
    return (uint32_t)GIRO[i] * 48u * (uint32_t)scala / 100u;
}

static uint16_t penta(int tonic, bool minor)
{
    uint16_t rel = minor ? 0x4A9u : 0x295u;                       /* 0 3 5 7 10 o 0 2 4 7 9 */
    uint32_t r = (uint32_t)rel << (((tonic % 12) + 12) % 12);
    return (uint16_t)((r | r >> 12) & 0xFFFu);
}

void amb_bloom_init(amb_bloom_t *b, uint32_t seed)
{
    memset(b, 0, sizeof *b);
    b->rng = seed ^ 0xA5A5F00Du;
    xs(&b->rng);
    for (int i = 0; i < AMB_VOICES; i++) b->v[i].note = b->v[i].last = 0xFF;
}

static void schedule(amb_bloom_t *b, uint32_t t)
{
    for (int i = 0; i < AMB_VOICES; i++)                          /* la prima entro mezzo quarto, le altre sparse */
        b->v[i].next = t + 48u + (uint32_t)i * 160u + (i ? xs(&b->rng) % 96u : 0u);
}

void amb_bloom_set(amb_bloom_t *b, bool on, int dens, int mood, int tonic, bool minor, uint32_t t)
{
    bool start = on && !b->on;
    b->on = on ? 1u : 0u;
    b->dens = (uint8_t)clampi(dens, 0, AMB_DENS_MAX);
    b->mood = (uint8_t)clampi(mood, 0, AMB_MOODS - 1);
    b->tonic = (uint8_t)(((tonic % 12) + 12) % 12);
    b->minor = minor ? 1u : 0u;
    if (start) schedule(b, t);
}

void amb_bloom_seed(amb_bloom_t *b, int var, uint32_t t)
{
    b->rng = 0x85EBCA6Bu * (uint32_t)(clampi(var, 0, AMB_VAR_MAX) + 1) ^ 0xC2B2AE35u;
    xs(&b->rng);
    for (int i = 0; i < AMB_VOICES; i++) b->v[i].last = 0xFF;
    if (b->on) schedule(b, t);
}

void amb_bloom_forget(amb_bloom_t *b)
{
    for (int i = 0; i < AMB_VOICES; i++) b->v[i].note = 0xFF;
}

/* la nota del prossimo giro: fra quelle del registro nelle classi dell'accordo o della pentatonica, vicina
 * all'ultima (ferma, un passo o due), e non una che già suona */
static int pick(amb_bloom_t *b, amb_voice_t *v, const uint8_t busy[128])
{
    uint8_t cand[48];
    int n = 0;
    uint16_t pcs = (uint16_t)(b->chord | penta(b->tonic, b->minor != 0));
    for (int x = REG_LO[b->mood]; x <= REG_HI[b->mood] && n < 48; x++)
        if (pcs >> (x % 12) & 1u) cand[n++] = (uint8_t)x;
    if (!n) return -1;
    int j = n / 2 + (int)(xs(&b->rng) % 3u) - 1;
    if (v->last != 0xFF) {
        int best = 999;
        for (int k = 0; k < n; k++) {
            int d = cand[k] > v->last ? cand[k] - v->last : v->last - cand[k];
            if (d < best) { best = d; j = k; }
        }
        static const int8_t PASSO[10] = { 0, 0, 0, 0, 1, 1, -1, -1, 2, -2 };
        j += PASSO[xs(&b->rng) % 10u];
    }
    j = clampi(j, 0, n - 1);
    for (int k = 0; k < 3; k++) {                                 /* già tenuta, anche da un'altra voce: un vicino */
        int c = j + (k == 1 ? 1 : k == 2 ? -1 : 0);
        if (c < 0 || c >= n || busy[cand[c]]) continue;
        bool mia = false;
        for (int i = 0; i < AMB_VOICES; i++) if (b->v[i].note == cand[c] && &b->v[i] != v) mia = true;
        if (!mia) return cand[c];
    }
    return -1;
}

int amb_bloom_run(amb_bloom_t *b, uint32_t t, uint16_t chord, const uint8_t busy[128], amb_ev_t *out, int max)
{
    int k = 0;
    if (chord) b->chord = chord & 0xFFFu;
    int nv = voices(b->dens);
    for (int i = 0; i < AMB_VOICES && k < max; i++) {
        amb_voice_t *v = &b->v[i];
        if (v->note != 0xFF && (int32_t)(t - v->off) >= 0) {
            out[k].note = v->note; out[k].vel = 0; k++;
            v->note = 0xFF;
        }
        if (!b->on || (int32_t)(t - v->next) < 0 || k >= max) continue;
        v->next = t + period(i, b->dens);
        if (i >= nv || xs(&b->rng) % 100u < 15u) continue;         /* le voci in più aspettano; ogni tanto un giro tace */
        int note = pick(b, v, busy);
        if (note < 0) continue;
        if (v->note != 0xFF) {
            out[k].note = v->note; out[k].vel = 0;
            if (++k >= max) { v->note = 0xFF; continue; }
        }
        int vel = 34 + (int)(xs(&b->rng) % 31u) + 2 * b->dens;
        out[k].note = (uint8_t)note;
        out[k].vel = (uint8_t)(vel > 96 ? 96 : vel);
        k++;
        v->note = v->last = (uint8_t)note;
        v->off = t + 192u + xs(&b->rng) % 385u;                   /* da due a sei quarti; la coda la fa il suono */
    }
    return k;
}
