/* perf.h — la performance sul treble (specifica 10, §9; ACC-160…183).
 *
 * Riceve la voicing treble del gesto (le note che il motore degli accordi suonerebbe a blocco) e
 * la trasforma secondo il modo: strum, strum su 2 ottave, slop, arpeggio, arpeggio su 2 ottave,
 * pattern, harp. Lavora in tick (96 per semiminima, ACC-200); gli eventi futuri stanno in una coda
 * statica ordinata (ACC-183). Il basso non passa di qui (ACC-142). C11 puro, niente heap.
 */
#ifndef STAME_PERF_H
#define STAME_PERF_H
#include "stame_base.h"

/* modi, nell'ordine di ACC-160 (uguali a PERF_* di ui_model.h) */
enum { PM_OFF, PM_STRUM, PM_STRUM2, PM_SLOP, PM_ARP, PM_ARP2, PM_PATTERN, PM_HARP, PM_COUNT };

#define PERF_SCHED_MAX 64
#define PERF_MAX_NOTES 24       /* 8 note della voicing per 3 ottave (HARP) */

typedef struct { uint32_t tick; uint8_t note, vel, on; } perf_ev_t;

typedef struct {
    uint8_t  mode, amount;              /* del gesto in corso */
    uint8_t  next_mode, next_amount;    /* PERF_SET: valgono dal prossimo KEY_DOWN (ACC-182) */
    uint8_t  n, notes[8], vel;          /* voicing treble crescente (ACC-165) */
    uint8_t  active;                    /* arpeggio o pattern in corso */
    uint32_t step, next;                /* passo e tick del prossimo passo */
    perf_ev_t q[PERF_SCHED_MAX];        /* eventi futuri, ordinati per tick */
    uint8_t  qn;
    uint8_t  out_on[16];                /* note accese in uscita */
    uint32_t rng;                       /* xorshift32 dello slop (ACC-170) */
    uint32_t dropped;                   /* eventi scartati a coda piena (ACC-183) */
} perf_t;

void perf_init(perf_t *p, uint32_t seed);
/* PERF_SET (ACC-162): modo e amount per i prossimi gesti */
void perf_set(perf_t *p, uint8_t mode, uint8_t amount);
/* nuova voicing al tick t. key_down = nuovo gesto (KEY_DOWN); legato = nuovo tasto premuto prima di
 * rilasciare il precedente (ACC-173); altrimenti è un ri-attacco dello stesso tasto (ACC-179). */
int  perf_chord(perf_t *p, uint32_t tick, const uint8_t *notes, uint8_t n, uint8_t vel, bool key_down,
                bool legato, perf_ev_t *out, int max);
/* KEY_UP del tasto attivo: tutto spento, eventi futuri cancellati (ACC-181) */
int  perf_release(perf_t *p, uint32_t tick, perf_ev_t *out, int max);
/* eventi con tick ≤ tick: chiamata a ogni tick */
int  perf_run(perf_t *p, uint32_t tick, perf_ev_t *out, int max);

#endif
