/* gest.h — stato unito delle sorgenti, fuoco e riconoscimento dei gesti (sezione 40, §10.1–§10.4).
 *
 * Riceve gli eventi del pannello di tutti i profili e li passa al nucleo così:
 *   - PNL_ENC_DOWN/UP/TURN diventano gesti G_* con ENC_FOCUS già risolto (MIDI-103, MIDI-104);
 *   - tasti e tasti accordo escono una volta sola anche se li tengono più sorgenti (MIDI-102);
 *   - PNL_FOCUS_STEP sposta il fuoco e non esce;
 *   - un PNL_ENC_UP con b = PNL_B_SYNTH chiude il gesto senza G_PRESS (profile.h);
 *   - gli altri eventi passano invariati.
 * Gli eventi in uscita usano pnl_event_t; i gesti hanno i tipi G_*, dopo quelli di pnl_type_t.
 */
#ifndef STAME_GEST_H
#define STAME_GEST_H

#include "profile.h"

enum {                      /* a = enc_id_t già risolto */
    G_TURN = 0x20,          /* b = scatti con segno */
    G_PRESS_TURN,           /* b = scatti con segno: premere e ruotare */
    G_HOLD,                 /* alla soglia T_HOLD, con l'encoder ancora premuto */
    G_HOLD_LONG,            /* solo ENC_LOOP, alla soglia T_HOLD2 */
    G_PRESS,                /* al rilascio, se non tenuto e non ruotato */
    G_RELEASE               /* sempre, alla fine della pressione */
};

enum { GS_IDLE, GS_DOWN, GS_HELD };

#define GEST_T_HOLD_US  1000000u    /* MIDI-103: 1 s per tutti ([M] Bass e BPM, [V] VO-12 gli altri) */
#define GEST_T_HOLD2_US 2000000u    /* MIDI-103: Loop, uscita morbida e lista Save Loop [M] */

typedef struct {
    uint8_t  cnt[ENC_COUNT][SRC_COUNT]; /* pressioni di ogni encoder per sorgente (MIDI-102) */
    uint8_t  fdown[SRC_COUNT];          /* encoder preso dall'ENC_DOWN(ENC_FOCUS) della sorgente; ENC_COUNT = nessuno */
    uint8_t  keys[12];                  /* bit per sorgente che tiene la classe di nota */
    uint8_t  chords[CHB_COUNT];         /* bit per sorgente che tiene il tasto accordo */
    uint8_t  st[ENC_COUNT];             /* GS_* (MIDI-103) */
    uint8_t  rotated[ENC_COUNT];
    uint8_t  long_done[ENC_COUNT];
    uint8_t  down_src[ENC_COUNT];       /* sorgente che ha cominciato la pressione */
    uint32_t t_down[ENC_COUNT];
    uint8_t  focus;                     /* fuoco del pannello (MIDI-104), parte da Sound */
    uint8_t  owner;                     /* encoder della lista, del menu o dell'overlay visibile; ENC_COUNT = nessuno */
    uint8_t  owner_list;                /* 1 = l'owner ha aperto una lista o un menu (MIDI-105) */
    uint8_t  started;                   /* now è valido */
    uint32_t now;                       /* tempo più recente visto */
    uint32_t dropped;                   /* eventi che non stavano in out[] */
} gest_t;

void gest_init(gest_t *g);

/* Lista, menu o overlay visibile e il suo encoder (MIDI-104 punto 1); ENC_COUNT = nessuno.
 * Lo imposta core/ui. */
void gest_set_owner(gest_t *g, uint8_t enc, bool is_list);

/* Un evento del pannello -> 0..max eventi per il nucleo; ritorna quanti. */
int  gest_feed(gest_t *g, const pnl_event_t *e, pnl_event_t *out, int max);

/* Da chiamare ogni 10 ms: soglie di G_HOLD e G_HOLD_LONG. */
int  gest_tick(gest_t *g, uint32_t t_us, pnl_event_t *out, int max);

/* Dopo una pausa lunga dell'orologio (sospensione): il tempo riparte da t_us anche se, letto in 32
 * bit, sembra indietro. Le pressioni in corso ripartono da adesso per le soglie del tenuto. */
void gest_resync(gest_t *g, uint32_t t_us);

/* Encoder che ENC_FOCUS ruota adesso: l'owner, altrimenti il fuoco (ui_controls_t.turn_target). */
uint8_t gest_target(const gest_t *g);

/* Encoder tenuto (GS_DOWN o GS_HELD), per le combinazioni come Bass Voicing + Loop (UI-104). */
static inline bool gest_held(const gest_t *g, uint8_t enc) { return enc < ENC_COUNT && g->st[enc] != GS_IDLE; }

#endif
