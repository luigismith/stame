/* spsc.h — coda lock-free a un produttore e un consumatore (PLT-015, PLT-016, PLT-105).
 *
 * Capienza potenza di 2, elementi di dimensione fissa, indici _Atomic uint32_t
 * con ordinamento acquire/release. Funziona tra thread e, sul Teensy, tra un
 * interrupt e loop(). A coda piena il produttore scarta e conta (mai attese).
 *
 * La memoria degli elementi la passa il chiamante:
 *     static my_ev_t buf[256];
 *     static spsc_t q;
 *     spsc_init(&q, buf, sizeof buf[0], 256);
 */
#ifndef STAME_SPSC_H
#define STAME_SPSC_H

#include "stame_base.h"
#include <stdatomic.h>

typedef struct {
    _Atomic uint32_t head;      /* scritto solo dal produttore */
    _Atomic uint32_t tail;      /* scritto solo dal consumatore */
    _Atomic uint32_t dropped;   /* elementi scartati a coda piena */
    uint8_t *buf;
    uint32_t elem_size;
    uint32_t mask;              /* capienza - 1 */
} spsc_t;

/* cap DEVE essere una potenza di 2; ritorna false altrimenti. */
static inline bool spsc_init(spsc_t *q, void *buf, uint32_t elem_size, uint32_t cap)
{
    if (cap == 0 || (cap & (cap - 1)) != 0 || elem_size == 0) return false;
    atomic_init(&q->head, 0u);
    atomic_init(&q->tail, 0u);
    atomic_init(&q->dropped, 0u);
    q->buf = (uint8_t *)buf;
    q->elem_size = elem_size;
    q->mask = cap - 1;
    return true;
}

/* Solo produttore. false = coda piena, elemento scartato e contato. */
static inline bool spsc_push(spsc_t *q, const void *elem)
{
    uint32_t h = atomic_load_explicit(&q->head, memory_order_relaxed);
    uint32_t t = atomic_load_explicit(&q->tail, memory_order_acquire);
    if (h - t > q->mask) {
        atomic_fetch_add_explicit(&q->dropped, 1u, memory_order_relaxed);
        return false;
    }
    memcpy(q->buf + (size_t)(h & q->mask) * q->elem_size, elem, q->elem_size);
    atomic_store_explicit(&q->head, h + 1u, memory_order_release);
    return true;
}

/* Solo consumatore. false = coda vuota. */
static inline bool spsc_pop(spsc_t *q, void *elem)
{
    uint32_t t = atomic_load_explicit(&q->tail, memory_order_relaxed);
    uint32_t h = atomic_load_explicit(&q->head, memory_order_acquire);
    if (h == t) return false;
    memcpy(elem, q->buf + (size_t)(t & q->mask) * q->elem_size, q->elem_size);
    atomic_store_explicit(&q->tail, t + 1u, memory_order_release);
    return true;
}

/* Numero di elementi presenti: esatto solo dal produttore o dal consumatore. */
static inline uint32_t spsc_count(spsc_t *q)
{
    uint32_t h = atomic_load_explicit(&q->head, memory_order_acquire);
    uint32_t t = atomic_load_explicit(&q->tail, memory_order_acquire);
    return h - t;
}

static inline uint32_t spsc_dropped(spsc_t *q)
{
    return atomic_load_explicit(&q->dropped, memory_order_relaxed);
}

#endif
