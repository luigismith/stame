/* ui/ui_model.h — lo stato completo da mostrare (sezione 30, §2, UI-020..UI-029).
 *
 * C11 puro, nessuna dipendenza oltre a core/input/panel.h (enc_id_t). Si copia per valore a ogni
 * frame: niente puntatori, tranne quello in sola lettura all'anello dell'oscilloscopio.
 * I testi derivati dai valori li compongono i renderer con ui_fmt_* (UI-029).
 */
#ifndef STAME_UI_MODEL_H
#define STAME_UI_MODEL_H

#include "../core/stame_base.h"
#include "../core/input/panel.h"

/* ---- 2.1 accordo e note (UI-021, UI-033) ---- */
#define UI_NOTES_MAX 16
typedef enum { ROLE_TREBLE, ROLE_BASS } ui_role_t;
typedef enum { CH_NONE, CH_SOUNDING, CH_LINGER, CH_GHOST } ui_chord_state_t;
typedef struct { uint8_t midi, role; char name[12]; } ui_note_t;     /* name UTF-8: "F♯3", "B♭♭3" */

typedef struct {
    char root[2];           /* "C".."B" */
    char acc[8];            /* "", "♯", "♭", "x", "♭♭" (6 byte: in Fa♭ maggiore o Re♭ minore) */
    char quality[8];        /* in linea: "", "m", "dim", "sus", "+", "m(add4)" */
    char sup[8];            /* apice: "", "7", "M7", "6", "9", "M79", "m6", "5", "JAZZ", "WTF" */
    char slash_root[2];     /* basso diverso dalla fondamentale, oppure "" */
    char slash_acc[8];
} chord_label_t;

typedef struct {
    chord_label_t chord;
    uint8_t  chord_state;               /* ui_chord_state_t */
    uint8_t  single_note;               /* 1 = nota singola (UI-037) */
    uint8_t  single_midi;
    uint8_t  n_notes;
    ui_note_t notes[UI_NOTES_MAX];      /* note dal vivo, dalla più grave; basso compreso */
    uint32_t live_treble[4], live_bass[4];
    uint32_t loop_treble[4], loop_bass[4];
    uint16_t pc_sounding;               /* classi treble che suonano */
    uint16_t pc_in_key;                 /* classi della tonalità; 0 con la Key mode spenta */
    uint8_t  key_on, key_index;
    char     key_name[16];              /* "F♯ Minor" */
    int8_t   transpose;
    uint8_t  v, W, vb, WB;              /* voicing grezzi e finestre (ACC-072..075) */
    uint8_t  single_notes;              /* 0 SPLIT, 1 FULL_OCTAVE */
    uint8_t  play_style, secret_chords;
    uint8_t  pocket_pc;                 /* 255 = nessuna */
} ui_music_t;

/* ---- 2.2 tempo (UI-022) ---- */
#define UI_INV_PARTS 5                  /* come INV_PARTS e INV_STEPS di core/inventa.h */
#define UI_INV_STEPS 32
typedef enum { BEAT_OFF, BEAT_METRONOME, BEAT_PATTERN } ui_beat_mode_t;
typedef struct {
    uint16_t bpm;
    uint8_t  beats_per_bar, beat_unit;
    uint8_t  running;
    uint8_t  beat;                      /* 0..beats_per_bar-1 */
    uint32_t bar;                       /* da 1 */
    uint16_t beat_phase;                /* 0..65535 */
    uint8_t  beat_mode;                 /* ui_beat_mode_t */
    uint8_t  beat_index;
    char     beat_name[24];
    uint8_t  beat_volume;
    uint8_t  drums_on;
    uint8_t  metro_on;                  /* metronomo indipendente dal Beat (T3 del pad, MIDI-133) */
    uint8_t  kit, roll, accent;         /* drum machine (40 MIDI-135): kit scelto (0 = del Beat), Roll 0…6, Accent 0…10 */
    char     kit_name[16];              /* nome del kit scelto, «Beat» con il kit del Beat (20 SND-541) */
    char     kit_info[32];              /* «Synth, analog», «Samples, acoustic»; con il kit del Beat: «Funk: Studio» */
    uint8_t  swing, drive;              /* Swing in tick 0…12 (10 ACC-216), Drive 0…10 (20 SND-538) */
    int8_t   filt;                      /* filtro della batteria: −10 passa-basso … 0 spento … +10 passa-alto */
    uint8_t  drop;                      /* T13 tenuto (40 MIDI-140): Beat, loop di batteria e basso tacciono */
    /* la batteria che si inventa (40 MIDI-139): il Beat è il loop inventato; stile, variazione, densità
     * di tutto, parte che M regola (0 = tutto, 1…5 = cassa, rullante, charleston, aperto, percussioni),
     * densità di ogni parte, passo che suona (255 = fermo) e la griglia dei colpi (velocity, 0 = niente) */
    uint8_t  inv, groove, variation, density, part;
    uint8_t  dens[UI_INV_PARTS];
    uint8_t  inv_step;
    uint8_t  grid[UI_INV_PARTS][UI_INV_STEPS];
    char     groove_name[12];
} ui_tempo_t;

