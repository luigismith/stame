/* pad_brimford.h — profilo del macro pad BRIMFORD (sezione 40, §8.10, MIDI-120…127).
 *
 * Riceve i codici MPAD_* già tradotti dalla piattaforma (MIDI-124). T1–T9 sono i pulsanti degli
 * encoder, T10 Back, T11 menu della piattaforma, T12 Panic tenuto 1 s; M, m1 e m2 le manopole di
 * Chord Voicing, Bass Voicing e liste.
 *
 * Il ripiego per le pressioni istantanee (MIDI-125, ultimo punto) dipende dalla verifica VP-3 e
 * non c'è ancora.
 */
#ifndef STAME_PAD_BRIMFORD_H
#define STAME_PAD_BRIMFORD_H

#include "profile.h"

#define MPAD_PANIC_HOLD_US 1000000u   /* MIDI-126: T12 tenuto 1 s */
#define MPAD_CLEAR_HOLD_US 1000000u   /* T14 Stop tenuto 1 s = Clear del loop */

typedef struct {
    uint16_t t_down;        /* bit i: tasto T(i+1) tenuto */
    uint8_t  knob_down;     /* bit 0 M, 1 m1, 2 m2: pressione tenuta */
    uint8_t  t12;           /* 0 su, 1 giù in attesa di 1 s, 2 giù dopo il Panic */
    uint32_t t12_t0;
    uint8_t  t14;           /* Stop: 0 su, 1 giù in attesa di 1 s, 2 giù dopo il Clear */
    uint32_t t14_t0;
    uint32_t dropped;       /* eventi che non stavano in out[] */
} mpad_state_t;

extern const ctl_profile_t PAD_BRIMFORD;

#endif
