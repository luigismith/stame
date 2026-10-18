/* input.c — profili dei controller e riconoscitore dei gesti insieme (sezione 40, §2, §10, §11). */
#include "input.h"

/* un profilo per sorgente, nell'ordine di src_t */
static const ctl_profile_t *const PROFILE[SRC_COUNT] STAME_ROM = { &MPK_STAME, &FLIP_TASTI, &PAD_BRIMFORD };

/* il profilo della sorgente: per la MPK dipende dal modello collegato */
static const ctl_profile_t *prof(const inp_t *h, int src)
{
    return src == SRC_MPK && h->mpk_model == MPK_MODEL_MK4 ? &MPK_MK4 : PROFILE[src];
}

static void *state(inp_t *h, int src)
{
    switch (src) {
    case SRC_MPK:  return h->mpk_model == MPK_MODEL_MK4 ? (void *)&h->mk4 : (void *)&h->mpk;
    case SRC_FLIP: return &h->flip;
    default:       return &h->mpad;
    }
}

/* bit di flip_keys: PAD_B…PAD_R3 = 0…14, croce = 16…19 */
static int pad_bit(uint16_t code)
{
    if (code >= PAD_B && code <= PAD_R3) return code - PAD_B;
    if (code >= PAD_UP && code <= PAD_RIGHT) return 16 + code - PAD_UP;
    return -1;
}

static uint16_t bit_pad(int b)
{
    return (uint16_t)(b < 16 ? PAD_B + b : PAD_UP + b - 16);
}

/* Configurazione (MIDI-137, 17/10/2026): i tasti della Flip non tacciono mai, ma X e START cambiano
 * ruolo con la tastiera collegata. Si chiama dopo ogni collegamento, scollegamento o cambio di
 * modello, anche perché il reset dei profili azzera cfg. */
static void cfg_sync(inp_t *h)
{
    bool mpk = (h->connected & (1u << SRC_MPK)) != 0;
    bool mk4 = mpk && h->mpk_model == MPK_MODEL_MK4;
    h->flip.cfg = (uint8_t)((mk4 ? FLIP_CFG_MK4 : 0) | (mpk && !mk4 ? FLIP_CFG_PLUS : 0));
}

/* eventi di un profilo -> gest -> out[k…]; ritorna il nuovo k */
static int to_gest(inp_t *h, const pnl_event_t *ev, int n, pnl_event_t *out, int max, int k)
{
    for (int i = 0; i < n; i++) k += gest_feed(&h->gest, &ev[i], out + k, max - k);
    return k;
}

/* manda a un profilo i tasti della Flip tenuti, premuti (value 1) o rilasciati (value 0); i
 * rilasci sono sintetici, perché li decide lo scollegamento e non l'utente */
static int replay_flip_keys(inp_t *h, int src, int32_t value, uint32_t t_us, pnl_event_t *out, int max, int k)
{
    pnl_event_t tmp[PNL_MAX_OUT];
    for (int b = 0; b < 32; b++) {
        if (!(h->flip_keys & (1u << b))) continue;
        int n = prof(h, src)->on_pad(state(h, src), bit_pad(b), value, t_us, tmp, PNL_MAX_OUT);
        for (int i = 0; i < n; i++)
            if (value == 0 && tmp[i].type == PNL_ENC_UP) tmp[i].b = PNL_B_SYNTH;
        k = to_gest(h, tmp, n, out, max, k);
    }
    return k;
}

void inp_init(inp_t *h)
{
    memset(h, 0, sizeof *h);
    for (int s = 0; s < SRC_COUNT; s++) prof(h, s)->reset(state(h, s));
    gest_init(&h->gest);
    cfg_sync(h);
}

void inp_set_mpk_model(inp_t *h, uint8_t model)
{
    if (model == h->mpk_model) return;
    h->mpk_model = model;
    prof(h, SRC_MPK)->reset(state(h, SRC_MPK));
    cfg_sync(h);
}

int inp_midi(inp_t *h, const midi_msg_t *m, pnl_event_t *out, int max)
{
    if (m->sysex && !m->valid) return 0;
    /* Plus: la porta 2 è l'ingresso MIDI (§5); MK4: la porta 2 (DAW) porta manopole e trasporto */
    if (m->port != MIDI_PORT_CTL && h->mpk_model != MPK_MODEL_MK4) return 0;
    pnl_event_t tmp[PNL_MAX_OUT];
    int n = prof(h, SRC_MPK)->on_midi(state(h, SRC_MPK), m->port, midi_msg_data(m), midi_msg_len(m), m->t_us, tmp,
                                      PNL_MAX_OUT);
    return to_gest(h, tmp, n, out, max, 0);
}

int inp_pad(inp_t *h, uint16_t code, int32_t value, uint32_t t_us, pnl_event_t *out, int max)
{
    pnl_event_t tmp[PNL_MAX_OUT];
    int b = pad_bit(code), k = 0;
    if (b >= 0 && value == 1) h->flip_keys |= 1u << b;
    if (b >= 0 && value == 0) h->flip_keys &= ~(1u << b);
    for (int s = 0; s < SRC_COUNT; s++) {
        int n = prof(h, s)->on_pad(state(h, s), code, value, t_us, tmp, PNL_MAX_OUT);
        k = to_gest(h, tmp, n, out, max, k);
    }
    return k;
}

int inp_tick(inp_t *h, uint32_t t_us, pnl_event_t *out, int max)
{
    pnl_event_t tmp[PNL_MAX_OUT];
    int k = 0;
    for (int s = 0; s < SRC_COUNT; s++) {
        int n = prof(h, s)->on_tick(state(h, s), t_us, tmp, PNL_MAX_OUT);
        k = to_gest(h, tmp, n, out, max, k);
    }
    return k + gest_tick(&h->gest, t_us, out + k, max - k);
}

int inp_connected(inp_t *h, uint8_t src, uint32_t t_us, pnl_event_t *out, int max)
{
    if (src >= SRC_COUNT) return 0;
    prof(h, src)->reset(state(h, src));
    h->connected |= (uint8_t)(1u << src);
    cfg_sync(h);

    pnl_event_t ev = { .type = PNL_SRC_CONNECTED, .src = src, .a = src, .b = 0, .t_us = t_us };
    int k = gest_feed(&h->gest, &ev, out, max);
    if (src == SRC_FLIP) h->flip_keys = 0;
    else k = replay_flip_keys(h, src, 1, t_us, out, max, k);   /* X tenuto alla connessione della MPK */
    return k;
}

int inp_lost(inp_t *h, uint8_t src, uint32_t t_us, pnl_event_t *out, int max)
{
    if (src >= SRC_COUNT) return 0;
    pnl_event_t tmp[PNL_MAX_OUT];
    int k = 0;

    if (src == SRC_FLIP) {                                        /* X tenuto: il PUSH si rilascia */
        for (int s = 0; s < SRC_COUNT; s++)
            if (s != SRC_FLIP) k = replay_flip_keys(h, s, 0, t_us, out, max, k);
        h->flip_keys = 0;
    }
    int n = prof(h, src)->on_lost(state(h, src), t_us, tmp, PNL_MAX_OUT);
    k = to_gest(h, tmp, n, out, max, k);
    h->connected &= (uint8_t)~(1u << src);
    cfg_sync(h);
    return k;
}

uint32_t inp_dropped(const inp_t *h)
{
    return h->mpk.dropped + h->mk4.dropped + h->flip.dropped + h->mpad.dropped + h->gest.dropped;
}
