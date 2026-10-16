/* zona_stato.c — Z1, testata (UI-126). Scritte stampate in dim, valori accesi.
 *
 * Lo stato tace quando va tutto bene: nella pagina di gioco la testata mostra solo la batteria e,
 * quando servono, gli avvisi (MPK assente o occupata, profilo di fabbrica, macro pad in errore,
 * modo tascabile, clip, xrun) e il Lock delle manopole del pad, che è uno stato come il LED del
 * Caps Lock (MIDI-131). In Geek Out torna la barra completa: attività MIDI, voci, carico, livelli,
 * macro pad.
 */
#include "uf_int.h"

static bool mpk_blink(const ui_model_t *m) { return uf_blink(m->now_ms, 500, 500); }
static bool geek(const ui_model_t *m) { return m->ctl.view == VIEW_GEEK; }

uint64_t uf_sig_z1(const ui_model_t *m, const ui_flip_state_t *st)
{
    uint64_t h = UF_H0;
    const ui_platform_t *pl = &m->plat;
    bool g = geek(m);
    uint8_t v[19] = {
        pl->mpk_link, pl->mpk_profile, pl->mpk_bank, pl->pad_link, m->prefs.pocket, m->prefs.meters, m->ctl.knob_lock,
        (uint8_t)(g && m->now_ms - pl->midi_in_ms < 50), (uint8_t)(g && m->now_ms - pl->midi_out_ms < 50),
        g ? m->meters.voices_used : 0, g ? m->meters.dsp_load_pct : 0, pl->battery_pct, pl->charging,
        (uint8_t)((int32_t)(st->xrun_until - m->now_ms) > 0), (uint8_t)((int32_t)(st->clip_until - m->now_ms) > 0),
        (uint8_t)(pl->mpk_link == MPK_ABSENT && mpk_blink(m)),
        (uint8_t)(pl->battery_pct < 10 && uf_blink(m->now_ms, 500, 500)),
        (uint8_t)g, m->tempo.drums_on,
    };
    h = uf_h(h, v, sizeof v);
    if (g) h = uf_h(h, st->peak_db10, sizeof st->peak_db10);
    h = UF_HV(h, m->prefs.theme);
    return h;
}

static void level_bar(gfx_fb16_t *fb, const uf_pal_t *p, int x, int y, int db10)
{
    const int n = 22;
    int lit = db10 * n / 480;
    for (int i = 0; i < n; i++) {
        gfx_c c = i >= lit ? p->c[T_SEGOFF] : (i >= 20 ? p->c[T_ACTIVE] : p->c[T_TEXT]);
        gfx_fill(fb, x + i * 4, y, 3, 4, c);
    }
}

static void battery(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m)
{
    const ui_platform_t *pl = &m->plat;
    int pct = pl->battery_pct;
    bool unknown = pct == 255;
    bool low = !unknown && pct < 15;
    bool hide = !unknown && pct < 10 && !uf_blink(m->now_ms, 500, 500);
    gfx_c c = low ? p->c[T_WARN] : p->c[T_TEXT];
    char buf[8];
    if (unknown) ui_fmt_copy(buf, sizeof buf, "--");
    else { ui_fmt_int(buf, sizeof buf, pct, 1); ui_fmt_cat(buf, sizeof buf, buf, "%"); }
    /* la colonna è 576..635 (UI-126): «100%» finiva sopra «POCKET», che arriva a 575 */
    if (!hide) gfx_text_right(fb, &GFX_S, 606, 4, buf, c, 0);
    /* icona 28×12: contorno, polo, 4 celle */
    int x = 608, y = 6;
    gfx_frame(fb, x, y, 26, 12, 1, p->c[T_DIM]);
    gfx_fill(fb, x + 26, y + 3, 2, 6, p->c[T_DIM]);
    int cells = unknown ? 0 : (pct + 24) / 25;
    for (int i = 0; i < 4; i++)
        gfx_fill(fb, x + 2 + i * 6, y + 2, 5, 8, i < cells && !hide ? c : p->c[T_SEGOFF]);
    if (pl->charging) {
        gfx_text(fb, &GFX_XS, x + 10, y, "\xE2\x9A\xA1", p->c[T_ACTIVE]);
    }
}

/* clip e xrun: compaiono per un attimo quando succedono */
static int clip_xrun(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m, const ui_flip_state_t *st, int x,
                     bool frame, bool show_xrun)
{
    bool clip = (int32_t)(st->clip_until - m->now_ms) > 0;
    bool xr = (int32_t)(st->xrun_until - m->now_ms) > 0;
    if (clip) {
        gfx_fill(fb, x, 5, 34, 14, p->c[T_WARN]);
        uf_label(fb, x + 4, 6, "CLIP", p->c[T_BG]);
        x += 42;
    } else if (frame) {
        gfx_frame(fb, x, 5, 34, 14, 1, p->c[T_SEGOFF]);
        uf_label(fb, x + 4, 6, "CLIP", p->c[T_SEGOFF]);
        x += 42;
    }
    if (xr && show_xrun) x = gfx_text(fb, &GFX_S, x, 4, "XRUN", p->c[T_WARN]) + 12;
    return x;
}

