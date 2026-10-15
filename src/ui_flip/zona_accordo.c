/* zona_accordo.c — Z2, zona accordo (UI-145..UI-147).
 *
 * Il nome dell'accordo è scritto con Matrice, a punti come su un VFD: la parte dell'accordo nel
 * colore treble, il basso dopo la barra nel colore bass, così il nome si lega ai tasti accesi
 * della tastiera. Ogni lettera mostra anche i suoi punti spenti.
 * Nella vista Chord (quella di fabbrica) c'è solo ciò che si legge a un braccio di distanza:
 * tonalità, transpose e nome. Note, intervalli, finestre, Play Style e cartellino di Linneo
 * stanno nella vista Geek Out (UI-147).
 */
#include "uf_int.h"

/* note del modello, mai oltre UI_NOTES_MAX anche se n_notes lo supera */
static int uf_nn(const ui_music_t *mu) { return mu->n_notes < UI_NOTES_MAX ? mu->n_notes : UI_NOTES_MAX; }


#define ZW        416
#define NAME_X    12
#define NAME_MAXW 392

static const uf_name_scale_t SCALE[4] = { { 14, 10, 7 }, { 12, 8, 6 }, { 9, 6, 4 }, { 6, 4, 3 } };
#define NSCALE 4
/* linea di base del nome nella vista Chord: il nome sta al centro del vetrino (y 66..232) */
static int chord_base(int si) { return 149 + 7 * SCALE[si].p_root / 2; }

/* ---- nome a punti ---- */

static int part_w(const char *s, int pitch) { return s && s[0] ? gfx_matrix_w(s, pitch) : 0; }

int uf_name_w(const chord_label_t *c, const uf_name_scale_t *s)
{
    int w = part_w(c->root, s->p_root);
    if (c->acc[0]) w += s->p_root / 2 + part_w(c->acc, s->p_mid);
    if (c->quality[0]) w += s->p_mid + part_w(c->quality, s->p_mid);
    if (c->sup[0]) w += s->p_mid / 2 + part_w(c->sup, s->p_sup);
    if (c->slash_root[0]) {
        w += s->p_mid + part_w("/", s->p_mid) + s->p_mid + part_w(c->slash_root, s->p_mid);
        if (c->slash_acc[0]) w += s->p_mid / 2 + part_w(c->slash_acc, s->p_sup);
    }
    return w;
}

void uf_name_draw(gfx_fb16_t *fb, const uf_pal_t *p, int x, int base, const chord_label_t *c,
                  const uf_name_scale_t *s, int tok_main, int tok_bass, bool ghost_cells)
{
    gfx_dots_t dm = uf_dots(p, tok_main, ghost_cells), db = uf_dots(p, tok_bass, ghost_cells);
    int top = base - 7 * s->p_root;                      /* cima delle maiuscole della fondamentale */
    x = gfx_matrix(fb, x, base, s->p_root, c->root, &dm);
    if (c->acc[0]) x = gfx_matrix(fb, x + s->p_root / 2, top + 7 * s->p_mid, s->p_mid, c->acc, &dm);
    if (c->quality[0]) x = gfx_matrix(fb, x + s->p_mid, base, s->p_mid, c->quality, &dm);
    if (c->sup[0]) x = gfx_matrix(fb, x + s->p_mid / 2, top + 7 * s->p_sup, s->p_sup, c->sup, &dm);
    if (c->slash_root[0]) {
        x = gfx_matrix(fb, x + s->p_mid, base, s->p_mid, "/", &db);
        int btop = base - 7 * s->p_mid;
        x = gfx_matrix(fb, x + s->p_mid, base, s->p_mid, c->slash_root, &db);
        if (c->slash_acc[0]) gfx_matrix(fb, x + s->p_mid / 2, btop + 7 * s->p_sup, s->p_sup, c->slash_acc, &db);
    }
}

static int pick_scale(const chord_label_t *c, int maxw, int smin)
{
    for (int i = smin; i < NSCALE; i++)
        if (uf_name_w(c, &SCALE[i]) <= maxw) return i;
    return NSCALE - 1;
}

