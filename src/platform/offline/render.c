/* render.c — render offline della plancia (PLT-076, sezione 50 §11): fotogrammi in PNG.
 *
 * Uso: stame-render <cartella> [--mpk] [istanti in ms della demo…] [--boot ms…] [--tutti passo_ms]
 *   per ogni istante scrive <cartella>/demo_<ms>.png; con --boot le schermate d'avvio.
 * Usa la vetrina e lo stesso renderer della Flip (ui_flip), con il framebuffer RGB565.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "../vetrina/vetrina.h"
#include "../vetrina/vetrina_dsp.h"
#include "../vetrina/banco.h"
#include "../../ui_flip/ui_flip.h"

static uint16_t px[UI_FLIP_W * UI_FLIP_H];

static uint32_t crc_table[256];
static void crc_init(void)
{
    for (uint32_t n = 0; n < 256; n++) {
        uint32_t c = n;
        for (int k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320u ^ (c >> 1) : c >> 1;
        crc_table[n] = c;
    }
}
static uint32_t crc(uint32_t c, const uint8_t *b, size_t n)
{
    c ^= 0xFFFFFFFFu;
    for (size_t i = 0; i < n; i++) c = crc_table[(c ^ b[i]) & 0xFF] ^ (c >> 8);
    return c ^ 0xFFFFFFFFu;
}
static void be32(uint8_t *p, uint32_t v) { p[0] = (uint8_t)(v >> 24); p[1] = (uint8_t)(v >> 16); p[2] = (uint8_t)(v >> 8); p[3] = (uint8_t)v; }

static void chunk(FILE *f, const char *type, const uint8_t *data, uint32_t n)
{
    uint8_t h[8];
    be32(h, n);
    memcpy(h + 4, type, 4);
    fwrite(h, 1, 8, f);
    if (n) fwrite(data, 1, n, f);
    uint32_t c = crc(0, (const uint8_t *)type, 4);   /* il CRC copre tipo e dati */
    if (n) c = crc(c, data, n);
    uint8_t t[4];
    be32(t, c);
    fwrite(t, 1, 4, f);
}

/* PNG 8 bit RGB (ch = 3) o RGBA (ch = 4), deflate «stored» (senza compressione): niente zlib.
 * pix: righe di w * ch byte. */
static int write_png_px(const char *path, const uint8_t *pix, int w, int h, int ch)
{
    size_t row = (size_t)w * (size_t)ch;
    size_t raw_n = (size_t)h * (1 + row);
    uint8_t *raw = malloc(raw_n);
    if (!raw) return -1;
    for (int y = 0; y < h; y++) {
        raw[(size_t)y * (1 + row)] = 0;
        memcpy(raw + (size_t)y * (1 + row) + 1, pix + (size_t)y * row, row);
    }
    size_t nblk = (raw_n + 65534) / 65535;
    size_t z_n = 2 + raw_n + nblk * 5 + 4;
    uint8_t *z = malloc(z_n);
    size_t k = 0;
    z[k++] = 0x78; z[k++] = 0x01;
    uint32_t a = 1, b = 0;
    for (size_t i = 0; i < raw_n; i++) { a = (a + raw[i]) % 65521u; b = (b + a) % 65521u; }
    for (size_t off = 0; off < raw_n; off += 65535) {
        size_t len = raw_n - off > 65535 ? 65535 : raw_n - off;
        z[k++] = off + len >= raw_n ? 1 : 0;
        z[k++] = (uint8_t)len; z[k++] = (uint8_t)(len >> 8);
        z[k++] = (uint8_t)~len; z[k++] = (uint8_t)(~len >> 8);
        memcpy(z + k, raw + off, len);
        k += len;
    }
    be32(z + k, (b << 16) | a);
    k += 4;
    FILE *f = fopen(path, "wb");
    if (!f) { free(raw); free(z); return -1; }
    static const uint8_t sig[8] = { 137, 80, 78, 71, 13, 10, 26, 10 };
    fwrite(sig, 1, 8, f);
    uint8_t ihdr[13];
    be32(ihdr, (uint32_t)w); be32(ihdr + 4, (uint32_t)h);
    ihdr[8] = 8; ihdr[9] = ch == 4 ? 6 : 2; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
    chunk(f, "IHDR", ihdr, 13);
    chunk(f, "IDAT", z, (uint32_t)k);
    chunk(f, "IEND", NULL, 0);
    fclose(f);
    free(raw);
    free(z);
    return 0;
}

