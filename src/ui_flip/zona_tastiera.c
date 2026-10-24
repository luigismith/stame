/* zona_tastiera.c — Z4, tastiera di 4 ottave che segue le finestre del voicing (UI-150).
 *
 * Tasti come segmenti di un VFD: spenti ma visibili, accesi nel colore del ruolo. Le note della
 * tonalità hanno un granello di polline (un punto tondo). Le finestre del voicing sono filamenti
 * sopra i tasti, con un'antera tonda a ogni capo: compaiono mentre si gira un voicing e in Geek Out.
 */
#include "uf_int.h"

#define KX0 12
#define KW  22          /* passo dei tasti bianchi */
#define ZY  240         /* cima della zona */
#define WY0 262
#define WY1 362         /* bianchi: righe 262..361 */
#define BY1 322         /* neri: righe 262..321 */

static const int8_t WHITE_OF[12] = { 0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6 };
static const bool   IS_BLACK[12] = { 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0 };

int uf_kb_lo(int prev, int W, int WB)
{
    int lo = W < WB ? W : WB, hi = (W > WB ? W : WB) + 11;
    int kb = prev;
    if (kb < 0 || kb % 12) kb = (WB / 12) * 12;
    if (hi - lo + 1 > 48) {                     /* le finestre non stanno insieme: vince il treble */
        lo = W;
        hi = W + 11;
    }
    while (lo < kb) kb -= 12;
    while (hi > kb + 47) kb += 12;
    if (kb < 0) kb = 0;
    if (kb > 120 - 48) kb = 72;
    return kb;
}

/* filamenti delle finestre: solo mentre si gira un voicing (overlay) e in Geek Out */
static bool windows_shown(const ui_model_t *m)
{
    uint8_t k = m->layer.ov.kind;
    return m->ctl.view == VIEW_GEEK || k == OV_VOICING || k == OV_BASS_VOICING || k == OV_SINGLE_NOTES;
}

static bool bit128(const uint32_t *m, int n) { return n >= 0 && n < 128 && (m[n >> 5] >> (n & 31)) & 1u; }

/* x del tasto (bordo sinistro) e larghezza, per la nota n con la gamma da kb_lo */
static void key_box(int kb_lo, int n, int *x, int *w, bool *black)
{
    int rel = n - kb_lo, oct = rel / 12, pc = rel % 12;
    int wi = oct * 7 + WHITE_OF[pc];
    *black = IS_BLACK[pc];
    if (*black) { *x = KX0 + KW * wi + 15; *w = 13; }
    else        { *x = KX0 + KW * wi;      *w = 21; }
}

uint64_t uf_sig_z4(const ui_model_t *m, int kb_lo)
{
    const ui_music_t *mu = &m->music;
    uint64_t h = UF_H0;
    h = uf_h(h, mu->live_treble, sizeof mu->live_treble);
    h = uf_h(h, mu->live_bass, sizeof mu->live_bass);
    h = uf_h(h, mu->loop_treble, sizeof mu->loop_treble);
    h = uf_h(h, mu->loop_bass, sizeof mu->loop_bass);
    h = uf_h(h, mu->amb_treble, sizeof mu->amb_treble);
    uint8_t v[11] = { mu->W, mu->WB, mu->single_notes, mu->pocket_pc, m->prefs.pocket, m->prefs.note_labels,
                      (uint8_t)kb_lo, m->prefs.theme, (uint8_t)(mu->pc_in_key & 0xFF), (uint8_t)(mu->pc_in_key >> 8),
                      (uint8_t)windows_shown(m) };
    h = uf_h(h, v, sizeof v);
    return h;
}

static void window(gfx_fb16_t *fb, const uf_pal_t *p, int kb_lo, int start, int y, int tok)
{
    int x0, w0, x1, w1;
    bool b0, b1;
    int a = start < kb_lo ? kb_lo : start, b = start + 11 > kb_lo + 47 ? kb_lo + 47 : start + 11;
    if (b < a) return;
    key_box(kb_lo, a, &x0, &w0, &b0);
    key_box(kb_lo, b, &x1, &w1, &b1);
    int xa = x0, xb = x1 + w1;
    gfx_fill(fb, xa + 3, y, xb - xa - 6, 2, p->c[tok]);
    /* antere ai due capi */
    gfx_disc(fb, (xa + 2) * GFX_SUB, y * GFX_SUB + GFX_SUB, 3 * GFX_SUB, p->c[tok]);
    gfx_disc(fb, (xb - 2) * GFX_SUB, y * GFX_SUB + GFX_SUB, 3 * GFX_SUB, p->c[tok]);
}

