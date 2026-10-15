/* gfx/font.h — font bitmap incorporati (UI-144).
 *
 * gfx_font_t: celle monospazio di Spleen (BSD 2-Clause, third_party/spleen) e simboli di Stame
 * nelle stesse celle; righe di bpr byte, bit più alto = pixel a sinistra; codepoint ordinati.
 * gfx_mfont_t: Matrice, il font a punti 5×7 di Stame (tools/matrice.py).
 * I file font_*.c sono generati da tools/bdf2c.py, tools/simboli.py e tools/matrice.py.
 */
#ifndef STAME_GFX_FONT_H
#define STAME_GFX_FONT_H

#include "../core/stame_base.h"

typedef struct {
    uint8_t  w, h;          /* cella in pixel */
    uint8_t  ascent;        /* righe sopra la linea di base */
    uint8_t  bpr;           /* byte per riga */
    uint16_t n;             /* glifi */
    const uint16_t *cp;     /* codepoint ordinati */
    const uint8_t  *bits;   /* n * h * bpr */
} gfx_font_t;

typedef struct {
    uint8_t w;              /* larghezza in punti, 1..5 */
    uint8_t r[9];           /* righe 0..6 sopra la linea di base, 7..8 discendente; bit w-1 = colonna di sinistra */
} gfx_mglyph_t;

typedef struct {
    uint16_t n;
    const uint16_t *cp;
    const gfx_mglyph_t *g;
} gfx_mfont_t;

extern const gfx_font_t GFX_FONT_6X12, GFX_FONT_8X16, GFX_FONT_12X24, GFX_FONT_16X32, GFX_FONT_32X64;
extern const gfx_font_t GFX_SIMB_6X12, GFX_SIMB_8X16, GFX_SIMB_12X24, GFX_SIMB_16X32, GFX_SIMB_32X64;
extern const gfx_mfont_t GFX_MATRICE;

/* Bitmap del glifo (h * bpr byte) o NULL se il font non ha quel codepoint. */
const uint8_t *gfx_font_glyph(const gfx_font_t *f, uint32_t cp);
/* Glifo di Matrice o NULL. */
const gfx_mglyph_t *gfx_mfont_glyph(const gfx_mfont_t *f, uint32_t cp);

#endif
