/* test_kits.c — la libreria dei kit di batteria sintetizzati (specifica 20, SND-540…SND-543; T-SND-55…59). */
#include "test.h"
#include "../../src/dsp/dsp.h"
#include "../../src/dsp/drums.h"
#include "../../src/core/beat.h"
#include "../../src/core/inventa.h"
#include "../../src/core/motore.h"
#include <math.h>
#include <string.h>

/* il picco di ogni strumento a velocity 127, dBFS mono prima del volume del Beat (tools/kits.py, LIVELLO) */
static const float LIVELLO[DRUM_KIT_INST] = { -1.0f, -3.0f, -1.5f, -2.0f, -4.0f, -2.0f, -4.0f, -2.0f, -5.0f, -2.5f,
                                              -4.0f, -5.0f };

/* un colpo a 127 del kit sintetizzato kit (NULL = il Chip) con il seme 7, come stame-render --kits:
 * picco mono, energia, blocchi finché la voce suona, e se l'uscita è sempre finita */
typedef struct { double energy; float peak; int blocks; bool finite; } colpo_t;

static colpo_t colpo(const drum_kit_t *kit, int inst, int max_blocks)
{
    static drums_t k;
    colpo_t c = { 0.0, 0.0f, 0, true };
    drums_init(&k, 48000.0f, 7);
    drums_volume(&k, 99);
    drums_set_synth(&k, kit);
    drums_hit(&k, (uint8_t)inst, 127);
    float gs = 1.0f;
    if (kit) {
        float th = (kit->r[inst].pan + 1.0f) * 0.25f * 3.14159265f;
        gs = cosf(th) + sinf(th);
    }
    for (int b = 0; b < max_blocks; b++) {
        float l[16], r[16];
        memset(l, 0, sizeof l);
        memset(r, 0, sizeof r);
        bool on = k.v[0].on;
        drums_render16(&k, l, r);
        if (on) c.blocks = b + 1;
        for (int s = 0; s < 16; s++) {
            if (!isfinite(l[s]) || !isfinite(r[s])) c.finite = false;
            c.energy += (double)l[s] * (double)l[s] + (double)r[s] * (double)r[s];
            float y = kit ? fabsf((l[s] + r[s]) / gs) : fabsf(l[s]);
            if (y > c.peak) c.peak = y;
        }
    }
    return c;
}

/* T-SND-55 (SND-540, SND-542): ogni strumento di ogni kit sintetizzato suona, resta finito, arriva al suo
 * livello entro −1 … +0,5 dB e si spegne entro la sua durata; dopo, il bus tace */
static void test_livelli(void)
{
    for (int ki = 0; ki < DRUM_SYNTH_KITS; ki++)
        for (int i = 0; i < DRUM_KIT_INST; i++) {
            const drum_rec_t *r = &drum_kits[ki].r[i];
            int max_b = (int)(r->dur * 48000.0f / 16.0f * 1.01f) + 8;   /* il tempo della voce è un float: qualche ms di deriva */
            colpo_t c = colpo(&drum_kits[ki], i, max_b + 8);
            float db = 20.0f * log10f(c.peak + 1e-12f);
            CHECKM(c.finite, "T-SND-55: %s, strumento %d: NaN o infinito", drum_kits[ki].name, i);
            CHECKM(db > LIVELLO[i] - 1.0f && db < LIVELLO[i] + 0.5f, "T-SND-55: %s, strumento %d a %.2f dBFS invece di %.1f",
                   drum_kits[ki].name, i, (double)db, (double)LIVELLO[i]);
            CHECKM(c.blocks <= max_b, "T-SND-55: %s, strumento %d suona %d blocchi, durata %.3f s", drum_kits[ki].name, i,
                   c.blocks, (double)r->dur);
            CHECKM(r->dur > 0.0f && r->dur <= 6.0f && r->gain > 0.0f, "T-SND-55: %s, strumento %d", drum_kits[ki].name, i);
        }
}

/* T-SND-56 (SND-541): il Chip non cambia. Energia e picco di ogni strumento, clic compresi, misurati prima
 * della libreria (19/10/2026) con lo stesso seme, volume 99 e 15 000 blocchi */
