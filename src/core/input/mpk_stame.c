/* mpk_stame.c — mappa della MPK mini Plus verso il pannello dell'originale (sezione 40, §8.5–§8.8). */
#include "mpk_stame.h"
#include "../midi_parse.h"

/* ------------------------------------------------------------------ tabelle */

/* MIDI-078: K1–K8 = CC 70–77, griglia gemella dei tasti T1–T8 del macro pad */
static const uint8_t KNOB_ENC[8] STAME_ROM = {
    ENC_SOUND, ENC_PERFORM, ENC_FX, ENC_KEY, ENC_BASS, ENC_LOOP, ENC_BPM, ENC_VOLUME
};
/* MIDI-081: uno scatto ogni 2 unità per K1–K6, ogni unità per K7 (BPM) e K8 (Volume) [V VM-8] */
static const uint8_t KNOB_STEP[8] STAME_ROM = { 2, 2, 2, 2, 2, 2, 1, 1 };

/* banco A, note 36–43: fila bassa 6 m7 M7 9, fila alta Dim Min Maj Sus (MIDI-078) */
static const uint8_t CHORD_OF_PAD[8] STAME_ROM = {
    CHB_6, CHB_MIN7, CHB_MAJ7, CHB_9, CHB_DIM, CHB_MIN, CHB_MAJ, CHB_SUS
};
/* banco B, note 44–50 (B1–B7); 51 = B8 = PUSH */
static const uint8_t FN_ENC[7] STAME_ROM = {
    ENC_KEY, ENC_BASS, ENC_PERFORM, ENC_CHORD_VOICING, ENC_LOOP, ENC_BPM, ENC_OPTIONS
};

enum { CH_KEYS = 0, CH_PADS = 9 };                    /* ch1 e ch10 (MIDI-075) */
enum { PAD_FIRST = 36, PAD_BANK_B = 44, PAD_PUSH = 51 };
enum { CC_MOD = 1, CC_JOY_DOWN = 2, CC_JOY_UP = 3, CC_JOY_LEFT = 12, CC_JOY_RIGHT = 13,
       CC_SUSTAIN = 64, CC_K1 = 70, CC_REW = 115, CC_FWD = 116, CC_STOP = 117, CC_PLAY = 118,
       CC_REC = 119 };
enum { JOY_RIGHT, JOY_LEFT, JOY_UP, JOY_DOWN };

#define VERTICAL_FOCUS ((uint8_t)(ENC_FOCUS | PNL_F_VERTICAL))

/* -------------------------------------------------------------------- PUSH */

static void push_down(mpk_state_t *s)
{
    if (s->push == MPK_PUSH_IDLE) s->push = MPK_PUSH_ARMED;
}

/* synth = PNL_B_SYNTH per un rilascio che l'utente non ha fatto, 0 altrimenti */
static void push_up(mpk_state_t *s, pnl_out_t *o, int16_t synth)
{
    if (s->push >= MPK_PUSH_TARGET) pnl_put(o, PNL_ENC_UP, KNOB_ENC[s->push - MPK_PUSH_TARGET], synth);
    s->push = MPK_PUSH_IDLE;
}

/* B8 o X: il PUSH è premuto se lo è almeno uno dei due */
static void push_source(mpk_state_t *s, pnl_out_t *o, uint8_t *src, uint8_t other, bool down, int16_t synth)
{
    if (down == (*src != 0)) return;
    *src = down;
    if (other) return;
    if (down) push_down(s);
    else push_up(s, o, synth);
}

/* -------------------------------------------------------------------- pad */

/* MIDI-089: una nota di un banco rilascia ciò che risulta premuto nell'altro */
static void release_bank_a(mpk_state_t *s, pnl_out_t *o)
{
    for (uint8_t c = 0; c < CHB_COUNT; c++)
        if (s->chords & (1u << c)) pnl_put(o, PNL_CHORD_UP, c, 0);
    s->chords = 0;
}

static void release_bank_b(mpk_state_t *s, pnl_out_t *o)
{
    for (int k = 0; k < 7; k++)
        if (s->fn & (1u << k)) pnl_put(o, PNL_ENC_UP, FN_ENC[k], PNL_B_SYNTH);
    s->fn = 0;
    push_source(s, o, &s->b8, s->x, false, PNL_B_SYNTH);
}

