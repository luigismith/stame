/* flip_tasti.c — tasti, levette e grilletti della Flip, schema a fuoco sempre attivo
 * (sezione 40, §9.1, MIDI-137, MIDI-138). */
#include "flip_tasti.h"

/* indici interni dei tasti usati dallo schema a fuoco, e i loro codici */
enum { F_UP, F_DOWN, F_LEFT, F_RIGHT, F_A, F_B, F_X, F_Y, F_L1, F_R1, F_SELECT, F_START, F_MENU, F_L3, F_R3,
       F_COUNT };

static const uint16_t CODE[F_COUNT] STAME_ROM = {
    PAD_UP, PAD_DOWN, PAD_LEFT, PAD_RIGHT, PAD_A, PAD_B, PAD_X, PAD_Y, PAD_L1, PAD_R1,
    PAD_SELECT, PAD_START, PAD_MENU, PAD_L3, PAD_R3
};

/* tasti che tengono premuto un encoder (MIDI-092); START solo senza la MK4 (MIDI-137); i clic delle
 * levette sono i pulsanti dei due voicing (MIDI-138) */
static uint8_t held_enc(const flip_state_t *s, int idx)
{
    switch (idx) {
    case F_A:      return ENC_FOCUS;
    case F_Y:      return ENC_BASS_VOICING;
    case F_SELECT: return ENC_OPTIONS;
    case F_START:  return s->start_fill ? (uint8_t)ENC_COUNT : (uint8_t)ENC_BPM;
    case F_L3:     return ENC_BASS_VOICING;
    case F_R3:     return ENC_CHORD_VOICING;
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

/* ---------------------------------------------------------------- levette e grilletti */

/* zona morta del 20% (PLT-055), poi di nuovo tutta la corsa: ±32767 */
static int32_t dead(int32_t v)
{
    int32_t a = v < 0 ? -v : v;
    if (a <= FLIP_STICK_DEAD) return 0;
    if (a > 32767) a = 32767;
    int32_t r = (a - FLIP_STICK_DEAD) * 32767 / (32767 - FLIP_STICK_DEAD);
    return v < 0 ? -r : r;
}

/* levetta destra: asse 0 = X, Bass Voicing (destra = su di un'ottava); asse 1 = Y, Chord Voicing
 * (su = più in alto; l'asse Y cresce verso il basso). Isteresi: il passo si lascia sotto il 40% */
static const uint8_t STEP_ENC[2] STAME_ROM = { ENC_BASS_VOICING, ENC_CHORD_VOICING };

static int32_t step_pos(const flip_state_t *s, int a) { return a ? -s->rs[a] : s->rs[a]; }

static void stick_step(flip_state_t *s, pnl_out_t *o, int a, uint32_t t_us)
{
    int32_t u = step_pos(s, a);
    int8_t d = s->step[a], nd;
    if (d > 0 && u >= FLIP_STICK_STEP - FLIP_STICK_HYST) nd = 1;
    else if (d < 0 && u <= -(FLIP_STICK_STEP - FLIP_STICK_HYST)) nd = -1;
    else nd = u >= FLIP_STICK_STEP ? 1 : u <= -FLIP_STICK_STEP ? -1 : 0;
    if (nd == d) return;
    s->step[a] = nd;
    if (!nd) return;
    pnl_put(o, PNL_ENC_TURN, STEP_ENC[a], nd);                    /* il primo passo subito */
    s->step_next[a] = t_us + FLIP_REPEAT_FIRST_US;
}

/* L2 = Tap tempo, R2 = Fill finché è tenuto (MIDI-138), con l'isteresi di PLT-055 */
static void trigger(flip_state_t *s, pnl_out_t *o, int t, int32_t v)
{
    uint8_t bit = (uint8_t)(1u << t);
    bool on = (s->trig & bit) != 0;
    if (!on && v > FLIP_TRIG_ON) {
        s->trig |= bit;
        pnl_put(o, PNL_MACRO, t ? MACRO_FILL : MACRO_TAP_TEMPO, t ? 1 : 0);
    } else if (on && v < FLIP_TRIG_OFF) {
        s->trig &= (uint8_t)~bit;
        if (t) pnl_put(o, PNL_MACRO, MACRO_FILL, 0);
    }
}

static int axis(flip_state_t *s, pnl_out_t *o, uint16_t code, int32_t v, uint32_t t_us)
{
    switch (code) {
    case PAD_LSTICK_X: {                                          /* pitch bend, a molla */
        int16_t b = (int16_t)(dead(v) * 8191 / 32767);
        int diff = b - s->bend;
        bool edge = (b == 0 || b == 8191 || b == -8191) && b != s->bend;
        if (edge || diff >= FLIP_BEND_STEP || diff <= -FLIP_BEND_STEP) {
            pnl_put(o, PNL_BEND, 0, b);
            s->bend = b;
        }
        break;
    }
    case PAD_LSTICK_Y: {                                          /* modulazione: in su o in giù */
        int32_t a = dead(v);
        uint8_t m = (uint8_t)((a < 0 ? -a : a) * 127 / 32767);
        if (m != s->mod) { pnl_put(o, PNL_MOD, 0, m); s->mod = m; }
        break;
    }
    case PAD_RSTICK_X: s->rs[0] = v; stick_step(s, o, 0, t_us); break;
    case PAD_RSTICK_Y: s->rs[1] = v; stick_step(s, o, 1, t_us); break;
    case PAD_L2:       trigger(s, o, 0, v); break;
    case PAD_R2:       trigger(s, o, 1, v); break;
    default: break;
    }
    return o->n;
}

/* ---------------------------------------------------------------- profilo */

static void flip_reset(void *st)
{
    memset(st, 0, sizeof(flip_state_t));
}

static int flip_on_pad(void *st, uint16_t code, int32_t value, uint32_t t_us, pnl_event_t *out, int max)
{
    flip_state_t *s = (flip_state_t *)st;
    pnl_out_t o;
    pnl_out_init(&o, out, max, SRC_FLIP, t_us, &s->dropped);

    if (code >= PAD_L2 && code <= PAD_RSTICK_Y) return axis(s, &o, code, value, t_us);
    if (value != 0 && value != 1) return 0;                       /* 2 = ripetizione del kernel */
    int idx = -1;
    for (int i = 0; i < F_COUNT; i++)
        if (CODE[i] == code) { idx = i; break; }
    if (idx < 0) return 0;

    bool down = value == 1;
    uint16_t bit = (uint16_t)(1u << idx);
    if (down == ((s->down & bit) != 0)) return 0;
    s->down ^= bit;

    if (idx == F_START && down) s->start_fill = (s->cfg & FLIP_CFG_MK4) != 0;   /* il ruolo si fissa qui */
    if (idx == F_START && s->start_fill) {                        /* con la MK4: Fill finché è tenuto */
        pnl_put(&o, PNL_MACRO, MACRO_FILL, down);
        if (!down) s->start_fill = 0;
        return o.n;
    }
    uint8_t enc = held_enc(s, idx);
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
    case F_X:                                                     /* Hold; con la Plus è il suo PUSH (mpk_stame) */
        if (!(s->cfg & FLIP_CFG_PLUS)) pnl_put(&o, PNL_MACRO, MACRO_HOLD_TOGGLE, 0);
        break;
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
    for (int a = 0; a < 2; a++) {                                 /* levetta destra tenuta: il passo si ripete */
        if (!s->step[a] || pnl_dt(t_us, s->step_next[a]) < 0) continue;
        int32_t u = step_pos(s, a);
        bool fast = (u < 0 ? -u : u) >= FLIP_STICK_FAST;
        pnl_put(&o, PNL_ENC_TURN, STEP_ENC[a], s->step[a]);
        s->step_next[a] = t_us + (fast ? FLIP_STICK_FAST_US : FLIP_STICK_REPEAT_US);
    }
    return o.n;
}

static int flip_on_lost(void *st, uint32_t t_us, pnl_event_t *out, int max)
{
    flip_state_t *s = (flip_state_t *)st;
    pnl_out_t o;
    pnl_out_init(&o, out, max, SRC_FLIP, t_us, &s->dropped);
    for (int i = 0; i < F_COUNT; i++) {
        uint8_t enc = held_enc(s, i);
        if (enc != ENC_COUNT && (s->down & (1u << i))) pnl_put(&o, PNL_ENC_UP, enc, PNL_B_SYNTH);
    }
    if (s->start_fill && (s->down & (1u << F_START))) pnl_put(&o, PNL_MACRO, MACRO_FILL, 0);
    if (s->trig & 2) pnl_put(&o, PNL_MACRO, MACRO_FILL, 0);      /* R2 tenuto */
    if (s->bend) pnl_put(&o, PNL_BEND, 0, 0);                    /* la levetta torna al centro */
    if (s->mod) pnl_put(&o, PNL_MOD, 0, 0);
    pnl_put(&o, PNL_SRC_LOST, SRC_FLIP, 0);

    uint32_t dropped = s->dropped;
    uint8_t cfg = s->cfg;
    flip_reset(s);
    s->dropped = dropped;
    s->cfg = cfg;
    return o.n;
}

const ctl_profile_t FLIP_TASTI = {
    "flip_tasti", flip_reset, flip_on_midi, flip_on_pad, flip_on_tick, flip_on_lost
};
