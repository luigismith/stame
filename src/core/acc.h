/* acc.h — motore degli accordi (sezione 10 della specifica).
 *
 * Trasforma gli input logici (tasto, tipo, estensioni, dial) in eventi di nota.
 * C11 puro, deterministico, nessuna allocazione: lo stato acc_state lo alloca
 * il chiamante (ACC-001, ACC-002).
 *
 * Fase F1: accordi, Secret Chords, nomi, voicing, note singole, transpose,
 * Key mode, Play Style e basso (§1–§8). Performance, clock, Beat e looper
 * (§9–§11) arrivano con le fasi successive.
 */
#ifndef STAME_ACC_H
#define STAME_ACC_H

#include "stame_base.h"

/* ---- Costanti (§1.4, §5) ---- */
enum { ACC_DIM, ACC_MIN, ACC_MAJ, ACC_SUS, ACC_TYPE_COUNT };          /* tipi, ordine del pannello */
enum { ACC_E6, ACC_E7MIN, ACC_E7MAJ, ACC_E9, ACC_EXT_COUNT };         /* estensioni 6, m7, M7, 9 */

#define ACC_V_MIN         1
#define ACC_V_MAX         60
#define ACC_V_DEFAULT     24     /* [V] T-02 */
#define ACC_VB_MIN        0
#define ACC_VB_MAX        48
#define ACC_VB_DEFAULT    23     /* [V] T-02 */
#define ACC_W_OFFSET      24     /* W = v + 24   [V] T-02 */
#define ACC_WB_OFFSET     13     /* WB = vb + 13 [V] T-02 */
#define ACC_TRANSPOSE_MIN (-12)  /* [V] T-14 */
#define ACC_TRANSPOSE_MAX 12
#define ACC_VEL_FIXED     100    /* Velocity Sense Off [V] T-10 */
#define ACC_KEY_COUNT     42
#define ACC_MAX_NOTES     12     /* note distinte di una voicing (pitch class) */

typedef enum { ACC_STYLE_SIMPLE, ACC_STYLE_ADVANCED, ACC_STYLE_FREE } acc_style;
typedef enum { ACC_EXTADD_ADD_NOTE, ACC_EXTADD_PLAY_CHORD } acc_extadd;
typedef enum { ACC_SECRET_OFF, ACC_SECRET_SIMPLE_ONLY, ACC_SECRET_ALL } acc_secret_opt;
typedef enum { ACC_SINGLE_SPLIT, ACC_SINGLE_FULL_OCTAVE } acc_single_opt;
typedef enum { ACC_BASS_CHORDS_ONLY, ACC_BASS_UNISON, ACC_BASS_SINGLE_NOTES, ACC_BASS_SOLO } acc_bass_mode;

/* ---- Input logici (§1.2, ACC-005) ---- */
typedef enum {
    ACC_IN_KEY_DOWN,            /* a = k 0..11, b = vel 1..127 */
    ACC_IN_KEY_UP,              /* a = k */
    ACC_IN_TYPE_DOWN,           /* a = tipo */
    ACC_IN_TYPE_UP,
    ACC_IN_EXT_DOWN,            /* a = estensione */
    ACC_IN_EXT_UP,
    ACC_IN_VOICING_STEP,        /* b = scatti con segno */
    ACC_IN_BASS_VOICING_STEP,   /* b = scatti con segno */
    ACC_IN_SINGLE_NOTES_TOGGLE,
    ACC_IN_KEY_MODE_TOGGLE,
    ACC_IN_KEY_SELECT,          /* a = indice 0..41 */
    ACC_IN_TRANSPOSE_STEP,      /* b = semitoni con segno */
    ACC_IN_BASS_TOGGLE,
    ACC_IN_BASS_MODE_SET,       /* a = acc_bass_mode */
    ACC_IN_OPTION_SET           /* a = acc_option, b = valore */
} acc_in_type;

typedef enum {
    ACC_OPT_PLAY_STYLE, ACC_OPT_EXT_ADD, ACC_OPT_SECRET, ACC_OPT_SINGLE_NOTES,
    ACC_OPT_VEL_SENSE, ACC_OPT_BASS_MODE, ACC_OPT_BASS_ON, ACC_OPT_KEY_ON,
    ACC_OPT_KEY_INDEX, ACC_OPT_TRANSPOSE, ACC_OPT_VOICING, ACC_OPT_BASS_VOICING,
    ACC_OPT_COMPAT_DIM7_TRUE,          /* ACC-023 */
    ACC_OPT_COMPAT_PARTIAL_RETRIGGER,  /* ACC-077 */
    ACC_OPT_COMPAT_FREE_2025,          /* ACC-115 */
    ACC_OPT_COUNT
} acc_option;

typedef struct {
    uint32_t offset;   /* campione nel blocco corrente */
    uint8_t  type;     /* acc_in_type */
    uint8_t  a;
    int16_t  b;
} acc_in;

/* ---- Uscita (§1.3, ACC-008) ---- */
typedef enum { ACC_ROLE_TREBLE, ACC_ROLE_BASS, ACC_ROLE_CHORD_BLOCK, ACC_ROLE_DRUM } acc_role;

typedef struct {
    uint32_t offset;
    uint8_t  role;     /* acc_role */
    uint8_t  note;     /* nota MIDI dopo il transpose */
    uint8_t  vel;      /* 1..127 per note-on, 0 per note-off */
    uint8_t  on;
} acc_note_ev;

