/* smp.h — banco di campioni e voce campionata: il modello SMP (specifica 20, §7b; SND-370…379).
 *
 * Il banco è un blob in sola lettura (file stame.smp, formato in §7b.2) che la piattaforma carica in
 * memoria fuori dal percorso audio, o che sta in flash. Qui lo si legge soltanto: C11, niente heap,
 * niente I/O. I campioni sono int16 mono little-endian, allineati a 2 byte.
 */
#ifndef STAME_DSP_SMP_H
#define STAME_DSP_SMP_H
#include "../core/stame_base.h"

#define SMP_SETS_MAX  64
#define SMP_ZONES_MAX 640
#define SMP_NAME      24
#define SMP_HEADER    20
#define SMP_SET_REC   32
#define SMP_ZONE_REC  32
#define SMP_VERSION   1
#define SMP_LOOP_MIN  16            /* loop più corti si rifiutano: il passo di lettura arriva a 16 (SND-374) */

typedef struct {
    const int16_t *data;            /* campioni mono */
    uint32_t len;                   /* in campioni, ≥ 4 */
    uint32_t loop_start, loop_end;  /* loop_end > loop_start: da loop_end si torna a loop_start; loop_end 0 = one-shot */
    uint32_t rate;                  /* Hz di registrazione */
    float    gain;                  /* lineare */
    uint8_t  root, lo, hi, vel_lo;  /* nota di registrazione, note coperte, velocity minima del layer */
} smp_zone_t;

typedef struct {
    char     name[SMP_NAME];        /* terminato da 0 */
    uint16_t first, n;              /* zone del set, consecutive in bank->zones */
    uint16_t flags;                 /* bit 0: zone con loop */
} smp_set_t;

typedef struct {
    uint16_t   n_sets, n_zones;
    smp_set_t  sets[SMP_SETS_MAX];
    smp_zone_t zones[SMP_ZONES_MAX];
} smp_bank_t;

/* Legge il blob: false se non è un banco valido (e il banco resta vuoto). I puntatori delle zone
 * entrano nel blob, che deve restare in memoria finché il banco è in uso. */
bool smp_bank_parse(smp_bank_t *b, const void *blob, size_t n);
const smp_set_t *smp_set_find(const smp_bank_t *b, const char *name);
/* set per indice; NULL se fuori dal banco */
const smp_set_t *smp_set_at(const smp_bank_t *b, int idx);
/* la zona del set che copre la nota (per i kit: lo strumento) con il layer di velocity più alto
 * che non supera vel; NULL se nessuna la copre */
const smp_zone_t *smp_zone_for(const smp_bank_t *b, const smp_set_t *s, int note, int vel);

#endif
