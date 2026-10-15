/* test_plancia.c — temi (UI-128, T-UI-20) e renderer della plancia (UI-003, UI-115, UI-160). */
#include <math.h>
#include <string.h>
#include "test.h"
#include "ui_flip/ui_flip.h"
#include "ui/ui_fmt.h"

static double lum(uint32_t rgb)
{
    double c[3];
    for (int i = 0; i < 3; i++) {
        double v = (double)((rgb >> (16 - 8 * i)) & 0xFF) / 255.0;
        c[i] = v <= 0.03928 ? v / 12.92 : pow((v + 0.055) / 1.055, 2.4);
    }
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}

static double contrast(uint32_t a, uint32_t b)
{
    double la = lum(a), lb = lum(b);
    return la > lb ? (la + 0.05) / (lb + 0.05) : (lb + 0.05) / (la + 0.05);
}

static void test_tema(void)
{
    static const int TEXT[] = { T_TEXT, T_DIM, T_TREBLE, T_BASS, T_LOOP, T_FOCUS, T_ACTIVE, T_WARN };
    static const int ROLE[] = { T_TREBLE, T_BASS };
    for (int th = 0; th < 2; th++) {
        const uint32_t *c = UF_THEME[th].rgb;
        for (unsigned i = 0; i < sizeof TEXT / sizeof TEXT[0]; i++) {
            CHECKM(contrast(c[TEXT[i]], c[T_BG]) >= 4.5, "T-UI-20 tema %d token %d su bg: %.2f", th, TEXT[i], contrast(c[TEXT[i]], c[T_BG]));
            CHECKM(contrast(c[TEXT[i]], c[T_PANEL]) >= 4.5, "T-UI-20 tema %d token %d su panel", th, TEXT[i]);
        }
        for (unsigned i = 0; i < sizeof ROLE / sizeof ROLE[0]; i++)
            CHECKM(contrast(c[ROLE[i]], c[T_KBW]) >= 3.0, "T-UI-20 tema %d ruolo %d sui tasti bianchi", th, ROLE[i]);
        /* testo in negativo (titolo con il fuoco, valore attivo, avvisi, legenda dei tasti) */
        CHECK(contrast(c[T_BG], c[T_FOCUS]) >= 4.5);
        CHECK(contrast(c[T_BG], c[T_ACTIVE]) >= 4.5);
        CHECK(contrast(c[T_BG], c[T_WARN]) >= 4.5);
        CHECK(contrast(c[T_BG], c[T_DIM]) >= 4.5);
        /* ghost è un ricordo: tenue ma leggibile da vicino; i segmenti spenti appena visibili */
        double g = contrast(c[T_GHOST], c[T_BG]);
        CHECKM(g >= 2.0 && g <= 3.5, "ghost tema %d: %.2f", th, g);
        double so = contrast(c[T_SEGOFF], c[T_BG]);
        CHECKM(so > 1.05 && so < 1.6, "segmenti spenti tema %d: %.2f", th, so);
    }
}

static uint16_t fb_a[UI_FLIP_W * UI_FLIP_H], fb_b[UI_FLIP_W * UI_FLIP_H];
static ui_model_t m;

static void model_base(void)
{
    memset(&m, 0, sizeof m);
    m.layer.base = BASE_PLAY;
    m.prefs.legend = 1;
    m.prefs.meters = 1;
    m.prefs.linnaeus = 1;
    m.plat.mpk_link = MPK_OPEN;
    m.plat.battery_pct = 80;
    m.now_ms = m.core_ms = 10000;
    m.plat.midi_in_ms = m.plat.midi_out_ms = 1000;
    m.music.v = 24; m.music.W = 48; m.music.vb = 23; m.music.WB = 36;
    m.tempo.bpm = 120; m.tempo.beats_per_bar = 4; m.tempo.beat_unit = 4;
    m.ctl.view = VIEW_CHORD;
    m.ctl.focus = ENC_SOUND;
    ui_fmt_copy(m.ctl.sound_name, sizeof m.ctl.sound_name, "Glass Pollen");
    m.music.key_on = 1;
    ui_fmt_copy(m.music.key_name, sizeof m.music.key_name, "F\xE2\x99\xAF Minor");
}

static void chord(void)
{
    m.music.chord_state = CH_SOUNDING;
    m.music.chord.root[0] = 'F';
    ui_fmt_copy(m.music.chord.acc, sizeof m.music.chord.acc, "\xE2\x99\xAF");
    ui_fmt_copy(m.music.chord.quality, sizeof m.music.chord.quality, "m");
    ui_fmt_copy(m.music.chord.sup, sizeof m.music.chord.sup, "7");
    static const uint8_t N[5] = { 42, 54, 57, 61, 64 };
    m.music.n_notes = 5;
    for (int i = 0; i < 5; i++) {
        m.music.notes[i].midi = N[i];
        m.music.notes[i].role = i ? ROLE_TREBLE : ROLE_BASS;
        ui_fmt_copy(m.music.notes[i].name, sizeof m.music.notes[i].name, "X3");
        uint32_t *mask = i ? m.music.live_treble : m.music.live_bass;
        mask[N[i] >> 5] |= 1u << (N[i] & 31);
    }
    m.music.pc_sounding = (1u << 6) | (1u << 9) | (1u << 1) | (1u << 4);
}

