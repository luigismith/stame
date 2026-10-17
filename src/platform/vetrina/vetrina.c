/* vetrina.c — pilota dimostrativo della plancia (vetrina.h). Codice di piattaforma: niente veleni. */
#include "vetrina.h"
#include "demo.h"
#include "../../ui/ui_fmt.h"
#include "../../core/kv.h"
#include <math.h>
#include <string.h>

#define BOOT_MS      2600u
#define OVERLAY_MS   3400u        /* UI-069 */
#define LINGER_MS    2000u
#define DEMO_IDLE_MS 20000u
#define LIST_IDLE_MS 10000u       /* UI-076 */
#define PAGE_MS      5000u        /* UI-142a: la pagina dei comandi si chiude da sola */

/* ---- dati della vetrina (nessun preset dell'Orchid): suoni e bassi in patch_vetrina.c (tools/patch.py) ---- */
#define SOUNDS vet_sound_info
#define BASSES vet_bass_name
/* i Beat della vetrina sono quelli di core/beat.c dall'indice 1 (lo 0 è il provvisorio di ACC-210) */
#define BEATS_NAME(i) beat_name((i) + 1)

#define N_SOUNDS ((int)STAME_COUNT(SOUNDS))
#define N_BASSES ((int)STAME_COUNT(BASSES))
#define N_BEATS  (BEAT_COUNT - 1)

/* stato dei controlli. perf_amount è l'amount di ACC-160: 1…6 per Arpeggiate (tipo di ACC-171),
 * 1…13 per Pattern, 1…10 per gli altri modi; 0 = spento. beat_mode è la selezione del menu dei Beat
 * (metronomo con la metrica, o un Beat), beat_on dice se suona (TRANSPORT_TOGGLE, ACC-205). */
typedef struct {
    int sound, perf_mode, perf_amount, fx_type, fx_amount, bass, volume, bass_volume;
    int bpm, beat_mode, beat, meter, beat_on, beat_volume, view;
    uint8_t lock_perf, lock_fx, sec[ENC_COUNT];
    uint8_t drums;                      /* batteria a tastiera (ACC-211): i tasti colpiscono il kit */
    uint8_t hold, metro, fill;          /* Hold dell'accordo, metronomo, Fill del Beat (MIDI-133) */
    uint16_t hold_keys;                 /* tasti il cui rilascio aspetta (Hold) */
    uint8_t hold_chords;                /* tasti accordo idem */
    uint32_t tap_ms[4];                 /* ultimi tocchi del tap tempo */
    uint8_t tap_n;
    uint8_t scene_keep;                 /* una scena ha appena messo suono, Perform ed effetto: snd_sync non li rimette */
    int kit, roll, accent;              /* drum machine (MIDI-135): kit 0 = del Beat, Roll 0…6, Accent 0…10 */
    uint8_t knob_lock;                  /* Lock delle manopole del macro pad (MIDI-131), per la testata */
    uint32_t drum_ms[12];               /* ultimo colpo di ogni tasto, per accendere il tasto sulla plancia */
} sim_t;
static sim_t S;                    /* una vetrina sola per processo */

static void drums_toggle(vet_t *v);             /* definita con gli ingressi, più sotto */

static int wrap(int v, int n) { v %= n; return v < 0 ? v + n : v; }
static int clampi(int v, int a, int b) { return v < a ? a : v > b ? b : v; }
static float clampf(float v, float a, float b) { return v < a ? a : v > b ? b : v; }

static void snd_push(vet_t *v, uint8_t type, uint8_t engine, uint8_t a, uint8_t b)
{
    if ((uint16_t)(v->snd_w - v->snd_r) >= VET_SND_Q) return;       /* coda piena: si scarta */
    vet_snd_t *e = &v->snd_q[v->snd_w % VET_SND_Q];
    e->type = type; e->engine = engine; e->a = a; e->b = b;
    e->timed = v->snd_timed;                                         /* la demo: vale dal tick snd_at */
    e->at = v->snd_at;
    v->snd_w++;
}

bool vet_snd_pop(vet_t *v, vet_snd_t *out)
{
    if (v->snd_r == v->snd_w) return false;
    *out = v->snd_q[v->snd_r % VET_SND_Q];
    v->snd_r++;
    return true;
}

bool vet_snd_peek(const vet_t *v, vet_snd_t *out)
{
    if (v->snd_r == v->snd_w) return false;
    *out = v->snd_q[v->snd_r % VET_SND_Q];
    return true;
}

void vet_set_scope(vet_t *v, const int16_t *buf, uint16_t len, const volatile uint32_t *wr,
                   const volatile float *peak)
{
    v->ext_scope = buf;
    v->ext_scope_len = len;
    v->ext_scope_wr = wr;
    v->ext_peak = peak;
}

void vet_set_motore(vet_t *v, const mot_snap_t *snap)
{
    v->snap_src = snap;
    v->snap = snap ? &v->snap_copy : NULL;
    if (snap) mot_snap_read(snap, &v->snap_copy);
}

void vet_set_audio_stats(vet_t *v, const vet_audio_stats_t *stats) { v->stats = stats; }

static uint8_t lp_state(const vet_t *v) { return v->snap ? v->snap->lp_state : (uint8_t)LP_IDLE; }
static int count_in_left(const vet_t *v);
static void demo_start(vet_t *v);

/* motore degli accordi: le note TREBLE vanno al Sound, le BASS al Bass (specifica 20, §9) */
static void ain(vet_t *v, uint8_t type, uint8_t a, int16_t b)
{
    int n = acc_input(&v->acc, type, a, b, 0, v->ev, (int)STAME_COUNT(v->ev));
    /* il transpose arriva al motore prima delle note che lo usano: il looper registra senza (ACC-220) */
    if (v->acc.transpose != v->snd_tr) {
        snd_push(v, VS_TRANSPOSE, 0, (uint8_t)(int8_t)v->acc.transpose, 0);
        v->snd_tr = v->acc.transpose;
    }
    if (type == ACC_IN_KEY_DOWN) snd_push(v, VS_CHORD_START, 0, 0, 0);
    for (int i = 0; i < n; i++) {
        const acc_note_ev *e = &v->ev[i];
        if (e->role != ACC_ROLE_TREBLE && e->role != ACC_ROLE_BASS) continue;
        uint8_t eng = e->role == ACC_ROLE_BASS ? 1 : 0;
        if (e->on && e->vel) snd_push(v, VS_NOTE_ON, eng, e->note, e->vel);
        else snd_push(v, VS_NOTE_OFF, eng, e->note, 0);
    }
}

static void overlay(vet_t *v, uint8_t kind, uint8_t enc, int value)
{
    v->m.layer.ov.kind = kind;
    v->m.layer.ov.enc = enc;
    v->m.layer.ov.value = (int16_t)value;
    v->ov_until = v->now_ms + OVERLAY_MS;
    v->m.layer.ov.until_ms = v->ov_until;
}

/* l'overlay è solo un'evidenza: la manopola del fuoco resta al fuoco (MIDI-104, 16/10/2026) */
static void ov_hide(vet_t *v)
{
    v->m.layer.ov.kind = OV_NONE;
}

static void msg(vet_t *v, uint8_t level, const char *text, uint32_t ms)
{
    ui_msg_t *mm = &v->m.msg_plat;
    mm->level = level;
    mm->until_ms = v->now_ms + ms;
    ui_fmt_copy(mm->text, sizeof mm->text, text);
}

/* ---- Perform: amount di ACC-160 ---- */
static int perf_max(int mode)
{
    return mode == PERF_ARP || mode == PERF_ARP2 ? 6 : mode == PERF_PATTERN ? 13 : mode ? 10 : 0;
}

static bool perf_arp(void) { return S.perf_mode == PERF_ARP || S.perf_mode == PERF_ARP2; }

/* ---- liste ---- */
enum { L_NONE, L_SOUND, L_PERFORM, L_OPTIONS, L_PLATFORM, L_BEATS };

/* lista dei Beat (UI-077): Exit, le quattro metriche del metronomo, poi i Beat */
#define BEAT_ITEMS (5 + N_BEATS)

static int list_n(int kind)
{
    switch (kind) {
    case L_SOUND: return N_SOUNDS;
    case L_PERFORM: return PERF_COUNT;
    case L_OPTIONS: return 5;
    case L_PLATFORM: return 11;
    case L_BEATS: return BEAT_ITEMS;
    default: return 0;
    }
}

static int beat_item(void) { return S.beat_mode == BEAT_PATTERN ? 5 + S.beat : 1 + S.meter; }

static void list_item(const vet_t *v, int kind, int i, ui_item_t *it)
{
    memset(it, 0, sizeof *it);
    it->enabled = 1;
    switch (kind) {
    case L_SOUND:
        ui_fmt_int(it->num, sizeof it->num, i + 1, 2);
        ui_fmt_copy(it->label, sizeof it->label, SOUNDS[i].name);
        ui_fmt_cat(it->info, sizeof it->info, ui_fmt_engine(SOUNDS[i].engine), "  ");
        ui_fmt_cat(it->info, sizeof it->info, it->info, SOUNDS[i].cat);
        if (i == S.sound) it->mark = MK_CHECK;
        break;
    case L_PERFORM:
        /* «Exit» in cima come in ogni lista (UI-073, UI-077): spegnere si fa con la manopola, amount 0
         * (ACC-160). Prima la voce 0 era «Off» */
        ui_fmt_copy(it->label, sizeof it->label, i == 0 ? "Exit" : ui_fmt_perf_long((uint8_t)i));
        if (i && i == S.perf_mode) it->mark = MK_DOT;
        break;
    case L_OPTIONS: {
        static const char *const L[] = { "Exit", "View", "Play Style", "Single Notes", "Secret Chords" };
        ui_fmt_copy(it->label, sizeof it->label, L[i]);
        if (i == 1) ui_fmt_copy(it->value, sizeof it->value, ui_fmt_view_short((uint8_t)S.view));
        if (i == 2) ui_fmt_copy(it->value, sizeof it->value, ui_fmt_play_style(v->acc.style));
        if (i == 3) ui_fmt_copy(it->value, sizeof it->value, v->acc.single_notes ? "Octave" : "Split");
        if (i == 4) ui_fmt_copy(it->value, sizeof it->value, v->acc.secret ? "On" : "Off");
        break;
    }
    case L_BEATS: {
        static const char *const M[] = { "Exit", "2/4", "3/4", "4/4", "6/8" };
        if (i < 5) ui_fmt_copy(it->label, sizeof it->label, M[i]);
        else {
            ui_fmt_int(it->num, sizeof it->num, i - 4, 2);
            ui_fmt_copy(it->label, sizeof it->label, BEATS_NAME(i - 5));
        }
        if (i && i == beat_item()) it->mark = MK_CHECK;
        break;
    }
    case L_PLATFORM: {
        /* Panic al secondo posto (UI-129: MENU, giù, A); Metronome e Save Loop (MIDI-137): senza il pad
         * i suoi T3 e T10 stanno qui, e senza MK4 né pad il Panic ha solo questa casa */
        static const char *const L[] = { "Exit", "Panic", "Metronome", "Save Loop", "Theme", "Linnaeus Tag",
                                         "Legend", "Meters", "Demo", "Play Demo Song", "Quit Stame" };
        ui_fmt_copy(it->label, sizeof it->label, L[i]);
        if (i == 2) ui_fmt_copy(it->value, sizeof it->value, S.metro ? "On" : "Off");
        if (i == 4) ui_fmt_copy(it->value, sizeof it->value, v->m.prefs.theme ? "Light" : "Dark");
        if (i == 5) ui_fmt_copy(it->value, sizeof it->value, v->m.prefs.linnaeus ? "On" : "Off");
        if (i == 6) ui_fmt_copy(it->value, sizeof it->value, v->m.prefs.legend ? "On" : "Off");
        if (i == 7) ui_fmt_copy(it->value, sizeof it->value, v->m.prefs.meters ? "On" : "Off");
        if (i == 8) ui_fmt_copy(it->value, sizeof it->value, v->demo_on ? "Auto" : "Off");
        break;
    }
    default: break;
    }
}

