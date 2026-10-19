/* motore.h — clock, performance, Beat e looper nel thread audio (specifica 10, §9–§11; 50, §3).
 *
 * Il thread audio ne è l'unico proprietario (PLT-006). Riceve dalla piattaforma le note del motore
 * degli accordi (treble e basso) e i comandi (BPM, Perform, Beat, transpose, looper). A ogni blocco
 * di 16 campioni fa avanzare il clock a 96 tick per semiminima (ACC-200), con la posizione del tick
 * in campioni a virgola fissa 32.32 (ACC-201); fa suonare performance, Beat e looper e rende il synth
 * con il bus della batteria. Gli eventi di un tick valgono dall'inizio del blocco che lo contiene.
 *
 * Il trasporto è in moto quando suona il Beat (o il metronomo) o quando il looper lavora (ACC-204).
 * Parte da battuta 1 quando si mette in moto, e riparte con il looper quando questo comincia una
 * registrazione o riprende dalla pausa (ACC-222). Spegnere il Beat mentre il looper suona lo zittisce
 * soltanto: il tempo del loop continua (ACC-205).
 */
#ifndef STAME_MOTORE_H
#define STAME_MOTORE_H
#include "stame_base.h"
#include <stdatomic.h>
#include "perf.h"
#include "beat.h"
#include "inventa.h"
#include "looper.h"
#include "../dsp/dsp.h"
#include "../dsp/drums.h"

#define MOT_NONE 0xFFu
#define MOT_SWING_MAX 12u               /* swing (ACC-216): ritardo massimo dei sedicesimi dispari, 12 tick = 75 % */
#define MOT_SWQ 16                      /* colpi del loop in attesa dello swing */

/* stato per l'interfaccia, scritto dal thread audio a ogni periodo e letto senza lock dal thread
 * della UI con un seqlock (PLT-017): seq è dispari mentre l'audio scrive; la UI copia i campi con
 * mot_snap_read e ritenta se seq è cambiato, così non vede mai lp_len di un giro e lp_t0 di un altro */
typedef struct {
    _Atomic uint32_t seq;
    uint32_t tick, tr_t0, lp_t0, lp_len;
    uint16_t bpm;
    uint8_t  tr_on, lp_state, lp_layers, lp_full;
    uint8_t  lp_notes[2][16];           /* note che il loop sta suonando (treble, basso), già trasposte */
} mot_snap_t;

/* copia coerente dello snapshot per il thread della UI (al più tre tentativi) */
void mot_snap_read(const mot_snap_t *src, mot_snap_t *dst);

typedef struct {
    dsp_t   *d;
    const smp_bank_t *bank;             /* banco dei campioni: kit dei Beat e modello SMP (20 §7b) */
    drums_t  drums;
    perf_t   perf;
    looper_t loop;
    uint32_t fs;
    /* campioni resi; campioni dall'inizio del blocco corrente al prossimo tick e campioni per tick
     * (32.32). next_fp è relativo al blocco: una posizione assoluta in 32.32 traboccava dopo 2³²
     * campioni (24,85 h a 48 kHz) e il ciclo dei tick non usciva più */
    uint64_t s, next_fp, spt_fp;
    uint32_t tick;
    uint16_t bpm;
    uint8_t  beat_sel, beat, meter;     /* Beat o metronomo selezionato (BEAT_M_*), indice, metrica */
    uint8_t  beat_on, tr_on;            /* Beat acceso; trasporto in moto (ACC-204) */
    uint8_t  metro_on, fill;            /* metronomo indipendente dal Beat e Fill tenuto (MIDI-133) */
    uint8_t  kit_sel;                   /* drum machine (MIDI-135): 0 = il kit del Beat, 1…KIT_COUNT a mano */
    uint8_t  roll_div;                  /* Roll: tick fra due ripetizioni di un tasto tenuto, 0 = spento */
    uint8_t  swing;                     /* swing (ACC-216): tick di ritardo dei sedicesimi dispari, 0…MOT_SWING_MAX */
    int32_t  sw_step;                   /* passo dispari del Beat che aspetta lo swing (−1 = nessuno) e quando suona */
    uint32_t sw_due;
    uint8_t  swq_n;                     /* colpi del loop sui sedicesimi dispari, in attesa dello swing */
    struct { uint32_t due; uint8_t inst, vel; } swq[MOT_SWQ];
    uint8_t  inv_on;                    /* il Beat viene dalla batteria che si inventa (MIDI-139) */
    uint8_t  inv_dens[INV_PARTS];       /* densità delle cinque parti, 0…10 */
    inv_t    inv;                       /* stile, variazione e priorità del loop inventato */
    uint8_t  drum_held[DRUM_COUNT];     /* velocity dei tasti di batteria tenuti (0 = su) */
    uint32_t drum_t[DRUM_COUNT];        /* tick del colpo che li ha premuti */
    uint32_t tr_t0;                     /* tick della battuta 1 */
    uint8_t  held[16], held_vel;        /* voicing treble che arriva dal motore degli accordi */
    uint8_t  dirty, key_down, legato, went_empty;
    uint8_t  removed;                   /* una nota treble è stata spenta dall'ultimo gesto: non è un ADD_NOTE */
    int8_t   transpose;
    uint8_t  pre[2][128];               /* nota in uscita → nota registrata (prima del transpose) */
    uint8_t  lp_out[2][128];            /* nota del loop → nota suonata, per il note-off */
    uint8_t  ref[2][128];               /* sorgenti che tengono la nota (dal vivo, loop): ACC-253 */
    mot_snap_t snap;
} motore_t;

