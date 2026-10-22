/* test_ambient.c — il modulo AMBIENT (specifica 10, §10.9: TV-125, TV-126). */
#include "test.h"
#include "../../src/core/ambient.h"
#include "../../src/core/acc.h"
#include "../../src/core/motore.h"

static int pop12(uint16_t x)
{
    int n = 0;
    for (; x; x &= (uint16_t)(x - 1)) n++;
    return n;
}

static uint16_t scala(int tonic, bool minor)
{
    static const uint8_t MAJ[7] = { 0, 2, 4, 5, 7, 9, 11 }, MIN[7] = { 0, 2, 3, 5, 7, 8, 10 };
    uint16_t m = 0;
    for (int i = 0; i < 7; i++) m |= (uint16_t)(1u << ((tonic + (minor ? MIN[i] : MAJ[i])) % 12));
    return m;
}

static bool same(amb_chord_t a, amb_chord_t b) { return a.key == b.key && a.types == b.types && a.exts == b.exts; }

/* TV-125 (ACC-261): l'armonia. Casa all'inizio; accordi sempre diversi dal precedente, di almeno tre note, quasi
 * tutti nella scala; ripetibile per variazione, diversa fra due variazioni; il giro si muove per note in comune;
 * la durata con il movimento; l'accordo di chi suona diventa quello in corso */
static void test_armonia(void)
{
    for (int mood = 0; mood < AMB_MOODS; mood++)
        for (int minor = 0; minor < 2; minor++)
            for (int tonic = 0; tonic < 12; tonic += 5) {
                amb_harm_t h, g;
                amb_harm_init(&h, mood, 7, tonic, minor);
                amb_chord_t c = amb_harm_first(&h), prev = c;
                CHECKM(pop12(amb_chord_pcs(c)) >= 3, "TV-125: casa di %s ha %d note", amb_mood_name(mood), pop12(amb_chord_pcs(c)));
                int fuori = 0, note = 0, comuni = 0, n = 200;
                uint16_t sc = scala(tonic, minor);
                for (int i = 0; i < n; i++) {
                    amb_chord_t d = amb_harm_next(&h);
                    uint16_t p = amb_chord_pcs(d), q = amb_chord_pcs(prev);
                    CHECKM(!same(d, prev), "TV-125: %s ripete l'accordo", amb_mood_name(mood));
                    CHECKM(pop12(p) >= 3, "TV-125: %s, un accordo di %d note", amb_mood_name(mood), pop12(p));
                    CHECKM(d.vel >= 64 && d.vel <= 84, "TV-125: velocity %d", d.vel);
                    CHECKM(d.key < 12 && d.types && (d.types & (d.types - 1)) == 0, "TV-125: un tipo solo");
                    fuori += pop12((uint16_t)(p & ~sc));
                    note += pop12(p);
                    comuni += pop12((uint16_t)(p & q));
                    prev = d;
                }
                CHECKM(fuori * 10 <= note, "TV-125: %s %s, %d note fuori scala su %d", amb_mood_name(mood),
                       minor ? "minore" : "maggiore", fuori, note);
                CHECKM(comuni >= n, "TV-125: %s, in media meno di una nota in comune (%d su %d)", amb_mood_name(mood), comuni, n);
                /* ripetibile, e un'altra variazione prende un'altra strada */
                amb_harm_init(&h, mood, 7, tonic, minor);
                amb_harm_init(&g, mood, 7, tonic, minor);
                amb_harm_first(&h); amb_harm_first(&g);
                bool uguali = true;
                for (int i = 0; i < 30; i++) uguali = uguali && same(amb_harm_next(&h), amb_harm_next(&g));
                CHECKM(uguali, "TV-125: stessa variazione, stesso giro");
                amb_harm_init(&h, mood, 7, tonic, minor);
                amb_harm_init(&g, mood, 8, tonic, minor);
                amb_harm_first(&h); amb_harm_first(&g);
                bool diversi = false;
                for (int i = 0; i < 30; i++) diversi = diversi || !same(amb_harm_next(&h), amb_harm_next(&g));
                CHECKM(diversi, "TV-125: %s, le variazioni 7 e 8 fanno lo stesso giro", amb_mood_name(mood));
            }
    /* la durata: 0 non cambia mai, poi sempre più corta */
    CHECK_EQ(amb_chord_beats(0, 3), 0);
    CHECK_EQ(amb_chord_beats(10, 3), 4);
    for (uint32_t s = 0; s < 10; s++) {
        CHECK(amb_chord_beats(1, s) >= 60 && amb_chord_beats(1, s) <= 72);
        for (int m = 1; m < AMB_MOTION_MAX - 1; m++)
            CHECKM(amb_chord_beats(m, s) >= amb_chord_beats(m + 2, s), "TV-125: il movimento %d dura meno del %d", m, m + 2);
        CHECK(amb_chord_beats(5, s) % 4 == 0);                    /* gli accordi lunghi restano a battute intere */
    }
    /* l'accordo di chi suona: Re minore in Do maggiore; il prossimo gli somiglia */
    amb_harm_t h;
    amb_harm_init(&h, AMB_FLOAT, 0, 0, false);
    amb_harm_first(&h);
    amb_chord_t dm = { 2, 1u << ACC_MIN, 0, 0 };
    amb_harm_follow(&h, amb_chord_pcs(dm));
    CHECK(h.cur == -1 && h.pcs == amb_chord_pcs(dm));
    amb_chord_t c = amb_harm_next(&h);
    CHECKM(pop12((uint16_t)(amb_chord_pcs(c) & amb_chord_pcs(dm))) >= 1, "TV-125: dopo l'accordo di chi suona, uno vicino");
    /* un accordo della tavolozza seguito non si ripete subito */
    amb_harm_init(&h, AMB_TIDE, 0, 0, false);
    amb_chord_t casa = amb_harm_first(&h);
    amb_harm_follow(&h, amb_chord_pcs(casa));
    CHECK_EQ(h.cur, 0);
    CHECK(!same(amb_harm_next(&h), casa));
    for (int m = 0; m < AMB_MOODS; m++) CHECK(amb_mood_name(m)[0] && strlen(amb_mood_name(m)) < 8);
}

