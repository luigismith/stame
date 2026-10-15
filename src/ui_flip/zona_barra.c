/* zona_barra.c — Z6, la banda in fondo alla plancia (UI-154..UI-156): una cosa sola alla volta.
 *
 * Il case porta i nomi dei controlli, lo schermo i valori. La banda mostra in grande il controllo
 * appena toccato, con l'etichetta del suo overlay (UI-065): è l'overlay dell'Orchid, che qui non
 * copre l'accordo. A riposo mostra il suono. Gli avvisi passano davanti a tutto. La legenda dei
 * tasti della Flip compare solo nella pagina dei comandi, l'unica che si usa con quei tasti.
 */
#include "uf_int.h"

#define BY 384          /* cima della banda */
#define VY 420          /* cima delle cifre e delle maiuscole del valore */

typedef struct { const char *key, *fn; } leg_t;

static const leg_t ROW_FLIP_PLAY[] = {
    { "L1 R1", "focus" }, { "\xE2\x9C\x9A", "turn" }, { "A", "press" }, { "B", "back" }, { "X", "push" },
    { "Y", "bs.voic" }, { "SEL", "opt" }, { "START", "bpm" }, { NULL, NULL }
};
static const leg_t ROW_FLIP_LIST[] = {
    { "\xE2\x9C\x9A\xE2\x96\xB2\xE2\x96\xBC", "scroll" }, { "A", "select" }, { "B", "back" }, { "MENU", "menu" },
    { NULL, NULL }
};

static void legend_row(gfx_fb16_t *fb, const uf_pal_t *p, int y, const leg_t *row)
{
    int w = 0;
    for (int i = 0; row[i].key; i++)
        w += gfx_text_w(&GFX_S, row[i].key, 0) + 4 + 4 + gfx_text_w(&GFX_S, row[i].fn, 0) + (row[i + 1].key ? 14 : 0);
    int x = 320 - w / 2;
    for (int i = 0; row[i].key; i++) {
        x = uf_keycap(fb, p, x, y, row[i].key);
        x = gfx_text(fb, &GFX_S, x + 4, y, row[i].fn, p->c[T_TEXT]);
        x += 14;
    }
}

static const ui_msg_t *top_msg(const ui_model_t *m, int level)
{
    if (m->msg_core.level == level) return &m->msg_core;
    if (m->msg_plat.level == level) return &m->msg_plat;
    return NULL;
}

uint64_t uf_sig_z6(const ui_model_t *m)
{
    uint64_t h = UF_H0;
    h = uf_h(h, &m->layer.ov.kind, 1);
    h = uf_h(h, &m->layer.ov.value, sizeof m->layer.ov.value);
    h = uf_h(h, &m->msg_core, sizeof m->msg_core);
    h = uf_h(h, &m->msg_plat, sizeof m->msg_plat);
    uint8_t v[8] = { m->layer.prompt, m->layer.list.open, (uint8_t)uf_controls(m), m->prefs.legend, m->prefs.theme,
                     m->music.key_on, (uint8_t)m->plat.battery_pct, m->plat.charging };
    h = uf_h(h, v, sizeof v);
    /* i valori dei controlli, senza lo stato dei tasti premuti (cambia a ogni pressione) */
    const size_t off = offsetof(ui_controls_t, focus);
    h = uf_h(h, (const uint8_t *)&m->ctl + off, sizeof m->ctl - off);
    /* tonalità e finestre contano solo per i loro overlay */
    uint8_t k = m->layer.ov.kind;
    if (k == OV_KEY || k == OV_KEY_TOGGLE) h = uf_h(h, m->music.key_name, sizeof m->music.key_name);
    if (k == OV_VOICING) h = UF_HV(h, m->music.W);
    if (k == OV_BASS_VOICING) h = UF_HV(h, m->music.WB);
    return h;
}

/* ---- evidenza: etichetta, valore grande, dettaglio ---- */

typedef struct {
    const char *label;      /* il nome inciso sul case */
    const char *digits;     /* cifre a sette segmenti, oppure NULL */
    const char *text;       /* testo a punti (Matrice), oppure NULL */
    const char *detail;     /* in piccolo, a destra dell'etichetta */
    int  gauge;             /* barra 0..1000, -1 = nessuna */
    bool negative;          /* funzione secondaria (premi e gira): banda in negativo */
    bool live;              /* controllo appena toccato: segno a sinistra, valore grande */
} hl_t;

