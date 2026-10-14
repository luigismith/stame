/* mpk_stame.h — profilo della MPK mini Plus con il programma STAME (sezione 40, §8.5–§8.8).
 *
 * Riceve i messaggi della porta 1 (MIDI-072). Riconosce da solo il programma di fabbrica e passa
 * a funzioni ridotte (mpk_fabbrica, MIDI-088): stesso codice, campo factory acceso.
 * Il PUSH (MIDI-084) è il pad B8 oppure il tasto X della Flip: on_pad riceve PAD_X.
 */
#ifndef STAME_MPK_STAME_H
#define STAME_MPK_STAME_H

#include "profile.h"

enum { MPK_BANK_UNKNOWN, MPK_BANK_A, MPK_BANK_B };          /* stima del banco dei pad (MIDI-089) */
enum { MPK_PUSH_IDLE, MPK_PUSH_ARMED, MPK_PUSH_TARGET };     /* TARGET(k) = MPK_PUSH_TARGET + k, come ui_controls_t.push */
enum { MPK_ID_NONE, MPK_ID_PLUS, MPK_ID_OTHER };             /* risposta all'Identity Request (MIDI-073) */

#define MPK_PUSH_DEBOUNCE_US  150000u    /* MIDI-084: tremolio della selezione */
#define MPK_STOP_CLEAR_US    1000000u    /* Stop tenuto 1 s: Clear (§8.5) */
#define MPK_JOY_ON            100        /* MIDI-082: soglia di attivazione */
#define MPK_JOY_OFF            60        /* MIDI-082: soglia di riarmo */
#define MPK_REPEAT_FIRST_US   400000u    /* MIDI-082: ripetizione dopo 400 ms … */
#define MPK_REPEAT_US         200000u    /* … poi ogni 200 ms */

typedef struct {
    /* tastiera (MIDI-079) */
    uint8_t  held[16];          /* bitmap delle 128 note fisiche tenute */
    uint8_t  pc_count[12];      /* tasti fisici tenuti per classe di nota */
    /* pad (MIDI-080, MIDI-089) */
    uint8_t  bank;              /* MPK_BANK_* */
    uint8_t  chords;            /* bit chord_btn_t tenuti dal banco A */
    uint8_t  fn;                /* bit 0..6: pulsanti B1–B7 tenuti */
    /* PUSH (MIDI-084) */
    uint8_t  b8, x;             /* B8 e X della Flip tenuti */
    uint8_t  push;              /* MPK_PUSH_IDLE, MPK_PUSH_ARMED, MPK_PUSH_TARGET + k */
    uint32_t t_sel;
    /* manopole K1–K8 (MIDI-081, MIDI-088) */
    int8_t   acc[8];            /* unità accumulate verso il prossimo scatto */
    uint8_t  absolute;          /* bit k: manopola k in Absolute */
    uint8_t  abs_ref;           /* bit k: abs_last[k] valido */
    uint8_t  abs_last[8];
    uint8_t  factory;           /* 1 = programma di fabbrica o sconosciuto: funzioni ridotte (MIDI-088, MIDI-119) */
    /* trasporto (MIDI-083) */
    uint8_t  trpt_release;      /* visto almeno un valore 0 su CC 115–119 */
    uint8_t  rec, play;         /* Rec e Play tenuti */
    uint8_t  stop;              /* 0 su, 1 giù in attesa del Clear, 2 giù e basta */
    uint32_t t_stop;
    /* joystick (MIDI-082, MIDI-088) */
    uint8_t  joy_seen;          /* visto CC 13 o CC 3: joystick in 2CC */
    uint8_t  joy;               /* bit 0 destra (CC 13), 1 sinistra (12), 2 su (3), 3 giù (2) */
    uint32_t joy_next[2];       /* prossima ripetizione di su e giù */
    /* identità (MIDI-073) */
    uint8_t  identity;          /* MPK_ID_* */
    uint8_t  fw[3];             /* firmware: 1.13 = 01 01 03 */
    uint32_t dropped;           /* eventi che non stavano in out[] */
} mpk_state_t;

extern const ctl_profile_t MPK_STAME;

/* "mpk_stame" oppure "mpk_fabbrica" (§10.2) */
const char *mpk_profile_name(const mpk_state_t *s);

#endif
