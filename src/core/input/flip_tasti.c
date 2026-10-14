/* flip_tasti.c — tasti della Flip, schema a fuoco sempre attivo (sezione 40, §9.1). */
#include "flip_tasti.h"

/* indici interni dei tasti usati dallo schema a fuoco, e i loro codici */
enum { F_UP, F_DOWN, F_LEFT, F_RIGHT, F_A, F_B, F_Y, F_L1, F_R1, F_SELECT, F_START, F_MENU, F_COUNT };

static const uint16_t CODE[F_COUNT] STAME_ROM = {
    PAD_UP, PAD_DOWN, PAD_LEFT, PAD_RIGHT, PAD_A, PAD_B, PAD_Y, PAD_L1, PAD_R1,
    PAD_SELECT, PAD_START, PAD_MENU
};

/* tasti che tengono premuto un encoder (MIDI-092) */
static uint8_t held_enc(int idx)
{
    switch (idx) {
    case F_A:      return ENC_FOCUS;
    case F_Y:      return ENC_BASS_VOICING;
    case F_SELECT: return ENC_OPTIONS;
    case F_START:  return ENC_BPM;
    default:       return ENC_COUNT;
    }
}

/* croce: su e giù sono comandi verticali (MIDI-105), sinistra e destra rotazioni */
static void dpad_step(pnl_out_t *o, int idx)
{
    static const int8_t DIR[4] STAME_ROM = { 1, -1, -1, 1 };
    uint8_t a = idx <= F_DOWN ? (uint8_t)(ENC_FOCUS | PNL_F_VERTICAL) : (uint8_t)ENC_FOCUS;
    pnl_put(o, PNL_ENC_TURN, a, DIR[idx]);
}

static void flip_reset(void *st)
{
    memset(st, 0, sizeof(flip_state_t));
}

static int flip_on_pad(void *st, uint16_t code, int32_t value, uint32_t t_us, pnl_event_t *out, int max)
{
    flip_state_t *s = (flip_state_t *)st;
    pnl_out_t o;
    pnl_out_init(&o, out, max, SRC_FLIP, t_us, &s->dropped);

    if (value != 0 && value != 1) return 0;                       /* 2 = ripetizione del kernel */
    int idx = -1;
    for (int i = 0; i < F_COUNT; i++)
        if (CODE[i] == code) { idx = i; break; }
    if (idx < 0) return 0;                                        /* X, L2, R2, L3, R3, levette */

    bool down = value == 1;
    uint16_t bit = (uint16_t)(1u << idx);
    if (down == ((s->down & bit) != 0)) return 0;
    s->down ^= bit;

    uint8_t enc = held_enc(idx);
    if (enc != ENC_COUNT) {
        pnl_put(&o, down ? PNL_ENC_DOWN : PNL_ENC_UP, enc, 0);
        return o.n;
    }
    if (!down) return 0;
    switch (idx) {
    case F_UP: case F_DOWN: case F_LEFT: case F_RIGHT:
        dpad_step(&o, idx);
        s->next[idx] = t_us + FLIP_REPEAT_FIRST_US;
        break;
    case F_L1: pnl_put(&o, PNL_FOCUS_STEP, 0, -1); break;
    case F_R1: pnl_put(&o, PNL_FOCUS_STEP, 0, 1); break;
    case F_B:  pnl_put(&o, PNL_BACK, 0, 0); break;
    case F_MENU: pnl_put(&o, PNL_MACRO, MACRO_SYSTEM_MENU, 0); break;
    default: break;
    }
    return o.n;
}

static int flip_on_midi(void *st, uint8_t port, const uint8_t *m, uint16_t n,
                        uint32_t t_us, pnl_event_t *out, int max)
{
    (void)st; (void)port; (void)m; (void)n; (void)t_us; (void)out; (void)max;
    return 0;
}

static int flip_on_tick(void *st, uint32_t t_us, pnl_event_t *out, int max)
{
    flip_state_t *s = (flip_state_t *)st;
    pnl_out_t o;
    pnl_out_init(&o, out, max, SRC_FLIP, t_us, &s->dropped);
    for (int d = F_UP; d <= F_RIGHT; d++) {
        if (!(s->down & (1u << d)) || pnl_dt(t_us, s->next[d]) < 0) continue;
        dpad_step(&o, d);
        s->next[d] += FLIP_REPEAT_US;
        if (pnl_dt(t_us, s->next[d]) >= 0) s->next[d] = t_us + FLIP_REPEAT_US;
    }
    return o.n;
}

static int flip_on_lost(void *st, uint32_t t_us, pnl_event_t *out, int max)
{
    flip_state_t *s = (flip_state_t *)st;
    pnl_out_t o;
    pnl_out_init(&o, out, max, SRC_FLIP, t_us, &s->dropped);
    for (int i = 0; i < F_COUNT; i++) {
        uint8_t enc = held_enc(i);
        if (enc != ENC_COUNT && (s->down & (1u << i))) pnl_put(&o, PNL_ENC_UP, enc, PNL_B_SYNTH);
    }
    pnl_put(&o, PNL_SRC_LOST, SRC_FLIP, 0);

    uint32_t dropped = s->dropped;
    flip_reset(s);
    s->dropped = dropped;
    return o.n;
}

const ctl_profile_t FLIP_TASTI = {
    "flip_tasti", flip_reset, flip_on_midi, flip_on_pad, flip_on_tick, flip_on_lost
};