static void hl(gfx_fb16_t *fb, const uf_pal_t *p, const hl_t *e)
{
    /* funzione secondaria: etichetta in negativo e valore in giallo, come il tasto tenuto premuto */
    int tok = e->negative ? T_ACTIVE : T_TEXT;
    gfx_c fg = p->c[tok], dim = p->c[T_DIM];
    gfx_dots_t dots = uf_dots(p, tok, false);       /* niente punti spenti: le parole lunghe diventano una griglia */
    gfx_seg_t seg = uf_seg(p, tok);
    if (e->live || e->negative) gfx_fill(fb, 0, BY + 1, 4, 95, p->c[T_ACTIVE]);
    char up[32];
    int n = 0;
    for (const char *s = e->label; *s && n < (int)sizeof up - 1; s++) up[n++] = (*s >= 'a' && *s <= 'z') ? (char)(*s - 32) : *s;
    up[n] = 0;
    if (e->negative) {
        int lw = gfx_text_w(&GFX_S, up, 1);
        gfx_fill(fb, 12, BY + 8, lw + 8, 20, p->c[T_ACTIVE]);
        gfx_text_ex(fb, &GFX_S, 16, BY + 10, up, p->c[T_BG], 1, 1);
    } else {
        gfx_text_ex(fb, &GFX_S, 16, BY + 10, up, dim, 1, 1);
    }
    if (e->detail) gfx_text_right(fb, &GFX_S, 624, BY + 10, e->detail, dim, 0);

    /* a riposo il valore sta un gradino sotto: quando si tocca un controllo, cresce */
    bool big = e->live || e->negative;
    int vy = big ? VY : VY + 8, dh = big ? 48 : 32, pmax = big ? 6 : 4;
    int x = 16;
    if (e->digits) x = gfx_seg7(fb, x, vy, dh, e->digits, &seg) + (big ? 20 : 14);
    if (e->text) {
        int room = 624 - x, pitch = 0;
        for (int pt = pmax; pt >= 3 && !pitch; pt--)
            if (gfx_matrix_w(e->text, pt) <= room) pitch = pt;
        if (pitch) x = gfx_matrix(fb, x, vy + 7 * pitch, pitch, e->text, &dots) + 20;
        else x = gfx_text_fit(fb, &GFX_L, x, vy, e->text, fg, room) + 20;
    }
    if (e->gauge >= 0 && x < 600) {
        int cells = (624 - x) / 8;
        int lit = (e->gauge * cells + 500) / 1000;
        uf_gauge(fb, x, VY + 12, 24, cells, 6, 2, lit, fg, p->c[T_SEGOFF]);
    }
}

static const char *pc_oct(char *buf, int n, int midi)
{
    static const char *const PC[12] = { "C", "C\xE2\x99\xAF", "D", "D\xE2\x99\xAF", "E", "F", "F\xE2\x99\xAF", "G",
                                        "G\xE2\x99\xAF", "A", "A\xE2\x99\xAF", "B" };
    char o[6];
    ui_fmt_int(o, sizeof o, midi / 12 - 1, 1);
    ui_fmt_cat(buf, n, PC[midi % 12], o);
    return buf;
}

static void sound(const ui_controls_t *c, char *d, int nd, char *t, int nt)
{
    char n[8];
    if (c->sound_user) { ui_fmt_int(n, sizeof n, c->sound_num, 2); ui_fmt_cat(d, nd, "U", n); }
    else ui_fmt_int(d, nd, c->sound_num, 2);
    ui_fmt_cat(t, nt, ui_fmt_engine(c->sound_engine), "  ");
    ui_fmt_cat(t, nt, t, c->sound_cat);
}