static void list_open(vet_t *v, int kind, uint8_t owner)
{
    v->list_kind = (uint8_t)kind;
    v->list_owner = owner;
    v->list_ms = v->now_ms;
    v->m.layer.ov.kind = OV_NONE;
    switch (kind) {
    case L_SOUND: v->list_sel = (uint16_t)S.sound; break;
    case L_PERFORM: v->list_sel = (uint16_t)S.perf_mode; break;
    case L_BEATS: v->list_sel = (uint16_t)beat_item(); break;
    default: v->list_sel = 0; break;
    }
    gest_set_owner(&v->inp.gest, owner);
}

static void list_close(vet_t *v)
{
    v->list_kind = L_NONE;
    gest_set_owner(&v->inp.gest, ENC_COUNT);
}

static void list_select(vet_t *v)
{
    int i = v->list_sel;
    v->list_ms = v->now_ms;
    switch (v->list_kind) {
    case L_SOUND: S.sound = i; break;
    case L_PERFORM:
        if (i == 0) { list_close(v); break; }
        S.perf_mode = i;
        if (S.perf_amount == 0) S.perf_amount = perf_arp() ? 6 : S.perf_mode == PERF_PATTERN ? 1 : 5;
        S.perf_amount = clampi(S.perf_amount, 0, perf_max(S.perf_mode));
        break;
    case L_BEATS:
        if (i == 0) list_close(v);
        else if (i < 5) { S.beat_mode = BEAT_METRONOME; S.meter = i - 1; }
        else { S.beat_mode = BEAT_PATTERN; S.beat = i - 5; }
        break;
    case L_OPTIONS:
        if (i == 0) list_close(v);
        else if (i == 1) S.view = wrap(S.view + 1, VIEW_COUNT);
        else if (i == 2) ain(v, ACC_IN_OPTION_SET, ACC_OPT_PLAY_STYLE, (int16_t)wrap(v->acc.style + 1, 3));
        else if (i == 3) ain(v, ACC_IN_SINGLE_NOTES_TOGGLE, 0, 0);
        else if (i == 4) ain(v, ACC_IN_OPTION_SET, ACC_OPT_SECRET, v->acc.secret ? ACC_SECRET_OFF : ACC_SECRET_ALL);
        break;
    case L_PLATFORM:
        if (i == 0) list_close(v);
        else if (i == 1) {                              /* come T12 e SHIFT + STOP/PLAY */
            msg(v, MSG_INFO, "Panic: all notes off", 2000);
            snd_push(v, VS_ALL_OFF, 0, 0, 0);
            list_close(v);
        }
        else if (i == 2) { S.metro = (uint8_t)!S.metro; snd_push(v, VS_METRO, 0, S.metro, 0); }
        else if (i == 3) { snd_push(v, VS_LOOP, 0, (uint8_t)LOOP_C_EXIT, 0); list_close(v); }   /* come T10 */
        else if (i == 4) v->m.prefs.theme = (uint8_t)!v->m.prefs.theme;
        else if (i == 5) v->m.prefs.linnaeus = (uint8_t)!v->m.prefs.linnaeus;
        else if (i == 6) v->m.prefs.legend = (uint8_t)!v->m.prefs.legend;
        else if (i == 7) v->m.prefs.meters = (uint8_t)!v->m.prefs.meters;
        else if (i == 8) v->demo_on = (uint8_t)!v->demo_on;
        else if (i == 9) {                              /* il brano successivo, subito */
            if (v->demo_running) v->demo_song = (uint8_t)((v->demo_song + 1) % vet_demo_songs_n);
            demo_start(v);
        }
        else if (i == 10) v->quit = 1;
        break;
    default: break;
    }
}

/* ---- looper: comandi al motore e menu a tre voci (UI-088) ---- */
static void loop_send(vet_t *v, int cmd) { snd_push(v, VS_LOOP, 0, (uint8_t)cmd, 0); }

static void loop_menu(const vet_t *v, uint8_t *out)
{
    static const uint8_t M[5][3] = {
        { LPI_REC, LPI_PLAY, LPI_BACK },          /* count-in e registrazione */
        { LPI_OVERDUB, LPI_PAUSE, LPI_CLEAR },    /* riproduzione con il solo strato 0 */
        { LPI_OVERDUB, LPI_PAUSE, LPI_UNDO },     /* riproduzione dopo un overdub */
        { LPI_STOP, LPI_PLAY, LPI_CLEAR },        /* overdub */
        { LPI_OVERDUB, LPI_PLAY, LPI_CLEAR },     /* pausa */
    };
    uint8_t st = lp_state(v), layers = v->snap ? v->snap->lp_layers : 0;
    int k = st == LP_PLAY ? (layers > 1 ? 2 : 1) : st == LP_OVERDUB ? 3 : st == LP_PAUSE ? 4 : 0;
    memcpy(out, M[k], 3);
}

static void looper_item(vet_t *v, uint8_t item)
{
    uint8_t st = lp_state(v);
    switch (item) {
    case LPI_REC: if (st == LP_IDLE) loop_send(v, LOOP_C_PRESS); break;
    case LPI_PLAY: if (st == LP_REC || st == LP_OVERDUB || st == LP_PAUSE) loop_send(v, LOOP_C_STOP); break;
    case LPI_OVERDUB:
        if (st == LP_PAUSE) loop_send(v, LOOP_C_STOP);           /* riparte e registra sopra */
        loop_send(v, LOOP_C_OVERDUB);
        break;
    case LPI_PAUSE: if (st == LP_PLAY) loop_send(v, LOOP_C_STOP); break;
    case LPI_STOP: if (st == LP_OVERDUB) loop_send(v, LOOP_C_STOP); break;
    case LPI_UNDO: loop_send(v, LOOP_C_UNDO); break;
    case LPI_CLEAR: loop_send(v, LOOP_C_CLEAR); break;
    case LPI_BACK: gest_set_owner(&v->inp.gest, ENC_COUNT); break;
    default: break;
    }
}

/* premere Loop: da fermo parte il count-in, poi esegue la voce selezionata del menu */
static void looper_press(vet_t *v)
{
    if (lp_state(v) == LP_IDLE) { loop_send(v, LOOP_C_PRESS); return; }
    uint8_t menu[3];
    loop_menu(v, menu);
    looper_item(v, menu[v->m.looper.menu_sel % 3]);
}

static void looper_stop(vet_t *v) { loop_send(v, LOOP_C_STOP); }

/* drum machine (MIDI-135): suddivisioni del Roll in tick e velocity con l'Accent (0 = colpi uguali, 10 = com'è) */
static const uint8_t ROLL_TICKS[7] = { 0, 96, 48, 32, 24, 16, 12 };

/* ---- gesti ---- */
static void turn(vet_t *v, int enc, int d, bool pressed)
{
    if (v->list_kind) {
        if (enc == v->list_owner) {
            v->list_sel = (uint16_t)clampi((int)v->list_sel + d, 0, list_n(v->list_kind) - 1);
            v->list_ms = v->now_ms;
            return;
        }
        list_close(v);
    }
    if (S.drums && !pressed) {                          /* drum machine (MIDI-135): kit, Roll e Accent sotto DRUMS */
        if (enc == ENC_SOUND) {
            S.kit = wrap(S.kit + d, KIT_COUNT + 1);
            snd_push(v, VS_KIT, 0, (uint8_t)S.kit, 0);
            overlay(v, OV_KIT, ENC_SOUND, S.kit);
            return;
        }
        if (enc == ENC_PERFORM) {
            S.roll = clampi(S.roll + d, 0, 6);
            snd_push(v, VS_ROLL, 0, ROLL_TICKS[S.roll], 0);
            overlay(v, OV_ROLL, ENC_PERFORM, S.roll);
            return;
        }
        if (enc == ENC_BASS) {
            S.accent = clampi(S.accent + d, 0, 10);
            overlay(v, OV_ACCENT, ENC_BASS, S.accent);
            return;
        }
    }
    switch (enc) {
    case ENC_SOUND:
        S.sound = wrap(S.sound + d, N_SOUNDS);
        overlay(v, OV_SOUND, ENC_SOUND, S.sound + 1);
        break;
    case ENC_PERFORM:                                   /* amount del modo: per Arpeggiate il tipo (ACC-171) */
        S.perf_amount = clampi(S.perf_amount + d, 0, perf_max(S.perf_mode));
        overlay(v, perf_arp() && S.perf_amount ? OV_ARP : OV_PERFORM, ENC_PERFORM, S.perf_amount);
        break;
    case ENC_FX:
        S.fx_amount = clampi(S.fx_amount + d, 0, 10);
        overlay(v, OV_FX, ENC_FX, S.fx_amount);
        break;
    case ENC_KEY:
        if (pressed) {
            ain(v, ACC_IN_TRANSPOSE_STEP, 0, (int16_t)d);
            S.sec[ENC_KEY] = 1;
            overlay(v, OV_TRANSPOSE, ENC_KEY, v->acc.transpose);
        } else {
            ain(v, ACC_IN_KEY_SELECT, (uint8_t)wrap(v->acc.key_index + d, ACC_KEY_COUNT), 0);
            if (!v->acc.key_on) ain(v, ACC_IN_KEY_MODE_TOGGLE, 0, 0);
            overlay(v, OV_KEY, ENC_KEY, v->acc.key_index);
        }
        break;
    case ENC_BASS:
        S.bass = wrap(S.bass + d, N_BASSES);
        overlay(v, OV_BASS_SOUND, ENC_BASS, S.bass + 1);
        break;
    case ENC_LOOP:
        if (lp_state(v) != LP_IDLE) v->m.looper.menu_sel = (uint8_t)clampi(v->m.looper.menu_sel + d, 0, 2);
        break;
    case ENC_BPM:
        if (pressed) {
            S.beat_volume = clampi(S.beat_volume + d, 0, 99);
            S.sec[ENC_BPM] = 1;
            overlay(v, OV_BEAT_VOLUME, ENC_BPM, S.beat_volume);
        } else {
            S.bpm = clampi(S.bpm + d, 60, 200);
            overlay(v, OV_BPM, ENC_BPM, S.bpm);
        }
        break;
    case ENC_VOLUME:
        if (pressed) {
            S.bass_volume = clampi(S.bass_volume + d, 0, 99);
            S.sec[ENC_VOLUME] = 1;
            overlay(v, OV_BASS_VOLUME, ENC_VOLUME, S.bass_volume);
        } else {
            S.volume = clampi(S.volume + d, 0, 99);
            overlay(v, OV_VOLUME, ENC_VOLUME, S.volume);
        }
        break;
    case ENC_OPTIONS:
        S.view = wrap(S.view + d, VIEW_COUNT);
        break;
    case ENC_CHORD_VOICING:
        ain(v, ACC_IN_VOICING_STEP, 0, (int16_t)d);
        overlay(v, OV_VOICING, ENC_CHORD_VOICING, v->acc.v);
        break;
    case ENC_BASS_VOICING:
        ain(v, ACC_IN_BASS_VOICING_STEP, 0, (int16_t)d);
        overlay(v, OV_BASS_VOICING, ENC_BASS_VOICING, v->acc.vb);
        break;
    default: break;
    }
}

