/* banco.h — carica il banco di campioni stame.smp da disco (specifica 20, §7b; 50, PLT-095).
 *
 * Codice di piattaforma: legge il file in un buffer suo (malloc, una volta, prima che l'audio parta)
 * e lo fa leggere al nucleo con smp_bank_parse. Il buffer resta in memoria per tutta la vita del
 * programma, perché il banco tiene puntatori dentro di esso.
 */
#ifndef STAME_BANCO_H
#define STAME_BANCO_H
#include "../../dsp/smp.h"

/* NULL se il file manca o non è un banco valido; il motivo va nel log del chiamante (banco_errore) */
const smp_bank_t *banco_carica(const char *path);
const char *banco_errore(void);
/* set, zone e byte del banco caricato, per il log */
void banco_info(const smp_bank_t *b, char *out, size_t n);

#endif
