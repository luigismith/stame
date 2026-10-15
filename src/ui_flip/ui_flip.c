/* ui_flip.c — plancia della Flip: zone, firme, aiuti comuni (sezione 30, §4). */
#include "uf_int.h"
#include <math.h>

/* Plancia calma (UI-140): mentre si suona si vedono Z1, Z2, Z3, Z4 e Z6. Z5 prende il posto della
 * tastiera solo quando si usano i tasti della Flip o si apre una lista (UI-142). */
const gfx_rect_t UF_ZONE_RECT[UF_ZONES] = {
    {   0,   0, 640,  24 },     /* Z1 testata: avvisi e batteria */
    {   0,  24, 416, 216 },     /* Z2 accordo */
    { 416,  24, 224, 216 },     /* Z3 tempo e loop */
    {   0, 240, 640, 144 },     /* Z4 tastiera */
    {   0, 240, 640, 144 },     /* Z5 comandi o lista, al posto della tastiera */
    {   0, 384, 640,  96 },     /* Z6 banda: il controllo toccato, il suono, gli avvisi */
};

const gfx_rect_t UF_CELL_RECT[ENC_COUNT] = {
    {   0, 240, 208, 72 },      /* Sound */
    { 208, 240, 160, 72 },      /* Perform */
    { 368, 240, 144, 72 },      /* FX */
    { 512, 240, 128, 72 },      /* Key */
    {   0, 312, 144, 72 },      /* Bass */
    { 144, 312,  80, 72 },      /* Loop */
    { 224, 312,  88, 72 },      /* BPM */
    { 312, 312,  80, 72 },      /* Volume */
    { 392, 312,  72, 72 },      /* Options */
    { 464, 312,  88, 72 },      /* Chord Voicing */
    { 552, 312,  88, 72 },      /* Bass Voicing */
};

bool uf_controls(const ui_model_t *m)
{
    return m->layer.page == PAGE_CONTROLS || m->layer.list.open;
}

/* ---- aiuti ---- */

void uf_glass(gfx_fb16_t *fb, const uf_pal_t *p, int x, int y, int w, int h)
{
    gfx_mesh(fb, x, y, w, h, 4, p->c[T_BG], p->c[T_MESH]);
}

int uf_label(gfx_fb16_t *fb, int x, int y, const char *s, gfx_c c)
{
    return gfx_text_ex(fb, &GFX_XS, x, y, s, c, 1, 1);
}

int uf_label_w(const char *s) { return gfx_text_w(&GFX_XS, s, 1); }

int uf_label_right(gfx_fb16_t *fb, int xr, int y, const char *s, gfx_c c)
{
    return uf_label(fb, xr - uf_label_w(s), y, s, c);
}

gfx_dots_t uf_dots(const uf_pal_t *p, int tok, bool ghost)
{
    gfx_dots_t d;
    d.on = p->c[tok];
    d.on_edge = p->edge[tok];
    d.off = p->c[T_SEGOFF];
    d.ghost = ghost;
    return d;
}

gfx_seg_t uf_seg(const uf_pal_t *p, int tok)
{
    gfx_seg_t s;
    s.on = p->c[tok];
    s.off = p->c[T_SEGOFF];
    s.ghost = true;
    return s;
}

void uf_gauge(gfx_fb16_t *fb, int x, int y, int h, int n, int cell, int gap, int lit, gfx_c on, gfx_c off)
{
    for (int i = 0; i < n; i++)
        gfx_fill(fb, x + i * (cell + gap), y, cell, h, i < lit ? on : off);
}

int uf_keycap(gfx_fb16_t *fb, const uf_pal_t *p, int x, int y, const char *s)
{
    int w = gfx_text_w(&GFX_S, s, 0) + 4;
    gfx_fill(fb, x, y, w, 16, p->c[T_DIM]);
    gfx_text(fb, &GFX_S, x + 2, y, s, p->c[T_BG]);
    return x + w;
}

int uf_pcs(const ui_music_t *mu)
{
    uint16_t pcs = 0;
    for (int i = 0; i < mu->n_notes && i < UI_NOTES_MAX; i++) pcs |= (uint16_t)(1u << (mu->notes[i].midi % 12));
    int n = 0;
    for (int b = 0; b < 12; b++) n += (pcs >> b) & 1;
    return n;
}

