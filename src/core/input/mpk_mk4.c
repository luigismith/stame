/* mpk_mk4.c — mappa della MPK mini IV (preset DAW) verso il pannello dell'Orchid (sezione 40, §8.9b).
 *
 * Mappa decisa il 15/10/2026 con Luigi: tasti e pad come la Plus (stesse note), manopole K1–K8 sugli
 * 8 encoder, SHIFT = PUSH, manopola di navigazione = liste e fuoco (premuta = conferma, premuta e
 * ruotata = premi e ruota l'encoder col fuoco), REC = Loop, STOP/PLAY = BPM (beat), LOOP = pausa del
 * loop, UNDO = Undo (con SHIFT = Clear), ⊕ = Overdub, SHIFT + STOP/PLAY = Panic, − = Back, + = Menu.
 * Dal 16/10/2026 il PUSH è solo SHIFT: B8 e X non contano più e il banco B è libero (le sue note
 * rilasciano solo i tasti accordo del banco A, come un cambio di banco).
 */
#include "mpk_mk4.h"
#include "../midi_parse.h"

static const uint8_t KNOB_ENC[8] STAME_ROM = {
    ENC_SOUND, ENC_PERFORM, ENC_FX, ENC_KEY, ENC_BASS, ENC_LOOP, ENC_BPM, ENC_VOLUME
};
/* unità relative per scatto dell'Orchid: le manopole non hanno scatti e accelerano [V] (15/10/2026:
 * un gesto «di tre scatti» vale 50–90 unità) */
static const uint8_t KNOB_STEP[8] STAME_ROM = { 12, 8, 8, 12, 12, 12, 3, 2 };
/* banco B, note 44–51: otto pad di batteria (MIDI-135), strumenti nell'ordine di drums.h (ACC-212): fila bassa
 * cassa, rullante, rimshot, battimani; fila alta charleston chiuso, charleston aperto, tom basso, piatto */
static const uint8_t DRUM_OF_PAD[8] STAME_ROM = { 0, 2, 1, 3, 4, 6, 5, 11 };
/* banco A, note 36–43: fila bassa 6 m7 M7 9, fila alta Dim Min Maj Sus (come la Plus) */
static const uint8_t CHORD_OF_PAD[8] STAME_ROM = {
    CHB_6, CHB_MIN7, CHB_MAJ7, CHB_9, CHB_DIM, CHB_MIN, CHB_MAJ, CHB_SUS
};
enum { CH_KEYS = 0, CH_PADS = 9 };
enum { PAD_FIRST = 36, PAD_BANK_B = 44, PAD_LAST = 51 };
enum { CC_MOD = 1, CC_NAV_PUSH = 13, CC_NAV = 14, CC_SHIFT = 17, CC_K1 = 24, CC_SUSTAIN = 64,
       CC_UNDO = 73, CC_LOOP = 74, CC_PLAY = 76, CC_REC = 77, CC_OVERDUB = 78, CC_MINUS = 80, CC_PLUS = 81 };

/* -------------------------------------------------------------------- PUSH */

static void push_up(mk4_state_t *s, pnl_out_t *o, int16_t synth)
{
    if (s->push >= MPK_PUSH_TARGET) pnl_put(o, PNL_ENC_UP, KNOB_ENC[s->push - MPK_PUSH_TARGET], synth);
    s->push = MPK_PUSH_IDLE;
}

/* SHIFT: l'unica sorgente del PUSH */
static void push_shift(mk4_state_t *s, pnl_out_t *o, bool down, int16_t synth)
{
    if (down == (s->shift != 0)) return;
    s->shift = down;
    if (down) { if (s->push == MPK_PUSH_IDLE) s->push = MPK_PUSH_ARMED; }
    else push_up(s, o, synth);
}

/* -------------------------------------------------------------------- pad */

static void release_bank_a(mk4_state_t *s, pnl_out_t *o)
{
    for (uint8_t c = 0; c < CHB_COUNT; c++)
        if (s->chords & (1u << c)) pnl_put(o, PNL_CHORD_UP, c, 0);
    s->chords = 0;
}