/* framebuffer RGB565 -> PNG RGB */
static int write_png(const char *path, const uint16_t *fb, int w, int h)
{
    uint8_t *pix = malloc((size_t)w * (size_t)h * 3);
    if (!pix) return -1;
    for (int i = 0; i < w * h; i++) {
        uint16_t c = fb[i];
        uint8_t R = (uint8_t)((c >> 11) & 31), G = (uint8_t)((c >> 5) & 63), B = (uint8_t)(c & 31);
        pix[i * 3] = (uint8_t)((R << 3) | (R >> 2));
        pix[i * 3 + 1] = (uint8_t)((G << 2) | (G >> 4));
        pix[i * 3 + 2] = (uint8_t)((B << 3) | (B >> 2));
    }
    int r = write_png_px(path, pix, w, h, 3);
    free(pix);
    return r;
}

/* Icona dell'app (PLT-083): il marchio dei tre stami in oro (215, 180, 95) su fondo trasparente,
 * disegnato 4 volte più grande e ridotto a 70×70 con la copertura come trasparenza. */
static int write_icon(const char *path)
{
    enum { S = 70, K = 4, B = S * K };
    static uint16_t big[B * B];
    memset(big, 0, sizeof big);
    gfx_fb16_t fb;
    gfx_fb_init(&fb, big, B, B, B);
    ui_flip_logo(&fb, B / 2, B / 2 + 4, (int)(B * 0.86), 0xFFFF, 0xFFFF, 0xFFFF, 256, 3);
    static uint8_t pix[S * S * 4];
    for (int y = 0; y < S; y++)
        for (int x = 0; x < S; x++) {
            int cov = 0;
            for (int j = 0; j < K; j++)
                for (int i = 0; i < K; i++) cov += big[(y * K + j) * B + x * K + i] != 0;
            uint8_t *p = pix + (y * S + x) * 4;
            p[0] = 215; p[1] = 180; p[2] = 95;
            p[3] = (uint8_t)(cov * 255 / (K * K));
        }
    return write_png_px(path, pix, S, S, 4);
}

static vet_t vet;
static ui_flip_state_t st;

static void render_to(const char *dir, const char *name)
{
    gfx_fb16_t fb;
    gfx_fb_init(&fb, px, UI_FLIP_W, UI_FLIP_H, UI_FLIP_W);
    gfx_rect_t dirty[UI_FLIP_MAX_DIRTY];
    ui_flip_invalidate(&st);
    ui_flip_render(&st, vet_model(&vet), &fb, dirty, UI_FLIP_MAX_DIRTY);
    char path[512];
    snprintf(path, sizeof path, "%s/%s.png", dir, name);
    if (write_png(path, px, UI_FLIP_W, UI_FLIP_H) == 0) printf("%s\n", path);
    else printf("errore: %s\n", path);
}

/* ---- audio: la vetrina dall'avvio, con i comandi passati al motore vero (synth, Perform, Beat, looper) ---- */
static dsp_t dsp;
static motore_t mot;
static const smp_bank_t *bank;         /* il banco dei campioni, se c'è (20 §7b) */

static void le16(uint8_t *p, uint32_t v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); }
static void le32(uint8_t *p, uint32_t v) { le16(p, v); le16(p + 2, v >> 16); }

static void wav_header(FILE *f, uint32_t frames)
{
    uint8_t h[44];
    uint32_t bytes = frames * 4u;
    memcpy(h, "RIFF", 4); le32(h + 4, 36u + bytes); memcpy(h + 8, "WAVEfmt ", 8);
    le32(h + 16, 16); le16(h + 20, 1); le16(h + 22, 2); le32(h + 24, 48000); le32(h + 28, 48000u * 4u);
    le16(h + 32, 4); le16(h + 34, 16); memcpy(h + 36, "data", 4); le32(h + 40, bytes);
    fseek(f, 0, SEEK_SET);
    fwrite(h, 1, 44, f);
}

