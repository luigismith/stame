/* looper.c — il looper a eventi (looper.h; specifica 10, §11). */
#include "looper.h"

static bool bit_get(const uint8_t *b, uint8_t n) { return (b[n >> 3] >> (n & 7)) & 1u; }
static void bit_set(uint8_t *b, uint8_t n, bool on)
{
    if (on) b[n >> 3] |= (uint8_t)(1u << (n & 7)); else b[n >> 3] &= (uint8_t)~(1u << (n & 7));
}

void loop_init(looper_t *l)
{
    memset(l, 0, sizeof *l);
    l->bar = 384u;                                                /* 4/4 a 96 PPQN (ACC-206) */
    l->bars = 4;                                                  /* la vetrina registra 4 battute */
}

void loop_set_len(looper_t *l, uint32_t bar, uint8_t bars)
{
    if (l->state != LOOP_IDLE || !bar || !bars) return;
    l->bar = bar;
    l->bars = bars;
}

uint32_t loop_pos(const looper_t *l, uint32_t tick)
{
    if (l->state == LOOP_IDLE || l->state == LOOP_COUNT_IN || l->len == 0) return 0;
    uint32_t d = tick - l->t0;
    return l->state == LOOP_REC ? d : d % l->len;
}

/* note-off di tutto ciò che la riproduzione ha aperto; una nota il cui note-off non sta in out[] resta
 * aperta e la chiude la chiusura successiva */
static int close_open(looper_t *l, loop_ev_t *out, int max, int k)
{
    for (int r = 0; r < 2; r++)
        for (int n = 0; n < 128 && k < max; n++)
            if (bit_get(l->open[r], (uint8_t)n)) {
                out[k].t = 0; out[k].role = (uint8_t)r; out[k].note = (uint8_t)n; out[k].vel = 0;
                out[k].layer = 0; out[k].skip = 0; k++;
                bit_set(l->open[r], (uint8_t)n, false);
            }
    return k;
}

/* evento in ordine di t. I note-on e i colpi lasciano LOOP_OFF_RESERVE posti ai note-off, così ogni
 * nota registrata si chiude anche a loop pieno (ACC-231). Un evento dietro la testina non si risuona
 * in questo giro; uno davanti con skip lo salta il primo passaggio. */
static void insert(looper_t *l, uint32_t t, uint8_t role, uint8_t note, uint8_t vel, bool skip)
{
    int cap = (role != LOOP_DRUM && vel == 0) ? LOOP_EVENTS : LOOP_EVENTS - LOOP_OFF_RESERVE;
    if (l->n >= cap) { l->full = 1; return; }
    int i = l->n;
    if (i > 0 && l->ev[i - 1].t > t) {
        /* in overdub l'evento cade in mezzo: la posizione con una ricerca binaria (dopo tutti quelli
         * con lo stesso t) e lo spostamento con memmove. Spostare le struct una a una costava fino a
         * 3 ms in un callback con il loop quasi pieno (revisione del 16/10/2026) */
        int lo = 0, hi = i;
        while (lo < hi) { int mid = (lo + hi) >> 1; if (l->ev[mid].t > t) hi = mid; else lo = mid + 1; }
        memmove(&l->ev[lo + 1], &l->ev[lo], (size_t)(i - lo) * sizeof l->ev[0]);
        i = lo;
    }
    l->ev[i].t = t; l->ev[i].role = role; l->ev[i].note = note; l->ev[i].vel = vel;
    l->ev[i].layer = (uint8_t)(l->layers ? l->layers - 1 : 0);
    l->ev[i].skip = skip;
    l->n++;
    if (i < l->pi) l->pi++;
}

/* chiude lo strato: le note ancora tenute ricevono il note-off alla fine del loop (ACC-225) */
static void close_layer(looper_t *l)
{
    for (int r = 0; r < 2; r++)
        for (int n = 0; n < 128; n++)
            if (bit_get(l->rec_open[r], (uint8_t)n)) {
                insert(l, l->len - 1, (uint8_t)r, (uint8_t)n, 0, false);
                bit_set(l->rec_open[r], (uint8_t)n, false);
            }
}

static int clear(looper_t *l, loop_ev_t *out, int max, int k)
{
    k = close_open(l, out, max, k);
    l->state = LOOP_IDLE;
    l->n = l->pi = 0;
    l->layers = 0;
    l->full = 0;
    l->len = 0;
    memset(l->rec_open, 0, sizeof l->rec_open);
    return k;
}

