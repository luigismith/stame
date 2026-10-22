/* zona_comandi.c — Z5: le 11 celle dei controlli (UI-151..UI-153) e le liste (UI-157).
 *
 * Ogni cella è un modulo di strumento: titolo stampato sul vetro, valore acceso, dettaglio e
 * legenda dei comandi. Volume e voicing hanno una barra a celle sotto il valore.
 */
#include "uf_int.h"

static const char *const TITLE[ENC_COUNT] = {
    "SOUND", "PERFORM", "FX", "KEY", "BASS", "LOOP", "BPM", "VOLUME", "OPTIONS", "CH.VOICING", "BS.VOICING"
};

/* legende (UI-152), mappa del 16/10/2026: con la MK4 la pressione degli encoder è SHIFT + K («S+K»),
 * i voicing stanno sul macro pad (M, m1) e, senza pad, sul fuoco della Flip (L1 R1 e la manopola nav).
 * Con la Plus restano banco B e Y */
static const char *const LEG_MK4[ENC_COUNT] = {
    "K1 S+K1", "K2 S+K2", "K3 S+K3", "K4 S+K4", "K5 S+K5", "K6 REC", "K7 PLAY", "K8 S+K8", "SEL", "L1 R1", "Y"
};
static const char *const LEG_MK4_PAD[ENC_COUNT] = {
    "K1 S+K1", "K2 S+K2", "K3 S+K3", "K4 S+K4", "K5 S+K5", "K6 REC", "K7 PLAY", "K8 S+K8", "T9", "M", "m1"
};
static const char *const LEG_PLUS[ENC_COUNT] = {
    "K1", "K2 B3", "K3", "K4 B1", "K5 B2", "K6 B5 REC", "K7 B6 PLAY", "K8", "B7 SEL", "B4", "Y"
};
static const char *const LEG_PLUS_PAD[ENC_COUNT] = {
    "K1", "K2 B3", "K3", "K4 B1", "K5 B2", "K6 B5 REC", "K7 B6 PLAY", "K8", "T9", "M", "m1"
};
/* senza tastiera: il resto si raggiunge con il fuoco della Flip (L1 R1, croce, A); restano scritti solo i
 * comandi diretti della Flip e del pad, che fa quello che fa con la tastiera (MIDI-120) */
static const char *const LEG_FLIP[ENC_COUNT] = { "", "", "", "", "", "", "START", "", "SEL", "", "Y" };
static const char *const LEG_PAD[ENC_COUNT] = { "", "", "", "", "", "", "START", "", "T9", "M", "m1" };

static const char *pc_name(int pc)
{
    static const char *const N[12] = { "C", "C\xE2\x99\xAF", "D", "D\xE2\x99\xAF", "E", "F", "F\xE2\x99\xAF", "G",
                                       "G\xE2\x99\xAF", "A", "A\xE2\x99\xAF", "B" };
    return N[((pc % 12) + 12) % 12];
}

static void note_name(char *buf, int n, int midi)
{
    char o[6];
    ui_fmt_int(o, sizeof o, midi / 12 - 1, 1);
    ui_fmt_cat(buf, n, pc_name(midi % 12), o);
}