static void pad_note(mk4_state_t *s, pnl_out_t *o, uint8_t note, uint8_t vel, bool on)
{
    if (note < PAD_FIRST || note > PAD_LAST) return;
    if (note >= PAD_BANK_B) {                                     /* banco B: la batteria (MIDI-135); cambia banco (MIDI-089) */
        release_bank_a(s, o);
        pnl_put(o, PNL_MACRO, MACRO_DRUM_HIT, (int16_t)(DRUM_OF_PAD[note - PAD_BANK_B] << 8 | (on ? vel : 0)));
        return;
    }
    uint8_t c = CHORD_OF_PAD[note - PAD_FIRST];
    uint8_t bit = (uint8_t)(1u << c);
    if (on == ((s->chords & bit) != 0)) return;
    s->chords ^= bit;
    pnl_put(o, on ? PNL_CHORD_DOWN : PNL_CHORD_UP, c, 0);
}

/* --------------------------------------------------------------- tastiera */

static void key_note(mk4_state_t *s, pnl_out_t *o, uint8_t note, uint8_t vel, bool on)
{
    uint8_t byte = note >> 3, bit = (uint8_t)(1u << (note & 7));
    uint8_t pc = note % 12;
    if (on == ((s->held[byte] & bit) != 0)) return;
    s->held[byte] ^= bit;
    if (on) {
        if (s->pc_count[pc]++ == 0) pnl_put(o, PNL_KEY_DOWN, pc, vel);    /* l'ottava non conta (MIDI-079) */
    } else {
        if (--s->pc_count[pc] == 0) pnl_put(o, PNL_KEY_UP, pc, 0);
    }
}

/* ---------------------------------------------------------------- manopole */

static int rel(uint8_t v) { return v < 64 ? v : (int)v - 128; }     /* complemento a 2 su 7 bit */

static void knob(mk4_state_t *s, pnl_out_t *o, int k, uint8_t v)
{
    int delta = rel(v);
    if (delta == 0) return;
    if (s->push == MPK_PUSH_ARMED) {                              /* MIDI-084: la manopola toccata */
        pnl_put(o, PNL_ENC_DOWN, KNOB_ENC[k], 0);
        s->acc[k] = 0;
        s->t_sel = o->t_us;
        s->push = (uint8_t)(MPK_PUSH_TARGET + k);
        return;
    }
    if (s->push == MPK_PUSH_TARGET + k && pnl_dt(o->t_us, s->t_sel) < (int32_t)MK4_PUSH_DEBOUNCE_US)
        return;
    int a = s->acc[k] + delta;
    int n = a / KNOB_STEP[k];
    s->acc[k] = (int16_t)(a - n * KNOB_STEP[k]);
    if (n) pnl_put(o, PNL_ENC_TURN, KNOB_ENC[k], (int16_t)n);
}

/* --------------------------------------------------------------- porta 2 */

static void tap(pnl_out_t *o, uint8_t enc)
{
    pnl_put(o, PNL_ENC_DOWN, enc, 0);
    pnl_put(o, PNL_ENC_UP, enc, 0);
}

static void daw_cc(mk4_state_t *s, pnl_out_t *o, uint8_t cc, uint8_t v)
{
    bool push = s->push != MPK_PUSH_IDLE;
    if (cc >= CC_K1 && cc < CC_K1 + 8) { knob(s, o, cc - CC_K1, v); return; }
    switch (cc) {
    case CC_SHIFT: push_shift(s, o, v != 0, 0); break;
    case CC_NAV: {                                                /* liste e fuoco, orario = voce successiva */
        int d = rel(v);
        if (d) pnl_put(o, PNL_ENC_TURN, ENC_FOCUS, (int16_t)d);
        break;
    }
    case CC_NAV_PUSH:                                             /* conferma; premuta e ruotata = premi e ruota */
        if ((v != 0) == (s->nav_down != 0)) break;
        s->nav_down = v != 0;
        pnl_put(o, v ? PNL_ENC_DOWN : PNL_ENC_UP, ENC_FOCUS, 0);
        break;
    /* il trasporto manda solo la pressione: ogni pulsante è un tocco */
    case CC_REC:  if (v) tap(o, ENC_LOOP); break;
    case CC_PLAY:
        if (!v) break;
        if (push) pnl_put(o, PNL_MACRO, MACRO_PANIC, 0);          /* SHIFT + STOP/PLAY */
        else tap(o, ENC_BPM);
        break;
    case CC_LOOP: if (v) pnl_put(o, PNL_MACRO, MACRO_LOOP_STOP, 0); break;
    case CC_UNDO: if (v) pnl_put(o, PNL_MACRO, push ? MACRO_LOOP_CLEAR : MACRO_LOOP_UNDO, 0); break;
    case CC_OVERDUB: if (v) pnl_put(o, PNL_MACRO, MACRO_LOOP_OVERDUB, 0); break;
    case CC_MINUS: if (v) pnl_put(o, PNL_BACK, 0, 0); break;
    case CC_PLUS:  if (v) pnl_put(o, PNL_MACRO, MACRO_SYSTEM_MENU, 0); break;
    default: break;                                               /* CC 12 del banco e il resto: ignorati */
    }
}