static void press(vet_t *v, int enc)
{
    if (v->list_kind) {
        if (enc == v->list_owner) { list_select(v); return; }
        list_close(v);
    }
    switch (enc) {
    case ENC_SOUND: list_open(v, L_SOUND, ENC_SOUND); break;
    case ENC_PERFORM: list_open(v, L_PERFORM, ENC_PERFORM); break;
    case ENC_FX: overlay(v, OV_FX, ENC_FX, S.fx_amount); break;
    case ENC_KEY:
        ain(v, ACC_IN_KEY_MODE_TOGGLE, 0, 0);
        overlay(v, OV_KEY_TOGGLE, ENC_KEY, v->acc.key_on);
        break;
    case ENC_BASS:
        ain(v, ACC_IN_BASS_TOGGLE, 0, 0);
        overlay(v, OV_BASS_TOGGLE, ENC_BASS, v->acc.bass_on);
        break;
    case ENC_LOOP:
        if (gest_held(&v->inp.gest, ENC_BASS_VOICING)) loop_send(v, LOOP_C_RESET);   /* Mod + Loop: uscita forzata (ACC-222), anche in overdub */
        else looper_press(v);
        break;
    case ENC_BPM:
        if (gest_held(&v->inp.gest, ENC_BASS_VOICING)) drums_toggle(v);   /* Mod + BPM: DRUMS_TOGGLE (ACC-211) */
        else S.beat_on = !S.beat_on;                                     /* TRANSPORT_TOGGLE (ACC-205) */
        break;
    case ENC_VOLUME: overlay(v, OV_BATTERY, ENC_VOLUME, 0); break;
    case ENC_OPTIONS: list_open(v, L_OPTIONS, ENC_OPTIONS); break;
    case ENC_CHORD_VOICING:
        ain(v, ACC_IN_SINGLE_NOTES_TOGGLE, 0, 0);
        overlay(v, OV_SINGLE_NOTES, ENC_CHORD_VOICING, v->acc.single_notes);
        break;
    default: break;
    }
}

static void demo_release(vet_t *v);                 /* definita con la demo, più sotto */

/* batteria a tastiera (ACC-211): i 12 tasti colpiscono gli strumenti del kit del Beat (ACC-212) e
 * i colpi entrano nel loop quantizzati; tipi, estensioni, basso e performance restano fermi */
static void drums_toggle(vet_t *v)
{
    S.drums = (uint8_t)!S.drums;
    S.hold_keys = 0; S.hold_chords = 0;
    for (int k = 0; k < 12; k++) ain(v, ACC_IN_KEY_UP, (uint8_t)k, 0);   /* niente accordi appesi */
    for (int i = 0; i < 4; i++) {                       /* né tipi ed estensioni: il loro rilascio in modalità batteria si perde */
        ain(v, ACC_IN_TYPE_UP, (uint8_t)i, 0);
        ain(v, ACC_IN_EXT_UP, (uint8_t)i, 0);
    }
    overlay(v, OV_DRUMS, ENC_BPM, S.drums);
}

static uint8_t accent(int vel)
{
    int v = 100 + (vel - 100) * S.accent / 10;
    return (uint8_t)clampi(v, 1, 127);
}

static void drum_hit(vet_t *v, int inst, int vel)
{
    if (inst < 0 || inst >= 12) return;
    if (vel) {
        snd_push(v, VS_DRUM, 0, (uint8_t)inst, accent(vel));
        S.drum_ms[inst] = v->now_ms;
    } else snd_push(v, VS_DRUM_OFF, 0, (uint8_t)inst, 0);
    v->m.plat.midi_in_ms = v->now_ms;
}

static void chord_up(vet_t *v, uint8_t a)
{
    if (a < 4) ain(v, ACC_IN_TYPE_UP, a, 0); else ain(v, ACC_IN_EXT_UP, (uint8_t)(a - 4), 0);
}

/* Hold (MIDI-133, T1): i rilasci trattenuti escono prima del tasto nuovo o quando il Hold si spegne */
static void hold_release(vet_t *v)
{
    for (int k = 0; k < 12; k++) if (S.hold_keys & (1u << k)) ain(v, ACC_IN_KEY_UP, (uint8_t)k, 0);
    for (int c = 0; c < 8; c++) if (S.hold_chords & (1u << c)) chord_up(v, (uint8_t)c);
    S.hold_keys = 0;
    S.hold_chords = 0;
}

/* Tap tempo (MIDI-133, T2): il BPM dalla media degli ultimi quattro tocchi; due secondi senza tocchi = da capo */
static void tap_tempo(vet_t *v)
{
    uint32_t t = v->now_ms;
    if (S.tap_n && t - S.tap_ms[(S.tap_n - 1) & 3] > 2000u) S.tap_n = 0;
    S.tap_ms[S.tap_n & 3] = t;
    if (S.tap_n < 255) S.tap_n++;
    if (S.tap_n < 2) return;
    int n = S.tap_n < 4 ? S.tap_n : 4;
    uint32_t span = t - S.tap_ms[(S.tap_n - n) & 3];
    if (!span) return;
    S.bpm = clampi((int)(60000u * (uint32_t)(n - 1) / span), 60, 200);
    overlay(v, OV_BPM, ENC_BPM, S.bpm);
}

static void scene_text(char *t, size_t max, int n, const char *tail)
{
    char d[4];
    ui_fmt_int(d, sizeof d, n + 1, 1);
    ui_fmt_copy(t, max, "Scene ");
    ui_fmt_cat(t, max, t, d);
    ui_fmt_cat(t, max, t, tail);
}

/* Scene (MIDI-133, T5–T8): tocco = richiama suono, basso, Perform, effetto, tonalità e basso acceso */
static void scene_recall(vet_t *v, int n)
{
    char t[40];
    if (n < 0 || n > 3) return;
    const vet_scene_t *sc = &v->scenes[n];
    if (!sc->used) { scene_text(t, sizeof t, n, " empty: hold 1 s to save"); msg(v, MSG_INFO, t, 2500); return; }
    S.sound = sc->sound % N_SOUNDS;
    S.bass = sc->bass % N_BASSES;
    S.perf_mode = sc->perf_mode % PERF_COUNT;
    S.perf_amount = clampi(sc->perf_amount, 0, perf_max(S.perf_mode));
    S.fx_amount = clampi(sc->fx_amount, 0, 10);
    S.scene_keep = 1;
    ain(v, ACC_IN_KEY_SELECT, (uint8_t)(sc->key_index % ACC_KEY_COUNT), 0);
    if ((v->acc.key_on != 0) != (sc->key_on != 0)) ain(v, ACC_IN_KEY_MODE_TOGGLE, 0, 0);
    ain(v, ACC_IN_OPTION_SET, ACC_OPT_BASS_ON, sc->bass_on ? 1 : 0);
    scene_text(t, sizeof t, n, "");
    msg(v, MSG_INFO, t, 2000);
}

static void scene_save(vet_t *v, int n)
{
    char t[40];
    if (n < 0 || n > 3) return;
    vet_scene_t *sc = &v->scenes[n];
    sc->used = 1;
    sc->sound = (uint8_t)S.sound; sc->bass = (uint8_t)S.bass;
    sc->perf_mode = (uint8_t)S.perf_mode; sc->perf_amount = (uint8_t)S.perf_amount;
    sc->fx_amount = (uint8_t)S.fx_amount;
    sc->key_index = (uint8_t)v->acc.key_index; sc->key_on = v->acc.key_on != 0; sc->bass_on = v->acc.bass_on != 0;
    v->scenes_dirty = 1;
    scene_text(t, sizeof t, n, " saved");
    msg(v, MSG_INFO, t, 2000);
}

