/* main.c — la vetrina di Stame sulla Miyoo Flip.
 *
 * Un thread solo: legge tasti e MIDI, fa avanzare la vetrina, disegna la plancia con ui_flip e
 * presenta solo quando qualcosa è cambiato (UI-115). Si esce dal MENU con «Quit Stame» o con
 * SIGTERM/SIGINT (PLT-057, PLT-086). Il suono lo fa il synth vero nel thread audio (audio.c): qui si
 * passano soltanto i comandi della vetrina, subito dopo ogni ingresso.
 */
#define _GNU_SOURCE
#include <poll.h>
#include <stdlib.h>
#include <signal.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include "flip.h"
#include "../vetrina/vetrina.h"
#include "../vetrina/vetrina_dsp.h"
#include "../vetrina/banco.h"
#include "../../ui_flip/ui_flip.h"

static volatile sig_atomic_t stop;
static void on_signal(int s) { (void)s; stop = 1; }

uint32_t now_ms(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint32_t)((uint64_t)ts.tv_sec * 1000u + (uint64_t)ts.tv_nsec / 1000000u);
}

void log_msg(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    fprintf(stderr, "[stame %u] ", now_ms());
    vfprintf(stderr, fmt, ap);
    fputc('\n', stderr);
    va_end(ap);
}

void battery_read(uint8_t *pct, bool *charging)
{
    *pct = 255;
    *charging = false;
    FILE *f = fopen("/sys/class/power_supply/battery/capacity", "r");
    if (f) { int v; if (fscanf(f, "%d", &v) == 1 && v >= 0 && v <= 100) *pct = (uint8_t)v; fclose(f); }
    f = fopen("/sys/class/power_supply/battery/status", "r");
    if (f) { char s[32] = { 0 }; if (fgets(s, sizeof s, f)) *charging = strncmp(s, "Charging", 8) == 0; fclose(f); }
}

static vet_t vet;
static ui_flip_state_t ufs;
static uint16_t px[UI_FLIP_W * UI_FLIP_H];
static midi_parser_t parser, parser2;            /* porta 1 e porta 2 (DAW della MK4) */

/* comandi della vetrina verso il synth: si mandano subito, prima di disegnare */
static void pump(void)
{
    vet_snd_t e;
    while (vet_snd_pop(&vet, &e)) audio_send(&e);
}

static void on_pad(void *ctx, uint16_t code, int32_t value)
{
    (void)ctx;
    vet_pad(&vet, code, value, now_ms());
    pump();
}

/* --prova: la vetrina gira in memoria, senza schermo né tasti, e misura il tempo di disegno
 * (budget UI-160: fotogramma tipico ≤ 4 ms, ridisegno completo ≤ 8 ms sull'A55). */
static int prova(void)
{
    gfx_fb16_t fb;
    gfx_fb_init(&fb, px, UI_FLIP_W, UI_FLIP_H, UI_FLIP_W);
    gfx_rect_t dirty[UI_FLIP_MAX_DIRTY];
    struct timespec a, b;
    vet_init(&vet, 1000);
    vet_battery(&vet, 90, false);
    double tot = 0, peggiore = 0, completo = 0;
    int frames = 0, presentati = 0, quale = -1;
    for (uint32_t t = 0; t < 70000; t += 16) {
        vet_tick(&vet, 1000 + t);
        const ui_model_t *m = vet_model(&vet);
        if (t == 40000) ui_flip_invalidate(&ufs);
        clock_gettime(CLOCK_MONOTONIC, &a);
        int nd = ui_flip_render(&ufs, m, &fb, dirty, UI_FLIP_MAX_DIRTY);
        clock_gettime(CLOCK_MONOTONIC, &b);
        double ms = (double)(b.tv_sec - a.tv_sec) * 1000.0 + (double)(b.tv_nsec - a.tv_nsec) / 1e6;
        if (t == 40000) completo = ms;
        frames++;
        if (nd > 0) { presentati++; tot += ms; if (ms > peggiore) { peggiore = ms; quale = frames - 1; } }
    }
    uint32_t h = 2166136261u;
    for (int i = 0; i < UI_FLIP_W * UI_FLIP_H; i++) { h ^= px[i]; h *= 16777619u; }
    printf("prova: %d fotogrammi, %d disegnati, medio %.2f ms, peggiore %.2f ms (fotogramma %d), completo %.2f ms, firma %08x\n",
           frames, presentati, presentati ? tot / presentati : 0.0, peggiore, quale, completo, h);
    return 0;
}

