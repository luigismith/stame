/* test.h — runner minimo dei test del nucleo (PLT-075): macro CHECK, nessuna libreria. */
#ifndef STAME_TEST_H
#define STAME_TEST_H

#include <stdio.h>

extern int test_checks, test_failures;
extern const char *test_suite;

#define CHECK(cond) do { \
    test_checks++; \
    if (!(cond)) { \
        test_failures++; \
        printf("FALLITO [%s] %s:%d: %s\n", test_suite, __FILE__, __LINE__, #cond); \
    } \
} while (0)

/* Come CHECK, con un messaggio formattato (es. l'ID del vettore di test). */
#define CHECKM(cond, ...) do { \
    test_checks++; \
    if (!(cond)) { \
        test_failures++; \
        printf("FALLITO [%s] %s:%d: %s — ", test_suite, __FILE__, __LINE__, #cond); \
        printf(__VA_ARGS__); \
        printf("\n"); \
    } \
} while (0)

#define CHECK_EQ(a, b) CHECKM((a) == (b), "%s = %ld, atteso %ld", #a, (long)(a), (long)(b))

#endif