bool uf_blink(uint32_t now_ms, uint32_t on_ms, uint32_t off_ms)
{
    return (now_ms % (on_ms + off_ms)) < on_ms;
}

/* ---- meter ---- */

static int peak_db10(uint16_t q15)
{
    if (q15 == 0) return 0;
    float db = 6.0206f * log2f((float)q15 / 32768.0f);
    int v = (int)((db + 48.0f) * 10.0f);
    return v < 0 ? 0 : v > 480 ? 480 : v;
}

static void meters_update(ui_flip_state_t *st, const ui_model_t *m)
{
    uint32_t now = m->now_ms;
    for (int ch = 0; ch < 2; ch++) {
        int v = peak_db10(m->meters.peak[ch]);
        int shown = st->peak_db10[ch];
        if (v >= shown) { st->peak_db10[ch] = st->peak_top[ch] = (uint16_t)v; st->peak_ms[ch] = now; continue; }
        uint32_t held = now - st->peak_ms[ch];
        if (held > 1000u) {
            /* 20 dB/s in decimi dalla fine della tenuta, calcolati dal tempo e non sommati a ogni
             * fotogramma: a passi di pochi ms la caduta si arrotondava a zero */
            uint32_t h = held - 1000u;
            if (h > 60000u) h = 60000u;
            int fallen = (int)st->peak_top[ch] - (int)(h * 200u / 1000u);
            st->peak_db10[ch] = (uint16_t)(fallen < v ? v : fallen);
        }
    }
    st->meter_ms = now;
    if (m->meters.clip_count != st->clip_seen) { st->clip_seen = m->meters.clip_count; st->clip_until = now + 1500; }
    if (m->meters.xrun_count != st->xrun_seen) { st->xrun_seen = m->meters.xrun_count; st->xrun_until = now + 2000; }
}

/* ---- render ---- */

void ui_flip_invalidate(ui_flip_state_t *st) { st->ready = 0; }

static void add_dirty(gfx_rect_t *dirty, int *n, int max, gfx_rect_t r)
{
    if (*n < max) dirty[(*n)++] = r;
    else if (max > 0) { dirty[0].x = 0; dirty[0].y = 0; dirty[0].w = UI_FLIP_W; dirty[0].h = UI_FLIP_H; *n = 1; }
}

