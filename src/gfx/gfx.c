/* gfx.c — primitive di disegno su framebuffer RGB565 (gfx.h). */
#include "gfx.h"
#include <math.h>

uint32_t gfx_mix(uint32_t a, uint32_t b, int t)
{
    if (t <= 0) return a & 0xFFFFFFu;
    if (t >= 256) return b & 0xFFFFFFu;
    uint32_t r = 0;
    for (int sh = 0; sh <= 16; sh += 8) {
        int ca = (int)((a >> sh) & 0xFFu), cb = (int)((b >> sh) & 0xFFu);
        int c = ca + ((cb - ca) * t + (cb >= ca ? 128 : -128)) / 256;
        if (c < 0) c = 0;
        if (c > 255) c = 255;
        r |= (uint32_t)c << sh;
    }
    return r;
}

void gfx_fb_init(gfx_fb16_t *fb, uint16_t *px, int w, int h, int stride)
{
    fb->px = px;
    fb->w = (uint16_t)w;
    fb->h = (uint16_t)h;
    fb->stride = (uint16_t)stride;
    gfx_clip_all(fb);
}

void gfx_clip_all(gfx_fb16_t *fb)
{
    fb->clip.x = 0;
    fb->clip.y = 0;
    fb->clip.w = (int16_t)fb->w;
    fb->clip.h = (int16_t)fb->h;
}

void gfx_clip(gfx_fb16_t *fb, int x, int y, int w, int h)
{
    int x0 = x < 0 ? 0 : x, y0 = y < 0 ? 0 : y;
    int x1 = x + w > fb->w ? fb->w : x + w, y1 = y + h > fb->h ? fb->h : y + h;
    if (x1 < x0) x1 = x0;
    if (y1 < y0) y1 = y0;
    fb->clip.x = (int16_t)x0;
    fb->clip.y = (int16_t)y0;
    fb->clip.w = (int16_t)(x1 - x0);
    fb->clip.h = (int16_t)(y1 - y0);
}

/* ---- rettangoli e linee ---- */

void gfx_fill(gfx_fb16_t *fb, int x, int y, int w, int h, gfx_c c)
{
    int cx0 = fb->clip.x, cy0 = fb->clip.y, cx1 = cx0 + fb->clip.w, cy1 = cy0 + fb->clip.h;
    int x0 = x < cx0 ? cx0 : x, y0 = y < cy0 ? cy0 : y;
    int x1 = x + w > cx1 ? cx1 : x + w, y1 = y + h > cy1 ? cy1 : y + h;
    if (x0 >= x1 || y0 >= y1) return;
    for (int yy = y0; yy < y1; yy++) {
        uint16_t *p = fb->px + (size_t)yy * fb->stride + x0;
        for (int xx = x0; xx < x1; xx++) *p++ = c;
    }
}

void gfx_pixel(gfx_fb16_t *fb, int x, int y, gfx_c c)
{
    if (x < fb->clip.x || y < fb->clip.y || x >= fb->clip.x + fb->clip.w || y >= fb->clip.y + fb->clip.h)
        return;
    fb->px[(size_t)y * fb->stride + x] = c;
}

void gfx_hline(gfx_fb16_t *fb, int x, int y, int w, gfx_c c) { gfx_fill(fb, x, y, w, 1, c); }
void gfx_vline(gfx_fb16_t *fb, int x, int y, int h, gfx_c c) { gfx_fill(fb, x, y, 1, h, c); }

void gfx_frame(gfx_fb16_t *fb, int x, int y, int w, int h, int t, gfx_c c)
{
    if (w <= 0 || h <= 0 || t <= 0) return;
    if (2 * t >= w || 2 * t >= h) { gfx_fill(fb, x, y, w, h, c); return; }
    gfx_fill(fb, x, y, w, t, c);
    gfx_fill(fb, x, y + h - t, w, t, c);
    gfx_fill(fb, x, y + t, t, h - 2 * t, c);
    gfx_fill(fb, x + w - t, y + t, t, h - 2 * t, c);
}

