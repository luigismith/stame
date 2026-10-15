/* ui_flip/ui_flip.h — la plancia 640×480 della Flip, disegnata da ui_model_t (sezione 30, §4).
 *
 * Funzione pura del modello e dello stato visivo (UI-003, UI-005): firme delle zone per ridisegnare
 * solo ciò che cambia (UI-160), caduta dei meter, lampeggi. La memoria la dà il chiamante.
 *
 *     static ui_flip_state_t st;      // azzerata
 *     static uint16_t px[640 * 480];
 *     gfx_fb16_t fb; gfx_fb_init(&fb, px, 640, 480, 640);
 *     gfx_rect_t dirty[UI_FLIP_MAX_DIRTY];
 *     int n = ui_flip_render(&st, &model, &fb, dirty, UI_FLIP_MAX_DIRTY);
 */
#ifndef STAME_UI_FLIP_H
#define STAME_UI_FLIP_H

#include "../ui/ui_model.h"
#include "../gfx/gfx.h"
#include "tema.h"

#define UI_FLIP_W 640
#define UI_FLIP_H 480
#define UI_FLIP_MAX_DIRTY 24

enum { UF_Z1, UF_Z2, UF_Z3, UF_Z4, UF_Z5, UF_Z6, UF_ZONES };

typedef struct ui_flip_state {
    uint8_t  ready;                    /* 0 = tutto da ridisegnare */
    uint8_t  theme;
    uf_pal_t pal;
    uint64_t sig[UF_ZONES];
    uint64_t sig_cell[ENC_COUNT];
    uint64_t sig_boot;
    uint8_t  boot_shown;
    int16_t  kb_lo;                    /* prima nota della tastiera; si sposta solo se serve (UI-150) */
    /* meter (UI-126): picco mostrato con caduta di 20 dB/s e tenuta di 1 s */
    uint16_t peak_db10[2];             /* decimi di dB sopra -48 dBFS: 0..480 */
    uint32_t peak_ms[2];
    uint32_t meter_ms;
    uint32_t clip_seen, clip_until;
    uint32_t xrun_seen, xrun_until;
} ui_flip_state_t;

/* Disegna le zone cambiate; scrive in dirty i rettangoli ridisegnati e ne ritorna il numero. */
int      ui_flip_render(ui_flip_state_t *st, const ui_model_t *m, gfx_fb16_t *fb,
                        gfx_rect_t *dirty, int max_dirty);
/* Primo istante (orologio della piattaforma) in cui cambierà qualcosa di solo visivo. */
uint32_t ui_flip_next_visual_ms(const ui_flip_state_t *st, const ui_model_t *m);
/* Obbliga a ridisegnare tutto al prossimo render (per esempio dopo una sospensione). */
void     ui_flip_invalidate(ui_flip_state_t *st);

/* Il marchio di Stame (tre stami) centrato in (cx, cy), alto size pixel; grow 0..256 fa crescere
 * i filamenti, anthers 0..3 accende le antere una alla volta (animazione dell'avvio). */
void     ui_flip_logo(gfx_fb16_t *fb, int cx, int cy, int size, gfx_c filament, gfx_c anther,
                      gfx_c anther_off, int grow, int anthers);

#endif
