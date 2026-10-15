/* zona_tempo.c — Z3, tempo e loop (UI-148, UI-149).
 *
 * Il BPM sta su cifre a sette segmenti con i segmenti spenti visibili, come un frequenzimetro.
 * Sotto, i movimenti della battuta. Il looper compare solo quando lavora (o quando si tocca il suo
 * controllo): stato, giro e menu a tre voci. Metrica, ritmo e numero di battuta sono di Geek Out.
 */
#include "uf_int.h"

#define X0 428
#define XW 204

static bool recording(const ui_looper_t *lp)
{
    return lp->state == LP_REC || lp->state == LP_OVERDUB || lp->state == LP_COUNT_IN;
}

static bool looper_shown(const ui_model_t *m)
{
    return m->looper.state != LP_IDLE || m->ctl.turn_target == ENC_LOOP;
}

static bool beat_flash(const ui_model_t *m)
{
    const ui_tempo_t *t = &m->tempo;
    if (!m->prefs.beat_flash || !t->running || !t->bpm) return false;
    uint32_t beat_ms = 60000u / t->bpm;
    return (uint32_t)t->beat_phase * beat_ms / 65536u < 60u;
}

uint64_t uf_sig_z3(const ui_model_t *m)
{
    uint64_t h = UF_H0;
    ui_tempo_t t = m->tempo;
    t.beat_phase = 0;                                  /* la fase conta solo per il lampo */
    if (m->ctl.view != VIEW_GEEK) t.bar = 0;           /* la battuta si scrive solo in Geek Out */
    h = uf_h(h, &t, sizeof t);
    ui_looper_t lp = m->looper;
    lp.progress = 0;                                   /* la testina conta per pixel, qui sotto: non a ogni fotogramma */
    h = uf_h(h, &lp, sizeof lp);
    uint8_t v[5] = { m->ctl.turn_target, (uint8_t)beat_flash(m), m->prefs.theme, 0, (uint8_t)(m->ctl.view == VIEW_GEEK) };
    if (m->looper.state == LP_REC && m->looper.free_mode && m->looper.bars == 0) v[3] = (uint8_t)(m->now_ms / 100u);
    h = uf_h(h, v, sizeof v);
    /* la barra si ridisegna quando la testina avanza di un pixel */
    uint16_t px = (uint16_t)((uint32_t)m->looper.progress * XW / 65536u);
    h = UF_HV(h, px);
    return h;
}

static const char *item_name(uint8_t it)
{
    static const char *const N[] = { "REC", "PLAY", "BACK", "OVERDUB", "PAUSE", "CLEAR", "STOP", "UNDO" };
    return it < STAME_COUNT(N) ? N[it] : "";
}

static void progress_bar(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m, int y, int h)
{
    const ui_looper_t *lp = &m->looper;
    int bars = lp->bars ? lp->bars : 1;
    bool wait = lp->state == LP_WAITING_ROOM;
    if (wait) bars = lp->wr_choice ? lp->wr_choice : 1;
    int head = (int)((uint32_t)lp->progress * XW / 65536u);
    gfx_c on = p->c[recording(lp) ? T_WARN : T_LOOP];
    bool free_rec = lp->state == LP_REC && lp->free_mode && lp->bars == 0;
    bool active = lp->state == LP_PLAY || lp->state == LP_REC || lp->state == LP_OVERDUB || lp->state == LP_PAUSE;
    for (int i = 0; i < XW; i++) {
        /* stacco di 2 pixel fra le battute */
        int seg = i * bars / XW, seg_next = (i + 2) * bars / XW;
        if (bars > 1 && seg_next != seg && i + 2 < XW) continue;
        if (i % 4 == 3) continue;                            /* celle di 3 pixel */
        gfx_c c = p->c[T_SEGOFF];
        if (free_rec) {
            if (((i + (int)(m->now_ms / 100u) * 4) / 8) % 2 == 0) c = on;
        } else if (active && i < head) {
            c = on;
        }
        gfx_fill(fb, X0 + i, y, 1, h, c);
    }
    if (active && !free_rec) gfx_fill(fb, X0 + head, y - 2, 2, h + 4, p->c[T_TEXT]);
}

