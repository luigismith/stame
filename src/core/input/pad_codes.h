/* core/input/pad_codes.h — codici portabili dei tasti, passati a on_pad dei profili (MIDI-101).
 *
 * PAD_*  : tasti e assi della Flip (MIDI-090, PLT-054). I tasti hanno lo stesso numero del codice
 *          evdev EV_KEY, così input_evdev.c può bloccare la compilazione con
 *          _Static_assert(PAD_A == BTN_SOUTH, ...) se i nomi si confondono. I nomi BTN_* sono vietati.
 * MPAD_* : azioni del macro pad BRIMFORD, già tradotte dalla mappa di MIDI-122 o da pad.map
 *          (MIDI-124). I nomi KEY_* sono vietati.
 *
 * Valori: tasti 1 = giù, 0 = su, 2 = ripetizione automatica del kernel (da ignorare, MIDI-125).
 */
#ifndef STAME_PAD_CODES_H
#define STAME_PAD_CODES_H

enum {
    /* tasti della Flip: codice evdev (PLT-054, §7.1) */
    PAD_B = 304, PAD_A = 305, PAD_Y = 307, PAD_X = 308,
    PAD_L1 = 310, PAD_R1 = 311,
    PAD_SELECT = 314, PAD_START = 315, PAD_MENU = 316,
    PAD_L3 = 317, PAD_R3 = 318,

    /* croce: la piattaforma traduce ABS_HAT0X/ABS_HAT0Y (−1, 0, +1) in quattro tasti */
    PAD_UP = 0x400, PAD_DOWN, PAD_LEFT, PAD_RIGHT,

    /* assi, valore grezzo: L2 e R2 0..255 (ABS_Z, ABS_RZ); levette −32767..32767 con 0 al centro,
     * già scalate dalla piattaforma con i limiti di EVIOCGABS */
    PAD_L2 = 0x410, PAD_R2, PAD_LSTICK_X, PAD_LSTICK_Y, PAD_RSTICK_X, PAD_RSTICK_Y,

    /* macro pad BRIMFORD (§8.10): T1–T12 e le tre azioni di ciascuna manopola */
    MPAD_T1 = 0x800, MPAD_T2, MPAD_T3, MPAD_T4, MPAD_T5, MPAD_T6,
    MPAD_T7, MPAD_T8, MPAD_T9, MPAD_T10, MPAD_T11, MPAD_T12,
    MPAD_M_CCW, MPAD_M_PUSH, MPAD_M_CW,
    MPAD_M1_CCW, MPAD_M1_PUSH, MPAD_M1_CW,
    MPAD_M2_CCW, MPAD_M2_PUSH, MPAD_M2_CW,
    MPAD_END
};

#endif
