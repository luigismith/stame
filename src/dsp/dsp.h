/* dsp.h — il synth di Stame (specifica 20): due motori, Sound e Bass, su un pool di 16 voci.
 *
 * C11 puro, float a 32 bit, niente heap: tutto lo stato sta in dsp_t, che alloca il chiamante
 * (SND-004). Rende a blocchi di 16 frame (SND-002); gli eventi valgono dal blocco successivo
 * (SND-003). Lo chiama un solo thread, quello audio (SND-031).
 */
#ifndef STAME_DSP_H
#define STAME_DSP_H
#include "../core/stame_base.h"
#include "patch.h"
#include "smp.h"

#define DSP_BLOCK    16
#define DSP_VOICES   16
#define DSP_TAILS    16                 /* code: voci rubate (SND-024) e voci di una patch cambiata */
#define DSP_FS_MAX   48000
#define DSP_SCOPE_N  2048               /* SND-033 */
#define DSP_FX_LINE  4096               /* linea modulata di chorus, ensemble, flanger */
#define DSP_DELAY_N  131072             /* potenza di 2 sopra i 2 s a 48 kHz (SND-521) */
#define DSP_REV_LINES 8
#define DSP_REV_N    8192               /* linea del riverbero (potenza di 2), 256 KB in tutto */
#define DSP_REV_AP_N 1024

typedef enum { DSP_SOUND = 0, DSP_BASS = 1 } dsp_engine;
#define DSP_ENGINES 2
#define DSP_LOAD_FXLOCK 0x1u            /* SND-125 */

enum { DSP_V_FREE, DSP_V_HELD, DSP_V_RELEASED };
enum { DSP_ENV_IDLE, DSP_ENV_ATT, DSP_ENV_HOLD, DSP_ENV_DEC, DSP_ENV_REL };

typedef struct { uint8_t stage; float level, t; } dsp_env_t;
typedef struct { float phase, a, b; uint8_t done; } dsp_lfo_t;

/* Reed Piano: tre modi della lamella, due risonatori di clank, rumori (§7) */
typedef struct { float y1, y2, b1, b2, gain; } dsp_res_t;
typedef struct {
    dsp_res_t mode[3], clank[2];
    float t60[3];               /* T60 correnti dei modi */
    float x, xc;                /* impulso del colpo per la lamella (già con A) e per il clank, campione successivo */
    float hammer, keyoff;       /* inviluppi dei rumori */
    float hb1, hb2, hy1, hy2;   /* passa-banda del martelletto */
    float kb1, kb2, ky1, ky2;   /* passa-banda dello smorzatore */
    float hp_amp, kof_amp;
    float tone_z, mel_z;        /* tilt e passa-basso del pickup MELLOW */
    float dc;                   /* blocco della continua del pickup (un polo a 12 Hz) */
    float amp;                  /* A del colpo (SND-351) */
    float silence;              /* blocchi consecutivi sotto −90 dB */
} dsp_rp_voice_t;

/* voce campionata (§7b): zona del banco, posizione intera e frazionaria */
typedef struct {
    const smp_zone_t *z;
    uint32_t idx;
    float    frac;
    uint8_t  ended, looping;
} dsp_smp_voice_t;

typedef struct {
    uint8_t state, engine, note, vel, sustained, legato_env;
    uint32_t age;
    float v, rnd, glide;
    dsp_env_t env[4];
    dsp_lfo_t lfo[4];
    float mod_envt[4], mod_envs[4], mod_lfo[4];   /* modulazioni del blocco precedente (SND-421) */
    float lfo_out[4];
    /* oscillatori e operatori */
    float ph[4], inc[4];
    float og[4], og_t[4];       /* guadagni (VA) o livelli (FM): corrente e obiettivo */
    float duty[4], duty_t[4];   /* larghezza d'impulso (VA) o feedback dell'OP4 (FM): corrente e obiettivo */
    float noise_g, noise_t;
    float fb1, fb2;             /* feedback dell'OP4 */
    float pink[3];
    /* filtro */
    float ic1, ic2, f_a1, f_a2, f_a3, f_k;       /* stato e coefficienti correnti dell'SVF */
    float t_a1, t_a2, t_a3, t_k;                 /* coefficienti obiettivo */
    float hp_lp, hp_a;
    /* ampiezza */
    float gl, gr, gl_t, gr_t;
    float peak;                 /* ampiezza del blocco, per lo stealing */
    float quiet;                /* blocchi sotto −90 dBFS dopo il rilascio */
    dsp_rp_voice_t rp;
    dsp_smp_voice_t smp;
} dsp_voice_t;

/* una coda suona con la copia della patch che aveva: in dissolvenza (step > 0) o fino alla fine del rilascio */
typedef struct { dsp_voice_t v; uint8_t p[DSP_NPAR]; float sm[DSP_NPAR]; float fade, step; uint8_t on; uint32_t age; } dsp_tail_t;

