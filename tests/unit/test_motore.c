/* test_motore.c — performance, Beat, looper e clock (specifica 10, §13.8–§13.9: TV-90…103, TV-110…121). */
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

/* comandi a tempo (la demo della vetrina): mot_due dice quando applicarli perché valgano dal loro tick */
static void test_due(void)
{
    static dsp_t D;
    static motore_t M;
    static float l[16], r[16];
    dsp_init(&D, 48000.0f, 1);
    mot_init(&M, &D, 48000, 1);                                   /* 120 BPM: un tick ogni 250 campioni */
    CHECK(mot_due(&M, 0) && !mot_due(&M, 1));
    for (int i = 0; i < 15; i++) mot_render(&M, l, r, 16);        /* 240 campioni: il tick 1 cade a 250 */
    CHECK(M.tick == 1 && mot_due(&M, 1) && !mot_due(&M, 2));
    mot_render(&M, l, r, 16);
    CHECK(M.tick == 2 && mot_due(&M, 1) && !mot_due(&M, 2));     /* in ritardo: subito */

    /* un accordo con il Pattern, applicato quando mot_due lo dice, parte proprio dal suo tick (ACC-173) */
    mot_perf(&M, PM_PATTERN, 5);
    while (!mot_due(&M, 100)) mot_render(&M, l, r, 16);
    CHECK_EQ(M.tick, 100);
    mot_chord_start(&M);
    for (int i = 0; i < 3; i++) mot_note(&M, 0, C_MAJ[i], 100);
    mot_render(&M, l, r, 16);
    CHECK(M.perf.active && M.perf.step == 1 && M.perf.next == 124);
}

/* ACC-211, ACC-212: batteria a tastiera nel loop, quantizzata al sedicesimo; il colpo suona dal vivo e al giro dopo */
static void test_drum_loop(void)
{
    static dsp_t D;
    static motore_t M;
    static float l[16], r[16];
    dsp_init(&D, 48000.0f, 1);
    mot_init(&M, &D, 48000, 1);                                   /* 120 BPM: 250 campioni per tick */
    mot_loop(&M, LOOP_C_PRESS);                                   /* count-in di 384 tick, poi 4 battute */
    while (M.tick < 384 + 100) mot_render(&M, l, r, 16);
    CHECK_EQ(M.loop.state, LOOP_REC);
    mot_drum(&M, DRUM_SNARE, 100);                                /* tick 484: quantizzato a 480, t = 96 nel loop */
    CHECK_EQ(M.loop.n, 1);
    CHECK(M.loop.ev[0].role == LOOP_DRUM && M.loop.ev[0].t == 96 && M.loop.ev[0].note == DRUM_SNARE && M.loop.ev[0].vel == 100);
    bool on = false;
    for (int i = 0; i < DRUM_VOICES; i++) if (M.drums.v[i].on && M.drums.v[i].inst == DRUM_SNARE) on = true;
    CHECK(on);                                                    /* dal vivo suona subito */
    drums_all_off(&M.drums);
    mot_drum(&M, DRUM_KICK, 0);                                   /* velocity 0: niente */
    CHECK_EQ(M.loop.n, 1);
    while (M.tick <= 384 + 1536 + 96) mot_render(&M, l, r, 16);   /* il giro dopo: il rullante torna al tick 96 (tick_run gira prima di tick++) */
    CHECK_EQ(M.loop.state, LOOP_PLAY);
    on = false;
    for (int i = 0; i < DRUM_VOICES; i++) if (M.drums.v[i].on && M.drums.v[i].inst == DRUM_SNARE) on = true;
    CHECK(on);
    /* overdub: un colpo quantizzato in avanti si registra ma non si risuona nello stesso giro */
    mot_loop(&M, LOOP_C_OVERDUB);
    CHECK_EQ(M.loop.state, LOOP_OVERDUB);
    while (M.tick < 384 + 1536 + 206) mot_render(&M, l, r, 16);  /* tick 2126: pos 206 → quantizzato avanti a 216 */
    drums_all_off(&M.drums);
    mot_drum(&M, DRUM_COWBELL, 90);
    CHECK_EQ(M.loop.n, 2);
    CHECK(M.loop.ev[1].t == 216 && M.loop.ev[1].skip == 1);
    while (M.tick <= 384 + 1536 + 216) mot_render(&M, l, r, 16);
    on = false;
    for (int i = 0; i < DRUM_VOICES; i++) if (M.drums.v[i].on && M.drums.v[i].inst == DRUM_COWBELL && M.drums.v[i].t > 0.03f) on = true;
    CHECK(on);                                                    /* c'è solo il colpo dal vivo, invecchiato */
    bool fresh = false;
    for (int i = 0; i < DRUM_VOICES; i++) if (M.drums.v[i].on && M.drums.v[i].inst == DRUM_COWBELL && M.drums.v[i].t < 0.01f) fresh = true;
    CHECK(!fresh);                                                /* nessun secondo colpo (flam) */
    CHECK_EQ(M.loop.ev[1].skip, 0);                               /* al giro dopo suonerà */
}

/* ---- revisione del 15/10/2026: i difetti trovati, ciascuno con il suo caso ---- */

static int out_note(const loop_ev_t *ev, int n, uint8_t note, bool on)
{
    int c = 0;
    for (int i = 0; i < n; i++) if (ev[i].note == note && (ev[i].vel != 0) == on) c++;
    return c;
}

static bool any_hit(const motore_t *m, uint8_t inst)
{
    for (int i = 0; i < DRUM_VOICES; i++) if (m->drums.v[i].on && m->drums.v[i].inst == inst) return true;
    return false;
}

