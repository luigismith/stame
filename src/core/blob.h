/* blob.h — contenitore dei salvataggi (sezione 50, PLT-065, PLT-068).
 *
 *    0   magia, 4 byte: STM1 impostazioni e stato, STP1 preset, STL1 loop
 *    4   versione del contenuto, u16
 *    6   lunghezza del contenuto n, u32
 *   10   contenuto
 * 10+n   CRC-32 (IEEE 802.3, come zlib) dei 10+n byte precedenti, u32
 *
 * Campi multibyte little-endian, scritti byte per byte: niente struct copiate in blocco, così il
 * formato è lo stesso sulla Flip e sul Teensy. Le letture oltre la fine del contenuto danno il
 * default: un blob di una versione vecchia, con meno campi, resta leggibile.
 */
#ifndef STAME_BLOB_H
#define STAME_BLOB_H

#include "stame_base.h"

typedef enum { BLOB_SETTINGS, BLOB_PRESET, BLOB_LOOP, BLOB_KIND_COUNT } blob_kind_t;

typedef enum {
    BLOB_OK,
    BLOB_E_SHORT,       /* meno byte dell'intestazione e del CRC */
    BLOB_E_MAGIC,       /* magia sconosciuta o di un altro tipo */
    BLOB_E_LENGTH,      /* la lunghezza dichiarata non torna con i byte ricevuti */
    BLOB_E_CRC          /* CRC errato */
} blob_err_t;

#define BLOB_HEAD     10u
#define BLOB_OVERHEAD 14u   /* intestazione + CRC */

/* CRC-32 incrementale: crc = 0 all'inizio, poi si passa il valore restituito.
 * blob_crc32(0, "123456789", 9) = 0xCBF43926. */
uint32_t blob_crc32(uint32_t crc, const void *p, size_t n);

/* ------------------------------------------------------------ scrittura */
typedef struct {
    uint8_t *buf;
    size_t   max, n;
    bool     over;          /* il contenuto non stava in max */
} blob_w_t;

void   blob_w_begin(blob_w_t *w, uint8_t *buf, size_t max, blob_kind_t kind, uint16_t version);
void   blob_w_u8(blob_w_t *w, uint8_t v);
void   blob_w_u16(blob_w_t *w, uint16_t v);
void   blob_w_u32(blob_w_t *w, uint32_t v);
void   blob_w_bytes(blob_w_t *w, const void *p, size_t n);
/* Per chi scrive il contenuto da sé, senza copie (per esempio il testo chiave=valore): ritorna dove
 * scrivere e in *room quanti byte ci stanno; poi blob_w_skip conta i byte scritti. */
uint8_t *blob_w_room(blob_w_t *w, size_t *room);
void   blob_w_skip(blob_w_t *w, size_t n);
/* Scrive lunghezza e CRC; ritorna i byte totali del blob, 0 se non stava in max. */
size_t blob_w_end(blob_w_t *w);

/* ------------------------------------------------------------- lettura */
typedef struct {
    const uint8_t *p;       /* contenuto */
    uint32_t n, pos;
    uint16_t version;
} blob_r_t;

/* Controlla magia, lunghezza e CRC. Con un errore il file va rinominato in .bad e si usano i
 * default (PLT-068): lo fa il chiamante. */
blob_err_t blob_r_open(blob_r_t *r, const uint8_t *buf, size_t n, blob_kind_t kind);
uint8_t    blob_r_u8(blob_r_t *r, uint8_t def);
uint16_t   blob_r_u16(blob_r_t *r, uint16_t def);
uint32_t   blob_r_u32(blob_r_t *r, uint32_t def);
/* Copia n byte; false, con dst intatto, se il contenuto finisce prima. */
bool       blob_r_bytes(blob_r_t *r, void *dst, size_t n);

#endif