void gfx_hdots(gfx_fb16_t *fb, int x, int y, int w, int step, gfx_c c)
{
    if (step < 1) step = 1;
    for (int i = 0; i < w; i += step) gfx_pixel(fb, x + i, y, c);
}

void gfx_vdots(gfx_fb16_t *fb, int x, int y, int h, int step, gfx_c c)
{
    if (step < 1) step = 1;
    for (int i = 0; i < h; i += step) gfx_pixel(fb, x, y + i, c);
}

void gfx_mesh(gfx_fb16_t *fb, int x, int y, int w, int h, int step, gfx_c bg, gfx_c mesh)
{
    gfx_fill(fb, x, y, w, h, bg);
    if (step < 2 || bg == mesh) return;
    int cx0 = fb->clip.x, cy0 = fb->clip.y, cx1 = cx0 + fb->clip.w, cy1 = cy0 + fb->clip.h;
    int x0 = x < cx0 ? cx0 : x, y0 = y < cy0 ? cy0 : y;
    int x1 = x + w > cx1 ? cx1 : x + w, y1 = y + h > cy1 ? cy1 : y + h;
    for (int yy = y0; yy < y1; yy++) {
        if (yy % step) continue;
        int off = ((yy / step) & 1) ? step / 2 : 0;          /* righe sfalsate: maglia esagonale */
        int first = x0 + ((off - x0) % step + step) % step;
        uint16_t *row = fb->px + (size_t)yy * fb->stride;
        for (int xx = first; xx < x1; xx += step) row[xx] = mesh;
    }
}

void gfx_corners(gfx_fb16_t *fb, int x, int y, int w, int h, int l, int t, gfx_c c)
{
    gfx_fill(fb, x, y, l, t, c);
    gfx_fill(fb, x, y, t, l, c);
    gfx_fill(fb, x + w - l, y, l, t, c);
    gfx_fill(fb, x + w - t, y, t, l, c);
    gfx_fill(fb, x, y + h - t, l, t, c);
    gfx_fill(fb, x, y + h - l, t, l, c);
    gfx_fill(fb, x + w - l, y + h - t, l, t, c);
    gfx_fill(fb, x + w - t, y + h - l, t, l, c);
}

/* ---- forme geometriche ---- */

static int ceil_div16(int32_t v)            /* ceil(v / 16) per v con segno */
{
    return v >= 0 ? (int)((v + 15) / 16) : -(int)((-v) / 16);
}

static void span(gfx_fb16_t *fb, int y, int xa, int xb, gfx_c c)   /* pixel xa..xb-1 */
{
    if (xb > xa) gfx_fill(fb, xa, y, xb - xa, 1, c);
}

void gfx_poly(gfx_fb16_t *fb, const int32_t *xy, int n, gfx_c c)
{
    if (n < 3 || n > 32) return;
    int32_t ymin = xy[1], ymax = xy[1];
    for (int i = 1; i < n; i++) {
        if (xy[2 * i + 1] < ymin) ymin = xy[2 * i + 1];
        if (xy[2 * i + 1] > ymax) ymax = xy[2 * i + 1];
    }
    int py0 = ceil_div16(ymin - 8), py1 = ceil_div16(ymax - 8);
    if (py0 < fb->clip.y) py0 = fb->clip.y;
    if (py1 > fb->clip.y + fb->clip.h) py1 = fb->clip.y + fb->clip.h;
    for (int py = py0; py < py1; py++) {
        int32_t yc = py * GFX_SUB + GFX_SUB / 2;
        int32_t xs[32];
        int k = 0;
        for (int i = 0; i < n; i++) {
            int32_t x1 = xy[2 * i], y1 = xy[2 * i + 1];
            int32_t x2 = xy[2 * ((i + 1) % n)], y2 = xy[2 * ((i + 1) % n) + 1];
            if (y1 == y2) continue;
            if ((yc >= y1 && yc < y2) || (yc >= y2 && yc < y1)) {
                int64_t num = (int64_t)(yc - y1) * (x2 - x1);
                xs[k++] = x1 + (int32_t)(num / (y2 - y1));
            }
        }
        for (int i = 1; i < k; i++) {                 /* ordinamento per inserzione: k è piccolo */
            int32_t v = xs[i];
            int j = i - 1;
            while (j >= 0 && xs[j] > v) { xs[j + 1] = xs[j]; j--; }
            xs[j + 1] = v;
        }
        for (int i = 0; i + 1 < k; i += 2)
            span(fb, py, ceil_div16(xs[i] - 8), ceil_div16(xs[i + 1] - 8), c);
    }
}

