/* avvio.c — schermata d'avvio (UI-091, UI-159) e marchio di Stame.
 *
 * Il marchio: tre stami che salgono da un punto solo. Il filamento centrale è dritto, i due laterali
 * si aprono ad arco; ogni antera è un ovale inclinato come la testa di una nota. Tre stami, tre
 * note: una triade. All'avvio i filamenti crescono e le antere si accendono una alla volta, dalla
 * più bassa, come un arpeggio; poi si accende la scritta STAME, lettera per lettera.
 */
#include "uf_int.h"
#include <math.h>

typedef struct { float x, y; } pt_t;

static pt_t bez(pt_t a, pt_t b, pt_t c, pt_t d, float t)
{
    float u = 1.0f - t;
    float k0 = u * u * u, k1 = 3.0f * t * u * u, k2 = 3.0f * t * t * u, k3 = t * t * t;
    pt_t r = { k0 * a.x + k1 * b.x + k2 * c.x + k3 * d.x, k0 * a.y + k1 * b.y + k2 * c.y + k3 * d.y };
    return r;
}

static int32_t fx(float v) { return (int32_t)(v * (float)GFX_SUB); }

/* tratto lungo una curva fino alla frazione t */
static void stroke(gfx_fb16_t *fb, pt_t a, pt_t b, pt_t c, pt_t d, float t, float w, gfx_c col)
{
    const int N = 24;
    pt_t prev = a;
    for (int i = 1; i <= N; i++) {
        float ti = (float)i / (float)N;
        if (ti > t) ti = t;
        pt_t q = bez(a, b, c, d, ti);
        gfx_line(fb, fx(prev.x), fx(prev.y), fx(q.x), fx(q.y), fx(w), true, col);
        prev = q;
        if (ti >= t) break;
    }
}

void ui_flip_logo(gfx_fb16_t *fb, int cx, int cy, int size, gfx_c filament, gfx_c anther,
                  gfx_c anther_off, int grow, int anthers)
{
    float s = (float)size;
#define Q(u, v) ((pt_t){ (float)cx + ((u) - 0.5f) * s, (float)cy + ((v) - 0.5f) * s })
    pt_t base = Q(0.5f, 0.98f);
    float w = s * 0.035f;
    if (w < 2.0f) w = 2.0f;
    float t = (float)(grow < 0 ? 0 : grow > 256 ? 256 : grow) / 256.0f;

    /* ricettacolo */
    pt_t r0 = Q(0.30f, 0.98f), r1 = Q(0.70f, 0.98f);
    gfx_line(fb, fx(r0.x), fx(r0.y), fx(r1.x), fx(r1.y), fx(w), true, filament);

    /* filamenti: sinistro, centrale, destro */
    pt_t tip[3];
    tip[0] = Q(0.16f, 0.36f);
    tip[1] = Q(0.50f, 0.30f);
    tip[2] = Q(0.84f, 0.36f);
    if (t > 0.0f) {
        stroke(fb, base, Q(0.47f, 0.62f), Q(0.22f, 0.52f), tip[0], t, w, filament);
        stroke(fb, base, Q(0.50f, 0.75f), Q(0.50f, 0.50f), tip[1], t, w, filament);
        stroke(fb, base, Q(0.53f, 0.62f), Q(0.78f, 0.52f), tip[2], t, w, filament);
    }
    /* antere: ovali inclinati; accese nell'ordine sinistra, centro, destra */
    static const float ANG[3] = { -0.45f, 0.0f, 0.45f };
    for (int i = 0; i < 3; i++) {
        gfx_c c = i < anthers ? anther : anther_off;
        gfx_ellipse(fb, fx(tip[i].x), fx(tip[i].y - s * 0.10f), fx(s * 0.105f), fx(s * 0.17f), ANG[i], c);
    }
#undef Q
}

void uf_draw_boot(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m)
{
    uint32_t t = m->boot.t_ms;
    uf_glass(fb, p, 0, 0, UI_FLIP_W, UI_FLIP_H);
    gfx_corners(fb, 8, 8, 624, 464, 14, 1, p->c[T_LINE]);
    uf_label(fb, 20, 16, "TAB. I", p->c[T_DIM]);

    /* marchio: 0–800 ms crescono i filamenti, poi le antere a 800, 1000, 1200 ms */
    int grow = t >= 800 ? 256 : (int)(t * 256 / 800);
    int anth = t < 800 ? 0 : t < 1000 ? 1 : t < 1200 ? 2 : 3;
    ui_flip_logo(fb, 320, 150, 170, p->c[T_TREBLE], p->c[T_TREBLE], p->c[T_SEGOFF], grow, anth);

    /* STAME a punti: celle spente subito, lettere accese dai 1200 ms, una ogni 80 ms */
    const char *word = "STAME";
    int pitch = 9;
    int x = 320 - gfx_matrix_w(word, pitch) / 2;
    int lit = t < 1200 ? 0 : (int)((t - 1200) / 80) + 1;
    gfx_dots_t on = uf_dots(p, T_TEXT, true), off = uf_dots(p, T_TEXT, true);
    off.on = off.on_edge = p->c[T_SEGOFF];
    for (int i = 0; i < 5; i++) {
        char ch[2] = { word[i], 0 };
        x = gfx_matrix(fb, x, 318, pitch, ch, i < lit ? &on : &off) + pitch;
    }
    if (t >= 1600) {
        const char *sub = "STAMEN HARMONICUM \xC2\xB7 TRIANDRIA";
        gfx_text_center(fb, &GFX_XS, 320, 334, sub, p->c[T_DIM], 2);
    }

    /* righe dell'inizializzazione e versione */
    for (int i = 0; i < 3; i++)
        if (m->boot.line[i][0]) gfx_text(fb, &GFX_S, 24, 394 + i * 20, m->boot.line[i], p->c[T_DIM]);
    if (m->boot.version[0]) gfx_text_right(fb, &GFX_S, 616, 434, m->boot.version, p->c[T_DIM], 0);
}
