/* test_smp.c — il campionatore (specifica 20, §7b; T-SND-50…54) e i kit dei Beat (SND-537). */
#include "test.h"
#include "../../src/dsp/dsp.h"
#include "../../src/dsp/drums.h"
#include "../../src/core/beat.h"
#include <math.h>
#include <string.h>

#define FS 48000
#define PI_D 3.14159265358979323846

/* un banco costruito a mano, nel formato di §7b.2: un seno a 440 Hz registrato a 32 kHz (zona
 * 0, set «seno», nota 69, loop sull'intero ciclo intero di 4000 campioni = 55 cicli), un one-shot
 * di 800 campioni a rampa (zona 1) e un kit con due strumenti (set «kit», zone 2 e 3). Testa, 2 set e
 * 4 zone, allineati a 4, poi i dati (il 15/10/2026 il buffer era 52 byte troppo corto: ASan) */
static uint8_t blob[((SMP_HEADER + 2 * SMP_SET_REC + 4 * SMP_ZONE_REC + 3) & ~3) + 2 * (4000 + 800 + 64 + 64)];
static size_t blob_n;

static void w16(uint8_t *p, unsigned v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); }
static void w32(uint8_t *p, uint32_t v) { w16(p, v & 0xFFFFu); w16(p + 2, v >> 16); }
static void wf(uint8_t *p, float f) { uint32_t u; memcpy(&u, &f, 4); w32(p, u); }

static void zone(uint8_t *r, uint32_t off, uint32_t len, uint32_t ls, uint32_t le, uint32_t rate, float g,
                 int root, int lo, int hi, int vel_lo)
{
    w32(r, off); w32(r + 4, len); w32(r + 8, ls); w32(r + 12, le); w32(r + 16, rate); wf(r + 20, g);
    r[24] = (uint8_t)root; r[25] = (uint8_t)lo; r[26] = (uint8_t)hi; r[27] = (uint8_t)vel_lo;
}

static void build_blob(void)
{
    memset(blob, 0, sizeof blob);
    const int ns = 2, nz = 4;
    uint32_t data_off = SMP_HEADER + ns * SMP_SET_REC + nz * SMP_ZONE_REC;
    data_off = (data_off + 3u) & ~3u;
    memcpy(blob, "STMP", 4);
    w16(blob + 4, SMP_VERSION); w16(blob + 6, (unsigned)ns); w16(blob + 8, (unsigned)nz);
    w32(blob + 12, data_off);
    uint32_t data_n = 4000 + 800 + 64 + 64;
    w32(blob + 16, data_n);
    uint8_t *s = blob + SMP_HEADER;
    memcpy(s, "seno", 5); w16(s + 24, 0); w16(s + 26, 2); w16(s + 28, 1);
    s += SMP_SET_REC;
    memcpy(s, "kit", 4); w16(s + 24, 2); w16(s + 26, 2); w16(s + 28, 0);
    uint8_t *z = blob + SMP_HEADER + ns * SMP_SET_REC;
    zone(z, 0, 4000, 0, 4000, 32000, 1.0f, 69, 0, 127, 0);                 /* loop intero */
    zone(z + 32, 4000, 800, 0, 0, 32000, 1.0f, 60, 0, 127, 0);             /* one-shot */
    zone(z + 64, 4800, 64, 0, 0, 48000, 1.0f, DRUM_KICK, DRUM_KICK, DRUM_KICK, 0);
    zone(z + 96, 4864, 64, 0, 0, 48000, 0.5f, DRUM_SNARE, DRUM_SNARE, DRUM_SNARE, 90);   /* layer forte */
    int16_t *d = (int16_t *)(void *)(blob + data_off);
    for (int i = 0; i < 4000; i++) d[i] = (int16_t)(20000.0 * sin(2.0 * PI_D * 440.0 * i / 32000.0));
    for (int i = 0; i < 800; i++) d[4000 + i] = (int16_t)(16000 - i * 20);
    for (int i = 0; i < 64; i++) { d[4800 + i] = 16000; d[4864 + i] = -16000; }
    blob_n = data_off + data_n * 2u;
}