/* il motore fino al tick t compreso, con la batteria spenta appena prima: suona solo ciò che esce a t */
static void render_tick(motore_t *m, uint32_t t)
{
    static float l[16], r[16];
    while (m->tick < t) mot_render(m, l, r, 16);
    drums_all_off(&m->drums);
    while (m->tick <= t) mot_render(m, l, r, 16);
}

static void test_looper_revisione(void)
{
    static looper_t L;
    static loop_ev_t ev[LOOP_OUT_MAX];
    /* un loop di una battuta: t0 = 384, len = 384 */
    loop_init(&L);
    loop_set_len(&L, 384, 1);
    loop_cmd(&L, LOOP_C_PRESS, 0, ev, LOOP_OUT_MAX);
    for (uint32_t t = 0; t < 768; t++) loop_run(&L, t, ev, LOOP_OUT_MAX);
    /* ACC-225: la registrazione finisce a t0 + len; una nota su quel tick non entra (era un bordone) */
    loop_record(&L, 768, LOOP_TREBLE, 62, 100);
    CHECK_EQ(L.n, 0);
    loop_run(&L, 768, ev, LOOP_OUT_MAX);
    CHECK_EQ(L.state, LOOP_PLAY);
    for (uint32_t t = 769; t < 800; t++) loop_run(&L, t, ev, LOOP_OUT_MAX);

    /* overdub: la nota suonata dal vivo non si risuona nello stesso giro (doppio attacco), al giro dopo sì */
    loop_cmd(&L, LOOP_C_OVERDUB, 800, ev, LOOP_OUT_MAX);
    loop_record(&L, 800, LOOP_TREBLE, 60, 100);                   /* pos 32 */
    int n = loop_run(&L, 800, ev, LOOP_OUT_MAX);
    CHECKM(out_note(ev, n, 60, true) == 0, "overdub: nessun secondo note-on nello stesso tick");
    int on = 0, off = 0;
    for (uint32_t t = 801; t <= 810; t++) { n = loop_run(&L, t, ev, LOOP_OUT_MAX); on += out_note(ev, n, 60, true); }
    loop_record(&L, 810, LOOP_TREBLE, 60, 0);                     /* pos 42 */
    /* ACC-225: una nota tenuta oltre il punto di giro ha il note-off a t mod L */
    for (uint32_t t = 810; t < 1068; t++) loop_run(&L, t, ev, LOOP_OUT_MAX);
    loop_record(&L, 1068, LOOP_BASS, 40, 100);                    /* pos 300 */
    for (uint32_t t = 1068; t < 1202; t++) loop_run(&L, t, ev, LOOP_OUT_MAX);
    loop_record(&L, 1202, LOOP_BASS, 40, 0);                      /* pos 50 del giro dopo */
    loop_cmd(&L, LOOP_C_OVERDUB, 1203, ev, LOOP_OUT_MAX);         /* chiude lo strato */
    CHECK_EQ(L.state, LOOP_PLAY);
    int on40 = 0, off40_early = 0, off40_50 = 0, on60 = 0;
    for (uint32_t t = 1203; t < 1203 + 2 * 384; t++) {
        n = loop_run(&L, t, ev, LOOP_OUT_MAX);
        uint32_t pos = loop_pos(&L, t);
        on40 += out_note(ev, n, 40, true);
        if (pos < 50) off40_early += out_note(ev, n, 40, false);
        if (pos == 50) off40_50 += out_note(ev, n, 40, false);
        on60 += out_note(ev, n, 60, true);
        off += out_note(ev, n, 60, false);
    }
    CHECKM(on == 0 && on60 == 2 && off == 2, "overdub: il 60 torna una volta per giro (%d %d %d)", on, on60, off);
    CHECKM(on40 == 2 && off40_early == 0 && off40_50 == 2, "ACC-225: note-off a t mod L, non al giro (%d %d %d)",
           on40, off40_early, off40_50);

    /* UNDO: gli eventi al tick del comando, non ancora suonato, suonano */
    loop_cmd(&L, LOOP_C_OVERDUB, 1971, ev, LOOP_OUT_MAX);
    loop_record(&L, 1971, LOOP_TREBLE, 72, 100);
    for (uint32_t t = 1971; t < 2336; t++) loop_run(&L, t, ev, LOOP_OUT_MAX);    /* pos 2336 = 32 */
    loop_cmd(&L, LOOP_C_UNDO, 2336, ev, LOOP_OUT_MAX);
    n = loop_run(&L, 2336, ev, LOOP_OUT_MAX);
    CHECKM(out_note(ev, n, 60, true) == 1, "UNDO: il 60 a pos 32 suona al tick del comando");
    CHECK(L.full == 0);

    /* LOOP_C_RESET svuota anche durante l'overdub (Clear lì vale Undo dello strato) */
    loop_cmd(&L, LOOP_C_OVERDUB, 2400, ev, LOOP_OUT_MAX);
    CHECK_EQ(L.state, LOOP_OVERDUB);
    loop_cmd(&L, LOOP_C_RESET, 2401, ev, LOOP_OUT_MAX);
    CHECK(L.state == LOOP_IDLE && L.n == 0);
}

