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
/* Nome di Linneo del numero di classi di nota di un accordo: 3 -> "TRIANDRIA" (identità). */
const char *ui_fmt_linnaeus(int n_pcs);

#endif