/* ---- 2.3 looper (UI-023) ---- */
typedef enum { LP_IDLE, LP_WAITING_ROOM, LP_COUNT_IN, LP_REC, LP_PLAY, LP_OVERDUB, LP_PAUSE } ui_lp_state_t;
typedef enum { LPI_REC, LPI_PLAY, LPI_BACK, LPI_OVERDUB, LPI_PAUSE, LPI_CLEAR, LPI_STOP, LPI_UNDO } ui_lp_item_t;
typedef struct {
    uint8_t  state, free_mode, bars, cur_bar;   /* free_mode: «free» della specifica, nome avvelenato da stame_base.h */
    uint16_t progress;
    uint8_t  count_in, layers, loop_full, slot;
    uint8_t  menu[3], menu_sel;
    uint8_t  wr_choice;
} ui_looper_t;

/* ---- 2.4 controlli (UI-024) ---- */
enum { CF_PRESSED = 1, CF_LED = 2, CF_LOCK = 4, CF_ACTIVE = 8, CF_SECONDARY = 16, CF_LEGACY = 32 };
typedef struct {
    uint8_t  flags;
    uint32_t pressed_since_ms;
    uint16_t t_hold_ms;
} ui_ctl_state_t;

enum { ENGINE_VA, ENGINE_FM, ENGINE_RP, ENGINE_SMP };   /* SMP: il campionatore di Stame (20 §7b) */
enum { PERF_OFF, PERF_STRUM, PERF_STRUM2, PERF_SLOP, PERF_ARP, PERF_ARP2, PERF_PATTERN, PERF_HARP, PERF_COUNT };
enum { FX_REV, FX_CHO, FX_ENS, FX_PHA, FX_FLA, FX_DRV, FX_TRM, FX_DLY, FX_FLT, FX_COUNT };
enum { VIEW_REACT, VIEW_CHORD, VIEW_KEYBOARD, VIEW_CHORD_KB, VIEW_NOTES, VIEW_GEEK, VIEW_COUNT };
enum { ARP_UP, ARP_DOWN, ARP_UPDOWN };
typedef struct {
    ui_ctl_state_t st[ENC_COUNT];
    uint8_t  focus, turn_target, push;
    uint8_t  hold, fill;                /* Hold dell'accordo e Fill del Beat tenuto (T1, T4 del pad: MIDI-133) */
    uint8_t  sound_user, sound_num;
    char     sound_name[17];
    uint8_t  sound_engine;
    char     sound_cat[24];
    uint8_t  perf_mode, perf_amount, arp_rate, arp_dir;
    uint8_t  fx_main_type, fx_main_amount;
    struct { uint8_t type, amount; } fx[4];
    uint8_t  bass_on, bass_mode, bass_num;
    char     bass_name[17];
    uint8_t  volume, bass_volume;
    uint8_t  view;
} ui_controls_t;

/* ---- 2.5 livelli (UI-025) ---- */
typedef enum { OV_NONE, OV_VOLUME, OV_BASS_VOLUME, OV_BEAT_VOLUME, OV_BATTERY, OV_SOUND, OV_PERFORM,
               OV_ARP, OV_FX, OV_KEY, OV_KEY_TOGGLE, OV_TRANSPOSE, OV_BPM, OV_BASS_SOUND,
               OV_BASS_TOGGLE, OV_VOICING, OV_BASS_VOICING, OV_SINGLE_NOTES, OV_COUNT_IN,
               OV_SAVED, OV_DRUMS, OV_LOW_BATTERY, OV_KIT, OV_ROLL, OV_ACCENT,
               OV_DENSITY, OV_GROOVE, OV_VARIATION, OV_DRUM_LOOP,   /* MIDI-139 */
               OV_SWING, OV_DRIVE, OV_FILTER } ui_ov_kind_t;        /* MIDI-135: K4, K3 e K3 premuta sotto DRUMS */
typedef struct { uint8_t kind, enc; int16_t value; uint32_t until_ms; } ui_overlay_t;