static void test_motore_revisione(void)
{
    static dsp_t D;
    static motore_t M;
    static float l[16], r[16];

    /* batteria: la griglia è quella del loop (t0), non il tick assoluto: t0 = 1389, 1389 mod 24 = 21 */
    dsp_init(&D, 48000.0f, 1);
    mot_init(&M, &D, 48000, 1);
    while (M.tick < 1005) mot_render(&M, l, r, 16);
    mot_loop(&M, LOOP_C_PRESS);
    uint32_t t0 = M.loop.t0;
    CHECK_EQ(t0, 1389);
    while (M.tick < t0 + 96) mot_render(&M, l, r, 16);
    mot_drum(&M, DRUM_SNARE, 100);                                /* proprio sul secondo battito */
    CHECKM(M.loop.n == 1 && M.loop.ev[0].t == 96, "ACC-211: colpo a t = %u, atteso 96", (unsigned)M.loop.ev[0].t);
    /* arrotondato oltre la fine della registrazione: entra a t = 0 e il primo giro non lo ripete */
    while (M.tick < t0 + 1536 - 5) mot_render(&M, l, r, 16);
    drums_all_off(&M.drums);
    mot_drum(&M, DRUM_COWBELL, 100);
    CHECK(M.loop.n == 2 && M.loop.ev[0].t == 0 && M.loop.ev[0].skip == 1);
    render_tick(&M, t0 + 1536);
    CHECK_EQ(M.loop.state, LOOP_PLAY);
    CHECKM(!any_hit(&M, DRUM_COWBELL), "nessun flam al primo giro");
    render_tick(&M, t0 + 2 * 1536);
    CHECKM(any_hit(&M, DRUM_COWBELL), "al secondo giro il colpo c'è");
    /* overdub, colpo arrotondato all'indietro: niente salto, suona al giro dopo */
    mot_loop(&M, LOOP_C_OVERDUB);
    while (M.tick < t0 + 2 * 1536 + 220) mot_render(&M, l, r, 16);
    mot_drum(&M, DRUM_CLAP, 100);                                 /* pos 220 → 216 */
    bool back = false;
    for (int i = 0; i < M.loop.n; i++) if (M.loop.ev[i].note == DRUM_CLAP) back = M.loop.ev[i].t == 216 && !M.loop.ev[i].skip;
    CHECK(back);
    render_tick(&M, t0 + 3 * 1536 + 216);
    CHECKM(any_hit(&M, DRUM_CLAP), "il colpo arrotondato all'indietro suona al giro dopo");

    /* ACC-253: una nota del loop alla stessa altezza di una tenuta dal vivo non la spegne */
    dsp_init(&D, 48000.0f, 1);
    mot_init(&M, &D, 48000, 1);
    mot_loop(&M, LOOP_C_PRESS);
    t0 = M.loop.t0;
    while (M.tick < t0 + 10) mot_render(&M, l, r, 16);
    mot_chord_start(&M);
    mot_note(&M, 0, 60, 100);
    while (M.tick < t0 + 200) mot_render(&M, l, r, 16);
    mot_note(&M, 0, 60, 0);
    while (M.tick < t0 + 1536 + 5) mot_render(&M, l, r, 16);
    mot_chord_start(&M);
    mot_note(&M, 0, 60, 100);                                     /* dal vivo da pos 5 */
    while (M.tick < t0 + 1536 + 210) mot_render(&M, l, r, 16);    /* il loop: on a 10, off a 200 */
    bool held = false;
    for (int i = 0; i < DSP_VOICES; i++) if (D.voice[i].note == 60 && D.voice[i].state == DSP_V_HELD) held = true;
    CHECKM(held, "ACC-253: il 60 tenuto dal vivo suona ancora dopo il note-off del loop");
    mot_note(&M, 0, 60, 0);
    mot_render(&M, l, r, 16);
    held = false;
    for (int i = 0; i < DSP_VOICES; i++) if (D.voice[i].note == 60 && D.voice[i].state == DSP_V_HELD) held = true;
    CHECK(!held);

    /* il clock non si ferma dopo 2³² campioni (24,85 h a 48 kHz): il prossimo tick è relativo al blocco */
    M.s = ((uint64_t)1 << 32) - 64u;
    uint32_t t1 = M.tick;
    for (int i = 0; i < 64; i++) mot_render(&M, l, r, 16);       /* 1024 campioni: 4 tick a 120 BPM */
    CHECK(M.tick >= t1 + 4 && M.tick <= t1 + 5);

    /* un gesto che non dà note treble non consuma il KEY_DOWN: le note che arrivano dopo partono dal passo 0 */
    dsp_init(&D, 48000.0f, 1);
    mot_init(&M, &D, 48000, 1);
    mot_perf(&M, PM_ARP, 1);
    mot_chord_start(&M);
    mot_note(&M, 1, 36, 100);                                     /* solo il basso */
    mot_render(&M, l, r, 16);
    for (int i = 0; i < 3; i++) mot_note(&M, 0, C_MAJ[i], 100);   /* poi le note treble del gesto */
    for (int i = 0; i < 20; i++) mot_render(&M, l, r, 16);        /* fino al tick dopo */
    CHECKM(M.perf.mode == PM_ARP && M.perf.active && M.perf.step >= 1, "ACC-182: il modo vale per le note del gesto");
}

