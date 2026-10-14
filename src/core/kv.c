/* kv.c — scrittura e lettura delle righe chiave=valore (PLT-066). */
#include "kv.h"

/* ------------------------------------------------------------ scrittura */

static void put(kv_w_t *w, const char *s, size_t n)
{
    if (w->over || w->n + n > w->max) { w->over = true; return; }
    memcpy(w->buf + w->n, s, n);
    w->n += n;
}

static void put_line_start(kv_w_t *w, const char *key)
{
    put(w, key, strlen(key));
    put(w, "=", 1);
}

void kv_w_begin(kv_w_t *w, char *buf, size_t max)
{
    w->buf = buf;
    w->max = max;
    w->n = 0;
    w->over = false;
}

void kv_w_int(kv_w_t *w, const char *key, int32_t v)
{
    char digits[11];
    int n = 0;
    uint32_t u = v < 0 ? 0u - (uint32_t)v : (uint32_t)v;      /* regge anche INT32_MIN */
    do { digits[n++] = (char)('0' + u % 10u); u /= 10u; } while (u);
    put_line_start(w, key);
    if (v < 0) put(w, "-", 1);
    while (n) put(w, &digits[--n], 1);
    put(w, "\n", 1);
}

void kv_w_str(kv_w_t *w, const char *key, const char *v)
{
    put_line_start(w, key);
    put(w, v, strlen(v));
    put(w, "\n", 1);
}

size_t kv_w_end(const kv_w_t *w)
{
    return w->over ? 0 : w->n;
}

/* ------------------------------------------------------------- lettura */

static bool is_space(char c) { return c == ' ' || c == '\t' || c == '\r'; }

static void trim(const char **s, size_t *n)
{
    while (*n && is_space(**s)) { (*s)++; (*n)--; }
    while (*n && is_space((*s)[*n - 1])) (*n)--;
}

void kv_r_begin(kv_r_t *r, const char *txt, size_t n)
{
    r->p = txt;
    r->n = n;
    r->pos = 0;
}

bool kv_r_next(kv_r_t *r, kv_pair_t *kv)
{
    while (r->pos < r->n) {
        const char *line = r->p + r->pos;
        size_t len = 0;
        while (r->pos + len < r->n && line[len] != '\n') len++;
        r->pos += len + (r->pos + len < r->n);                    /* salta anche il '\n' */

        trim(&line, &len);
        if (len == 0 || line[0] == '#') continue;
        size_t eq = 0;
        while (eq < len && line[eq] != '=') eq++;
        if (eq == len) continue;                                  /* riga senza '=' */
        kv->key = line;
        kv->klen = eq;
        kv->val = line + eq + 1;
        kv->vlen = len - eq - 1;
        for (size_t i = 1; i < kv->vlen; i++)                     /* commento in coda: " # …" */
            if (kv->val[i] == '#' && (kv->val[i - 1] == ' ' || kv->val[i - 1] == '\t')) { kv->vlen = i; break; }
        trim(&kv->key, &kv->klen);
        trim(&kv->val, &kv->vlen);
        if (kv->klen) return true;
    }
    return false;
}

bool kv_key_is(const kv_pair_t *kv, const char *name)
{
    size_t n = strlen(name);
    return kv->klen == n && memcmp(kv->key, name, n) == 0;
}

bool kv_val_int(const kv_pair_t *kv, int32_t *out)
{
    const char *s = kv->val;
    size_t n = kv->vlen, i = 0;
    bool neg = false;
    if (i < n && (s[i] == '-' || s[i] == '+')) neg = s[i++] == '-';
    if (i == n) return false;
    int64_t v = 0;
    for (; i < n; i++) {
        if (s[i] < '0' || s[i] > '9') return false;
        v = v * 10 + (s[i] - '0');
        if (v > (int64_t)INT32_MAX + 1) return false;
    }
    if (neg) v = -v;
    if (v > INT32_MAX || v < INT32_MIN) return false;
    *out = (int32_t)v;
    return true;
}