#define UI_LIST_WIN 9
typedef enum { MK_NONE, MK_CHECK, MK_DOT, MK_INDEX, MK_SUBMENU } ui_mark_t;
typedef struct {
    char    label[24];
    char    num[4];
    char    value[12];
    char    info[24];
    uint8_t mark, enabled;
} ui_item_t;

typedef enum { LS_SOUND, LS_PERFORM, LS_FX, LS_BASS, LS_BEATS, LS_SAVE_SOUND, LS_SAVE_LOOP,
               LS_SLOTS, LS_OPTIONS, LS_WAITING_ROOM, LS_PLATFORM, LS_MPK_STATUS, LS_VERSION,
               LS_KITS } ui_list_kind_t;                       /* la lista dei kit sotto DRUMS (30 UI-177) */
#define OWN_PLATFORM 0xFE
typedef struct {
    uint8_t   open, owner, kind;
    char      path[48];
    uint16_t  n, sel, win_first;
    ui_item_t win[UI_LIST_WIN];
    uint8_t   editing;
} ui_list_t;

enum { BASE_BOOT, BASE_PLAY, BASE_LOOPER };
enum { PROMPT_NONE, PROMPT_SELECT_KEY };
/* pagina della plancia (UI-142): mentre si suona, oppure i comandi aperti dai tasti della Flip */
enum { PAGE_PLAY, PAGE_CONTROLS };
typedef struct {
    uint8_t      base;
    ui_overlay_t ov;
    ui_list_t    list;
    uint8_t      prompt;
    uint8_t      platform_menu;
    uint8_t      page;
} ui_layer_t;

/* ---- 2.6 meter (UI-026) ---- */
typedef struct {
    uint8_t  voices_used, voices_bass;
    uint16_t peak[2];
    uint32_t clip_count;
    uint8_t  dsp_load_pct, dsp_load_max_pct;
    uint32_t xrun_count;
    const int16_t *scope;
    uint16_t scope_len;
    const volatile uint32_t *scope_wr;
} ui_meters_t;

/* ---- 2.7 preferenze e piattaforma (UI-027) ---- */
enum { THEME_DARK, THEME_LIGHT, THEME_COUNT };
enum { LBL_OCTAVES, LBL_ALL, LBL_OFF };
typedef struct {
    uint8_t  theme, legend, note_labels, meters, beat_flash, ghost_chord, debug, pocket;
    uint8_t  linnaeus;                  /* 1 = cartellino di Linneo sotto il nome (identità, default 1) */
    uint32_t quit_seq, learn_pad_seq;
} ui_prefs_t;

typedef enum { MPK_ABSENT, MPK_BUSY, MPK_OPEN, MPK_ERROR } ui_mpk_link_t;
typedef enum { PADL_ABSENT, PADL_OPEN, PADL_UNMAPPED, PADL_ERROR } ui_pad_link_t;
enum { MPKP_STAME, MPKP_FACTORY };
enum { MPK_BANK_EST_UNKNOWN, MPK_BANK_EST_A, MPK_BANK_EST_B };
typedef struct {
    uint8_t  mpk_link, pad_link, pad_learn_step;
    uint32_t pad_learned;
    uint8_t  mpk_profile, mpk_bank;
    uint8_t  mpk_model;                 /* 0 Plus, 1 MK4: decide le legende delle celle (UI-152) */
    char     mpk_fw[8];
    char     mpk_last[24];
    uint32_t midi_in_ms, midi_out_ms;
    uint8_t  battery_pct, charging;     /* 255 = sconosciuta */
    uint8_t  audio_backend;
    uint16_t period_frames, periods;
    uint16_t frame_us;
} ui_platform_t;

/* ---- 2.8 avvisi (UI-028) ---- */
typedef enum { MSG_NONE, MSG_INFO, MSG_WARN } ui_msg_level_t;
typedef struct { uint8_t id, level; uint32_t until_ms; char text[64]; } ui_msg_t;

/* ---- avvio (UI-091, UI-159) ---- */
typedef struct {
    uint16_t t_ms;                      /* tempo dall'inizio dell'avvio, per l'animazione del logo */
    char     line[3][48];               /* righe dell'inizializzazione */
    char     version[16];
} ui_boot_t;

typedef struct {
    uint32_t       seq, core_ms, now_ms;
    ui_music_t     music;
    ui_tempo_t     tempo;
    ui_looper_t    looper;
    ui_controls_t  ctl;
    ui_layer_t     layer;
    ui_meters_t    meters;
    ui_prefs_t     prefs;
    ui_platform_t  plat;
    ui_msg_t       msg_core, msg_plat;
    ui_boot_t      boot;
} ui_model_t;

_Static_assert(sizeof(ui_model_t) < 4096, "UI-029: ui_model_t sotto i 4 KB");

#endif