static void test_perf_revisione(void)
{
    /* nessuna sequenza da continuare: si riparte dal passo 0, senza recuperare i passi persi */
    start(PM_ARP, 1, C_MAJ, 3, 100);
    run_to(0, 100);
    NE = perf_release(&P, 100, E, 256);
    NE = perf_chord(&P, 100000, G_MAJ, 3, 100, false, false, E, 256);
    run_to(100000, 100000);
    CHECKM(ons() <= 1, "nessuna raffica: %d note-on", ons());
    /* sequenza in corso ma arretrata (un blocco perso): un passo solo */
    start(PM_ARP, 4, C_MAJ, 3, 100);
    run_to(0, 0);
    NE = 0;
    run_to(5000, 5000);
    CHECK(ons() == 1);
    /* Strum su Do, poi Perform OFF e Sol legato: le note dello strum in coda non partono più */
    start(PM_STRUM, 10, C_MAJ, 3, 100);
    perf_set(&P, PM_OFF, 0);
    NE = perf_chord(&P, 5, G_MAJ, 3, 100, true, true, E, 256);
    CHECK_EQ(P.qn, 0);
    int k = NE;
    run_to(6, 60);
    bool c52 = false;
    for (int i = k; i < NE; i++) if (E[i].on && E[i].note == 52) c52 = true;
    CHECK(!c52);

    /* ACC-180 (16/10/2026): un'estensione aggiunta (ADD_NOTE) non fa ripartire lo strum: la nota nuova
     * parte subito, le note in coda arrivano al loro tempo */
    start(PM_STRUM, 10, C_MAJ, 3, 100);                           /* 48 a 0, 52 a 20, 55 a 40 */
    run_to(0, 25);
    int before = NE;
    NE += perf_add(&P, 26, C_MAJ7, 4, E + NE, 256 - NE);
    CHECKM(NE == before + 1 && ev_is(before, 26, 59, true), "ACC-180: la settima parte subito");
    run_to(27, 60);
    CHECKM(NE == before + 2 && ev_is(before + 1, 40, 55, true), "ACC-180: il 55 in coda al suo tempo, niente ripartenza");
    /* STRUM2: la nota nuova parte con la sua ottava */
    start(PM_STRUM2, 1, C_MAJ, 3, 100);
    run_to(0, 20);
    before = NE;
    NE += perf_add(&P, 21, C_MAJ7, 4, E + NE, 256 - NE);
    CHECK(NE == before + 2 && ev_is(before, 21, 59, true) && ev_is(before + 1, 21, 71, true));
    /* ARP: la nota nuova entra dal passo successivo, senza ripartire dal passo 0 */
    start(PM_ARP, 1, C_MAJ, 3, 100);                              /* Up, un passo ogni 48 tick */
    run_to(0, 50);                                                /* 48 e 52 suonate */
    before = NE;
    uint32_t step = P.step;
    NE += perf_add(&P, 51, C_MAJ7, 4, E + NE, 256 - NE);
    CHECK(NE == before && P.step == step);
    run_to(51, 144);
    CHECKM(ev_is(before, 72, 52, false) && ev_is(before + 1, 96, 55, true) && ev_is(before + 3, 144, 59, true),
           "ACC-180: l'arpeggio continua e la settima entra al suo passo");

    /* nel motore: Do maggiore in strum, poi la settima aggiunta senza KEY_DOWN né spegnimenti */
    static dsp_t D;
    static motore_t M;
    static float l[16], r[16];
    dsp_init(&D, 48000.0f, 1);
    mot_init(&M, &D, 48000, 1);
    mot_perf(&M, PM_STRUM, 10);
    mot_chord_start(&M);
    for (int i = 0; i < 3; i++) mot_note(&M, 0, C_MAJ[i], 100);
    mot_render(&M, l, r, 16);
    uint32_t qn = M.perf.qn;
    mot_note(&M, 0, 59, 100);
    mot_render(&M, l, r, 16);
    CHECKM(M.perf.n == 4 && M.perf.qn == qn && M.ref[0][59] == 1, "ACC-180 nel motore: coda intatta, settima accesa");
    /* un ri-attacco (nota spenta e riaccesa) riparte da capo come prima (ACC-179) */
    mot_note(&M, 0, 52, 0);
    mot_note(&M, 0, 51, 100);
    mot_render(&M, l, r, 16);
    CHECK(M.perf.n == 4 && M.ref[0][48] == 1 && M.ref[0][52] == 0);
}