void gfx_disc(gfx_fb16_t *fb, int32_t cx, int32_t cy, int32_t r, gfx_c c)
{
    if (r <= 0) return;
    int py0 = ceil_div16(cy - r - 8), py1 = ceil_div16(cy + r - 8);
    for (int py = py0; py < py1; py++) {
        float dy = (float)(py * GFX_SUB + GFX_SUB / 2 - cy);
        float q = (float)r * (float)r - dy * dy;
        if (q < 0.0f) continue;
        int32_t hw = (int32_t)sqrtf(q);
        span(fb, py, ceil_div16(cx - hw - 8), ceil_div16(cx + hw - 8 + 1), c);
    }
}

void gfx_ring(gfx_fb16_t *fb, int32_t cx, int32_t cy, int32_t r, int32_t t, gfx_c c)
{
    if (r <= 0 || t <= 0) return;
    int32_t ri = r - t;
    int py0 = ceil_div16(cy - r - 8), py1 = ceil_div16(cy + r - 8);
    for (int py = py0; py < py1; py++) {
        float dy = (float)(py * GFX_SUB + GFX_SUB / 2 - cy);
        float q = (float)r * (float)r - dy * dy;
        if (q < 0.0f) continue;
        int32_t hw = (int32_t)sqrtf(q);
        int xa = ceil_div16(cx - hw - 8), xb = ceil_div16(cx + hw - 8 + 1);
        float qi = ri > 0 ? (float)ri * (float)ri - dy * dy : -1.0f;
        if (qi <= 0.0f) { span(fb, py, xa, xb, c); continue; }
        int32_t hi = (int32_t)sqrtf(qi);
        int ia = ceil_div16(cx - hi - 8), ib = ceil_div16(cx + hi - 8 + 1);
        span(fb, py, xa, ia, c);
        span(fb, py, ib, xb, c);
    }
}

void gfx_ellipse(gfx_fb16_t *fb, int32_t cx, int32_t cy, int32_t rx, int32_t ry, float ang, gfx_c c)
{
    if (rx <= 0 || ry <= 0) return;
    float cs = cosf(ang), sn = sinf(ang);
    float irx2 = 1.0f / ((float)rx * (float)rx), iry2 = 1.0f / ((float)ry * (float)ry);
    float A = cs * cs * irx2 + sn * sn * iry2;
    int32_t rmax = rx > ry ? rx : ry;
    int py0 = ceil_div16(cy - rmax - 8), py1 = ceil_div16(cy + rmax - 8);
    for (int py = py0; py < py1; py++) {
        float dy = (float)(py * GFX_SUB + GFX_SUB / 2 - cy);
        float B = 2.0f * dy * cs * sn * (irx2 - iry2);
        float C = dy * dy * (sn * sn * irx2 + cs * cs * iry2) - 1.0f;
        float disc = B * B - 4.0f * A * C;
        if (disc < 0.0f) continue;
        float sq = sqrtf(disc);
        float x0 = (-B - sq) / (2.0f * A), x1 = (-B + sq) / (2.0f * A);
        span(fb, py, ceil_div16(cx + (int32_t)x0 - 8), ceil_div16(cx + (int32_t)x1 - 8 + 1), c);
    }
}