static void pad_note(mpk_state_t *s, pnl_out_t *o, uint8_t note, bool on)
{
    if (note < PAD_FIRST || note > PAD_PUSH) return;
    bool bank_b = note >= PAD_BANK_B;
    s->bank = bank_b ? MPK_BANK_B : MPK_BANK_A;
    if (bank_b) release_bank_a(s, o);
    else release_bank_b(s, o);

    if (!bank_b) {                                    /* tasti accordo: la velocity non conta (MIDI-080) */
        uint8_t c = CHORD_OF_PAD[note - PAD_FIRST];
        uint8_t bit = (uint8_t)(1u << c);
        if (on == ((s->chords & bit) != 0)) return;   /* Note Off senza Note On, o Note On doppio */
        s->chords ^= bit;
        pnl_put(o, on ? PNL_CHORD_DOWN : PNL_CHORD_UP, c, 0);
    } else if (note < PAD_PUSH) {
        int k = note - PAD_BANK_B;
        uint8_t bit = (uint8_t)(1u << k);
        if (on == ((s->fn & bit) != 0)) return;
        s->fn ^= bit;
        pnl_put(o, on ? PNL_ENC_DOWN : PNL_ENC_UP, FN_ENC[k], 0);
    } else {
        push_source(s, o, &s->b8, s->x, on, 0);
    }
}

/* --------------------------------------------------------------- tastiera */

static void key_note(mpk_state_t *s, pnl_out_t *o, uint8_t note, uint8_t vel, bool on)
{
    uint8_t byte = note >> 3, bit = (uint8_t)(1u << (note & 7));
    uint8_t pc = note % 12;
    if (on == ((s->held[byte] & bit) != 0)) return;   /* Note Off senza Note On, o Note On doppio */
    s->held[byte] ^= bit;
    if (on) {
        if (s->pc_count[pc]++ == 0) pnl_put(o, PNL_KEY_DOWN, pc, vel);   /* MIDI-079 */
    } else {
        if (--s->pc_count[pc] == 0) pnl_put(o, PNL_KEY_UP, pc, 0);
    }
}

/* ---------------------------------------------------------------- manopole */

/* [D] Il joystick in 2CC (CC 13 o CC 3) è del programma STAME: se il profilo era passato a
 * fabbrica, il programma è cambiato di nuovo e le manopole tornano Relative. */
static void back_to_stame(mpk_state_t *s)
{
    s->factory = 0;
    s->absolute = 0;
    s->abs_ref = 0;
    memset(s->acc, 0, sizeof s->acc);
}

static void knob(mpk_state_t *s, pnl_out_t *o, int k, uint8_t v)
{
    uint8_t bit = (uint8_t)(1u << k);
    int delta;

    if (!(s->absolute & bit) && v >= 16 && v <= 112) {          /* MIDI-088: Absolute */
        s->absolute |= bit;
        s->abs_ref &= (uint8_t)~bit;
        s->acc[k] = 0;
        s->factory = 1;
    }
    if (s->absolute & bit) {
        if (!(s->abs_ref & bit)) {                                /* primo valore: solo riferimento */
            s->abs_ref |= bit;
            s->abs_last[k] = v;
            return;
        }
        delta = (int)v - s->abs_last[k];
        s->abs_last[k] = v;
    } else {
        delta = v < 64 ? v : (int)v - 128;                        /* MIDI-081 */
    }
    if (delta == 0) return;

    if (s->push == MPK_PUSH_ARMED) {                              /* MIDI-084: la manopola toccata */
        pnl_put(o, PNL_ENC_DOWN, KNOB_ENC[k], 0);
        s->acc[k] = 0;
        s->t_sel = o->t_us;
        s->push = (uint8_t)(MPK_PUSH_TARGET + k);
        return;
    }
    if (s->push == MPK_PUSH_TARGET + k && pnl_dt(o->t_us, s->t_sel) < (int32_t)MPK_PUSH_DEBOUNCE_US)
        return;

    int a = s->acc[k] + delta;
    int n = a / KNOB_STEP[k];
    s->acc[k] = (int8_t)(a - n * KNOB_STEP[k]);
    if (n) pnl_put(o, PNL_ENC_TURN, KNOB_ENC[k], (int16_t)n);
}

/* --------------------------------------------------------------- trasporto */

static void transport_button(mpk_state_t *s, pnl_out_t *o, uint8_t *held, uint8_t enc, bool press)
{
    if (!press) {
        if (*held) { *held = 0; pnl_put(o, PNL_ENC_UP, enc, 0); }
        return;
    }
    if (*held) return;
    pnl_put(o, PNL_ENC_DOWN, enc, 0);
    if (s->trpt_release) *held = 1;
    else pnl_put(o, PNL_ENC_UP, enc, 0);                          /* MIDI-083: Trpt = On */
}