static void test_chip(void)
{
    static const double REF[DRUM_COUNT][2] = {
        { 3837.29337, 0.77309221 }, { 59.6836727, 0.827988088 }, { 1011.19717, 1.12210476 },
        { 1613.88604, 2.6871841 }, { 47.0730283, 0.285967141 }, { 2999.56687, 0.845687151 },
        { 459.822964, 0.303677708 }, { 2399.53802, 0.51930666 }, { 52.5132992, 0.30801937 },
        { 1440.37164, 0.827724516 }, { 9477.11474, 2.23764658 }, { 743.307885, 0.285419405 },
        { 132.496195, 0.700266838 }, { 132.489789, 0.695286751 },
    };
    for (int i = 0; i < DRUM_COUNT; i++) {
        colpo_t c = colpo(NULL, i, 15000);
        CHECKM(fabs(c.energy - REF[i][0]) < 1e-5 * REF[i][0] && fabs((double)c.peak - REF[i][1]) < 1e-6,
               "T-SND-56: il Chip, strumento %d: energia %.9g picco %.9g", i, c.energy, (double)c.peak);
    }
    /* i clic del metronomo restano quelli di sempre anche con un kit sintetizzato */
    colpo_t a = colpo(NULL, DRUM_CLICK_ACCENT, 200), b = colpo(&drum_kits[DK_KIT_909_HOUSE], DRUM_CLICK_ACCENT, 200);
    CHECKM(fabs(a.energy - b.energy) < 1e-9, "T-SND-56: il clic cambia con il kit");
}

/* T-SND-57 (SND-540): stesso seme, stesso colpo; il chiuso strozza l'aperto anche nella libreria; il
 * battimani fa i suoi colpi; il kit a campioni, dove c'è, passa davanti alla ricetta */
static void test_ricette(void)
{
    colpo_t a = colpo(&drum_kits[DK_KIT_808_BOOM], DRUM_SNARE, 4000), b = colpo(&drum_kits[DK_KIT_808_BOOM], DRUM_SNARE, 4000);
    CHECKM(a.energy == b.energy && a.peak == b.peak, "T-SND-57: lo stesso colpo non è ripetibile");

    static drums_t k;
    float l[16], r[16];
    drums_init(&k, 48000.0f, 7);
    drums_volume(&k, 99);
    drums_set_synth(&k, &drum_kits[DK_KIT_808_BOOM]);
    drums_hit(&k, DRUM_OPEN_HAT, 120);
    for (int b2 = 0; b2 < 30; b2++) { memset(l, 0, sizeof l); memset(r, 0, sizeof r); drums_render16(&k, l, r); }
    CHECK(k.v[0].on && k.v[0].inst == DRUM_OPEN_HAT);
    drums_hit(&k, DRUM_CLOSED_HAT, 120);
    for (int b2 = 0; b2 < 300; b2++) { memset(l, 0, sizeof l); memset(r, 0, sizeof r); drums_render16(&k, l, r); }  /* 100 ms */
    bool open = false;
    for (int i = 0; i < DRUM_VOICES; i++) if (k.v[i].on && k.v[i].inst == DRUM_OPEN_HAT) open = true;
    CHECKM(!open, "T-SND-57: il charleston chiuso non strozza l'aperto");

    /* il battimani dell'808 Boom: quattro colpi a 9,5 ms, poi la coda; il secondo è un massimo locale */
    drums_init(&k, 48000.0f, 7);
    drums_volume(&k, 99);
    drums_set_synth(&k, &drum_kits[DK_KIT_808_BOOM]);
    drums_hit(&k, DRUM_CLAP, 127);
    float env[40] = { 0 };
    for (int b2 = 0; b2 < 120; b2++) {                           /* 40 ms in finestre da 1 ms (3 blocchi) */
        memset(l, 0, sizeof l); memset(r, 0, sizeof r);
        drums_render16(&k, l, r);
        for (int s = 0; s < 16; s++) if (fabsf(l[s]) > env[b2 / 3]) env[b2 / 3] = fabsf(l[s]);
    }
    CHECKM(env[10] > 2.0f * env[7] && env[19] > 2.0f * env[17], "T-SND-57: il battimani non ha i suoi colpi (%.3f %.3f %.3f %.3f)",
           (double)env[7], (double)env[10], (double)env[17], (double)env[19]);
}

