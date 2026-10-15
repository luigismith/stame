/* perf.c — la performance sul treble (perf.h; specifica 10, §9). */
#include "perf.h"

/* ACC-178: i 13 pattern provvisori, 16 passi da 1/16. Notazione della specifica: '.' pausa, cifre =
 * indici suonati insieme, '!' accento (127), '\'' debole (70), senza segno 100. */
static const char *const PATTERN[13] STAME_ROM = {
    "012! . . 012 . . 012 . 012! . . 012 . . 012 .",
    "0! 12 . 12 0 12 . 12 0! 12 . 12 0 12 . 12",
    "0! . 12 . 0 . 12 . 0! . 12 . 0 . 12 .",
    "012! . . . . . 012 . . . 012 . . . . .",
    "0! 1 2 1 0 1 2 1 0! 1 2 1 0 1 2 1",
    "01! . 2 . 01 . 2 2 01! . 2 . 01 . 2 .",
    "0! . . 0 . . 0 . 12! . . 12 . . 12 .",
    "012! . 012' . 012 . 012' . 012! . 012' . 012 . 012' .",
    "0! 2 1 2 0 2 1 2 0! 2 1 2 0 2 1 2",
    ". 012! . 012 . 012! . 012 . 012! . 012 . 012! . 012",
    "0! . 1 . 2 . 3 . 2 . 1 . 0 . 1 .",
    "012! . . . . . . . 01 . 2 . 01 . 2 .",
    "02! . 1 02 . 1 02 . 1 02 . 1 02 . 1 .",
};

#define PATTERN_GATE 20u        /* ACC-176 [V] */
#define PATTERN_STEP 24u

/* passo s (0…15) del pattern: maschera degli indici e velocity del passo; 0 = pausa */
static uint8_t pattern_step(int pat, int s, uint8_t *vel)
{
    const char *p = PATTERN[pat];
    for (int k = 0; *p; k++) {
        while (*p == ' ') p++;
        uint8_t mask = 0;
        *vel = 100;
        while (*p && *p != ' ') {
            if (*p >= '0' && *p <= '7') mask |= (uint8_t)(1u << (*p - '0'));
            else if (*p == '!') *vel = 127;
            else if (*p == '\'') *vel = 70;
            p++;
        }
        if (k == s) return mask;
    }
    return 0;
}

static bool is_on(const perf_t *p, uint8_t note) { return (p->out_on[note >> 3] >> (note & 7)) & 1u; }

static int emit(perf_t *p, perf_ev_t *out, int max, int k, uint32_t tick, uint8_t note, uint8_t vel, bool on)
{
    if (note > 127) return k;
    uint8_t bit = (uint8_t)(1u << (note & 7));
    if (on && is_on(p, note) && k < max) {                       /* già accesa: prima si spegne */
        out[k].tick = tick; out[k].note = note; out[k].vel = 0; out[k].on = 0; k++;
    }
    if (!on && !is_on(p, note)) return k;
    if (k >= max) { p->dropped++; return k; }
    out[k].tick = tick; out[k].note = note; out[k].vel = vel; out[k].on = on;
    if (on) p->out_on[note >> 3] |= bit; else p->out_on[note >> 3] &= (uint8_t)~bit;
    return k + 1;
}

static void sched(perf_t *p, uint32_t tick, uint8_t note, uint8_t vel, bool on)
{
    if (p->qn >= PERF_SCHED_MAX) { p->dropped++; return; }        /* ACC-183 */
    int i = p->qn;
    while (i > 0 && (int32_t)(p->q[i - 1].tick - tick) > 0) { p->q[i] = p->q[i - 1]; i--; }
    p->q[i].tick = tick; p->q[i].note = note; p->q[i].vel = vel; p->q[i].on = on;
    p->qn++;
}

/* spegne tutto ciò che è acceso e cancella gli eventi futuri */
static int all_off(perf_t *p, uint32_t tick, perf_ev_t *out, int max, int k)
{
    p->qn = 0;
    for (int n = 0; n < 128; n++) if (is_on(p, (uint8_t)n)) k = emit(p, out, max, k, tick, (uint8_t)n, 0, false);
    return k;
}

void perf_init(perf_t *p, uint32_t seed)
{
    memset(p, 0, sizeof *p);
    p->rng = seed ? seed : 1u;
}

void perf_set(perf_t *p, uint8_t mode, uint8_t amount)
{
    p->next_mode = mode < PM_COUNT ? mode : PM_OFF;
    p->next_amount = amount;
}

static uint32_t xs(perf_t *p)
{
    uint32_t x = p->rng;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    return p->rng = x;
}

/* sequenza di strum, harp e slop: N, poi N+12 (STRUM2), poi N+24 (HARP) */
static int seq_up(const perf_t *p, uint8_t *seq, int oct)
{
    int k = 0;
    for (int o = 0; o < oct; o++)
        for (int i = 0; i < p->n && k < PERF_MAX_NOTES; i++) seq[k++] = (uint8_t)(p->notes[i] + 12 * o);
    return k;
}

/* base dell'arpeggio: N, oppure N ∪ N+12 (ARP2), crescente (ACC-172) */
static int arp_base(const perf_t *p, uint8_t *b)
{
    return seq_up(p, b, p->mode == PM_ARP2 ? 2 : 1);
}

/* nota del passo s dell'arpeggio secondo il tipo (amount 1…6, ACC-171) */
static uint8_t arp_note(const perf_t *p, uint32_t s)
{
    uint8_t b[PERF_MAX_NOTES];
    int m = arp_base(p, b);
    if (m == 0) return 0;
    int type = (p->amount - 1) % 3;                               /* 0 Up, 1 Down, 2 UpDown */
    if (type == 0) return b[s % (uint32_t)m];
    if (type == 1) return b[m - 1 - (int)(s % (uint32_t)m)];
    int cyc = m <= 2 ? m : 2 * m - 2;                             /* estremi non ripetuti */
    int i = (int)(s % (uint32_t)cyc);
    return b[i < m ? i : cyc - i];
}