static dsp_t D;
static smp_bank_t B;
static float L[FS], R[FS];

static void render(int n)
{
    for (int i = 0; i + DSP_BLOCK <= n; i += DSP_BLOCK) dsp_render16(&D, L + i, R + i, NULL, NULL);
}

static double freq(const float *x, int n)
{
    double t0 = -1, t1 = 0;
    int k = 0;
    for (int i = 1; i < n; i++)
        if (x[i - 1] < 0.0f && x[i] >= 0.0f) {
            double t = i - 1 + (double)x[i - 1] / ((double)x[i - 1] - (double)x[i]);
            if (t0 < 0) t0 = t; else { t1 = t; k++; }
        }
    return k > 0 ? k / (t1 - t0) * FS : 0;
}

static float peak(const float *x, int n)
{
    float p = 0;
    for (int i = 0; i < n; i++) if (fabsf(x[i]) > p) p = fabsf(x[i]);
    return p;
}

static void smp_patch(uint8_t *p, int set)
{
    snd_patch_init(p, SND_MODEL_SMP);
    p[SND_P_RPHEIGHT] = (uint8_t)set;
    p[SND_P_E(2, 0)] = 0;                      /* attacco e rilascio nulli: conta il campione */
    p[SND_P_E(2, 4)] = 0;
}

/* T-SND-50: il banco si legge, i puntatori entrano nel blob, i set si trovano per nome e per indice */
static void test_parse(void)
{
    build_blob();
    CHECK(smp_bank_parse(&B, blob, blob_n));
    CHECK_EQ(B.n_sets, 2);
    CHECK_EQ(B.n_zones, 4);
    const smp_set_t *s = smp_set_find(&B, "seno");
    CHECK(s && s == smp_set_at(&B, 0) && s->n == 2 && (s->flags & 1));
    CHECK(smp_set_find(&B, "kit") == smp_set_at(&B, 1));
    CHECK(smp_set_find(&B, "manca") == NULL && smp_set_at(&B, 2) == NULL);
    const smp_zone_t *z = smp_zone_for(&B, s, 69, 100);
    CHECK(z && z->root == 69 && z->rate == 32000 && z->loop_end == 4000 && z->data[0] == 0);
    CHECK(z && z->data[1] == (int16_t)(20000.0 * sin(2.0 * PI_D * 440.0 / 32000.0)));
    /* layer di velocity: il kit sceglie la zona forte solo da 90 in su */
    const smp_set_t *k = smp_set_find(&B, "kit");
    CHECK(smp_zone_for(&B, k, DRUM_SNARE, 100) == &B.zones[3]);
    CHECK(smp_zone_for(&B, k, DRUM_SNARE, 80) == NULL);
    CHECK(smp_zone_for(&B, k, DRUM_KICK, 10) == &B.zones[2]);
    CHECK(smp_zone_for(&B, k, DRUM_CLAP, 100) == NULL);
    /* blob rotti: magic, zona oltre i dati, versione */
    smp_bank_t b2;
    uint8_t bad[SMP_HEADER + 32];
    memcpy(bad, blob, sizeof bad);
    bad[0] = 'X';
    CHECK(!smp_bank_parse(&b2, bad, sizeof bad) && b2.n_sets == 0);
    CHECK(!smp_bank_parse(&b2, blob, blob_n - 100));
    CHECK(!smp_bank_parse(&b2, NULL, 0));
    /* revisione del 15/10/2026: loop più corto di SMP_LOOP_MIN, e loop_start che gira in 32 bit */
    static uint8_t copia[sizeof blob];
    uint8_t *z0 = copia + SMP_HEADER + 2 * SMP_SET_REC;
    memcpy(copia, blob, blob_n);
    w32(z0 + 8, 4000 - SMP_LOOP_MIN + 1);
    CHECK(!smp_bank_parse(&b2, copia, blob_n));
    w32(z0 + 8, 0xFFFFFFFDu);
    CHECK(!smp_bank_parse(&b2, copia, blob_n));
    w32(z0 + 8, 4000 - SMP_LOOP_MIN);
    CHECK(smp_bank_parse(&b2, copia, blob_n));
}