/* T-SND-58 (SND-541, ACC-218): il catalogo. I primi cinque sono quelli di sempre, nello stesso ordine;
 * nomi unici che stanno nella cella; i kit sintetizzati hanno la ricetta, quelli a campioni il set */
static void test_catalogo(void)
{
    CHECK_EQ(KIT_COUNT, KIT_SYNTH0 + DRUM_SYNTH_KITS);
    CHECKM(DRUM_SYNTH_KITS >= 30, "T-SND-58: la libreria ha %d kit", DRUM_SYNTH_KITS);
    CHECK(!strcmp(beat_kit_label(KIT_STUDIO), "Studio") && !strcmp(beat_kit_label(KIT_JAZZ), "Jazz") &&
          !strcmp(beat_kit_label(KIT_808), "808") && !strcmp(beat_kit_label(KIT_TECHNO), "Techno") &&
          !strcmp(beat_kit_label(KIT_CHIP), "Chip"));
    for (int i = 0; i < KIT_COUNT; i++) {
        const char *n = beat_kit_label(i);
        CHECKM(n[0] && strlen(n) < 16, "T-SND-58: kit %d senza nome o troppo lungo", i);
        CHECKM(beat_kit_style(i)[0] != 0, "T-SND-58: kit %d senza stile", i);
        for (int j = 0; j < i; j++) CHECKM(strcmp(n, beat_kit_label(j)) != 0, "T-SND-58: «%s» due volte", n);
        CHECK((beat_kit_synth(i) != NULL) == (i >= KIT_SYNTH0));
        CHECK((beat_kit_name(i) != NULL) == (i < KIT_CHIP));
    }
    CHECK(beat_kit_label(KIT_COUNT)[0] == 0 && beat_kit_synth(KIT_COUNT) == NULL && beat_kit_name(-1) == NULL);
    for (int b = 0; b < BEAT_COUNT; b++) CHECKM(beat_kit_of(b) >= 0 && beat_kit_of(b) < KIT_COUNT, "Beat %d", b);
    for (int g = 0; g < INV_GROOVES; g++) CHECKM(inv_groove_kit(g) >= 0 && inv_groove_kit(g) < KIT_COUNT, "stile %d", g);

    /* nel motore: K1 sceglie un kit della libreria, 0 torna a quello del Beat */
    static dsp_t D;
    static motore_t M;
    dsp_init(&D, 48000.0f, 1);
    mot_init(&M, &D, 48000, 1);
    mot_beat(&M, BEAT_M_PATTERN, 1);
    CHECK(M.drums.syn == beat_kit_synth(beat_kit_of(1)));
    mot_kit(&M, (uint8_t)(KIT_SYN(DK_KIT_909_HOUSE) + 1));
    CHECK(M.drums.syn == &drum_kits[DK_KIT_909_HOUSE] && M.drums.kit == NULL);
    mot_kit(&M, KIT_CHIP + 1);
    CHECK(M.drums.syn == NULL);
    mot_kit(&M, 0);
    CHECK(M.drums.syn == beat_kit_synth(beat_kit_of(1)));
}

/* T-SND-59 (SND-543): il caso peggiore della CPU sta nel conto. Dieci voci di metallo (le più care) per un
 * secondo: nessun NaN, e le voci finiscono */
static void test_dieci_voci(void)
{
    static drums_t k;
    drums_init(&k, 48000.0f, 3);
    drums_volume(&k, 99);
    drums_set_synth(&k, &drum_kits[DK_KIT_808_BOOM]);
    for (int i = 0; i < DRUM_VOICES; i++) drums_hit(&k, i & 1 ? DRUM_CYMBAL : DRUM_COWBELL, 100);
    int on = 0;
    bool finite = true;
    for (int b = 0; b < 3000; b++) {
        float l[16], r[16];
        memset(l, 0, sizeof l);
        memset(r, 0, sizeof r);
        drums_render16(&k, l, r);
        for (int s = 0; s < 16; s++) if (!isfinite(l[s]) || fabsf(l[s]) > 8.0f) finite = false;
    }
    for (int i = 0; i < DRUM_VOICES; i++) on += k.v[i].on;
    CHECK(finite);
    CHECKM(on <= DRUM_VOICES / 2, "T-SND-59: %d voci di campanaccio ancora accese dopo un secondo", on);
}

