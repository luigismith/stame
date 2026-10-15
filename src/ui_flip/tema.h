/* ui_flip/tema.h — i due temi della plancia e i colori derivati (UI-128, identità visiva).
 *
 * Notte (default): un display a fluorescenza (VFD) degli anni Settanta. Vetro nero appena verde,
 * fosfori che si accendono, segmenti spenti ancora visibili.
 * Giorno: un LCD riflettente. Fondo grigio-verde, inchiostri scuri, stessi ruoli e stesse forme.
 * I valori e le soglie di contrasto sono in docs/identita/README.md e in tests/unit/test_tema.c.
 */
#ifndef STAME_UF_TEMA_H
#define STAME_UF_TEMA_H

#include "../gfx/gfx.h"

typedef enum {
    T_BG,        /* vetro / fondo */
    T_MESH,      /* punti della maglia del vetro */
    T_PANEL,     /* fondo delle intestazioni e delle liste */
    T_LINE,      /* separatori e contorni */
    T_SEGOFF,    /* segmenti e punti spenti */
    T_BAR,       /* barre di valore, traccia del progresso */
    T_GHOST,     /* ultimo accordo, dopo la persistenza; legende dei controlli */
    T_TEXT,      /* valori accesi */
    T_DIM,       /* scritte stampate sul vetro: titoli, unità */
    T_TREBLE,    /* note treble, nome dell'accordo, finestra del voicing */
    T_BASS,      /* basso */
    T_LOOP,      /* looper */
    T_FOCUS,     /* fuoco, selezione, primo movimento */
    T_ACTIVE,    /* evidenze, transpose, LOCK */
    T_WARN,      /* registrazione, clip, avvisi */
    T_KBW,       /* tasti bianchi spenti */
    T_KBB,       /* tasti neri spenti */
    T_INKEY,     /* granelli di polline: note della tonalità */
    T_COUNT
} uf_tok_t;

typedef struct { uint32_t rgb[T_COUNT]; } uf_theme_def_t;

extern const uf_theme_def_t UF_THEME[2];      /* THEME_DARK (Notte), THEME_LIGHT (Giorno) */

typedef struct {
    gfx_c c[T_COUNT];        /* colori pieni */
    gfx_c edge[T_COUNT];     /* bordo dei punti accesi: colore mescolato con il fondo */
    gfx_c soft[T_COUNT];     /* colore mescolato al 25% con il fondo: aloni e fondi tenui */
    uint8_t theme;
} uf_pal_t;

void uf_pal_make(uf_pal_t *p, uint8_t theme);

#endif