uint64_t uf_sig_cell(const ui_model_t *m, int k)
{
    uint64_t h = UF_H0;
    const ui_controls_t *c = &m->ctl;
    h = uf_h(h, &c->st[k].flags, 1);
    uint8_t f[12] = { (uint8_t)(c->focus == k), (uint8_t)(c->turn_target == k), (uint8_t)(c->push == 2 + k),
                      m->plat.pad_link, m->prefs.legend, m->prefs.theme, m->plat.mpk_model,
                      m->tempo.drums_on, m->tempo.kit, m->tempo.roll, m->tempo.accent, m->plat.mpk_link };
    h = uf_h(h, f, sizeof f);
    uint8_t g[9] = { m->tempo.inv, m->tempo.groove, m->tempo.variation, m->tempo.density, m->tempo.part,   /* MIDI-139 */
                     m->tempo.swing, m->tempo.drive, (uint8_t)m->tempo.filt, m->tempo.bassline };       /* MIDI-135, MIDI-142 */
    h = uf_h(h, g, sizeof g);
    h = uf_h(h, m->tempo.dens, sizeof m->tempo.dens);
    if (k == ENC_SOUND) {                                           /* la cella KIT sotto DRUMS (SND-541) */
        h = uf_h(h, m->tempo.kit_name, sizeof m->tempo.kit_name);
        h = uf_h(h, m->tempo.kit_info, sizeof m->tempo.kit_info);
    }
    if (c->st[k].flags & CF_PRESSED) {
        uint32_t held = m->core_ms - c->st[k].pressed_since_ms;
        uint16_t q = (uint16_t)(held / 33u > 60 ? 60 : held / 33u);
        h = UF_HV(h, q);
    }
    switch (k) {
    case ENC_SOUND:
        h = UF_HV(h, c->sound_user); h = UF_HV(h, c->sound_num); h = UF_HV(h, c->sound_engine);
        h = uf_h(h, c->sound_name, sizeof c->sound_name); h = uf_h(h, c->sound_cat, sizeof c->sound_cat);
        break;
    case ENC_PERFORM:
        h = UF_HV(h, c->perf_mode); h = UF_HV(h, c->perf_amount); h = UF_HV(h, c->arp_rate); h = UF_HV(h, c->arp_dir);
        break;
    case ENC_FX:
        h = UF_HV(h, c->fx_main_type); h = UF_HV(h, c->fx_main_amount); h = uf_h(h, c->fx, sizeof c->fx);
        break;
    case ENC_KEY:
        h = uf_h(h, m->music.key_name, sizeof m->music.key_name);
        h = UF_HV(h, m->music.key_on); h = UF_HV(h, m->music.transpose);
        break;
    case ENC_BASS:
        h = UF_HV(h, c->bass_on); h = UF_HV(h, c->bass_num); h = uf_h(h, c->bass_name, sizeof c->bass_name);
        break;
    case ENC_LOOP:
        h = UF_HV(h, m->looper.state); h = UF_HV(h, m->looper.cur_bar); h = UF_HV(h, m->looper.bars);
        h = UF_HV(h, m->looper.free_mode); h = UF_HV(h, m->looper.slot);
        break;
    case ENC_BPM:
        h = UF_HV(h, m->tempo.bpm); h = UF_HV(h, m->tempo.beat_mode); h = UF_HV(h, m->tempo.beat_index);
        h = UF_HV(h, m->tempo.beat_volume);
        break;
    case ENC_VOLUME:
        h = UF_HV(h, c->volume); h = UF_HV(h, c->bass_volume);
        break;
    case ENC_OPTIONS:
        h = UF_HV(h, c->view); h = UF_HV(h, m->music.play_style);
        break;
    case ENC_CHORD_VOICING:
        h = UF_HV(h, m->music.v); h = UF_HV(h, m->music.W); h = UF_HV(h, m->music.single_notes);
        break;
    case ENC_BASS_VOICING:
        h = UF_HV(h, m->music.vb); h = UF_HV(h, m->music.WB);
        break;
    default: break;
    }
    return h;
}

/* testi della cella: titolo, valore, dettaglio, eventuale barra (0..1000, -1 = nessuna) */
typedef struct { const char *title; char value[40]; char detail[40]; int gauge; int detail_tok; } cell_txt_t;

