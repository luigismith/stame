/* gest.c — stato unito delle sorgenti (MIDI-102), riconoscitore dei gesti (MIDI-103) e fuoco
 * (MIDI-104, MIDI-105). */
#include "gest.h"

void gest_init(gest_t *g)
{
    memset(g, 0, sizeof *g);
    g->focus = ENC_SOUND;
    g->owner = ENC_COUNT;
    for (int s = 0; s < SRC_COUNT; s++) g->fdown[s] = ENC_COUNT;
}

void gest_set_owner(gest_t *g, uint8_t enc, bool is_list)
{
    g->owner = enc < ENC_COUNT ? enc : (uint8_t)ENC_COUNT;
    g->owner_list = g->owner < ENC_COUNT && is_list;
}

uint8_t gest_target(const gest_t *g)
{
    return g->owner < ENC_COUNT ? g->owner : g->focus;
}

/* ----------------------------------------------------------------- uscita */

static void put_src(pnl_out_t *o, uint8_t src, uint8_t type, uint8_t a, int16_t b)
{
    uint8_t keep = o->src;
    o->src = src;
    pnl_put(o, type, a, b);
    o->src = keep;
}

static void pass(pnl_out_t *o, const pnl_event_t *e)
{
    if (o->n >= o->max) { if (o->dropped) (*o->dropped)++; return; }
    o->ev[o->n++] = *e;
}

/* ------------------------------------------------------------ riconoscitore */

static void set_now(gest_t *g, uint32_t t_us)
{
    if (!g->started || pnl_dt(t_us, g->now) > 0) g->now = t_us;
    g->started = 1;
}

/* soglie a tempo (MIDI-103, "ogni 10 ms") */
static void advance(gest_t *g, pnl_out_t *o)
{
    for (uint8_t e = 0; e < ENC_COUNT; e++) {
        int32_t held_for = pnl_dt(g->now, g->t_down[e]);
        if (g->st[e] == GS_DOWN && !g->rotated[e] && held_for >= (int32_t)GEST_T_HOLD_US) {
            put_src(o, g->down_src[e], G_HOLD, e, 0);
            g->st[e] = GS_HELD;
        }
        if (g->st[e] == GS_HELD && e == ENC_LOOP && !g->long_done[e] && held_for >= (int32_t)GEST_T_HOLD2_US) {
            put_src(o, g->down_src[e], G_HOLD_LONG, e, 0);
            g->long_done[e] = 1;
        }
    }
}

static bool enc_pressed(const gest_t *g, uint8_t e)
{
    for (int s = 0; s < SRC_COUNT; s++)
        if (g->cnt[e][s]) return true;
    return false;
}

/* l'encoder passa da libero a premuto in almeno una sorgente: PNL_ENC_DOWN per il riconoscitore */
static void enc_down(gest_t *g, uint8_t e, uint8_t src)
{
    bool was = enc_pressed(g, e);
    if (g->cnt[e][src] < UINT8_MAX) g->cnt[e][src]++;
    if (was) return;
    g->st[e] = GS_DOWN;
    g->t_down[e] = g->now;
    g->rotated[e] = 0;
    g->long_done[e] = 0;
    g->down_src[e] = src;
}

/* lo rilasciano tutte: PNL_ENC_UP per il riconoscitore; un rilascio sintetico non dà G_PRESS */
static void enc_up(gest_t *g, pnl_out_t *o, uint8_t e, uint8_t src, bool all, bool synth)
{
    if (!g->cnt[e][src]) return;
    g->cnt[e][src] = all ? 0 : (uint8_t)(g->cnt[e][src] - 1);
    if (enc_pressed(g, e)) return;
    if (g->st[e] == GS_DOWN && !g->rotated[e] && !synth) pnl_put(o, G_PRESS, e, 0);
    pnl_put(o, G_RELEASE, e, 0);
    g->st[e] = GS_IDLE;
}

static void enc_turn(gest_t *g, pnl_out_t *o, uint8_t e, int16_t n)
{
    switch (g->st[e]) {
    case GS_IDLE: pnl_put(o, G_TURN, e, n); break;
    case GS_DOWN: g->rotated[e] = 1; pnl_put(o, G_PRESS_TURN, e, n); break;
    default: break;                                               /* GS_HELD: ignorato [D] */
    }
}

/* tasti e tasti accordo: escono al primo che preme e all'ultimo che rilascia (MIDI-102) */
static void merged(pnl_out_t *o, uint8_t *bits, uint8_t src, bool down, const pnl_event_t *e)
{
    uint8_t before = *bits, bit = (uint8_t)(1u << src);
    *bits = down ? (uint8_t)(before | bit) : (uint8_t)(before & ~bit);
    if ((before == 0) != (*bits == 0)) pass(o, e);
}