void mot_init(motore_t *m, dsp_t *d, uint32_t fs, uint32_t seed);
/* il banco dei campioni, prima di suonare: va al synth (dsp_set_bank) e dà il kit al Beat scelto */
void mot_set_bank(motore_t *m, const smp_bank_t *bank);
/* nota del motore degli accordi: engine 0 = treble (passa dalla performance), 1 = basso; vel 0 = off */
void mot_note(motore_t *m, int engine, uint8_t note, uint8_t vel);
void mot_chord_start(motore_t *m);              /* KEY_DOWN di un accordo nuovo */
/* batteria a tastiera (ACC-211): il tasto k (0 = Do … 11 = Si) colpisce lo strumento k del kit del
 * Beat (ACC-212) e, se il looper registra, entra nel loop quantizzato al sedicesimo più vicino della
 * griglia del loop (da t0, l'inizio del giro), con lo swing se c'è (ACC-216) */
void mot_drum(motore_t *m, uint8_t k, uint8_t vel);
/* drum machine (MIDI-135): rilascio del tasto k (ferma il Roll), kit a mano (0 = quello del Beat),
 * Roll in tick fra due ripetizioni (0 = spento): un tasto tenuto si ripete sulla griglia del loop o del trasporto */
void mot_drum_off(motore_t *m, uint8_t k);
void mot_kit(motore_t *m, uint8_t sel);
void mot_roll(motore_t *m, uint8_t div_ticks);
/* swing (ACC-216): i sedicesimi dispari della griglia (dal tick della battuta 1 per il Beat, da t0 per il
 * loop) suonano ticks dopo; il loop tiene i colpi sulla griglia dritta e lo swing vale a ogni giro */
void mot_swing(motore_t *m, uint8_t ticks);
/* FX del bus della batteria (SND-538): drive 0…10, filtro −10…+10 (passa-basso … spento … passa-alto) */
void mot_drum_fx(motore_t *m, uint8_t drive, int8_t filt);
/* la batteria che si inventa (MIDI-139, ACC-215): il Beat suona il loop di inventa.h con lo stile e la
 * variazione dati, finché non si sceglie un Beat del menu (mot_beat); le densità valgono dal passo dopo */
void mot_inventa(motore_t *m, uint8_t groove, uint8_t var);
void mot_inventa_dens(motore_t *m, uint8_t part, uint8_t dens);
void mot_bpm(motore_t *m, uint16_t bpm);        /* 60…200 (ACC-202) */
void mot_perf(motore_t *m, uint8_t mode, uint8_t amount);
/* selezione del menu dei Beat: BEAT_M_METRONOME con la metrica, o BEAT_M_PATTERN con l'indice di beat.h */
void mot_beat(motore_t *m, uint8_t mode, uint8_t beat);
void mot_meter(motore_t *m, uint8_t meter);     /* METER_*: vale per il metronomo (ACC-208) */
/* TRANSPORT_TOGGLE (ACC-205): accende o spegne il Beat o il metronomo selezionato */
void mot_beat_on(motore_t *m, bool on);
void mot_beat_volume(motore_t *m, uint8_t v);
/* metronomo on/off indipendente dal Beat (T3 del pad, MIDI-133): mette in moto il trasporto come il Beat */
void mot_metronome(motore_t *m, bool on);
/* Fill del Beat finché on (T4 tenuto, MIDI-133): il pattern di riempimento al posto di quello normale */
void mot_fill(motore_t *m, bool on);
void mot_transpose(motore_t *m, int8_t t);
void mot_loop(motore_t *m, int cmd);            /* LOOP_C_* */
void mot_all_off(motore_t *m);
/* n frame (multiplo di 16) */
void mot_render(motore_t *m, float *L, float *R, uint32_t n);
/* Comandi a tempo: true se il tick `at` è già passato o cade nel prossimo blocco di 16 campioni.
 * Chi ha un comando per il tick `at` lo applica appena prima di quel blocco, così vale dal tick
 * giusto come gli eventi del clock (performance, Beat, looper). */
bool mot_due(const motore_t *m, uint32_t at);
/* campione assoluto del tick t, per i test (TV-110, TV-111) */
uint64_t mot_tick_sample(const motore_t *m, uint32_t t);
/* tick della battuta e fra due battiti della metrica in uso: 4/4 con un Beat (ACC-209) */
uint32_t mot_bar(const motore_t *m);
uint32_t mot_click(const motore_t *m);

#endif