int ui_flip_render(ui_flip_state_t *st, const ui_model_t *m, gfx_fb16_t *fb, gfx_rect_t *dirty, int max_dirty)
{
    int n = 0;
    if (!st->ready || st->theme != m->prefs.theme) {
        uf_pal_make(&st->pal, m->prefs.theme);
        st->theme = m->prefs.theme;
        for (int z = 0; z < UF_ZONES; z++) st->sig[z] = 0;
        for (int k = 0; k < ENC_COUNT; k++) st->sig_cell[k] = 0;
        st->sig_boot = 0;
        st->ready = 1;
    }
    const uf_pal_t *p = &st->pal;

    if (m->layer.base == BASE_BOOT) {
        uint64_t h = UF_H0;
        uint16_t t = (uint16_t)(m->boot.t_ms / 33u);
        h = UF_HV(h, t);
        ui_boot_t b = m->boot;                              /* il tempo conta a 30 fotogrammi al secondo, non al ms */
        b.t_ms = 0;
        h = uf_h(h, &b, sizeof b);
        if (h != st->sig_boot || !st->boot_shown) {
            gfx_clip_all(fb);
            uf_draw_boot(fb, p, m);
            st->sig_boot = h;
            st->boot_shown = 1;
            gfx_rect_t r = { 0, 0, UI_FLIP_W, UI_FLIP_H };
            add_dirty(dirty, &n, max_dirty, r);
        }
        for (int z = 0; z < UF_ZONES; z++) st->sig[z] = 0;
        for (int k = 0; k < ENC_COUNT; k++) st->sig_cell[k] = 0;
        return n;
    }
    st->boot_shown = 0;

    meters_update(st, m);
    st->kb_lo = (int16_t)uf_kb_lo(st->ready > 1 ? st->kb_lo : -1, m->music.W, m->music.WB);
    st->ready = 2;

    bool controls = uf_controls(m);
    uint64_t sig[UF_ZONES];
    sig[UF_Z1] = uf_sig_z1(m, st);
    sig[UF_Z2] = uf_sig_z2(m);
    sig[UF_Z3] = uf_sig_z3(m);
    sig[UF_Z4] = uf_sig_z4(m, st->kb_lo);
    sig[UF_Z5] = m->layer.list.open ? uf_sig_z5_list(m) : 1u;
    sig[UF_Z6] = uf_sig_z6(m);

    /* tastiera e comandi stanno nello stesso rettangolo: quella che torna si ridisegna tutta */
    if (controls) st->sig[UF_Z4] = 0;
    else if (st->sig[UF_Z5]) st->sig[UF_Z5] = 0;

    for (int z = 0; z < UF_ZONES; z++) {
        if (z == UF_Z5 || (z == UF_Z4 && controls)) continue;
        if (sig[z] == st->sig[z]) continue;
        const gfx_rect_t *r = &UF_ZONE_RECT[z];
        gfx_clip(fb, r->x, r->y, r->w, r->h);
        switch (z) {
        case UF_Z1: uf_draw_z1(fb, p, m, st); break;
        case UF_Z2: uf_draw_z2(fb, p, m); break;
        case UF_Z3: uf_draw_z3(fb, p, m); break;
        case UF_Z4: uf_draw_z4(fb, p, m, st->kb_lo); break;
        case UF_Z6: uf_draw_z6(fb, p, m); break;
        default: break;
        }
        st->sig[z] = sig[z];
        add_dirty(dirty, &n, max_dirty, *r);
    }

    /* Z5: lista aperta (una zona sola) oppure le 11 celle, ognuna con la sua firma */
    if (!controls) {
        /* pagina di gioco: le celle non si vedono */
    } else if (m->layer.list.open) {
        if (sig[UF_Z5] != st->sig[UF_Z5]) {
            const gfx_rect_t *r = &UF_ZONE_RECT[UF_Z5];
            gfx_clip(fb, r->x, r->y, r->w, r->h);
            uf_draw_list(fb, p, m);
            st->sig[UF_Z5] = sig[UF_Z5];
            add_dirty(dirty, &n, max_dirty, *r);
        }
        for (int k = 0; k < ENC_COUNT; k++) st->sig_cell[k] = 0;
    } else {
        if (st->sig[UF_Z5] != 1u) {                 /* si chiude una lista: si ridisegnano tutte le celle */
            for (int k = 0; k < ENC_COUNT; k++) st->sig_cell[k] = 0;
            st->sig[UF_Z5] = 1u;
        }
        for (int k = 0; k < ENC_COUNT; k++) {
            uint64_t h = uf_sig_cell(m, k);
            if (h == st->sig_cell[k]) continue;
            const gfx_rect_t *r = &UF_CELL_RECT[k];
            gfx_clip(fb, r->x, r->y, r->w, r->h);
            uf_draw_cell(fb, p, m, k);
            st->sig_cell[k] = h;
            add_dirty(dirty, &n, max_dirty, *r);
        }
    }
    gfx_clip_all(fb);
    return n;
}

uint32_t ui_flip_next_visual_ms(const ui_flip_state_t *st, const ui_model_t *m)
{
    uint32_t now = m->now_ms, next = UINT32_MAX;
#define UF_SOON(t) do { uint32_t t_ = (t); if ((int32_t)(t_ - now) > 0 && (int32_t)(t_ - next) < 0) next = t_; } while (0)
    if (m->layer.base == BASE_BOOT) return now + 33;
    UF_SOON(m->plat.midi_in_ms + 50);
    UF_SOON(m->plat.midi_out_ms + 50);
    UF_SOON(st->clip_until);
    UF_SOON(st->xrun_until);
    if (st->peak_db10[0] || st->peak_db10[1]) UF_SOON(now + 33);
    /* lampeggi a 1 Hz (MPK assente, batteria sotto il 10%) e a 500/250 ms (voce in modifica) */
    if (m->plat.mpk_link == MPK_ABSENT || m->plat.battery_pct < 10)          /* 255 = sconosciuta: già ≥ 10 */
        UF_SOON(now - now % 500 + 500);
    if (m->layer.list.open && m->layer.list.editing) UF_SOON(now - now % 250 + 250);
    /* barra del tenuto (UI-153) */
    for (int k = 0; k < ENC_COUNT; k++)
        if ((m->ctl.st[k].flags & CF_PRESSED) && !(m->ctl.st[k].flags & CF_SECONDARY)) UF_SOON(now + 33);
#undef UF_SOON
    return next;
}