/* nota singola: l'ottava come apice, nel colore dim (UI-037) */
static chord_label_t single_label(const ui_music_t *mu)
{
    chord_label_t c = mu->chord;
    c.quality[0] = 0;
    c.slash_root[0] = 0;
    c.slash_acc[0] = 0;
    ui_fmt_int(c.sup, sizeof c.sup, mu->single_midi / 12 - 1, 1);
    return c;
}

static bool has_name(const ui_music_t *mu) { return mu->chord_state != CH_NONE && mu->chord.root[0]; }

/* Disegna il nome con la scala più grande (da smin in giù) che sta in maxw; base < 0 = quella della
 * vista Chord. Ritorna la larghezza disegnata. */
static int draw_name(gfx_fb16_t *fb, const uf_pal_t *p, const ui_music_t *mu, int x, int base, int maxw, int smin)
{
    if (!has_name(mu)) return 0;
    chord_label_t c = mu->single_note ? single_label(mu) : mu->chord;
    int si = pick_scale(&c, maxw, smin);
    if (base < 0) base = chord_base(si);
    bool ghost = mu->chord_state == CH_GHOST;
    int tm = ghost ? T_GHOST : T_TREBLE, tb = ghost ? T_GHOST : T_BASS;
    if (mu->single_note) {
        chord_label_t root = c;
        root.sup[0] = 0;
        uf_name_draw(fb, p, x, base, &root, &SCALE[si], tm, tb, true);
        int wr = uf_name_w(&root, &SCALE[si]);
        gfx_dots_t d = uf_dots(p, ghost ? T_GHOST : T_DIM, true);
        int top = base - 7 * SCALE[si].p_root;
        gfx_matrix(fb, x + wr + SCALE[si].p_mid / 2, top + 7 * SCALE[si].p_sup, SCALE[si].p_sup, c.sup, &d);
    } else {
        uf_name_draw(fb, p, x, base, &c, &SCALE[si], tm, tb, true);
    }
    return uf_name_w(&c, &SCALE[si]);
}

/* ---- tastiera di un'ottava con le classi ripiegate ---- */

static void octave_kb(gfx_fb16_t *fb, const uf_pal_t *p, const ui_music_t *mu, int x, int y, int w, int h)
{
    static const int8_t WHITE_PC[7] = { 0, 2, 4, 5, 7, 9, 11 };
    static const int8_t BLACK_AFTER[5] = { 0, 1, 3, 4, 5 };      /* bianco a sinistra di C♯ D♯ F♯ G♯ A♯ */
    static const int8_t BLACK_PC[5] = { 1, 3, 6, 8, 10 };
    int kw = w / 7;
    uint16_t treb = mu->pc_sounding, bass = 0;
    for (int n = 0; n < 128; n++)                       /* il basso che suona, come il treble: notes[] resta dopo il rilascio */
        if (mu->live_bass[n >> 5] >> (n & 31) & 1u) bass |= (uint16_t)(1u << (n % 12));
    for (int i = 0; i < 7; i++) {
        int pc = WHITE_PC[i];
        int kx = x + i * kw;
        bool t = treb >> pc & 1, b = bass >> pc & 1;
        gfx_c c = t ? p->c[T_TREBLE] : b ? p->c[T_BASS] : p->c[T_KBW];
        gfx_fill(fb, kx, y, kw - 2, h, c);
        if (t && b) gfx_fill(fb, kx + (kw - 2) / 2, y, (kw - 2) - (kw - 2) / 2, h, p->c[T_BASS]);
        if (mu->pc_in_key >> pc & 1) {
            gfx_c dc = (t || b) ? p->c[T_BG] : p->c[T_INKEY];
            gfx_disc(fb, (kx + (kw - 2) / 2) * GFX_SUB + GFX_SUB / 2, (y + h - 10) * GFX_SUB, 3 * GFX_SUB, dc);
        }
    }
    int bw = kw * 6 / 10, bh = h * 6 / 10;
    for (int i = 0; i < 5; i++) {
        int pc = BLACK_PC[i];
        int kx = x + (BLACK_AFTER[i] + 1) * kw - 1 - bw / 2;
        bool t = treb >> pc & 1, b = bass >> pc & 1;
        gfx_c c = t ? p->c[T_TREBLE] : b ? p->c[T_BASS] : p->c[T_KBB];
        gfx_fill(fb, kx - 1, y, bw + 2, bh + 1, p->c[T_BG]);
        gfx_fill(fb, kx, y, bw, bh, c);
        if (!t && !b) gfx_frame(fb, kx, y, bw, bh, 1, p->c[T_LINE]);
        if (mu->pc_in_key >> pc & 1) {
            gfx_c dc = (t || b) ? p->c[T_BG] : p->c[T_INKEY];
            gfx_disc(fb, (kx + bw / 2) * GFX_SUB + GFX_SUB / 2, (y + bh - 8) * GFX_SUB, 2 * GFX_SUB + 8, dc);
        }
    }
}

