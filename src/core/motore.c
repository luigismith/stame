/* motore.c — clock, performance, Beat e looper nel thread audio (motore.h). */
#include "motore.h"

#define STEP_TICKS 24u          /* 1/16 a 96 PPQN */

static uint64_t spt(uint32_t fs, uint16_t bpm)    /* campioni per tick in 32.32: fs · 60 / (bpm · 96) */
{
    return ((uint64_t)fs * 60u << 32) / ((uint64_t)bpm * 96u);
}

void mot_init(motore_t *m, dsp_t *d, uint32_t fs, uint32_t seed)
{
    memset(m, 0, sizeof *m);
    m->d = d;
    m->fs = fs;
    m->bpm = 120;
    m->spt_fp = spt(fs, 120);
    drums_init(&m->drums, (float)fs, seed ^ 0x5A5Au);
    perf_init(&m->perf, seed);
    loop_init(&m->loop);
    m->beat_sel = BEAT_M_PATTERN;
    m->beat = 1;
    m->meter = METER_4_4;
    memset(m->pre, MOT_NONE, sizeof m->pre);
    memset(m->lp_out, MOT_NONE, sizeof m->lp_out);
}

uint64_t mot_tick_sample(const motore_t *m, uint32_t t)
{
    return (m->spt_fp >> 32) * t + (((m->spt_fp & 0xFFFFFFFFu) * t) >> 32);   /* senza traboccare in 64 bit */
}

uint32_t mot_bar(const motore_t *m) { return m->beat_sel == BEAT_M_PATTERN ? meter_bar(METER_4_4) : meter_bar(m->meter); }
uint32_t mot_click(const motore_t *m) { return m->beat_sel == BEAT_M_PATTERN ? meter_click(METER_4_4) : meter_click(m->meter); }

/* ---------------------------------------------------------------- uscita */

/* ACC-253: una nota già aperta che riceve un altro note-on (dal vivo sopra il loop) prima si spegne e
 * riparte; la voce si spegne solo quando la rilasciano tutte le sorgenti, così il loop non taglia una
 * nota tenuta dal vivo e viceversa */
static void voice_on(motore_t *m, int r, uint8_t note, uint8_t vel)
{
    dsp_engine e = r ? DSP_BASS : DSP_SOUND;
    if (m->ref[r][note]) dsp_note_off(m->d, e, note);
    if (m->ref[r][note] < UINT8_MAX) m->ref[r][note]++;
    dsp_note_on(m->d, e, note, vel);
}

static void voice_off(motore_t *m, int r, uint8_t note)
{
    if (!m->ref[r][note]) return;
    if (--m->ref[r][note] == 0) dsp_note_off(m->d, r ? DSP_BASS : DSP_SOUND, note);
}

/* il looper registra prima del transpose (ACC-220); il note-off segue la nota del suo note-on */
static void record(motore_t *m, uint8_t role, uint8_t note, uint8_t vel)
{
    uint8_t *pre = &m->pre[role][note];
    if (vel) {
        int p = (int)note - m->transpose;
        *pre = p >= 0 && p <= 127 ? (uint8_t)p : MOT_NONE;
        if (*pre != MOT_NONE) loop_record(&m->loop, m->tick, role, *pre, vel);
    } else if (*pre != MOT_NONE) {
        loop_record(&m->loop, m->tick, role, *pre, 0);
        *pre = MOT_NONE;
    }
}

static void treble(motore_t *m, uint8_t note, uint8_t vel)
{
    if (note > 127) return;
    if (vel) voice_on(m, 0, note, vel); else voice_off(m, 0, note);
    record(m, LOOP_TREBLE, note, vel);
}

static void apply_perf(motore_t *m, const perf_ev_t *ev, int n)
{
    for (int i = 0; i < n; i++) treble(m, ev[i].note, ev[i].on ? ev[i].vel : 0);
}