/* la MPK: nella pagina di gioco solo se qualcosa non va */
static int mpk(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m, int x, bool always)
{
    const ui_platform_t *pl = &m->plat;
    const char *word = "STAME";
    int tok = T_FOCUS;
    switch (pl->mpk_link) {
    case MPK_OPEN:
        if (pl->mpk_profile == MPKP_FACTORY) { word = "FACTORY"; tok = T_ACTIVE; }
        else if (!always) return x;
        break;
    case MPK_BUSY:  word = "BUSY"; tok = T_WARN; break;
    case MPK_ERROR: word = "ERROR"; tok = T_WARN; break;
    default:
        /* «NO MPK» lampeggia; lo spazio resta occupato, così il resto non si sposta */
        if (mpk_blink(m)) gfx_text(fb, &GFX_S, x, 4, "NO MPK", p->c[T_WARN]);
        return x + gfx_text_w(&GFX_S, "NO MPK", 0) + 16;
    }
    int x1 = gfx_text(fb, &GFX_S, x, 4, "MPK", p->c[T_DIM]);
    x1 = gfx_text(fb, &GFX_S, x1 + 8, 4, word, p->c[tok]);
    if (always && pl->mpk_link == MPK_OPEN) {
        const char *bank = pl->mpk_bank == MPK_BANK_EST_A ? "A" : pl->mpk_bank == MPK_BANK_EST_B ? "B" : "?";
        x1 = gfx_text(fb, &GFX_S, x1 + 8, 4, bank, p->c[T_DIM]);
    }
    return x1 + 16;
}

void uf_draw_z1(gfx_fb16_t *fb, const uf_pal_t *p, const ui_model_t *m, const ui_flip_state_t *st)
{
    const ui_platform_t *pl = &m->plat;
    gfx_fill(fb, 0, 0, 640, 24, p->c[T_PANEL]);
    const int y = 4;

    if (!geek(m)) {
        int x = mpk(fb, p, m, 8, false);
        if (pl->pad_link == PADL_ERROR || pl->pad_link == PADL_UNMAPPED)
            x = gfx_text(fb, &GFX_S, x, y, "PAD", p->c[T_WARN]) + 16;
        if (m->prefs.pocket) x = gfx_text(fb, &GFX_S, x, y, "POCKET", p->c[T_ACTIVE]) + 16;
        if (m->ctl.knob_lock) {                       /* lo stato acceso, poi cosa fanno le manopole, stampato */
            x = gfx_text(fb, &GFX_S, x, y, "LOCK", p->c[T_ACTIVE]);
            x = gfx_text(fb, &GFX_S, x + 8, y, "SOUND PERFORM KEY", p->c[T_DIM]) + 16;
        }
        /* batteria a tastiera: uno stato, quindi sempre in vista (anche con il transpose o la pagina dei comandi) */
        if (m->tempo.drums_on) x = gfx_text(fb, &GFX_S, x, y, "DRUMS", p->c[T_ACTIVE]) + 16;
        clip_xrun(fb, p, m, st, x, false, true);
        battery(fb, p, m);
        return;
    }

    /* Geek Out: la barra completa */
    mpk(fb, p, m, 4, true);
    bool in = m->now_ms - pl->midi_in_ms < 50, out = m->now_ms - pl->midi_out_ms < 50;
    int x = gfx_text(fb, &GFX_S, 108, y, "IN", p->c[T_DIM]);
    gfx_text(fb, &GFX_S, x + 2, y, in ? "\xE2\x97\x8F" : "\xE2\x97\x8B", in ? p->c[T_TREBLE] : p->c[T_SEGOFF]);
    x = gfx_text(fb, &GFX_S, 140, y, "OUT", p->c[T_DIM]);
    gfx_text(fb, &GFX_S, x + 2, y, out ? "\xE2\x97\x8F" : "\xE2\x97\x8B", out ? p->c[T_TREBLE] : p->c[T_SEGOFF]);

    if (m->prefs.meters) {
        char buf[16], n2[8];
        int vu = m->meters.voices_used;
        ui_fmt_int(buf, sizeof buf, vu, 2);
        ui_fmt_cat(buf, sizeof buf, buf, "/16");
        x = gfx_text(fb, &GFX_S, 208, y, "VOX", p->c[T_DIM]);
        gfx_text(fb, &GFX_S, x + 4, y, buf, p->c[vu >= 16 ? T_WARN : vu > 14 ? T_ACTIVE : T_TEXT]);
        bool xr = (int32_t)(st->xrun_until - m->now_ms) > 0;
        int load = m->meters.dsp_load_pct;
        if (!xr) {
            ui_fmt_int(n2, sizeof n2, load, 1);
            ui_fmt_cat(buf, sizeof buf, n2, "%");
            x = gfx_text(fb, &GFX_S, 292, y, "CPU", p->c[T_DIM]);
            gfx_text(fb, &GFX_S, x + 4, y, buf, p->c[load > 90 ? T_WARN : load > 70 ? T_ACTIVE : T_TEXT]);
        }
        level_bar(fb, p, 360, 7, st->peak_db10[0]);
        level_bar(fb, p, 360, 13, st->peak_db10[1]);
        if (xr) gfx_text(fb, &GFX_S, 292, y, "XRUN", p->c[T_WARN]);
        clip_xrun(fb, p, m, st, 452, true, false);
    }

    if (pl->pad_link != PADL_ABSENT) {                /* con il Lock acceso il contrassegno diventa LOCK */
        bool lk = m->ctl.knob_lock != 0;
        gfx_text(fb, &GFX_S, 492, y, lk ? "LOCK" : "PAD", p->c[lk ? T_ACTIVE : pl->pad_link == PADL_OPEN ? T_FOCUS : T_WARN]);
    }
    if (m->prefs.pocket)
        gfx_text(fb, &GFX_S, 528, y, "POCKET", p->c[T_ACTIVE]);

    battery(fb, p, m);
}