static void handle(vet_t *v, const pnl_event_t *e)
{
    switch (e->type) {
    case PNL_KEY_DOWN:
        if (S.drums) drum_hit(v, e->a % 12, e->b ? e->b : 100);
        else { hold_release(v); ain(v, ACC_IN_KEY_DOWN, e->a, e->b); }
        break;
    case PNL_KEY_UP:
        if (S.drums) { drum_hit(v, e->a % 12, 0); break; }        /* ferma il Roll */
        if (S.hold) S.hold_keys |= (uint16_t)(1u << (e->a % 12));   /* Hold: il rilascio aspetta il tasto dopo */
        else ain(v, ACC_IN_KEY_UP, e->a, 0);
        break;
    case PNL_CHORD_DOWN:
        if (S.drums) break;
        if (e->a < 4) ain(v, ACC_IN_TYPE_DOWN, e->a, 0); else ain(v, ACC_IN_EXT_DOWN, (uint8_t)(e->a - 4), 0);
        break;
    case PNL_CHORD_UP:
        if (S.drums) break;
        if (S.hold) S.hold_chords |= (uint8_t)(1u << (e->a & 7));
        else chord_up(v, e->a);
        break;
    case PNL_BACK:
        if (v->list_kind) list_close(v);
        else {
            ov_hide(v);
            v->page_until = v->now_ms;                  /* B chiude anche la pagina dei comandi */
            v->page_pinned = 0;
        }
        break;
    case PNL_MACRO:
        if (e->a == MACRO_SYSTEM_MENU) {
            if (v->list_kind == L_PLATFORM) list_close(v); else list_open(v, L_PLATFORM, ENC_OPTIONS);
            v->m.layer.platform_menu = 1;
        } else if (e->a == MACRO_LOOP_STOP) looper_stop(v);
        else if (e->a == MACRO_LOOP_CLEAR) loop_send(v, LOOP_C_CLEAR);
        else if (e->a == MACRO_LOOP_OVERDUB) loop_send(v, LOOP_C_OVERDUB);   /* ⊕ della MK4: entra ed esce dall'overdub */
        else if (e->a == MACRO_LOOP_UNDO) loop_send(v, LOOP_C_UNDO);         /* con lo strato 0 vale Clear (ACC-222) */
        else if (e->a == MACRO_PANIC) { msg(v, MSG_INFO, "Panic: all notes off", 2000); snd_push(v, VS_ALL_OFF, 0, 0, 0); }
        else if (e->a == MACRO_RESET) {                                           /* T12 tenuto 3 s (MIDI-126) */
            demo_release(v);
            if (v->list_kind) list_close(v);
            ov_hide(v);
            loop_send(v, LOOP_C_RESET);                 /* anche in overdub, dove Clear è l'Undo dello strato */
            memset(S.sec, 0, sizeof S.sec);
            S.beat_on = 0;
            ain(v, ACC_IN_OPTION_SET, ACC_OPT_TRANSPOSE, 0);
            S.perf_mode = PERF_OFF; S.perf_amount = 0; S.lock_perf = 0;
            S.drums = 0;
            S.hold = S.metro = S.fill = 0; S.hold_keys = 0; S.hold_chords = 0;
            snd_push(v, VS_METRO, 0, 0, 0);
            snd_push(v, VS_FILL, 0, 0, 0);
            S.view = VIEW_CHORD;
            v->page_until = v->now_ms;
            v->page_pinned = 0;
            snd_push(v, VS_ALL_OFF, 0, 0, 0);
            msg(v, MSG_INFO, "Reset: loop, beat, transpose, perform", 3000);
        }
        else if (e->a == MACRO_KNOB_LOCK) S.knob_lock = (uint8_t)e->b;   /* T13 del pad (MIDI-131); vet_model lo copia */
        else if (e->a == MACRO_VIEW_TOGGLE) {                                    /* T14: Geek Out e ritorno (MIDI-132) */
            if (S.view == VIEW_GEEK) S.view = v->view_back;
            else { v->view_back = (uint8_t)S.view; S.view = VIEW_GEEK; }
        } else if (e->a == MACRO_CONTROLS_PAGE) {                                /* T15: la pagina resta aperta */
            v->page_pinned = (uint8_t)!v->page_pinned;
            if (!v->page_pinned) v->page_until = v->now_ms;
        }
        /* le funzioni dei tasti liberi del pad (MIDI-133) */
        else if (e->a == MACRO_HOLD_TOGGLE) { S.hold = (uint8_t)!S.hold; if (!S.hold) hold_release(v); }
        else if (e->a == MACRO_TAP_TEMPO) tap_tempo(v);
        else if (e->a == MACRO_METRO_TOGGLE) { S.metro = (uint8_t)!S.metro; snd_push(v, VS_METRO, 0, S.metro, 0); }
        else if (e->a == MACRO_FILL) { S.fill = (uint8_t)(e->b != 0); snd_push(v, VS_FILL, 0, S.fill, 0); }
        else if (e->a == MACRO_SCENE) scene_recall(v, (int)e->b);
        else if (e->a == MACRO_SCENE_SAVE) scene_save(v, (int)e->b);
        else if (e->a == MACRO_LOOP_EXIT) loop_send(v, LOOP_C_EXIT);
        else if (e->a == MACRO_DRUMS_TOGGLE) drums_toggle(v);
        else if (e->a == MACRO_BEAT_VOL) {
            S.beat_volume = clampi(S.beat_volume + e->b, 0, 99);
            overlay(v, OV_BEAT_VOLUME, ENC_BPM, S.beat_volume);
        } else if (e->a == MACRO_BASS_VOL) {
            S.bass_volume = clampi(S.bass_volume + e->b, 0, 99);
            overlay(v, OV_BASS_VOLUME, ENC_VOLUME, S.bass_volume);
        } else if (e->a == MACRO_DRUM_HIT) drum_hit(v, (e->b >> 8) & 0x7F, e->b & 0x7F);   /* pad del banco B (MIDI-135) */
        break;
    case PNL_SRC_CONNECTED:
        if (e->a == SRC_MACROPAD) msg(v, MSG_INFO, "Pad connected", 2000);
        break;
    case PNL_SRC_LOST:
        if (e->a == SRC_MACROPAD) msg(v, MSG_WARN, "Pad disconnected", 2000);
        break;
    case G_TURN: turn(v, e->a, e->b, false); break;
    case G_PRESS_TURN: turn(v, e->a, e->b, true); break;
    case G_PRESS: press(v, e->a); break;
    case G_HOLD:
        if (e->a == ENC_PERFORM) S.lock_perf = (uint8_t)!S.lock_perf;
        if (e->a == ENC_FX) S.lock_fx = (uint8_t)!S.lock_fx;
        if (e->a == ENC_BPM) list_open(v, L_BEATS, ENC_BPM);  /* tempo in chiave e Beat (UI-077) */
        break;
    case G_RELEASE:
        if (e->a < ENC_COUNT) S.sec[e->a] = 0;
        break;
    default: break;
    }
}

static void feed(vet_t *v, const pnl_event_t *ev, int n)
{
    for (int i = 0; i < n; i++) handle(v, &ev[i]);
}

/* ---- demo: il brano di demo.h, a tick del motore ---- */
#define DEMO_AHEAD 12u      /* tick di anticipo dei comandi della demo: circa 80 ms a 96 BPM */

static void snd_sync(vet_t *v);
static int fx_main(const uint8_t *p, int *ui_type);   /* definita con il synth, più sotto */

static const dsong_t *song_of(const vet_t *v) { return &vet_demo_songs[v->demo_song % vet_demo_songs_n]; }

uint32_t vet_demo_len(int i)
{
    if (i < 0) return 0;
    return vet_demo_songs[i % vet_demo_songs_n].ms;
}

void vet_demo_select(vet_t *v, int i) { v->demo_song = (uint8_t)((i % vet_demo_songs_n + vet_demo_songs_n) % vet_demo_songs_n); }

/* ---- scene (MIDI-133): testo chiave=valore, chiavi s1.sound … s4.basson ---- */
static const char *const SCENE_KEY[9] = { "used", "sound", "bass", "perf", "amount", "fx", "key", "keyon", "basson" };

size_t vet_scenes_write(const vet_t *v, char *buf, size_t max)
{
    kv_w_t w;
    kv_w_begin(&w, buf, max);
    for (int n = 0; n < 4; n++) {
        const vet_scene_t *s = &v->scenes[n];
        const int val[9] = { s->used, s->sound, s->bass, s->perf_mode, s->perf_amount, s->fx_amount,
                             s->key_index, s->key_on, s->bass_on };
        for (int k = 0; k < 9; k++) {
            char key[16] = "s1.";
            key[1] = (char)('1' + n);
            ui_fmt_cat(key, sizeof key, key, SCENE_KEY[k]);
            kv_w_int(&w, key, val[k]);
        }
    }
    return kv_w_end(&w);
}

void vet_scenes_read(vet_t *v, const char *txt, size_t n)
{
    kv_r_t r;
    kv_pair_t kv;
    kv_r_begin(&r, txt, n);
    while (kv_r_next(&r, &kv)) {
        int32_t x;
        if (kv.klen < 4 || kv.key[0] != 's' || kv.key[1] < '1' || kv.key[1] > '4' || kv.key[2] != '.') continue;
        if (!kv_val_int(&kv, &x)) continue;
        uint8_t b = (uint8_t)(x < 0 ? 0 : x > 255 ? 255 : x);
        vet_scene_t *s = &v->scenes[kv.key[1] - '1'];
        for (int k = 0; k < 9; k++) {
            size_t l = strlen(SCENE_KEY[k]);
            if (kv.klen - 3 != l || memcmp(kv.key + 3, SCENE_KEY[k], l)) continue;
            switch (k) {
            case 0: s->used = b != 0; break;
            case 1: s->sound = b; break;
            case 2: s->bass = b; break;
            case 3: s->perf_mode = b; break;
            case 4: s->perf_amount = b; break;
            case 5: s->fx_amount = b; break;
            case 6: s->key_index = b; break;
            case 7: s->key_on = b != 0; break;
            default: s->bass_on = b != 0; break;
            }
        }
    }
}

/* tick del motore; senza motore, quelli che vet_tick conta dall'orologio */
static uint32_t now_tick(const vet_t *v) { return v->snap ? v->snap->tick : v->vtick; }

static uint8_t demo_types, demo_exts;
static int8_t demo_key = -1;

/* opzioni degli accordi che il brano cambia: tornano come erano quando la demo si ferma */
static const uint8_t DEMO_OPTS[VET_DEMO_OPTS] = { ACC_OPT_KEY_INDEX, ACC_OPT_KEY_ON, ACC_OPT_BASS_ON, ACC_OPT_VOICING,
                                                  ACC_OPT_BASS_VOICING, ACC_OPT_SINGLE_NOTES, ACC_OPT_TRANSPOSE,
                                                  ACC_OPT_PLAY_STYLE, ACC_OPT_SECRET };
/* i controlli di chi suonava (suono, Perform, effetto, basso, volumi, tempo, Beat, vista, Lock):
 * fotografati quando la demo parte da ferma, rimessi quando si ferma */
static sim_t demo_S;

static void demo_release(vet_t *v)
{
    if (demo_key >= 0) ain(v, ACC_IN_KEY_UP, (uint8_t)demo_key, 0);
    for (int i = 0; i < 4; i++) if (demo_types >> i & 1) ain(v, ACC_IN_TYPE_UP, (uint8_t)i, 0);
    for (int i = 0; i < 4; i++) if (demo_exts >> i & 1) ain(v, ACC_IN_EXT_UP, (uint8_t)i, 0);
    demo_types = demo_exts = 0;
    demo_key = -1;
}

static void demo_do(vet_t *v, const dstep_t *s)
{
    switch (s->act) {
    case D_CHORD:
        demo_release(v);
        for (int i = 0; i < 4; i++) if ((uint8_t)s->a >> i & 1) ain(v, ACC_IN_TYPE_DOWN, (uint8_t)i, 0);
        for (int i = 0; i < 4; i++) if ((uint8_t)s->b >> i & 1) ain(v, ACC_IN_EXT_DOWN, (uint8_t)i, 0);
        ain(v, ACC_IN_KEY_DOWN, s->c, s->d ? s->d : 96);
        demo_types = (uint8_t)s->a;
        demo_exts = (uint8_t)s->b;
        demo_key = (int8_t)s->c;
        v->m.plat.midi_in_ms = v->now_ms;
        break;
    case D_OFF: demo_release(v); break;
    case D_TURN: turn(v, s->a, s->b, false); break;
    case D_PTURN:                                       /* premi, gira e lascia: la funzione secondaria non resta */
        turn(v, s->a, s->b, true);
        if (s->a >= 0 && s->a < ENC_COUNT) S.sec[s->a] = 0;
        break;
    case D_PRESS: press(v, s->a); break;
    case D_HOLD: { pnl_event_t e = { G_HOLD, SRC_FLIP, (uint8_t)s->a, 0, 0 }; handle(v, &e); break; }
    case D_BACK: { pnl_event_t e = { PNL_BACK, SRC_FLIP, 0, 0, 0 }; handle(v, &e); break; }
    case D_FOCUS: v->inp.gest.focus = (uint8_t)s->a; break;
    case D_VIEW: S.view = s->a; break;
    case D_THEME:                                       /* Notte = il tema di chi suona, Giorno = l'altro */
        v->m.prefs.theme = s->a == THEME_DARK ? v->demo_theme : (uint8_t)!v->demo_theme;
        break;
    case D_LOOP: loop_send(v, s->a); break;
    case D_BEATON: S.beat_on = s->a; break;
    case D_MENU: { pnl_event_t e = { PNL_MACRO, SRC_FLIP, MACRO_SYSTEM_MENU, 0, 0 }; handle(v, &e); break; }
    case D_PAGE: v->page_until = v->now_ms + (uint32_t)s->a * 1000u; break;
    case D_SOUND: turn(v, ENC_SOUND, (int)s->c - S.sound, false); break;
    case D_PERF:
        S.perf_mode = s->a;
        S.perf_amount = clampi(s->b, 0, perf_max(S.perf_mode));
        overlay(v, perf_arp() && S.perf_amount ? OV_ARP : OV_PERFORM, ENC_PERFORM, S.perf_amount);
        break;
    case D_VOICING: turn(v, ENC_CHORD_VOICING, (int)s->c - (int)v->acc.v, false); break;
    case D_BASS: turn(v, ENC_BASS, (int)s->c - S.bass, false); break;
    case D_BEAT: S.beat_mode = BEAT_PATTERN; S.beat = s->a; break;
    case D_BPM: turn(v, ENC_BPM, (int)s->c - S.bpm, false); break;
    case D_OPT: ain(v, ACC_IN_OPTION_SET, (uint8_t)s->a, s->b); break;
    case D_TITLE: msg(v, MSG_INFO, song_of(v)->title, 6000); break;
    case D_DRUMS: drums_toggle(v); break;
    case D_HIT:
        snd_push(v, VS_DRUM, 0, (uint8_t)(s->a % 12), s->d ? s->d : 100);
        S.drum_ms[s->a % 12] = v->now_ms;
        v->m.plat.midi_in_ms = v->now_ms;
        break;
    default: break;
    }
}