/* il loop suona con il transpose corrente (ACC-221); il note-off spegne la nota che è partita */
static void apply_loop(motore_t *m, const loop_ev_t *ev, int n)
{
    for (int i = 0; i < n; i++) {
        if (ev[i].role == LOOP_DRUM) {                            /* colpo registrato: il kit, senza transpose */
            if (ev[i].vel) drums_hit(&m->drums, ev[i].note, ev[i].vel);
            continue;
        }
        uint8_t r = ev[i].role == LOOP_BASS ? 1 : 0, src = ev[i].note & 127u;
        if (ev[i].vel) {
            int note = (int)src + m->transpose;
            if (note < 0 || note > 127) { m->lp_out[r][src] = MOT_NONE; continue; }
            m->lp_out[r][src] = (uint8_t)note;
            voice_on(m, r, (uint8_t)note, ev[i].vel);
        } else if (m->lp_out[r][src] != MOT_NONE) {
            voice_off(m, r, m->lp_out[r][src]);
            m->lp_out[r][src] = MOT_NONE;
        }
    }
}

/* ---------------------------------------------------------------- trasporto */

static bool loop_moving(const looper_t *l)
{
    return l->state == LOOP_COUNT_IN || l->state == LOOP_REC || l->state == LOOP_PLAY || l->state == LOOP_OVERDUB;
}

/* in moto se suona il Beat o lavora il looper; si mette in moto da battuta 1 (ACC-204) */
static void transport(motore_t *m, bool restart)
{
    bool on = m->beat_on || loop_moving(&m->loop);
    if (on && (!m->tr_on || restart)) m->tr_t0 = m->tick;
    m->tr_on = on;
}

/* ---------------------------------------------------------------- ingressi */

static bool held_any(const motore_t *m)
{
    for (int i = 0; i < 16; i++) if (m->held[i]) return true;
    return false;
}

void mot_drum(motore_t *m, uint8_t k, uint8_t vel)
{
    if (k >= DRUM_COUNT || vel == 0) return;
    drums_hit(&m->drums, k, vel);
    /* il sedicesimo più vicino sulla griglia del loop, che parte da t0 e non dal tick 0: sul tick
     * assoluto ogni colpo finiva spostato di t0 mod 24 (fino a 60 ms a 120 BPM) */
    int32_t x = (int32_t)(m->tick - m->loop.t0) + (int32_t)(STEP_TICKS / 2u);
    int32_t f = x >= 0 ? x / (int32_t)STEP_TICKS : -((-x + (int32_t)STEP_TICKS - 1) / (int32_t)STEP_TICKS);
    loop_record_hit(&m->loop, m->loop.t0 + (uint32_t)(f * (int32_t)STEP_TICKS), m->tick, k, vel);
}

void mot_note(motore_t *m, int engine, uint8_t note, uint8_t vel)
{
    if (note > 127) return;
    if (engine == 1) {                                            /* il basso non passa dalla performance (ACC-142) */
        if (vel) voice_on(m, 1, note, vel); else voice_off(m, 1, note);
        record(m, LOOP_BASS, note, vel);
        return;
    }
    uint8_t bit = (uint8_t)(1u << (note & 7));
    if (vel) { m->held[note >> 3] |= bit; m->held_vel = vel; }
    else {
        m->held[note >> 3] &= (uint8_t)~bit;
        m->removed = 1;
        if (!held_any(m)) m->went_empty = 1;
    }
    m->dirty = 1;
}

void mot_chord_start(motore_t *m)
{
    m->key_down = 1;
    m->legato = held_any(m) && !m->went_empty;                    /* nuovo tasto senza rilasciare (ACC-173) */
    m->dirty = 1;
    dsp_chord_start(m->d, DSP_SOUND);
}

