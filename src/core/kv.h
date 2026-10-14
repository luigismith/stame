/* kv.h — righe chiave=valore per impostazioni e stato (sezione 50, PLT-066).
 *
 * UTF-8, fine riga LF. In lettura le chiavi sconosciute si ignorano e quelle mancanti restano al
 * default, così un file vecchio resta leggibile; si tollerano anche CR finali, spazi attorno a '=',
 * righe di commento che cominciano con '#' e commenti in coda al valore, se il '#' segue uno spazio
 * o un tab (come in piattaforma.txt, §9.2). Niente printf: i numeri li scrive kv_w_int. I valori
 * scritti non devono contenere '\n'.
 */
#ifndef STAME_KV_H
#define STAME_KV_H

#include "stame_base.h"

/* I due file di testo del nucleo (sezione 50 §9.1): ogni modulo scrive le sue chiavi nel file giusto. */
typedef enum { KV_IMPOSTAZIONI, KV_STATO } kv_file_t;

typedef struct {
    char  *buf;
    size_t max, n;
    bool   over;            /* il testo non stava in max */
} kv_w_t;

void   kv_w_begin(kv_w_t *w, char *buf, size_t max);
void   kv_w_int(kv_w_t *w, const char *key, int32_t v);
void   kv_w_str(kv_w_t *w, const char *key, const char *v);
/* Ritorna i byte scritti (senza terminatore), 0 se il testo non stava in max. */
size_t kv_w_end(const kv_w_t *w);

typedef struct {
    const char *p;
    size_t n, pos;
} kv_r_t;

typedef struct {
    const char *key, *val;  /* puntano nel testo, non sono terminati */
    size_t klen, vlen;
} kv_pair_t;

void kv_r_begin(kv_r_t *r, const char *txt, size_t n);
/* Prossima riga chiave=valore; salta righe vuote, commenti e righe senza '='. */
bool kv_r_next(kv_r_t *r, kv_pair_t *kv);
bool kv_key_is(const kv_pair_t *kv, const char *name);
/* Intero decimale con segno opzionale; false se il valore non è un numero o esce da int32_t. */
bool kv_val_int(const kv_pair_t *kv, int32_t *out);

#endif