void gfx_line(gfx_fb16_t *fb, int32_t x0, int32_t y0, int32_t x1, int32_t y1, int32_t w, bool round, gfx_c c)
{
    float dx = (float)(x1 - x0), dy = (float)(y1 - y0);
    float len = sqrtf(dx * dx + dy * dy);
    if (len < 1.0f) { gfx_disc(fb, x0, y0, w / 2, c); return; }
    float nx = -dy / len * (float)w * 0.5f, ny = dx / len * (float)w * 0.5f;
    int32_t pts[8] = {
        x0 + (int32_t)nx, y0 + (int32_t)ny, x1 + (int32_t)nx, y1 + (int32_t)ny,
        x1 - (int32_t)nx, y1 - (int32_t)ny, x0 - (int32_t)nx, y0 - (int32_t)ny
    };
    gfx_poly(fb, pts, 4, c);
    if (round) {
        gfx_disc(fb, x0, y0, w / 2, c);
        gfx_disc(fb, x1, y1, w / 2, c);
    }
}

/* ---- font ---- */

const uint8_t *gfx_font_glyph(const gfx_font_t *f, uint32_t cp)
{
    if (!f || cp > 0xFFFFu) return NULL;
    int lo = 0, hi = (int)f->n - 1;
    while (lo <= hi) {
        int mid = (lo + hi) / 2;
        if (f->cp[mid] == cp) return f->bits + (size_t)mid * f->h * f->bpr;
        if (f->cp[mid] < cp) lo = mid + 1; else hi = mid - 1;
    }
    return NULL;
}

const gfx_mglyph_t *gfx_mfont_glyph(const gfx_mfont_t *f, uint32_t cp)
{
    if (!f || cp > 0xFFFFu) return NULL;
    int lo = 0, hi = (int)f->n - 1;
    while (lo <= hi) {
        int mid = (lo + hi) / 2;
        if (f->cp[mid] == cp) return &f->g[mid];
        if (f->cp[mid] < cp) lo = mid + 1; else hi = mid - 1;
    }
    return NULL;
}

const gfx_face_t GFX_XS  = { &GFX_FONT_6X12,  &GFX_SIMB_6X12 };
const gfx_face_t GFX_S   = { &GFX_FONT_8X16,  &GFX_SIMB_8X16 };
const gfx_face_t GFX_M   = { &GFX_FONT_12X24, &GFX_SIMB_12X24 };
const gfx_face_t GFX_L   = { &GFX_FONT_16X32, &GFX_SIMB_16X32 };
const gfx_face_t GFX_XXL = { &GFX_FONT_32X64, &GFX_SIMB_32X64 };

uint32_t gfx_utf8(const char **s)
{
    const uint8_t *p = (const uint8_t *)*s;
    uint32_t c = p[0];
    if (c == 0) return 0;
    int n = c < 0x80 ? 0 : (c & 0xE0) == 0xC0 ? 1 : (c & 0xF0) == 0xE0 ? 2 : (c & 0xF8) == 0xF0 ? 3 : -1;
    if (n < 0) { *s += 1; return '?'; }
    if (n == 0) { *s += 1; return c; }
    c &= 0x3Fu >> n;
    for (int i = 1; i <= n; i++) {
        if ((p[i] & 0xC0) != 0x80) { *s += i; return '?'; }
        c = (c << 6) | (p[i] & 0x3Fu);
    }
    *s += n + 1;
    return c;
}

int gfx_text_len(const char *s)
{
    int n = 0;
    while (gfx_utf8(&s)) n++;
    return n;
}

int gfx_text_w(const gfx_face_t *f, const char *s, int extra)
{
    int n = gfx_text_len(s);
    return n ? n * (f->f->w + extra) - extra : 0;
}

