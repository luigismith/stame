/* pad_brimford.h — profilo del macro pad BRIMFORD (sezione 40, §8.10, MIDI-120…127, MIDI-133).
 *
 * Riceve i codici MPAD_* già tradotti dalla piattaforma (MIDI-124). Dal 16/10/2026 (decisione di
 * Luigi: ogni comando in una casa sola) la pressione degli encoder sta su SHIFT + K della MK4 e la
 * navigazione sulla sua manopola: qui restano T9 Options, T12 Panic tenuto 1 s (3 s = Reset), T13 Lock
 * (MIDI-131, a scatto come il Caps Lock: acceso, M, m1 e m2 sono Sound, Perform e Key), T14 View e T15
 * Page (MIDI-132), M Chord Voicing e m1 Bass Voicing. I tasti liberi fanno quello che l'Orchid non ha
 * (MIDI-133): T1 Hold, T2 Tap tempo, T3 Metronomo, T4 Fill del Beat finché è tenuto, T5–T8 Scene
 * (tocco = richiama, tenuto 1 s = salva), T10 Save Loop (uscita morbida), T11 batteria a tastiera;
 * m2 senza Lock è il volume del Beat e, premuta e girata, quello del basso.
 */
#ifndef STAME_PAD_BRIMFORD_H
#define STAME_PAD_BRIMFORD_H

#include "profile.h"

#define MPAD_PANIC_HOLD_US 1000000u   /* MIDI-126: T12 tenuto 1 s = Panic */
#define MPAD_RESET_HOLD_US 3000000u   /* MIDI-126: T12 tenuto 3 s = Reset */
#define MPAD_SCENE_HOLD_US 1000000u   /* MIDI-133: T5–T8 tenuti 1 s = salva la scena */

typedef struct {
    uint16_t t_down;        /* bit i: tasto T(i+1) tenuto */
    uint8_t  knob_down;     /* bit 0 M, 1 m1, 2 m2: pressione tenuta */
    uint8_t  knob_enc[3];   /* ruolo di ogni manopola al momento della pressione: il rilascio e i giri vanno lì */
    uint8_t  lock;          /* Lock acceso (MIDI-131) */
    uint8_t  t12;           /* 0 su, 1 giù in attesa di 1 s, 2 giù dopo il Panic, 3 giù dopo il Reset */
    uint32_t t12_t0;
    uint8_t  scene_saved;   /* bit n: T(5+n) tenuto ha già salvato la scena; il rilascio non la richiama */
    uint32_t scene_t0[4];   /* pressione di T5–T8 */
    uint32_t dropped;       /* eventi che non stavano in out[] */
} mpad_state_t;

extern const ctl_profile_t PAD_BRIMFORD;

#endif
