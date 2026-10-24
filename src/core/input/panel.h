/* core/input/panel.h — C11, nessuna dipendenza
 *
 * Eventi del pannello: il contratto fra i profili dei controller e il nucleo (sezione 40,
 * MIDI-100). Il nucleo musicale vede solo questi, mai byte MIDI né codici evdev (MIDI-002).
 */
#ifndef STAME_PANEL_H
#define STAME_PANEL_H

#include <stdint.h>

typedef enum {                      /* i controlli rotanti dell'originale */
    ENC_SOUND, ENC_PERFORM, ENC_FX, ENC_KEY, ENC_BASS, ENC_LOOP,
    ENC_BPM, ENC_VOLUME, ENC_OPTIONS, ENC_CHORD_VOICING, ENC_BASS_VOICING,
    ENC_COUNT,
    ENC_FOCUS = 0x40                /* pseudo-encoder: lo risolve il nucleo (MIDI-104) */
} enc_id_t;

typedef enum {                      /* gli 8 tasti accordo */
    CHB_DIM, CHB_MIN, CHB_MAJ, CHB_SUS, CHB_6, CHB_MIN7, CHB_MAJ7, CHB_9, CHB_COUNT
} chord_btn_t;

typedef enum {
    MACRO_LOOP_STOP, MACRO_LOOP_CLEAR, MACRO_PANIC, MACRO_SYSTEM_MENU, MACRO_LOOP_UNDO, MACRO_LOOP_OVERDUB,
    MACRO_DROP,                     /* T13: b = 1 tenuto (Beat, loop di batteria e basso tacciono), 0 rilasciato (MIDI-140) */
    MACRO_AMBIENT_TOGGLE,           /* il modulo AMBIENT acceso o spento (T14 del macro pad, MIDI-143; fino al 22/10/2026 View) */
    MACRO_CONTROLS_PAGE,            /* apre o chiude la pagina dei comandi della Flip (T15, MIDI-132) */
    MACRO_RESET,                    /* Panic più looper, Beat, transpose e Perform da capo (T12 tenuto 3 s, MIDI-126) */
    /* le funzioni che l'originale non ha, sui tasti liberi del macro pad (MIDI-133, 16/10/2026) */
    MACRO_HOLD_TOGGLE,              /* T1: l'accordo resta a suonare dopo il rilascio, fino al tasto dopo */
    MACRO_TAP_TEMPO,                /* T2: un tocco del tap tempo */
    MACRO_METRO_TOGGLE,             /* T3: metronomo on/off, indipendente dal Beat */
    MACRO_FILL,                     /* T4: b = 1 tenuto (fill del Beat), 0 rilasciato */
    MACRO_SCENE,                    /* T5–T8 toccati: b = scena 0…3 da richiamare */
    MACRO_SCENE_SAVE,               /* T5–T8 tenuti 1 s: b = scena 0…3 da salvare */
    MACRO_LOOP_EXIT,                /* T10: Save Loop, l'uscita morbida (ACC-222 EXIT) */
    MACRO_DRUMS_TOGGLE,             /* T11: DRUMS on/off (ACC-211) */
    MACRO_BEAT_VOL,                 /* m2 girata: b = scatti con segno sul volume del Beat */
    MACRO_BASS_VOL,                 /* m2 premuta e girata: b = scatti sul volume del basso */
    MACRO_DRUM_HIT,                 /* pad del banco B della MK4 (MIDI-135): b = strumento << 8 | velocity, 0 = rilascio */
    MACRO_KNOB_CLICK                /* manopola del pad premuta e lasciata senza girarla, se non è un encoder: b = 2 (m2) */
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