/* ---- Nome strutturato (§4, ACC-050) ---- */
typedef enum { ACC_ACC_NONE, ACC_ACC_SHARP, ACC_ACC_FLAT, ACC_ACC_DSHARP, ACC_ACC_DFLAT } acc_accidental;
typedef struct { char letter; uint8_t acc; } acc_spelled;
typedef struct {
    acc_spelled root;
    char    quality[5];   /* "", "m", "sus", "dim", "+", "7#" */
    char    sup[6];       /* "", "6", "9", "7", "m7", "M7", "76", …, "JAZZ", "WTF", "5", "add4", "m6" */
    uint8_t has_slash;
    acc_spelled slash;
    uint8_t single;       /* 1 = nota singola: solo radice + numero di nota (ACC-051) */
    uint8_t single_note;
} acc_chord_name;

/* ---- Accordo risolto (ACC-111) ---- */
enum { ACC_KIND_NONE, ACC_KIND_SINGLE, ACC_KIND_CHORD, ACC_KIND_KEYCHORD };

typedef struct {
    uint8_t  kind;          /* ACC_KIND_* */
    uint8_t  from_type;     /* viene da un tipo (o Secret), non dalla Key mode */
    uint8_t  root_pc;       /* fondamentale per il nome, non trasposta */
    uint8_t  bass_pc;
    uint16_t pcs;           /* maschera assoluta delle pitch class */
    uint8_t  type;          /* CHORD normale: tipo usato */
    int8_t   secret;        /* indice del Secret Chord o -1 */
    uint8_t  exts;          /* estensioni al momento della risoluzione */
    uint8_t  key_quality;   /* KEYCHORD: tipo riconosciuto dalla triade */
    uint8_t  key_seventh_iv;/* KEYCHORD: intervallo settima → radice */
    uint8_t  has_slash;
    uint8_t  slash_pc;
} acc_resolved;

/* ---- Stato ---- */
typedef struct {
    uint8_t n;
    uint8_t note[ACC_MAX_NOTES];   /* crescenti, già trasposte */
} acc_notes;

typedef struct {
    /* opzioni (§1.4) */
    uint8_t style, ext_add, secret, single_notes, vel_sense, bass_mode, bass_on, key_on, key_index;
    int8_t  transpose;
    uint8_t v, vb;
    uint8_t compat_dim7_true, compat_partial_retrigger, compat_free_2025;

    /* ingressi tenuti */
    uint16_t keys_held;              /* bit k = tasto fisicamente premuto */
    int8_t   key;                    /* tasto attivo, -1 = nessuno (ACC-082) */
    uint8_t  key_vel;                /* velocity dell'attacco, dopo ACC-014 */
    uint8_t  types_order[ACC_TYPE_COUNT];   /* tipi tenuti in ordine di pressione */
    uint8_t  n_types;
    uint8_t  exts;                   /* bit e = estensione tenuta */
    uint8_t  locked;                 /* solo ADVANCED (ACC-113) */

    /* accordo corrente e nome (ACC-012) */
    uint8_t      sounding;           /* il tasto attivo sta suonando qualcosa */
    acc_resolved res;
    acc_chord_name name;
    uint8_t      has_name;

    /* note aperte, come emesse (già trasposte) */
    acc_notes treble;                /* ruolo TREBLE */
    acc_notes block;                 /* ruolo CHORD_BLOCK */
    int16_t  bass_note;              /* -1 = nessuna */

    /* uscita del blocco corrente */
    acc_note_ev *out;
    int out_n, out_max, out_dropped;
} acc_state;

void acc_init(acc_state *s);

/* Elabora gli input del blocco nell'ordine dato (ACC-006) e scrive gli eventi in out.
 * Ritorna quanti eventi ha scritto; quelli oltre max si scartano e si contano in
 * out_dropped. */
int acc_process(acc_state *s, const acc_in *in, int n_in, acc_note_ev *out, int max);

/* Comodità: un solo input. */
int acc_input(acc_state *s, uint8_t type, uint8_t a, int16_t b, uint32_t offset,
              acc_note_ev *out, int max);

/* Valore attuale di un'opzione (acc_option), per i salvataggi; 0 per un'opzione sconosciuta. */
int acc_option_get(const acc_state *s, int opt);

/* ---- Funzioni pure, esposte per i test e per l'interfaccia ---- */
int      acc_place(int pc, int w);                                   /* W + ((pc - W) mod 12) */
uint16_t acc_chord_mask(int type, uint8_t exts, bool dim7_true);     /* maschera relativa alla fondamentale */
int      acc_voicing(int root, uint16_t rel_mask, int w, uint8_t *notes);  /* ritorna n; note crescenti */
void     acc_name_normal(acc_chord_name *nm, int type, uint8_t exts); /* solo quality e sup (ACC-052) */
bool     acc_key_in_scale(int key_index, int pc);
int      acc_key_tonic_pc(int key_index);
bool     acc_key_is_minor(int key_index);
int      acc_effective_key(int key_index, int transpose);            /* ACC-055 */
void     acc_key_degree_spelling(int key_index, int degree, acc_spelled *out);   /* ACC-093 */
acc_spelled acc_spell_pc(const acc_state *s, int pc);                /* grafia secondo Key mode e transpose */

/* Rende il nome come testo ASCII (es. "Dm/A", "C#sus^M7", "Cdim^WTF"): per i test e il registro. */
int      acc_name_text(const acc_chord_name *nm, char *buf, int max);

#endif
