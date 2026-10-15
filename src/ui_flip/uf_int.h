/* uf_int.h — parti interne del renderer della plancia (ui_flip). */
#ifndef STAME_UF_INT_H
#define STAME_UF_INT_H

#include "ui_flip.h"
#include "../ui/ui_fmt.h"

extern const gfx_rect_t UF_ZONE_RECT[UF_ZONES];

/* celle della zona comandi (UI-151), nell'ordine di enc_id_t */
extern const gfx_rect_t UF_CELL_RECT[ENC_COUNT];

/* ---- firme (FNV-1a a 64 bit) ---- */
static inline uint64_t uf_h(uint64_t h, const void *p, size_t n)
{
    const uint8_t *b = (const uint8_t *)p;
    for (size_t i = 0; i < n; i++) { h ^= b[i]; h *= 1099511628211ull; }
    return h;
}
#define UF_H0 1469598103934665603ull
#define UF_HV(h, v) uf_h((h), &(v), sizeof(v))

/* ---- aiuti di disegno ---- */
void uf_glass(gfx_fb16_t *fb, const uf_pal_t *p, int x, int y, int w, int h);
/* etichetta stampata sul vetro: XS maiuscolo con un pixel di spaziatura */
int  uf_label(gfx_fb16_t *fb, int x, int y, const char *s, gfx_c c);
int  uf_label_w(const char *s);
int  uf_label_right(gfx_fb16_t *fb, int xr, int y, const char *s, gfx_c c);
gfx_dots_t uf_dots(const uf_pal_t *p, int tok, bool ghost);
gfx_seg_t  uf_seg(const uf_pal_t *p, int tok);
/* barra a segmenti stile VFD: n celle larghe cell, stacco gap; le prime lit accese */
void uf_gauge(gfx_fb16_t *fb, int x, int y, int h, int n, int cell, int gap, int lit, gfx_c on, gfx_c off);
/* nome di un tasto in negativo (legenda viva): ritorna la x dopo il riquadro */
int  uf_keycap(gfx_fb16_t *fb, const uf_pal_t *p, int x, int y, const char *s);
/* classi di nota distinte delle note che suonano (per il cartellino di Linneo) */
int  uf_pcs(const ui_music_t *mu);
bool uf_blink(uint32_t now_ms, uint32_t on_ms, uint32_t off_ms);
/* pagina dei comandi (o lista) al posto della tastiera (UI-142) */
bool uf_controls(const ui_model_t *m);

/* ---- zone ---- */
uint64_t uf_sig_z1(const ui_model_t *m, const ui_flip_state_t *st);
uint64_t uf_sig_z2(const ui_model_t *m);
uint64_t uf_sig_z3(const ui_model_t *m);
uint64_t uf_sig_z4(const ui_model_t *m, int kb_lo);
int      uf_kb_lo(int prev, int W, int WB);           /* prima nota della tastiera (UI-150) */
uint64_t uf_sig_z5_list(const ui_model_t *m);
uint64_t uf_sig_cell(const ui_model_t *m, int k);
uint64_t uf_sig_z6(const ui_model_t *m);

void uf_draw_z1(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m, const ui_flip_state_t *st);
void uf_draw_z2(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m);
void uf_draw_z3(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m);
void uf_draw_z4(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m, int kb_lo);
void uf_draw_z5_frame(gfx_fb16_t *fb, const uf_pal_t *p);
void uf_draw_cell(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m, int k);
void uf_draw_list(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m);
void uf_draw_z6(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m);
void uf_draw_boot(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m);

/* nome dell'accordo a punti (zona accordo e evidenze) */
typedef struct { int p_root, p_mid, p_sup; } uf_name_scale_t;
int  uf_name_w(const chord_label_t *c, const uf_name_scale_t *s);
void uf_name_draw(gfx_fb16_t *fb, const uf_pal_t *p, int x, int base, const chord_label_t *c,
                  const uf_name_scale_t *s, int tok_main, int tok_bass, bool ghost_cells);

#endif