/* ---- note che suonano ---- */

static int note_row(gfx_fb16_t *fb, const uf_pal_t *p, const ui_music_t *mu, const gfx_face_t *f, int x, int y, int maxw)
{
    int cw = f->f->w;
    int x0 = x;
    bool any_bass = false, sep = false;
    for (int i = 0; i < uf_nn(mu); i++) if (mu->notes[i].role == ROLE_BASS) any_bass = true;
    for (int pass = 0; pass < 2; pass++) {
        for (int i = 0; i < uf_nn(mu); i++) {
            const ui_note_t *n = &mu->notes[i];
            if ((pass == 0) != (n->role == ROLE_BASS)) continue;
            if (pass == 1 && any_bass && !sep) {
                if (x - x0 + 2 * cw > maxw) return x;
                x = gfx_text(fb, f, x, y, ":", p->c[T_DIM]) + cw;
                sep = true;
            }
            int w = gfx_text_w(f, n->name, 0);
            if (x - x0 + w + cw > maxw) { gfx_text(fb, f, x, y, "\xE2\x80\xA6", p->c[T_DIM]); return x + cw; }
            x = gfx_text(fb, f, x, y, n->name, p->c[n->role == ROLE_BASS ? T_BASS : T_TREBLE]) + cw;
        }
    }
    return x;
}

/* modo tascabile: la classe scelta, da tenere d'occhio anche mentre si suona */
static void stick(gfx_fb16_t *fb, const uf_pal_t *p, const ui_music_t *mu, int xr, int y)
{
    static const char *const PC[12] = { "C", "C\xE2\x99\xAF", "D", "E\xE2\x99\xAD", "E", "F", "F\xE2\x99\xAF", "G",
                                        "A\xE2\x99\xAD", "A", "B\xE2\x99\xAD", "B" };
    char buf[16];
    ui_fmt_cat(buf, sizeof buf, "STICK ", PC[mu->pocket_pc % 12]);
    uf_label_right(fb, xr, y, buf, p->c[T_FOCUS]);
}

static void play_style(gfx_fb16_t *fb, const uf_pal_t *p, const ui_music_t *mu, bool pocket, int y)
{
    static const char *const W[3] = { "SIMPLE", "ADV", "FREE" };
    int xr = 404;
    int w = 0;
    for (int i = 0; i < 3; i++) w += uf_label_w(W[i]) + (i ? 6 : 0);
    int x = xr - w;
    for (int i = 0; i < 3; i++) {
        x = uf_label(fb, x, y, W[i], p->c[mu->play_style == i ? T_TEXT : T_SEGOFF]) + 6;
    }
    int xl = xr - w - 10;
    if (mu->secret_chords) xl = uf_label_right(fb, xl, y, "SECRET", p->c[T_ACTIVE]) - 8;
    if (pocket && mu->pocket_pc != 255) stick(fb, p, mu, xl, y);
}

/* ---- intervalli e nomi per Geek Out ---- */

static int letter_pc(char l)
{
    switch (l) {
    case 'C': return 0; case 'D': return 2; case 'E': return 4; case 'F': return 5;
    case 'G': return 7; case 'A': return 9; case 'B': return 11; default: return 0;
    }
}

static int acc_delta(const char *a)
{
    if (!a[0]) return 0;
    if (a[0] == 'x' && a[1] == 0) return 2;
    if ((unsigned char)a[0] == 0xE2 && (unsigned char)a[2] == 0xAD && (unsigned char)a[3] == 0xE2) return -2;   /* ♭♭ */
    if ((unsigned char)a[0] == 0xE2 && (unsigned char)a[2] == 0xAF) return 1;   /* ♯ */
    if ((unsigned char)a[0] == 0xE2 && (unsigned char)a[2] == 0xAD) return -1;  /* ♭ */
    return 0;
}