/* TV-126 (ACC-262): le note sparse. Nel registro, nelle classi dell'accordo o della pentatonica; non più voci
 * della densità; ogni nota si spegne; la prima entro mezzo quarto; densità 0 tace; le note già tenute non si
 * ripetono; spente, finiscono e non ne partono altre; ripetibili; più dense, più note */
static int corri(amb_bloom_t *b, uint32_t t0, uint32_t t1, uint16_t chord, const uint8_t busy[128], int *prima, int *max_insieme)
{
    static uint8_t su[128];
    memset(su, 0, sizeof su);
    int ons = 0, insieme = 0;
    for (int i = 0; i < AMB_VOICES; i++)                          /* le note di prima che suonano ancora */
        if (b->v[i].note != 0xFF) { su[b->v[i].note] = 1; insieme++; }
    *prima = -1;
    *max_insieme = 0;
    uint16_t ok = (uint16_t)(chord | 0x295u);                    /* Do maggiore: la pentatonica 0 2 4 7 9 */
    for (uint32_t t = t0; t <= t1; t++) {
        amb_ev_t ev[16];
        int n = amb_bloom_run(b, t, chord, busy, ev, 16);
        for (int i = 0; i < n; i++) {
            if (ev[i].vel) {
                ons++;
                if (*prima < 0) *prima = (int)(t - t0);
                CHECKM(ev[i].note >= 72 && ev[i].note <= 96, "TV-126: nota %d fuori dal registro di Float", ev[i].note);
                CHECKM(ok >> (ev[i].note % 12) & 1u, "TV-126: nota %d fuori dall'accordo e dalla pentatonica", ev[i].note);
                CHECKM(ev[i].vel >= 34 && ev[i].vel <= 96, "TV-126: velocity %d", ev[i].vel);
                CHECKM(!su[ev[i].note], "TV-126: nota %d accesa due volte", ev[i].note);
                CHECKM(!busy[ev[i].note], "TV-126: nota %d già tenuta", ev[i].note);
                su[ev[i].note] = 1;
                insieme++;
            } else {
                CHECKM(su[ev[i].note], "TV-126: note-off di una nota spenta (%d)", ev[i].note);
                su[ev[i].note] = 0;
                insieme--;
            }
            if (insieme > *max_insieme) *max_insieme = insieme;
        }
    }
    return ons;
}

