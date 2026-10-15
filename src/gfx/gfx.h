/* gfx/gfx.h — primitive di disegno su framebuffer software RGB565 (UI-001, UI-006).
 *
 * C11 puro, niente heap e niente stato globale: tutto passa dal framebuffer del chiamante.
 * Solo colori pieni e rettangoli o righe di pixel interi, senza fusioni alfa (UI-160 punto 4).
 * I «bordi morbidi» dei punti di Matrice sono colori pieni già mescolati dal chiamante.
 *
 * Coordinate: pixel interi, origine in alto a sinistra. Le forme geometriche (poligoni, dischi,
 * linee spesse) prendono le coordinate in sedicesimi di pixel (GFX_SUB) e accendono i pixel il
 * cui centro cade dentro la forma. Ogni primitiva disegna solo dentro fb->clip.
 */
#ifndef STAME_GFX_H
#define STAME_GFX_H

#include "../core/stame_base.h"
#include "font.h"

#define GFX_SUB 16                     /* sottopixel per pixel delle forme geometriche */

typedef uint16_t gfx_c;                /* colore RGB565 */

typedef struct { int16_t x, y, w, h; } gfx_rect_t;

typedef struct {
    uint16_t  *px;
    uint16_t   w, h, stride;           /* stride in pixel */
    gfx_rect_t clip;                   /* le primitive disegnano solo qui dentro */
} gfx_fb16_t;

/* 0xRRGGBB -> RGB565 */
static inline gfx_c gfx_565(uint32_t rgb)
{
    return (gfx_c)(((rgb >> 8) & 0xF800u) | ((rgb >> 5) & 0x07E0u) | ((rgb >> 3) & 0x001Fu));
}
/* Mescola due colori 0xRRGGBB: t = 0 dà a, t = 256 dà b. */
uint32_t gfx_mix(uint32_t a, uint32_t b, int t);

void gfx_fb_init(gfx_fb16_t *fb, uint16_t *px, int w, int h, int stride);
void gfx_clip(gfx_fb16_t *fb, int x, int y, int w, int h);   /* intersecata con lo schermo */
void gfx_clip_all(gfx_fb16_t *fb);

/* ---- rettangoli e linee ---- */
void gfx_pixel(gfx_fb16_t *fb, int x, int y, gfx_c c);
void gfx_fill(gfx_fb16_t *fb, int x, int y, int w, int h, gfx_c c);
void gfx_hline(gfx_fb16_t *fb, int x, int y, int w, gfx_c c);
void gfx_vline(gfx_fb16_t *fb, int x, int y, int h, gfx_c c);
void gfx_frame(gfx_fb16_t *fb, int x, int y, int w, int h, int t, gfx_c c);
/* linea orizzontale a punti: un pixel acceso ogni step, a partire da x */
void gfx_hdots(gfx_fb16_t *fb, int x, int y, int w, int step, gfx_c c);
void gfx_vdots(gfx_fb16_t *fb, int x, int y, int h, int step, gfx_c c);
/* sfondo «a maglia»: colore bg con un punto mesh ogni step pixel, righe alterne sfalsate (rete dei VFD) */
void gfx_mesh(gfx_fb16_t *fb, int x, int y, int w, int h, int step, gfx_c bg, gfx_c mesh);
/* angoli a squadra (quattro L) di un riquadro: lato l, spessore t */
void gfx_corners(gfx_fb16_t *fb, int x, int y, int w, int h, int l, int t, gfx_c c);

/* ---- forme geometriche, coordinate in 1/GFX_SUB di pixel ---- */
void gfx_poly(gfx_fb16_t *fb, const int32_t *xy, int n, gfx_c c);   /* regola pari-dispari, n <= 32 */
void gfx_disc(gfx_fb16_t *fb, int32_t cx, int32_t cy, int32_t r, gfx_c c);
void gfx_ring(gfx_fb16_t *fb, int32_t cx, int32_t cy, int32_t r, int32_t t, gfx_c c);
/* ellisse piena con i semiassi rx, ry ruotata di ang radianti */
void gfx_ellipse(gfx_fb16_t *fb, int32_t cx, int32_t cy, int32_t rx, int32_t ry, float ang, gfx_c c);
/* segmento spesso w, estremi arrotondati se round */
void gfx_line(gfx_fb16_t *fb, int32_t x0, int32_t y0, int32_t x1, int32_t y1, int32_t w, bool round, gfx_c c);

/* ---- testo con i font a celle ---- */
typedef struct { const gfx_font_t *f, *sym; } gfx_face_t;
extern const gfx_face_t GFX_XS, GFX_S, GFX_M, GFX_L, GFX_XXL;   /* 6x12, 8x16, 12x24, 16x32, 32x64 */

/* Prossimo codepoint di una stringa UTF-8 (0 alla fine); una sequenza rotta dà '?'. */
uint32_t gfx_utf8(const char **s);
int  gfx_text_len(const char *s);                                   /* codepoint */
int  gfx_text_w(const gfx_face_t *f, const char *s, int extra);     /* larghezza in pixel */
/* y = cima della cella; extra = pixel in più dopo ogni carattere; scale intera >= 1.
 * Ritorna la x dopo l'ultimo carattere. Un codepoint che nessuno dei due font ha diventa '?'. */
int  gfx_text_ex(gfx_fb16_t *fb, const gfx_face_t *f, int x, int y, const char *s, gfx_c fg,
                 int extra, int scale);
static inline int gfx_text(gfx_fb16_t *fb, const gfx_face_t *f, int x, int y, const char *s, gfx_c fg)
{
    return gfx_text_ex(fb, f, x, y, s, fg, 0, 1);
}
/* Come gfx_text, ma tronca con «…» se supera max_w pixel. */
int  gfx_text_fit(gfx_fb16_t *fb, const gfx_face_t *f, int x, int y, const char *s, gfx_c fg, int max_w);
/* Allineamenti: x è il bordo destro o il centro. */
int  gfx_text_right(gfx_fb16_t *fb, const gfx_face_t *f, int x_right, int y, const char *s, gfx_c fg, int extra);
int  gfx_text_center(gfx_fb16_t *fb, const gfx_face_t *f, int x_mid, int y, const char *s, gfx_c fg, int extra);

/* ---- Matrice: testo a punti, come i display a fluorescenza ---- */
typedef struct {
    gfx_c on, on_edge;      /* punto acceso: centro e bordo (bordo = on mescolato con lo sfondo) */
    gfx_c off;              /* punto spento della cella */
    bool  ghost;            /* disegna anche i punti spenti */
} gfx_dots_t;
/* Larghezza in pixel di un testo con passo pitch (un punto = pitch pixel, una colonna di stacco). */
int  gfx_matrix_w(const char *s, int pitch);
/* base = riga sotto l'ultima riga di punti della lettera (linea di base). Ritorna la x finale. */
int  gfx_matrix(gfx_fb16_t *fb, int x, int base, int pitch, const char *s, const gfx_dots_t *d);

/* ---- cifre a sette segmenti, inclinate come sui VFD ---- */
typedef struct { gfx_c on, off; bool ghost; } gfx_seg_t;
int  gfx_seg7_w(int h, const char *s);
/* Cifre 0–9, spazio, '-', ':', '.', e le lettere A b C d E F H L n o P r t U u y. Ritorna la x finale. */
int  gfx_seg7(gfx_fb16_t *fb, int x, int y, int h, const char *s, const gfx_seg_t *c);

#endif
