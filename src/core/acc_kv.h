/* acc_kv.h — opzioni del motore degli accordi in righe chiave=valore (sezione 50 §9, PLT-066).
 *
 * Le voci di Options > Instrument e Options > Bass (UI-079) e le opzioni di compatibilità vanno in
 * impostazioni.txt; tonalità, transpose, basso acceso e voicing sono stato della sessione e vanno
 * in stato.txt (UI-111, UI-093). I valori sono gli indici degli enum di acc.h; in lettura passano
 * da ACC_IN_OPTION_SET, che li riporta nei limiti.
 */
#ifndef STAME_ACC_KV_H
#define STAME_ACC_KV_H

#include "acc.h"
#include "kv.h"

/* Scrive le chiavi del motore degli accordi che stanno nel file dato. */
void acc_kv_save(const acc_state *s, kv_w_t *w, kv_file_t file);

/* Applica una riga letta: true se la chiave è del motore degli accordi e il valore è un intero.
 * Le chiavi degli altri moduli si lasciano a loro; un valore non numerico lascia il default. */
bool acc_kv_apply(acc_state *s, const kv_pair_t *kv);

#endif
