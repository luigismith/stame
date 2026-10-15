/* test_gfx.c — primitive di disegno, UTF-8, font, Matrice, sette segmenti (UI-144, UI-160). */
#include "test.h"
#include "gfx/gfx.h"

static uint16_t px[64 * 48];

static int count(uint16_t c)
{
    int n = 0;
    for (int i = 0; i < 64 * 48; i++) n += px[i] == c;
    return n;
}

void test_gfx(void)
{
    gfx_fb16_t fb;
    gfx_fb_init(&fb, px, 64, 48, 64);

    /* colori: 565 e mescolanza */
    CHECK_EQ(gfx_565(0xFFFFFF), 0xFFFF);
    CHECK_EQ(gfx_565(0xFF0000), 0xF800);
    CHECK_EQ(gfx_mix(0x000000, 0xFFFFFF, 0), 0x000000);
    CHECK_EQ(gfx_mix(0x000000, 0xFFFFFF, 256), 0xFFFFFF);
    CHECK_EQ(gfx_mix(0x000000, 0xC8C8C8, 128), 0x646464);

    /* riempimento e ritaglio */
    gfx_fill(&fb, 0, 0, 64, 48, 0);
    gfx_fill(&fb, -10, -10, 20, 20, 1);
    CHECK_EQ(count(1), 100);
    gfx_clip(&fb, 30, 30, 10, 10);
    gfx_fill(&fb, 0, 0, 64, 48, 2);
    CHECK_EQ(count(2), 100);
    gfx_clip_all(&fb);

    /* poligono: un quadrato 8×8 allineato ai pixel accende 64 pixel */
    gfx_fill(&fb, 0, 0, 64, 48, 0);
    int32_t sq[8] = { 8 * 16, 8 * 16, 16 * 16, 8 * 16, 16 * 16, 16 * 16, 8 * 16, 16 * 16 };
    gfx_poly(&fb, sq, 4, 3);
    CHECK_EQ(count(3), 64);
    /* disco di raggio 10: area vicina a pi * r^2 = 314 */
    gfx_fill(&fb, 0, 0, 64, 48, 0);
    gfx_disc(&fb, 32 * 16, 24 * 16, 10 * 16, 4);
    int a = count(4);
    CHECKM(a > 290 && a < 340, "area del disco %d", a);

    /* UTF-8 */
    const char *s = "F\xE2\x99\xAF" "m";
    CHECK_EQ(gfx_utf8(&s), 'F');
    CHECK_EQ(gfx_utf8(&s), 0x266F);
    CHECK_EQ(gfx_utf8(&s), 'm');
    CHECK_EQ(gfx_utf8(&s), 0);
    const char *bad = "\xE2\x28";
    CHECK_EQ(gfx_utf8(&bad), '?');
    CHECK_EQ(gfx_text_len("C\xE2\x99\xAF" "4"), 3);

    /* font: Spleen ha le lettere, i simboli di Stame hanno il diesis */
    CHECK(gfx_font_glyph(&GFX_FONT_8X16, 'A') != NULL);
    CHECK(gfx_font_glyph(&GFX_FONT_8X16, 0x266F) == NULL);
    CHECK(gfx_font_glyph(&GFX_SIMB_8X16, 0x266F) != NULL);
    CHECK(gfx_font_glyph(&GFX_SIMB_12X24, 0x2014) != NULL);
    CHECK_EQ(gfx_text_w(&GFX_S, "BPM", 0), 24);
    CHECK_EQ(gfx_text_w(&GFX_XS, "BPM", 1), 20);

    /* il testo disegna qualcosa e il carattere sconosciuto diventa '?' */
    gfx_fill(&fb, 0, 0, 64, 48, 0);
    int x = gfx_text(&fb, &GFX_S, 0, 0, "A\xE2\x99\xAF", 5);
    CHECK_EQ(x, 16);
    CHECK(count(5) > 20);

    /* Matrice: larghezze (5 colonne + stacco) e punti accesi */
    CHECK_EQ(gfx_matrix_w("C", 12), 60);
    CHECK_EQ(gfx_matrix_w("CD", 2), 22);
    CHECK_EQ(gfx_matrix_w("i", 4), 12);
    CHECK(gfx_mfont_glyph(&GFX_MATRICE, 0x266D) != NULL);
    gfx_fill(&fb, 0, 0, 64, 48, 0);
    gfx_dots_t d = { 6, 7, 8, false };
    gfx_matrix(&fb, 0, 40, 4, "I", &d);
    CHECK(count(6) + count(7) > 0);
    CHECK_EQ(count(8), 0);
    d.ghost = true;
    gfx_matrix(&fb, 20, 40, 4, "I", &d);
    CHECK(count(8) > 0);

    /* sette segmenti: larghezza e segmenti spenti visibili */
    CHECK(gfx_seg7_w(30, "120") > gfx_seg7_w(30, "12"));
    gfx_fill(&fb, 0, 0, 64, 48, 0);
    gfx_seg_t sg = { 9, 10, true };
    gfx_seg7(&fb, 2, 2, 30, "1", &sg);
    CHECK(count(9) > 0);
    CHECK(count(10) > count(9));
}