static void glyph(gfx_fb16_t *fb, const gfx_face_t *f, int x, int y, uint32_t cp, gfx_c fg, int scale)
{
    const gfx_font_t *font = f->f;
    const uint8_t *g = gfx_font_glyph(font, cp);
    if (!g && f->sym) { g = gfx_font_glyph(f->sym, cp); if (g) font = f->sym; }
    if (!g) { g = gfx_font_glyph(f->f, '?'); font = f->f; }
    if (!g) return;
    int w = font->w, h = font->h, bpr = font->bpr;
    int cx0 = fb->clip.x, cy0 = fb->clip.y, cx1 = cx0 + fb->clip.w, cy1 = cy0 + fb->clip.h;
    bool inside = x >= cx0 && y >= cy0 && x + w * scale <= cx1 && y + h * scale <= cy1;
    for (int r = 0; r < h; r++) {
        const uint8_t *row = g + r * bpr;
        for (int col = 0; col < w; col++) {
            if (!(row[col >> 3] & (0x80u >> (col & 7)))) continue;
            if (scale == 1) {
                if (inside) fb->px[(size_t)(y + r) * fb->stride + x + col] = fg;
                else gfx_pixel(fb, x + col, y + r, fg);
            } else {
                gfx_fill(fb, x + col * scale, y + r * scale, scale, scale, fg);
            }
        }
    }
}

int gfx_text_ex(gfx_fb16_t *fb, const gfx_face_t *f, int x, int y, const char *s, gfx_c fg,
                int extra, int scale)
{
    if (scale < 1) scale = 1;
    int adv = f->f->w * scale + extra;
    uint32_t cp;
    bool first = true;
    while ((cp = gfx_utf8(&s)) != 0) {
        if (!first) x += extra;
        first = false;
        if (cp != ' ') glyph(fb, f, x, y, cp, fg, scale);
        x += adv - extra;
    }
    return x;
}

int gfx_text_fit(gfx_fb16_t *fb, const gfx_face_t *f, int x, int y, const char *s, gfx_c fg, int max_w)
{
    int cw = f->f->w;
    int n = gfx_text_len(s);
    if (n * cw <= max_w) return gfx_text(fb, f, x, y, s, fg);
    int keep = max_w / cw - 1;
    if (keep < 0) return x;
    for (int i = 0; i < keep; i++) {
        uint32_t cp = gfx_utf8(&s);
        if (cp != ' ') glyph(fb, f, x, y, cp, fg, 1);
        x += cw;
    }
    glyph(fb, f, x, y, 0x2026, fg, 1);
    return x + cw;
}

int gfx_text_right(gfx_fb16_t *fb, const gfx_face_t *f, int x_right, int y, const char *s, gfx_c fg, int extra)
{
    return gfx_text_ex(fb, f, x_right - gfx_text_w(f, s, extra), y, s, fg, extra, 1);
}

int gfx_text_center(gfx_fb16_t *fb, const gfx_face_t *f, int x_mid, int y, const char *s, gfx_c fg, int extra)
{
    return gfx_text_ex(fb, f, x_mid - gfx_text_w(f, s, extra) / 2, y, s, fg, extra, 1);
}

/* ---- Matrice ---- */

#define DOT_MAX 32

typedef struct { int d, off; int8_t lo[DOT_MAX], hi[DOT_MAX], ilo[DOT_MAX], ihi[DOT_MAX]; } dotshape_t;

static void circle_spans(int d, int8_t *lo, int8_t *hi)
{
    float R = (float)d * 0.5f;
    for (int r = 0; r < d; r++) {
        float dy = (float)r + 0.5f - R;
        float q = R * R - dy * dy;
        float hw = q > 0.0f ? sqrtf(q) : 0.0f;
        int a = (int)floorf(R - hw + 0.5f), b = (int)floorf(R + hw + 0.5f);
        if (b <= a) { a = (int)R; b = a + 1; }
        lo[r] = (int8_t)a;
        hi[r] = (int8_t)b;
    }
}

