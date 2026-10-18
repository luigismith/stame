/* midi_parse.h — dai byte MIDI ai messaggi completi (sezione 40, MIDI-001 strato 2, MIDI-005, MIDI-006).
 *
 * Un parser per porta: il running status vale per un flusso di byte solo. Il buffer dei SysEx
 * (4096 byte) sta dentro midi_parser_t, che il chiamante alloca staticamente: niente heap.
 *
 *     static midi_parser_t mpk1;
 *     midi_parser_init(&mpk1, MIDI_PORT_CTL);
 *     midi_msg_t m[MIDI_PARSE_MAX_OUT];
 *     int n = midi_parse_byte(&mpk1, b, t_us, m);   // 0, 1 o 2 messaggi
 */
#ifndef STAME_MIDI_PARSE_H
#define STAME_MIDI_PARSE_H

#include "stame_base.h"

#define MIDI_SX_MAX        4096   /* MIDI-005: SysEx più lunghi vengono troncati e marcati non validi */
#define MIDI_PARSE_MAX_OUT 2      /* uno status che chiude un SysEx può completare anche un messaggio suo (F6) */

/* Porte della MPK (§8.1): la porta 1 (cable 0) va al profilo, la porta 2 (cable 1) all'ingresso
 * MIDI dell'originale (MIDI-072). */
enum { MIDI_PORT_CTL = 0, MIDI_PORT_DIN = 1 };

typedef struct {
    uint32_t t_us;          /* arrivo del byte che completa il messaggio, orologio monotono (MIDI-006) */
    uint8_t  port;          /* MIDI_PORT_* */
    uint8_t  n;             /* byte in b[]: 1..3; 0 per un SysEx */
    uint8_t  b[3];          /* status e dati; un Note On con velocity 0 arriva già come Note Off 8n */
    uint8_t  sysex;         /* 1 = SysEx: i byte, F0 e F7 compresi, sono in sx[0..sx_n) */
    uint8_t  valid;         /* 0 = SysEx troncato a MIDI_SX_MAX byte */
    uint16_t sx_n;
    const uint8_t *sx;      /* buffer del parser: valido fino alla prossima chiamata di midi_parse_byte */
} midi_msg_t;

typedef struct {
    uint8_t  port;
    uint8_t  st;            /* running status; 0 = nessuno */
    uint8_t  need, n;       /* byte di dati attesi e ricevuti */
    uint8_t  d[2];
    uint8_t  in_sx, sx_over;
    uint16_t sx_n;
    uint8_t  sx[MIDI_SX_MAX];
} midi_parser_t;

void midi_parser_init(midi_parser_t *p, uint8_t port);

/* Dà un byte al parser; scrive in out[] i messaggi completati (al massimo MIDI_PARSE_MAX_OUT)
 * e ritorna quanti. */
int midi_parse_byte(midi_parser_t *p, uint8_t b, uint32_t t_us, midi_msg_t out[MIDI_PARSE_MAX_OUT]);

/* Byte del messaggio così come li vuole on_midi dei profili (MIDI-101). */
static inline const uint8_t *midi_msg_data(const midi_msg_t *m) { return m->sysex ? m->sx : m->b; }
static inline uint16_t midi_msg_len(const midi_msg_t *m) { return m->sysex ? m->sx_n : m->n; }

#endif
