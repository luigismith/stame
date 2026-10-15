/* test_motore.c — performance, Beat, looper e clock (specifica 10, §13.8–§13.9: TV-90…103, TV-110…116). */
#include "test.h"
#include "../../src/core/motore.h"
#include <math.h>

static perf_t P;
static perf_ev_t E[256];
static int NE;

/* esegue la performance fino al tick t (incluso), accumulando gli eventi */
static void run_to(uint32_t from, uint32_t to)
{
    for (uint32_t t = from; t <= to; t++) NE += perf_run(&P, t, E + NE, 256 - NE);
}

static void start(uint8_t mode, uint8_t amount, const uint8_t *notes, uint8_t n, uint8_t vel)
{
    perf_init(&P, 1);
    perf_set(&P, mode, amount);
    NE = perf_chord(&P, 0, notes, n, vel, true, false, E, 256);
}

/* l'evento k è (tick, nota, acceso)? */
static bool ev_is(int k, uint32_t tick, uint8_t note, bool on)
{
    return k < NE && E[k].tick == tick && E[k].note == note && (E[k].on != 0) == on;
}

static int ons(void)
{
    int c = 0;
    for (int i = 0; i < NE; i++) if (E[i].on) c++;
    return c;
}

static const uint8_t C_MAJ[3] = { 48, 52, 55 };
static const uint8_t C_MAJ7[4] = { 48, 52, 55, 59 };
static const uint8_t G_MAJ[3] = { 50, 55, 59 };

static void test_strum_harp(void)
{
    start(PM_STRUM, 1, C_MAJ, 3, 100);                            /* TV-90 */
    run_to(0, 20);
    CHECKM(ev_is(0, 0, 48, true) && ev_is(1, 2, 52, true) && ev_is(2, 4, 55, true) && NE == 3, "TV-90");
    NE += perf_release(&P, 30, E + NE, 256 - NE);
    CHECK_EQ(NE, 6);                                              /* tutti OFF al rilascio */

    start(PM_STRUM, 10, C_MAJ, 3, 100);                           /* TV-91 */
    run_to(0, 50);
    CHECKM(ev_is(1, 20, 52, true) && ev_is(2, 40, 55, true), "TV-91");

    start(PM_STRUM2, 1, C_MAJ, 3, 100);                           /* TV-92 */
    run_to(0, 20);
    static const uint8_t S2[6] = { 48, 52, 55, 60, 64, 67 };
    bool ok = NE == 6;
    for (int i = 0; i < 6 && ok; i++) ok = ev_is(i, (uint32_t)(2 * i), S2[i], true);
    CHECKM(ok, "TV-92");

    start(PM_HARP, 1, C_MAJ, 3, 100);                             /* TV-93 */
    run_to(0, 20);
    static const uint8_t H[9] = { 48, 52, 55, 60, 64, 67, 72, 76, 79 };
    ok = NE == 9;
    for (int i = 0; i < 9 && ok; i++) ok = ev_is(i, (uint32_t)i, H[i], true);
    CHECKM(ok, "TV-93");

    start(PM_STRUM, 1, C_MAJ, 3, 100);                            /* TV-103: rilascio a 700 campioni */
    run_to(0, 2);
    NE += perf_release(&P, 3, E + NE, 256 - NE);
    run_to(4, 20);
    CHECKM(NE == 4 && ev_is(2, 3, 48, false) && ev_is(3, 3, 52, false), "TV-103: il 55 non deve partire");
}

