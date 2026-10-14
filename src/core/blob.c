/* blob.c — contenitore dei salvataggi: intestazione, campi little-endian e CRC-32 (PLT-065). */
#include "blob.h"

static const char MAGIC[BLOB_KIND_COUNT][4] STAME_ROM = { { 'S', 'T', 'M', '1' }, { 'S', 'T', 'P', '1' }, { 'S', 'T', 'L', '1' } };

/* CRC-32 riflesso, polinomio 0xEDB88320, una tabella da 16 voci (mezzo byte alla volta) */
static const uint32_t CRC_NIBBLE[16] STAME_ROM = {
    0x00000000u, 0x1DB71064u, 0x3B6E20C8u, 0x26D930ACu, 0x76DC4190u, 0x6B6B51F4u, 0x4DB26158u, 0x5005713Cu,
    0xEDB88320u, 0xF00F9344u, 0xD6D6A3E8u, 0xCB61B38Cu, 0x9B64C2B0u, 0x86D3D2D4u, 0xA00AE278u, 0xBDBDF21Cu,
};

uint32_t blob_crc32(uint32_t crc, const void *p, size_t n)
{
    const uint8_t *b = (const uint8_t *)p;
    crc = ~crc;
    for (size_t i = 0; i < n; i++) {
        crc ^= b[i];
        crc = (crc >> 4) ^ CRC_NIBBLE[crc & 15u];
        crc = (crc >> 4) ^ CRC_NIBBLE[crc & 15u];
    }
    return ~crc;
}

static void put_le(uint8_t *d, uint32_t v, int bytes)
{
    for (int i = 0; i < bytes; i++) d[i] = (uint8_t)(v >> (8 * i));
}

static uint32_t get_le(const uint8_t *s, int bytes)
{
    uint32_t v = 0;
    for (int i = 0; i < bytes; i++) v |= (uint32_t)s[i] << (8 * i);
    return v;
}

/* ------------------------------------------------------------ scrittura */

static void w_put(blob_w_t *w, uint32_t v, int bytes)
{
    if (w->over || w->n + (size_t)bytes > w->max) { w->over = true; return; }
    put_le(w->buf + w->n, v, bytes);
    w->n += (size_t)bytes;
}

void blob_w_begin(blob_w_t *w, uint8_t *buf, size_t max, blob_kind_t kind, uint16_t version)
{
    w->buf = buf;
    w->max = max >= 4 ? max - 4 : 0;                  /* il CRC in coda ha sempre posto */
    w->n = 0;
    w->over = max < BLOB_OVERHEAD || (unsigned)kind >= BLOB_KIND_COUNT;
    if (w->over) return;
    memcpy(buf, MAGIC[kind], 4);
    w->n = 4;
    w_put(w, version, 2);
    w_put(w, 0, 4);                                   /* lunghezza: la scrive blob_w_end */
}

void blob_w_u8(blob_w_t *w, uint8_t v)   { w_put(w, v, 1); }
void blob_w_u16(blob_w_t *w, uint16_t v) { w_put(w, v, 2); }
void blob_w_u32(blob_w_t *w, uint32_t v) { w_put(w, v, 4); }

void blob_w_bytes(blob_w_t *w, const void *p, size_t n)
{
    if (w->over || w->n + n > w->max) { w->over = true; return; }
    memcpy(w->buf + w->n, p, n);
    w->n += n;
}

uint8_t *blob_w_room(blob_w_t *w, size_t *room)
{
    *room = w->over ? 0 : w->max - w->n;
    return w->buf + w->n;
}

void blob_w_skip(blob_w_t *w, size_t n)
{
    if (w->over || w->n + n > w->max) { w->over = true; return; }
    w->n += n;
}

size_t blob_w_end(blob_w_t *w)
{
    if (w->over) return 0;
    put_le(w->buf + 6, (uint32_t)(w->n - BLOB_HEAD), 4);
    put_le(w->buf + w->n, blob_crc32(0, w->buf, w->n), 4);
    return w->n + 4;
}

/* ------------------------------------------------------------- lettura */

blob_err_t blob_r_open(blob_r_t *r, const uint8_t *buf, size_t n, blob_kind_t kind)
{
    memset(r, 0, sizeof *r);
    if (n < BLOB_OVERHEAD) return BLOB_E_SHORT;
    if ((unsigned)kind >= BLOB_KIND_COUNT || memcmp(buf, MAGIC[kind], 4) != 0) return BLOB_E_MAGIC;
    uint32_t len = get_le(buf + 6, 4);
    if (len != n - BLOB_OVERHEAD) return BLOB_E_LENGTH;
    if (blob_crc32(0, buf, BLOB_HEAD + len) != get_le(buf + BLOB_HEAD + len, 4)) return BLOB_E_CRC;
    r->p = buf + BLOB_HEAD;
    r->n = len;
    r->version = (uint16_t)get_le(buf + 4, 2);
    return BLOB_OK;
}

static uint32_t r_get(blob_r_t *r, int bytes, uint32_t def)
{
    if (r->pos + (uint32_t)bytes > r->n) { r->pos = r->n; return def; }
    uint32_t v = get_le(r->p + r->pos, bytes);
    r->pos += (uint32_t)bytes;
    return v;
}

uint8_t  blob_r_u8(blob_r_t *r, uint8_t def)   { return (uint8_t)r_get(r, 1, def); }
uint16_t blob_r_u16(blob_r_t *r, uint16_t def) { return (uint16_t)r_get(r, 2, def); }
uint32_t blob_r_u32(blob_r_t *r, uint32_t def) { return r_get(r, 4, def); }

bool blob_r_bytes(blob_r_t *r, void *dst, size_t n)
{
    if (n > r->n - r->pos) { r->pos = r->n; return false; }
    memcpy(dst, r->p + r->pos, n);
    r->pos += (uint32_t)n;
    return true;
}
