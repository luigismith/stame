/* test_midi.c — parser MIDI (sezione 40, MIDI-005): running status, real time ovunque, SysEx nel
 * buffer statico e troncati, dati orfani, Note On a velocity 0 (PLT-075). */
#include "test.h"
#include "core/midi_parse.h"
#include <string.h>

typedef struct {
    uint8_t  b[8];          /* primi byte del messaggio */
    uint8_t  last;          /* ultimo byte (per i SysEx lunghi) */
    uint16_t n;
    uint8_t  sysex, valid, port;
    uint32_t t_us;
} got_t;

static midi_parser_t P;
static got_t GOT[32];
static int NGOT;

static void start(uint8_t port)
{
    midi_parser_init(&P, port);
    NGOT = 0;
}

/* un byte, all'istante t; ritorna quanti messaggi ha chiuso */
static int byte_at(uint8_t b, uint32_t t)
{
    midi_msg_t out[MIDI_PARSE_MAX_OUT];
    int k = midi_parse_byte(&P, b, t, out);
    for (int j = 0; j < k && NGOT < 32; j++) {
        got_t *g = &GOT[NGOT++];
        const uint8_t *d = midi_msg_data(&out[j]);
        memset(g, 0, sizeof *g);
        g->n = midi_msg_len(&out[j]);
        for (int x = 0; x < g->n && x < 8; x++) g->b[x] = d[x];
        g->last = d[g->n - 1];
        g->sysex = out[j].sysex;
        g->valid = out[j].valid;
        g->port = out[j].port;
        g->t_us = out[j].t_us;
    }
    return k;
}

/* byte esadecimali separati da spazi, il primo all'istante 1000 e poi uno ogni µs */
static void feed(const char *hex)
{
    uint32_t t = 1000;
    for (const char *p = hex; *p; ) {
        while (*p == ' ') p++;
        if (!*p) break;
        unsigned v = 0;
        for (int i = 0; i < 2; i++, p++) v = v * 16 + (unsigned)(*p <= '9' ? *p - '0' : *p - 'A' + 10);
        byte_at((uint8_t)v, t++);
    }
}

/* il messaggio i è esattamente questi byte */
static bool is(int i, const char *hex)
{
    uint8_t want[8];
    int n = 0;
    for (const char *p = hex; *p && n < 8; ) {
        while (*p == ' ') p++;
        if (!*p) break;
        unsigned v = 0;
        for (int k = 0; k < 2; k++, p++) v = v * 16 + (unsigned)(*p <= '9' ? *p - '0' : *p - 'A' + 10);
        want[n++] = (uint8_t)v;
    }
    return i < NGOT && GOT[i].n == n && memcmp(GOT[i].b, want, (size_t)n) == 0;
}

static void t_canale(void)
{
    start(MIDI_PORT_CTL);
    feed("90 3C 64");
    CHECK_EQ(NGOT, 1);
    CHECK(is(0, "90 3C 64"));
    CHECK(GOT[0].valid && !GOT[0].sysex);
    CHECK_EQ(GOT[0].port, MIDI_PORT_CTL);
    CHECK_EQ(GOT[0].t_us, 1002);                                  /* MIDI-006: tempo dell'ultimo byte */

    /* running status, anche per i messaggi a un dato */
    start(MIDI_PORT_DIN);
    feed("90 3C 64 3E 50 C0 05 06 E0 00 40 7F");
    CHECK_EQ(NGOT, 5);
    CHECK(is(0, "90 3C 64"));
    CHECK(is(1, "90 3E 50"));
    CHECK(is(2, "C0 05"));
    CHECK(is(3, "C0 06"));
    CHECK(is(4, "E0 00 40"));
    CHECK_EQ(GOT[1].port, MIDI_PORT_DIN);
    CHECK_EQ(P.n, 1);                                             /* 7F: il secondo bend aspetta */

    /* Note On a velocity 0 = Note Off; il running status resta 90 */
    start(MIDI_PORT_CTL);
    feed("91 3C 00 3C 64");
    CHECK_EQ(NGOT, 2);
    CHECK(is(0, "81 3C 00"));
    CHECK(is(1, "91 3C 64"));

    /* uno status nuovo butta via un messaggio incompleto */
    start(MIDI_PORT_CTL);
    feed("90 3C B0 07 64");
    CHECK_EQ(NGOT, 1);
    CHECK(is(0, "B0 07 64"));
}