static void test_arp(void)
{
    start(PM_ARP, 4, C_MAJ, 3, 100);                              /* TV-94 */
    run_to(0, 72);
    CHECKM(ev_is(0, 0, 48, true) && ev_is(1, 12, 48, false) && ev_is(2, 24, 52, true) && ev_is(3, 36, 52, false) &&
           ev_is(4, 48, 55, true) && ev_is(5, 60, 55, false) && ev_is(6, 72, 48, true), "TV-94");

    start(PM_ARP, 3, C_MAJ, 3, 100);                              /* TV-95: 8 UpDown, gate 24 */
    run_to(0, 48 * 5);
    static const uint8_t UD[6] = { 48, 52, 55, 52, 48, 52 };
    bool ok = true;
    for (int i = 0; i < 6 && ok; i++) ok = ev_is(2 * i, (uint32_t)(48 * i), UD[i], true) &&
                                          (i == 5 || ev_is(2 * i + 1, (uint32_t)(48 * i + 24), UD[i], false));
    CHECKM(ok, "TV-95");

    start(PM_ARP, 2, C_MAJ7, 4, 100);                             /* TV-96: 8 Down */
    run_to(0, 48 * 4);
    CHECKM(ev_is(0, 0, 59, true) && ev_is(2, 48, 55, true) && ev_is(4, 96, 52, true) && ev_is(6, 144, 48, true) &&
           ev_is(8, 192, 59, true), "TV-96");

    start(PM_ARP2, 1, C_MAJ, 3, 100);                             /* TV-97: 2 ottave, 8 Up */
    run_to(0, 48 * 6);
    static const uint8_t A2[7] = { 48, 52, 55, 60, 64, 67, 48 };
    ok = true;
    for (int i = 0; i < 7 && ok; i++) ok = ev_is(2 * i, (uint32_t)(48 * i), A2[i], true);
    CHECKM(ok, "TV-97");

    start(PM_ARP, 4, C_MAJ, 3, 100);                              /* TV-98: legato */
    run_to(0, 27);
    int before = NE;
    NE += perf_chord(&P, 28, G_MAJ, 3, 100, true, true, E + NE, 256 - NE);
    CHECKM(NE == before + 1 && ev_is(before, 28, 52, false), "TV-98: OFF di 52 al cambio legato");
    run_to(28, 48);
    CHECKM(ev_is(NE - 1, 48, 59, true), "TV-98: il passo 2 suona l'indice 2 di {50 55 59}");
}

static void test_pattern_slop(void)
{
    start(PM_PATTERN, 5, C_MAJ, 3, 127);                          /* TV-99 */
    run_to(0, 72);
    CHECKM(ev_is(0, 0, 48, true) && E[0].vel == 127 && ev_is(1, 20, 48, false) && ev_is(2, 24, 52, true) &&
           E[2].vel == 100 && ev_is(4, 48, 55, true) && ev_is(6, 72, 52, true), "TV-99");

    start(PM_PATTERN, 5, C_MAJ, 3, 64);                           /* TV-100 */
    run_to(0, 24);
    CHECKM(E[0].vel == 64 && E[2].vel == 50, "TV-100: vel %d e %d", E[0].vel, E[2].vel);

    start(PM_SLOP, 5, C_MAJ, 3, 100);                             /* TV-101 */
    run_to(0, 40);
    uint32_t t1[3];
    bool ok = ons() == 3;
    for (int i = 0; i < 3 && ok; i++) {
        t1[i] = E[i].tick;
        ok = E[i].tick >= (uint32_t)(2 * i) && E[i].tick <= (uint32_t)(2 * i + 15);
    }
    CHECKM(ok, "TV-101: tempi fuori da i·2 + [0, 15]");
    start(PM_SLOP, 5, C_MAJ, 3, 100);
    run_to(0, 40);
    ok = ons() == 3;
    for (int i = 0; i < 3 && ok; i++) ok = E[i].tick == t1[i];
    CHECKM(ok, "TV-101: con lo stesso seme la sequenza è la stessa");
    NE += perf_release(&P, 41, E + NE, 256 - NE);
    int k0 = NE;
    NE += perf_chord(&P, 100, C_MAJ, 3, 100, true, false, E + NE, 256 - NE);
    run_to(100, 140);
    bool diff = false;
    for (int i = 0; i < 3; i++) if (E[k0 + i].tick - 100 != t1[i]) diff = true;
    CHECKM(diff, "TV-101: alla pressione successiva la sequenza cambia");
}

