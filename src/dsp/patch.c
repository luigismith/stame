/* patch.c — intervalli, nomi e patch INIT (specifica 20, §2.2 e §2.4). */
#include "patch.h"

/* massimi dalla colonna "Range" di §2.2; dove non indicato 127 */
const uint8_t snd_par_max[DSP_NPAR] STAME_ROM = {
    2, 2, 7, 127, 127, 3, 12, 4, 127, 127,                 /* VER … HPKT */
    3, 127, 127, 127, 127,  3, 127, 127, 127, 127,          /* O1, O2 */
    3, 127, 127, 127, 127,  3, 127, 127, 127, 127,          /* O3, O4 */
    1, 1, 127, 127, 1,                                      /* O4KT, O4SYNC, O4FB, NOISE, PINK */
    127, 127, 127, 127, 127,  127, 127, 127, 127, 127,      /* E1, E2 */
    127, 127, 127, 127, 127,  127, 127, 127, 127, 127,      /* E3, E4 */
    6, 127, 3,  6, 127, 3,  6, 127, 3,  6, 127, 3,          /* L1…L4 */
    3, 127, 127, 127, 127, 127, 127, 127, 127,              /* FTYPE … PAN */
    14, 33, 127,  14, 33, 127,  14, 33, 127,  14, 33, 127,  /* M1…M4 */
    14, 33, 127,  14, 33, 127,  14, 33, 127,  14, 33, 127,  /* M5…M8 */
    6, 127, 127, 127, 127, 127, 127,                        /* FX1 */
    7, 127, 127, 127, 127, 127, 127,                        /* FX2 */
    127, 127, 127, 127,                                     /* REVSEND … REVHP */
    127, 127, 127, 3, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127, 127,   /* RP */
};

const char *const snd_par_name[DSP_NPAR] STAME_ROM = {
    "VER", "MODEL", "FMALG", "HIGHPASS", "GLIDE", "GLIDEMODE", "BENDRANGE", "UNISON", "UDETUNE", "HPKT",
    "O1SHAPE", "O1SEMI", "O1DETUNE", "O1PW", "O1GAIN", "O2SHAPE", "O2SEMI", "O2DETUNE", "O2PW", "O2GAIN",
    "O3SHAPE", "O3SEMI", "O3DETUNE", "O3PW", "O3GAIN", "O4SHAPE", "O4SEMI", "O4DETUNE", "O4PW", "O4GAIN",
    "O4KT", "O4SYNC", "O4FB", "NOISE", "PINK",
    "E1A", "E1H", "E1D", "E1S", "E1R", "E2A", "E2H", "E2D", "E2S", "E2R",
    "E3A", "E3H", "E3D", "E3S", "E3R", "E4A", "E4H", "E4D", "E4S", "E4R",
    "L1SHAPE", "L1RATE", "L1MODE", "L2SHAPE", "L2RATE", "L2MODE",
    "L3SHAPE", "L3RATE", "L3MODE", "L4SHAPE", "L4RATE", "L4MODE",
    "FTYPE", "CUTOFF", "RESONANCE", "FENV", "FVELO", "FKT", "GAIN", "GVELO", "PAN",
    "M1S", "M1D", "M1A", "M2S", "M2D", "M2A", "M3S", "M3D", "M3A", "M4S", "M4D", "M4A",
    "M5S", "M5D", "M5A", "M6S", "M6D", "M6A", "M7S", "M7D", "M7A", "M8S", "M8D", "M8A",
    "FX1TYPE", "FX1P1", "FX1P2", "FX1P3", "FX1P4", "FX1P5", "FX1P6",
    "FX2TYPE", "FX2P1", "FX2P2", "FX2P3", "FX2P4", "FX2P5", "FX2P6",
    "REVSEND", "REVSIZE", "REVLP", "REVHP",
    "RPHEIGHT", "RPDISTANCE", "RPKT", "RPICKUP", "RPDECAY", "RPRELEASE", "RPTONE", "RPVELCURVE",
    "RPCLANK", "RPCLANCURVE", "RPCKT", "RPTREMOLO", "RPTREMRATE", "RPVOL", "RPHAMMER", "RPKEYOFF",
    "RPTSTEREO",
};

/* default della tabella Parinfo (colonna "Def" di §2.2) */
static const uint8_t DEF[DSP_NPAR] STAME_ROM = {
    2, 0, 0, 0, 0, 0, 2, 0, 0, 0,
    1, 64, 64, 64, 64,  0, 64, 64, 64, 0,
    0, 64, 64, 64, 0,   0, 64, 64, 64, 0,
    1, 0, 0, 0, 0,
    0, 0, 64, 64, 64,   0, 0, 64, 127, 64,
    0, 0, 64, 127, 64,  0, 0, 64, 127, 64,
    0, 0, 0,  0, 0, 0,  0, 0, 0,  0, 0, 0,
    1, 127, 0, 0, 0, 0, 64, 0, 64,
    0, 0, 64,  0, 0, 64,  0, 0, 64,  0, 0, 64,
    0, 0, 64,  0, 0, 64,  0, 0, 64,  0, 0, 64,
    0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0,
    0, 100, 120, 10,
    10, 10, 64, 0, 110, 32, 64, 90, 32, 32, 32, 0, 80, 127, 16, 16, 0,
};

void snd_patch_init(uint8_t p[DSP_NPAR], int model)
{
    memcpy(p, DEF, DSP_NPAR);
    p[SND_P_MODEL] = (uint8_t)(model < 0 ? 0 : model > 2 ? 2 : model);
    if (model == SND_MODEL_RP) {            /* SND-110: in INIT - REED PIANO cambiano tre campi */
        p[SND_P_RPHEIGHT] = 64;
        p[SND_P_RPDISTANCE] = 64;
        p[SND_P_RPVOL] = 64;
    }
}

void snd_patch_clamp(uint8_t p[DSP_NPAR])
{
    for (int i = 0; i < DSP_NPAR; i++)
        if (p[i] > snd_par_max[i]) p[i] = snd_par_max[i];
}