static void dot_shape(int pitch, dotshape_t *s)
{
    int gap = pitch >= 8 ? pitch / 4 : (pitch >= 4 ? 1 : 0);
    int d = pitch - gap;
    if (d > DOT_MAX) d = DOT_MAX;
    if (d < 1) d = 1;
    s->d = d;
    s->off = gap / 2;
    if (d >= 5) {
        circle_spans(d, s->lo, s->hi);
        int8_t lo2[DOT_MAX], hi2[DOT_MAX];
        circle_spans(d - 2, lo2, hi2);
        for (int r = 0; r < d; r++) { s->ilo[r] = 0; s->ihi[r] = 0; }
        for (int r = 0; r < d - 2; r++) { s->ilo[r + 1] = (int8_t)(lo2[r] + 1); s->ihi[r + 1] = (int8_t)(hi2[r] + 1); }
    } else {
        for (int r = 0; r < d; r++) { s->lo[r] = 0; s->hi[r] = (int8_t)d; s->ilo[r] = 0; s->ihi[r] = (int8_t)d; }
        if (d >= 3) {                                  /* angoli smussati con il colore del bordo */
            s->ilo[0] = 1; s->ihi[0] = (int8_t)(d - 1);
            s->ilo[d - 1] = 1; s->ihi[d - 1] = (int8_t)(d - 1);
        }
    }
}

static void dot(gfx_fb16_t *fb, int x, int y, const dotshape_t *s, gfx_c edge, gfx_c core)
{
    for (int r = 0; r < s->d; r++) {
        int yy = y + s->off + r, xx = x + s->off;
        span(fb, yy, xx + s->lo[r], xx + s->hi[r], edge);
        if (core != edge) span(fb, yy, xx + s->ilo[r], xx + s->ihi[r], core);
    }
}

int gfx_matrix_w(const char *s, int pitch)
{
    int cols = 0, n = 0;
    uint32_t cp;
    while ((cp = gfx_utf8(&s)) != 0) {
        const gfx_mglyph_t *g = gfx_mfont_glyph(&GFX_MATRICE, cp);
        if (!g) g = gfx_mfont_glyph(&GFX_MATRICE, '?');
        cols += g ? g->w : 5;
        n++;
    }
    return n ? (cols + n - 1) * pitch : 0;
}

int gfx_matrix(gfx_fb16_t *fb, int x, int base, int pitch, const char *s, const gfx_dots_t *d)
{
    dotshape_t sh;
    dot_shape(pitch, &sh);
    uint32_t cp;
    bool first = true;
    while ((cp = gfx_utf8(&s)) != 0) {
        const gfx_mglyph_t *g = gfx_mfont_glyph(&GFX_MATRICE, cp);
        if (!g) g = gfx_mfont_glyph(&GFX_MATRICE, '?');
        if (!g) continue;
        if (!first) x += pitch;
        first = false;
        for (int r = 0; r < 9; r++) {
            int y = base + (r - 7) * pitch;
            for (int c = 0; c < g->w; c++) {
                bool on = (g->r[r] >> (g->w - 1 - c)) & 1u;
                if (on) dot(fb, x + c * pitch, y, &sh, d->on_edge, d->on);
                else if (d->ghost && r < 7 && cp != ' ') dot(fb, x + c * pitch, y, &sh, d->off, d->off);
            }
        }
        x += g->w * pitch;
    }
    return x;
}

/* ---- sette segmenti ---- */

static uint8_t seg_mask(char ch)
{
    static const uint8_t DIG[10] STAME_ROM = { 0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F };
    if (ch >= '0' && ch <= '9') return DIG[ch - '0'];
    switch (ch) {
    case '-': return 0x40;
    case 'A': return 0x77;
    case 'b': return 0x7C;
    case 'C': return 0x39;
    case 'd': return 0x5E;
    case 'E': return 0x79;
    case 'F': return 0x71;
    case 'H': return 0x76;
    case 'L': return 0x38;
    case 'n': return 0x54;
    case 'o': return 0x5C;
    case 'P': return 0x73;
    case 'r': return 0x50;
    case 't': return 0x78;
    case 'U': return 0x3E;
    case 'u': return 0x1C;
    case 'y': return 0x6E;
    default:  return 0;
    }
}

typedef struct { int w, t, g, adv, narrow; } seg_geo_t;