static void draw_key(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m, int kb_lo, int n, bool black)
{
    const ui_music_t *mu = &m->music;
    int x, w;
    bool bk;
    key_box(kb_lo, n, &x, &w, &bk);
    (void)black;
    int y1 = bk ? BY1 : WY1;
    bool t = bit128(mu->live_treble, n), b = bit128(mu->live_bass, n);
    gfx_c base = bk ? p->c[T_KBB] : p->c[T_KBW];
    if (bk) gfx_fill(fb, x - 1, WY0, w + 2, y1 - WY0 + 1, p->c[T_BG]);
    if (t && b) {
        gfx_fill(fb, x, WY0, w / 2, y1 - WY0, p->c[T_TREBLE]);
        gfx_fill(fb, x + w / 2, WY0, w - w / 2, y1 - WY0, p->c[T_BASS]);
    } else {
        gfx_fill(fb, x, WY0, w, y1 - WY0, t ? p->c[T_TREBLE] : b ? p->c[T_BASS] : base);
    }
    if (bk && !t && !b) gfx_frame(fb, x, WY0, w, y1 - WY0, 1, p->c[T_LINE]);
    /* note del looper: striscia in fondo al tasto */
    if (bit128(mu->loop_treble, n) || bit128(mu->loop_bass, n)) {
        if (bk) gfx_fill(fb, x, BY1 - 8, w, 8, p->c[T_LOOP]);
        else gfx_fill(fb, x, WY1 - 12, w, 12, p->c[T_LOOP]);
    } else if (bit128(mu->amb_treble, n)) {                       /* le note sparse di AMBIENT (MIDI-143) */
        if (bk) gfx_fill(fb, x, BY1 - 8, w, 8, p->c[T_ACTIVE]);
        else gfx_fill(fb, x, WY1 - 12, w, 12, p->c[T_ACTIVE]);
    }
    /* granello di polline sulle note della tonalità */
    if (mu->pc_in_key >> (n % 12) & 1) {
        gfx_c c = (t || b) ? p->c[T_BG] : p->c[T_INKEY];
        if (bk) gfx_disc(fb, (x * 2 + w) * GFX_SUB / 2, (BY1 - 14) * GFX_SUB + 8, 5 * GFX_SUB / 2, c);
        else gfx_disc(fb, (x * 2 + w) * GFX_SUB / 2, (WY1 - 20) * GFX_SUB + 8, 3 * GFX_SUB, c);
    }
    /* modo tascabile: contorno sulla classe scelta, dentro la finestra treble */
    if (m->prefs.pocket && mu->pocket_pc != 255 && n % 12 == mu->pocket_pc && n >= mu->W && n <= mu->W + 11)
        gfx_frame(fb, x, WY0, w, y1 - WY0, 2, p->c[T_FOCUS]);
}

void uf_draw_z4(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m, int kb_lo)
{
    const ui_music_t *mu = &m->music;
    gfx_hline(fb, 0, ZY, 640, p->c[T_LINE]);
    uf_glass(fb, p, 0, ZY + 1, 640, 143);

    /* finestre del voicing */
    bool win = windows_shown(m);
    if (win) {
        window(fb, p, kb_lo, mu->W, ZY + 6, T_TREBLE);
        window(fb, p, kb_lo, mu->WB, ZY + 12, T_BASS);
    }
    if (win && mu->single_notes) {               /* Full Octave: ottava delle note singole */
        int oct = mu->W - (mu->W % 12);
        int x0, w0, x1, w1;
        bool b0, b1;
        if (oct >= kb_lo && oct + 11 <= kb_lo + 47) {
            key_box(kb_lo, oct, &x0, &w0, &b0);
            key_box(kb_lo, oct + 11, &x1, &w1, &b1);
            gfx_hdots(fb, x0, ZY + 16, x1 + w1 - x0, 3, p->c[T_TREBLE]);
        }
    }

    /* prima i bianchi, poi i neri sopra */
    for (int pass = 0; pass < 2; pass++)
        for (int n = kb_lo; n < kb_lo + 48; n++)
            if (IS_BLACK[n % 12] == (pass == 1)) draw_key(fb, p, m, kb_lo, n, pass == 1);

    /* note fuori gamma */
    /* nel colore del ruolo (UI-150): il treble vince sul basso, il basso sul loop; 0 = nessuna */
    static const int TOK[3] = { T_TREBLE, T_BASS, T_LOOP };
    int below = 0, above = 0;
    for (int r = 2; r >= 0; r--)
        for (int n = 0; n < 128; n++) {
            bool on = r == 0 ? bit128(mu->live_treble, n) : r == 1 ? bit128(mu->live_bass, n)
                    : bit128(mu->loop_treble, n) || bit128(mu->loop_bass, n);
            if (!on) continue;
            if (n < kb_lo) below = TOK[r];
            if (n > kb_lo + 47) above = TOK[r];
        }
    if (below) gfx_text(fb, &GFX_S, 1, 300, "\xE2\x97\x80", p->c[below]);
    if (above) gfx_text(fb, &GFX_S, 630, 300, "\xE2\x96\xB6", p->c[above]);

    /* etichette delle ottave */
    if (m->prefs.note_labels != LBL_OFF) {
        static const char LET[7] = { 'C', 'D', 'E', 'F', 'G', 'A', 'B' };
        for (int i = 0; i < 28; i++) {
            int x = KX0 + KW * i;
            int n = kb_lo + (i / 7) * 12;
            if (i % 7 == 0) {
                char buf[8], o[4];
                ui_fmt_int(o, sizeof o, n / 12 - 1, 1);
                ui_fmt_cat(buf, sizeof buf, "C", o);
                gfx_text(fb, &GFX_S, x + 2, WY1 + 2, buf, p->c[n == 60 ? T_TEXT : T_DIM]);
            } else if (m->prefs.note_labels == LBL_ALL) {
                char l[2] = { LET[i % 7], 0 };
                gfx_text(fb, &GFX_XS, x + 7, WY1 + 4, l, p->c[T_GHOST]);
            }
        }
    }
}