static void test_looper(void)
{
    static looper_t L;
    loop_ev_t ev[64];
    loop_init(&L);                                                /* TV-113: count-in, REC, PLAY con BARS_1 */
    loop_set_len(&L, 384, 1);
    loop_cmd(&L, LOOP_C_PRESS, 0, ev, 64);
    bool ok = L.state == LOOP_COUNT_IN;
    for (uint32_t t = 0; t < 384; t++) { loop_run(&L, t, ev, 64); ok = ok && L.state == LOOP_COUNT_IN; }
    loop_run(&L, 384, ev, 64);
    ok = ok && L.state == LOOP_REC;
    for (uint32_t t = 385; t < 768; t++) { loop_run(&L, t, ev, 64); ok = ok && L.state == LOOP_REC; }
    loop_run(&L, 768, ev, 64);
    CHECKM(ok && L.state == LOOP_PLAY && L.len == 384, "TV-113");

    loop_init(&L);                                                /* 4 battute di 4/4 dopo il count-in */
    loop_cmd(&L, LOOP_C_PRESS, 1000 - 384, ev, 64);
    CHECK_EQ(L.state, LOOP_COUNT_IN);
    loop_record(&L, 1000 - 30, LOOP_TREBLE, 64, 100);             /* troppo presto: non entra */
    loop_record(&L, 1000 - 20, LOOP_TREBLE, 67, 100);             /* anticipo di 20 tick: entra a t = 0 */
    CHECK(L.n == 1 && L.ev[0].t == 0 && L.ev[0].note == 67);
    loop_run(&L, 1000, ev, 64);
    CHECK_EQ(L.state, LOOP_REC);
    loop_record(&L, 1005, LOOP_TREBLE, 67, 0);
    loop_record(&L, 1010, LOOP_TREBLE, 60, 100);
    loop_record(&L, 1050, LOOP_TREBLE, 60, 0);
    loop_record(&L, 1100, LOOP_BASS, 36, 90);                     /* tenuta fino alla fine del loop */
    int n = 0;
    for (uint32_t t = 1000; t < 1000 + 1536; t++) n += loop_run(&L, t, ev, 64);
    CHECK_EQ(n, 0);                                               /* in REC non si suona */
    n = loop_run(&L, 1000 + 1536, ev, 64);
    CHECK_EQ(L.state, LOOP_PLAY);
    int on60 = 0, off36 = 0;
    for (uint32_t t = 1000 + 1537; t < 1000 + 2 * 1536; t++) {
        n = loop_run(&L, t, ev, 64);
        for (int i = 0; i < n; i++) {
            if (ev[i].note == 60 && ev[i].vel && t == 1000 + 1536 + 10) on60++;
            if (ev[i].note == 36 && !ev[i].vel && t == 1000 + 1536 + 1535) off36++;
        }
    }
    CHECKM(on60 == 1, "looper: il 60 suona di nuovo al tick 10 del giro");
    CHECKM(off36 == 1, "ACC-225: la nota tenuta riceve il note-off alla fine del loop");
    loop_cmd(&L, LOOP_C_PRESS, 5000, ev, 64);                     /* overdub */
    CHECK_EQ(L.state, LOOP_OVERDUB);
    CHECK_EQ(L.layers, 2);
    uint16_t before = L.n;
    loop_record(&L, 5000, LOOP_TREBLE, 72, 100);
    loop_record(&L, 5010, LOOP_TREBLE, 72, 0);
    CHECK_EQ(L.n, before + 2);
    loop_cmd(&L, LOOP_C_UNDO, 5020, ev, 64);
    CHECK_EQ(L.n, before);
    CHECK_EQ(L.layers, 1);
    loop_cmd(&L, LOOP_C_UNDO, 5030, ev, 64);                      /* TV-116: con il solo strato 0 vale Clear */
    CHECK_EQ(L.state, LOOP_IDLE);
    CHECK_EQ(L.n, 0);
}

static void test_clock_beat(void)
{
    static dsp_t D;
    static motore_t M;
    dsp_init(&D, 48000.0f, 1);
    mot_init(&M, &D, 48000, 1);
    CHECK_EQ((long long)mot_tick_sample(&M, 9600), 2400000LL);    /* TV-110 */
    mot_init(&M, &D, 44100, 1);
    mot_bpm(&M, 97);
    double exact = 1000000.0 * 44100.0 * 60.0 / (97.0 * 96.0);
    double got = (double)mot_tick_sample(&M, 1000000);
    CHECKM(fabs(got - exact) < 1.0, "TV-111: %.3f contro %.3f", got, exact);

    beat_hit_t h[4];                                              /* TV-112 */
    CHECK(metro_hits(METER_4_4, 0, h, 4) == 1 && h[0].inst == DRUM_CLICK_ACCENT);
    CHECK(metro_hits(METER_4_4, 96, h, 4) == 1 && h[0].inst == DRUM_CLICK);
    CHECK(metro_hits(METER_4_4, 192, h, 4) == 1 && metro_hits(METER_4_4, 288, h, 4) == 1);
    CHECK(metro_hits(METER_4_4, 48, h, 4) == 0);
    CHECK(metro_hits(METER_4_4, 384, h, 4) == 1 && h[0].inst == DRUM_CLICK_ACCENT);
    /* ACC-207: in 3/4 l'accento torna ogni 288 tick; in 6/8 un clic per croma, accenti sulla 1 e sulla 4 */
    CHECK(metro_hits(METER_3_4, 288, h, 4) == 1 && h[0].inst == DRUM_CLICK_ACCENT);
    CHECK(metro_hits(METER_6_8, 48, h, 4) == 1 && h[0].inst == DRUM_CLICK);
    CHECK(metro_hits(METER_6_8, 144, h, 4) == 1 && h[0].inst == DRUM_CLICK_ACCENT);
    CHECK(metro_hits(METER_6_8, 24, h, 4) == 0);

    /* il motore: un arpeggio e il metronomo suonano davvero (voci del synth e della batteria) */
    dsp_init(&D, 48000.0f, 1);
    mot_init(&M, &D, 48000, 1);
    mot_perf(&M, PM_ARP, 4);
    mot_beat(&M, BEAT_M_METRONOME, 1);
    CHECK_EQ(M.tr_on, 0);                                         /* selezionare non avvia (ACC-205) */
    mot_beat_on(&M, true);
    CHECK(M.tr_on == 1 && M.tr_t0 == 0);
    mot_chord_start(&M);
    for (int i = 0; i < 3; i++) mot_note(&M, 0, C_MAJ[i], 100);
    mot_note(&M, 1, 36, 100);                                     /* TV-102: il basso parte subito */
    CHECK_EQ(dsp_voices_active(&D), 1);
    static float l[4800], r[4800];
    mot_render(&M, l, r, 4800);                                   /* 100 ms: 4 tick per … */
    CHECK(dsp_voices_active(&D) >= 2);
    bool drum = false;
    for (int i = 0; i < DRUM_VOICES; i++) if (M.drums.v[i].on || M.drums.v[i].t > 0.0f) drum = true;
    CHECK(drum);
    CHECK(M.snap.tr_on == 1 && M.snap.bpm == 120 && M.snap.tick > 0);
}

