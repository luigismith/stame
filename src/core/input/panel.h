/* core/input/panel.h — C11, nessuna dipendenza
 *
 * Eventi del pannello: il contratto fra i profili dei controller e il nucleo (sezione 40,
 * MIDI-100). Il nucleo musicale vede solo questi, mai byte MIDI né codici evdev (MIDI-002).
 */
#ifndef STAME_PANEL_H
#define STAME_PANEL_H

#include <stdint.h>

typedef enum {                      /* i controlli rotanti dell'Orchid */
    ENC_SOUND, ENC_PERFORM, ENC_FX, ENC_KEY, ENC_BASS, ENC_LOOP,
    ENC_BPM, ENC_VOLUME, ENC_OPTIONS, ENC_CHORD_VOICING, ENC_BASS_VOICING,
    ENC_COUNT,
    ENC_FOCUS = 0x40                /* pseudo-encoder: lo risolve il nucleo (MIDI-104) */
} enc_id_t;

typedef enum {                      /* gli 8 tasti accordo */
    CHB_DIM, CHB_MIN, CHB_MAJ, CHB_SUS, CHB_6, CHB_MIN7, CHB_MAJ7, CHB_9, CHB_COUNT
} chord_btn_t;

typedef enum {
    MACRO_LOOP_STOP, MACRO_LOOP_CLEAR, MACRO_PANIC, MACRO_SYSTEM_MENU
} macro_t;

typedef enum {
    PNL_KEY_DOWN, PNL_KEY_UP,       /* a = classe 0..11 (0 = Do), b = velocity 1..127 */
    PNL_CHORD_DOWN, PNL_CHORD_UP,   /* a = chord_btn_t */
    PNL_ENC_TURN,                   /* a = enc_id_t, b = scatti con segno, b != 0 */
    PNL_ENC_DOWN, PNL_ENC_UP,       /* a = enc_id_t */
    PNL_BACK,                       /* chiude overlay o risale nel menu */
    PNL_FOCUS_STEP,                 /* b = ±1 */
    PNL_BEND,                       /* b = -8192..8191 */
    PNL_MOD,                        /* b = 0..127 */
    PNL_SUSTAIN,                    /* b = 0 o 1 */
    PNL_MACRO,                      /* a = macro_t */
    PNL_SRC_CONNECTED, PNL_SRC_LOST /* a = src_t */
} pnl_type_t;

#define PNL_F_VERTICAL 0x80         /* in a, solo per PNL_ENC_TURN(ENC_FOCUS): scatto da un comando verticale (MIDI-105) */

typedef enum { SRC_MPK, SRC_FLIP, SRC_MACROPAD, SRC_COUNT } src_t;   /* SRC_MACROPAD: §8.10 */

typedef struct {
    uint8_t  type;                  /* pnl_type_t */
    uint8_t  src;                   /* src_t */
    uint8_t  a;
    int16_t  b;
    uint32_t t_us;                  /* tempo d'arrivo, orologio monotono */
} pnl_event_t;

#endif