/* --prova-audio: tutto il brano della demo reso dal synth in memoria, senza dispositivo audio; misura
 * la frazione di un core usata (PLT-034, SND-700) e il blocco peggiore. Niente schermo né tasti. */
#include "../vetrina/vetrina_dsp.h"
static dsp_t dsp_prova;
static motore_t mot_prova;
static int prova_audio(void)
{
    vet_init(&vet, 1000);
    vet_snd_init(&mot_prova, &dsp_prova, 48000u, 1);
    vet_set_motore(&vet, &mot_prova.snap);
    float L[DSP_BLOCK], R[DSP_BLOCK];
    struct timespec a, b, c, d;
    double peggiore = 0.0;
    int voci = 0;
    const uint32_t durata = 2600u + vet_demo_len(0);         /* avvio, poi il primo brano intero */
    clock_gettime(CLOCK_MONOTONIC, &a);
    for (uint32_t t = 0; t < durata; t++) {
        vet_tick(&vet, 1000 + t);
        for (int k = 0; k < 3; k++) {
            clock_gettime(CLOCK_MONOTONIC, &c);
            vet_snd_render(&mot_prova, &vet, L, R, DSP_BLOCK);
            clock_gettime(CLOCK_MONOTONIC, &d);
            double us = (double)(d.tv_sec - c.tv_sec) * 1e6 + (double)(d.tv_nsec - c.tv_nsec) / 1e3;
            if (us > peggiore) peggiore = us;
        }
        int n = dsp_voices_active(&dsp_prova);
        if (n > voci) voci = n;
    }
    clock_gettime(CLOCK_MONOTONIC, &b);
    double s = (double)(b.tv_sec - a.tv_sec) + (double)(b.tv_nsec - a.tv_nsec) / 1e9;
    double sec = durata / 1000.0;
    printf("prova-audio: %.0f s di demo in %.2f s, %.1f %% di un core, blocco peggiore %.0f us su 333, voci al massimo %d\n",
           sec, s, s / sec * 100.0, peggiore, voci);
    return 0;
}

