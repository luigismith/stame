/* tema.c — palette Notte (VFD) e Giorno (LCD) della plancia (tema.h). */
#include "tema.h"
#include "../ui/ui_model.h"

const uf_theme_def_t UF_THEME[2] = {
    { {                         /* Notte: vetro VFD */
        0x050C0B,   /* bg */
        0x0A1614,   /* mesh */
        0x0A1715,   /* panel */
        0x1B302C,   /* line */
        0x10221F,   /* seg_off */
        0x123029,   /* bar */
        0x3F655D,   /* ghost */
        0xDDFBF1,   /* text */
        0xA99F86,   /* dim */
        0x3FE3CB,   /* treble: fosforo acqua */
        0xFFAE4A,   /* bass: filtro ambra */
        0xB996FF,   /* loop: filtro viola */
        0xA4F06A,   /* focus: verde lime */
        0xFFDD5E,   /* active: giallo */
        0xFF6156,   /* warn: rosso */
        0x183632,   /* kb_white */
        0x08110F,   /* kb_black */
        0x6FA597,   /* in_key */
    } },
    { {                         /* Giorno: LCD riflettente */
        0xCED4C2,   /* bg */
        0xC8CEBB,   /* mesh */
        0xD9DECE,   /* panel */
        0xA2AA95,   /* line */
        0xC1C8B4,   /* seg_off */
        0xB5BDA7,   /* bar */
        0x879180,   /* ghost */
        0x141B18,   /* text */
        0x424C47,   /* dim */
        0x005A51,   /* treble */
        0x853A00,   /* bass */
        0x4A2894,   /* loop */
        0x285C00,   /* focus */
        0x634A00,   /* active */
        0x9E160C,   /* warn */
        0xE3E7D8,   /* kb_white */
        0x252D29,   /* kb_black */
        0x424C47,   /* in_key */
    } },
};

void uf_pal_make(uf_pal_t *p, uint8_t theme)
{
    if (theme >= THEME_COUNT) theme = THEME_DARK;
    const uf_theme_def_t *t = &UF_THEME[theme];
    uint32_t bg = t->rgb[T_BG];
    for (int i = 0; i < T_COUNT; i++) {
        p->c[i] = gfx_565(t->rgb[i]);
        p->edge[i] = gfx_565(gfx_mix(t->rgb[i], bg, theme == THEME_DARK ? 110 : 70));
        p->soft[i] = gfx_565(gfx_mix(bg, t->rgb[i], 64));
    }
    p->theme = theme;
}