/* TV-123 (ACC-218, ACC-215): la libreria dei Beat e degli stili. I Beat e gli stili di prima tengono i loro
 * kit; i nuovi hanno un kit della libreria; ogni Beat suona e ha un fill; nomi unici che stanno nella plancia;
 * ogni kit della libreria fa da kit ad almeno un Beat o a uno stile; ogni Beat ha uno stile vicino */
static void test_beat_libreria(void)
{
    static const uint8_t KIT_PRIMA[20] = { KIT_CHIP, KIT_STUDIO, KIT_JAZZ, KIT_808, KIT_JAZZ, KIT_STUDIO, KIT_808,
                                           KIT_808, KIT_STUDIO, KIT_JAZZ, KIT_STUDIO, KIT_JAZZ, KIT_CHIP, KIT_TECHNO,
                                           KIT_TECHNO, KIT_808, KIT_TECHNO, KIT_TECHNO, KIT_808, KIT_808 };
    static const uint8_t STILE_PRIMA[10] = { KIT_TECHNO, KIT_STUDIO, KIT_STUDIO, KIT_808, KIT_808, KIT_TECHNO,
                                             KIT_JAZZ, KIT_808, KIT_808, KIT_TECHNO };
    CHECK_EQ(BEAT_COUNT, 61);
    CHECK_EQ(INV_GROOVES, 30);
    for (int b = 0; b < 20; b++) CHECKM(beat_kit_of(b) == KIT_PRIMA[b], "TV-123: il Beat %d ha cambiato kit", b);
    for (int g = 0; g < 10; g++) CHECKM(inv_groove_kit(g) == STILE_PRIMA[g], "TV-123: lo stile %d ha cambiato kit", g);
    bool usato[DRUM_SYNTH_KITS] = { false };
    beat_hit_t h[8];
    for (int b = 1; b < BEAT_COUNT; b++) {
        const char *n = beat_name(b);
        CHECKM(n[0] && strlen(n) < 24, "TV-123: Beat %d senza nome o troppo lungo", b);
        for (int c = 1; c < b; c++) CHECKM(strcmp(n, beat_name(c)) != 0, "TV-123: «%s» due volte", n);
        if (b >= 20) CHECKM(beat_kit_of(b) >= KIT_SYNTH0, "TV-123: «%s» senza un kit della libreria", n);
        if (beat_kit_of(b) >= KIT_SYNTH0) usato[beat_kit_of(b) - KIT_SYNTH0] = true;
        int nb = 0, nf = 0, k0 = 0;
        for (int s = 0; s < 16; s++) {
            int k = beat_hits(b, s, h, 8);
            nb += k;
            for (int i = 0; i < k; i++) if (s == 0) k0++;
            nf += beat_fill_hits(b, s, h, 8);
        }
        CHECKM(nb >= 6 && nf >= 6 && k0 > 0, "TV-123: «%s» suona %d colpi, il fill %d, il primo passo %d", n, nb, nf, k0);
        CHECK(inv_groove_of_beat(b) >= 0 && inv_groove_of_beat(b) < INV_GROOVES);
    }
    for (int g = 0; g < INV_GROOVES; g++) {
        const char *n = inv_groove_name(g);
        CHECKM(n[0] && strlen(n) < 12, "TV-123: stile %d senza nome o troppo lungo", g);
        for (int c = 0; c < g; c++) CHECKM(strcmp(n, inv_groove_name(c)) != 0, "TV-123: lo stile «%s» due volte", n);
        if (g >= 10) CHECKM(inv_groove_kit(g) >= KIT_SYNTH0, "TV-123: lo stile «%s» senza un kit della libreria", n);
        if (inv_groove_kit(g) >= KIT_SYNTH0) usato[inv_groove_kit(g) - KIT_SYNTH0] = true;
    }
    for (int i = 0; i < DRUM_SYNTH_KITS; i++) CHECKM(usato[i], "TV-123: il kit «%s» non è di nessun Beat né stile", drum_kits[i].name);
}

void test_kits(void)
{
    test_livelli();
    test_chip();
    test_ricette();
    test_catalogo();
    test_dieci_voci();
    test_beat_libreria();
}
