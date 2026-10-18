/* inc.h — file .inc dell'editor dell'originale (specifica 20, §2.5). */
#ifndef STAME_DSP_INC_H
#define STAME_DSP_INC_H
#include "patch.h"

#define SND_INC_SIZE 3414    /* dimensione esatta di un .inc scritto (SND-120) */

/* scrive la patch in out (al massimo max byte); restituisce la lunghezza, 3414 */
size_t snd_inc_write(const uint8_t p[DSP_NPAR], char *out, size_t max);
/* legge un .inc in modo tollerante (SND-121): 0 = ok, −1 formato, −2 indice incoerente, −3 righe mancanti */
int snd_inc_read(const char *txt, size_t n, uint8_t p[DSP_NPAR]);

#endif
