/* string.h minimo per la compilazione di prova freestanding Cortex-M7 (PLT-107).
 * Solo le funzioni ammesse da PLT-001. */
#ifndef STAME_SHIM_STRING_H
#define STAME_SHIM_STRING_H

#include <stddef.h>

void *memcpy(void *dst, const void *src, size_t n);
void *memmove(void *dst, const void *src, size_t n);
void *memset(void *dst, int c, size_t n);
int   memcmp(const void *a, const void *b, size_t n);
size_t strlen(const char *s);

#endif