/* MIDI-133 (16/10/2026): metronomo indipendente dal Beat, fill tenuto, uscita morbida con il loop in RAM */
static void test_mappa_133(void)
{
    static dsp_t D;
    static motore_t M;
    static float l[4800], r[4800];
    beat_hit_t h[8];

    /* il fill è una battuta a sé: alla fine della battuta il Funk ha il rullante forte dove il Beat lo ha piano */
    int nb = beat_hits(1, 15, h, 8), vb = 0, vf = 0;
    for (int i = 0; i < nb; i++) if (h[i].inst == DRUM_SNARE) vb = h[i].vel;
    int nf = beat_fill_hits(1, 15, h, 8);
    for (int i = 0; i < nf; i++) if (h[i].inst == DRUM_SNARE) vf = h[i].vel;
    CHECKM(vb == 80 && vf == 110, "fill del Funk: rullante %d contro %d", vf, vb);
    for (int b = 0; b < BEAT_COUNT; b++) {                       /* ogni fill ha colpi e nessun passo fuori */
        int tot = 0;
        for (int s = 0; s < 16; s++) tot += beat_fill_hits(b, s, h, 8);
        CHECKM(tot > 0, "fill del Beat %d vuoto", b);
    }
    CHECK_EQ(beat_fill_hits(0, 16, h, 8), 0);

    /* metronomo di T3: mette in moto il trasporto da solo e clicca, con il Beat spento */
    dsp_init(&D, 48000.0f, 1);
    mot_init(&M, &D, 48000, 1);
    mot_beat(&M, BEAT_M_PATTERN, 1);
    CHECK_EQ(M.tr_on, 0);
    mot_metronome(&M, true);
    CHECK(M.tr_on == 1 && M.tr_t0 == 0);
    mot_render(&M, l, r, 4800);
    bool drum = false;
    for (int i = 0; i < DRUM_VOICES; i++) if (M.drums.v[i].on || M.drums.v[i].t > 0.0f) drum = true;
    CHECKM(drum, "il metronomo di T3 clicca senza Beat");
    mot_metronome(&M, false);
    CHECK_EQ(M.tr_on, 0);
    /* con il Beat acceso il metronomo non lo ferma né lo riavvia */
    mot_beat_on(&M, true);
    uint32_t t0 = M.tr_t0;
    mot_render(&M, l, r, 4800);
    mot_metronome(&M, true);
    CHECK(M.tr_on == 1 && M.tr_t0 == t0);
    mot_fill(&M, true);
    CHECK_EQ(M.fill, 1);
    mot_fill(&M, false);

    /* drum machine (MIDI-135): con il Roll a 1/16 un tasto tenuto si ripete sulla griglia ed entra nel loop in
     * registrazione; il rilascio lo ferma; il kit a mano resta nei limiti */
    mot_roll(&M, 24);
    mot_loop(&M, LOOP_C_PRESS);
    int guard = 0;
    while (M.loop.state == LOOP_COUNT_IN && guard++ < 100) mot_render(&M, l, r, 4800);
    CHECK_EQ(M.loop.state, LOOP_REC);
    mot_drum(&M, 0, 100);
    uint16_t n0 = M.loop.n;
    for (int i = 0; i < 10; i++) mot_render(&M, l, r, 4800);   /* un secondo a 120 BPM: otto sedicesimi */
    int hits = M.loop.n - n0;
    CHECKM(hits >= 7 && hits <= 9, "Roll 1/16: %d colpi in un secondo", hits);
    mot_drum_off(&M, 0);
    n0 = M.loop.n;
    for (int i = 0; i < 10; i++) mot_render(&M, l, r, 4800);
    CHECK_EQ(M.loop.n, n0);
    mot_roll(&M, 0);
    mot_kit(&M, 3);
    CHECK_EQ(M.kit_sel, 3);
    mot_kit(&M, 9);
    CHECK_EQ(M.kit_sel, 0);
    mot_loop(&M, LOOP_C_RESET);

    /* uscita morbida: il loop resta in RAM e il Loop successivo lo riprende da capo invece di registrare */
    static looper_t L;
    loop_ev_t ev[64];
    loop_init(&L);
    loop_set_len(&L, 384, 1);
    loop_cmd(&L, LOOP_C_PRESS, 0, ev, 64);
    for (uint32_t t = 0; t <= 384; t++) loop_run(&L, t, ev, 64);
    loop_record(&L, 400, LOOP_TREBLE, 60, 100);
    loop_record(&L, 450, LOOP_TREBLE, 60, 0);
    for (uint32_t t = 385; t <= 768; t++) loop_run(&L, t, ev, 64);
    CHECK_EQ(L.state, LOOP_PLAY);
    uint16_t n = L.n;
    loop_cmd(&L, LOOP_C_EXIT, 800, ev, 64);
    CHECK(L.state == LOOP_IDLE && L.n == n && L.len == 384);
    loop_cmd(&L, LOOP_C_PRESS, 1000, ev, 64);
    CHECKM(L.state == LOOP_PLAY && L.t0 == 1000, "il loop in RAM riprende da t = 0");
    int on60 = 0;
    for (uint32_t t = 1000; t < 1384; t++) {
        int k = loop_run(&L, t, ev, 64);
        for (int i = 0; i < k; i++) if (ev[i].note == 60 && ev[i].vel && t == 1016) on60++;
    }
    CHECK_EQ(on60, 1);
    loop_cmd(&L, LOOP_C_EXIT, 1400, ev, 64);
    loop_cmd(&L, LOOP_C_CLEAR, 1401, ev, 64);                    /* Clear da fermo svuota la RAM */
    CHECK(L.state == LOOP_IDLE && L.n == 0);
    loop_cmd(&L, LOOP_C_PRESS, 1500, ev, 64);
    CHECK_EQ(L.state, LOOP_COUNT_IN);                             /* e il Loop dopo registra di nuovo */
    loop_cmd(&L, LOOP_C_EXIT, 1600, ev, 64);                      /* uscita durante il count-in: niente da tenere */
    CHECK(L.state == LOOP_IDLE && L.n == 0);
}

/* TV-119 (MIDI-139, ACC-215): la batteria che si inventa. Densità monotona (i colpi di d stanno in d + 1),
 * 0 tace e 1 è lo scheletro; la variazione è ripetibile, non tocca lo scheletro né le prime tre battute
 * della seconda battuta; le parti hanno strumenti diversi; il fill aggiunge colpi; nel motore il loop
 * inventato prende il posto del Beat e un Beat del menu lo spegne */
static int inv_count(const inv_t *g, const uint8_t *dens, bool fill, int part_inst)
{
    beat_hit_t h[8];
    int tot = 0;
    for (int s = 0; s < INV_STEPS; s++) {
        int n = inv_hits(g, dens, s, fill, h, 8);
        for (int i = 0; i < n; i++) if (part_inst < 0 || h[i].inst == part_inst) tot++;
    }
    return tot;
}

