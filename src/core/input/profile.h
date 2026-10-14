/* core/input/profile.h — interfaccia dei profili dei controller (sezione 40, MIDI-101).
 *
 * Un profilo trasforma i messaggi di un controller (MIDI della porta 1 della MPK, tasti della Flip,
 * azioni del macro pad) in eventi del pannello. Aggiungere un controller vuol dire aggiungere un
 * profilo, senza toccare il nucleo. Lo stato lo alloca il chiamante; niente heap né I/O (MIDI-003).
 */
#ifndef STAME_PROFILE_H
#define STAME_PROFILE_H

#include "../stame_base.h"
#include "panel.h"
#include "pad_codes.h"

typedef struct {
    const char *name;
    void (*reset)(void *st);
    /* messaggio MIDI completo -> 0..max eventi; ritorna quanti */
    int  (*on_midi)(void *st, uint8_t port, const uint8_t *m, uint16_t n,
                    uint32_t t_us, pnl_event_t *out, int max);
    /* tasto della console (PAD_*), del macro pad (MPAD_*, §8.10) o asse -> eventi */
    int  (*on_pad)(void *st, uint16_t pad_code, int32_t value,
                   uint32_t t_us, pnl_event_t *out, int max);
    /* chiamata ogni 10 ms: ripetizioni, soglie a tempo */
    int  (*on_tick)(void *st, uint32_t t_us, pnl_event_t *out, int max);
    /* sorgente persa: rilasci sintetici di tutto ciò che è premuto */
    int  (*on_lost)(void *st, uint32_t t_us, pnl_event_t *out, int max);
} ctl_profile_t;

/* Posto da dare a ogni chiamata di un profilo: basta per i rilasci di on_lost della MPK
 * (12 classi, 8 tasti accordo, 7 pulsanti, PUSH, trasporto, sustain, bend, SRC_LOST). */
#define PNL_MAX_OUT 48

#define PNL_TICK_US 10000u          /* periodo di on_tick */

/* [D] Valore di b in un PNL_ENC_UP sintetico (sorgente persa, cambio di banco dei pad): il
 * riconoscitore chiude il gesto con G_RELEASE ma senza G_PRESS, così un rilascio che l'utente non
 * ha fatto non esegue la funzione del tocco (per esempio Rec del looper o Key mode on/off).
 * In MIDI-100 b non ha significato per PNL_ENC_UP; i rilasci veri hanno b = 0. */
#define PNL_B_SYNTH 1

/* Uscita di un profilo: gli eventi oltre max si contano in *dropped, non si scrivono. */
typedef struct {
    pnl_event_t *ev;
    int n, max;
    uint8_t src;
    uint32_t t_us;
    uint32_t *dropped;
} pnl_out_t;

static inline void pnl_out_init(pnl_out_t *o, pnl_event_t *ev, int max, uint8_t src,
                                uint32_t t_us, uint32_t *dropped)
{
    o->ev = ev; o->n = 0; o->max = max; o->src = src; o->t_us = t_us; o->dropped = dropped;
}

static inline void pnl_put(pnl_out_t *o, uint8_t type, uint8_t a, int16_t b)
{
    if (o->n >= o->max) { if (o->dropped) (*o->dropped)++; return; }
    pnl_event_t *e = &o->ev[o->n++];
    e->type = type; e->src = o->src; e->a = a; e->b = b; e->t_us = o->t_us;
}

/* differenza di tempo con segno: regge il giro di uint32_t (71 minuti) */
static inline int32_t pnl_dt(uint32_t now, uint32_t then) { return (int32_t)(now - then); }

#endif
