/* pad_brimford.c — mappa del macro pad BRIMFORD verso il pannello (sezione 40, MIDI-120…127, 133).
 *
 * Mappa del 16/10/2026 (Luigi: «vedo comandi replicati sui vari device... questa cosa non mi piace»):
 * il pad non rifà più i pulsanti degli encoder né la navigazione, che stanno sulla MK4; tiene Options,
 * Panic, Lock, View, Page e i due voicing, e dà ai tasti liberi le funzioni che l'originale non ha.
 */
#include "pad_brimford.h"

#define KNOB_VOL 0xFE               /* m2 senza Lock: volumi del Beat e del basso, non un encoder */

/* M, m1, m2 senza e con il Lock (MIDI-131) */
static const uint8_t KNOB_ROLE[2][3] STAME_ROM = {
    { ENC_CHORD_VOICING, ENC_BASS_VOICING, KNOB_VOL }, { ENC_SOUND, ENC_PERFORM, ENC_KEY }
};

enum { T_HOLD, T_TAP, T_METRO, T_FILL, T_SCENE1, T_SCENE2, T_SCENE3, T_SCENE4, T_OPTIONS, T_EXIT, T_DRUMS,
       T_PANIC, T_LOCK, T_VIEW, T_PAGE };
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
        if (i >= T_SCENE1 && i <= T_SCENE4) {                     /* tocco = richiama; tenuto 1 s = salva (on_tick) */
            int n = i - T_SCENE1;
            uint8_t sb = (uint8_t)(1u << n);
            if (down) { s->scene_t0[n] = t_us; s->scene_saved &= (uint8_t)~sb; }
            else if (!(s->scene_saved & sb)) pnl_put(&o, PNL_MACRO, MACRO_SCENE, (int16_t)n);
            return o.n;
        }
        switch (i) {
        case T_HOLD:    if (down) pnl_put(&o, PNL_MACRO, MACRO_HOLD_TOGGLE, 0); break;
        case T_TAP:     if (down) pnl_put(&o, PNL_MACRO, MACRO_TAP_TEMPO, 0); break;
        case T_METRO:   if (down) pnl_put(&o, PNL_MACRO, MACRO_METRO_TOGGLE, 0); break;
        case T_FILL:    pnl_put(&o, PNL_MACRO, MACRO_FILL, down); break;        /* finché è tenuto */
        case T_OPTIONS: pnl_put(&o, down ? PNL_ENC_DOWN : PNL_ENC_UP, ENC_OPTIONS, 0); break;
        case T_EXIT:    if (down) pnl_put(&o, PNL_MACRO, MACRO_LOOP_EXIT, 0); break;
        case T_DRUMS:   if (down) pnl_put(&o, PNL_MACRO, MACRO_DRUMS_TOGGLE, 0); break;
        case T_PANIC:   s->t12 = down; s->t12_t0 = t_us; break;    /* MIDI-126: il Panic lo decide on_tick */
        case T_LOCK:                                              /* a scatto, come il Caps Lock (MIDI-131) */
            if (down) { s->lock = (uint8_t)!s->lock; pnl_put(&o, PNL_MACRO, MACRO_KNOB_LOCK, s->lock); }
            break;
        case T_VIEW:    if (down) pnl_put(&o, PNL_MACRO, MACRO_VIEW_TOGGLE, 0); break;     /* MIDI-132 */
        case T_PAGE:    if (down) pnl_put(&o, PNL_MACRO, MACRO_CONTROLS_PAGE, 0); break;
        default: break;
        }
        return o.n;
    }

    int j = code - MPAD_M_CCW, k = j / 3, act = j % 3;
    uint8_t kb = (uint8_t)(1u << k);
    if (act == ACT_PUSH) {
        if (down == ((s->knob_down & kb) != 0)) return 0;
        s->knob_down ^= kb;
        if (down) { s->knob_enc[k] = KNOB_ROLE[s->lock][k]; s->knob_turned &= (uint8_t)~kb; }   /* il rilascio va al ruolo premuto */
        if (s->knob_enc[k] != KNOB_VOL) pnl_put(&o, down ? PNL_ENC_DOWN : PNL_ENC_UP, s->knob_enc[k], 0);
        else if (!down && !(s->knob_turned & kb)) pnl_put(&o, PNL_MACRO, MACRO_KNOB_CLICK, k);   /* MIDI-139 */
    } else if (down) {                                            /* conta solo il KEY_DOWN (MIDI-125) */
        int16_t d = act == ACT_CW ? 1 : -1;
        bool pressed = (s->knob_down & kb) != 0;
        uint8_t role = pressed ? s->knob_enc[k] : KNOB_ROLE[s->lock][k];
        if (pressed) s->knob_turned |= kb;
        if (role == KNOB_VOL) pnl_put(&o, PNL_MACRO, pressed ? MACRO_BASS_VOL : MACRO_BEAT_VOL, d);
        else pnl_put(&o, PNL_ENC_TURN, role, d);
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
    if (s->t12 == 2 && pnl_dt(t_us, s->t12_t0) >= (int32_t)MPAD_RESET_HOLD_US) {
        pnl_put(&o, PNL_MACRO, MACRO_RESET, 0);                   /* tenuto ancora: tutto da capo */
        s->t12 = 3;
    }
    for (int n = 0; n < 4; n++) {                                 /* scena tenuta 1 s: si salva, una volta */
        uint8_t sb = (uint8_t)(1u << n);
        if (!(s->t_down & (1u << (T_SCENE1 + n))) || (s->scene_saved & sb)) continue;
        if (pnl_dt(t_us, s->scene_t0[n]) >= (int32_t)MPAD_SCENE_HOLD_US) {
            pnl_put(&o, PNL_MACRO, MACRO_SCENE_SAVE, (int16_t)n);
            s->scene_saved |= sb;
        }
    }
    return o.n;
}

/* MIDI-127: rilasci sintetici, attese annullate, poi SRC_LOST */
static int mpad_on_lost(void *st, uint32_t t_us, pnl_event_t *out, int max)
{
    mpad_state_t *s = (mpad_state_t *)st;
    pnl_out_t o;
    pnl_out_init(&o, out, max, SRC_MACROPAD, t_us, &s->dropped);

    if (s->t_down & (1u << T_OPTIONS)) pnl_put(&o, PNL_ENC_UP, ENC_OPTIONS, PNL_B_SYNTH);
    if (s->t_down & (1u << T_FILL)) pnl_put(&o, PNL_MACRO, MACRO_FILL, 0);
    for (int k = 0; k < 3; k++)
        if ((s->knob_down & (1u << k)) && s->knob_enc[k] != KNOB_VOL)
            pnl_put(&o, PNL_ENC_UP, s->knob_enc[k], PNL_B_SYNTH);
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
