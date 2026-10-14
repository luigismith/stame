/* stame_base.h — base comune dei moduli portabili (core, dsp, ui, gfx, ui_flip).
 *
 * Ogni file .c di questi moduli DEVE includerlo (PLT-002). Contiene solo gli
 * header ammessi da PLT-001 e avvelena i simboli vietati, così un uso di heap,
 * I/O, orologio o rand() blocca la compilazione.
 *
 * Il codice di prova e di piattaforma, che include gli header del nucleo ma usa
 * printf e malloc, si compila con -DSTAME_HOST: niente veleno, il resto uguale.
 */
#ifndef STAME_BASE_H
#define STAME_BASE_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <string.h>
#include <limits.h>

/* Tabelle costanti: vuota sulla Flip, PROGMEM sul Teensy (PLT-099). */
#ifndef STAME_ROM
#define STAME_ROM
#endif

#define STAME_COUNT(a) (sizeof(a) / sizeof((a)[0]))

#if !defined(STAME_HOST) && (defined(__GNUC__) || defined(__clang__))
#pragma GCC poison malloc calloc realloc free printf fprintf sprintf fopen rand srand time
#endif

#endif