/* il gruppo di note arrivato fra due blocchi diventa un gesto della performance */
static void commit(motore_t *m)
{
    perf_ev_t ev[48];
    if (!held_any(m)) {
        /* nessuna nota treble (per esempio un tasto che suona solo il basso): il KEY_DOWN resta in
         * attesa delle note del gesto, così il modo e il passo 0 valgono quando arrivano (ACC-173, ACC-182) */
        apply_perf(m, ev, perf_release(&m->perf, m->tick, ev, 48));
        m->dirty = m->legato = m->went_empty = m->removed = 0;
        return;
    }
    uint8_t notes[8], k = 0;
    for (int i = 0; i < 128 && k < 8; i++) if (m->held[i >> 3] >> (i & 7) & 1u) notes[k++] = (uint8_t)i;
    /* ADD_NOTE (ACC-180): solo note nuove sopra la voicing in corso, senza KEY_DOWN né spegnimenti.
     * Prima passava per perf_chord come un ri-attacco e lo strum ripartiva da capo a ogni estensione */
    bool add = !m->key_down && !m->removed && m->perf.n > 0 && k > m->perf.n;
    for (int j = 0; add && j < m->perf.n; j++) {
        bool found = false;
        for (int i = 0; i < k; i++) if (notes[i] == m->perf.notes[j]) found = true;
        if (!found) add = false;
    }
    if (add) apply_perf(m, ev, perf_add(&m->perf, m->tick, notes, k, ev, 48));
    else apply_perf(m, ev, perf_chord(&m->perf, m->tick, notes, k, m->held_vel, m->key_down, m->legato, ev, 48));
    m->dirty = m->key_down = m->legato = m->went_empty = m->removed = 0;
}

void mot_bpm(motore_t *m, uint16_t bpm)
{
    if (bpm < 60) bpm = 60;
    if (bpm > 200) bpm = 200;
    m->bpm = bpm;
    m->spt_fp = spt(m->fs, bpm);                                  /* dal tick successivo (ACC-202) */
    dsp_set_bpm(m->d, (float)bpm);
}

void mot_perf(motore_t *m, uint8_t mode, uint8_t amount)
{
    perf_set(&m->perf, amount ? mode : PM_OFF, amount);
}

/* il kit del Beat scelto (SND-537): il set del banco con quel nome, o la sintesi se manca */
static void apply_kit(motore_t *m)
{
    const char *kit = beat_kit(m->beat);
    drums_set_kit(&m->drums, m->bank, kit ? smp_set_find(m->bank, kit) : NULL);
}

void mot_set_bank(motore_t *m, const smp_bank_t *bank)
{
    m->bank = bank;
    dsp_set_bank(m->d, bank);
    apply_kit(m);
}

void mot_beat(motore_t *m, uint8_t mode, uint8_t beat)
{
    m->beat_sel = mode == BEAT_M_METRONOME ? BEAT_M_METRONOME : BEAT_M_PATTERN;
    m->beat = beat < BEAT_COUNT ? beat : 1;
    apply_kit(m);
}

void mot_meter(motore_t *m, uint8_t meter)
{
    if (meter <= METER_6_8) m->meter = meter;
}

void mot_beat_on(motore_t *m, bool on)
{
    m->beat_on = on;                    /* col looper in moto è solo un mute: la battuta 1 resta (ACC-205) */
    transport(m, false);
}

void mot_beat_volume(motore_t *m, uint8_t v) { drums_volume(&m->drums, v); }
void mot_transpose(motore_t *m, int8_t t) { m->transpose = t; }

void mot_loop(motore_t *m, int cmd)
{
    uint8_t was = m->loop.state;
    if (was == LOOP_IDLE) loop_set_len(&m->loop, mot_bar(m), m->loop.bars);
    loop_ev_t ev[LOOP_OUT_MAX];
    apply_loop(m, ev, loop_cmd(&m->loop, cmd, m->tick, ev, LOOP_OUT_MAX));
    uint8_t st = m->loop.state;
    /* registrazione nuova o ripresa dalla pausa: il trasporto riparte con il loop (ACC-222) */
    transport(m, st != was && (st == LOOP_COUNT_IN || (was == LOOP_PAUSE && st == LOOP_PLAY)));
}

void mot_all_off(motore_t *m)
{
    perf_ev_t ev[48];
    apply_perf(m, ev, perf_release(&m->perf, m->tick, ev, 48));
    memset(m->held, 0, sizeof m->held);
    dsp_all_notes_off(m->d);
    drums_all_off(&m->drums);
    memset(m->lp_out, MOT_NONE, sizeof m->lp_out);
    memset(m->ref, 0, sizeof m->ref);
}

/* ---------------------------------------------------------------- tempo */