static void test_note_sparse(void)
{
    static amb_bloom_t b, c;
    static uint8_t busy[128];
    memset(busy, 0, sizeof busy);
    uint16_t cmaj7 = 0x891u;                                      /* Do Mi Sol Si */
    int prima, insieme;
    amb_bloom_init(&b, 1);
    amb_bloom_set(&b, true, 5, AMB_FLOAT, 0, false, 1000);
    int n5 = corri(&b, 1000, 1000 + 96 * 400, cmaj7, busy, &prima, &insieme);
    CHECKM(n5 > 20, "TV-126: densità 5, %d note in 400 quarti", n5);
    CHECKM(prima >= 0 && prima <= 48, "TV-126: la prima nota dopo %d tick", prima);
    CHECKM(insieme <= 3, "TV-126: densità 5, %d note insieme (al più 3 voci)", insieme);
    /* spente: le note finiscono, non ne partono altre */
    amb_bloom_set(&b, false, 5, AMB_FLOAT, 0, false, 1000 + 96 * 400);
    int n = corri(&b, 1000 + 96 * 400 + 1, 1000 + 96 * 500, cmaj7, busy, &prima, &insieme);
    CHECK_EQ(n, 0);
    for (int i = 0; i < AMB_VOICES; i++) CHECK_EQ(b.v[i].note, 0xFF);
    /* ripetibili */
    amb_bloom_init(&b, 9);
    amb_bloom_init(&c, 9);
    amb_bloom_set(&b, true, 7, AMB_FLOAT, 0, false, 0);
    amb_bloom_set(&c, true, 7, AMB_FLOAT, 0, false, 0);
    bool uguali = true;
    for (uint32_t t = 0; t < 96 * 200; t++) {
        amb_ev_t e1[16], e2[16];
        int a = amb_bloom_run(&b, t, cmaj7, busy, e1, 16), d = amb_bloom_run(&c, t, cmaj7, busy, e2, 16);
        uguali = uguali && a == d && !memcmp(e1, e2, (size_t)a * sizeof e1[0]);
    }
    CHECKM(uguali, "TV-126: stesso seme, stesse note");
    /* densità: 0 tace, 10 suona più di 2 */
    amb_bloom_init(&b, 3);
    amb_bloom_set(&b, true, 0, AMB_FLOAT, 0, false, 0);
    CHECK_EQ(corri(&b, 0, 96 * 300, cmaj7, busy, &prima, &insieme), 0);
    amb_bloom_init(&b, 3);
    amb_bloom_set(&b, true, 2, AMB_FLOAT, 0, false, 0);
    int n2 = corri(&b, 0, 96 * 600, cmaj7, busy, &prima, &insieme);
    amb_bloom_init(&b, 3);
    amb_bloom_set(&b, true, 10, AMB_FLOAT, 0, false, 0);
    int n10 = corri(&b, 0, 96 * 600, cmaj7, busy, &prima, &insieme);
    CHECKM(n10 > 3 * n2, "TV-126: densità 10, %d note; densità 2, %d", n10, n2);
    CHECKM(insieme <= AMB_VOICES, "TV-126: densità 10, %d note insieme", insieme);
    /* le note già tenute non si ripetono: tutto tenuto, niente note */
    memset(busy, 1, sizeof busy);
    amb_bloom_init(&b, 3);
    amb_bloom_set(&b, true, 10, AMB_FLOAT, 0, false, 0);
    CHECK_EQ(corri(&b, 0, 96 * 100, cmaj7, busy, &prima, &insieme), 0);
    memset(busy, 0, sizeof busy);
    /* senza accordo restano la pentatonica e l'ultimo accordo sentito */
    amb_bloom_init(&b, 4);
    amb_bloom_set(&b, true, 6, AMB_FLOAT, 0, false, 0);
    CHECK(corri(&b, 0, 96 * 200, 0, busy, &prima, &insieme) > 0);
}

/* il modulo dentro il motore: le note sparse escono sul Sound sopra l'accordo tenuto, senza entrare nel loop
 * e senza passare dalla performance; Panic le dimentica */
static void test_ambient_motore(void)
{
    static dsp_t D;
    static motore_t M;
    static float l[16], r[16];
    dsp_init(&D, 48000.0f, 1);
    mot_init(&M, &D, 48000, 1);
    mot_note(&M, 0, 48, 90); mot_note(&M, 0, 52, 90); mot_note(&M, 0, 55, 90); mot_note(&M, 0, 59, 90);
    mot_chord_start(&M);
    mot_ambient(&M, true, 8, AMB_FLOAT, 0, false);
    bool sopra = false, visto = false;
    while (M.tick < 96 * 40) {
        mot_render(&M, l, r, 16);
        for (int i = 0; i < DSP_VOICES; i++)
            if (D.voice[i].engine == DSP_SOUND && D.voice[i].state == DSP_V_HELD && D.voice[i].note >= 72) sopra = true;
        for (int i = 0; i < 16; i++) if (M.snap.amb_notes[i]) visto = true;
    }
    CHECKM(sopra, "TV-126: le note sparse suonano sul Sound sopra l'accordo");
    CHECKM(visto, "TV-126: lo snapshot le pubblica per la plancia");
    CHECK_EQ(M.loop.n, 0);
    mot_all_off(&M);
    for (int i = 0; i < AMB_VOICES; i++) CHECK_EQ(M.amb.v[i].note, 0xFF);
    mot_ambient(&M, false, 8, AMB_FLOAT, 0, false);
}

void test_ambient(void)
{
    test_armonia();
    test_note_sparse();
    test_ambient_motore();
}
