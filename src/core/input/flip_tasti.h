/* flip_tasti.h — profilo dei tasti della Miyoo Flip, schema a fuoco (sezione 40, §9.1, MIDI-092).
 *
 * L1/R1 spostano il fuoco, la croce ruota l'encoder con il fuoco (con ripetizione), A lo preme,
 * B torna indietro, Y è il Bass Voicing premuto, SELECT Options, MENU il menu della piattaforma.
 * Dal 17/10/2026 (Luigi: «i tasti della flip devono funzionare per la gestione», poi «tutti») i tasti
 * della Flip non tacciono mai: due cambiano ruolo secondo gli apparecchi collegati (MIDI-137), e
 * input.c lo scrive in cfg:
 *   - X è Hold; con la Plus collegata è il suo PUSH, e lo gestisce mpk_stame;
 *   - START è il pulsante di BPM; con la MK4 collegata, che ha STOP/PLAY, è il Fill finché è tenuto.
 * Il ruolo di START si fissa alla pressione: il rilascio va lì anche se intanto cambia la configurazione.
 *
 * Levette e grilletti (17/10/2026, Luigi: «gli analogici dalla flip? non ti piacevano?», MIDI-138):
 *   - levetta sinistra: orizzontale = pitch bend, verticale = modulazione (in su o in giù), a molla
 *     come il joystick delle MPK; con il solo pad sono l'unico bend e l'unica modulazione;
 *   - levetta destra: su/giù = Chord Voicing, destra/sinistra = Bass Voicing, un passo oltre il 50%
 *     della corsa, ripetuto finché è tenuta (ogni 150 ms, ogni 50 ms oltre il 90%), come MIDI-093;
 *   - R3 = Chord Voicing premuto (Split/Octave), L3 = Bass Voicing premuto (Mod);
 *   - L2 = Tap tempo, R2 = Fill finché è tenuto.
 * Zona morta del 20% e isteresi dei grilletti (sopra 160, sotto 96) sono quelle di PLT-055; la
 * piattaforma manda le levette in −32767..32767 (0 al centro, l'asse Y cresce verso il basso) e i
 * grilletti in 0..255, già scalati con i limiti di EVIOCGABS.
 *
 * Il modo tascabile (§9.2, MIDI-093/094: opzionale, spento per default) arriva con la fase F5.
 */
#ifndef STAME_FLIP_TASTI_H
#define STAME_FLIP_TASTI_H

#include "profile.h"

#define FLIP_REPEAT_FIRST_US 400000u    /* ripetizione della croce come MIDI-082 */
#define FLIP_REPEAT_US       200000u

#define FLIP_STICK_DEAD      6553       /* PLT-055: zona morta del 20% della corsa */
#define FLIP_STICK_STEP      16384      /* MIDI-093: un passo del voicing oltre il 50% */
#define FLIP_STICK_HYST      3277       /* il passo si lascia sotto il 40% */
#define FLIP_STICK_FAST      29490      /* oltre il 90%: ripetizione veloce */
#define FLIP_STICK_REPEAT_US 150000u
#define FLIP_STICK_FAST_US   50000u
#define FLIP_BEND_STEP       64         /* il bend esce quando cambia almeno di tanto (su ±8191) */
#define FLIP_TRIG_ON         160        /* PLT-055: L2 e R2 premuti sopra 160, lasciati sotto 96 */
#define FLIP_TRIG_OFF        96

enum { FLIP_CFG_MK4 = 1, FLIP_CFG_PLUS = 2 };   /* bit di flip_state_t.cfg: tastiera collegata */

typedef struct {
    uint16_t down;          /* bit dei tasti tenuti (indici interni) */
    uint32_t next[4];       /* prossima ripetizione di su, giù, sinistra, destra */
    uint8_t  cfg;           /* FLIP_CFG_*: lo aggiorna input.c a ogni collegamento */
    uint8_t  start_fill;    /* START premuto come Fill (con la MK4): il rilascio chiude il Fill */
    int16_t  bend;          /* ultimo pitch bend mandato dalla levetta sinistra */
    uint8_t  mod;           /* ultima modulazione mandata */
    int32_t  rs[2];         /* levetta destra: X (Bass Voicing), Y (Chord Voicing) */
    int8_t   step[2];       /* passo in corso sui due assi: −1, 0, +1 */
    uint32_t step_next[2];  /* prossima ripetizione del passo */
    uint8_t  trig;          /* bit 0 L2, bit 1 R2 premuti */
    uint32_t dropped;       /* eventi che non stavano in out[] */
} flip_state_t;

extern const ctl_profile_t FLIP_TASTI;

#endif