/* sorgente persa: rilascia ciò che tiene ancora, senza G_PRESS (rete di sicurezza dopo on_lost) */
static void release_src(gest_t *g, pnl_out_t *o, uint8_t s)
{
    uint8_t bit = (uint8_t)(1u << s);
    for (uint8_t e = 0; e < ENC_COUNT; e++) enc_up(g, o, e, s, true, true);
    g->fdown[s] = ENC_COUNT;
    for (uint8_t pc = 0; pc < 12; pc++)
        if (g->keys[pc] & bit) {
            g->keys[pc] &= (uint8_t)~bit;
            if (!g->keys[pc]) pnl_put(o, PNL_KEY_UP, pc, 0);
        }
    for (uint8_t c = 0; c < CHB_COUNT; c++)
        if (g->chords[c] & bit) {
            g->chords[c] &= (uint8_t)~bit;
            if (!g->chords[c]) pnl_put(o, PNL_CHORD_UP, c, 0);
        }
}

int gest_feed(gest_t *g, const pnl_event_t *e, pnl_event_t *out, int max)
{
    pnl_out_t o;
    set_now(g, e->t_us);
    pnl_out_init(&o, out, max, e->src, g->now, &g->dropped);
    advance(g, &o);

    uint8_t s = e->src;
    if (s >= SRC_COUNT) return o.n;

    switch (e->type) {
    case PNL_ENC_TURN: {
        uint8_t a = e->a & (uint8_t)~PNL_F_VERTICAL;
        int16_t n = e->b;
        if (n == 0) break;
        if (a == ENC_FOCUS) {
            a = gest_target(g);
            if ((e->a & PNL_F_VERTICAL) && g->owner_list) n = (int16_t)-n;   /* MIDI-105: su = voce precedente */
        }
        if (a < ENC_COUNT) enc_turn(g, &o, a, n);
        break;
    }
    case PNL_ENC_DOWN:
        if (e->a == ENC_FOCUS) {
            if (g->fdown[s] < ENC_COUNT) break;                   /* già premuto da questa sorgente */
            g->fdown[s] = gest_target(g);
            enc_down(g, g->fdown[s], s);
        } else if (e->a < ENC_COUNT) {
            g->focus = e->a;                                      /* MIDI-104: la pressione porta il fuoco */
            /* e lo toglie all'overlay di un altro encoder: dopo aver girato Sound e premuto un altro
             * tasto, m2 girava ancora Sound per 3,4 s mentre la cornice del fuoco stava altrove. Le
             * liste e i menu restano padroni finché non si chiudono */
            if (g->owner < ENC_COUNT && !g->owner_list && g->owner != e->a) g->owner = ENC_COUNT;
            enc_down(g, e->a, s);
        }
        break;
    case PNL_ENC_UP: {
        bool synth = e->b == PNL_B_SYNTH;
        if (e->a == ENC_FOCUS) {
            uint8_t a = g->fdown[s];
            g->fdown[s] = ENC_COUNT;
            if (a < ENC_COUNT) enc_up(g, &o, a, s, false, synth);
        } else if (e->a < ENC_COUNT) {
            enc_up(g, &o, e->a, s, false, synth);
        }
        break;
    }
    case PNL_FOCUS_STEP: {
        int f = (g->focus + e->b) % ENC_COUNT;
        g->focus = (uint8_t)(f < 0 ? f + ENC_COUNT : f);
        break;
    }
    case PNL_KEY_DOWN: case PNL_KEY_UP:
        if (e->a < 12) merged(&o, &g->keys[e->a], s, e->type == PNL_KEY_DOWN, e);
        break;
    case PNL_CHORD_DOWN: case PNL_CHORD_UP:
        if (e->a < CHB_COUNT) merged(&o, &g->chords[e->a], s, e->type == PNL_CHORD_DOWN, e);
        break;
    case PNL_SRC_LOST:
        if (e->a < SRC_COUNT) release_src(g, &o, e->a);
        pass(&o, e);
        break;
    default:                                                      /* BACK, BEND, MOD, SUSTAIN, MACRO, CONNECTED */
        pass(&o, e);
        break;
    }
    return o.n;
}

void gest_resync(gest_t *g, uint32_t t_us)
{
    g->now = t_us;
    g->started = 1;
    for (uint8_t e = 0; e < ENC_COUNT; e++) if (g->st[e] != GS_IDLE) g->t_down[e] = t_us;
}

int gest_tick(gest_t *g, uint32_t t_us, pnl_event_t *out, int max)
{
    pnl_out_t o;
    set_now(g, t_us);
    pnl_out_init(&o, out, max, SRC_COUNT, g->now, &g->dropped);
    advance(g, &o);
    return o.n;
}