/* revisione del 15/10/2026: una nota campionata ribattuta mentre suona riparte in una voce nuova e la
 * vecchia sfuma in coda in 2 ms; prima il campione ripartiva da capo con il VCA aperto (clic) */
static void test_restrike(void)
{
    uint8_t p[DSP_NPAR];
    dsp_init(&D, FS, 7);
    dsp_set_bank(&D, &B);
    dsp_set_master_volume(&D, 99);
    smp_patch(p, 0);
    dsp_load_patch(&D, DSP_SOUND, p, 0);
    dsp_note_on(&D, DSP_SOUND, 69, 100);
    render(FS / 10 + 37 * DSP_BLOCK);                   /* una fase qualunque del seno */
    float steady = 0.0f;
    for (int i = FS / 20; i < FS / 10; i++) { float j = fabsf(L[i] - L[i - 1]); if (j > steady) steady = j; }
    float last = L[FS / 10 + 37 * DSP_BLOCK - 1];
    dsp_note_on(&D, DSP_SOUND, 69, 100);
    render(960);
    float jump = fabsf(L[0] - last);
    for (int i = 1; i < 960; i++) { float j = fabsf(L[i] - L[i - 1]); if (j > jump) jump = j; }
    CHECKM(jump <= 2.0f * steady + 0.002f, "ribattuta: salto %.4f, a regime %.4f", (double)jump, (double)steady);
}

/* T-SND-51: una voce SMP suona il campione alla sua nota e trasposto, in loop finché è tenuta */
static void test_pitch(void)
{
    uint8_t p[DSP_NPAR];
    dsp_init(&D, FS, 7);
    dsp_set_bank(&D, &B);
    dsp_set_master_volume(&D, 99);
    smp_patch(p, 0);
    dsp_load_patch(&D, DSP_SOUND, p, 0);
    dsp_note_on(&D, DSP_SOUND, 69, 100);
    render(FS / 2);                                     /* mezzo secondo: ben oltre i 125 ms del campione */
    double f = freq(L + FS / 4, FS / 4);
    CHECKM(fabs(f - 440.0) < 1.0, "A4 campionato a %.2f Hz", f);
    CHECK(peak(L + FS / 4, FS / 4) > 0.05f);
    dsp_note_off(&D, DSP_SOUND, 69);
    dsp_note_on(&D, DSP_SOUND, 76, 100);                /* una quinta sopra: 659,26 Hz */
    render(FS / 2);
    f = freq(L + FS / 4, FS / 4);
    CHECKM(fabs(f - 659.26) < 1.5, "E5 campionato a %.2f Hz", f);
    /* SMPLOOP = 1 toglie il loop: il campione finisce e la voce si libera */
    dsp_note_off(&D, DSP_SOUND, 76);
    p[SND_P_RPDISTANCE] = 1;
    dsp_load_patch(&D, DSP_SOUND, p, 0);
    dsp_note_on(&D, DSP_SOUND, 69, 100);
    render(FS / 2);
    CHECK(peak(L + FS / 4, FS / 4) < 1e-6f);
    CHECK_EQ(dsp_voices_active(&D), 0);
    /* senza banco la voce tace e non resta appesa */
    dsp_set_bank(&D, NULL);
    dsp_note_on(&D, DSP_SOUND, 69, 100);
    render(DSP_BLOCK * 4);
    CHECK(peak(L, DSP_BLOCK * 4) == 0.0f);
    CHECK_EQ(dsp_voices_active(&D), 0);
}