void test_plancia(void)
{
    test_tema();

    static ui_flip_state_t sa, sb;
    gfx_fb16_t fa, fbb;
    gfx_fb_init(&fa, fb_a, UI_FLIP_W, UI_FLIP_H, UI_FLIP_W);
    gfx_fb_init(&fbb, fb_b, UI_FLIP_W, UI_FLIP_H, UI_FLIP_W);
    gfx_rect_t dirty[UI_FLIP_MAX_DIRTY];

    /* UI-142: la pagina di gioco disegna 5 zone (testata, accordo, tempo, tastiera, banda) e nessuna cella */
    model_base();
    chord();
    int n = ui_flip_render(&sa, &m, &fa, dirty, UI_FLIP_MAX_DIRTY);
    CHECK_EQ(n, 5);
    /* UI-115: nulla di cambiato, nulla da presentare */
    CHECK_EQ(ui_flip_render(&sa, &m, &fa, dirty, UI_FLIP_MAX_DIRTY), 0);

    /* UI-003: stesso modello, stesso framebuffer, pixel per pixel */
    memset(&sb, 0, sizeof sb);
    ui_flip_render(&sb, &m, &fbb, dirty, UI_FLIP_MAX_DIRTY);
    CHECK(memcmp(fb_a, fb_b, sizeof fb_a) == 0);

    /* cambia solo il voicing: si ridisegnano accordo e tastiera, non la testata né la banda */
    m.music.v = 25; m.music.W = 49;
    n = ui_flip_render(&sa, &m, &fa, dirty, UI_FLIP_MAX_DIRTY);
    CHECK(n >= 1 && n <= 2);
    bool z1 = false, z6 = false;
    for (int i = 0; i < n; i++) {
        if (dirty[i].y == 0 && dirty[i].h == 24) z1 = true;
        if (dirty[i].y == 384) z6 = true;
    }
    CHECK(!z1);
    CHECK(!z6);

    /* UI-126: fuori da Geek Out l'attività MIDI e il carico non ridisegnano la testata */
    m.plat.midi_in_ms = m.now_ms;
    m.meters.dsp_load_pct = 40;
    CHECK_EQ(ui_flip_render(&sa, &m, &fa, dirty, UI_FLIP_MAX_DIRTY), 0);
    m.ctl.view = VIEW_GEEK;
    n = ui_flip_render(&sa, &m, &fa, dirty, UI_FLIP_MAX_DIRTY);
    z1 = false;
    for (int i = 0; i < n; i++) if (dirty[i].y == 0 && dirty[i].h == 24) z1 = true;
    CHECK(z1);
    m.ctl.view = VIEW_CHORD;
    ui_flip_render(&sa, &m, &fa, dirty, UI_FLIP_MAX_DIRTY);

    /* UI-154: un overlay accende la banda; quello del voicing mostra anche le finestre sulla tastiera */
    m.layer.ov.kind = OV_VOICING;
    m.layer.ov.value = 25;
    n = ui_flip_render(&sa, &m, &fa, dirty, UI_FLIP_MAX_DIRTY);
    bool z4 = false;
    z6 = false;
    for (int i = 0; i < n; i++) {
        if (dirty[i].y == 240 && dirty[i].w == 640) z4 = true;
        if (dirty[i].y == 384) z6 = true;
    }
    CHECK(z4);
    CHECK(z6);
    m.layer.ov.kind = OV_NONE;
    ui_flip_render(&sa, &m, &fa, dirty, UI_FLIP_MAX_DIRTY);

    /* il cambio di tema ridisegna tutto e cambia i pixel */
    m.prefs.theme = THEME_LIGHT;
    n = ui_flip_render(&sa, &m, &fa, dirty, UI_FLIP_MAX_DIRTY);
    CHECK_EQ(n, 5);
    CHECK(fb_a[UI_FLIP_W * 100 + 300] != fb_b[UI_FLIP_W * 100 + 300]);

    /* UI-142a: la pagina dei comandi prende il posto della tastiera: 11 celle e la banda con la legenda */
    m.layer.page = PAGE_CONTROLS;
    n = ui_flip_render(&sa, &m, &fa, dirty, UI_FLIP_MAX_DIRTY);
    CHECK_EQ(n, ENC_COUNT + 1);
    bool sound = false;
    for (int i = 0; i < n; i++) if (dirty[i].x == 0 && dirty[i].y == 240 && dirty[i].w == 208) sound = true;
    CHECK(sound);
    /* tornando a suonare si ridisegnano la tastiera e la banda, non le altre zone */
    m.layer.page = PAGE_PLAY;
    n = ui_flip_render(&sa, &m, &fa, dirty, UI_FLIP_MAX_DIRTY);
    CHECK_EQ(n, 2);

    /* una lista aperta prende la zona comandi in un rettangolo solo, anche dalla pagina di gioco */
    m.layer.list.open = 1;
    m.layer.list.n = 3;
    ui_fmt_copy(m.layer.list.path, sizeof m.layer.list.path, "MENU");
    ui_fmt_copy(m.layer.list.win[0].label, sizeof m.layer.list.win[0].label, "Exit");
    n = ui_flip_render(&sa, &m, &fa, dirty, UI_FLIP_MAX_DIRTY);
    bool z5 = false;
    for (int i = 0; i < n; i++) if (dirty[i].y == 240 && dirty[i].w == 640 && dirty[i].h == 144) z5 = true;
    CHECK(z5);

    /* l'avvio è a tutto schermo */
    m.layer.base = BASE_BOOT;
    m.boot.t_ms = 1500;
    n = ui_flip_render(&sa, &m, &fa, dirty, UI_FLIP_MAX_DIRTY);
    CHECK_EQ(n, 1);
    CHECK_EQ(dirty[0].w, UI_FLIP_W);

    /* cartellino di Linneo */
    CHECK(strcmp(ui_fmt_linnaeus(3), "TRIANDRIA") == 0);
    CHECK(strcmp(ui_fmt_linnaeus(4), "TETRANDRIA") == 0);
    CHECK(strcmp(ui_fmt_linnaeus(1), "MONANDRIA") == 0);
    CHECK(strcmp(ui_fmt_linnaeus(0), "") == 0);
}