/* WAV 16 bit stereo a 48 kHz di ms millisecondi: avvio, poi la demo (che parte da sola) */
static int render_wav(const char *path, uint32_t ms, bool mpk, int song)
{
    FILE *f = fopen(path, "wb");
    if (!f) { printf("errore: %s\n", path); return 1; }
    wav_header(f, 0);
    vet_init(&vet, 100000);
    vet_battery(&vet, 87, false);
    if (mpk) vet_mpk(&vet, true, NULL, 100000);
    vet_demo_select(&vet, song);
    vet_snd_init(&mot, &dsp, 48000u, 1);
    vet_set_motore(&vet, &mot.snap);
    vet_set_scope(&vet, dsp.scope, DSP_SCOPE_N, &dsp.scope_wr, NULL);
    float L[DSP_BLOCK], R[DSP_BLOCK], pk = 0.0f;
    double sq = 0.0;
    int16_t out[DSP_BLOCK * 2];
    uint32_t frames = 0, clip = 0;
    for (uint32_t t = 0; t < ms; t++) {
        vet_tick(&vet, 100000 + t);
        for (int b = 0; b < 3; b++) {                     /* 1 ms = 48 frame = 3 blocchi */
            vet_snd_render(&mot, &vet, L, R, DSP_BLOCK);
            for (int i = 0; i < DSP_BLOCK; i++) {
                float l = L[i], r = R[i];
                float a = fabsf(l) > fabsf(r) ? fabsf(l) : fabsf(r);
                if (a > pk) pk = a;
                if (a >= 0.999f) clip++;
                sq += (double)l * (double)l + (double)r * (double)r;
                out[2 * i] = (int16_t)(l * 32767.0f);
                out[2 * i + 1] = (int16_t)(r * 32767.0f);
            }
            fwrite(out, sizeof out[0], DSP_BLOCK * 2, f);
            frames += DSP_BLOCK;
        }
    }
    wav_header(f, frames);
    fclose(f);
    double rms = sqrt(sq / (2.0 * frames));
    printf("%s: %.1f s, picco %.3f (%.1f dBFS), rms %.1f dBFS, campioni al limite %u, furti di voce %u\n", path,
           frames / 48000.0, (double)pk, 20.0 * log10((double)pk + 1e-9), 20.0 * log10(rms + 1e-12),
           (unsigned)clip, (unsigned)dsp.steals);
    return 0;
}

/* passo della demo per le PNG: i comandi al motore e 10 ms di audio, perché la plancia mostri il
 * trasporto e il looper veri */
static void seek_step(vet_t *v, void *ctx)
{
    (void)ctx;
    static float l[480], r[480];
    vet_snd_render(&mot, v, l, r, 480);
}

static void seek(uint32_t t)
{
    vet_snd_init(&mot, &dsp, 48000u, 1);
    vet_set_motore(&vet, &mot.snap);
    vet_set_scope(&vet, dsp.scope, DSP_SCOPE_N, &dsp.scope_wr, NULL);   /* la forma d'onda vera */
    vet_demo_seek(&vet, t, seek_step, NULL);
}

/* anteprima dei suoni: ogni suono della vetrina suona lo stesso accordo, ogni basso la stessa nota.
 * Scrive <cartella>/sound_NN.wav e bass_NN.wav e stampa il livello (rms della prima mezza nota). */