/* Geek Out: metrica, ritmo e battuta, in piccolo */
static void geek_line(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m, int y)
{
    const ui_tempo_t *t = &m->tempo;
    const ui_looper_t *lp = &m->looper;
    char buf[32], n2[8];
    int x;
    if (lp->slot) {
        ui_fmt_int(n2, sizeof n2, lp->slot, 2);
        x = uf_label(fb, X0, y + 2, "LOOP", p->c[T_DIM]);
        gfx_text(fb, &GFX_S, x + 6, y, n2, p->c[T_LOOP]);
    } else if (t->beat_mode == BEAT_PATTERN) {
        ui_fmt_int(n2, sizeof n2, t->beat_index, 2);
        ui_fmt_cat(buf, sizeof buf, n2, " ");
        ui_fmt_cat(buf, sizeof buf, buf, t->beat_name);
        x = uf_label(fb, X0, y + 2, "BEAT", p->c[T_DIM]);
        gfx_text_fit(fb, &GFX_S, x + 6, y, buf, p->c[T_TEXT], 104);
    } else if (t->beat_mode == BEAT_METRONOME) {
        uf_label(fb, X0, y + 2, "METRO", p->c[T_TEXT]);
    } else {
        uf_label(fb, X0, y + 2, "BEAT OFF", p->c[T_DIM]);
    }
    if (t->running) {
        ui_fmt_int(n2, sizeof n2, (int)(t->bar > 999 ? 999 : t->bar), 1);
        int w = gfx_text_w(&GFX_S, n2, 0);
        gfx_text(fb, &GFX_S, X0 + XW - w, y, n2, p->c[T_TEXT]);
        uf_label_right(fb, X0 + XW - w - 6, y + 2, "BAR", p->c[T_DIM]);
    }
}