static seg_geo_t seg_geo(int h)
{
    seg_geo_t q;
    q.w = (h * 9 + 8) / 16;
    q.t = (h + 4) / 8;
    if (q.t < 2) q.t = 2;
    q.g = q.t / 3 < 1 ? 1 : q.t / 3;
    q.adv = q.w + (h / 6 < 3 ? 3 : h / 6);
    q.narrow = q.t * 2 + 2;
    return q;
}

int gfx_seg7_w(int h, const char *s)
{
    seg_geo_t q = seg_geo(h);
    int w = 0;
    for (; *s; s++) w += (*s == ':' || *s == '.') ? q.narrow : q.adv;
    return w > 0 ? w - (q.adv - q.w) : 0;
}

/* esagono di un segmento in coordinate locali (sedicesimi), con l'inclinazione */
static void seg_poly(gfx_fb16_t *fb, int ox, int oy, int h, const float *p, gfx_c c)
{
    int32_t xy[12];
    const float slant = 1.0f / 12.0f;
    for (int i = 0; i < 6; i++) {
        float x = p[2 * i], y = p[2 * i + 1];
        x += ((float)h - y) * slant;
        xy[2 * i] = (int32_t)((float)ox * GFX_SUB + x * GFX_SUB);
        xy[2 * i + 1] = (int32_t)((float)oy * GFX_SUB + y * GFX_SUB);
    }
    gfx_poly(fb, xy, 6, c);
}

static void seg_digit(gfx_fb16_t *fb, int x, int y, int h, const seg_geo_t *q, uint8_t mask, gfx_c c)
{
    float w = (float)q->w, t = (float)q->t, g = (float)q->g, m = (float)h * 0.5f, H = (float)h;
    for (int s = 0; s < 7; s++) {
        if (!(mask & (1u << s))) continue;
        float p[12];
        if (s == 0 || s == 6 || s == 3) {                       /* a, g, d */
            float y0 = s == 0 ? 0.0f : s == 6 ? m - t * 0.5f : H - t;
            float v[12] = { g + t * 0.5f, y0 + t * 0.5f, g + t, y0, w - g - t, y0,
                            w - g - t * 0.5f, y0 + t * 0.5f, w - g - t, y0 + t, g + t, y0 + t };
            memcpy(p, v, sizeof v);
        } else {                                                /* b, c, e, f */
            float x0 = (s == 1 || s == 2) ? w - t : 0.0f;
            float ya = (s == 1 || s == 5) ? 0.0f : m, yb = (s == 1 || s == 5) ? m : H;
            float v[12] = { x0 + t * 0.5f, ya + g + t * 0.5f, x0 + t, ya + g + t, x0 + t, yb - g - t,
                            x0 + t * 0.5f, yb - g - t * 0.5f, x0, yb - g - t, x0, ya + g + t };
            memcpy(p, v, sizeof v);
        }
        seg_poly(fb, x, y, h, p, c);
    }
}

int gfx_seg7(gfx_fb16_t *fb, int x, int y, int h, const char *s, const gfx_seg_t *c)
{
    seg_geo_t q = seg_geo(h);
    for (; *s; s++) {
        if (*s == ':' || *s == '.') {
            int sz = q.t;
            int cx = x + (q.narrow - sz) / 2;
            if (*s == ':') {
                gfx_fill(fb, cx + h / 24, y + h / 3 - sz / 2, sz, sz, c->on);
                gfx_fill(fb, cx, y + (2 * h) / 3 - sz / 2, sz, sz, c->on);
            } else {
                gfx_fill(fb, cx, y + h - sz, sz, sz, c->on);
            }
            x += q.narrow;
            continue;
        }
        if (c->ghost) seg_digit(fb, x, y, h, &q, 0x7F, c->off);
        uint8_t m = seg_mask(*s);
        if (m) seg_digit(fb, x, y, h, &q, m, c->on);
        x += q.adv;
    }
    return x - (q.adv - q.w);
}
