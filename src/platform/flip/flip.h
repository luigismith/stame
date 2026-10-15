/* flip.h — piattaforma Miyoo Flip della vetrina: video SDL, tasti evdev, MIDI grezzo, batteria.
 *
 * Sezione 50: SDL2 caricata con dlopen (PLT-059, PLT-060), tasti letti solo da evdev (PLT-052,
 * PLT-053), MIDI rawmidi senza alsa-lib (§6.1), batteria da sysfs (PLT-090). Audio: il motore
 * (performance, Beat, looper) e il synth nel thread audio di SDL, con i comandi della vetrina su una
 * coda SPSC (audio.c).
 */
#ifndef STAME_FLIP_H
#define STAME_FLIP_H

#include <stdint.h>
#include <stdbool.h>
#include "../../core/motore.h"

/* video */
int  video_open(void);                                        /* 0 = ok */
void video_present(const uint16_t *px, const void *rects, int n_rects);   /* rects: gfx_rect_t[] */
void video_close(void);
/* audio di SDL con callback (video_sdl.c) */
int  sdl_audio_open(int rate, int frames, void (*cb)(void *, uint8_t *, int), int *got_rate, int *got_frames);
void sdl_audio_close(void);

/* il synth (audio.c): comandi della vetrina, logo sonoro, oscilloscopio e picchi dell'uscita */
int  audio_open(int frames);                                  /* 0 = ok */
void audio_send(const void *cmd);                             /* un vet_snd_t, dal thread principale */
void audio_logo(void);                                        /* suona il logo dell'avvio */
void audio_close(void);
const int16_t *audio_scope(uint16_t *len, const volatile uint32_t **wr, const volatile float **peak);
const mot_snap_t *audio_motore(void);                        /* trasporto, Beat e looper per la plancia */

/* tasti della Flip: richiama cb per ogni tasto (codice PAD_*, valore 1 giù / 0 su) */
typedef void (*pad_cb_t)(void *ctx, uint16_t code, int32_t value);
int  pad_open(void);                                          /* fd o -1 */
int  pad_read(int fd, pad_cb_t cb, void *ctx);                 /* 0, oppure −1 se il dispositivo è sparito */
void pad_close(int fd);

/* macro pad BRIMFORD (macropad.c): numero di nodi aperti, 0 assente, −2 grab fallito */
int  macropad_open(void);
void macropad_close(void);
int  macropad_fds(int *out, int max);
int  macropad_read(pad_cb_t cb, void *ctx);                    /* −1 perso, altrimenti codici ignorati di fila */

/* MIDI grezzo della MPK (porta 1) */
typedef struct {
    int     fd, fd2;              /* porta 1 e porta 2 (solo MK4) */
    int     card;
    uint8_t model;                /* 0 = Plus o altra tastiera, 1 = MPK mini IV (MPK_MODEL_*) */
    char    name[48];
} midi_dev_t;
bool midi_scan(midi_dev_t *d);                                /* cerca e apre; true se aperto */
bool midi_retry_port2(midi_dev_t *d);                         /* MK4 aperta senza la porta 2: riprova; true se ora c'è */
int  midi_read(midi_dev_t *d, int port, uint8_t *buf, int max);   /* port 0 o 1; byte letti, 0 nessuno, -1 perso */
void midi_close(midi_dev_t *d);

/* batteria: percentuale (255 = sconosciuta) e carica */
void battery_read(uint8_t *pct, bool *charging);

/* orologio monotono in ms e registro */
uint32_t now_ms(void);
void log_msg(const char *fmt, ...);

#endif
