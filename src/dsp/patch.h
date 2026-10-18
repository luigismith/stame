/* patch.h — la patch da 135 byte (specifica 20, §2; SND-101…SND-110).
 *
 * Indici, intervalli e nomi della tabella Parinfo dell'editor dell'originale, versione 1.0.2 (= firmware 3.92). Una patch è
 * un array di 135 byte raw, uguale per i tre modelli (VA, Reed Piano, FM).
 */
#ifndef STAME_DSP_PATCH_H
#define STAME_DSP_PATCH_H
#include "../core/stame_base.h"

#define DSP_NPAR 135

/* indici dei parametri (SND-101): oscillatori, inviluppi, LFO e matrice hanno passo costante */
enum {
    SND_P_VER, SND_P_MODEL, SND_P_FMALG, SND_P_HIGHPASS, SND_P_GLIDE, SND_P_GLIDEMODE, SND_P_BENDRANGE,
    SND_P_UNISON, SND_P_UDETUNE, SND_P_HPKT,
    SND_P_O1SHAPE = 10, SND_P_O1SEMI, SND_P_O1DETUNE, SND_P_O1PW, SND_P_O1GAIN,      /* On: 10 + 5·(n−1) */
    SND_P_O4KT = 30, SND_P_O4SYNC, SND_P_O4FB, SND_P_NOISE, SND_P_PINK,
    SND_P_E1A = 35, SND_P_E1H, SND_P_E1D, SND_P_E1S, SND_P_E1R,                      /* En: 35 + 5·(n−1) */
    SND_P_L1SHAPE = 55, SND_P_L1RATE, SND_P_L1MODE,                                  /* Ln: 55 + 3·(n−1) */
    SND_P_FTYPE = 67, SND_P_CUTOFF, SND_P_RESONANCE, SND_P_FENV, SND_P_FVELO, SND_P_FKT,
    SND_P_GAIN, SND_P_GVELO, SND_P_PAN,
    SND_P_M1S = 76, SND_P_M1D, SND_P_M1A,                                            /* Mn: 76 + 3·(n−1) */
    SND_P_FX1TYPE = 100, SND_P_FX1P1,                                                /* FX1P1…P6: 101…106 */
    SND_P_FX2TYPE = 107, SND_P_FX2P1,                                                /* FX2P1…P6: 108…113 */
    SND_P_REVSEND = 114, SND_P_REVSIZE, SND_P_REVLP, SND_P_REVHP,
    SND_P_RPHEIGHT = 118, SND_P_RPDISTANCE, SND_P_RPKT, SND_P_RPICKUP, SND_P_RPDECAY, SND_P_RPRELEASE,
    SND_P_RPTONE, SND_P_RPVELCURVE, SND_P_RPCLANK, SND_P_RPCLANCURVE, SND_P_RPCKT, SND_P_RPTREMOLO,
    SND_P_RPTREMRATE, SND_P_RPVOL, SND_P_RPHAMMER, SND_P_RPKEYOFF, SND_P_RPTSTEREO
};
#define SND_P_O(n, campo) (SND_P_O1SHAPE + 5 * ((n) - 1) + (campo))   /* campo 0 SHAPE … 4 GAIN */
#define SND_P_E(n, campo) (SND_P_E1A + 5 * ((n) - 1) + (campo))       /* campo 0 A, 1 H, 2 D, 3 S, 4 R */
#define SND_P_L(n, campo) (SND_P_L1SHAPE + 3 * ((n) - 1) + (campo))   /* campo 0 SHAPE, 1 RATE, 2 MODE */
#define SND_P_M(n, campo) (SND_P_M1S + 3 * ((n) - 1) + (campo))       /* campo 0 S, 1 D, 2 A */

/* modelli, forme, modi (§2.2). SMP è il campionatore di Stame (§7b): nei byte 118…122 legge
 * SMPSET (= RPHEIGHT), SMPLOOP (= RPDISTANCE), SMPSTART (= RPKT) e SMPTUNE (= RPDECAY). */
enum { SND_MODEL_VA, SND_MODEL_RP, SND_MODEL_FM, SND_MODEL_SMP };
enum { SND_SHAPE_OFF, SND_SHAPE_SAW, SND_SHAPE_PULSE, SND_SHAPE_TRI };
enum { SND_GLIDE_POLY, SND_GLIDE_POLY_LEGATO, SND_GLIDE_MONO, SND_GLIDE_MONO_LEGATO };
enum { SND_LFO_SINE, SND_LFO_TRI, SND_LFO_SQU, SND_LFO_SAW, SND_LFO_SAWN, SND_LFO_RAND, SND_LFO_SH };
enum { SND_LFOM_RESET, SND_LFOM_FREE, SND_LFOM_MONO, SND_LFOM_ONESHOT };
enum { SND_FT_OFF, SND_FT_LP, SND_FT_BP, SND_FT_HP };
enum { SND_FX_OFF, SND_FX_CHORUS, SND_FX_ENSEMBLE, SND_FX_PHASER, SND_FX_FLANGER, SND_FX_DRIVE,
       SND_FX_TREMOLO, SND_FX_DELAY };
enum { SND_PICKUP_NORMAL, SND_PICKUP_MELLOW, SND_PICKUP_SHARP, SND_PICKUP_ODD };

/* sorgenti e destinazioni della matrice (§8.3) */
enum { SND_MS_KEYTRACK, SND_MS_VELOCITY, SND_MS_UNISON, SND_MS_RANDOM, SND_MS_LFO1, SND_MS_ENV1 = 8,
       SND_MS_WHEEL = 12, SND_MS_BEND, SND_MS_UNKNOWN, SND_MS_COUNT };
enum { SND_MD_OFF, SND_MD_PITCH, SND_MD_OSC1, SND_MD_PW1, SND_MD_GAIN1,   /* OSCn, PWn, GAINn: passo 3 */
       SND_MD_PW4FB = 12, SND_MD_GAIN4, SND_MD_GLIDE, SND_MD_CUTOFF, SND_MD_Q, SND_MD_VOLUME, SND_MD_PAN,
       SND_MD_LFO1 = 19, SND_MD_ENV1T = 23, SND_MD_ENV1S = 24,             /* ENVnT 23+2(n−1), ENVnS 24+2(n−1) */
       SND_MD_MOD7 = 31, SND_MD_MOD8, SND_MD_NOISE, SND_MD_COUNT };

/* valore massimo di ogni parametro (SND-102: al caricamento i valori si limitano qui) */
extern const uint8_t snd_par_max[DSP_NPAR];
/* nome del parametro, come nella colonna "Nome" (SND-105), senza il prefisso TREBLE_ */
extern const char *const snd_par_name[DSP_NPAR];

/* patch INIT del modello (SND-110) */
void snd_patch_init(uint8_t p[DSP_NPAR], int model);
/* limita ogni byte al massimo del suo parametro (SND-102) */
void snd_patch_clamp(uint8_t p[DSP_NPAR]);

#endif
