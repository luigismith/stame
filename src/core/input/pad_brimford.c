/* pad_brimford.c — mappa del macro pad BRIMFORD verso il pannello (sezione 40, MIDI-120…127, 133, 136).
 *
 * Mappa del 16/10/2026 (Luigi: «vedo comandi replicati sui vari device... questa cosa non mi piace»):
 * il pad non rifà più i pulsanti degli encoder né la navigazione, che stanno sulla MK4; tiene Options,
 * Panic, Lock, View, Page e i due voicing, e dà ai tasti liberi le funzioni che l'Orchid non ha.
 * Senza tastiera, dal 17/10/2026, il pad è lo strumento (MIDI-136): fondamentali, tipo ed estensione.
 */
#include "pad_brimford.h"

/* ruoli delle manopole che non sono encoder */
#define KNOB_VOL  0xFE              /* m2 senza Lock: volumi del Beat e del basso */
#define KNOB_TYPE 0xFD              /* M dello strumento: tipo d'accordo tenuto; premuta toglie tipo ed estensione */
#define KNOB_EXT  0xFC              /* m1 dello strumento: estensione tenuta */

/* M, m1, m2 con la tastiera, con il Lock acceso (MIDI-131) e nello strumento (MIDI-136) */
enum { MAP_CTL, MAP_LOCK, MAP_INST };
static const uint8_t KNOB_TURN[3][3] STAME_ROM = {
    { ENC_CHORD_VOICING, ENC_BASS_VOICING, KNOB_VOL },
    { ENC_SOUND, ENC_PERFORM, ENC_KEY },
    { KNOB_TYPE, KNOB_EXT, ENC_FOCUS }
};
static const uint8_t KNOB_PRESS[3][3] STAME_ROM = {
    { ENC_CHORD_VOICING, ENC_BASS_VOICING, KNOB_VOL },
    { ENC_SOUND, ENC_PERFORM, ENC_KEY },
    { KNOB_TYPE, ENC_BASS_VOICING, ENC_FOCUS }      /* m1 premuta è il Mod, m2 preme il controllo col fuoco */
};

enum { T_HOLD, T_TAP, T_METRO, T_FILL, T_SCENE1, T_SCENE2, T_SCENE3, T_SCENE4, T_OPTIONS, T_EXIT, T_DRUMS,
       T_PANIC, T_LOCK, T_VIEW, T_PAGE };
enum { ACT_CCW, ACT_PUSH, ACT_CW };

static int knob_map(const mpad_state_t *s) { return s->lock ? MAP_LOCK : s->inst ? MAP_INST : MAP_CTL; }
static bool is_enc(uint8_t r) { return r < ENC_COUNT || r == ENC_FOCUS; }

/* tipo o estensione tenuti come un tasto accordo (MIDI-136): si lascia il vecchio e si preme il nuovo,
 * come una mano che passa da un tasto all'altro; agli estremi la manopola si ferma */
static void latch(pnl_out_t *o, uint8_t *v, int d, uint8_t first)
{
    int n = *v + d;
    if (n < 0) n = 0;
    if (n > MPAD_LATCH_MAX) n = MPAD_LATCH_MAX;
    if (n == *v) return;
    if (*v) pnl_put(o, PNL_CHORD_UP, (uint8_t)(first + *v - 1), 0);
    if (n) pnl_put(o, PNL_CHORD_DOWN, (uint8_t)(first + n - 1), 0);
    *v = (uint8_t)n;
}

static void unlatch(mpad_state_t *s, pnl_out_t *o)
{
    latch(o, &s->ch_type, -MPAD_LATCH_MAX, CHB_DIM);
    latch(o, &s->ch_ext, -MPAD_LATCH_MAX, CHB_6);
}

/* la mappa cambia solo con il pad fermo; lasciando lo strumento si rilasciano tipo ed estensione */
static void apply_map(mpad_state_t *s, pnl_out_t *o)
{
    if (s->inst == s->want_inst || s->t_down || s->knob_down) return;
    if (s->inst) unlatch(s, o);
    s->inst = s->want_inst;
}

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
    apply_map(s, &o);

    if (code <= MPAD_T15) {
        int i = code - MPAD_T1;
        uint16_t bit = (uint16_t)(1u << i);
        if (down == ((s->t_down & bit) != 0)) return o.n;         /* nessun cambio */
        s->t_down ^= bit;
        if (s->inst && i < 12) {                                  /* fondamentali Do…Si (MIDI-136) */
            pnl_put(&o, down ? PNL_KEY_DOWN : PNL_KEY_UP, (uint8_t)i, down ? MPAD_VELOCITY : 0);
            return o.n;
        }
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
        if (down == ((s->knob_down & kb) != 0)) return o.n;
        s->knob_down ^= kb;
        if (down) {                                               /* il rilascio e i giri vanno al ruolo premuto */
            int mp = knob_map(s);
            s->knob_enc[k] = KNOB_PRESS[mp][k];
            s->knob_turn[k] = KNOB_TURN[mp][k];
        }
        uint8_t r = s->knob_enc[k];
        if (r == KNOB_TYPE) { if (down) unlatch(s, &o); }         /* M dello strumento: di nuovo l'accordo di Key */
        else if (is_enc(r)) pnl_put(&o, down ? PNL_ENC_DOWN : PNL_ENC_UP, r, 0);
    } else if (down) {                                            /* conta solo il KEY_DOWN (MIDI-125) */
        int16_t d = act == ACT_CW ? 1 : -1;
        bool pressed = (s->knob_down & kb) != 0;
        uint8_t role = pressed ? s->knob_turn[k] : KNOB_TURN[knob_map(s)][k];
        switch (role) {
        case KNOB_VOL:  pnl_put(&o, PNL_MACRO, pressed ? MACRO_BASS_VOL : MACRO_BEAT_VOL, d); break;
        case KNOB_TYPE: latch(&o, &s->ch_type, d, CHB_DIM); break;
        case KNOB_EXT:  latch(&o, &s->ch_ext, d, CHB_6); break;
        default:        pnl_put(&o, PNL_ENC_TURN, role, d); break;
        }
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
    apply_map(s, &o);
    if (s->t12 == 1 && pnl_dt(t_us, s->t12_t0) >= (int32_t)MPAD_PANIC_HOLD_US) {
        pnl_put(&o, PNL_MACRO, MACRO_PANIC, 0);                   /* una volta sola */
        s->t12 = 2;
    }
    if (s->t12 == 2 && pnl_dt(t_us, s->t12_t0) >= (int32_t)MPAD_RESET_HOLD_US) {
        pnl_put(&o, PNL_MACRO, MACRO_RESET, 0);                   /* tenuto ancora: tutto da capo */
        s->t12 = 3;
    }
    for (int n = 0; n < 4 && !s->inst; n++) {                     /* scena tenuta 1 s: si salva, una volta */
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

    if (s->inst) {                                                /* fondamentali tenute, tipo ed estensione */
        for (uint8_t i = 0; i < 12; i++) if (s->t_down & (1u << i)) pnl_put(&o, PNL_KEY_UP, i, 0);
        unlatch(s, &o);
    } else {
        if (s->t_down & (1u << T_OPTIONS)) pnl_put(&o, PNL_ENC_UP, ENC_OPTIONS, PNL_B_SYNTH);
        if (s->t_down & (1u << T_FILL)) pnl_put(&o, PNL_MACRO, MACRO_FILL, 0);
    }
    for (int k = 0; k < 3; k++)
        if ((s->knob_down & (1u << k)) && is_enc(s->knob_enc[k]))
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