int loop_cmd(looper_t *l, int cmd, uint32_t tick, loop_ev_t *out, int max)
{
    int k = 0;
    switch (cmd) {
    case LOOP_C_PRESS:
        if (l->state == LOOP_IDLE && l->len && l->n) {             /* loop in RAM dopo l'uscita morbida: riprende (ACC-222) */
            l->state = LOOP_PLAY;
            l->t0 = tick;
            l->pi = 0;
            l->last = 0;
        } else if (l->state == LOOP_IDLE) {                       /* una battuta di count-in, poi 4 da registrare */
            l->state = LOOP_COUNT_IN;
            l->t0 = tick + l->bar;
            l->len = (uint32_t)l->bars * l->bar;
            l->n = l->pi = 0;
            l->layers = 1;
            l->last = 0;
            memset(l->rec_open, 0, sizeof l->rec_open);
        } else if (l->state == LOOP_REC || l->state == LOOP_OVERDUB) {
            close_layer(l);
            l->state = LOOP_PLAY;
        } else if (l->state == LOOP_PLAY && l->layers < LOOP_LAYERS) {
            l->state = LOOP_OVERDUB;
            l->layers++;
        } else if (l->state == LOOP_PAUSE) {
            l->state = LOOP_PLAY;
            l->t0 = tick;                                         /* riparte da t = 0 */
            l->pi = 0;
        }
        break;
    case LOOP_C_OVERDUB:
        if (l->state == LOOP_PLAY && l->layers < LOOP_LAYERS) { l->state = LOOP_OVERDUB; l->layers++; }
        else if (l->state == LOOP_OVERDUB) { close_layer(l); l->state = LOOP_PLAY; }
        break;
    case LOOP_C_STOP:
        if (l->state == LOOP_COUNT_IN) k = clear(l, out, max, k);           /* annulla la registrazione */
        else if (l->state == LOOP_REC || l->state == LOOP_OVERDUB) { close_layer(l); l->state = LOOP_PLAY; }
        else if (l->state == LOOP_PLAY) { k = close_open(l, out, max, k); l->state = LOOP_PAUSE; }
        else if (l->state == LOOP_PAUSE) { l->state = LOOP_PLAY; l->t0 = tick; l->pi = 0; }
        break;
    case LOOP_C_UNDO:
        if (l->state == LOOP_IDLE) break;
        if (l->layers <= 1) { k = clear(l, out, max, k); break; } /* con il solo strato 0 vale Clear */
        if (l->state == LOOP_OVERDUB) l->state = LOOP_PLAY;
        k = close_open(l, out, max, k);
        {
            uint8_t last = (uint8_t)(l->layers - 1);
            int j = 0;
            for (int i = 0; i < l->n; i++) if (l->ev[i].layer != last) l->ev[j++] = l->ev[i];
            l->n = (uint16_t)j;
            l->layers--;
            if (l->n < LOOP_EVENTS - LOOP_OFF_RESERVE) l->full = 0;   /* c'è di nuovo posto (ACC-231) */
            /* il tick del comando non è ancora suonato: la testina si ferma prima dei suoi eventi */
            uint32_t pos = loop_pos(l, tick);
            l->pi = 0;
            while (l->pi < l->n && l->ev[l->pi].t < pos) l->pi++;
            memset(l->rec_open, 0, sizeof l->rec_open);
        }
        break;
    case LOOP_C_CLEAR:
        if (l->state == LOOP_OVERDUB) return loop_cmd(l, LOOP_C_UNDO, tick, out, max);   /* annulla lo strato in corso */
        k = clear(l, out, max, k);
        break;
    case LOOP_C_RESET:
        k = clear(l, out, max, k);                                /* in ogni stato, anche in overdub */
        break;
    case LOOP_C_EXIT:                                             /* uscita morbida: ferma, il loop resta in RAM */
        if (l->state == LOOP_IDLE) break;
        if (l->state == LOOP_COUNT_IN) { k = clear(l, out, max, k); break; }   /* niente ancora da tenere */
        if (l->state == LOOP_REC || l->state == LOOP_OVERDUB) close_layer(l);
        k = close_open(l, out, max, k);
        l->state = LOOP_IDLE;
        memset(l->rec_open, 0, sizeof l->rec_open);
        break;
    default: break;
    }
    return k;
}

