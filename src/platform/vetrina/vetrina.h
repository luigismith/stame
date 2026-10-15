/* vetrina.h — la vetrina di Stame: un pilota dimostrativo della plancia.
 *
 * Non è il nucleo (core/ui, looper e suono arriveranno con le fasi F2–F4): serve a vedere e
 * provare l'identità visiva sulla Flip prima di allora. Usa il motore degli accordi vero
 * (core/acc) e lo strato di input vero (core/input: profili della MPK, della Flip e del macro pad,
 * gesti e fuoco); il resto (suoni, effetti, looper, liste) è simulato con dati inventati.
 *
 * Senza ingressi per 20 secondi parte una dimostrazione automatica che passa per tutti gli stati
 * della plancia; un tasto o un accordo la ferma.
 */
#ifndef STAME_VETRINA_H
#define STAME_VETRINA_H

#include "../../core/acc.h"
#include "../../core/input/input.h"
#include "../../ui/ui_model.h"
#include "../../dsp/patch.h"

#define VET_SCOPE_LEN 1024
#define VET_SND_Q     512
#define VET_N_SOUNDS  16
#define VET_N_BASSES  6

/* Comandi per il synth (specifica 20): la vetrina li mette in coda, la piattaforma li legge con
 * vet_snd_pop e li passa al dsp (thread audio sulla Flip, render in WAV sul PC). */
enum { VS_NOTE_ON, VS_NOTE_OFF, VS_CHORD_START, VS_PATCH, VS_PARAM, VS_MASTER, VS_BASS_VOL, VS_ALL_OFF };
typedef struct { uint8_t type, engine, a, b; } vet_snd_t;   /* engine: 0 Sound, 1 Bass */

/* patch di Stame per i suoni e i bassi della vetrina (patch_vetrina.c, da tools/patch.py) */
extern const uint8_t vet_sound_patch[VET_N_SOUNDS][DSP_NPAR];
extern const uint8_t vet_bass_patch[VET_N_BASSES][DSP_NPAR];

typedef struct {
    /* nucleo vero */
    acc_state   acc;
    acc_note_ev ev[96];
    inp_t       inp;

    /* stato simulato */
    ui_model_t  m;                    /* modello pubblicato */
    uint32_t    now_ms, boot_ms, last_ms;
    uint32_t    tick_us;              /* prossimo inp_tick */
    uint8_t     booting;

    /* accordo: persistenza dopo il rilascio */
    uint8_t     have_last;
    uint32_t    released_ms;
    chord_label_t last_chord;
    uint8_t     last_single, last_single_midi;
    ui_note_t   last_notes[UI_NOTES_MAX];
    uint8_t     last_n;

    /* trasporto e looper simulati */
    uint32_t    t0_ms;                /* inizio del trasporto */
    uint8_t     lp_state, lp_bars;
    uint32_t    lp_t0_ms;
    uint16_t    lp_rec_pcs[16][2];    /* treble e basso registrati per battuta */
    uint8_t     lp_layers;

    /* overlay e liste */
    uint32_t    ov_until;
    uint8_t     list_kind;            /* ui_list_kind_t + 1; 0 = nessuna */
    uint16_t    list_sel;
    uint32_t    list_ms;
    uint8_t     list_owner;
    uint32_t    page_until;           /* pagina dei comandi aperta fino a qui (UI-142a) */

    /* demo automatica */
    uint8_t     demo_on;              /* preferenza: demo automatica permessa */
    uint8_t     demo_running;
    uint32_t    demo_t0, last_input_ms;
    int         demo_step;

    /* meter finti */
    float       level;
    int16_t     scope[VET_SCOPE_LEN];
    uint32_t    scope_wr;
    float       phase[8];

    /* synth: coda dei comandi e ultimi valori mandati */
    vet_snd_t   snd_q[VET_SND_Q];
    uint16_t    snd_w, snd_r;
    int16_t     snd_sound, snd_bass, snd_vol, snd_bvol, snd_fx;
    uint8_t     snd_fx_idx;           /* parametro dell'effetto principale del suono (SND-601) */
    /* oscilloscopio e livelli veri, se la piattaforma li ha (vet_set_scope) */
    const int16_t *ext_scope;
    uint16_t    ext_scope_len;
    const volatile uint32_t *ext_scope_wr;
    const volatile float *ext_peak;   /* picchi L e R dell'uscita, 0…1 */

    uint8_t     quit;
} vet_t;

/* Prossimo comando per il synth; false = coda vuota. */
bool vet_snd_pop(vet_t *v, vet_snd_t *out);
/* L'oscilloscopio e i picchi dell'uscita vera prendono il posto di quelli simulati. */
void vet_set_scope(vet_t *v, const int16_t *buf, uint16_t len, const volatile uint32_t *wr,
                   const volatile float *peak);

void vet_init(vet_t *v, uint32_t now_ms);
/* Messaggio MIDI completo dalla porta 1 della MPK. */
void vet_midi(vet_t *v, const midi_msg_t *msg, uint32_t now_ms);
/* Tasto della Flip (PAD_*) o azione del macro pad. */
void vet_pad(vet_t *v, uint16_t code, int32_t value, uint32_t now_ms);
/* Quale MPK è collegata (MPK_MODEL_PLUS o MPK_MODEL_MK4): da chiamare prima di vet_mpk. */
void vet_mpk_model(vet_t *v, uint8_t model);
/* MPK collegata o persa (per gli avvisi e lo stato). */
void vet_mpk(vet_t *v, bool connected, const char *fw, uint32_t now_ms);
/* Macro pad: link = PADL_OPEN, PADL_UNMAPPED, PADL_ERROR o PADL_ABSENT (ui_model.h). */
void vet_macropad(vet_t *v, uint8_t link, uint32_t now_ms);
/* Da chiamare spesso (almeno ogni 10 ms): gesti a tempo, trasporto, demo, meter. */
void vet_tick(vet_t *v, uint32_t now_ms);
/* Batteria della Flip: 255 = sconosciuta. */
void vet_battery(vet_t *v, uint8_t pct, bool charging);
/* Il modello aggiornato da passare a ui_flip_render. */
const ui_model_t *vet_model(vet_t *v);
/* 1 quando si sceglie «Quit Stame» nel menu. */
static inline bool vet_quit(const vet_t *v) { return v->quit != 0; }
/* Per le prove: ferma l'avvio e porta la demo all'istante t_ms del suo copione. */
void vet_demo_seek(vet_t *v, uint32_t t_ms);
/* Durata del copione della demo, in ms. */
uint32_t vet_demo_len(void);

#endif