static void test_inventa(void)
{
    static inv_t g, g2, base;
    beat_hit_t h[8], h2[8];
    for (int gr = 0; gr < INV_GROOVES; gr++) {
        CHECKM(inv_groove_name(gr)[0] != 0, "stile %d senza nome", gr);
        CHECK(inv_groove_kit(gr) >= 0 && inv_groove_kit(gr) < KIT_COUNT);
        inv_build(&base, gr, 0);
        for (int s = 0; s < 16; s++)                             /* variazione 0: due battute uguali */
            for (int p = 0; p < INV_PARTS; p++) CHECK_EQ(base.lv[p][s], base.lv[p][s + 16]);
        for (int var = 0; var <= INV_VAR_MAX; var += 7) {
            inv_build(&g, gr, var);
            inv_build(&g2, gr, var);
            CHECKM(memcmp(&g, &g2, sizeof g) == 0, "TV-119: stile %d, variazione %d non ripetibile", gr, var);
            for (int a = 0; a < INV_PARTS; a++)                  /* strumenti diversi: la griglia li distingue */
                for (int b = a + 1; b < INV_PARTS; b++) CHECK(g.inst[a] != g.inst[b]);
            int skel = 0, bad = 0;
            for (int p = 0; p < INV_PARTS; p++)
                for (int s = 0; s < INV_STEPS; s++) {
                    if (base.lv[p][s] == 144) { skel++; bad += g.lv[p][s] != 144; }   /* lo scheletro resta */
                    else bad += g.lv[p][s] >= 144;
                    if (s >= 16 && s < 28) bad += g.lv[p][s] != g.lv[p][s - 16];
                }
            CHECKM(skel > 0 && bad == 0, "TV-119: stile %d var %d, scheletro %d, passi sbagliati %d", gr, var, skel, bad);
            for (int p = 0; p < INV_PARTS; p++) {                /* densità monotona, parte per parte */
                uint8_t d[INV_PARTS] = { 0 };
                for (int dv = 0; dv < INV_DENS_MAX; dv++)
                    for (int s = 0; s < INV_STEPS; s++) {
                        d[p] = (uint8_t)dv;
                        int n1 = inv_hits(&g, d, s, false, h, 8);
                        d[p] = (uint8_t)(dv + 1);
                        int n2 = inv_hits(&g, d, s, false, h2, 8);
                        bad += !(n2 >= n1 && (n1 == 0 || (h2[0].inst == h[0].inst && h2[0].vel == h[0].vel)));
                    }
            }
            CHECKM(bad == 0, "TV-119: stile %d var %d, densità non monotona in %d passi", gr, var, bad);
        }
        uint8_t zero[INV_PARTS] = { 0 }, one[INV_PARTS] = { 1, 1, 1, 1, 1 }, mid[INV_PARTS] = { 5, 5, 5, 5, 5 };
        CHECK_EQ(inv_count(&base, zero, false, -1), 0);          /* 0 tace, anche nel fill */
        CHECK_EQ(inv_count(&base, zero, true, -1), 0);
        int sk = inv_count(&base, one, false, -1);
        CHECKM(sk > 0 && sk < inv_count(&base, mid, false, -1), "stile %d: lo scheletro è il meno", gr);
        CHECK(inv_count(&base, mid, true, -1) > inv_count(&base, mid, false, -1));   /* il fill aggiunge */
        inv_build(&g, gr, 1);
        CHECKM(memcmp(g.lv, base.lv, sizeof g.lv) != 0, "TV-119: la variazione 1 dello stile %d non cambia niente", gr);
    }
    for (int b = 0; b < BEAT_COUNT; b++) CHECK(inv_groove_of_beat(b) >= 0 && inv_groove_of_beat(b) < INV_GROOVES);
    for (int var = 0; var <= INV_VAR_MAX; var++) {
        int n = inv_var_next(var, (uint32_t)var * 31u);
        CHECK(n != var && n >= 1 && n <= INV_VAR_MAX);
    }
    CHECK_EQ(inv_hits(&base, (const uint8_t[INV_PARTS]){ 10, 10, 10, 10, 10 }, INV_STEPS, false, h, 8), 0);

    /* nel motore: tutto a 0 tace, a 5 suona; un Beat del menu spegne il loop inventato */
    static dsp_t D;
    static motore_t M;
    static float l[4800], r[4800];
    dsp_init(&D, 48000.0f, 1);
    mot_init(&M, &D, 48000, 1);
    mot_inventa(&M, 2, 3);
    CHECK(M.inv_on == 1 && M.inv.groove == 2 && M.inv.var == 3 && M.beat_sel == BEAT_M_PATTERN);
    for (int p = 0; p < INV_PARTS; p++) mot_inventa_dens(&M, (uint8_t)p, 0);
    mot_beat_on(&M, true);
    bool drum = false;
    for (int i = 0; i < 10; i++) mot_render(&M, l, r, 4800);
    for (int i = 0; i < DRUM_VOICES; i++) if (M.drums.v[i].on) drum = true;
    CHECKM(!drum, "MIDI-139: densità 0, silenzio");
    for (int p = 0; p < INV_PARTS; p++) mot_inventa_dens(&M, (uint8_t)p, 5);
    for (int i = 0; i < 10; i++) mot_render(&M, l, r, 4800);
    for (int i = 0; i < DRUM_VOICES; i++) if (M.drums.v[i].on || M.drums.v[i].t > 0.0f) drum = true;
    CHECKM(drum, "MIDI-139: il loop inventato suona");
    mot_inventa_dens(&M, INV_KICK, 40);
    CHECK_EQ(M.inv_dens[INV_KICK], INV_DENS_MAX);
    mot_beat(&M, BEAT_M_PATTERN, 1);
    CHECK_EQ(M.inv_on, 0);
}

/* il colpo dello strumento inst è partito adesso (non è la coda di uno vecchio) */
static bool fresh_hit(const motore_t *m, uint8_t inst)
{
    for (int i = 0; i < DRUM_VOICES; i++)
        if (m->drums.v[i].on && m->drums.v[i].inst == inst && m->drums.v[i].t < 0.004f) return true;
    return false;
}

