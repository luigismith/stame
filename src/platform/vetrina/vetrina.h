/* vetrina.h — la vetrina di Stame: un pilota dimostrativo della plancia.
 *
 * Non è ancora core/ui: serve a suonare e provare Stame sulla Flip prima di allora. Usa il motore
 * degli accordi vero (core/acc), lo strato di input vero (core/input: profili della MPK, della
 * Flip e del macro pad, gesti e fuoco) e, attraverso la coda dei comandi, il motore audio vero
 * (core/motore: synth, Perform, Beat, metronomo e looper). Nomi dei suoni, effetti secondari e
 * meter di riserva sono dati della vetrina.
 *
 * Senza ingressi per 20 secondi parte la demo: un brano suonato da Stame stesso (demo.h), che passa
 * anche per gli stati della plancia; un tasto o un accordo la ferma. I suoi comandi partono un po' in
 * anticipo con il tick del motore a cui valgono, e il thread audio li applica proprio a quel tick.
 */
#ifndef STAME_VETRINA_H
#define STAME_VETRINA_H

#include "../../core/acc.h"
#include "../../core/input/input.h"
#include "../../core/motore.h"
#include "../../ui/ui_model.h"
#include "../../dsp/patch.h"
#include <stdatomic.h>

#define VET_SCOPE_LEN 1024
#define VET_SND_Q     512
#define VET_DEMO_OPTS 9         /* opzioni degli accordi che la demo rimette (DEMO_OPTS in vetrina.c) */
#include "patch_vetrina.h"      /* VET_N_SOUNDS, VET_N_BASSES: li scrive tools/patch.py */

/* Comandi per il motore audio (core/motore e synth): la vetrina li mette in coda, la piattaforma li
 * legge con vet_snd_pop e li passa al motore (thread audio sulla Flip, render in WAV sul PC).
 * VS_PERF: a = modo, b = amount; VS_BEAT: a = BEAT_M_*, b = indice; VS_LOOP: a = LOOP_C_*;
 * VS_TRANSPOSE: a = semitoni con segno.
 * timed = 1: il comando vale dal tick `at` del motore (la demo); chi lo consuma lo tiene in coda finché
 * mot_due non dice che è il momento (vet_snd_due). timed = 0: subito. */
enum { VS_NOTE_ON, VS_NOTE_OFF, VS_CHORD_START, VS_PATCH, VS_PARAM, VS_MASTER, VS_BASS_VOL, VS_ALL_OFF,
       VS_BPM, VS_PERF, VS_BEAT, VS_METER, VS_BEAT_ON, VS_BEAT_VOL, VS_TRANSPOSE, VS_LOOP,
       VS_DRUM,                         /* a = tasto 0…11, b = velocity: batteria a tastiera (ACC-211) */
       VS_METRO, VS_FILL };             /* a = on: metronomo indipendente e Fill del Beat (MIDI-133) */
typedef struct { uint8_t type, engine, a, b, timed; uint32_t at; } vet_snd_t;   /* engine: 0 Sound, 1 Bass */

/* statistiche del thread audio della piattaforma (PLT-021), scritte dal callback e lette dalla UI:
 * underrun stimati, carico medio dell'ultimo secondo e massimo in percento del periodo, callback
 * più lungo in µs, scheduling ottenuto (0 normale, 1 nice −10, 2 SCHED_FIFO) con l'errno di SCHED_FIFO */
typedef struct vet_audio_stats { _Atomic uint32_t xruns, load_pct, load_max_pct, cb_max_us, sched, sched_err; } vet_audio_stats_t;

/* una scena del macro pad (MIDI-133, T5–T8): suono, basso, Perform, effetto, tonalità e basso acceso */
typedef struct { uint8_t used, sound, bass, perf_mode, perf_amount, fx_amount, key_index, key_on, bass_on; } vet_scene_t;