static void cell_text(const ui_model_t *m, int k, cell_txt_t *t)
{
    const ui_controls_t *c = &m->ctl;
    char a[16], b[16];
    t->title = TITLE[k];
    t->value[0] = t->detail[0] = 0;
    t->gauge = -1;
    t->detail_tok = T_DIM;
    bool sec = (c->st[k].flags & CF_SECONDARY) != 0;
    if (m->tempo.drums_on && (k == ENC_SOUND || k == ENC_PERFORM || k == ENC_BASS)) {   /* drum machine (MIDI-135) */
        if (k == ENC_SOUND) {                                       /* il kit della libreria (SND-541) */
            t->title = "KIT";
            if (m->tempo.kit) {
                ui_fmt_int(a, sizeof a, m->tempo.kit, 2);
                ui_fmt_cat(t->value, sizeof t->value, a, " ");
                ui_fmt_cat(t->value, sizeof t->value, t->value, m->tempo.kit_name);
            } else ui_fmt_copy(t->value, sizeof t->value, m->tempo.kit_name);
            ui_fmt_copy(t->detail, sizeof t->detail, m->tempo.kit_info);
        } else if (k == ENC_PERFORM) {
            t->title = "ROLL";
            ui_fmt_copy(t->value, sizeof t->value, ui_fmt_roll(m->tempo.roll));
            ui_fmt_copy(t->detail, sizeof t->detail, "Hold a key");
        } else if (sec) {                                       /* K5 premuta e girata: il basso che rotola (MIDI-142) */
            t->title = "BASSLINE";
            ui_fmt_copy(t->value, sizeof t->value, ui_fmt_bassline(m->tempo.bassline));
            ui_fmt_int(a, sizeof a, m->tempo.accent, 2);
            ui_fmt_cat(t->detail, sizeof t->detail, "Accent ", a);
        } else {
            t->title = "ACCENT";
            ui_fmt_int(t->value, sizeof t->value, m->tempo.accent, 2);
            if (m->tempo.bassline) ui_fmt_cat(t->detail, sizeof t->detail, "Bass ", ui_fmt_bassline(m->tempo.bassline));
            else ui_fmt_copy(t->detail, sizeof t->detail, "Velocity");
        }
        return;
    }
    if (m->tempo.drums_on && (k == ENC_FX || k == ENC_KEY)) {   /* K3 drive e filtro, K4 swing (MIDI-135) */
        if (k == ENC_FX) {
            t->title = sec ? "FILTER" : "DRIVE";
            if (sec) ui_fmt_filter(t->value, sizeof t->value, m->tempo.filt);
            else ui_fmt_int(t->value, sizeof t->value, m->tempo.drive, 2);
            if (sec) ui_fmt_int(a, sizeof a, m->tempo.drive, 2);
            else ui_fmt_filter(a, sizeof a, m->tempo.filt);
            ui_fmt_cat(t->detail, sizeof t->detail, sec ? "Drive " : "Filter ", a);
            if (!sec) t->gauge = m->tempo.drive * 100;
        } else {
            t->title = "SWING";
            ui_fmt_copy(t->value, sizeof t->value, ui_fmt_swing(m->tempo.swing));
            ui_fmt_copy(t->detail, sizeof t->detail, "Beat and loop");
        }
        return;
    }
    if (m->tempo.drums_on && (k == ENC_CHORD_VOICING || k == ENC_BASS_VOICING)) {   /* batteria che si inventa (MIDI-139) */
        if (k == ENC_CHORD_VOICING) {
            int d = m->tempo.part ? m->tempo.dens[(m->tempo.part - 1) % UI_INV_PARTS] : m->tempo.density;
            t->title = "DENSITY";
            ui_fmt_int(t->value, sizeof t->value, d, 2);
            ui_fmt_copy(t->detail, sizeof t->detail, ui_fmt_part(m->tempo.part));
            t->gauge = d * 100;
        } else {
            t->title = "GROOVE";
            ui_fmt_copy(t->value, sizeof t->value, m->tempo.groove_name);
            ui_fmt_int(a, sizeof a, m->tempo.variation, 1);
            ui_fmt_cat(t->detail, sizeof t->detail, "Var ", a);
        }
        return;
    }
    switch (k) {
    case ENC_SOUND:
        if (c->sound_user) { ui_fmt_int(b, sizeof b, c->sound_num, 2); ui_fmt_cat(a, sizeof a, "U", b); }
        else ui_fmt_int(a, sizeof a, c->sound_num, 2);
        ui_fmt_cat(t->value, sizeof t->value, a, " ");
        ui_fmt_cat(t->value, sizeof t->value, t->value, c->sound_name);
        ui_fmt_cat(t->detail, sizeof t->detail, ui_fmt_engine(c->sound_engine), "  ");
        ui_fmt_cat(t->detail, sizeof t->detail, t->detail, c->sound_cat);
        if (c->st[k].flags & CF_LEGACY) ui_fmt_cat(t->detail, sizeof t->detail, t->detail, " legacy");
        break;
    case ENC_PERFORM:
        ui_fmt_copy(t->value, sizeof t->value, c->perf_mode ? ui_fmt_perf_short(c->perf_mode) : "Off");
        if (c->perf_mode == PERF_ARP || c->perf_mode == PERF_ARP2) {
            static const char *const DIR[3] = { "UP", "DOWN", "UP/DOWN" };
            ui_fmt_int(a, sizeof a, c->arp_rate, 2);
            ui_fmt_cat(t->detail, sizeof t->detail, a, "  ");
            ui_fmt_cat(t->detail, sizeof t->detail, t->detail, DIR[c->arp_dir % 3]);
        } else if (c->perf_mode == PERF_PATTERN) {
            ui_fmt_int(a, sizeof a, c->perf_amount, 2);
            ui_fmt_cat(t->detail, sizeof t->detail, "Pattern ", a);
        } else if (c->perf_mode) {
            ui_fmt_int(a, sizeof a, c->perf_amount, 2);
            ui_fmt_cat(t->detail, sizeof t->detail, "Amount ", a);
        }
        break;
    case ENC_FX: {
        if (c->fx_main_amount) ui_fmt_int(a, sizeof a, c->fx_main_amount, 2);
        else ui_fmt_copy(a, sizeof a, "OFF");
        ui_fmt_cat(t->value, sizeof t->value, ui_fmt_fx_name(c->fx_main_type), " ");
        ui_fmt_cat(t->value, sizeof t->value, t->value, a);
        for (int i = 0; i < 4; i++) {
            if (!c->fx[i].amount) continue;
            ui_fmt_int(b, sizeof b, c->fx[i].amount, 1);
            ui_fmt_cat(a, sizeof a, ui_fmt_fx_abbr(c->fx[i].type), b);
            if (t->detail[0]) ui_fmt_cat(t->detail, sizeof t->detail, t->detail, " ");
            ui_fmt_cat(t->detail, sizeof t->detail, t->detail, a);
        }
        break;
    }
    case ENC_KEY:
        if (sec) t->title = "TRANSPOSE";
        ui_fmt_copy(t->value, sizeof t->value, m->music.key_on ? m->music.key_name : "Off");
        ui_fmt_signed(a, sizeof a, m->music.transpose);
        ui_fmt_cat(t->detail, sizeof t->detail, "Trans ", a);
        t->detail_tok = m->music.transpose ? T_ACTIVE : T_DIM;
        break;
    case ENC_BASS:
        ui_fmt_int(a, sizeof a, c->bass_num, 2);
        ui_fmt_cat(t->value, sizeof t->value, c->bass_on ? "On  " : "Off  ", a);
        ui_fmt_copy(t->detail, sizeof t->detail, c->bass_name);
        break;
    case ENC_LOOP: {
        static const char *const S[] = { "\xE2\x80\x94", "Wait", "Count", "Rec", "Play", "Dub", "Pause" };
        const ui_looper_t *lp = &m->looper;
        ui_fmt_copy(t->value, sizeof t->value, lp->state < STAME_COUNT(S) ? S[lp->state] : "?");
        if (lp->slot) { ui_fmt_int(a, sizeof a, lp->slot, 2); ui_fmt_cat(t->detail, sizeof t->detail, "Loop ", a); }
        else if (lp->free_mode && !lp->bars) ui_fmt_copy(t->detail, sizeof t->detail, "Free");
        else if (lp->bars) {
            ui_fmt_int(a, sizeof a, lp->cur_bar, 1);
            ui_fmt_int(b, sizeof b, lp->bars, 1);
            ui_fmt_cat(t->detail, sizeof t->detail, "bar ", a);
            ui_fmt_cat(t->detail, sizeof t->detail, t->detail, "/");
            ui_fmt_cat(t->detail, sizeof t->detail, t->detail, b);
        }
        break;
    }
    case ENC_BPM:
        if (sec) {
            t->title = "BEAT VOL";
            ui_fmt_int(t->value, sizeof t->value, m->tempo.beat_volume, 2);
            t->gauge = m->tempo.beat_volume * 1000 / 99;
        } else {
            ui_fmt_int(t->value, sizeof t->value, m->tempo.bpm, 1);
        }
        if (m->tempo.beat_mode == BEAT_PATTERN && m->tempo.inv) {   /* il loop inventato (MIDI-139) */
            ui_fmt_int(a, sizeof a, m->tempo.variation, 1);
            ui_fmt_cat(t->detail, sizeof t->detail, m->tempo.groove_name, " v");
            ui_fmt_cat(t->detail, sizeof t->detail, t->detail, a);
        } else if (m->tempo.beat_mode == BEAT_PATTERN) {
            ui_fmt_int(a, sizeof a, m->tempo.beat_index, 2);
            ui_fmt_cat(t->detail, sizeof t->detail, "Beat ", a);
        } else {
            ui_fmt_copy(t->detail, sizeof t->detail, m->tempo.beat_mode == BEAT_METRONOME ? "Metro" : "Off");
        }
        break;
    case ENC_VOLUME:
        if (sec) {
            t->title = "BASS VOL";
            ui_fmt_int(t->value, sizeof t->value, c->bass_volume, 2);
            t->gauge = c->bass_volume * 1000 / 99;
        } else {
            ui_fmt_int(t->value, sizeof t->value, c->volume, 2);
            t->gauge = c->volume * 1000 / 99;
        }
        ui_fmt_int(a, sizeof a, c->bass_volume, 2);
        ui_fmt_cat(t->detail, sizeof t->detail, "Bass ", a);
        break;
    case ENC_OPTIONS:
        ui_fmt_copy(t->value, sizeof t->value, ui_fmt_view_short(c->view));
        ui_fmt_copy(t->detail, sizeof t->detail, ui_fmt_play_style(m->music.play_style));
        break;
    case ENC_CHORD_VOICING:
        ui_fmt_int(t->value, sizeof t->value, m->music.v, 3);
        note_name(a, sizeof a, m->music.W);
        ui_fmt_cat(t->detail, sizeof t->detail, a, m->music.single_notes ? " Oct" : " Split");
        t->gauge = (m->music.v - 1) * 1000 / 59;
        break;
    case ENC_BASS_VOICING:
        ui_fmt_int(t->value, sizeof t->value, m->music.vb, 2);
        note_name(t->detail, sizeof t->detail, m->music.WB);
        t->gauge = m->music.vb * 1000 / 48;
        break;
    default: break;
    }
}