/* T-SND-52: one-shot: la rampa parte dal campione 0 e finisce con il campione, anche se la nota è tenuta */
static void test_oneshot(void)
{
    uint8_t p[DSP_NPAR];
    dsp_init(&D, FS, 7);
    dsp_set_bank(&D, &B);
    dsp_set_master_volume(&D, 99);
    smp_patch(p, 0);
    dsp_load_patch(&D, DSP_SOUND, p, 0);
    dsp_note_on(&D, DSP_SOUND, 60, 100);                /* la zona 1 copre tutto ma la 0 pure: vince la prima trovata? */
    render(DSP_BLOCK);
    /* le due zone coprono 0…127 con lo stesso layer: la ricerca prende la prima (la 0, in loop); per
     * il one-shot si usa un set con la sola zona 1 */
    dsp_all_sound_off(&D);
    B.sets[0].first = 1; B.sets[0].n = 1;              /* set «seno» → solo la rampa */
    dsp_note_on(&D, DSP_SOUND, 60, 100);
    render(FS / 4);
    /* 800 campioni a 32 kHz durano 1200 campioni a 48 kHz: poi silenzio (il bus del motore sta a −12 dB) */
    CHECK(peak(L, 1100) > 0.05f);
    CHECK(peak(L + 1300, FS / 4 - 1300) == 0.0f);
    CHECK_EQ(dsp_voices_active(&D), 0);
    B.sets[0].first = 0; B.sets[0].n = 2;
}

/* T-SND-53: il kit a campioni suona lo strumento del Beat, e torna alla sintesi dove il kit manca */
static void test_kit(void)
{
    static drums_t K;
    float l[DSP_BLOCK], r[DSP_BLOCK];
    drums_init(&K, FS, 3);
    drums_set_kit(&K, &B, smp_set_find(&B, "kit"));
    drums_hit(&K, DRUM_KICK, 100);
    memset(l, 0, sizeof l); memset(r, 0, sizeof r);
    drums_render16(&K, l, r);
    CHECK(l[0] > 0.05f && l[15] > 0.05f);               /* il campione del kick è una costante positiva */
    for (int i = 0; i < 4; i++) { memset(l, 0, sizeof l); memset(r, 0, sizeof r); drums_render16(&K, l, r); }
    CHECK(l[0] == 0.0f);                                /* 64 campioni: finito dopo 4 blocchi */
    drums_hit(&K, DRUM_CLAP, 100);                      /* non nel kit: sintesi */
    bool any = false;
    for (int i = 0; i < 8; i++) { memset(l, 0, sizeof l); memset(r, 0, sizeof r); drums_render16(&K, l, r); if (peak(l, DSP_BLOCK) > 0.0f) any = true; }
    CHECK(any);
    /* lo strato forte del rullante solo con la velocity alta */
    drums_hit(&K, DRUM_SNARE, 60);
    memset(l, 0, sizeof l); memset(r, 0, sizeof r);
    drums_render16(&K, l, r);
    CHECK(K.v[0].z == NULL || K.v[1].z == NULL);        /* almeno una voce in sintesi */
    drums_set_kit(&K, NULL, NULL);
    drums_hit(&K, DRUM_KICK, 100);
    CHECK(K.v[0].z == NULL && K.v[1].z == NULL && K.v[2].z == NULL);
}

/* SND-537: ogni Beat della vetrina ha un kit noto o nessuno, e il nome è quello di un set del banco */
static void test_beat_kits(void)
{
    int con = 0;
    for (int b = 0; b < BEAT_COUNT; b++) {
        const char *k = beat_kit(b);
        CHECK(beat_name(b)[0] != 0);
        if (!k) continue;
        con++;
        CHECK(strcmp(k, "kit_studio") == 0 || strcmp(k, "kit_jazz") == 0 || strcmp(k, "kit_808") == 0);
        beat_hit_t h[8];
        int n = 0;
        for (int s = 0; s < 16; s++) n += beat_hits(b, s, h, 8);
        CHECK(n > 0);
    }
    CHECK(con >= 9);
    CHECK(beat_kit(0) == NULL);
}

void test_smp(void)
{
    test_parse();
    test_restrike();
    test_pitch();
    test_oneshot();
    test_kit();
    test_beat_kits();
}
