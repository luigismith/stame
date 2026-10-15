/* inc.c — file .inc di Pistil (specifica 20, §2.5; SND-120…122).
 *
 * Lavora su buffer in memoria: la lettura e la scrittura dei file sono della piattaforma.
 * Solo le funzioni di string.h ammesse da PLT-001.
 */
#include "inc.h"

static const char HEX[] = "0123456789ABCDEF";

static size_t put(char *out, size_t max, size_t n, const char *s, size_t len)
{
    for (size_t i = 0; i < len; i++) if (n + i < max) out[n + i] = s[i];
    return n + len;
}

static size_t cstrlen(const char *s)
{
    size_t n = 0;
    while (s[n]) n++;
    return n;
}

size_t snd_inc_write(const uint8_t p[DSP_NPAR], char *out, size_t max)
{
    size_t n = 0;
    for (int i = 0; i < DSP_NPAR; i++) {
        char num[4];
        int k = 0, v = i;
        char rev[4];
        do { rev[k++] = (char)('0' + v % 10); v /= 10; } while (v);
        for (int j = 0; j < k; j++) num[j] = rev[k - 1 - j];
        char hx[6] = { '0', 'x', HEX[p[i] >> 4 & 15], HEX[p[i] & 15], ',', '\t' };
        n = put(out, max, n, hx, 6);
        n = put(out, max, n, "//", 2);
        n = put(out, max, n, num, (size_t)k);
        n = put(out, max, n, " TREBLE_", 8);
        n = put(out, max, n, snd_par_name[i], cstrlen(snd_par_name[i]));
        if (i < DSP_NPAR - 1) n = put(out, max, n, "\r\n", 2);
    }
    return n;
}

static int hexval(char c)
{
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

static bool space(char c) { return c == ' ' || c == '\t'; }

int snd_inc_read(const char *txt, size_t n, uint8_t p[DSP_NPAR])
{
    uint8_t tmp[DSP_NPAR];
    int line = 0;
    size_t i = 0;
    while (i < n && line < DSP_NPAR) {
        size_t e = i;
        while (e < n && txt[e] != '\n') e++;
        size_t end = e;
        if (end > i && txt[end - 1] == '\r') end--;
        size_t k = i;
        while (k < end && space(txt[k])) k++;
        if (k == end) { i = e + 1; continue; }                    /* riga vuota */
        if (k + 4 > end || txt[k] != '0' || (txt[k + 1] != 'x' && txt[k + 1] != 'X')) return -1;
        int h1 = hexval(txt[k + 2]), h2 = hexval(txt[k + 3]);
        if (h1 < 0 || h2 < 0) return -1;
        k += 4;
        if (k < end && txt[k] == ',') k++;
        while (k < end && space(txt[k])) k++;
        if (k + 2 > end || txt[k] != '/' || txt[k + 1] != '/') return -1;
        k += 2;
        int idx = 0, digits = 0;
        while (k < end && txt[k] >= '0' && txt[k] <= '9') { idx = idx * 10 + (txt[k] - '0'); k++; digits++; }
        if (!digits || idx != line) return -2;                    /* indice incoerente: rifiutato */
        while (k < end && space(txt[k])) k++;
        static const char T[] = "TREBLE_", B[] = "BASS_";
        bool ok = false;
        if (end - k >= 7 && !memcmp(txt + k, T, 7)) { k += 7; ok = true; }
        else if (end - k >= 5 && !memcmp(txt + k, B, 5)) { k += 5; ok = true; }
        if (!ok) return -1;
        const char *name = snd_par_name[line];
        size_t len = cstrlen(name);
        if (end - k < len || memcmp(txt + k, name, len)) return -1;
        tmp[line++] = (uint8_t)(h1 * 16 + h2);
        i = e + 1;
    }
    if (line < DSP_NPAR) return -3;
    memcpy(p, tmp, DSP_NPAR);
    snd_patch_clamp(p);                                            /* SND-102 */
    return 0;
}