void loop_record(looper_t *l, uint32_t tick, uint8_t role, uint8_t note, uint8_t vel)
{
    if (role == LOOP_DRUM) { loop_record_hit(l, tick, tick, note, vel); return; }
    if (role > LOOP_BASS || note > 127) return;
    uint32_t t;
    bool skip = false;
    if (l->state == LOOP_COUNT_IN) {                              /* anticipo sulla battuta: entra a t = 0 */
        int32_t d = (int32_t)(tick - l->t0);
        if (d < -(int32_t)LOOP_EARLY) return;
        t = d > 0 ? (uint32_t)d : 0u;
    } else if (l->state == LOOP_REC) {
        /* al tick t0 + len la registrazione è finita anche se loop_run non è ancora passato: una nota sul
         * primo battere del giro non entra (diventava un bordone lungo tutto il loop) */
        if (tick - l->t0 >= l->len) return;
        t = tick - l->t0;
    } else if (l->state == LOOP_OVERDUB) {
        t = loop_pos(l, tick) % l->len;
        skip = true;                                              /* suona già dal vivo: il giro corrente non la ripete */
    } else {
        return;
    }
    if (vel == 0 && !bit_get(l->rec_open[role], note)) return;   /* note-off di una nota non registrata */
    bit_set(l->rec_open[role], note, vel != 0);
    insert(l, t, role, note, vel, skip);
}

void loop_record_hit(looper_t *l, uint32_t at, uint32_t now, uint8_t inst, uint8_t vel)
{
    if (inst > 127 || vel == 0) return;                           /* i colpi non hanno note-off */
    uint32_t t;
    bool skip = false;
    if (l->state == LOOP_COUNT_IN) {
        int32_t d = (int32_t)(at - l->t0);
        if (d < -(int32_t)LOOP_EARLY) return;
        t = d > 0 ? (uint32_t)d : 0u;
    } else if (l->state == LOOP_REC) {
        if (now - l->t0 >= l->len) return;
        int32_t d = (int32_t)(at - l->t0);
        if (d < 0) d = 0;
        t = (uint32_t)d % l->len;
        skip = (uint32_t)d >= l->len;       /* oltre la fine: il primo giro lo suonerebbe subito dopo il colpo dal vivo */
    } else if (l->state == LOOP_OVERDUB) {
        t = loop_pos(l, at) % l->len;
        skip = (int32_t)(at - now) >= 0;    /* adesso o in avanti: la testina lo raggiunge dopo il colpo dal vivo */
    } else {
        return;
    }
    insert(l, t, LOOP_DRUM, inst, vel, skip);
}

int loop_run(looper_t *l, uint32_t tick, loop_ev_t *out, int max)
{
    int k = 0;
    if (l->state == LOOP_COUNT_IN) {
        if ((int32_t)(tick - l->t0) < 0) return 0;
        l->state = LOOP_REC;                                      /* fine del count-in: t = 0 */
    }
    if (l->state == LOOP_REC) {
        if (tick - l->t0 < l->len) return 0;
        close_layer(l);                                           /* 4 battute: il loop suona */
        l->state = LOOP_PLAY;
    }
    if (l->state != LOOP_PLAY && l->state != LOOP_OVERDUB) return 0;
    uint32_t pos = loop_pos(l, tick);
    /* giro nuovo: la testina torna all'inizio. Le note tenute oltre il punto di giro continuano fino al
     * loro note-off a t mod L (ACC-225); una nota rimasta aperta si chiude prima del suo prossimo
     * note-on (ACC-226) */
    if (pos < l->last || (pos == 0 && l->pi > 0)) l->pi = 0;
    l->last = pos;
    while (l->pi < l->n && l->ev[l->pi].t <= pos) {
        loop_ev_t e = l->ev[l->pi];
        l->ev[l->pi++].skip = 0;                                  /* il salto vale per un passaggio */
        if (e.t != pos || e.skip) continue;                       /* passato senza suonarlo, o già sentito dal vivo */
        if (e.role == LOOP_DRUM) {                                /* colpo: niente note aperte */
            if (k < max) out[k++] = e;
            continue;
        }
        if (e.vel == 0 && !bit_get(l->open[e.role], e.note)) continue;
        if (e.vel && bit_get(l->open[e.role], e.note) && k < max) {   /* stessa nota: prima il note-off */
            out[k] = e; out[k].vel = 0; k++;
        }
        if (k < max) {
            bit_set(l->open[e.role], e.note, e.vel != 0);
            out[k++] = e;
        }
    }
    return k;
}