/* il contenuto di ogni overlay (UI-065), con le etichette della mascherina */
static void overlay(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m)
{
    const ui_overlay_t *ov = &m->layer.ov;
    const ui_controls_t *c = &m->ctl;
    char d[16], t[48];
    int v = ov->value;
    hl_t e = { "", NULL, NULL, NULL, -1, false, true };
    switch (ov->kind) {
    case OV_SOUND:
        sound(c, d, sizeof d, t, sizeof t);
        e.label = "Sound"; e.digits = d; e.text = c->sound_name; e.detail = t;
        break;
    case OV_PERFORM:
        if (v) ui_fmt_int(d, sizeof d, v, 2);
        e.label = ui_fmt_perf_short(c->perf_mode); e.digits = v ? d : NULL; e.text = v ? NULL : "OFF";
        break;
    case OV_ARP: {
        static const char *const DIR[3] = { "UP", "DOWN", "UP/DOWN" };
        ui_fmt_int(d, sizeof d, c->arp_rate, 2);
        e.label = "Arpeggiate"; e.digits = d; e.text = DIR[c->arp_dir % 3];
        break;
    }
    case OV_FX:
        if (v) ui_fmt_int(d, sizeof d, v, 2);
        e.label = ui_fmt_fx_name(c->fx_main_type); e.digits = v ? d : NULL; e.text = v ? NULL : "OFF";
        break;
    case OV_KEY: case OV_KEY_TOGGLE:
        e.label = "Key"; e.text = m->music.key_on ? m->music.key_name : "Off";
        break;
    case OV_TRANSPOSE:
        if (v) ui_fmt_signed(t, sizeof t, v); else ui_fmt_copy(t, sizeof t, "OFF");
        e.label = "Transpose"; e.text = t; e.negative = true;
        break;
    case OV_VOLUME:
        ui_fmt_int(d, sizeof d, v, 2);
        e.label = "Volume"; e.digits = d; e.gauge = v * 1000 / 99;
        break;
    case OV_BASS_VOLUME: case OV_BEAT_VOLUME:
        ui_fmt_int(d, sizeof d, v, 2);
        e.label = ov->kind == OV_BASS_VOLUME ? "Bass Volume" : "Beat Volume"; e.digits = d;
        e.gauge = v * 1000 / 99; e.negative = true;
        break;
    case OV_BPM:
        ui_fmt_int(d, sizeof d, v, 1);
        e.label = "BPM"; e.digits = d;
        break;
    case OV_BASS_SOUND:
        ui_fmt_int(d, sizeof d, v, 2);
        e.label = "Bass Sound"; e.digits = d; e.text = c->bass_name;
        break;
    case OV_BASS_TOGGLE:
        ui_fmt_int(d, sizeof d, c->bass_num, 2);
        e.label = c->bass_on ? "Bass Sound" : "Bass"; e.digits = c->bass_on ? d : NULL; e.text = c->bass_on ? c->bass_name : "OFF";
        break;
    case OV_VOICING:
        ui_fmt_int(d, sizeof d, v, 3);
        e.label = "Voicing"; e.digits = d; e.text = pc_oct(t, sizeof t, m->music.W);
        e.gauge = (v - 1) * 1000 / 59;
        break;
    case OV_BASS_VOICING:
        ui_fmt_int(d, sizeof d, v, 2);
        e.label = "Bass Voicing"; e.digits = d; e.text = pc_oct(t, sizeof t, m->music.WB);
        e.gauge = v * 1000 / 48;
        break;
    case OV_SINGLE_NOTES:
        e.label = "Single Notes"; e.text = v ? "Octave" : "Split";
        break;
    case OV_COUNT_IN:
        ui_fmt_int(d, sizeof d, v, 2);
        e.label = "Counting in"; e.digits = d;
        break;
    case OV_SAVED:
        ui_fmt_int(d, sizeof d, v, 2);
        ui_fmt_cat(t, sizeof t, "U", d);
        e.label = "Saved"; e.text = t;
        break;
    case OV_BATTERY: case OV_LOW_BATTERY:
        ui_fmt_int(d, sizeof d, m->plat.battery_pct, 2);
        e.label = ov->kind == OV_LOW_BATTERY ? "Low Battery" : "Battery"; e.digits = d; e.text = "%";
        e.detail = m->plat.charging ? "Charging" : "No cable detected";
        break;
    case OV_DRUMS:
        e.label = "Drums"; e.text = v ? "On" : "Off";
        break;
    default:
        return;
    }
    hl(fb, p, &e);
}

void uf_draw_z6(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m)
{
    gfx_hline(fb, 0, BY, 640, p->c[T_LINE]);
    uf_glass(fb, p, 0, BY + 1, 640, 95);

    const ui_msg_t *w = top_msg(m, MSG_WARN);
    if (w) {
        gfx_fill(fb, 0, BY + 1, 6, 95, p->c[T_WARN]);
        gfx_text(fb, &GFX_L, 20, BY + 32, "\xE2\x97\x8F", p->c[T_WARN]);
        gfx_text_fit(fb, &GFX_L, 48, BY + 32, w->text, p->c[T_WARN], 576);
        return;
    }
    if (m->layer.ov.kind != OV_NONE) { overlay(fb, p, m); return; }
    if (m->layer.prompt == PROMPT_SELECT_KEY) {
        gfx_text(fb, &GFX_L, 16, BY + 14, "Select Key", p->c[T_ACTIVE]);
        gfx_text(fb, &GFX_S, 16, BY + 56, "press a key (hold Min for minor)", p->c[T_TEXT]);
        return;
    }
    const ui_msg_t *info = top_msg(m, MSG_INFO);
    if (info) {
        gfx_text(fb, &GFX_L, 20, BY + 32, "\xE2\x97\x8B", p->c[T_DIM]);
        gfx_text_fit(fb, &GFX_L, 48, BY + 32, info->text, p->c[T_TEXT], 576);
        return;
    }
    if (uf_controls(m)) {
        if (m->prefs.legend) legend_row(fb, p, BY + 40, m->layer.list.open ? ROW_FLIP_LIST : ROW_FLIP_PLAY);
        return;
    }
    /* a riposo: il suono che si sta suonando */
    char d[16], t[48];
    sound(&m->ctl, d, sizeof d, t, sizeof t);
    hl_t e = { "Sound", d, m->ctl.sound_name, t, -1, false, false };
    hl(fb, p, &e);
}