static void transport(mpk_state_t *s, pnl_out_t *o, uint8_t cc, uint8_t v)
{
    bool press = v != 0;
    if (!press) s->trpt_release = 1;

    switch (cc) {
    case CC_REW: case CC_FWD:
        if (press) pnl_put(o, PNL_ENC_TURN, ENC_FOCUS, cc == CC_REW ? -1 : 1);
        break;
    case CC_REC:  transport_button(s, o, &s->rec, ENC_LOOP, press); break;
    case CC_PLAY: transport_button(s, o, &s->play, ENC_BPM, press); break;
    case CC_STOP:
        if (!press) { s->stop = 0; break; }
        if (s->stop) break;
        if (s->push != MPK_PUSH_IDLE) {                           /* PUSH + Stop = Panic (MIDI-084) */
            pnl_put(o, PNL_MACRO, MACRO_PANIC, 0);
            s->stop = s->trpt_release ? 2 : 0;
        } else {
            pnl_put(o, PNL_MACRO, MACRO_LOOP_STOP, 0);
            s->stop = s->trpt_release ? 1 : 0;                    /* senza rilascio niente Clear (MIDI-083) */
            s->t_stop = o->t_us;
        }
        break;
    default:
        break;
    }
}

/* ---------------------------------------------------------------- joystick */

static void joy_step(pnl_out_t *o, int dir)
{
    pnl_put(o, PNL_ENC_TURN, VERTICAL_FOCUS, dir == JOY_UP ? 1 : -1);   /* MIDI-105: su = +1 */
}

static void joystick(mpk_state_t *s, pnl_out_t *o, uint8_t cc, uint8_t v)
{
    if (cc == CC_JOY_RIGHT || cc == CC_JOY_UP) {
        s->joy_seen = 1;
        if (s->factory) back_to_stame(s);
    }
    if (!s->joy_seen) return;                                     /* MIDI-088: direzione ignota */

    int d = cc == CC_JOY_RIGHT ? JOY_RIGHT : cc == CC_JOY_LEFT ? JOY_LEFT
          : cc == CC_JOY_UP ? JOY_UP : JOY_DOWN;
    uint8_t bit = (uint8_t)(1u << d);
    if (s->joy & bit) {
        if (v <= MPK_JOY_OFF) s->joy &= (uint8_t)~bit;
        return;
    }
    if (v < MPK_JOY_ON) return;
    s->joy |= bit;
    switch (d) {
    case JOY_RIGHT:                                               /* conferma */
        pnl_put(o, PNL_ENC_DOWN, ENC_FOCUS, 0);
        pnl_put(o, PNL_ENC_UP, ENC_FOCUS, 0);
        break;
    case JOY_LEFT:
        pnl_put(o, PNL_BACK, 0, 0);
        break;
    default:
        joy_step(o, d);
        s->joy_next[d - JOY_UP] = o->t_us + MPK_REPEAT_FIRST_US;
        break;
    }
}

/* ---------------------------------------------------------------- identità */

/* F0 7E <dev> 06 02 47 54 00 19 00 <fw 3 byte> … F7 (§8.1). Gli altri SysEx si ignorano (MIDI-074). */
static void identity(mpk_state_t *s, const uint8_t *m, uint16_t n)
{
    if (n < 6 || m[1] != 0x7E || m[3] != 0x06 || m[4] != 0x02) return;
    if (n >= 14 && m[5] == 0x47 && m[6] == 0x54 && m[7] == 0x00 && m[8] == 0x19) {
        s->identity = MPK_ID_PLUS;
        s->fw[0] = m[10]; s->fw[1] = m[11]; s->fw[2] = m[12];
    } else {
        s->identity = MPK_ID_OTHER;
    }
}

/* ---------------------------------------------------------------- profilo */

static void mpk_reset(void *st)
{
    memset(st, 0, sizeof(mpk_state_t));
}