static int render_suoni(const char *dir)
{
    static const uint8_t ACCORDO[5] = { 52, 57, 61, 64, 68 };    /* A maj7 su E */
    float L[DSP_BLOCK], R[DSP_BLOCK];
    int16_t out[DSP_BLOCK * 2];
    for (int k = 0; k < VET_N_SOUNDS + VET_N_BASSES; k++) {
        bool bass = k >= VET_N_SOUNDS;
        int n = bass ? k - VET_N_SOUNDS : k;
        char path[512];
        snprintf(path, sizeof path, "%s/%s_%02d.wav", dir, bass ? "bass" : "sound", n + 1);
        FILE *f = fopen(path, "wb");
        if (!f) { printf("errore: %s\n", path); return 1; }
        wav_header(f, 0);
        dsp_init(&dsp, 48000.0f, 1);
        dsp_set_bank(&dsp, bank);
        dsp_set_master_volume(&dsp, 72);
        dsp_set_bass_volume(&dsp, 70);
        dsp_load_patch(&dsp, bass ? DSP_BASS : DSP_SOUND, bass ? vet_bass_patch[n] : vet_sound_patch[n], 0);
        if (bass) dsp_note_on(&dsp, DSP_BASS, 40, 100);
        else for (int i = 0; i < 5; i++) dsp_note_on(&dsp, DSP_SOUND, ACCORDO[i], 100);
        uint32_t frames = 0;
        double sq = 0.0, best = 0.0;
        float pk = 0.0f;
        const uint32_t tot = 48000u * 3u, off = 48000u * 3u / 2u;
        while (frames < tot) {
            if (frames == off) {
                if (bass) dsp_note_off(&dsp, DSP_BASS, 40);
                else for (int i = 0; i < 5; i++) dsp_note_off(&dsp, DSP_SOUND, ACCORDO[i]);
            }
            dsp_render16(&dsp, L, R, NULL, NULL);
            for (int i = 0; i < DSP_BLOCK; i++) {
                sq += (double)L[i] * (double)L[i] + (double)R[i] * (double)R[i];
                float a = fabsf(L[i]) > fabsf(R[i]) ? fabsf(L[i]) : fabsf(R[i]);
                if (a > pk) pk = a;
                out[2 * i] = (int16_t)(L[i] * 32767.0f);
                out[2 * i + 1] = (int16_t)(R[i] * 32767.0f);
            }
            fwrite(out, sizeof out[0], DSP_BLOCK * 2, f);
            frames += DSP_BLOCK;
            if (frames % 4800u == 0) {                       /* finestre da 100 ms mentre la nota è tenuta */
                if (frames <= off && sq > best) best = sq;
                sq = 0.0;
            }
        }
        wav_header(f, frames);
        fclose(f);
        printf("%s %2d  rms %6.1f dBFS  picco %6.1f dBFS  %s\n", bass ? "bass " : "sound", n + 1,
               10.0 * log10(best / 9600.0 + 1e-12), 20.0 * log10((double)pk + 1e-9), path);
    }
    return 0;
}

/* ---- la libreria dei kit sintetizzati (SND-542): per ogni strumento di ogni kit il picco mono di un colpo
 * a 127 con guadagno 1, come dizionario PICCO_DB da incollare in tools/kits.py; e per ogni kit un WAV
 * d'ascolto, <cartella>/kit_NN.wav: i dodici strumenti uno dopo l'altro, poi due battute del Funk ---- */
static int render_kits(const char *dir)
{
    static drums_t k;
    float L[DSP_BLOCK], R[DSP_BLOCK];
    int16_t out[DSP_BLOCK * 2];
    printf("PICCO_DB = {\n");
    for (int ki = 0; ki < DRUM_SYNTH_KITS; ki++) {
        printf("    '%s': (", drum_kits[ki].name);
        for (int i = 0; i < DRUM_KIT_INST; i++) {
            const drum_rec_t *r = &drum_kits[ki].r[i];
            float th = (r->pan + 1.0f) * 0.25f * 3.14159265f, gs = cosf(th) + sinf(th), pk = 0.0f;
            drums_init(&k, 48000.0f, 7);
            drums_volume(&k, 99);
            drums_set_synth(&k, &drum_kits[ki]);
            drums_hit(&k, (uint8_t)i, 127);
            for (int b = 0; b < 48000 * 7 / DSP_BLOCK && k.v[0].on; b++) {
                memset(L, 0, sizeof L);
                memset(R, 0, sizeof R);
                drums_render16(&k, L, R);
                for (int s = 0; s < DSP_BLOCK; s++) {
                    float y = fabsf((L[s] + R[s]) / gs);
                    if (y > pk) pk = y;
                }
            }
            printf("%.2f%s", 20.0 * log10((double)(pk / r->gain) + 1e-12), i < DRUM_KIT_INST - 1 ? ", " : "");
        }
        printf("),\n");
        char path[512];
        snprintf(path, sizeof path, "%s/kit_%02d.wav", dir, ki + 1);
        FILE *f = fopen(path, "wb");
        if (!f) { printf("errore: %s\n", path); return 1; }
        wav_header(f, 0);
        drums_init(&k, 48000.0f, 7);
        drums_volume(&k, 72);
        drums_set_synth(&k, &drum_kits[ki]);
        uint32_t frames = 0;
        const uint32_t step16 = 6000u;                       /* un sedicesimo a 120 BPM */
        for (uint32_t n = 0; n < 12u * 24000u + 32u * step16 + 48000u; n += DSP_BLOCK) {
            if (n < 12u * 24000u && n % 24000u == 0) drums_hit(&k, (uint8_t)(n / 24000u), 110);
            uint32_t m = n - 12u * 24000u;
            if (n >= 12u * 24000u && m % step16 == 0 && m / step16 < 32u) {
                beat_hit_t h[8];
                int nh = beat_hits(1, (int)(m / step16 % 16u), h, 8);
                for (int j = 0; j < nh; j++) drums_hit(&k, h[j].inst, h[j].vel);
            }
            memset(L, 0, sizeof L);
            memset(R, 0, sizeof R);
            drums_render16(&k, L, R);
            for (int s = 0; s < DSP_BLOCK; s++) {
                out[2 * s] = (int16_t)(fmaxf(-1.0f, fminf(1.0f, L[s])) * 32767.0f);
                out[2 * s + 1] = (int16_t)(fmaxf(-1.0f, fminf(1.0f, R[s])) * 32767.0f);
            }
            fwrite(out, sizeof out[0], DSP_BLOCK * 2, f);
            frames += DSP_BLOCK;
        }
        wav_header(f, frames);
        fclose(f);
    }
    printf("}\n");
    return 0;
}

