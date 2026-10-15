/* campioni_idx.h — indici dei set del banco stame.smp (specifica 20, §7b). Generato da
 * tools/campioni.py: non va modificato a mano. Le patch SMP mettono l'indice in SMPSET. */
#ifndef STAME_CAMPIONI_IDX_H
#define STAME_CAMPIONI_IDX_H

enum {
    SMP_SET_PIANO_KAWAI = 0,        /* 18 zone */
    SMP_SET_PIANO_UPRIGHT = 1,      /* 13 zone */
    SMP_SET_FM_PIANO = 2,           /* 22 zone */
    SMP_SET_VIBES = 3,              /* 11 zone */
    SMP_SET_MARIMBA = 4,            /* 10 zone */
    SMP_SET_GLOCK = 5,              /* 6 zone */
    SMP_SET_CHIMES = 6,             /* 9 zone */
    SMP_SET_HARP = 7,               /* 11 zone */
    SMP_SET_KALIMBA = 8,            /* 15 zone */
    SMP_SET_HARPSICHORD = 9,        /* 15 zone */
    SMP_SET_ORGAN = 10,             /* 11 zone */
    SMP_SET_RECORDER = 11,          /* 12 zone */
    SMP_SET_SAX = 12,               /* 12 zone */
    SMP_SET_KIT_STUDIO = 13,        /* 13 zone */
    SMP_SET_KIT_JAZZ = 14,          /* 13 zone */
    SMP_SET_KIT_808 = 15,           /* 12 zone */
    SMP_SET_COUNT = 16
};

#endif