/* il resto (suono, tempo, opzioni, Beat) lo prepara il brano con i suoi primi passi */
static void demo_reset(vet_t *v)
{
    demo_release(v);
    if (v->list_kind) list_close(v);
    ov_hide(v);
    loop_send(v, LOOP_C_RESET);
    ain(v, ACC_IN_OPTION_SET, ACC_OPT_TRANSPOSE, 0);
    S.lock_perf = S.lock_fx = 0;
    S.drums = 0;
    S.hold = S.metro = S.fill = 0; S.hold_keys = 0; S.hold_chords = 0;
    snd_push(v, VS_METRO, 0, 0, 0);
    snd_push(v, VS_FILL, 0, 0, 0);
    S.view = VIEW_CHORD;
    S.beat_mode = BEAT_PATTERN; S.beat = 0; S.beat_on = 0;
    v->snd_sound = -1;                          /* suono, Perform ed effetto da capo (ACC-162) */
    v->inp.gest.focus = ENC_SOUND;
    v->page_until = v->now_ms;
    v->page_pinned = 0;
}

static void demo_start(vet_t *v)
{
    if (!v->demo_running)
    {
        for (int i = 0; i < VET_DEMO_OPTS; i++) v->demo_saved[i] = (int16_t)acc_option_get(&v->acc, DEMO_OPTS[i]);
        v->demo_theme = v->m.prefs.theme;               /* la demo cambia tema: alla fine torna il suo */
        demo_S = S;
        v->demo_focus = v->inp.gest.focus;
        v->demo_view_back = v->view_back;
        v->demo_pinned = v->page_pinned;
    }
    v->demo_tick0 = now_tick(v) + DEMO_AHEAD;
    v->snd_timed = 1;
    v->snd_at = v->demo_tick0;
    demo_reset(v);
    snd_sync(v);
    v->snd_timed = 0;
    v->demo_running = 1;
    v->demo_t0 = v->now_ms;
    v->demo_step = 0;
}

/* chi tocca un controllo ritrova lo strumento come lo aveva lasciato: il loop e il Beat della demo si
 * fermano; suono, Perform, effetto, basso, volumi, tempo, Beat, vista, Lock, opzioni, transpose,
 * tema, fuoco e pagina tornano quelli di prima; liste, menu e overlay della demo si chiudono */
static void demo_stop(vet_t *v)
{
    if (!v->demo_running) return;
    v->demo_running = 0;
    demo_release(v);
    loop_send(v, LOOP_C_RESET);                         /* anche se la demo era in overdub */
    for (int i = 0; i < VET_DEMO_OPTS; i++) ain(v, ACC_IN_OPTION_SET, DEMO_OPTS[i], v->demo_saved[i]);
    uint8_t lock = S.knob_lock;                         /* il Lock del pad è del pad, non della demo */
    S = demo_S;
    S.knob_lock = lock;
    S.beat_on = 0;
    S.drums = 0;
    memset(S.sec, 0, sizeof S.sec);
    if (S.sound != v->snd_sound) {                      /* il suono di prima, con il suo Perform e il suo effetto */
        int t;
        snd_push(v, VS_PATCH, 0, (uint8_t)S.sound, 0);
        v->snd_fx_idx = (uint8_t)fx_main(vet_sound_patch[S.sound % VET_N_SOUNDS], &t);
        S.fx_type = t;
        v->snd_sound = (int16_t)S.sound;
        v->snd_fx = -1;
    }
    v->m.prefs.theme = v->demo_theme;                   /* il tema scelto da chi suona, non quello della demo */
    v->inp.gest.focus = v->demo_focus;
    v->view_back = v->demo_view_back;
    v->page_pinned = v->demo_pinned;
    if (!v->page_pinned) v->page_until = v->now_ms;
    if (v->list_kind) list_close(v);                    /* il menu che la demo apre a fine Acacia */
    ov_hide(v);
    v->m.msg_plat.level = MSG_NONE;
}

/* la demo non parte da sola mentre si suona: un accordo che suona, il trasporto in moto (loop o
 * Beat), la batteria a tastiera accesa (Luigi, 15/10/2026: «è passato da solo al tema scuro») */
static bool busy(const vet_t *v)
{
    if (v->acc.sounding || S.beat_on || S.drums) return true;
    return v->snap && (v->snap->tr_on || v->snap->lp_state != LP_IDLE);
}

/* i passi fino a DEMO_AHEAD tick da ora partono subito, ognuno con il tick a cui vale */
static void demo_run(vet_t *v)
{
    uint32_t horizon = now_tick(v) + DEMO_AHEAD;
    const dsong_t *song = song_of(v);
    while (v->demo_step < (int)song->n) {
        const dstep_t *s = &song->steps[v->demo_step];
        uint32_t at = v->demo_tick0 + s->t;
        if ((int32_t)(at - horizon) > 0) break;
        v->demo_step++;
        if (s->act == D_END) {                          /* finito: il brano dopo, in giro */
            v->demo_song = (uint8_t)((v->demo_song + 1) % vet_demo_songs_n);
            demo_start(v);
            return;
        }
        v->snd_timed = 1;
        v->snd_at = at;
        demo_do(v, s);
        snd_sync(v);
        v->snd_timed = 0;
    }
}

void vet_demo_seek(vet_t *v, uint32_t t_ms, void (*step)(vet_t *v, void *ctx), void *ctx)
{
    v->booting = 0;
    v->m.layer.base = BASE_PLAY;
    demo_start(v);
    uint32_t start = v->now_ms;
    for (uint32_t t = 0; t <= t_ms; t += 10) {     /* come l'app: un modello a ogni passo */
        vet_tick(v, start + t);
        if (step) step(v, ctx);
        vet_model(v);
    }
}

/* ---- ingressi ---- */
static void user_input(vet_t *v, uint32_t now_ms)
{
    v->last_input_ms = now_ms;
    if (v->booting) { v->booting = 0; v->m.layer.base = BASE_PLAY; }
    demo_stop(v);
}

void vet_midi(vet_t *v, const midi_msg_t *msg, uint32_t now_ms)
{
    pnl_event_t ev[INP_MAX_OUT];
    v->now_ms = now_ms;
    v->m.plat.midi_in_ms = now_ms;
    if (msg->port != MIDI_PORT_CTL && v->inp.mpk_model != MPK_MODEL_MK4) return;
    uint8_t st = msg->n ? msg->b[0] & 0xF0 : 0;
    if (st == 0x90 || st == 0xB0 || st == 0xE0) user_input(v, now_ms);
    int n = inp_midi(&v->inp, msg, ev, INP_MAX_OUT);
    feed(v, ev, n);
}

static uint32_t menu_down_ms;      /* uscita di sicurezza della vetrina: MENU tenuto 2 s */
static uint8_t menu_down;

static bool mk4_present(const vet_t *v)
{
    return (v->inp.connected & (1u << SRC_MPK)) && v->inp.mpk_model == MPK_MODEL_MK4;
}

/* con la Plus X della Flip è il suo PUSH; senza è Hold (MIDI-137) */
static bool plus_present(const vet_t *v)
{
    return (v->inp.connected & (1u << SRC_MPK)) && v->inp.mpk_model != MPK_MODEL_MK4;
}

/* solo la MK4, senza pad (MIDI-137): il fuoco parte da Chord Voicing, così nav è la manopola dei rivolti */
static void mk4_only_focus(vet_t *v)
{
    if (mk4_present(v) && !(v->inp.connected & (1u << SRC_MACROPAD))) v->inp.gest.focus = ENC_CHORD_VOICING;
}

void vet_pad(vet_t *v, uint16_t code, int32_t value, uint32_t now_ms)
{
    pnl_event_t ev[INP_MAX_OUT];
    v->now_ms = now_ms;
    if (code == PAD_MENU && value != 2) { menu_down = value == 1; menu_down_ms = now_ms; }
    /* levette e grilletti mandano valori, non 1 e 0: contano come un ingresso oltre metà corsa */
    bool axis = code >= PAD_L2 && code <= PAD_RSTICK_Y;
    if (axis ? (code <= PAD_R2 ? value > 160 : (value > 16384 || value < -16384)) : value == 1) user_input(v, now_ms);
    /* i tasti del fuoco aprono la pagina dei comandi e la tengono aperta (UI-142a); dal 17/10/2026 i
     * tasti della Flip non tacciono mai (MIDI-137), quindi anche con la MK4. X solo quando è il PUSH della Plus */
    if (value != 0 && (code == PAD_L1 || code == PAD_R1 || code == PAD_A || (code == PAD_X && plus_present(v)) ||
                       code == PAD_UP || code == PAD_DOWN || code == PAD_LEFT || code == PAD_RIGHT))
        v->page_until = now_ms + PAGE_MS;
    int n = inp_pad(&v->inp, code, value, now_ms * 1000u, ev, INP_MAX_OUT);
    feed(v, ev, n);
}

void vet_mpk_model(vet_t *v, uint8_t model) { inp_set_mpk_model(&v->inp, model); }

void vet_mpk(vet_t *v, bool connected, const char *fw, uint32_t now_ms)
{
    pnl_event_t ev[INP_MAX_OUT];
    v->now_ms = now_ms;
    int n = connected ? inp_connected(&v->inp, SRC_MPK, now_ms * 1000u, ev, INP_MAX_OUT)
                      : inp_lost(&v->inp, SRC_MPK, now_ms * 1000u, ev, INP_MAX_OUT);
    feed(v, ev, n);
    if (connected) mk4_only_focus(v);
    v->m.plat.mpk_link = connected ? MPK_OPEN : MPK_ABSENT;
    v->factory_warned = 0;
    if (fw) ui_fmt_copy(v->m.plat.mpk_fw, sizeof v->m.plat.mpk_fw, fw);
    msg(v, connected ? MSG_INFO : MSG_WARN, connected ? "MPK connected" : "MPK disconnected", 2000);
}