void uf_draw_z3(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m)
{
    const ui_tempo_t *t = &m->tempo;
    const ui_looper_t *lp = &m->looper;
    bool geek = m->ctl.view == VIEW_GEEK;
    gfx_hline(fb, 416, 24, 224, p->c[T_LINE]);
    gfx_vline(fb, 416, 24, 216, p->c[T_LINE]);
    uf_glass(fb, p, 417, 25, 223, 215);
    if (recording(lp)) gfx_frame(fb, 417, 25, 223, 215, 2, p->c[T_WARN]);

    /* BPM a sette segmenti, alto abbastanza da leggersi a un braccio */
    char buf[24], n2[8];
    if (beat_flash(m)) gfx_fill(fb, X0 - 4, 32, 112, 58, p->c[T_BAR]);
    int bpm = t->bpm > 999 ? 999 : t->bpm;
    ui_fmt_int(n2, sizeof n2, bpm, 1);
    buf[0] = 0;
    for (int i = gfx_text_len(n2); i < 3; i++) ui_fmt_cat(buf, sizeof buf, buf, " ");
    ui_fmt_cat(buf, sizeof buf, buf, n2);
    gfx_seg_t sg = uf_seg(p, T_TEXT);
    int x = gfx_seg7(fb, X0, 36, 50, buf, &sg);
    uf_label(fb, x + 8, 76, "BPM", p->c[T_DIM]);
    if (geek) {
        ui_fmt_int(buf, sizeof buf, t->beats_per_bar, 1);
        ui_fmt_int(n2, sizeof n2, t->beat_unit, 1);
        ui_fmt_cat(buf, sizeof buf, buf, "/");
        ui_fmt_cat(buf, sizeof buf, buf, n2);
        gfx_text_right(fb, &GFX_M, X0 + XW, 34, buf, p->c[T_TEXT], 0);
        geek_line(fb, p, m, 94);
    }

    /* celle dei movimenti */
    int n = t->beats_per_bar ? t->beats_per_bar : 4;
    int cw = (XW - 6 * (n - 1)) / n;
    for (int i = 0; i < n; i++) {
        int cx = X0 + i * (cw + 6);
        bool cur = t->running && t->beat == i;
        gfx_c c = cur ? p->c[i == 0 ? T_FOCUS : T_TEXT] : p->c[T_SEGOFF];
        gfx_fill(fb, cx, 116, cw, 28, c);
        if (lp->state == LP_COUNT_IN && lp->count_in) {
            int left = lp->count_in;
            if (i == n - left || (n - left < 0 && i == 0)) {
                ui_fmt_int(n2, sizeof n2, left, 1);
                gfx_text_center(fb, &GFX_M, cx + cw / 2, 118, n2, cur ? p->c[T_BG] : p->c[T_TEXT], 0);
            }
        }
    }

    if (!looper_shown(m)) return;

    /* stato del looper */
    const char *st = "LOOP";
    int tok = T_DIM;
    switch (lp->state) {
    case LP_REC:          st = "\xE2\x97\x8F REC"; tok = T_WARN; break;
    case LP_OVERDUB:      st = "\xE2\x97\x89 DUB"; tok = T_WARN; break;
    case LP_PLAY:         st = "\xE2\x96\xB6 PLAY"; tok = T_LOOP; break;
    case LP_PAUSE:        st = "\xE2\x9D\x9A\xE2\x9D\x9A PAUSE"; tok = T_DIM; break;
    case LP_WAITING_ROOM: st = "WAIT"; tok = T_ACTIVE; break;
    case LP_COUNT_IN:     st = "COUNT"; tok = T_WARN; break;
    default: break;
    }
    gfx_text(fb, &GFX_L, X0, 152, st, p->c[tok]);
    if (lp->state != LP_IDLE) {
        if (lp->free_mode && lp->bars == 0) ui_fmt_copy(buf, sizeof buf, "FREE");
        else {
            ui_fmt_int(buf, sizeof buf, lp->cur_bar, 1);
            ui_fmt_int(n2, sizeof n2, lp->bars, 1);
            ui_fmt_cat(buf, sizeof buf, buf, "/");
            ui_fmt_cat(buf, sizeof buf, buf, n2);
        }
        int w = gfx_text_w(&GFX_L, buf, 0);
        gfx_text(fb, &GFX_L, X0 + XW - w, 152, buf, p->c[T_TEXT]);
        if (lp->layers) {
            ui_fmt_int(n2, sizeof n2, lp->layers, 1);
            ui_fmt_cat(buf, sizeof buf, "L", n2);
            gfx_text_right(fb, &GFX_S, X0 + XW - w - 8, 166, buf, p->c[T_LOOP], 0);
        }
        if (lp->loop_full) uf_label(fb, X0 + 112, 150, "FULL", p->c[T_WARN]);
    }
    progress_bar(fb, p, m, 190, 12);

    /* menu a tre voci (UI-088) */
    int bw = (XW - 8) / 3;
    for (int i = 0; i < 3; i++) {
        int bx = X0 + i * (bw + 4);
        const char *nm = item_name(lp->menu[i]);
        bool sel = lp->menu_sel == i;
        if (sel) {
            gfx_fill(fb, bx, 210, bw, 24, p->c[m->ctl.turn_target == ENC_LOOP ? T_FOCUS : T_BAR]);
            gfx_text_center(fb, &GFX_S, bx + bw / 2, 214, nm, m->ctl.turn_target == ENC_LOOP ? p->c[T_BG] : p->c[T_TEXT], 0);
        } else {
            gfx_frame(fb, bx, 210, bw, 24, 1, p->c[T_LINE]);
            gfx_text_center(fb, &GFX_S, bx + bw / 2, 214, nm, p->c[T_DIM], 0);
        }
    }
}
