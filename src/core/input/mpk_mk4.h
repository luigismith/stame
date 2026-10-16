/* mpk_mk4.h — profilo della MPK mini IV (MK4) nel preset DAW (sezione 40, §8.9b).
 *
 * Il preset DAW è di fabbrica e in sola lettura: non va programmato. Messaggi catturati il
 * 15/10/2026. Porta 1 (MIDI): tasti, pad, ruote, sustain. Porta 2 (DAW): manopole K1–K8 relative
 * (CC 24–31), SHIFT (CC 17), manopola di navigazione (CC 14 giro, CC 13 pressione), trasporto
 * (CC 73, 74, 76, 77, 78), − e + (CC 80, 81). I pad arrivano anche sulla porta 2: lì si ignorano.
 * Il PUSH (MIDI-084) è solo SHIFT (Luigi, 16/10/2026: ogni comando in una casa sola); il banco B
 * dei pad è libero e il tasto X della Flip non conta più sulla MK4.
 */
#ifndef STAME_MPK_MK4_H
#define STAME_MPK_MK4_H
#include "profile.h"
#include "mpk_stame.h"

#define MK4_PUSH_DEBOUNCE_US 300000u   /* manopole senza scatti: il tocco che sceglie dura di più [V] */

typedef struct {
    uint8_t  held[16];          /* bitmap delle note fisiche tenute */
    uint8_t  pc_count[12];      /* tasti tenuti per classe di nota */
    uint8_t  chords;            /* tasti accordo tenuti (banco A) */
    uint8_t  shift;             /* SHIFT tenuto: il PUSH */
    uint8_t  push;              /* MPK_PUSH_IDLE, MPK_PUSH_ARMED, MPK_PUSH_TARGET + k */
    uint32_t t_sel;
    int16_t  acc[8];            /* unità accumulate verso il prossimo scatto */
    uint8_t  nav_down;          /* manopola di navigazione premuta */
    uint32_t dropped;
} mk4_state_t;

extern const ctl_profile_t MPK_MK4;

#endif