/* ---- scene: le schermate del manuale, pilotando la vetrina con gli ingressi veri (tasti del macro
 * pad, note della MPK, tasti della Flip) e scattando a ogni stato ---- */
static uint32_t sc_now;

static void sc_run(uint32_t ms)                       /* avanza la vetrina di ms millisecondi, con l'audio */
{
    static float l[480], r[480];
    for (uint32_t t = 0; t < ms; t += 10) {
        sc_now += 10;
        vet_tick(&vet, sc_now);
        vet_snd_render(&mot, &vet, l, r, 480);
        vet_model(&vet);
    }
}

static void sc_hold(uint16_t code, uint32_t ms)
{
    vet_pad(&vet, code, 1, sc_now);
    sc_run(ms);
    vet_pad(&vet, code, 0, sc_now);
    sc_run(40);
}

static void sc_pad(uint16_t code) { sc_hold(code, 60); }

static void sc_midi(uint8_t st, uint8_t d1, uint8_t d2)
{
    midi_msg_t m;
    memset(&m, 0, sizeof m);
    m.t_us = sc_now * 1000u;
    m.port = MIDI_PORT_CTL;
    m.n = 3;
    m.b[0] = st; m.b[1] = d1; m.b[2] = d2;
    vet_midi(&vet, &m, sc_now);
}

/* porta 2 (DAW) della MK4: manopole, SHIFT, trasporto, nav, − e + (mappa del 16/10/2026) */
static void sc_daw(uint8_t d1, uint8_t d2)
{
    midi_msg_t m;
    memset(&m, 0, sizeof m);
    m.t_us = sc_now * 1000u;
    m.port = MIDI_PORT_DIN;
    m.n = 3;
    m.b[0] = 0xB0; m.b[1] = d1; m.b[2] = d2;
    vet_midi(&vet, &m, sc_now);
}

static void sc_daw_tap(uint8_t cc) { sc_daw(cc, 127); sc_run(60); sc_daw(cc, 0); sc_run(40); }

/* SHIFT + K: tenuto ms millisecondi con la manopola toccata (tocco = premi, oltre 1 s = tieni) */
static void sc_push(uint8_t knob, uint32_t ms)
{
    sc_daw(17, 127);
    sc_run(20);
    sc_daw((uint8_t)(24 + knob), 1);
    sc_run(ms);
    sc_daw(17, 0);
    sc_run(40);
}

static void sc_back(void) { sc_daw_tap(80); }           /* − della MK4: Back */

/* Do maggiore: il pad Maj (ch10, nota 42) e il tasto Do (ch1, nota 60) della MPK */
static void sc_chord(bool on)
{
    if (on) { sc_midi(0x99, 42, 100); sc_run(20); sc_midi(0x90, 60, 100); }
    else { sc_midi(0x80, 60, 0); sc_run(20); sc_midi(0x89, 42, 0); }
    sc_run(120);
}

