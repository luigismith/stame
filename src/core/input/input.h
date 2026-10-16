/* input.h — ingresso dei controlli: i tre profili e il riconoscitore in un oggetto solo
 * (sezione 40, §2 strati 3 e 4, §10, §11).
 *
 * Messaggi della porta 1 della MPK -> mpk_stame; tasti e azioni (PAD_*, MPAD_*) -> a tutti i
 * profili, ognuno prende i suoi (X della Flip va a mpk_stame come PUSH); poi gest. In uscita gli
 * eventi per il nucleo descritti in gest.h. Lo stato lo alloca il chiamante.
 *
 *     static inp_t in;
 *     inp_init(&in);
 *     pnl_event_t ev[INP_MAX_OUT];
 *     int n = inp_midi(&in, &msg, ev, INP_MAX_OUT);
 */
#ifndef STAME_INPUT_H
#define STAME_INPUT_H

#include "gest.h"
#include "mpk_stame.h"
#include "mpk_mk4.h"
#include "flip_tasti.h"
#include "pad_brimford.h"
#include "../midi_parse.h"

#define INP_MAX_OUT 128     /* posto consigliato per ogni chiamata: basta per uno scollegamento */

typedef struct {
    mpk_state_t  mpk;
    mk4_state_t  mk4;
    uint8_t      mpk_model;     /* MPK_MODEL_*: quale profilo legge la sorgente SRC_MPK */
    flip_state_t flip;
    mpad_state_t mpad;
    gest_t       gest;
    uint8_t      connected;     /* bit per src_t */
    uint32_t     flip_keys;     /* tasti PAD_* tenuti: al distacco della Flip si rilasciano anche negli altri profili */
    uint16_t     flip_mute;     /* encoder (bit ENC_*, ENC_COUNT = fuoco) la cui pressione dalla Flip è stata taciuta */
} inp_t;

/* modelli della tastiera: la Plus con il programma STAME (§8.5) o la MK4 nel preset DAW (§8.9b) */
enum { MPK_MODEL_PLUS, MPK_MODEL_MK4 };

void inp_init(inp_t *h);
/* La piattaforma dice quale MPK è collegata, prima di inp_connected (dal nome della scheda MIDI). */
void inp_set_mpk_model(inp_t *h, uint8_t model);

/* Ognuna ritorna quanti eventi ha scritto in out (al massimo max). */
int inp_midi(inp_t *h, const midi_msg_t *m, pnl_event_t *out, int max);    /* solo la porta 1 (MIDI-072) */
int inp_pad(inp_t *h, uint16_t code, int32_t value, uint32_t t_us, pnl_event_t *out, int max);
int inp_tick(inp_t *h, uint32_t t_us, pnl_event_t *out, int max);          /* ogni 10 ms */
int inp_connected(inp_t *h, uint8_t src, uint32_t t_us, pnl_event_t *out, int max);   /* §8.9 punto 7 */
int inp_lost(inp_t *h, uint8_t src, uint32_t t_us, pnl_event_t *out, int max);        /* MIDI-112, MIDI-127 */

/* Eventi persi perché non stavano nei buffer, da mostrare nel registro: deve restare 0. */
uint32_t inp_dropped(const inp_t *h);

#endif