/* ---------------------------------------------------------------- profilo */

static void mk4_reset(void *st)
{
    memset(st, 0, sizeof(mk4_state_t));
}

static int mk4_on_midi(void *st, uint8_t port, const uint8_t *m, uint16_t n,
                       uint32_t t_us, pnl_event_t *out, int max)
{
    mk4_state_t *s = (mk4_state_t *)st;
    pnl_out_t o;
    pnl_out_init(&o, out, max, SRC_MPK, t_us, &s->dropped);
    if (n < 3 || m[0] >= 0xF0) return 0;                          /* SysEx, real time, PC e AT a 2 byte */
    uint8_t ty = m[0] & 0xF0, ch = m[0] & 0x0F;
    uint8_t d1 = m[1] & 0x7F, d2 = m[2] & 0x7F;
    bool on = ty == 0x90 && d2 > 0;

    if (port != MIDI_PORT_CTL) {                                  /* porta 2 (DAW): solo i CC del canale 1 */
        if (ty == 0xB0 && ch == CH_KEYS) daw_cc(s, &o, d1, d2);
        return o.n;
    }
    if (ch == CH_PADS) {
        if (ty == 0x80 || ty == 0x90) pad_note(s, &o, d1, d2, on);   /* A9: aftertouch ignorato */
    } else if (ch == CH_KEYS) {
        switch (ty) {
        case 0x80: case 0x90: key_note(s, &o, d1, d2, on); break;
        case 0xB0:
            if (d1 == CC_MOD) pnl_put(&o, PNL_MOD, 0, d2);
            else if (d1 == CC_SUSTAIN) pnl_put(&o, PNL_SUSTAIN, 0, d2 != 0);
            break;
        case 0xE0: pnl_put(&o, PNL_BEND, 0, (int16_t)(((int)d2 << 7 | d1) - 8192)); break;
        default: break;
        }
    }
    return o.n;
}

static int mk4_on_pad(void *st, uint16_t code, int32_t value, uint32_t t_us, pnl_event_t *out, int max)
{
    (void)st; (void)code; (void)value; (void)t_us; (void)out; (void)max;   /* X non è più il PUSH della MK4 */
    return 0;
}

static int mk4_on_tick(void *st, uint32_t t_us, pnl_event_t *out, int max)
{
    (void)st; (void)t_us; (void)out; (void)max;
    return 0;
}

static int mk4_on_lost(void *st, uint32_t t_us, pnl_event_t *out, int max)
{
    mk4_state_t *s = (mk4_state_t *)st;
    pnl_out_t o;
    pnl_out_init(&o, out, max, SRC_MPK, t_us, &s->dropped);
    for (uint8_t pc = 0; pc < 12; pc++)
        if (s->pc_count[pc]) pnl_put(&o, PNL_KEY_UP, pc, 0);
    release_bank_a(s, &o);
    push_up(s, &o, PNL_B_SYNTH);
    if (s->nav_down) pnl_put(&o, PNL_ENC_UP, ENC_FOCUS, PNL_B_SYNTH);
    pnl_put(&o, PNL_SUSTAIN, 0, 0);
    pnl_put(&o, PNL_BEND, 0, 0);
    pnl_put(&o, PNL_SRC_LOST, SRC_MPK, 0);
    uint32_t dropped = s->dropped;
    mk4_reset(s);
    s->dropped = dropped;
    return o.n;
}

const ctl_profile_t MPK_MK4 = {
    "mpk_mk4", mk4_reset, mk4_on_midi, mk4_on_pad, mk4_on_tick, mk4_on_lost
};