static int mpk_on_midi(void *st, uint8_t port, const uint8_t *m, uint16_t n,
                       uint32_t t_us, pnl_event_t *out, int max)
{
    mpk_state_t *s = (mpk_state_t *)st;
    pnl_out_t o;
    pnl_out_init(&o, out, max, SRC_MPK, t_us, &s->dropped);

    if (port != MIDI_PORT_CTL || n == 0) return 0;               /* MIDI-072 */
    if (m[0] == 0xF0) { identity(s, m, n); return 0; }
    if (m[0] >= 0xF0 || n < 3) return 0;                         /* real time e sistema (MIDI-074); C0, D0 */

    uint8_t ty = m[0] & 0xF0, ch = m[0] & 0x0F;
    uint8_t d1 = m[1] & 0x7F, d2 = m[2] & 0x7F;
    bool on = ty == 0x90 && d2 > 0;

    if (ch == CH_PADS) {
        if (ty == 0x80 || ty == 0x90) pad_note(s, &o, d1, on);   /* A9, D9: aftertouch ignorato (MIDI-080) */
    } else if (ch == CH_KEYS) {
        switch (ty) {
        case 0x80: case 0x90:
            key_note(s, &o, d1, d2, on);
            break;
        case 0xB0:
            if (d1 == CC_MOD) pnl_put(&o, PNL_MOD, 0, d2);
            else if (d1 == CC_SUSTAIN) pnl_put(&o, PNL_SUSTAIN, 0, d2 != 0);
            else if (d1 >= CC_K1 && d1 < CC_K1 + 8) knob(s, &o, d1 - CC_K1, d2);
            else if (d1 >= CC_REW && d1 <= CC_REC) transport(s, &o, d1, d2);
            else if (d1 == CC_JOY_RIGHT || d1 == CC_JOY_LEFT || d1 == CC_JOY_UP || d1 == CC_JOY_DOWN)
                joystick(s, &o, d1, d2);
            break;
        case 0xE0:
            pnl_put(&o, PNL_BEND, 0, (int16_t)(((int)d2 << 7 | d1) - 8192));
            break;
        default:
            break;
        }
    }                                                             /* altri canali: ignorati (MIDI-075) */
    return o.n;
}

static int mpk_on_pad(void *st, uint16_t code, int32_t value, uint32_t t_us, pnl_event_t *out, int max)
{
    mpk_state_t *s = (mpk_state_t *)st;
    pnl_out_t o;
    pnl_out_init(&o, out, max, SRC_MPK, t_us, &s->dropped);
    if (code == PAD_X && (value == 0 || value == 1))              /* X della Flip = PUSH (§8.6) */
        push_source(s, &o, &s->x, s->b8, value == 1, 0);
    return o.n;
}

static int mpk_on_tick(void *st, uint32_t t_us, pnl_event_t *out, int max)
{
    mpk_state_t *s = (mpk_state_t *)st;
    pnl_out_t o;
    pnl_out_init(&o, out, max, SRC_MPK, t_us, &s->dropped);

    for (int d = JOY_UP; d <= JOY_DOWN; d++) {                    /* MIDI-082: ripetizione */
        uint32_t *next = &s->joy_next[d - JOY_UP];
        if (!(s->joy & (1u << d)) || pnl_dt(t_us, *next) < 0) continue;
        joy_step(&o, d);
        *next += MPK_REPEAT_US;
        if (pnl_dt(t_us, *next) >= 0) *next = t_us + MPK_REPEAT_US;   /* tick in ritardo: si riparte */
    }
    if (s->stop == 1 && pnl_dt(t_us, s->t_stop) >= (int32_t)MPK_STOP_CLEAR_US) {
        pnl_put(&o, PNL_MACRO, MACRO_LOOP_CLEAR, 0);
        s->stop = 2;
    }
    return o.n;
}

/* MIDI-112: rilasci sintetici, poi sustain e bend a riposo e SRC_LOST */
static int mpk_on_lost(void *st, uint32_t t_us, pnl_event_t *out, int max)
{
    mpk_state_t *s = (mpk_state_t *)st;
    pnl_out_t o;
    pnl_out_init(&o, out, max, SRC_MPK, t_us, &s->dropped);

    for (uint8_t pc = 0; pc < 12; pc++)
        if (s->pc_count[pc]) pnl_put(&o, PNL_KEY_UP, pc, 0);
    release_bank_a(s, &o);
    for (int k = 0; k < 7; k++)
        if (s->fn & (1u << k)) pnl_put(&o, PNL_ENC_UP, FN_ENC[k], PNL_B_SYNTH);
    push_up(s, &o, PNL_B_SYNTH);
    if (s->rec) pnl_put(&o, PNL_ENC_UP, ENC_LOOP, PNL_B_SYNTH);
    if (s->play) pnl_put(&o, PNL_ENC_UP, ENC_BPM, PNL_B_SYNTH);
    pnl_put(&o, PNL_SUSTAIN, 0, 0);
    pnl_put(&o, PNL_BEND, 0, 0);
    pnl_put(&o, PNL_SRC_LOST, SRC_MPK, 0);

    uint32_t dropped = s->dropped;
    mpk_reset(s);
    s->dropped = dropped;
    return o.n;
}

const ctl_profile_t MPK_STAME = {
    "mpk_stame", mpk_reset, mpk_on_midi, mpk_on_pad, mpk_on_tick, mpk_on_lost
};

const char *mpk_profile_name(const mpk_state_t *s)
{
    return s->factory ? "mpk_fabbrica" : "mpk_stame";
}