static void sc_setup(void)
{
    vet_init(&vet, 100000);
    sc_now = 100000;
    vet_battery(&vet, 87, false);
    vet_snd_init(&mot, &dsp, 48000u, 1);
    vet_set_motore(&vet, &mot.snap);
    vet_set_scope(&vet, dsp.scope, DSP_SCOPE_N, &dsp.scope_wr, NULL);
    sc_run(2500);                                     /* l'avvio dura 2,6 s: un ingresso prima della fine, */
    sc_pad(PAD_B);                                    /* così la demo non parte e lo stato resta quello di fabbrica */
    vet_mpk_model(&vet, MPK_MODEL_MK4);
    vet_mpk(&vet, true, "1.0.0", sc_now);
    vet_macropad(&vet, PADL_OPEN, sc_now);
    sc_run(2500);                                     /* passano gli avvisi di collegamento */
}

/* MENU › Theme: alterna Notte e Giorno dal menu della piattaforma con la manopola nav della MK4.
 * Theme è la terza voce: Exit, Panic, Theme */
static void sc_theme_toggle(void)
{
    sc_pad(PAD_MENU);
    sc_daw(14, 2);
    sc_run(60);
    sc_daw_tap(13);
    sc_back();
    sc_run(300);
}

/* le schermate del manuale, dei disegni, del sito e dell'identità stanno nel tema Giorno (Luigi, 15/10/2026:
 * «preferisci modalità chiara»); «notte» è la stessa pagina di gioco nel tema Notte, per confronto */