typedef struct {
    uint8_t type, old;          /* tipo corrente e tipo in dissolvenza (SND-507) */
    float xf;                   /* 1 = solo il tipo corrente */
    float line[2][DSP_FX_LINE];
    uint32_t lw;
    float lfo[8];               /* fase dell'LFO di ciascun tipo */
    float lfo2;                 /* secondo LFO dell'ensemble */
    float ap[2][6][2];          /* phaser: 6 all-pass per canale (x1, y1) */
    float pfb[2], ffb[2];
    float drv[2];
} dsp_fx_t;

typedef struct {
    float buf[2][DSP_DELAY_N];
    uint32_t w;
    float t_cur;                /* tempo di lettura in campioni, scorre verso l'obiettivo (SND-521) */
    float lp[2], hp[2];
} dsp_delay_t;

typedef struct {
    uint8_t p[DSP_NPAR];
    float sm[DSP_NPAR];         /* valori smussati (SND-041) */
    float bend, wheel;
    uint8_t sustain, max_voices;
    int16_t last_note;
    uint8_t held[16], n_held;   /* tasti tenuti, per MONO e i modi legato */
    dsp_lfo_t lfo[4];           /* LFO condivisi (FREE, MONO) */
    float lfo_out[4], lfo_mod[4];
    float trem_ph;              /* tremolo dell'oggetto RP */
    dsp_fx_t fx[2];
    dsp_delay_t dly;
} dsp_eng_t;

typedef struct {
    float line[DSP_REV_LINES][DSP_REV_N];
    float ap[2][DSP_REV_AP_N];
    uint32_t w, apw;
    float len[DSP_REV_LINES];   /* lunghezze correnti, scorrono verso l'obiettivo */
    float lp[DSP_REV_LINES];
    float hp_z[2];
    float mod;
    float size, lpr, hpr;       /* raw smussati */
} dsp_reverb_t;

typedef struct dsp {
    float fs, inv_fs;
    float k_sm5, k_sm20;        /* smoothing per blocco a 5 e 20 ms (SND-041) */
    uint32_t rng, age;
    float bpm;
    uint8_t master, bass_vol, vel_sense;
    float g_master, g_bass;
    uint8_t bass_mute;          /* Drop (SND-539): il basso tace, con una rampa di 5 ms */
    float g_bmute, bmute_step;
    dsp_eng_t eng[DSP_ENGINES];
    dsp_voice_t voice[DSP_VOICES];
    dsp_tail_t tail[DSP_TAILS];
    dsp_reverb_t rev;
    int16_t scope[DSP_SCOPE_N];
    volatile uint32_t scope_wr;
    float scope_acc;
    uint8_t scope_n;
    uint32_t steals;            /* diagnostica */
    const smp_bank_t *bank;     /* banco dei campioni del modello SMP (§7b); NULL = nessuno */
} dsp_t;

void dsp_init(dsp_t *d, float fs, uint32_t seed);
void dsp_reseed(dsp_t *d, uint32_t seed);
/* Il banco dei campioni, da dare prima di suonare e da non cambiare mentre si suona (SND-372):
 * le voci tengono puntatori dentro il banco. */
void dsp_set_bank(dsp_t *d, const smp_bank_t *bank);

void dsp_note_on(dsp_t *d, dsp_engine e, uint8_t note, uint8_t vel);
void dsp_note_off(dsp_t *d, dsp_engine e, uint8_t note);
void dsp_chord_start(dsp_t *d, dsp_engine e);
void dsp_pitch_bend(dsp_t *d, dsp_engine e, int16_t v);
void dsp_mod_wheel(dsp_t *d, dsp_engine e, uint8_t v);
void dsp_sustain(dsp_t *d, dsp_engine e, bool on);
void dsp_reset_controllers(dsp_t *d, dsp_engine e);
void dsp_all_notes_off(dsp_t *d);
void dsp_all_sound_off(dsp_t *d);

void dsp_setpar(dsp_t *d, dsp_engine e, uint8_t idx, uint8_t raw);
void dsp_load_patch(dsp_t *d, dsp_engine e, const uint8_t p[DSP_NPAR], uint32_t flags);
void dsp_get_patch(const dsp_t *d, dsp_engine e, uint8_t out[DSP_NPAR]);
void dsp_set_max_voices(dsp_t *d, dsp_engine e, uint8_t n);

void dsp_set_bpm(dsp_t *d, float bpm);
void dsp_set_master_volume(dsp_t *d, uint8_t v);    /* 0…99 */
void dsp_set_bass_volume(dsp_t *d, uint8_t v);      /* 0…99 */
/* Drop (SND-539): il motore Bass tace o torna, con una rampa lineare di 5 ms; le voci continuano */
void dsp_set_bass_mute(dsp_t *d, bool mute);
void dsp_set_velocity_sense(dsp_t *d, bool on);

/* 16 frame; drum_L/drum_R è il bus della batteria, può essere NULL (SND-535) */
void dsp_render16(dsp_t *d, float *L, float *R, const float *drum_L, const float *drum_R);
size_t dsp_scope_read(dsp_t *d, float *dst, size_t max);
int dsp_voices_active(const dsp_t *d);

#endif