void vet_flip_lost(vet_t *v, uint32_t now_ms)
{
    pnl_event_t ev[INP_MAX_OUT];
    v->now_ms = now_ms;
    int n = inp_lost(&v->inp, SRC_FLIP, now_ms * 1000u, ev, INP_MAX_OUT);
    feed(v, ev, n);
    n = inp_connected(&v->inp, SRC_FLIP, now_ms * 1000u, ev, INP_MAX_OUT);   /* il profilo riparte da capo */
    feed(v, ev, n);
}

/* macro pad collegato (link = PADL_*) o perso: avvisi, stato «PAD» e rilasci sintetici (MIDI-127) */
void vet_macropad(vet_t *v, uint8_t link, uint32_t now_ms)
{
    pnl_event_t ev[INP_MAX_OUT];
    v->now_ms = now_ms;
    bool on = link == PADL_OPEN || link == PADL_UNMAPPED;
    bool was = v->m.plat.pad_link == PADL_OPEN || v->m.plat.pad_link == PADL_UNMAPPED;
    if (on != was) {
        int n = on ? inp_connected(&v->inp, SRC_MACROPAD, now_ms * 1000u, ev, INP_MAX_OUT)
                   : inp_lost(&v->inp, SRC_MACROPAD, now_ms * 1000u, ev, INP_MAX_OUT);
        feed(v, ev, n);
        if (!on) mk4_only_focus(v);
    }
    v->m.plat.pad_link = link;
}

void vet_battery(vet_t *v, uint8_t pct, bool charging)
{
    v->m.plat.battery_pct = pct;
    v->m.plat.charging = charging;
}

/* ---- inizializzazione ---- */
void vet_init(vet_t *v, uint32_t now_ms)
{
    memset(v, 0, sizeof *v);
    memset(&S, 0, sizeof S);
    acc_init(&v->acc);
    inp_init(&v->inp);
    v->now_ms = v->boot_ms = v->last_ms = now_ms;
    v->booting = 1;
    v->demo_on = 1;
    v->last_input_ms = now_ms;
    v->tick_us = now_ms * 1000u;

    /* F♯ minore, basso acceso */
    for (int k = 21; k < ACC_KEY_COUNT; k++) {
        acc_spelled sp;
        acc_key_degree_spelling(k, 0, &sp);
        if (sp.letter == 'F' && sp.acc == ACC_ACC_SHARP) { ain(v, ACC_IN_KEY_SELECT, (uint8_t)k, 0); break; }
    }
    if (!v->acc.key_on) ain(v, ACC_IN_KEY_MODE_TOGGLE, 0, 0);
    ain(v, ACC_IN_OPTION_SET, ACC_OPT_BASS_ON, 1);

    /* il Perform arriva dal suono al primo snd_sync (ACC-162); il Beat è scelto ma fermo (ACC-205) */
    S.sound = 2; S.fx_type = FX_REV; S.fx_amount = 4; S.bass = 0; S.volume = 72; S.bass_volume = 70;
    S.bpm = 120; S.beat_mode = BEAT_PATTERN; S.beat = 0; S.meter = METER_4_4; S.beat_on = 0;
    S.beat_volume = 72; S.view = VIEW_CHORD;         /* i kit a campioni stanno a −1 dBFS: 72 ≈ −5,5 dB */
    S.accent = 10;                                   /* drum machine: tutta la dinamica (MIDI-135) */

    ui_model_t *m = &v->m;
    m->layer.base = BASE_BOOT;
    m->prefs.theme = THEME_LIGHT;                    /* Giorno: deciso da Luigi il 15/10/2026 (UI-128) */
    m->prefs.legend = 1;
    m->prefs.meters = 1;
    m->prefs.ghost_chord = 1;
    m->prefs.linnaeus = 1;
    m->plat.mpk_link = MPK_ABSENT;
    m->plat.battery_pct = 255;
    m->plat.midi_in_ms = m->plat.midi_out_ms = now_ms - 1000;
    ui_fmt_copy(m->boot.line[0], sizeof m->boot.line[0], "Audio   16 voices  VA FM RP  48 kHz");
    ui_fmt_copy(m->boot.line[1], sizeof m->boot.line[1], "MIDI    looking for the MPK mini");
#define VET_STR_(x) #x
#define VET_STR(x) VET_STR_(x)
    ui_fmt_copy(m->boot.line[2], sizeof m->boot.line[2],                    /* i conti veri, da patch_vetrina.h */
                "Sounds  " VET_STR(VET_N_SOUNDS) " Stame  " VET_STR(VET_N_BASSES) " basses  0 user");
    ui_fmt_copy(m->boot.version, sizeof m->boot.version, "vetrina 0.1");
    v->inp.gest.focus = ENC_SOUND;
    v->snd_sound = v->snd_bass = v->snd_vol = v->snd_bvol = v->snd_fx = -1;
    v->snd_bpm = v->snd_perf = v->snd_beat = v->snd_meter = v->snd_beat_on = v->snd_beat_vol = -1;
}

/* ---- synth: suono, basso, effetto principale e volumi verso il dsp ---- */

/* SND-601: l'effetto principale è il primo slot con intensità > 0 fra FX1, FX2 e Reverb; se sono
 * tutti a 0, FX1 se il tipo non è OFF, altrimenti Reverb. Restituisce l'indice del parametro. */
static int fx_main(const uint8_t *p, int *ui_type)
{
    static const uint8_t UI[8] = { FX_REV, FX_CHO, FX_ENS, FX_PHA, FX_FLA, FX_DRV, FX_TRM, FX_DLY };
    int t1 = p[SND_P_FX1TYPE], t2 = p[SND_P_FX2TYPE];
    int i1 = SND_P_FX1TYPE + (t1 == SND_FX_TREMOLO ? 1 : 2);
    int i2 = SND_P_FX2TYPE + (t2 == SND_FX_TREMOLO ? 1 : 2);
    if (t1 && p[i1] > 0) { *ui_type = UI[t1 & 7]; return i1; }
    if (t2 && p[i2] > 0) { *ui_type = UI[t2 & 7]; return i2; }
    if (p[SND_P_REVSEND] > 0 || !t1) { *ui_type = FX_REV; return SND_P_REVSEND; }
    *ui_type = UI[t1 & 7];
    return i1;
}

static int fx_display(int raw) { return (raw * 10 + 63) / 127; }      /* round(raw / 12,7) */

static void snd_sync(vet_t *v)
{
    if (S.sound != v->snd_sound) {
        const uint8_t *p = vet_sound_patch[S.sound % VET_N_SOUNDS];
        snd_push(v, VS_PATCH, 0, (uint8_t)S.sound, 0);
        int t;
        v->snd_fx_idx = (uint8_t)fx_main(p, &t);
        S.fx_type = t;
        v->snd_sound = (int16_t)S.sound;
        if (S.lock_fx || S.scene_keep) v->snd_fx = -1;   /* con il Lock, o da una scena, l'intensità è quella voluta */
        else { S.fx_amount = fx_display(p[v->snd_fx_idx]); v->snd_fx = (int16_t)S.fx_amount; }
        if (!S.lock_perf && !S.scene_keep) {        /* Perform di default del suono (ACC-162) */
            S.perf_mode = vet_sound_perf[S.sound % VET_N_SOUNDS][0];
            S.perf_amount = vet_sound_perf[S.sound % VET_N_SOUNDS][1];
        }
        S.scene_keep = 0;
    }
    if (S.fx_amount != v->snd_fx) {
        int raw = S.fx_amount * 127 / 10;
        snd_push(v, VS_PARAM, 0, v->snd_fx_idx, (uint8_t)raw);
        v->snd_fx = (int16_t)S.fx_amount;
    }
    if (S.bass != v->snd_bass) { snd_push(v, VS_PATCH, 1, (uint8_t)S.bass, 0); v->snd_bass = (int16_t)S.bass; }
    if (S.volume != v->snd_vol) { snd_push(v, VS_MASTER, 0, (uint8_t)S.volume, 0); v->snd_vol = (int16_t)S.volume; }
    if (S.bass_volume != v->snd_bvol) { snd_push(v, VS_BASS_VOL, 1, (uint8_t)S.bass_volume, 0); v->snd_bvol = (int16_t)S.bass_volume; }

    /* tempo, Perform e Beat verso il motore; la selezione del Beat prima dell'accensione */
    if (S.bpm != v->snd_bpm) { snd_push(v, VS_BPM, 0, (uint8_t)S.bpm, 0); v->snd_bpm = (int16_t)S.bpm; }
    int perf = S.perf_mode << 8 | S.perf_amount;
    if (perf != v->snd_perf) {
        snd_push(v, VS_PERF, 0, (uint8_t)S.perf_mode, (uint8_t)S.perf_amount);
        v->snd_perf = (int16_t)perf;
    }
    int beat = S.beat_mode << 8 | S.beat;
    if (beat != v->snd_beat) {                      /* i Beat della vetrina sono 1…6 in core/beat */
        snd_push(v, VS_BEAT, 0, S.beat_mode == BEAT_METRONOME ? BEAT_M_METRONOME : BEAT_M_PATTERN, (uint8_t)(S.beat + 1));
        v->snd_beat = (int16_t)beat;
    }
    if (S.meter != v->snd_meter) { snd_push(v, VS_METER, 0, (uint8_t)S.meter, 0); v->snd_meter = (int16_t)S.meter; }
    if (S.beat_on != v->snd_beat_on) { snd_push(v, VS_BEAT_ON, 0, (uint8_t)S.beat_on, 0); v->snd_beat_on = (int16_t)S.beat_on; }
    if (S.beat_volume != v->snd_beat_vol) {
        snd_push(v, VS_BEAT_VOL, 0, (uint8_t)S.beat_volume, 0);
        v->snd_beat_vol = (int16_t)S.beat_volume;
    }
}

/* ---- tempo che passa ---- */
static void synth_scope(vet_t *v, uint32_t dt_ms)
{
    const float sr = 9600.0f;
    int n = (int)((float)dt_ms * sr / 1000.0f);
    if (n > VET_SCOPE_LEN) n = VET_SCOPE_LEN;
    const acc_state *s = &v->acc;
    float f[8];
    int k = 0;
    for (int i = 0; i < s->treble.n && k < 6; i++) f[k++] = 440.0f * powf(2.0f, ((float)s->treble.note[i] - 69.0f) / 12.0f);
    if (s->bass_note >= 0 && k < 8) f[k++] = 440.0f * powf(2.0f, ((float)s->bass_note - 69.0f) / 12.0f);
    for (int j = 0; j < n; j++) {
        float x = 0.0f;
        for (int i = 0; i < k; i++) {
            v->phase[i] += f[i] / sr;
            if (v->phase[i] > 1.0f) v->phase[i] -= 1.0f;
            x += sinf(6.2831853f * v->phase[i]) + 0.3f * sinf(12.566371f * v->phase[i]);
        }
        x = k ? x / (float)k * v->level * 1.6f : 0.0f;
        if (x > 0.98f) x = 0.98f;
        if (x < -0.98f) x = -0.98f;
        v->scope[v->scope_wr % VET_SCOPE_LEN] = (int16_t)(x * 32767.0f);
        v->scope_wr++;
    }
}

