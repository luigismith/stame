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
 * Il modo tascabile (§9.2, MIDI-093/094: opzionale, spento per default) arriva con la fase F5,
 * insieme alle soglie di L2/R2 e delle levette (MIDI-091 e PLT-055 da allineare, T-PLT-10).
 */
#ifndef STAME_FLIP_TASTI_H
#define STAME_FLIP_TASTI_H

#include "profile.h"

#define FLIP_REPEAT_FIRST_US 400000u    /* ripetizione della croce come MIDI-082 */
#define FLIP_REPEAT_US       200000u

enum { FLIP_CFG_MK4 = 1, FLIP_CFG_PLUS = 2 };   /* bit di flip_state_t.cfg: tastiera collegata */

typedef struct {
    uint16_t down;          /* bit dei tasti tenuti (indici interni) */
    uint32_t next[4];       /* prossima ripetizione di su, giù, sinistra, destra */
    uint8_t  cfg;           /* FLIP_CFG_*: lo aggiorna input.c a ogni collegamento */
    uint8_t  start_fill;    /* START premuto come Fill (con la MK4): il rilascio chiude il Fill */
    uint32_t dropped;       /* eventi che non stavano in out[] */
} flip_state_t;

extern const ctl_profile_t FLIP_TASTI;

#endif
