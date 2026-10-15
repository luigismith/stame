/* curves.h — curve raw → grandezza fisica (specifica 20, §3, SND-150).
 * Generato da tools/curve.py: non modificare a mano. */
#ifndef STAME_DSP_CURVES_H
#define STAME_DSP_CURVES_H
#include "../core/stame_base.h"

enum {
    CURVE_T_ATT,
    CURVE_T_HOLD,
    CURVE_T_DEC,
    CURVE_T_GLIDE,
    CURVE_F_LFO,
    CURVE_F_CUT,
    CURVE_K_RES,
    CURVE_F_HP,
    CURVE_G_VOL,
    CURVE_G_OSC,
    CURVE_F_FX_RATE,
    CURVE_T_DELAY,
    CURVE_T_RP_DECAY,
    CURVE_T_RP_RELEASE,
    CURVE_F_RP_TREM,
    CURVE_T_REV,
    CURVE_F_REVLP,
    CURVE_F_REVHP,
    CURVE_F_DLYLP,
    CURVE_F_DLYHP,
    CURVE_COUNT
};

/* tabelle da 128 valori, una per curva */
extern const float dsp_curves[CURVE_COUNT][128];

/* valore della curva c al raw r (0…127); fra due raw interpola linearmente */
static inline float curve(int c, float r)
{
    if (!(r > 0.0f)) return dsp_curves[c][0];
    if (r >= 127.0f) return dsp_curves[c][127];
    int i = (int)r;
    float t = r - (float)i;
    return dsp_curves[c][i] + t * (dsp_curves[c][i + 1] - dsp_curves[c][i]);
}

/* valore al raw intero */
static inline float curve_i(int c, int r) { return dsp_curves[c][r < 0 ? 0 : r > 127 ? 127 : r]; }

#endif