void vet_tick(vet_t *v, uint32_t now_ms)
{
    pnl_event_t ev[INP_MAX_OUT];
    uint32_t dt = now_ms - v->last_ms;
    v->now_ms = now_ms;
    v->last_ms = now_ms;
    if (v->snap_src) mot_snap_read(v->snap_src, &v->snap_copy);   /* lo stato del motore, coerente */
    if (dt > 1000u) {
        /* una pausa lunga (Flip sospesa): l'orologio dei gesti in µs gira ogni 71,6 min e, oltre
         * mezz'ora, sembrava andato indietro e si fermava. Si riparte da adesso */
        v->tick_us = now_ms * 1000u;
        gest_resync(&v->inp.gest, v->tick_us);
    }
    if (menu_down && now_ms - menu_down_ms >= 2000) v->quit = 1;
    if (!v->snap) {                                     /* senza motore la demo conta i tick dall'orologio */
        v->vt_acc += (dt > 1000u ? 1000u : dt) * (uint32_t)S.bpm * 96u;
        v->vtick += v->vt_acc / 60000u;
        v->vt_acc %= 60000u;
    }

    if (v->booting) {
        v->m.boot.t_ms = (uint16_t)(now_ms - v->boot_ms);
        if (now_ms - v->boot_ms >= BOOT_MS) {
            v->booting = 0;
            v->m.layer.base = BASE_PLAY;
            v->last_input_ms = now_ms - DEMO_IDLE_MS;      /* la demo parte subito dopo l'avvio */
        }
    }
    /* gesti a tempo (G_HOLD, ripetizioni) */
    while ((int32_t)(now_ms * 1000u - v->tick_us) >= 0) {
        int n = inp_tick(&v->inp, v->tick_us, ev, INP_MAX_OUT);
        feed(v, ev, n);
        v->tick_us += PNL_TICK_US;
        if ((int32_t)(now_ms * 1000u - v->tick_us) > 100000) v->tick_us = now_ms * 1000u;
    }
    /* demo */
    if (!v->booting) {
        if (v->demo_running) demo_run(v);
        else if (v->demo_on && now_ms - v->last_input_ms > DEMO_IDLE_MS && !v->list_kind && !busy(v)) demo_start(v);
    }
    /* count-in: «04» … «01» sopra la plancia (UI-089) */
    if (lp_state(v) == LP_COUNT_IN) {
        v->m.layer.ov.kind = OV_COUNT_IN;
        v->m.layer.ov.enc = ENC_LOOP;
        v->m.layer.ov.value = (int16_t)count_in_left(v);
        v->ov_until = now_ms + 100u;
        v->m.layer.ov.until_ms = v->ov_until;
    }
    /* overlay e liste che scadono */
    if (v->m.layer.ov.kind != OV_NONE && (int32_t)(now_ms - v->ov_until) >= 0) ov_hide(v);
    if ((v->list_kind == L_SOUND || v->list_kind == L_PERFORM || v->list_kind == L_BEATS) && now_ms - v->list_ms > LIST_IDLE_MS)
        list_close(v);
    if (v->m.msg_plat.level && (int32_t)(now_ms - v->m.msg_plat.until_ms) >= 0) v->m.msg_plat.level = MSG_NONE;

    /* livello e oscilloscopio finti */
    float target = v->acc.sounding ? 0.55f + 0.04f * (float)v->acc.treble.n : 0.0f;
    float a = target > v->level ? 0.5f : 0.02f;
    v->level += (target - v->level) * a;
    if (!v->ext_scope) synth_scope(v, dt);
    snd_sync(v);
}

/* ---- modello ---- */
static void spell(const acc_state *s, int midi, char *buf, int n)
{
    static const char *const ACC[5] = { "", "\xE2\x99\xAF", "\xE2\x99\xAD", "x", "\xE2\x99\xAD\xE2\x99\xAD" };
    acc_spelled sp = acc_spell_pc(s, midi % 12);
    int oct = midi / 12 - 1;
    if (sp.letter == 'B' && (sp.acc == ACC_ACC_SHARP || sp.acc == ACC_ACC_DSHARP) && midi % 12 <= 1) oct--;
    if (sp.letter == 'C' && (sp.acc == ACC_ACC_FLAT || sp.acc == ACC_ACC_DFLAT) && midi % 12 >= 10) oct++;
    char o[6], l[2] = { sp.letter, 0 };
    ui_fmt_int(o, sizeof o, oct, 1);
    ui_fmt_cat(buf, n, l, ACC[sp.acc < 5 ? sp.acc : 0]);
    ui_fmt_cat(buf, n, buf, o);
}

static void label_from(const acc_chord_name *nm, chord_label_t *c)
{
    static const char *const ACC[5] = { "", "\xE2\x99\xAF", "\xE2\x99\xAD", "x", "\xE2\x99\xAD\xE2\x99\xAD" };
    memset(c, 0, sizeof *c);
    c->root[0] = nm->root.letter;
    ui_fmt_copy(c->acc, sizeof c->acc, ACC[nm->root.acc < 5 ? nm->root.acc : 0]);
    if (!nm->single) {
        ui_fmt_copy(c->quality, sizeof c->quality, nm->quality);
        ui_fmt_copy(c->sup, sizeof c->sup, nm->sup);
        if (nm->has_slash) {
            c->slash_root[0] = nm->slash.letter;
            ui_fmt_copy(c->slash_acc, sizeof c->slash_acc, ACC[nm->slash.acc < 5 ? nm->slash.acc : 0]);
        }
    }
}

static void set_bit(uint32_t *m, int n) { if (n >= 0 && n < 128) m[n >> 5] |= 1u << (n & 31); }

static void fill_music(vet_t *v, ui_music_t *mu)
{
    const acc_state *s = &v->acc;
    bool sounding = s->sounding && s->has_name;
    if (sounding) {
        v->have_last = 1;
        v->released_ms = v->now_ms;
        label_from(&s->name, &v->last_chord);
        v->last_single = s->name.single;
        v->last_single_midi = s->name.single_note;
        int n = 0;
        if (s->bass_note >= 0) {
            v->last_notes[n].midi = (uint8_t)s->bass_note;
            v->last_notes[n].role = ROLE_BASS;
            spell(s, s->bass_note, v->last_notes[n].name, sizeof v->last_notes[n].name);
            n++;
        }
        for (int i = 0; i < s->treble.n && n < UI_NOTES_MAX; i++, n++) {
            v->last_notes[n].midi = s->treble.note[i];
            v->last_notes[n].role = ROLE_TREBLE;
            spell(s, s->treble.note[i], v->last_notes[n].name, sizeof v->last_notes[n].name);
        }
        v->last_n = (uint8_t)n;
        for (int i = 0; i < s->treble.n; i++) { set_bit(mu->live_treble, s->treble.note[i]); mu->pc_sounding |= (uint16_t)(1u << (s->treble.note[i] % 12)); }
        if (s->bass_note >= 0) set_bit(mu->live_bass, s->bass_note);
    }
    if (S.drums)                                           /* il tasto colpito si accende per un attimo (UI-150b) */
        for (int k = 0; k < 12; k++)
            if (S.drum_ms[k] && v->now_ms - S.drum_ms[k] < 150u) set_bit(mu->live_treble, 60 + k);
    if (v->have_last) {
        uint32_t since = v->now_ms - v->released_ms;
        mu->chord_state = sounding ? CH_SOUNDING : since < LINGER_MS ? CH_LINGER : v->m.prefs.ghost_chord ? CH_GHOST : CH_NONE;
        mu->chord = v->last_chord;
        mu->single_note = v->last_single;
        mu->single_midi = v->last_single_midi;
        mu->n_notes = v->last_n;                           /* le note dell'ultimo accordo in ogni stato: le viste le colorano */
        memcpy(mu->notes, v->last_notes, sizeof mu->notes);
    }
    mu->key_on = s->key_on;
    mu->key_index = s->key_index;
    if (s->key_on) {
        int ek = acc_effective_key(s->key_index, s->transpose);
        for (int pc = 0; pc < 12; pc++) if (acc_key_in_scale(ek, pc)) mu->pc_in_key |= (uint16_t)(1u << pc);
        acc_spelled sp;
        acc_key_degree_spelling(ek, 0, &sp);
        static const char *const ACC[5] = { "", "\xE2\x99\xAF", "\xE2\x99\xAD", "x", "\xE2\x99\xAD\xE2\x99\xAD" };
        char l[2] = { sp.letter, 0 };
        ui_fmt_cat(mu->key_name, sizeof mu->key_name, l, ACC[sp.acc < 5 ? sp.acc : 0]);
        ui_fmt_cat(mu->key_name, sizeof mu->key_name, mu->key_name, acc_key_is_minor(ek) ? " Minor" : " Major");
    }
    mu->transpose = s->transpose;
    mu->v = s->v;
    mu->vb = s->vb;
    mu->W = (uint8_t)(s->v + ACC_W_OFFSET);
    mu->WB = (uint8_t)(s->vb + ACC_WB_OFFSET);
    mu->single_notes = s->single_notes;
    mu->play_style = s->style;
    mu->secret_chords = s->secret != ACC_SECRET_OFF;
    mu->pocket_pc = 255;
}

/* metrica in uso: quella del metronomo, o 4/4 con un Beat (ACC-209) */
static void meter_now(uint32_t *bar, uint32_t *click, int *bpb, int *unit)
{
    static const uint8_t BPB[4] = { 2, 3, 4, 6 };
    int meter = S.beat_mode == BEAT_PATTERN ? METER_4_4 : S.meter;
    *bar = meter_bar(meter);
    *click = meter_click(meter);
    *bpb = BPB[meter & 3];
    *unit = meter == METER_6_8 ? 8 : 4;
}

/* battiti che mancano alla fine del count-in: 4 … 1 in 4/4 (UI-089) */
static int count_in_left(const vet_t *v)
{
    uint32_t bar, click;
    int bpb, unit;
    meter_now(&bar, &click, &bpb, &unit);
    uint32_t c = v->snap->tick - v->snap->tr_t0;
    return bpb - (int)(c < bar ? c / click : (uint32_t)bpb - 1u);
}