static void midi_name(char *buf, int n, int midi)
{
    static const char *const PC[12] = { "C", "C\xE2\x99\xAF", "D", "D\xE2\x99\xAF", "E", "F", "F\xE2\x99\xAF", "G",
                                        "G\xE2\x99\xAF", "A", "A\xE2\x99\xAF", "B" };
    char o[6];
    ui_fmt_int(o, sizeof o, midi / 12 - 1, 1);
    ui_fmt_cat(buf, n, PC[midi % 12], o);
}

static void geek_lines(gfx_fb16_t *fb, const uf_pal_t *p, const ui_music_t *mu, int y)
{
    static const char *const IV[12] = { "1", "\xE2\x99\xAD" "2", "2", "\xE2\x99\xAD" "3", "3", "4", "\xE2\x99\xAD" "5", "5",
                                        "\xE2\x99\xAF" "5", "6", "\xE2\x99\xAD" "7", "7" };
    int root = (letter_pc(mu->chord.root[0]) + acc_delta(mu->chord.acc) + 12) % 12;
    /* riga 1: note con l'ottava */
    note_row(fb, p, mu, &GFX_S, NAME_X, y, NAME_MAXW);
    /* riga 2: intervalli dalla fondamentale */
    char buf[64];
    buf[0] = 0;
    uint16_t seen = 0;
    for (int i = 0; i < uf_nn(mu); i++) {
        if (mu->notes[i].role == ROLE_BASS) continue;
        int iv = (mu->notes[i].midi % 12 - root + 12) % 12;
        if (seen >> iv & 1) continue;
        seen |= (uint16_t)(1u << iv);
    }
    for (int iv = 0; iv < 12; iv++) {
        if (!(seen >> iv & 1)) continue;
        if (buf[0]) ui_fmt_cat(buf, sizeof buf, buf, " ");
        ui_fmt_cat(buf, sizeof buf, buf, IV[iv]);
    }
    int x = gfx_text(fb, &GFX_S, NAME_X, y + 20, "INT", p->c[T_DIM]);
    gfx_text(fb, &GFX_S, x + 8, y + 20, buf, p->c[T_TEXT]);
    /* riga 3: finestre */
    char w1[12], w2[12], n1[8], n2[8], line[64];
    midi_name(n1, sizeof n1, mu->W);
    midi_name(n2, sizeof n2, mu->WB);
    ui_fmt_int(w1, sizeof w1, mu->W, 2);
    ui_fmt_int(w2, sizeof w2, mu->WB, 2);
    x = gfx_text(fb, &GFX_S, NAME_X, y + 40, "W", p->c[T_DIM]);
    ui_fmt_cat(line, sizeof line, w1, " ");
    ui_fmt_cat(line, sizeof line, line, n1);
    x = gfx_text(fb, &GFX_S, x + 8, y + 40, line, p->c[T_TREBLE]);
    x = gfx_text(fb, &GFX_S, x + 16, y + 40, "WB", p->c[T_DIM]);
    ui_fmt_cat(line, sizeof line, w2, " ");
    ui_fmt_cat(line, sizeof line, line, n2);
    x = gfx_text(fb, &GFX_S, x + 8, y + 40, line, p->c[T_BASS]);
    gfx_text(fb, &GFX_S, x + 16, y + 40, mu->single_notes ? "Octave" : "Split", p->c[T_DIM]);
}

/* cartellino di Linneo: la classe delle piante con quel numero di stami (una nota = uno stame) */
static void linnaeus(gfx_fb16_t *fb, const uf_pal_t *p, const ui_music_t *mu, int y, int xmin)
{
    if (!mu->n_notes || mu->chord_state == CH_NONE) return;
    const char *cls = ui_fmt_linnaeus(uf_pcs(mu));
    int lw = uf_label_w(cls) + 10;
    if (!cls[0] || 404 - lw < xmin) return;
    int tok = mu->chord_state == CH_GHOST ? T_GHOST : T_DIM;
    int x = 404 - lw;
    gfx_text(fb, &GFX_XS, x, y, "\xEE\x80\x80", p->c[tok]);
    uf_label(fb, x + 10, y, cls, p->c[tok]);
}

