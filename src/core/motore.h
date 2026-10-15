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
#include "perf.h"
#include "beat.h"
#include "looper.h"
#include "../dsp/dsp.h"
#include "../dsp/drums.h"

#define MOT_NONE 0xFFu

/* stato per l'interfaccia, scritto dal thread audio a ogni periodo e letto senza lock dal thread
 * della UI: una lettura a cavallo di una scrittura sbaglia al più un fotogramma */
typedef struct {
    volatile uint32_t tick, tr_t0, lp_t0, lp_len;
    volatile uint16_t bpm;
    volatile uint8_t  tr_on, lp_state, lp_layers, lp_full;
    volatile uint8_t  lp_notes[2][16];  /* note che il loop sta suonando (treble, basso), già trasposte */
} mot_snap_t;

typedef struct {
    dsp_t   *d;
    drums_t  drums;
    perf_t   perf;
    looper_t loop;
    uint32_t fs;
    uint64_t s, next_fp, spt_fp;        /* campioni resi, campione del prossimo tick e campioni per tick (32.32) */
    uint32_t tick;
    uint16_t bpm;
    uint8_t  beat_sel, beat, meter;     /* Beat o metronomo selezionato (BEAT_M_*), indice, metrica */
    uint8_t  beat_on, tr_on;            /* Beat acceso; trasporto in moto (ACC-204) */
    uint32_t tr_t0;                     /* tick della battuta 1 */
    uint8_t  held[16], held_vel;        /* voicing treble che arriva dal motore degli accordi */
    uint8_t  dirty, key_down, legato, went_empty;
    int8_t   transpose;
    uint8_t  pre[2][128];               /* nota in uscita → nota registrata (prima del transpose) */
    uint8_t  lp_out[2][128];            /* nota del loop → nota suonata, per il note-off */
    mot_snap_t snap;
} motore_t;

void mot_init(motore_t *m, dsp_t *d, uint32_t fs, uint32_t seed);
/* nota del motore degli accordi: engine 0 = treble (passa dalla performance), 1 = basso; vel 0 = off */
void mot_note(motore_t *m, int engine, uint8_t note, uint8_t vel);
void mot_chord_start(motore_t *m);              /* KEY_DOWN di un accordo nuovo */
void mot_bpm(motore_t *m, uint16_t bpm);        /* 60…200 (ACC-202) */
void mot_perf(motore_t *m, uint8_t mode, uint8_t amount);
/* selezione del menu dei Beat: BEAT_M_METRONOME con la metrica, o BEAT_M_PATTERN con l'indice di beat.h */
void mot_beat(motore_t *m, uint8_t mode, uint8_t beat);
void mot_meter(motore_t *m, uint8_t meter);     /* METER_*: vale per il metronomo (ACC-208) */
/* TRANSPORT_TOGGLE (ACC-205): accende o spegne il Beat o il metronomo selezionato */
void mot_beat_on(motore_t *m, bool on);
void mot_beat_volume(motore_t *m, uint8_t v);
void mot_transpose(motore_t *m, int8_t t);
void mot_loop(motore_t *m, int cmd);            /* LOOP_C_* */
void mot_all_off(motore_t *m);
/* n frame (multiplo di 16) */
void mot_render(motore_t *m, float *L, float *R, uint32_t n);
/* campione assoluto del tick t, per i test (TV-110, TV-111) */
uint64_t mot_tick_sample(const motore_t *m, uint32_t t);
/* tick della battuta e fra due battiti della metrica in uso: 4/4 con un Beat (ACC-209) */
uint32_t mot_bar(const motore_t *m);
uint32_t mot_click(const motore_t *m);

#endif
