/* flip_tasti.h — profilo dei tasti della Miyoo Flip, schema a fuoco (sezione 40, §9.1, MIDI-092).
 *
 * L1/R1 spostano il fuoco, la croce ruota l'encoder con il fuoco (con ripetizione), A lo preme,
 * B torna indietro, Y è il Bass Voicing premuto, SELECT Options, START BPM, MENU il menu della
 * piattaforma. X è il PUSH della MPK e lo gestisce mpk_stame.
 *
 * Il modo tascabile (§9.2, MIDI-093/094: opzionale, spento per default) arriva con la fase F5,
 * insieme alle soglie di L2/R2 e delle levette (MIDI-091 e PLT-055 da allineare, T-PLT-10).
 */
#ifndef STAME_FLIP_TASTI_H
#define STAME_FLIP_TASTI_H

#include "profile.h"

#define FLIP_REPEAT_FIRST_US 400000u    /* ripetizione della croce come MIDI-082 */
#define FLIP_REPEAT_US       200000u

typedef struct {
    uint16_t down;          /* bit dei tasti tenuti (indici interni) */
    uint32_t next[4];       /* prossima ripetizione di su, giù, sinistra, destra */
    uint32_t dropped;       /* eventi che non stavano in out[] */
} flip_state_t;

extern const ctl_profile_t FLIP_TASTI;

#endif