static void t_real_time(void)
{
    /* dentro un messaggio di canale, senza interromperlo né toccare il running status */
    start(MIDI_PORT_CTL);
    feed("90 3C F8 64 FE 3E FA 64");
    CHECK_EQ(NGOT, 5);
    CHECK(is(0, "F8"));
    CHECK(is(1, "90 3C 64"));
    CHECK(is(2, "FE"));
    CHECK(is(3, "FA"));
    CHECK(is(4, "90 3E 64"));

    /* dentro un SysEx */
    start(MIDI_PORT_CTL);
    feed("F0 7E F8 7F 06 FC 01 F7");
    CHECK_EQ(NGOT, 3);
    CHECK(is(0, "F8"));
    CHECK(is(1, "FC"));
    CHECK(is(2, "F0 7E 7F 06 01 F7"));
    CHECK(GOT[2].sysex && GOT[2].valid);
}

static void t_sysex(void)
{
    /* chiuso da F7 */
    start(MIDI_PORT_CTL);
    feed("F0 7E 7F 06 02 F7 90 3C 64");
    CHECK_EQ(NGOT, 2);
    CHECK(is(0, "F0 7E 7F 06 02 F7"));
    CHECK(GOT[0].sysex && GOT[0].valid);
    CHECK(is(1, "90 3C 64"));

    /* chiuso da uno status di canale: il SysEx resta valido e lo status vale */
    start(MIDI_PORT_CTL);
    feed("F0 01 02 90 3C 64");
    CHECK_EQ(NGOT, 2);
    CHECK(is(0, "F0 01 02 F7"));
    CHECK(GOT[0].valid);
    CHECK(is(1, "90 3C 64"));

    /* chiuso da un altro F0 */
    start(MIDI_PORT_CTL);
    feed("F0 01 F0 02 F7");
    CHECK_EQ(NGOT, 2);
    CHECK(is(0, "F0 01 F7"));
    CHECK(is(1, "F0 02 F7"));

    /* chiuso da F6: due messaggi dallo stesso byte (MIDI_PARSE_MAX_OUT) */
    start(MIDI_PORT_CTL);
    feed("F0 01");
    CHECK_EQ(byte_at(0xF6, 2000), 2);
    CHECK(is(0, "F0 01 F7"));
    CHECK(is(1, "F6"));

    /* esattamente 4096 byte con F0 e F7: valido */
    start(MIDI_PORT_CTL);
    byte_at(0xF0, 1);
    for (int i = 0; i < MIDI_SX_MAX - 2; i++) byte_at((uint8_t)(i & 0x7F), 2);
    byte_at(0xF7, 3);
    CHECK_EQ(NGOT, 1);
    CHECK_EQ(GOT[0].n, MIDI_SX_MAX);
    CHECK(GOT[0].valid);
    CHECK_EQ(GOT[0].last, 0xF7);

    /* un byte in più: troncato e non valido (MIDI-005), poi il parser riparte */
    start(MIDI_PORT_CTL);
    byte_at(0xF0, 1);
    for (int i = 0; i < MIDI_SX_MAX - 1; i++) byte_at(0x11, 2);
    byte_at(0xF7, 3);
    CHECK_EQ(NGOT, 1);
    CHECK(GOT[0].sysex && !GOT[0].valid);
    CHECK_EQ(GOT[0].n, MIDI_SX_MAX);
    CHECK_EQ(GOT[0].last, 0xF7);
    byte_at(0x90, 4); byte_at(0x3C, 5); byte_at(0x64, 6);
    CHECK_EQ(NGOT, 2);
    CHECK(is(1, "90 3C 64"));
}

static void t_orfani_e_sistema(void)
{
    /* dati orfani: all'avvio, dopo un SysEx, dopo F1–F3 e dopo un F7 isolato */
    start(MIDI_PORT_CTL);
    feed("3C 64 F0 01 F7 3C 64 F2 01 02 03 04 F1 10 20 F3 05 06 F7 3C 64");
    CHECK_EQ(NGOT, 4);
    CHECK(is(0, "F0 01 F7"));
    CHECK(is(1, "F2 01 02"));
    CHECK(is(2, "F1 10"));
    CHECK(is(3, "F3 05"));

    /* F7 senza SysEx: ignorato, e annulla il running status */
    start(MIDI_PORT_CTL);
    feed("90 3C 64 F7 3E 64 90 40 64");
    CHECK_EQ(NGOT, 2);
    CHECK(is(0, "90 3C 64"));
    CHECK(is(1, "90 40 64"));

    /* F6 è un messaggio di un byte e annulla il running status */
    start(MIDI_PORT_CTL);
    feed("90 3C 64 F6 3E 64");
    CHECK_EQ(NGOT, 2);
    CHECK(is(1, "F6"));
}

void test_midi(void)
{
    t_canale();
    t_real_time();
    t_sysex();
    t_orfani_e_sistema();
}