static void fill_tempo_looper(vet_t *v, ui_model_t *m)
{
    uint32_t bar, click;
    int bpb, unit;
    meter_now(&bar, &click, &bpb, &unit);
    ui_tempo_t *t = &m->tempo;
    t->bpm = (uint16_t)S.bpm;
    t->beats_per_bar = (uint8_t)bpb;
    t->beat_unit = (uint8_t)unit;
    t->beat_mode = (uint8_t)S.beat_mode;
    t->beat_index = (uint8_t)(S.beat + 1);
    ui_fmt_copy(t->beat_name, sizeof t->beat_name, BEATS_NAME(S.beat % N_BEATS));
    t->beat_volume = (uint8_t)S.beat_volume;
    t->drums_on = S.drums;                                /* batteria a tastiera (UI-097) */
    t->metro_on = S.metro;                                /* metronomo di T3 (MIDI-133) */
    t->kit = (uint8_t)S.kit;                              /* drum machine (MIDI-135) */
    t->roll = (uint8_t)S.roll;
    t->accent = (uint8_t)S.accent;
    const mot_snap_t *sn = v->snap;
    if (sn && sn->tr_on) {                                        /* posizione del trasporto vero */
        uint32_t pos = sn->tick - sn->tr_t0;
        t->running = 1;
        t->beat = (uint8_t)((pos % bar) / click);
        t->bar = 1 + pos / bar;
        t->beat_phase = (uint16_t)((pos % click) * 65536u / click);
    }

    ui_looper_t *lp = &m->looper;
    uint8_t st = lp_state(v);
    if (st != v->lp_seen) { lp->menu_sel = 0; v->lp_seen = st; }  /* voce iniziale del menu (UI-088) */
    lp->state = st;
    if (st == LP_IDLE || !sn) return;
    lp->layers = sn->lp_layers;
    lp->loop_full = sn->lp_full;
    uint32_t len = sn->lp_len ? sn->lp_len : bar, pos = 0;
    if (st == LP_REC) pos = sn->tick - sn->lp_t0 < len ? sn->tick - sn->lp_t0 : len - 1;
    else if (st == LP_PLAY || st == LP_OVERDUB) pos = (sn->tick - sn->lp_t0) % len;
    lp->bars = (uint8_t)(len / bar);
    lp->cur_bar = (uint8_t)(1 + pos / bar);
    lp->progress = (uint16_t)((uint64_t)pos * 65535u / len);
    if (st == LP_COUNT_IN) lp->count_in = (uint8_t)count_in_left(v);
    for (int r = 0; r < 2; r++)                                   /* le note che il loop sta suonando */
        for (int i = 0; i < 128; i++)
            if (sn->lp_notes[r][i >> 3] >> (i & 7) & 1u) set_bit(r ? m->music.loop_bass : m->music.loop_treble, i);
    loop_menu(v, lp->menu);
}

const ui_model_t *vet_model(vet_t *v)
{
    ui_model_t *m = &v->m;
    if (v->snap_src) mot_snap_read(v->snap_src, &v->snap_copy);
    /* azzera le parti calcolate, tiene preferenze, piattaforma, avvisi e stato delle liste */
    memset(&m->music, 0, sizeof m->music);
    uint8_t menu_sel = m->looper.menu_sel;
    memset(&m->tempo, 0, sizeof m->tempo);
    memset(&m->looper, 0, sizeof m->looper);
    m->looper.menu_sel = menu_sel;
    memset(&m->ctl, 0, sizeof m->ctl);
    memset(&m->meters, 0, sizeof m->meters);

    m->now_ms = m->core_ms = v->now_ms;
    m->seq++;
    fill_music(v, &m->music);
    fill_tempo_looper(v, m);

    ui_controls_t *c = &m->ctl;
    c->focus = v->inp.gest.focus;
    c->turn_target = gest_target(&v->inp.gest);
    if (S.view != VIEW_GEEK) v->view_back = (uint8_t)S.view;   /* T14 torna all'ultima vista prima di Geek Out, comunque ci si arrivi */
    bool mk4 = v->inp.mpk_model == MPK_MODEL_MK4;
    m->plat.mpk_model = mk4;
    m->ctl.hold = S.hold;
    m->ctl.fill = S.fill;
    c->push = mk4 ? v->inp.mk4.push : v->inp.mpk.push;
    c->knob_lock = S.knob_lock;
    c->pad_inst = v->inp.mpad.inst;                   /* pad strumento: tipo ed estensione tenuti (MIDI-136) */
    c->pad_type = v->inp.mpad.ch_type;
    c->pad_ext = v->inp.mpad.ch_ext;
    if (c->pad_inst != v->pad_inst_seen) {             /* senza tastiera il pad suona: lo si dice una volta */
        v->pad_inst_seen = c->pad_inst;
        if (c->pad_inst && v->m.plat.pad_link == PADL_OPEN) msg(v, MSG_INFO, "Pad plays notes", 2000);
    }
    /* programma della Plus e banco stimato dei pad (MIDI-088, MIDI-089): prima non arrivavano alla
     * testata, e «FACTORY» non compariva mai. L'avviso di MIDI-119 una volta per collegamento */
    m->plat.mpk_profile = !mk4 && v->inp.mpk.factory ? MPKP_FACTORY : MPKP_STAME;
    m->plat.mpk_bank = mk4 ? MPK_BANK_EST_UNKNOWN : v->inp.mpk.bank == MPK_BANK_A ? MPK_BANK_EST_A
                     : v->inp.mpk.bank == MPK_BANK_B ? MPK_BANK_EST_B : MPK_BANK_EST_UNKNOWN;
    if (m->plat.mpk_profile == MPKP_FACTORY && !v->factory_warned && m->plat.mpk_link == MPK_OPEN) {
        v->factory_warned = 1;
        msg(v, MSG_WARN, "STAME program not active: reduced functions", 5000);
    }
    for (int k = 0; k < ENC_COUNT; k++) {
        if (gest_held(&v->inp.gest, (uint8_t)k)) {
            /* dal tempo trascorso, non da t_down/1000: i µs girano ogni 2³² (71,6 min) e la barra del
             * tenuto partiva piena a ogni pressione */
            int32_t held_us = pnl_dt(v->inp.gest.now, v->inp.gest.t_down[k]);
            c->st[k].flags |= CF_PRESSED;
            c->st[k].pressed_since_ms = v->now_ms - (uint32_t)(held_us > 0 ? held_us / 1000 : 0);
        }
        c->st[k].t_hold_ms = 1000;
        if (S.sec[k]) c->st[k].flags |= CF_SECONDARY;
    }
    if (m->layer.ov.kind != OV_NONE && m->layer.ov.enc < ENC_COUNT) c->st[m->layer.ov.enc].flags |= CF_ACTIVE;
    if (v->acc.key_on) c->st[ENC_KEY].flags |= CF_LED;
    if (v->acc.bass_on) c->st[ENC_BASS].flags |= CF_LED;
    if (S.lock_perf) c->st[ENC_PERFORM].flags |= CF_LOCK | CF_LED;
    if (S.lock_fx) c->st[ENC_FX].flags |= CF_LOCK | CF_LED;
    c->sound_num = (uint8_t)(S.sound + 1);
    ui_fmt_copy(c->sound_name, sizeof c->sound_name, SOUNDS[S.sound].name);
    c->sound_engine = SOUNDS[S.sound].engine;
    ui_fmt_copy(c->sound_cat, sizeof c->sound_cat, SOUNDS[S.sound].cat);
    c->perf_mode = (uint8_t)S.perf_mode;
    c->perf_amount = (uint8_t)S.perf_amount;
    c->arp_rate = S.perf_amount > 3 ? 16 : 8;              /* tipo di ACC-171 dall'amount */
    c->arp_dir = (uint8_t)(S.perf_amount ? (S.perf_amount - 1) % 3 : 0);
    c->fx_main_type = (uint8_t)S.fx_type;
    c->fx_main_amount = (uint8_t)S.fx_amount;
    c->fx[0].type = FX_REV; c->fx[0].amount = (uint8_t)S.fx_amount;
    c->fx[1].type = FX_CHO; c->fx[1].amount = 3;
    c->fx[2].type = FX_DLY; c->fx[2].amount = 5;
    c->fx[3].type = FX_FLT; c->fx[3].amount = 0;
    c->bass_on = v->acc.bass_on;
    c->bass_num = (uint8_t)(S.bass + 1);
    ui_fmt_copy(c->bass_name, sizeof c->bass_name, BASSES[S.bass]);
    c->volume = (uint8_t)S.volume;
    c->bass_volume = (uint8_t)S.bass_volume;
    c->view = (uint8_t)S.view;

    /* lista: finestra di 9 voci attorno alla selezione */
    ui_list_t *l = &m->layer.list;
    memset(l, 0, sizeof *l);
    if (v->list_kind) {
        static const char *const PATH[] = { "", "SOUND", "PERFORM", "OPTIONS", "MENU", "BEATS" };
        static const uint8_t KIND[] = { 0, LS_SOUND, LS_PERFORM, LS_OPTIONS, LS_PLATFORM, LS_BEATS };
        l->open = 1;
        l->owner = v->list_owner;
        l->kind = KIND[v->list_kind];
        ui_fmt_copy(l->path, sizeof l->path, PATH[v->list_kind]);
        l->n = (uint16_t)list_n(v->list_kind);
        l->sel = v->list_sel;
        int first = (int)l->sel - UI_LIST_WIN / 2;
        if (first < 0) first = 0;
        l->win_first = (uint16_t)first;
        for (int i = 0; i < UI_LIST_WIN && first + i < l->n; i++) list_item(v, v->list_kind, first + i, &l->win[i]);
    }
    m->layer.platform_menu = v->list_kind == L_PLATFORM;
    m->layer.page = (v->list_kind || v->page_pinned || (int32_t)(v->page_until - v->now_ms) > 0) ? PAGE_CONTROLS : PAGE_PLAY;

    /* meter finti */
    int voices = m->music.chord_state == CH_SOUNDING ? m->music.n_notes : 0;
    m->meters.voices_used = (uint8_t)voices;
    m->meters.dsp_load_pct = (uint8_t)(11 + voices * 2);
    uint16_t pk = (uint16_t)(v->level * 26000.0f);
    m->meters.peak[0] = pk;
    m->meters.peak[1] = (uint16_t)(pk * 9 / 10);
    m->meters.scope = v->scope;
    m->meters.scope_len = VET_SCOPE_LEN;
    m->meters.scope_wr = (const volatile uint32_t *)&v->scope_wr;
    if (v->ext_scope) {                                   /* uscita vera del synth */
        m->meters.scope = v->ext_scope;
        m->meters.scope_len = v->ext_scope_len;
        m->meters.scope_wr = v->ext_scope_wr;
    }
    if (v->ext_peak) {
        m->meters.peak[0] = (uint16_t)(clampf(v->ext_peak[0], 0.0f, 1.0f) * 32767.0f);
        m->meters.peak[1] = (uint16_t)(clampf(v->ext_peak[1], 0.0f, 1.0f) * 32767.0f);
    }
    if (v->stats) {                                       /* misure vere del thread audio (PLT-021) */
        uint32_t l = atomic_load_explicit(&v->stats->load_pct, memory_order_relaxed);
        uint32_t lm = atomic_load_explicit(&v->stats->load_max_pct, memory_order_relaxed);
        m->meters.dsp_load_pct = (uint8_t)(l > 100u ? 100u : l);
        m->meters.dsp_load_max_pct = (uint8_t)(lm > 100u ? 100u : lm);
        m->meters.xrun_count = atomic_load_explicit(&v->stats->xruns, memory_order_relaxed);
    }
    return m;
}
