/* audio.c — il synth di Stame sulla Flip (F4 della sezione 50).
 *
 * Backend di riserva di PLT-022: il callback dell'audio di SDL, che SDL chiama dal suo thread ad alta
 * priorità. Il thread principale manda i comandi della vetrina su una coda SPSC (PLT-015); il
 * callback li applica al motore (performance, Beat, looper e synth) e rende a blocchi di 16 (SND-002):
 * prima di ogni blocco, quelli senza tempo subito e quelli della demo al loro tick. Nel callback niente
 * lock, niente heap, niente I/O (PLT-019). Il logo sonoro dell'avvio si somma all'uscita.
 * Il backend ALSA diretto (PLT-022, periodo 256 × 2) arriverà dopo: qui il periodo lo decide SDL.
 */
#define _GNU_SOURCE
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "flip.h"
#include "../vetrina/vetrina_dsp.h"
#include "../../core/spsc.h"

static dsp_t dsp;
static motore_t mot;                   /* di proprietà del thread audio (PLT-006) */
static spsc_t q;
static vet_snd_t qbuf[1024];
static float bl[DSP_BLOCK], br[DSP_BLOCK];
static int bpos = DSP_BLOCK;
static int16_t *logo;                  /* PCM 16 bit stereo del logo */
static uint32_t logo_frames;
static _Atomic uint32_t logo_pos = UINT32_MAX;
static volatile float peak[2];
static float pk_hold[2];
static int opened;

/* SND-703, PLT-013: denormali a zero nel thread audio (FPCR.FZ su aarch64), altrimenti le code dei
 * filtri, dei riverberi e dei delay rallentano la FPU quando il suono si spegne */
static void flush_to_zero(void)
{
#if defined(__aarch64__)
    uint64_t r;
    __asm__ volatile("mrs %0, fpcr" : "=r"(r));
    if (!(r & (1u << 24))) { r |= 1u << 24; __asm__ volatile("msr fpcr, %0" : : "r"(r)); }
#endif
}

static void cb(void *ud, uint8_t *stream, int len)
{
    (void)ud;
    flush_to_zero();
    float *out = (float *)stream;
    int frames = len / (int)(2 * sizeof(float));
    vet_snd_t e;
    uint32_t lp0 = atomic_load_explicit(&logo_pos, memory_order_acquire), lp = lp0;
    float p0 = 0.0f, p1 = 0.0f;
    for (int i = 0; i < frames; i++) {
        if (bpos == DSP_BLOCK) {
            /* i comandi prima del blocco: subito, o al loro tick quelli della demo (vet_snd_due) */
            while (spsc_peek(&q, &e) && vet_snd_due(&mot, &e)) { spsc_pop(&q, &e); vet_snd_apply(&mot, &e); }
            mot_render(&mot, bl, br, DSP_BLOCK);
            bpos = 0;
        }
        float l = bl[bpos], r = br[bpos];
        bpos++;
        if (lp < logo_frames) {
            l += (float)logo[2 * lp] * (1.0f / 32768.0f);
            r += (float)logo[2 * lp + 1] * (1.0f / 32768.0f);
            lp++;
        }
        if (l > 1.0f) l = 1.0f; else if (l < -1.0f) l = -1.0f;
        if (r > 1.0f) r = 1.0f; else if (r < -1.0f) r = -1.0f;
        out[2 * i] = l;
        out[2 * i + 1] = r;
        float al = l < 0.0f ? -l : l, ar = r < 0.0f ? -r : r;
        if (al > p0) p0 = al;
        if (ar > p1) p1 = ar;
    }
    if (lp0 != UINT32_MAX)                                /* se nel frattempo il logo è ripartito, vince quello */
        atomic_compare_exchange_strong(&logo_pos, &lp0, lp >= logo_frames ? UINT32_MAX : lp);
    /* picchi con un rilascio lento, per i meter della plancia */
    for (int c = 0; c < 2; c++) {
        float p = c ? p1 : p0;
        pk_hold[c] = p > pk_hold[c] ? p : pk_hold[c] * 0.92f;
        peak[c] = pk_hold[c];
    }
}

/* WAV PCM 16 bit stereo, tutto in memoria (dal thread principale, prima dell'audio) */
static void load_logo(const char *path)
{
    FILE *f = fopen(path, "rb");
    if (!f) { log_msg("audio: %s assente", path); return; }
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    uint8_t *buf = malloc((size_t)n);
    if (!buf || fread(buf, 1, (size_t)n, f) != (size_t)n) { fclose(f); free(buf); return; }
    fclose(f);
    long pos = 12;
    int ok = n > 44 && !memcmp(buf, "RIFF", 4) && !memcmp(buf + 8, "WAVE", 4);
    uint16_t fmt = 0, ch = 0, bits = 0;
    while (ok && pos + 8 <= n) {
        uint32_t sz = (uint32_t)buf[pos + 4] | (uint32_t)buf[pos + 5] << 8 | (uint32_t)buf[pos + 6] << 16 |
                      (uint32_t)buf[pos + 7] << 24;
        if (!memcmp(buf + pos, "fmt ", 4) && sz >= 16 && pos + 24 <= n) {
            fmt = (uint16_t)(buf[pos + 8] | buf[pos + 9] << 8);
            ch = (uint16_t)(buf[pos + 10] | buf[pos + 11] << 8);
            bits = (uint16_t)(buf[pos + 22] | buf[pos + 23] << 8);
        } else if (!memcmp(buf + pos, "data", 4)) {
            if (fmt != 1 || bits != 16 || ch != 2) break;
            uint32_t m = sz;
            if (pos + 8 + (long)m > n) m = (uint32_t)(n - pos - 8);
            logo = malloc(m);
            if (logo) { memcpy(logo, buf + pos + 8, m); logo_frames = m / 4u; }
            break;
        }
        pos += 8 + (long)sz + (long)(sz & 1);
    }
    free(buf);
    if (!logo) log_msg("audio: %s non è un WAV 16 bit stereo", path);
}

int audio_open(int frames)
{
    spsc_init(&q, qbuf, sizeof qbuf[0], (uint32_t)STAME_COUNT(qbuf));
    load_logo("stame_avvio.wav");
    vet_snd_init(&mot, &dsp, 48000u, 0x5747u);
    int rate = 0, got = 0;
    if (sdl_audio_open(48000, frames, cb, &rate, &got) != 0) return -1;
    if (rate != 48000) log_msg("audio: il dispositivo lavora a %d Hz, il synth a 48000: converte SDL", rate);
    log_msg("audio: synth a 48 kHz, periodo %d frame (%.1f ms)", got, (double)got * 1000.0 / 48000.0);
    opened = 1;
    return 0;
}

void audio_send(const void *cmd)
{
    if (opened) spsc_push(&q, cmd);
}

void audio_logo(void)
{
    if (logo) atomic_store_explicit(&logo_pos, 0u, memory_order_release);
}

void audio_close(void)
{
    sdl_audio_close();
    opened = 0;
    free(logo);
    logo = NULL;
}

const int16_t *audio_scope(uint16_t *len, const volatile uint32_t **wr, const volatile float **pk)
{
    *len = DSP_SCOPE_N;
    *wr = &dsp.scope_wr;
    *pk = peak;
    return dsp.scope;
}

const mot_snap_t *audio_motore(void)
{
    return &mot.snap;
}