#define LY 240          /* cima della zona comandi (UF_ZONE_RECT[UF_Z5]) */

void uf_draw_z5_frame(gfx_fb16_t *fb, const uf_pal_t *p)
{
    gfx_hline(fb, 0, LY, 640, p->c[T_LINE]);
}

void uf_draw_cell(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m, int k)
{
    const gfx_rect_t *r = &UF_CELL_RECT[k];
    const ui_controls_t *c = &m->ctl;
    int x = r->x, y = r->y, w = r->w;
    uint8_t fl = c->st[k].flags;
    bool focus = c->focus == k;
    cell_txt_t t;
    cell_text(m, k, &t);

    gfx_hline(fb, x, y, w, p->c[T_LINE]);
    if (x > 0) gfx_vline(fb, x, y, 72, p->c[T_LINE]);
    int ix = x + (x > 0 ? 1 : 0);
    uf_glass(fb, p, ix, y + 1, x + w - ix, 71);

    /* titolo: stampato sul vetro; con il fuoco, in negativo */
    int tx = x + 5, ty = y + 5;
    if (focus) {
        gfx_fill(fb, ix, y + 1, x + w - ix, 16, p->c[T_FOCUS]);
        uf_label(fb, tx, ty, t.title, p->c[T_BG]);
    } else {
        uf_label(fb, tx, ty, t.title, p->c[(fl & CF_SECONDARY) ? T_ACTIVE : T_DIM]);
    }
    /* contrassegni a destra del titolo */
    int xr = x + w - 5;
    if (fl & CF_LOCK) {
        int lw = uf_label_w("LOCK") + 4;
        gfx_fill(fb, xr - lw, y + 3, lw, 12, p->c[T_ACTIVE]);
        uf_label(fb, xr - lw + 2, y + 4, "LOCK", p->c[T_BG]);
        xr -= lw + 4;
    }
    if (fl & CF_LED) gfx_disc(fb, (xr - 4) * GFX_SUB, (y + 9) * GFX_SUB, 3 * GFX_SUB, focus ? p->c[T_BG] : p->c[T_TEXT]);

    /* valore: con un overlay attivo, in negativo su active */
    int vy = y + 18;
    gfx_c vcol = p->c[T_TEXT];
    if (fl & CF_ACTIVE) {
        gfx_fill(fb, x + 3, vy, w - 6, 24, p->c[T_ACTIVE]);
        vcol = p->c[T_BG];
    }
    gfx_text_fit(fb, &GFX_M, x + 5, vy, t.value, vcol, w - 10);
    if (t.gauge >= 0) {
        int cells = (w - 10) / 4;
        int lit = (t.gauge * cells + 500) / 1000;
        uf_gauge(fb, x + 5, y + 42, 3, cells, 3, 1, lit, p->c[k == ENC_CHORD_VOICING ? T_TREBLE : k == ENC_BASS_VOICING ? T_BASS : T_TEXT], p->c[T_SEGOFF]);
    }
    gfx_text_fit(fb, &GFX_S, x + 5, y + 44, t.detail, p->c[t.detail_tok], w - 10);
    if (m->prefs.legend) {
        bool pad = m->plat.pad_link == PADL_OPEN;
        bool kb = m->plat.mpk_link == MPK_OPEN;
        const char *leg = !kb ? (pad ? LEG_PAD[k] : LEG_FLIP[k])
                        : m->plat.mpk_model ? (pad ? LEG_MK4_PAD[k] : LEG_MK4[k])
                                            : (pad ? LEG_PLUS_PAD[k] : LEG_PLUS[k]);
        gfx_text_fit(fb, &GFX_XS, x + 5, y + 59, leg, p->c[T_GHOST], w - 10);
    }
    /* fuoco: cornice di 2 pixel */
    if (focus) gfx_frame(fb, ix, y + 1, x + w - ix, 71, 2, p->c[T_FOCUS]);
    /* premuto: barra che cresce fino alla soglia del tenuto (UI-153) */
    /* anche la pressione del PUSH da B8 o X arriva come CF_PRESSED (il riconoscitore unisce le
     * sorgenti, MIDI-102): il bersaglio da solo non è una pressione, e con pressed_since_ms vecchio
     * la barra restava ferma o partiva piena */
    bool pushed = (fl & CF_PRESSED) != 0;
    if (pushed && !(fl & CF_SECONDARY)) {
        uint32_t held = m->core_ms - c->st[k].pressed_since_ms;
        uint32_t th = c->st[k].t_hold_ms ? c->st[k].t_hold_ms : 1000;
        int bw = (int)((held >= th ? th : held) * (uint32_t)(w - 2) / th);
        gfx_fill(fb, ix, y + 1, bw, 2, p->c[T_TEXT]);
    }
}