/* patch di Stame per i suoni e i bassi della vetrina (patch_vetrina.c, da tools/patch.py) */
extern const uint8_t vet_sound_patch[VET_N_SOUNDS][DSP_NPAR];
extern const uint8_t vet_bass_patch[VET_N_BASSES][DSP_NPAR];
/* nome, motore (ENGINE_* di ui_model.h) e famiglia di ogni suono; nomi dei bassi */
typedef struct { const char *name; uint8_t engine; const char *cat; } vet_snd_info_t;
extern const vet_snd_info_t vet_sound_info[VET_N_SOUNDS];
extern const char *const vet_bass_name[VET_N_BASSES];
/* Perform di default di ogni suono: modo e amount (ACC-162, colonne di bank.idx) */
extern const uint8_t vet_sound_perf[VET_N_SOUNDS][2];

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

    /* trasporto e looper veri: lo stato che pubblica il motore audio (vet_set_motore). snap punta alla
     * copia coerente fatta a ogni tick con mot_snap_read; NULL senza motore */
    const mot_snap_t *snap, *snap_src;
    mot_snap_t  snap_copy;
    const vet_audio_stats_t *stats;   /* statistiche del thread audio, se la piattaforma le ha */
    uint8_t     lp_seen;              /* ultimo stato del looper visto, per il menu a tre voci */

    /* overlay e liste */
    uint32_t    ov_until;
    uint8_t     list_kind;            /* ui_list_kind_t + 1; 0 = nessuna */
    uint16_t    list_sel;
    uint32_t    list_ms;
    uint8_t     list_owner;
    uint32_t    page_until;           /* pagina dei comandi aperta fino a qui (UI-142a) */
    uint8_t     page_pinned;          /* aperta da T15 del macro pad, finché non lo si ripreme o B (MIDI-132) */
    uint8_t     view_back;            /* la vista a cui T14 torna da Geek Out */

    /* demo automatica: il brano va a tick del motore (demo.h) */
    uint8_t     demo_on;              /* preferenza: demo automatica permessa */
    uint8_t     factory_warned;       /* avviso «STAME program not active» già dato per questo collegamento (MIDI-119) */
    vet_scene_t scenes[4];            /* scene del macro pad (MIDI-133) */
    uint8_t     scenes_dirty;         /* una scena salvata: la piattaforma scrive il file e lo azzera */
    uint8_t     demo_running;
    uint32_t    demo_t0, last_input_ms;
    uint8_t     demo_theme;           /* il tema di chi suona, da rimettere quando la demo si ferma */
    uint32_t    demo_tick0;           /* tick del motore a cui comincia il brano */
    int         demo_step;
    uint8_t     demo_song;            /* quale brano di vet_demo_songs; alla fine passa al successivo */
    int16_t     demo_saved[VET_DEMO_OPTS];   /* opzioni degli accordi da rimettere quando la demo si ferma */
    uint8_t     demo_focus, demo_view_back, demo_pinned;   /* fuoco, vista di T14 e pagina di chi suonava */
    uint32_t    vtick, vt_acc;        /* senza motore: tick contati dall'orologio, al BPM corrente */

    /* meter finti */
    float       level;
    int16_t     scope[VET_SCOPE_LEN];
    uint32_t    scope_wr;
    float       phase[8];

    /* synth: coda dei comandi e ultimi valori mandati */
    vet_snd_t   snd_q[VET_SND_Q];
    uint16_t    snd_w, snd_r;
    int16_t     snd_sound, snd_bass, snd_vol, snd_bvol, snd_fx;
    int16_t     snd_bpm, snd_perf, snd_beat, snd_meter, snd_beat_on, snd_beat_vol, snd_tr;
    uint8_t     snd_fx_idx;           /* parametro dell'effetto principale del suono (SND-601) */
    uint8_t     snd_timed;            /* i comandi messi in coda adesso valgono dal tick snd_at */
    uint32_t    snd_at;
    /* oscilloscopio e livelli veri, se la piattaforma li ha (vet_set_scope) */
    const int16_t *ext_scope;
    uint16_t    ext_scope_len;
    const volatile uint32_t *ext_scope_wr;
    const volatile float *ext_peak;   /* picchi L e R dell'uscita, 0…1 */

    uint8_t     quit;
} vet_t;

/* Prossimo comando per il synth; false = coda vuota. vet_snd_peek lo legge senza toglierlo. */
bool vet_snd_pop(vet_t *v, vet_snd_t *out);
bool vet_snd_peek(const vet_t *v, vet_snd_t *out);
/* L'oscilloscopio e i picchi dell'uscita vera prendono il posto di quelli simulati. */
void vet_set_scope(vet_t *v, const int16_t *buf, uint16_t len, const volatile uint32_t *wr,
                   const volatile float *peak);
/* Stato del motore audio (trasporto, Beat, looper) per la plancia; senza, tempo e looper restano fermi. */
void vet_set_motore(vet_t *v, const mot_snap_t *snap);
/* Statistiche del thread audio per i meter (carico, massimo, underrun). */
void vet_set_audio_stats(vet_t *v, const vet_audio_stats_t *stats);

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
/* i tasti della Flip spariti (il nodo evdev si è chiuso): rilasci sintetici di ciò che era tenuto */
void vet_flip_lost(vet_t *v, uint32_t now_ms);
/* Da chiamare spesso (almeno ogni 10 ms): gesti a tempo, trasporto, demo, meter. */
void vet_tick(vet_t *v, uint32_t now_ms);
/* Batteria della Flip: 255 = sconosciuta. */
void vet_battery(vet_t *v, uint8_t pct, bool charging);
/* Il modello aggiornato da passare a ui_flip_render. */
const ui_model_t *vet_model(vet_t *v);
/* 1 quando si sceglie «Quit Stame» nel menu. */
static inline bool vet_quit(const vet_t *v) { return v->quit != 0; }
/* Per le prove: ferma l'avvio e porta la demo all'istante t_ms del suo copione, a passi di 10 ms.
 * step (se c'è) gira dopo ogni passo: la piattaforma vi passa i comandi al motore e rende l'audio. */
void vet_demo_seek(vet_t *v, uint32_t t_ms, void (*step)(vet_t *v, void *ctx), void *ctx);
/* Durata del brano i della demo (o di quello corrente con i < 0), in ms, con i suoi cambi di tempo. */
uint32_t vet_demo_len(int i);
/* Sceglie il brano che la demo suonerà alla prossima partenza (il render lo usa per --song). */
void vet_demo_select(vet_t *v, int i);
/* Scene (MIDI-133) come testo chiave=valore (sezione 50 §9.1): la piattaforma le tiene in Saves/stame/scene.txt.
 * vet_scenes_write ritorna i byte scritti (0 se non stanno in max). */
size_t vet_scenes_write(const vet_t *v, char *buf, size_t max);
void vet_scenes_read(vet_t *v, const char *txt, size_t n);

#endif