int main(int argc, char **argv)
{
    if (argc > 1 && !strcmp(argv[1], "--prova")) return prova();
    if (argc > 1 && !strcmp(argv[1], "--prova-audio")) return prova_audio();
    signal(SIGTERM, on_signal);
    signal(SIGINT, on_signal);
    signal(SIGPIPE, SIG_IGN);
    log_msg("vetrina di Stame: avvio");
    if (video_open() != 0) { video_close(); return 1; }

    gfx_fb16_t fb;
    gfx_fb_init(&fb, px, UI_FLIP_W, UI_FLIP_H, UI_FLIP_W);
    uint32_t t = now_ms();
    vet_init(&vet, t);
    midi_parser_init(&parser, MIDI_PORT_CTL);
    midi_parser_init(&parser2, MIDI_PORT_DIN);
    /* il banco dei campioni accanto al binario (launch.sh fa cd nella cartella dell'app), prima dell'audio */
    const smp_bank_t *bank = banco_carica("stame.smp");
    {
        char info[64];
        banco_info(bank, info, sizeof info);
        if (bank) log_msg("campioni: %s", info); else log_msg("campioni: nessun banco (%s): suoni SMP e kit muti", banco_errore());
    }
    vet_snd_set_bank(bank);
    const char *fr = getenv("STAME_AUDIO_FRAMES");
    if (audio_open(fr ? atoi(fr) : 512) == 0) {
        uint16_t sl;
        const volatile uint32_t *sw;
        const volatile float *pk;
        const int16_t *sc = audio_scope(&sl, &sw, &pk);
        vet_set_scope(&vet, sc, sl, sw, pk);
        vet_set_motore(&vet, audio_motore());
    } else log_msg("audio: synth spento, la vetrina resta muta");

    int pad = pad_open();
    int mpad = 0;                                       /* nodi aperti del macro pad */
    midi_dev_t midi = { -1, -1, -1, 0, "" };
    uint32_t next_scan = t, next_batt = t;
    gfx_rect_t dirty[UI_FLIP_MAX_DIRTY];
    int suonato = 0;

    while (!stop && !vet_quit(&vet)) {
        struct pollfd pf[8];
        int n = 0;
        if (pad >= 0) { pf[n].fd = pad; pf[n].events = POLLIN; n++; }
        if (midi.fd >= 0) { pf[n].fd = midi.fd; pf[n].events = POLLIN; n++; }
        if (midi.fd2 >= 0) { pf[n].fd = midi.fd2; pf[n].events = POLLIN; n++; }
        int mfd[6], nm = macropad_fds(mfd, 6);
        for (int i = 0; i < nm; i++) { pf[n].fd = mfd[i]; pf[n].events = POLLIN; n++; }
        poll(pf, (nfds_t)n, 5);
        t = now_ms();

        if (pad >= 0) pad_read(pad, on_pad, NULL);
        if (mpad > 0) {                                  /* macro pad (MIDI-122…127) */
            int r = macropad_read(on_pad, NULL);
            if (r < 0) {
                log_msg("pad: scollegato");
                macropad_close();
                mpad = 0;
                vet_macropad(&vet, PADL_ABSENT, t);
                pump();
            } else if (r >= 5 && vet.m.plat.pad_link == PADL_OPEN) {
                vet_macropad(&vet, PADL_UNMAPPED, t);    /* cinque codici sconosciuti di fila (MIDI-123) */
            }
        }
        if (midi.fd >= 0) {
            uint8_t buf[256];
            int r = 0, lost = 0;
            for (int port = 0; port < 2 && !lost; port++) {   /* porta 1, poi la 2 della MK4 */
                midi_parser_t *ps = port ? &parser2 : &parser;
                while ((r = midi_read(&midi, port, buf, sizeof buf)) > 0) {
                    for (int i = 0; i < r; i++) {
                        midi_msg_t m[MIDI_PARSE_MAX_OUT];
                        int k = midi_parse_byte(ps, buf[i], t * 1000u, m);
                        for (int j = 0; j < k; j++) vet_midi(&vet, &m[j], t);
                    }
                }
                if (r < 0) lost = 1;
            }
            pump();
            if (lost) {
                log_msg("MIDI: dispositivo perso");
                midi_close(&midi);
                vet_mpk(&vet, false, NULL, t);
                midi_parser_init(&parser, MIDI_PORT_CTL);
                midi_parser_init(&parser2, MIDI_PORT_DIN);
            }
        }
        if ((int32_t)(t - next_scan) >= 0) {             /* hot-plug della MPK, una volta al secondo */
            next_scan = t + 1000;
            if (midi.fd < 0 && midi_scan(&midi)) {
                vet_mpk_model(&vet, midi.model ? MPK_MODEL_MK4 : MPK_MODEL_PLUS);
                vet_mpk(&vet, true, NULL, t);
            }
            if (mpad <= 0) {
                int r = macropad_open();
                if (r > 0) { mpad = r; vet_macropad(&vet, PADL_OPEN, t); }
                else if (r == -2 && vet.m.plat.pad_link != PADL_ERROR) vet_macropad(&vet, PADL_ERROR, t);
            }
        }
        if ((int32_t)(t - next_batt) >= 0) {             /* batteria ogni 5 s (PLT-090) */
            next_batt = t + 5000;
            uint8_t pct;
            bool ch;
            battery_read(&pct, &ch);
            vet_battery(&vet, pct, ch);
        }

        vet_tick(&vet, t);
        pump();
        /* logo sonoro: parte con la prima antera (800 ms dall'inizio dell'avvio) */
        if (!suonato && vet.booting && vet.m.boot.t_ms >= 800) {
            suonato = 1;
            audio_logo();
        }
        const ui_model_t *m = vet_model(&vet);
        int nd = ui_flip_render(&ufs, m, &fb, dirty, UI_FLIP_MAX_DIRTY);
        if (nd > 0) video_present(px, dirty, nd);
    }

    log_msg("vetrina di Stame: uscita");
    audio_close();
    macropad_close();
    midi_close(&midi);
    pad_close(pad);
    video_close();
    return 0;
}