static int render_scene(const char *dir)
{
    /* avvio */
    vet_init(&vet, 100000);
    vet.m.prefs.theme = THEME_LIGHT;
    vet_battery(&vet, 87, false);
    for (uint32_t k = 0; k <= 2000; k += 10) vet_tick(&vet, 100000 + k);
    render_to(dir, "avvio");

    sc_setup();
    if (vet.m.prefs.theme != THEME_LIGHT) sc_theme_toggle();     /* Giorno (il default dal 15/10/2026: si chiede, non si commuta) */
    if (vet_model(&vet)->music.key_on) { sc_push(3, 60); sc_run(3600); }   /* SHIFT + K4: Key mode spenta, il nome è quello dell'accordo; la banda torna a riposo */
    /* pagina di gioco con un accordo */
    sc_chord(true);
    sc_run(400);
    render_to(dir, "gioco");
    /* il controllo appena toccato: FX, K3 della MK4 girata di un passo (8 unità) */
    sc_daw(26, 8);
    sc_run(150);
    render_to(dir, "tocco");
    sc_run(2000);
    /* pagina dei comandi (T15) */
    sc_pad(MPAD_T15);
    sc_run(200);
    render_to(dir, "comandi");
    sc_pad(MPAD_T15);
    /* lista dei suoni (SHIFT + K1) e dei Beat (SHIFT + K7 tenuto) */
    sc_push(0, 60);
    sc_run(200);
    render_to(dir, "lista_suoni");
    sc_back();
    sc_push(6, 1200);
    sc_run(200);
    render_to(dir, "lista_beat");
    sc_back();
    sc_run(300);
    /* Geek Out (T14) */
    sc_pad(MPAD_T14);
    sc_run(200);
    render_to(dir, "geek");
    sc_pad(MPAD_T14);
    sc_chord(false);
    /* looper: Beat acceso (STOP/PLAY), REC, un giro di accordi, poi il loop suona */
    sc_daw_tap(76);
    sc_run(300);
    sc_daw_tap(77);
    sc_run(2100);                                     /* count-in: una battuta a 120 BPM */
    for (int bar = 0; bar < 4; bar++) {
        sc_chord(true);
        sc_run(700);
        if (bar == 1) render_to(dir, "rec");          /* mentre registra: cornice e barra rosse */
        sc_run(700);
        sc_chord(false);
        sc_run(300);
    }
    sc_run(1200);
    sc_chord(true);
    sc_run(300);
    render_to(dir, "looper");
    sc_chord(false);
    /* batteria a tastiera: T11 del pad, poi i tasti colpiscono il kit */
    sc_pad(MPAD_T11);
    sc_run(200);
    sc_midi(0x90, 60, 110); sc_run(60); sc_midi(0x80, 60, 0); sc_run(300);
    sc_midi(0x90, 64, 90);  sc_run(60); sc_midi(0x80, 64, 0); sc_run(300);
    sc_midi(0x90, 62, 110); sc_run(40);
    render_to(dir, "drums");
    sc_midi(0x80, 62, 0);
    /* la batteria che si inventa (MIDI-139): il Beat suona già; m1 la accende nello stile del Beat, M alza
     * la densità, m2 cambia variazione, m1 premuta sceglie la cassa */
    sc_pad(MPAD_M1_CW); sc_run(120);
    sc_pad(MPAD_M_CW); sc_run(120);
    sc_pad(MPAD_M_CW); sc_run(120);
    for (int i = 0; i < 3; i++) { sc_pad(MPAD_M2_CW); sc_run(120); }
    sc_pad(MPAD_M1_PUSH); sc_run(1500);
    render_to(dir, "drums_inventa");
    /* la pagina dei comandi sotto DRUMS: le celle KIT, ROLL, DRIVE, SWING e ACCENT (MIDI-135), con drive 4 e
     * swing 58 % (K3 vale 8 unità per scatto, K4 12); in testata SWING e DRUM FX */
    for (int i = 0; i < 32; i++) sc_daw(26, 1);
    for (int i = 0; i < 48; i++) sc_daw(27, 1);
    sc_run(100);
    sc_pad(MPAD_T15);
    sc_run(200);
    render_to(dir, "drums_comandi");
    sc_pad(MPAD_T15);
    sc_run(200);
    for (int i = 0; i < 32; i++) sc_daw(26, 0x7F);              /* di nuovo a zero: le scene dopo sono senza */
    for (int i = 0; i < 48; i++) sc_daw(27, 0x7F);
    sc_run(100);
    sc_pad(MPAD_T11);
    sc_run(2200);
    /* Drop (T13 tenuto, MIDI-140): il loop di batteria suona ancora; l'accordo resta, Beat e basso tacciono */
    sc_chord(true);
    sc_run(300);
    vet_pad(&vet, MPAD_T13, 1, sc_now);
    sc_run(400);
    render_to(dir, "drop");
    vet_pad(&vet, MPAD_T13, 0, sc_now);
    sc_run(300);
    sc_chord(false);
    sc_run(200);
    /* menu della piattaforma, poi la stessa pagina di gioco nel tema Notte */
    sc_pad(PAD_MENU);
    sc_run(200);
    render_to(dir, "menu");
    for (int i = 0; i < 7; i++) sc_pad(PAD_DOWN);               /* Play Demo Song: la lista dei brani */
    sc_pad(PAD_A);
    sc_run(200);
    render_to(dir, "demo_lista");
    sc_back();                                                   /* torna al menu */
    sc_back();
    sc_run(5200);                                                /* la pagina dei comandi, aperta dalla croce, si chiude dopo 5 s */
    if (vet.m.prefs.theme != THEME_DARK) sc_theme_toggle();      /* Notte */
    sc_chord(true);
    sc_run(400);
    render_to(dir, "notte");
    sc_chord(false);
    /* di nuovo Giorno, per i disegni, il sito e l'identità: un nome con l'estensione (Re, pad Maj e M7) */
    if (vet.m.prefs.theme != THEME_LIGHT) sc_theme_toggle();
    sc_run(3600);
    sc_midi(0x99, 42, 100); sc_midi(0x99, 38, 100); sc_run(20); sc_midi(0x90, 62, 100);
    sc_run(400);
    render_to(dir, "nome");
    /* la vista React: R1 della Flip porta il fuoco su Options, la croce a sinistra la gira */
    for (int i = 0; i < 2 * ENC_COUNT && vet.inp.gest.focus != ENC_OPTIONS; i++) sc_pad(PAD_R1);
    for (int i = 0; i < VIEW_COUNT && vet_model(&vet)->ctl.view != VIEW_REACT; i++) sc_pad(PAD_LEFT);
    sc_pad(PAD_B);
    sc_run(1200);
    render_to(dir, "react");
    for (int i = 0; i < VIEW_COUNT && vet_model(&vet)->ctl.view != VIEW_CHORD; i++) sc_pad(PAD_RIGHT);
    sc_pad(PAD_B);
    sc_run(3600);
    /* premi e gira Key (SHIFT + K4 toccata, poi girata di tre passi da 12 unità): Transpose +3 */
    sc_daw(17, 127);
    sc_run(20);
    sc_daw(27, 1);
    sc_run(400);                                      /* oltre MK4_PUSH_DEBOUNCE_US la manopola gira */
    for (int i = 0; i < 3; i++) { sc_daw(27, 12); sc_run(60); }
    sc_run(200);
    render_to(dir, "transpose");
    sc_daw(17, 0);
    sc_run(40);
    sc_midi(0x80, 62, 0); sc_run(20); sc_midi(0x89, 38, 0); sc_midi(0x89, 42, 0);
    sc_run(120);
    return 0;
}

