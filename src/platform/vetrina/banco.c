/* banco.c — lettura del file stame.smp (banco.h). */
#include <stdio.h>
#include <stdlib.h>
#include "banco.h"

static smp_bank_t banco;
static uint8_t *blob;
static size_t blob_n;
static const char *errore = "";

const char *banco_errore(void) { return errore; }

const smp_bank_t *banco_carica(const char *path)
{
    FILE *f = fopen(path, "rb");
    if (!f) { errore = "file assente"; return NULL; }
    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); errore = "file illeggibile"; return NULL; }
    long n = ftell(f);
    if (n < SMP_HEADER || n > 256L * 1024 * 1024) { fclose(f); errore = "dimensione fuori misura"; return NULL; }
    fseek(f, 0, SEEK_SET);
    free(blob);
    blob = malloc((size_t)n + 2u);                  /* +2: resta allineato a 2 byte anche a dispari */
    if (!blob) { fclose(f); errore = "memoria"; return NULL; }
    size_t got = fread(blob, 1, (size_t)n, f);
    fclose(f);
    if (got != (size_t)n) { errore = "lettura incompleta"; return NULL; }
    blob_n = got;
    if (!smp_bank_parse(&banco, blob, blob_n)) { errore = "formato non valido"; return NULL; }
    errore = "";
    return &banco;
}

void banco_info(const smp_bank_t *b, char *out, size_t n)
{
    if (!b) { snprintf(out, n, "nessun banco"); return; }
    snprintf(out, n, "%u set, %u zone, %.1f MB", (unsigned)b->n_sets, (unsigned)b->n_zones, (double)blob_n / 1048576.0);
}
