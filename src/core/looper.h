/* looper.h — il looper a eventi (specifica 10, §11; ACC-220…232), forma semplice della vetrina.
 *
 * Registra eventi, non audio (ACC-220): note TREBLE già passate dalla performance e note BASS,
 * prima del transpose, con il tempo in tick dall'inizio del loop. In riproduzione il chiamante
 * applica il transpose corrente (ACC-221). Stati come ui_lp_state_t: la pressione dà una battuta di
 * count-in (ACC-223), poi la registrazione dura 4 battute e il loop suona; overdub, pausa, undo e
 * clear come §11.2. La sala d'attesa e la scelta delle battute non ci sono ancora [D].
 * Le note suonate nell'ultimo sedicesimo del count-in entrano a t = 0 [D]: chi attacca un filo
 * prima della battuta non perde l'accordo. C11 puro, niente heap.
 */
#ifndef STAME_LOOPER_H
#define STAME_LOOPER_H
#include "stame_base.h"

enum { LOOP_IDLE, LOOP_WAITING, LOOP_COUNT_IN, LOOP_REC, LOOP_PLAY, LOOP_OVERDUB, LOOP_PAUSE };
/* LOOP_C_CLEAR in overdub annulla lo strato in corso; LOOP_C_RESET svuota sempre tutto (Reset, uscita
 * forzata, fine della demo) */
enum { LOOP_C_PRESS, LOOP_C_STOP, LOOP_C_UNDO, LOOP_C_CLEAR, LOOP_C_OVERDUB, LOOP_C_RESET };
enum { LOOP_TREBLE, LOOP_BASS, LOOP_DRUM };   /* LOOP_DRUM: colpi del kit, senza note-off (ACC-211) */

#define LOOP_EVENTS 8192        /* ACC-231 */
#define LOOP_LAYERS 32          /* ACC-224 */
#define LOOP_OFF_RESERVE 256    /* posti tenuti per i note-off delle note aperte (2 ruoli × 128) */
#define LOOP_OUT_MAX 320        /* eventi che un comando o un tick possono emettere: dimensione di out[] */

/* vel 0 = note-off; skip = già sentito dal vivo (nota suonata in overdub, colpo quantizzato in avanti):
 * il primo passaggio della testina lo salta, i giri dopo lo suonano */
typedef struct { uint32_t t; uint8_t role, note, vel, layer, skip; } loop_ev_t;

#define LOOP_EARLY 24u          /* anticipo accettato alla fine del count-in, in tick */

typedef struct {
    uint8_t  state, layers, full;
    uint32_t bar;               /* tick della battuta (384 in 4/4), fissato all'avvio della registrazione */
    uint8_t  bars;              /* battute da registrare (sync BARS_n) */
    uint32_t len;               /* lunghezza in tick */
    uint32_t t0;                /* tick in cui parte il loop (dopo il count-in) */
    loop_ev_t ev[LOOP_EVENTS];  /* ordinati per t */
    uint16_t n, pi;             /* eventi e prossimo da suonare */
    uint32_t last;              /* ultima posizione suonata */
    uint8_t  open[2][16];       /* note aperte dalla riproduzione, per ruolo */
    uint8_t  rec_open[2][16];   /* note aperte nello strato che si registra */
} looper_t;

void loop_init(looper_t *l);
/* battuta della metrica corrente in tick e numero di battute: valgono per la prossima registrazione */
void loop_set_len(looper_t *l, uint32_t bar, uint8_t bars);
/* comando al tick t; restituisce gli eventi da suonare subito (note-off di pausa, undo, clear) */
int  loop_cmd(looper_t *l, int cmd, uint32_t tick, loop_ev_t *out, int max);
/* nota da registrare al tick corrente (in COUNT_IN, REC e OVERDUB; negli altri stati non fa niente) */
void loop_record(looper_t *l, uint32_t tick, uint8_t role, uint8_t note, uint8_t vel);
/* colpo di batteria suonato al tick now e quantizzato al tick at (ACC-211) */
void loop_record_hit(looper_t *l, uint32_t at, uint32_t now, uint8_t inst, uint8_t vel);
/* eventi della riproduzione al tick t (da chiamare a ogni tick, in ordine) */
int  loop_run(looper_t *l, uint32_t tick, loop_ev_t *out, int max);
/* posizione nel giro, per l'interfaccia */
uint32_t loop_pos(const looper_t *l, uint32_t tick);

#endif
