/* ui/ui_fmt.h — testi derivati dai valori, uguali per tutti i renderer (UI-029).
 *
 * Ogni funzione scrive in buf (al massimo n byte, terminatore compreso) e ritorna buf.
 */
#ifndef STAME_UI_FMT_H
#define STAME_UI_FMT_H

#include "ui_model.h"

char *ui_fmt_int(char *buf, int n, int v, int digits);       /* zeri davanti: 7 -> "07" */
char *ui_fmt_signed(char *buf, int n, int v);                /* "+3", "0", "-3" */
char *ui_fmt_cat(char *buf, int n, const char *a, const char *b);
char *ui_fmt_copy(char *buf, int n, const char *s);
const char *ui_fmt_perf_short(uint8_t mode);                 /* UI-066 */
const char *ui_fmt_perf_long(uint8_t mode);
const char *ui_fmt_fx_abbr(uint8_t type);                    /* REV, CHO, ENS … */
const char *ui_fmt_fx_name(uint8_t type);
const char *ui_fmt_engine(uint8_t engine);                   /* VA, FM, RP */
const char *ui_fmt_view_short(uint8_t view);
const char *ui_fmt_play_style(uint8_t style);
/* drum machine (40 MIDI-135): suddivisione del Roll (il nome del kit lo scrive la piattaforma in tempo.kit_name) */
const char *ui_fmt_roll(uint8_t roll);
/* la figura del basso che rotola (10 ACC-219): Off, Offbeat, Rolling, Gallop, 8ths, 16ths */
const char *ui_fmt_bassline(uint8_t bl);
const char *ui_fmt_part(uint8_t part);
/* swing in tick (0 = «Off», poi 52%…75%, 10 ACC-216) e filtro della batteria (Off, LP 1…10, HP 1…10) */
const char *ui_fmt_swing(uint8_t ticks);
char *ui_fmt_filter(char *buf, int n, int filt);
/* Nome di Linneo del numero di classi di nota di un accordo: 3 -> "TRIANDRIA" (identità). */
const char *ui_fmt_linnaeus(int n_pcs);

#endif