static bool any_voice(const motore_t *m)
{
    for (int i = 0; i < DRUM_VOICES; i++) if (m->drums.v[i].on) return true;
    return false;
}

/* TV-120: lo swing (ACC-216) sposta i sedicesimi dispari del Beat, della griglia del loop e del Roll */
static void test_swing(void)
{
    static dsp_t D;
    static motore_t M;
    dsp_init(&D, 48000.0f, 1);
    mot_init(&M, &D, 48000, 1);                                   /* 120 BPM: 250 campioni per tick */
    mot_swing(&M, 40);
    CHECK_EQ(M.swing, MOT_SWING_MAX);
    /* un Beat che suona sul passo 1 (il primo sedicesimo dispari) */
    beat_hit_t h[8];
    int b = 1;
    while (b < BEAT_COUNT && beat_hits(b, 1, h, 8) == 0) b++;
    CHECKM(b < BEAT_COUNT, "TV-120: serve un Beat con un colpo sul passo 1");
    mot_beat(&M, BEAT_M_PATTERN, (uint8_t)b);
    mot_swing(&M, 6);
    mot_beat_on(&M, true);                                        /* battuta 1 al tick 0 */
    render_tick(&M, 24);
    CHECKM(!any_voice(&M), "TV-120: con lo swing il passo 1 non suona al tick 24");
    render_tick(&M, 30);
    CHECKM(any_voice(&M), "TV-120: il passo 1 suona al tick 30 (24 + 6)");
    render_tick(&M, 48 + 384);                                    /* i pari restano dritti: il passo 2 della battuta dopo */
    bool pari = any_voice(&M) || beat_hits(b, 2, h, 8) == 0;
    CHECKM(pari, "TV-120: i sedicesimi pari non si spostano");
    mot_swing(&M, 0);
    render_tick(&M, 768 + 24);
    CHECKM(any_voice(&M), "TV-120: senza swing il passo 1 torna al tick 24");
    mot_beat_on(&M, false);
    mot_all_off(&M);

    /* il loop: i colpi dal vivo vanno al punto più vicino della griglia spostata e si registrano dritti */
    mot_init(&M, &D, 48000, 1);
    mot_swing(&M, 12);
    mot_loop(&M, LOOP_C_PRESS);
    static float l[16], r[16];
    while (M.loop.state != LOOP_REC) mot_render(&M, l, r, 16);
    uint32_t t0 = M.loop.t0;
    while (M.tick < t0 + 37) mot_render(&M, l, r, 16);
    mot_drum(&M, DRUM_SNARE, 100);                                /* pos 37: con 12 tick di swing il più vicino è 36, il dispari 1 */
    CHECK_EQ(M.loop.n, 1);
    CHECKM(M.loop.ev[0].t == 24, "TV-120: il colpo a pos 37 si registra a t = 24 (dritto), non a 48: t = %u", (unsigned)M.loop.ev[0].t);
    while (M.tick < t0 + 100) mot_render(&M, l, r, 16);
    mot_drum(&M, DRUM_KICK, 100);                                 /* pos 100: il più vicino è 96, pari */
    CHECK(M.loop.n == 2 && M.loop.ev[1].t == 96);
    /* al giro dopo il rullante suona a t0 + len + 24 + 12, non a + 24 */
    uint32_t g2 = t0 + M.loop.len;
    render_tick(&M, g2 + 24);
    CHECKM(!fresh_hit(&M, DRUM_SNARE), "TV-120: il colpo del loop sul dispari non suona al posto dritto");
    render_tick(&M, g2 + 36);
    CHECKM(fresh_hit(&M, DRUM_SNARE), "TV-120: il colpo del loop sul dispari suona 12 tick dopo");
    render_tick(&M, g2 + 96);
    CHECKM(fresh_hit(&M, DRUM_KICK), "TV-120: il colpo sul pari resta al suo posto");

    /* il Roll a 1/16: i punti dispari suonano spostati ed entrano nel loop dritti */
    mot_loop(&M, LOOP_C_OVERDUB);
    mot_swing(&M, 6);
    mot_roll(&M, 24);
    uint32_t g3 = t0 + 2 * M.loop.len;
    while (M.tick < g3 + 150) mot_render(&M, l, r, 16);
    mot_drum(&M, DRUM_CLOSED_HAT, 90);
    uint16_t n0 = M.loop.n;
    render_tick(&M, g3 + 168);                                   /* 168 = 7 × 24, dispari: non ancora */
    CHECKM(!fresh_hit(&M, DRUM_CLOSED_HAT), "TV-120: il Roll non suona sul dispari dritto");
    render_tick(&M, g3 + 174);
    CHECKM(fresh_hit(&M, DRUM_CLOSED_HAT), "TV-120: il Roll suona sul dispari spostato");
    render_tick(&M, g3 + 192);
    CHECKM(fresh_hit(&M, DRUM_CLOSED_HAT), "TV-120: il Roll suona sul pari dritto");
    mot_drum_off(&M, DRUM_CLOSED_HAT);
    bool dritti = M.loop.n > n0;
    for (int i = 0; i < M.loop.n; i++)
        if (M.loop.ev[i].note == DRUM_CLOSED_HAT && M.loop.ev[i].t % 24 != 0) dritti = false;
    CHECKM(dritti, "TV-120: i colpi del Roll entrano nel loop sulla griglia dritta");
    mot_roll(&M, 0);
    mot_loop(&M, LOOP_C_RESET);
    CHECK_EQ(M.swq_n, 0);
}