static void tick_run(motore_t *m)
{
    perf_ev_t pe[48];
    apply_perf(m, pe, perf_run(&m->perf, m->tick, pe, 48));
    loop_ev_t le[LOOP_OUT_MAX];
    apply_loop(m, le, loop_run(&m->loop, m->tick, le, LOOP_OUT_MAX));
    if (!m->tr_on) return;
    uint32_t pos = m->tick - m->tr_t0;
    beat_hit_t h[8];
    int n = 0;
    if (m->beat_on && m->beat_sel == BEAT_M_PATTERN && pos % STEP_TICKS == 0)
        n = beat_hits(m->beat, (int)((pos / STEP_TICKS) % 16u), h, 6);
    /* il metronomo, e il count-in del looper con qualunque Beat (ACC-223) */
    if ((m->beat_on && m->beat_sel == BEAT_M_METRONOME) || m->loop.state == LOOP_COUNT_IN)
        n += metro_hits(m->beat_sel == BEAT_M_PATTERN ? METER_4_4 : m->meter, pos, h + n, 8 - n);
    for (int i = 0; i < n; i++) drums_hit(&m->drums, h[i].inst, h[i].vel);
}

bool mot_due(const motore_t *m, uint32_t at)
{
    int32_t d = (int32_t)(at - m->tick);
    return d < 0 || (d == 0 && (m->next_fp >> 32) < 16u);
}

void mot_render(motore_t *m, float *L, float *R, uint32_t n)
{
    if (m->dirty) commit(m);
    for (uint32_t i = 0; i + 16 <= n; i += 16) {
        while ((m->next_fp >> 32) < 16u) {                        /* i tick che cadono in questo blocco */
            tick_run(m);
            m->tick++;
            m->next_fp += m->spt_fp;
        }
        float dl[16] = { 0 }, dr[16] = { 0 };
        drums_render16(&m->drums, dl, dr);
        dsp_render16(m->d, L + i, R + i, dl, dr);
        m->s += 16;
        m->next_fp -= (uint64_t)16u << 32;                        /* il blocco dopo: next_fp resta relativo */
    }
    uint32_t sq = atomic_load_explicit(&m->snap.seq, memory_order_relaxed);
    atomic_store_explicit(&m->snap.seq, sq + 1u, memory_order_relaxed);     /* dispari: si scrive */
    atomic_thread_fence(memory_order_seq_cst);
    m->snap.tick = m->tick;
    m->snap.tr_t0 = m->tr_t0;
    m->snap.tr_on = m->tr_on;
    m->snap.bpm = m->bpm;
    m->snap.lp_state = m->loop.state;
    m->snap.lp_t0 = m->loop.t0;
    m->snap.lp_len = m->loop.len;
    m->snap.lp_layers = m->loop.layers;
    m->snap.lp_full = m->loop.full;
    uint8_t bits[2][16];
    memset(bits, 0, sizeof bits);
    for (int r = 0; r < 2; r++)
        for (int i = 0; i < 128; i++) {
            uint8_t o = m->lp_out[r][i];
            if (o != MOT_NONE) bits[r][o >> 3] |= (uint8_t)(1u << (o & 7));
        }
    for (int r = 0; r < 2; r++)
        for (int i = 0; i < 16; i++) m->snap.lp_notes[r][i] = bits[r][i];
    atomic_store_explicit(&m->snap.seq, sq + 2u, memory_order_release);     /* pari: pubblicato */
}

void mot_snap_read(const mot_snap_t *src, mot_snap_t *dst)
{
    const size_t off = offsetof(mot_snap_t, tick), len = sizeof *src - off;
    for (int k = 0; k < 3; k++) {
        uint32_t s0 = atomic_load_explicit(&src->seq, memory_order_acquire);
        if (s0 & 1u) continue;
        memcpy((uint8_t *)dst + off, (const uint8_t *)src + off, len);
        atomic_thread_fence(memory_order_acquire);
        if (atomic_load_explicit(&src->seq, memory_order_relaxed) == s0) return;
    }
    memcpy((uint8_t *)dst + off, (const uint8_t *)src + off, len);        /* scrive di continuo: l'ultima */
}