int perf_chord(perf_t *p, uint32_t tick, const uint8_t *notes, uint8_t n, uint8_t vel, bool key_down,
               bool legato, perf_ev_t *out, int max)
{
    int k = 0;
    if (n > 8) n = 8;
    bool was_seq = p->active && (p->mode == PM_ARP || p->mode == PM_ARP2 || p->mode == PM_PATTERN);
    if (key_down) { p->mode = p->next_mode; p->amount = p->next_amount ? p->next_amount : 1; }
    p->n = n;
    memcpy(p->notes, notes, n);
    if (key_down || vel) p->vel = vel ? vel : p->vel;

    switch (p->mode) {
    case PM_STRUM: case PM_STRUM2: case PM_SLOP: case PM_HARP: {  /* ripartono dall'inizio (ACC-179) */
        k = all_off(p, tick, out, max, k);
        uint8_t seq[PERF_MAX_NOTES];
        int m = seq_up(p, seq, p->mode == PM_STRUM2 ? 2 : p->mode == PM_HARP ? 3 : 1);
        uint32_t dt = p->mode == PM_HARP ? p->amount : 2u * p->amount;
        for (int i = 0; i < m; i++) {
            uint32_t t = tick + (uint32_t)i * dt;
            if (p->mode == PM_SLOP) t = tick + (uint32_t)i * 2u + xs(p) % (3u * p->amount + 1u);   /* ACC-169 */
            if (t == tick) k = emit(p, out, max, k, tick, seq[i], p->vel, true);
            else sched(p, t, seq[i], p->vel, true);
        }
        p->active = 0;
        break;
    }
    case PM_ARP: case PM_ARP2: case PM_PATTERN:
        /* passo 0 al tasto (ACC-173), e anche quando non c'era una sequenza da continuare: passo e
         * tempo vecchi facevano recuperare in un colpo tutti i passi persi */
        if ((key_down && !(legato && was_seq)) || !was_seq) {
            k = all_off(p, tick, out, max, k);
            p->step = 0;
            p->next = tick;
        } else {                                                  /* stessa fase e stesso indice */
            for (int i = 0; i < p->qn; ) {                        /* le note aperte si chiudono ora */
                if (!p->q[i].on) {
                    k = emit(p, out, max, k, tick, p->q[i].note, 0, false);
                    memmove(&p->q[i], &p->q[i + 1], sizeof p->q[0] * (size_t)(p->qn - i - 1));
                    p->qn--;
                } else i++;
            }
        }
        p->active = n > 0;
        break;
    default: {                                                    /* OFF: accordo a blocco */
        /* niente in coda dal modo di prima (strum, arpeggio): si spegne ora tutto ciò che suona e non
         * è nell'accordo, comprese le note di un arpeggio o di uno strum su due ottave */
        p->qn = 0;
        for (int nn = 0; nn < 128; nn++) {
            if (!is_on(p, (uint8_t)nn)) continue;
            bool keep = false;
            for (int j = 0; j < n; j++) if (notes[j] == nn) keep = true;
            if (!keep) k = emit(p, out, max, k, tick, (uint8_t)nn, 0, false);
        }
        for (int j = 0; j < n; j++)
            if (!is_on(p, notes[j]) || key_down) k = emit(p, out, max, k, tick, notes[j], p->vel, true);
        p->active = 0;
        break;
    }
    }
    return k;
}

int perf_release(perf_t *p, uint32_t tick, perf_ev_t *out, int max)
{
    p->n = 0;
    p->active = 0;
    return all_off(p, tick, out, max, 0);
}

int perf_run(perf_t *p, uint32_t tick, perf_ev_t *out, int max)
{
    int k = 0;
    while (p->qn > 0 && (int32_t)(tick - p->q[0].tick) >= 0) {
        perf_ev_t e = p->q[0];
        memmove(&p->q[0], &p->q[1], sizeof p->q[0] * (size_t)(p->qn - 1));
        p->qn--;
        k = emit(p, out, max, k, e.tick, e.note, e.vel, e.on);
    }
    if (!p->active || p->n == 0) return k;
    if ((int32_t)(tick - p->next) > 48) p->next = tick;          /* mai più di un passo da recuperare */
    while ((int32_t)(tick - p->next) >= 0) {
        if (p->mode == PM_PATTERN) {                              /* ACC-175…177 */
            uint8_t vs = 100, mask = pattern_step((p->amount - 1) % 13, (int)(p->step % 16u), &vs);
            uint8_t v = (uint8_t)((vs * p->vel + 63) / 127);
            if (v < 1) v = 1;
            for (int i = 0; i < 8; i++) {
                if (!(mask >> i & 1)) continue;
                uint8_t note = (uint8_t)(p->notes[i % p->n] + 12 * (i / p->n));   /* ACC-176 */
                k = emit(p, out, max, k, p->next, note, v, true);
                sched(p, p->next + PATTERN_GATE, note, 0, false);
            }
            p->next += PATTERN_STEP;
        } else {                                                  /* ACC-171, ACC-172 */
            uint32_t st = p->amount <= 3 ? 48u : 24u;
            uint8_t note = arp_note(p, p->step);
            k = emit(p, out, max, k, p->next, note, p->vel, true);
            sched(p, p->next + st / 2u, note, 0, false);          /* gate 50 % */
            p->next += st;
        }
        p->step++;
    }
    return k;
}