/* ---- liste e menu (UI-157) ---- */

uint64_t uf_sig_z5_list(const ui_model_t *m)
{
    uint64_t h = UF_H0 ^ 0x5A5A;
    h = uf_h(h, &m->layer.list, sizeof m->layer.list);
    h = UF_HV(h, m->prefs.theme);
    if (m->layer.list.editing) { uint8_t b = (uint8_t)uf_blink(m->now_ms, 500, 250); h = UF_HV(h, b); }
    return h;
}

void uf_draw_list(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m)
{
    const ui_list_t *l = &m->layer.list;
    gfx_hline(fb, 0, LY, 640, p->c[T_LINE]);
    gfx_fill(fb, 0, LY + 1, 640, 23, p->c[T_PANEL]);
    gfx_text_fit(fb, &GFX_S, 8, LY + 4, l->path, p->c[T_DIM], 520);
    char pos[16], a[8];
    ui_fmt_int(pos, sizeof pos, l->sel + 1, 1);
    ui_fmt_int(a, sizeof a, l->n, 1);
    ui_fmt_cat(pos, sizeof pos, pos, "/");
    ui_fmt_cat(pos, sizeof pos, pos, a);
    gfx_text_right(fb, &GFX_S, 632, LY + 4, pos, p->c[T_DIM], 0);
    uf_glass(fb, p, 0, LY + 24, 640, 120);

    for (int row = 0; row < 5; row++) {
        int idx = (int)l->sel - 2 + row;
        if (idx < 0 || idx >= (int)l->n) continue;
        int wi = idx - (int)l->win_first;
        if (wi < 0 || wi >= UI_LIST_WIN) continue;
        const ui_item_t *it = &l->win[wi];
        int y = LY + 24 + row * 24;
        bool sel = idx == (int)l->sel;
        gfx_c fg = sel ? p->c[T_BG] : it->enabled ? p->c[T_TEXT] : p->c[T_GHOST];
        gfx_c fd = sel ? p->c[T_BG] : p->c[T_DIM];
        if (sel) gfx_fill(fb, 0, y, 636, 24, p->c[T_FOCUS]);
        int lx = 16;
        if (it->num[0]) { gfx_text(fb, &GFX_M, 16, y, it->num, fd); lx = 64; }
        gfx_text_fit(fb, &GFX_M, lx, y, it->label, fg, 440 - lx);
        if (it->info[0]) gfx_text_fit(fb, &GFX_S, 448, y + 4, it->info, fd, 140);
        if (it->value[0]) {
            bool hide = sel && l->editing && !uf_blink(m->now_ms, 500, 250);
            if (!hide) gfx_text_right(fb, &GFX_M, 604, y, it->value, fg, 0);
        }
        const char *mk = it->mark == MK_CHECK ? "\xE2\x9C\x93" : it->mark == MK_DOT ? "\xE2\x97\x8F" :
                         it->mark == MK_SUBMENU ? "\xC2\xBB" : NULL;
        if (mk) gfx_text(fb, &GFX_S, 616, y + 4, mk, sel ? p->c[T_BG] : p->c[T_FOCUS]);
    }
    /* barra di scorrimento */
    gfx_fill(fb, 636, LY + 24, 3, 120, p->c[T_SEGOFF]);
    if (l->n > 1) {
        int th = 120 * 5 / (l->n > 5 ? l->n : 5);
        if (th < 8) th = 8;
        int ty = LY + 24 + (int)((120 - th) * l->sel / (l->n - 1));
        gfx_fill(fb, 636, ty, 3, th, p->c[T_DIM]);
    }
}