/* energia di 16 frame per n blocchi: il kit sintetizzato, un colpo all'inizio */
static double drum_energy(drums_t *k, uint8_t inst, int blocks, float *peak)
{
    double e = 0.0;
    float l[16], r[16];
    drums_hit(k, inst, 127);
    for (int b = 0; b < blocks; b++) {
        memset(l, 0, sizeof l); memset(r, 0, sizeof r);
        drums_render16(k, l, r);
        for (int s = 0; s < 16; s++) {
            e += (double)l[s] * (double)l[s];
            if (fabsf(l[s]) > *peak) *peak = fabsf(l[s]);
            if (l[s] != l[s]) return -1.0;                        /* NaN */
        }
    }
    return e;
}

/* il bus con l'FX fermo al valore dato: 200 ms, l'inseguimento di 15 ms arriva a 1e−4 in 140 */
static void fx_settle(drums_t *k, uint8_t drive, int8_t filt)
{
    float l[16], r[16];
    drums_fx(k, drive, filt);
    for (int b = 0; b < 600; b++) { memset(l, 0, sizeof l); memset(r, 0, sizeof r); drums_render16(k, l, r); }
}

/* TV-121: l'FX del bus della batteria (SND-538): spento è trasparente, il drive comprime, il filtro
 * toglie gli alti o i bassi, i clic del metronomo non ci passano */
static void test_drum_fx(void)
{
    static drums_t A, B;
    float pa = 0.0f, pb = 0.0f;
    drums_init(&A, 48000.0f, 7);
    drums_init(&B, 48000.0f, 7);
    fx_settle(&A, 0, 0);
    fx_settle(&B, 8, -6);
    fx_settle(&B, 0, 0);                                          /* acceso e poi spento: torna trasparente */
    float l1[16], r1[16], l2[16], r2[16];
    bool uguali = true;
    drums_hit(&A, DRUM_SNARE, 110);
    drums_hit(&B, DRUM_SNARE, 110);
    for (int b = 0; b < 200; b++) {
        memset(l1, 0, sizeof l1); memset(r1, 0, sizeof r1); memset(l2, 0, sizeof l2); memset(r2, 0, sizeof r2);
        drums_render16(&A, l1, r1);
        drums_render16(&B, l2, r2);
        if (memcmp(l1, l2, sizeof l1) || memcmp(r1, r2, sizeof r1)) uguali = false;
    }
    CHECKM(uguali, "TV-121: con drive 0 e filtro 0 il bus esce com'è");

    drums_init(&A, 48000.0f, 7);
    drums_init(&B, 48000.0f, 7);
    fx_settle(&B, 10, 0);
    double e0 = drum_energy(&A, DRUM_KICK, 600, &pa), e1 = drum_energy(&B, DRUM_KICK, 600, &pb);
    CHECKM(e0 > 0.0 && e1 > 1.3 * e0, "TV-121: drive 10 alza l'energia della cassa (%.3f → %.3f)", e0, e1);
    CHECKM(pb < 1.2f, "TV-121: drive 10, picco %.2f", (double)pb);

    drums_init(&A, 48000.0f, 7);
    drums_init(&B, 48000.0f, 7);
    fx_settle(&B, 0, -10);
    e0 = drum_energy(&A, DRUM_CLOSED_HAT, 300, &pa);
    e1 = drum_energy(&B, DRUM_CLOSED_HAT, 300, &pb);
    CHECKM(e1 < 0.05 * e0, "TV-121: passa-basso chiuso, il charleston quasi sparisce (%.4f su %.4f)", e1, e0);

    drums_init(&A, 48000.0f, 7);
    drums_init(&B, 48000.0f, 7);
    fx_settle(&B, 0, 10);
    e0 = drum_energy(&A, DRUM_KICK, 600, &pa);
    e1 = drum_energy(&B, DRUM_KICK, 600, &pb);
    CHECKM(e1 < 0.1 * e0, "TV-121: passa-alto aperto, la cassa quasi sparisce (%.4f su %.4f)", e1, e0);

    /* i clic del metronomo restano quelli di sempre anche con il filtro chiuso */
    drums_init(&A, 48000.0f, 7);
    drums_init(&B, 48000.0f, 7);
    fx_settle(&A, 0, 0);
    fx_settle(&B, 10, -10);
    drums_hit(&A, DRUM_CLICK_ACCENT, 120);
    drums_hit(&B, DRUM_CLICK_ACCENT, 120);
    uguali = true;
    for (int b = 0; b < 60; b++) {
        memset(l1, 0, sizeof l1); memset(r1, 0, sizeof r1); memset(l2, 0, sizeof l2); memset(r2, 0, sizeof r2);
        drums_render16(&A, l1, r1);
        drums_render16(&B, l2, r2);
        if (memcmp(l1, l2, sizeof l1)) uguali = false;
    }
    CHECKM(uguali, "TV-121: il clic del metronomo non passa dall'FX");

    /* il motore lo passa al kit */
    static dsp_t D;
    static motore_t M;
    dsp_init(&D, 48000.0f, 1);
    mot_init(&M, &D, 48000, 1);
    mot_drum_fx(&M, 30, -40);
    CHECK(M.drums.drive_t == 1.0f && M.drums.fpos_t == -1.0f);
}

void test_motore(void)
{
    test_swing();
    test_drum_fx();
    test_inventa();
    test_looper_revisione();
    test_motore_revisione();
    test_perf_revisione();
    test_mappa_133();
    test_drum_loop();
    test_strum_harp();
    test_arp();
    test_pattern_slop();
    test_looper();
    test_clock_beat();
    test_transport_loop();
    test_due();
}