/* ---- oscilloscopio (vista React) ---- */

static void scope(gfx_fb16_t *fb, const uf_pal_t *p, const ui_meters_t *me)
{
    const int x0 = NAME_X, w = NAME_MAXW, yc = 150, amp = 64;
    gfx_hdots(fb, x0, yc, w, 4, p->c[T_LINE]);
    for (int i = 0; i <= 8; i++) gfx_vdots(fb, x0 + i * w / 8, yc - amp, 2 * amp + 1, 4, p->c[T_LINE]);
    if (!me->scope || me->scope_len < 2) return;
    uint32_t wr = me->scope_wr ? *me->scope_wr : 0;
    int prev = yc;
    for (int i = 0; i < w; i++) {
        int idx = (int)((wr + (uint32_t)me->scope_len - (uint32_t)w + (uint32_t)i) % me->scope_len);
        int y = yc - me->scope[idx] * amp / 32768;
        int a = prev < y ? prev : y, b = prev < y ? y : prev;
        gfx_fill(fb, x0 + i, a, 1, b - a + 1, p->c[T_TREBLE]);
        prev = y;
    }
}

/* ---- oscilloscopio di sfondo (vista Chord, UI-147b): la forma d'onda dietro il nome, nel colore
 * delle celle spente, agganciata a uno zero crossing in salita così l'immagine sta ferma ---- */

static void scope_bg(gfx_fb16_t *fb, const uf_pal_t *p, const ui_meters_t *me)
{
    const int x0 = NAME_X, w = NAME_MAXW, yc = 150, amp = 72;
    if (!me->scope || me->scope_len < (uint16_t)(w + 512)) return;
    uint32_t wr = me->scope_wr ? *me->scope_wr : 0, len = me->scope_len;
    /* trigger: l'ultimo zero crossing in salita fra 896 e 392 campioni fa, altrimenti la finestra più recente */
    uint32_t start = wr + len - (uint32_t)w - 512u;
    uint32_t best = wr + len - (uint32_t)w;
    for (uint32_t k = start + 1; k < wr + len - (uint32_t)w; k++) {
        int16_t a = me->scope[(k - 1) % len], b = me->scope[k % len];
        if (a < 0 && b >= 0) best = k;
    }
    gfx_c c = p->c[T_BAR];
    int prev = yc;
    for (int i = 0; i < w; i++) {
        int y = yc - me->scope[(best + (uint32_t)i) % len] * amp / 32768;
        int a = prev < y ? prev : y, b = prev < y ? y : prev;
        gfx_fill(fb, x0 + i, a, 1, b - a + 1, c);
        prev = y;
    }
}

/* ---- firma e disegno ---- */

uint64_t uf_sig_z2(const ui_model_t *m)
{
    uint64_t h = UF_H0;
    h = uf_h(h, &m->music, sizeof m->music);
    h = UF_HV(h, m->ctl.view);
    h = UF_HV(h, m->layer.prompt);
    h = UF_HV(h, m->prefs.pocket);
    h = UF_HV(h, m->prefs.linnaeus);
    h = UF_HV(h, m->tempo.drums_on);
    /* l'oscilloscopio si muove a 30 fotogrammi al secondo solo se c'è suono: a riposo la zona sta
     * ferma (UI-115, PLT-014); prima ridisegnava per sempre */
    if ((m->ctl.view == VIEW_REACT || m->ctl.view == VIEW_CHORD) && m->meters.scope &&
        (m->meters.peak[0] > 16 || m->meters.peak[1] > 16)) {
        uint32_t t = m->now_ms / 33u;
        h = UF_HV(h, t);
    }
    return h;
}