/* trasporto condiviso fra Beat e looper (ACC-204, ACC-205, ACC-222) e transpose sul loop (ACC-220, ACC-221) */
static void test_transport_loop(void)
{
    static dsp_t D;
    static motore_t M;
    static float l[16], r[16];
    dsp_init(&D, 48000.0f, 1);
    mot_init(&M, &D, 48000, 1);
    while (M.tick < 1000) mot_render(&M, l, r, 16);
    uint32_t t_rec = M.tick;
    mot_loop(&M, LOOP_C_PRESS);                                   /* trasporto fermo: parte con il count-in */
    CHECK(M.tr_on == 1 && M.tr_t0 == t_rec && M.loop.state == LOOP_COUNT_IN && M.loop.t0 == t_rec + 384);
    while (M.tick < t_rec + 384 + 10) mot_render(&M, l, r, 16);
    CHECK_EQ(M.loop.state, LOOP_REC);
    mot_transpose(&M, 2);
    mot_note(&M, 1, 40, 100);                                     /* basso suonato con transpose +2 */
    while (M.tick < t_rec + 384 + 40) mot_render(&M, l, r, 16);
    mot_transpose(&M, 5);                                         /* il note-off arriva con un altro transpose */
    mot_note(&M, 1, 40, 0);
    CHECK(M.loop.n == 2 && M.loop.ev[0].note == 38 && M.loop.ev[1].note == 38 && M.loop.ev[1].vel == 0);

    mot_beat_on(&M, true);                                        /* col looper in moto il Beat non sposta la battuta 1 */
    CHECK_EQ(M.tr_t0, t_rec);
    mot_beat_on(&M, false);
    CHECK(M.tr_on == 1 && M.tr_t0 == t_rec);                      /* il tempo del loop continua */

    while (M.tick < t_rec + 384 + 1536 + 12) mot_render(&M, l, r, 16);   /* il loop suona: 38 + 5 */
    CHECK_EQ(M.loop.state, LOOP_PLAY);
    CHECK_EQ(M.lp_out[1][38], 43);
    CHECK(M.snap.lp_notes[1][43 >> 3] & (1u << (43 & 7)));
    mot_transpose(&M, 0);                                         /* il note-off spegne il 43 già partito */
    while (M.tick < t_rec + 384 + 1536 + 45) mot_render(&M, l, r, 16);
    CHECK_EQ(M.lp_out[1][38], MOT_NONE);

    mot_loop(&M, LOOP_C_STOP);                                    /* pausa: il trasporto si ferma */
    CHECK(M.loop.state == LOOP_PAUSE && M.tr_on == 0);
    while (M.tick < t_rec + 4000) mot_render(&M, l, r, 16);
    uint32_t t_play = M.tick;
    mot_loop(&M, LOOP_C_STOP);                                    /* ripresa: loop e trasporto ripartono insieme */
    CHECK(M.loop.state == LOOP_PLAY && M.loop.t0 == t_play && M.tr_on == 1 && M.tr_t0 == t_play);
    mot_loop(&M, LOOP_C_CLEAR);
    CHECK(M.loop.state == LOOP_IDLE && M.tr_on == 0);
}

void test_motore(void)
{
    test_strum_harp();
    test_arp();
    test_pattern_slop();
    test_looper();
    test_clock_beat();
    test_transport_loop();
}
