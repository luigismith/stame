/* pad_brimford.c — mappa del macro pad BRIMFORD verso il pannello (sezione 40, MIDI-120…127). */
#include "pad_brimford.h"

/* MIDI-120: T1–T8 gemelli delle manopole K1–K8 della MPK, T9 Options */
static const uint8_t T_ENC[9] STAME_ROM = {
    ENC_SOUND, ENC_PERFORM, ENC_FX, ENC_KEY, ENC_BASS, ENC_LOOP, ENC_BPM, ENC_VOLUME, ENC_OPTIONS
};
/* M, m1, m2 senza e con il Lock (MIDI-131); m2 ruota senza PNL_F_VERTICAL: orario = voce successiva (MIDI-105) */
static const uint8_t KNOB_ENC[2][3] STAME_ROM = {
    { ENC_CHORD_VOICING, ENC_BASS_VOICING, ENC_FOCUS }, { ENC_SOUND, ENC_PERFORM, ENC_KEY }
};

enum { T_BACK = 9, T_MENU = 10, T_PANIC = 11, T_LOCK = 12, T_VIEW = 13, T_PAGE = 14 };   /* T13–T15: 15/10/2026 */
enum { ACT_CCW, ACT_PUSH, ACT_CW };

static void mpad_reset(void *st)
{
    memset(st, 0, sizeof(mpad_state_t));
}

static int mpad_on_pad(void *st, uint16_t code, int32_t value, uint32_t t_us, pnl_event_t *out, int max)
{
    mpad_state_t *s = (mpad_state_t *)st;
    pnl_out_t o;
    pnl_out_init(&o, out, max, SRC_MACROPAD, t_us, &s->dropped);

    if (code < MPAD_T1 || code >= MPAD_END) return 0;
    if (value != 0 && value != 1) return 0;                       /* 2 = ripetizione del kernel (MIDI-125) */
    bool down = value == 1;

    if (code <= MPAD_T15) {
        int i = code - MPAD_T1;
        uint16_t bit = (uint16_t)(1u << i);
        if (down == ((s->t_down & bit) != 0)) return 0;          /* nessun cambio */
        s->t_down ^= bit;
        if (i < T_BACK) pnl_put(&o, down ? PNL_ENC_DOWN : PNL_ENC_UP, T_ENC[i], 0);
        else if (i == T_BACK) { if (down) pnl_put(&o, PNL_BACK, 0, 0); }
        else if (i == T_MENU) { if (down) pnl_put(&o, PNL_MACRO, MACRO_SYSTEM_MENU, 0); }
        else if (i == T_PANIC) { s->t12 = down; s->t12_t0 = t_us; }   /* MIDI-126: il Panic lo decide on_tick */
        else if (i == T_LOCK) {                                   /* a scatto, come il Caps Lock (MIDI-131) */
            if (down) { s->lock = (uint8_t)!s->lock; pnl_put(&o, PNL_MACRO, MACRO_KNOB_LOCK, s->lock); }
        }
        else if (i == T_VIEW) { if (down) pnl_put(&o, PNL_MACRO, MACRO_VIEW_TOGGLE, 0); }     /* MIDI-132 */
        else if (down) pnl_put(&o, PNL_MACRO, MACRO_CONTROLS_PAGE, 0);                       /* T15 */
        return o.n;
    }

    int j = code - MPAD_M_CCW, k = j / 3, act = j % 3;
    if (act == ACT_PUSH) {
        uint8_t bit = (uint8_t)(1u << k);
        if (down == ((s->knob_down & bit) != 0)) return 0;
        s->knob_down ^= bit;
        if (down) s->knob_enc[k] = KNOB_ENC[s->lock][k];          /* il rilascio va all'encoder premuto */
        pnl_put(&o, down ? PNL_ENC_DOWN : PNL_ENC_UP, s->knob_enc[k], 0);
    } else if (down) {                                            /* conta solo il KEY_DOWN (MIDI-125) */
        pnl_put(&o, PNL_ENC_TURN, KNOB_ENC[s->lock][k], act == ACT_CW ? 1 : -1);
    }
    return o.n;
}

static int mpad_on_midi(void *st, uint8_t port, const uint8_t *m, uint16_t n,
                        uint32_t t_us, pnl_event_t *out, int max)
{
    (void)st; (void)port; (void)m; (void)n; (void)t_us; (void)out; (void)max;
    return 0;
}

static int mpad_on_tick(void *st, uint32_t t_us, pnl_event_t *out, int max)
{
    mpad_state_t *s = (mpad_state_t *)st;
    pnl_out_t o;
    pnl_out_init(&o, out, max, SRC_MACROPAD, t_us, &s->dropped);
    if (s->t12 == 1 && pnl_dt(t_us, s->t12_t0) >= (int32_t)MPAD_PANIC_HOLD_US) {
        pnl_put(&o, PNL_MACRO, MACRO_PANIC, 0);                   /* una volta sola */
        s->t12 = 2;
    }
    return o.n;
}

/* MIDI-127: rilasci sintetici, attesa di T12 annullata, poi SRC_LOST */
static int mpad_on_lost(void *st, uint32_t t_us, pnl_event_t *out, int max)
{
    mpad_state_t *s = (mpad_state_t *)st;
    pnl_out_t o;
    pnl_out_init(&o, out, max, SRC_MACROPAD, t_us, &s->dropped);

    for (int i = 0; i < T_BACK; i++)
        if (s->t_down & (1u << i)) pnl_put(&o, PNL_ENC_UP, T_ENC[i], PNL_B_SYNTH);
    for (int k = 0; k < 3; k++)
        if (s->knob_down & (1u << k)) pnl_put(&o, PNL_ENC_UP, s->knob_enc[k], PNL_B_SYNTH);
    if (s->lock) pnl_put(&o, PNL_MACRO, MACRO_KNOB_LOCK, 0);     /* il Lock non sopravvive al pad */
    pnl_put(&o, PNL_SRC_LOST, SRC_MACROPAD, 0);

    uint32_t dropped = s->dropped;
    mpad_reset(s);
    s->dropped = dropped;
    return o.n;
}

const ctl_profile_t PAD_BRIMFORD = {
    "pad_brimford", mpad_reset, mpad_on_midi, mpad_on_pad, mpad_on_tick, mpad_on_lost
};