void uf_draw_z2(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m)
{
    const ui_music_t *mu = &m->music;
    gfx_hline(fb, 0, 24, ZW, p->c[T_LINE]);
    uf_glass(fb, p, 0, 25, ZW, 215);

    /* testata: tonalità e transpose (UI-145); con la Key mode spenta non si scrive nulla */
    if (m->ctl.view != VIEW_REACT) {
        if (mu->key_on) gfx_text(fb, &GFX_L, NAME_X, 30, mu->key_name, p->c[T_TEXT]);
        if (m->tempo.drums_on) {                             /* batteria a tastiera: lo stato vince sul transpose */
            gfx_text_right(fb, &GFX_L, 404, 30, "DRUMS", p->c[T_ACTIVE], 0);
        } else if (mu->transpose) {
            char t[8], buf[16];
            ui_fmt_signed(t, sizeof t, mu->transpose);
            ui_fmt_cat(buf, sizeof buf, "Trans ", t);
            gfx_text_right(fb, &GFX_L, 404, 30, buf, p->c[T_ACTIVE], 0);
        }
    } else if (m->tempo.drums_on) {
        gfx_text_right(fb, &GFX_L, 404, 30, "DRUMS", p->c[T_ACTIVE], 0);   /* anche in React */
    }

    if (m->layer.prompt == PROMPT_SELECT_KEY) {
        gfx_dots_t d = uf_dots(p, T_ACTIVE, true);
        int w = gfx_matrix_w("Select Key", 6);
        gfx_matrix(fb, ZW / 2 - w / 2, 170, 6, "Select Key", &d);
        return;
    }

    switch (m->ctl.view) {
    case VIEW_KEYBOARD:
        octave_kb(fb, p, mu, NAME_X, 72, NAME_MAXW, 156);
        break;
    case VIEW_CHORD_KB:
        draw_name(fb, p, mu, NAME_X, -1, 236, 1);
        octave_kb(fb, p, mu, 264, 76, 140, 152);
        break;
    case VIEW_NOTES: {
        draw_name(fb, p, mu, NAME_X, 116, NAME_MAXW, 3);
        int w = 0;
        for (int i = 0; i < uf_nn(mu); i++) w += gfx_text_w(&GFX_XXL, mu->notes[i].name, 0) + 32;
        const gfx_face_t *f = w - 32 <= NAME_MAXW ? &GFX_XXL : &GFX_L;
        int y = f == &GFX_XXL ? 140 : 160;
        w = 0;
        for (int i = 0; i < uf_nn(mu); i++) w += gfx_text_w(f, mu->notes[i].name, 0) + f->f->w;
        int x = ZW / 2 - (w - f->f->w) / 2;
        for (int i = 0; i < uf_nn(mu); i++)
            x = gfx_text(fb, f, x, y, mu->notes[i].name, p->c[mu->notes[i].role == ROLE_BASS ? T_BASS : T_TREBLE]) + f->f->w;
        break;
    }
    case VIEW_GEEK: {
        int nw = draw_name(fb, p, mu, NAME_X, 136, NAME_MAXW, 2);
        if (m->prefs.linnaeus) linnaeus(fb, p, mu, 74, NAME_X + nw + 16);
        geek_lines(fb, p, mu, 152);
        play_style(fb, p, mu, m->prefs.pocket, 220);
        break;
    }
    case VIEW_REACT: {
        scope(fb, p, &m->meters);
        if (has_name(mu)) {
            chord_label_t c = mu->single_note ? single_label(mu) : mu->chord;
            int w = uf_name_w(&c, &SCALE[3]);
            bool ghost = mu->chord_state == CH_GHOST;          /* UI-145: l'accordo fantasma tutto in ghost */
            uf_name_draw(fb, p, 404 - w, 74, &c, &SCALE[3], ghost ? T_GHOST : T_TREBLE, ghost ? T_GHOST : T_BASS, false);
        }
        break;
    }
    case VIEW_CHORD:
    default:
        /* vetrino: la forma d'onda in trasparenza, poi gli angoli a squadra attorno al nome */
        if (m->layer.prompt == PROMPT_NONE) scope_bg(fb, p, &m->meters);
        gfx_corners(fb, 4, 68, 408, 164, 9, 1, p->c[T_LINE]);
        draw_name(fb, p, mu, NAME_X + 4, -1, NAME_MAXW - 8, 0);
        if (m->prefs.pocket && mu->pocket_pc != 255) stick(fb, p, mu, 404, 222);
        break;
    }
}