int main(int argc, char **argv)
{
    /* il banco dei campioni, se tools/campioni.py lo ha costruito (STAME_SMP lo sposta) */
    const char *smp = getenv("STAME_SMP");
    bank = banco_carica(smp ? smp : "build/campioni/stame.smp");
    if (!bank) fprintf(stderr, "banco dei campioni: %s (suoni SMP e kit muti)\n", banco_errore());
    vet_snd_set_bank(bank);
    if (argc >= 3 && !strcmp(argv[1], "--suoni")) return render_suoni(argv[2]);
    if (argc >= 3 && !strcmp(argv[1], "--kits")) return render_kits(argv[2]);
    if (argc < 2) {
        printf("uso: stame-render <cartella> [--mpk] [ms…] [--boot ms…] [--tutti passo_ms]\n"
               "     stame-render --wav file.wav [ms] [--mpk] [--song N]   (la vetrina con il synth, dall'avvio)\n"
               "     stame-render --scene <cartella>   (le schermate del manuale: avvio, gioco, comandi, lock, liste…)\n");
        return 2;
    }
    crc_init();
    if (argc >= 3 && !strcmp(argv[1], "--scene")) return render_scene(argv[2]);
    if (!strcmp(argv[1], "--wav") && argc >= 3) {
        int song = 0;
        bool m = false;
        for (int i = 3; i < argc; i++) {
            if (!strcmp(argv[i], "--mpk")) m = true;
            else if (!strcmp(argv[i], "--song") && i + 1 < argc) song = atoi(argv[++i]);
        }
        uint32_t ms = argc >= 4 && argv[3][0] != '-' ? (uint32_t)atoi(argv[3]) : 2600u + vet_demo_len(song);
        return render_wav(argv[2], ms, m, song);
    }
    const char *dir = argv[1];
    bool boot = false, mpk = false;
    for (int i = 2; i < argc; i++) {
        if (!strcmp(argv[i], "--boot")) { boot = true; continue; }
        if (!strcmp(argv[i], "--mpk")) { mpk = true; continue; }   /* MPK collegata: testata a riposo */
        if (!strcmp(argv[i], "--icona") && i + 1 < argc) {
            const char *p = argv[++i];
            printf("%s %s\n", p, write_icon(p) == 0 ? "" : "(errore)");
            continue;
        }
        if (!strcmp(argv[i], "--tutti") && i + 1 < argc) {
            uint32_t step = (uint32_t)atoi(argv[++i]);
            for (uint32_t t = 0; t <= vet_demo_len(0); t += step) {
                vet_init(&vet, 100000);
                vet_battery(&vet, 87, false);
                if (mpk) vet_mpk(&vet, true, NULL, 100000);
                seek(t);
                char name[64];
                snprintf(name, sizeof name, "demo_%05u", (unsigned)t);
                render_to(dir, name);
            }
            continue;
        }
        uint32_t t = (uint32_t)atoi(argv[i]);
        char name[64];
        vet_init(&vet, 100000);
        vet_battery(&vet, 87, false);
        if (mpk) vet_mpk(&vet, true, NULL, 100000);
        if (boot) {
            for (uint32_t k = 0; k <= t; k += 10) vet_tick(&vet, 100000 + k);
            snprintf(name, sizeof name, "avvio_%05u", (unsigned)t);
        } else {
            seek(t);
            snprintf(name, sizeof name, "demo_%05u", (unsigned)t);
        }
        render_to(dir, name);
    }
    return 0;
}
