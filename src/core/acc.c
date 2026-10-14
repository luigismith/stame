/* acc.c — motore degli accordi: accordi, Secret Chords, nomi, voicing, Key mode,
 * Play Style e basso (sezione 10, §1–§8). */
#include "acc.h"

/* ------------------------------------------------------------------ tabelle */

static const uint16_t ACC_TYPE_MASK[ACC_TYPE_COUNT] STAME_ROM = { 0x049 /*DIM*/, 0x089 /*MIN*/, 0x091 /*MAJ*/, 0x0A1 /*SUS*/ };
static const uint8_t  ACC_EXT_PC[ACC_EXT_COUNT]     STAME_ROM = { 9 /*E6*/, 10 /*E7MIN*/, 11 /*E7MAJ*/, 2 /*E9*/ };
static const char     ACC_QUALITY[ACC_TYPE_COUNT][4] STAME_ROM = { "dim", "m", "", "sus" };

typedef struct { uint8_t types, req_ext, absorbed_ext; uint16_t mask; char base[3], sup[5]; } acc_secret;

#define TB(t) (1u << (t))
#define EB(e) (1u << (e))

/* ACC-040: tabella fissa, non l'unione degli intervalli. */
static const acc_secret ACC_SECRET[6] STAME_ROM = {
    { TB(ACC_DIM) | TB(ACC_SUS), 0,             0,             0x081, "",   "5"    },
    { TB(ACC_MAJ) | TB(ACC_SUS), 0,             0,             0x111, "+",  ""     },
    { TB(ACC_MIN) | TB(ACC_SUS), 0,             0,             0x0A9, "m",  "add4" },
    { TB(ACC_MIN) | TB(ACC_DIM), EB(ACC_E6),    EB(ACC_E6),    0x189, "m",  "m6"   },
    { TB(ACC_MAJ) | TB(ACC_DIM), 0,             EB(ACC_E6),    0x191, "",   "m6"   },
    { TB(ACC_MAJ) | TB(ACC_MIN), EB(ACC_E7MIN), EB(ACC_E7MIN), 0x499, "7#", "9"    },
};

static const uint8_t ACC_SCALE_MAJ[7] STAME_ROM = { 0, 2, 4, 5, 7, 9, 11 };
static const uint8_t ACC_SCALE_MIN[7] STAME_ROM = { 0, 2, 3, 5, 7, 8, 10 };   /* minore naturale (ACC-091) */

static const char    LETTERS[7] STAME_ROM = { 'C', 'D', 'E', 'F', 'G', 'A', 'B' };
static const uint8_t NAT_PC[7]  STAME_ROM = { 0, 2, 4, 5, 7, 9, 11 };

/* ACC-090: 21 radici; indice i = maggiore, i + 21 = minore. letter = indice in LETTERS. */
typedef struct { uint8_t letter; int8_t alter; uint8_t pc; } acc_key_root;
static const acc_key_root KEY_ROOTS[21] STAME_ROM = {
    {0, 0, 0}, {0, 1, 1}, {1, -1, 1}, {1, 0, 2}, {1, 1, 3}, {2, -1, 3}, {2, 0, 4},
    {2, 1, 5}, {3, -1, 4}, {3, 0, 5}, {3, 1, 6}, {4, -1, 6}, {4, 0, 7}, {4, 1, 8},
    {5, -1, 8}, {5, 0, 9}, {5, 1, 10}, {6, -1, 10}, {6, 0, 11}, {6, 1, 0}, {0, -1, 11},
};

/* lettera della grafia con i diesis (ACC-053): pc → indice in LETTERS */
static const uint8_t SHARP_LETTER[12] STAME_ROM = { 0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6 };

/* ----------------------------------------------------------------- utilità */

static int mod12(int a) { int r = a % 12; return r < 0 ? r + 12 : r; }

static int popcount8(unsigned x) { int n = 0; while (x) { n += (int)(x & 1u); x >>= 1; } return n; }

static int clampi(int x, int lo, int hi) { return x < lo ? lo : (x > hi ? hi : x); }

static void str_copy(char *dst, int cap, const char *src)
{
    int i = 0;
    while (src[i] && i < cap - 1) { dst[i] = src[i]; i++; }
    dst[i] = 0;
}

static void str_cat(char *dst, int cap, const char *src)
{
    int i = 0;
    while (dst[i]) i++;
    str_copy(dst + i, cap - i, src);
}

static uint8_t alter_to_acc(int alter)
{
    switch (alter) {
    case 1:  return ACC_ACC_SHARP;
    case -1: return ACC_ACC_FLAT;
    case 2:  return ACC_ACC_DSHARP;
    case -2: return ACC_ACC_DFLAT;
    default: return ACC_ACC_NONE;
    }
}

/* ---------------------------------------------------------- funzioni pure */

int acc_place(int pc, int w) { return w + mod12(pc - w); }

uint16_t acc_chord_mask(int type, uint8_t exts, bool dim7_true)
{
    uint16_t m = ACC_TYPE_MASK[type];
    for (int e = 0; e < ACC_EXT_COUNT; e++) {
        if (!(exts & EB(e))) continue;
        int pc = ACC_EXT_PC[e];
        if (dim7_true && type == ACC_DIM && e == ACC_E7MIN) pc = 9;   /* ACC-023, variante */
        m |= (uint16_t)(1u << pc);
    }
    return m;
}

int acc_voicing(int root, uint16_t rel_mask, int w, uint8_t *notes)
{
    int n = 0;
    for (int i = 0; i < 12; i++)
        if (rel_mask & (1u << i)) notes[n++] = (uint8_t)acc_place(root + i, w);
    /* ordinamento per inserzione: al massimo 12 note */
    for (int i = 1; i < n; i++) {
        uint8_t x = notes[i]; int j = i - 1;
        while (j >= 0 && notes[j] > x) { notes[j + 1] = notes[j]; j--; }
        notes[j + 1] = x;
    }
    return n;
}

/* ACC-052 */
void acc_name_normal(acc_chord_name *nm, int type, uint8_t exts)
{
    str_copy(nm->quality, sizeof nm->quality, ACC_QUALITY[type]);
    nm->sup[0] = 0;
    int n = popcount8(exts);
    if (n == 3) { str_copy(nm->sup, sizeof nm->sup, "JAZZ"); return; }
    if (n == 4) { str_copy(nm->sup, sizeof nm->sup, "WTF");  return; }
    if (exts & EB(ACC_E7MIN)) str_cat(nm->sup, sizeof nm->sup, type == ACC_SUS ? "m7" : "7");
    if (exts & EB(ACC_E7MAJ)) str_cat(nm->sup, sizeof nm->sup, "M7");
    if (exts & EB(ACC_E6))    str_cat(nm->sup, sizeof nm->sup, "6");
    if (exts & EB(ACC_E9))    str_cat(nm->sup, sizeof nm->sup, "9");
}

/* ------------------------------------------------------------------ Key mode */

bool acc_key_is_minor(int key_index) { return key_index >= 21; }
int  acc_key_tonic_pc(int key_index) { return KEY_ROOTS[key_index % 21].pc; }

static const uint8_t *key_scale(int key_index)
{
    return acc_key_is_minor(key_index) ? ACC_SCALE_MIN : ACC_SCALE_MAJ;
}

/* grado (0..6) di pc nella scala, -1 se fuori scala */
static int key_degree(int key_index, int pc)
{
    const uint8_t *sc = key_scale(key_index);
    int rel = mod12(pc - acc_key_tonic_pc(key_index));
    for (int d = 0; d < 7; d++) if (sc[d] == rel) return d;
    return -1;
}

bool acc_key_in_scale(int key_index, int pc) { return key_degree(key_index, pc) >= 0; }

/* ACC-093: alterazione (-2..+2) del grado d; scrive anche l'indice della lettera */
static int degree_alter(int key_index, int d, int *letter_out)
{
    const acc_key_root *r = &KEY_ROOTS[key_index % 21];
    int letter = (r->letter + d) % 7;
    int pc = mod12(r->pc + key_scale(key_index)[d]);
    if (letter_out) *letter_out = letter;
    return mod12(pc - NAT_PC[letter] + 6) - 6;
}

void acc_key_degree_spelling(int key_index, int degree, acc_spelled *out)
{
    int letter;
    int alter = degree_alter(key_index, degree, &letter);
    out->letter = LETTERS[letter];
    out->acc = alter_to_acc(alter);
}

/* somma delle alterazioni della scala (segno) e somma dei valori assoluti */
static int key_alter_sum(int key_index, int *abs_sum)
{
    int sum = 0, as = 0;
    for (int d = 0; d < 7; d++) { int a = degree_alter(key_index, d, NULL); sum += a; as += a < 0 ? -a : a; }
    if (abs_sum) *abs_sum = as;
    return sum;
}

/* ACC-055: fra le tonalità con la tonica trasposta e lo stesso modo, quella con meno
 * alterazioni; a parità, quella con i diesis. */
int acc_effective_key(int key_index, int transpose)
{
    if (transpose == 0) return key_index;
    int base = acc_key_is_minor(key_index) ? 21 : 0;
    int target = mod12(acc_key_tonic_pc(key_index) + transpose);
    int best = -1, best_abs = 0, best_sum = 0;
    for (int i = 0; i < 21; i++) {
        if (KEY_ROOTS[i].pc != target) continue;
        int as, sum = key_alter_sum(base + i, &as);
        if (best < 0 || as < best_abs || (as == best_abs && sum > 0 && best_sum <= 0)) {
            best = base + i; best_abs = as; best_sum = sum;
        }
    }
    return best;
}

/* quantizzazione armonica (ACC-094): la nota fuori scala scende di un semitono */
static int key_q(int key_index, int p)
{
    p = mod12(p);
    return acc_key_in_scale(key_index, p) ? p : mod12(p - 1);
}

/* ------------------------------------------------------------------- grafia */

acc_spelled acc_spell_pc(const acc_state *s, int pc)
{
    acc_spelled sp;
    pc = mod12(pc);
    if (!s->key_on) {                                   /* ACC-053: diesis */
        int l = SHARP_LETTER[pc];
        sp.letter = LETTERS[l];
        sp.acc = NAT_PC[l] == pc ? ACC_ACC_NONE : ACC_ACC_SHARP;
        return sp;
    }
    int ek = acc_effective_key(s->key_index, s->transpose);
    int d = key_degree(ek, pc);
    if (d >= 0) { acc_key_degree_spelling(ek, d, &sp); return sp; }
    /* ACC-054, fuori scala: una nota naturale resta naturale [D]; altrimenti bemolle
     * sulla lettera superiore se la tonalità è in bemolli, diesis sulla inferiore se no */
    for (int l = 0; l < 7; l++)
        if (NAT_PC[l] == pc) { sp.letter = LETTERS[l]; sp.acc = ACC_ACC_NONE; return sp; }
    if (key_alter_sum(ek, NULL) < 0) {
        int l = SHARP_LETTER[mod12(pc + 1)];
        sp.letter = LETTERS[l]; sp.acc = ACC_ACC_FLAT;
    } else {
        int l = SHARP_LETTER[pc];
        sp.letter = LETTERS[l]; sp.acc = ACC_ACC_SHARP;
    }
    return sp;
}

int acc_name_text(const acc_chord_name *nm, char *buf, int max)
{
    static const char *const ACC_TXT[5] = { "", "#", "b", "x", "bb" };
    char tmp[32];
    tmp[0] = nm->root.letter; tmp[1] = 0;
    str_cat(tmp, sizeof tmp, ACC_TXT[nm->root.acc]);
    if (!nm->single) {
        str_cat(tmp, sizeof tmp, nm->quality);
        if (nm->sup[0]) { str_cat(tmp, sizeof tmp, "^"); str_cat(tmp, sizeof tmp, nm->sup); }
        if (nm->has_slash) {
            char sl[3] = { '/', nm->slash.letter, 0 };
            str_cat(tmp, sizeof tmp, sl);
            str_cat(tmp, sizeof tmp, ACC_TXT[nm->slash.acc]);
        }
    }
    str_copy(buf, max, tmp);
    int n = 0; while (buf[n]) n++;
    return n;
}

/* ------------------------------------------------------------- risoluzione */

static bool secret_allowed(const acc_state *s)
{
    return s->secret == ACC_SECRET_ALL || (s->secret == ACC_SECRET_SIMPLE_ONLY && s->style == ACC_STYLE_SIMPLE);
}

static uint16_t rotate_mask(uint16_t rel, int root)
{
    uint16_t m = 0;
    for (int i = 0; i < 12; i++) if (rel & (1u << i)) m |= (uint16_t)(1u << mod12(root + i));
    return m;
}

/* ACC-097: radice e qualità dalla triade di Key mode, con l'eventuale slash */
static void key_name_from_notes(acc_resolved *r, uint16_t triad, int b)
{
    uint8_t cand[3]; int nc = 0;
    cand[nc++] = (uint8_t)b;
    for (int iv = 1; iv < 12; iv++)
        if (triad & (1u << mod12(b + iv))) cand[nc++] = (uint8_t)mod12(b + iv);
    r->root_pc = (uint8_t)b; r->key_quality = ACC_MAJ;
    for (int i = 0; i < nc; i++) {
        uint16_t rel = 0;
        for (int p = 0; p < 12; p++) if (triad & (1u << p)) rel |= (uint16_t)(1u << mod12(p - cand[i]));
        int t = -1;
        for (int k = 0; k < ACC_TYPE_COUNT; k++) if (ACC_TYPE_MASK[k] == rel) t = k;
        if (t >= 0) { r->root_pc = cand[i]; r->key_quality = (uint8_t)t; break; }
    }
    r->has_slash = r->root_pc != b;
    r->slash_pc = (uint8_t)b;
}

/* ACC-111 */
static acc_resolved resolve(const acc_state *s, int k)
{
    acc_resolved r;
    memset(&r, 0, sizeof r);
    r.secret = -1;
    r.exts = s->exts;

    if (s->n_types >= 2 && secret_allowed(s)) {
        uint8_t types = 0;
        for (int i = 0; i < s->n_types; i++) types |= (uint8_t)TB(s->types_order[i]);
        for (int i = 0; i < (int)STAME_COUNT(ACC_SECRET); i++) {
            const acc_secret *sc = &ACC_SECRET[i];
            if (sc->types != types || (s->exts & sc->req_ext) != sc->req_ext) continue;   /* ACC-042, ACC-043 */
            uint16_t rel = sc->mask;
            uint8_t extra = s->exts & (uint8_t)~(sc->req_ext | sc->absorbed_ext);       /* ACC-044 */
            for (int e = 0; e < ACC_EXT_COUNT; e++) if (extra & EB(e)) rel |= (uint16_t)(1u << ACC_EXT_PC[e]);
            r.kind = ACC_KIND_CHORD; r.from_type = 1; r.secret = (int8_t)i;
            r.root_pc = r.bass_pc = (uint8_t)k;                                           /* ACC-045 */
            r.pcs = rotate_mask(rel, k);
            return r;
        }
    }
    if (s->n_types > 0) {
        int t = s->types_order[s->n_types - 1];          /* ACC-025: l'ultimo premuto */
        r.kind = ACC_KIND_CHORD; r.from_type = 1; r.type = (uint8_t)t;
        r.root_pc = r.bass_pc = (uint8_t)k;
        r.pcs = rotate_mask(acc_chord_mask(t, s->exts, s->compat_dim7_true), k);
        return r;
    }
    if (s->key_on) {
        int key = s->key_index, tonic = acc_key_tonic_pc(key);
        const uint8_t *sc = key_scale(key);
        int qk = key_q(key, k);
        uint16_t triad = (uint16_t)((1u << qk) | (1u << key_q(key, k + 4)) | (1u << key_q(key, k + 7)));
        r.kind = ACC_KIND_KEYCHORD;
        r.bass_pc = (uint8_t)qk;
        r.pcs = triad;
        key_name_from_notes(&r, triad, qk);
        int d = key_degree(key, qk);                      /* ACC-096: estensioni diatoniche */
        for (int e = 0; e < ACC_EXT_COUNT; e++) {
            if (!(s->exts & EB(e))) continue;
            int step = e == ACC_E6 ? 5 : (e == ACC_E9 ? 1 : 6);
            int pc = mod12(tonic + sc[(d + step) % 7]);
            r.pcs |= (uint16_t)(1u << pc);
            if (e == ACC_E7MIN || e == ACC_E7MAJ) r.key_seventh_iv = (uint8_t)mod12(pc - r.root_pc);
        }
        return r;
    }
    r.kind = ACC_KIND_SINGLE;                             /* ACC-024: le estensioni sono ignorate */
    r.root_pc = r.bass_pc = (uint8_t)k;
    r.pcs = (uint16_t)(1u << k);
    return r;
}

static void build_name(const acc_state *s, const acc_resolved *r, int note, acc_chord_name *nm)
{
    memset(nm, 0, sizeof *nm);
    nm->root = acc_spell_pc(s, r->root_pc + s->transpose);       /* ACC-055 */
    if (r->kind == ACC_KIND_SINGLE) {
        nm->single = 1;
        nm->single_note = (uint8_t)clampi(note, 0, 127);
        return;
    }
    if (r->kind == ACC_KIND_CHORD) {
        if (r->secret >= 0) {
            str_copy(nm->quality, sizeof nm->quality, ACC_SECRET[r->secret].base);
            str_copy(nm->sup, sizeof nm->sup, ACC_SECRET[r->secret].sup);
        } else {
            acc_name_normal(nm, r->type, r->exts);
        }
        return;
    }
    /* ACC_KIND_KEYCHORD (ACC-097) */
    str_copy(nm->quality, sizeof nm->quality, ACC_QUALITY[r->key_quality]);
    bool has7 = (r->exts & (EB(ACC_E7MIN) | EB(ACC_E7MAJ))) != 0;
    int n = (has7 ? 1 : 0) + ((r->exts & EB(ACC_E6)) ? 1 : 0) + ((r->exts & EB(ACC_E9)) ? 1 : 0);
    if (n == 3) {
        str_copy(nm->sup, sizeof nm->sup, "JAZZ");
    } else {
        if (has7) str_cat(nm->sup, sizeof nm->sup,
                          r->key_seventh_iv == 11 ? "M7" : (r->key_quality == ACC_SUS ? "m7" : "7"));
        if (r->exts & EB(ACC_E6)) str_cat(nm->sup, sizeof nm->sup, "6");
        if (r->exts & EB(ACC_E9)) str_cat(nm->sup, sizeof nm->sup, "9");
    }
    if (r->has_slash) { nm->has_slash = 1; nm->slash = acc_spell_pc(s, r->slash_pc + s->transpose); }
}

/* ------------------------------------------------------------ note di uscita */

static int win_w(const acc_state *s)  { return s->v + ACC_W_OFFSET; }
static int win_wb(const acc_state *s) { return s->vb + ACC_WB_OFFSET; }

/* nota singola (ACC-080), non trasposta */
static int single_note(const acc_state *s, int k)
{
    int w = win_w(s);
    return s->single_notes == ACC_SINGLE_FULL_OCTAVE ? 12 * (w / 12) + k : acc_place(k, w);
}

static void notes_add(acc_notes *n, int note)
{
    if (note < 0 || note > 127 || n->n >= ACC_MAX_NOTES) return;   /* ACC-083: fuori gamma si scarta */
    n->note[n->n++] = (uint8_t)note;
}

static bool notes_has(const acc_notes *n, uint8_t note)
{
    for (int i = 0; i < n->n; i++) if (n->note[i] == note) return true;
    return false;
}

static bool notes_equal(const acc_notes *a, const acc_notes *b)
{
    if (a->n != b->n) return false;
    for (int i = 0; i < a->n; i++) if (a->note[i] != b->note[i]) return false;
    return true;
}

/* Note treble e di basso da far suonare per r (ACC-144, ACC-145), già trasposte. */
static void target_notes(const acc_state *s, const acc_resolved *r, int k, acc_notes *treble, int *bass)
{
    treble->n = 0;
    *bass = -1;
    if (r->kind == ACC_KIND_NONE) return;
    bool treble_on, bass_on = s->bass_on != 0;
    if (r->kind == ACC_KIND_SINGLE) {
        switch (s->bass_mode) {
        case ACC_BASS_CHORDS_ONLY:  treble_on = true; bass_on = false; break;
        case ACC_BASS_UNISON:       treble_on = true; break;
        case ACC_BASS_SINGLE_NOTES: treble_on = !bass_on; break;
        default /* SOLO */:         treble_on = false; break;
        }
    } else {
        treble_on = s->bass_mode != ACC_BASS_SOLO;
    }
    if (treble_on) {
        if (r->kind == ACC_KIND_SINGLE) {
            notes_add(treble, single_note(s, k) + s->transpose);
        } else {
            uint8_t tmp[ACC_MAX_NOTES];
            int n = acc_voicing(0, r->pcs, win_w(s), tmp);
            for (int i = 0; i < n; i++) notes_add(treble, tmp[i] + s->transpose);
        }
    }
    if (bass_on) {
        int nb = acc_place(r->bass_pc, win_wb(s)) + s->transpose;   /* ACC-140 */
        if (nb >= 0 && nb <= 127) *bass = nb;
    }
}

/* ------------------------------------------------------------------ emissione */

static void emit(acc_state *s, uint32_t off, int role, int note, int vel, int on)
{
    if (s->out_n >= s->out_max) { s->out_dropped++; return; }
    acc_note_ev *e = &s->out[s->out_n++];
    e->offset = off; e->role = (uint8_t)role; e->note = (uint8_t)note;
    e->vel = (uint8_t)(on ? vel : 0); e->on = (uint8_t)on;
}

enum { TR_FULL, TR_PARTIAL, TR_ADD };
enum { BASS_KEEP_IF_SAME, BASS_RETRIGGER, BASS_OFF_ON };

/* Porta treble e chord block dalle note aperte a nt (ACC-009, ACC-010, ACC-077, ACC-116). */
static void move_treble(acc_state *s, uint32_t off, const acc_notes *nt, int mode)
{
    if (mode == TR_ADD) {
        for (int i = 0; i < s->treble.n; i++)
            if (!notes_has(nt, s->treble.note[i])) { mode = TR_FULL; break; }   /* non è una pura aggiunta */
    }
    if (mode == TR_FULL) {
        for (int i = 0; i < s->block.n; i++)  emit(s, off, ACC_ROLE_CHORD_BLOCK, s->block.note[i], 0, 0);
        for (int i = 0; i < s->treble.n; i++) emit(s, off, ACC_ROLE_TREBLE, s->treble.note[i], 0, 0);
        for (int i = 0; i < nt->n; i++) emit(s, off, ACC_ROLE_CHORD_BLOCK, nt->note[i], s->key_vel, 1);
        for (int i = 0; i < nt->n; i++) emit(s, off, ACC_ROLE_TREBLE, nt->note[i], s->key_vel, 1);
    } else {
        if (mode == TR_PARTIAL) {
            for (int i = 0; i < s->block.n; i++)
                if (!notes_has(nt, s->block.note[i])) emit(s, off, ACC_ROLE_CHORD_BLOCK, s->block.note[i], 0, 0);
            for (int i = 0; i < s->treble.n; i++)
                if (!notes_has(nt, s->treble.note[i])) emit(s, off, ACC_ROLE_TREBLE, s->treble.note[i], 0, 0);
        }
        for (int i = 0; i < nt->n; i++)
            if (!notes_has(&s->block, nt->note[i])) emit(s, off, ACC_ROLE_CHORD_BLOCK, nt->note[i], s->key_vel, 1);
        for (int i = 0; i < nt->n; i++)
            if (!notes_has(&s->treble, nt->note[i])) emit(s, off, ACC_ROLE_TREBLE, nt->note[i], s->key_vel, 1);
    }
    s->treble = *nt;
    s->block = *nt;
}

/* ACC-147 (legato: prima il nuovo note-on), ACC-078 */
static void move_bass(acc_state *s, uint32_t off, int nb, int policy)
{
    int ob = s->bass_note;
    if (ob >= 0 && nb >= 0) {
        if (ob == nb) {
            if (policy == BASS_KEEP_IF_SAME) return;
            emit(s, off, ACC_ROLE_BASS, ob, 0, 0);
            emit(s, off, ACC_ROLE_BASS, nb, s->key_vel, 1);
        } else if (policy == BASS_OFF_ON) {
            emit(s, off, ACC_ROLE_BASS, ob, 0, 0);
            emit(s, off, ACC_ROLE_BASS, nb, s->key_vel, 1);
        } else {
            emit(s, off, ACC_ROLE_BASS, nb, s->key_vel, 1);
            emit(s, off, ACC_ROLE_BASS, ob, 0, 0);
        }
    } else if (ob >= 0) {
        emit(s, off, ACC_ROLE_BASS, ob, 0, 0);
    } else if (nb >= 0) {
        emit(s, off, ACC_ROLE_BASS, nb, s->key_vel, 1);
    }
    s->bass_note = (int16_t)nb;
}

static void refresh_name(acc_state *s)
{
    build_name(s, &s->res, single_note(s, s->key < 0 ? 0 : s->key) + s->transpose, &s->name);
    s->has_name = 1;
}

/* Risolve il tasto attivo e lo fa suonare. */
static void play(acc_state *s, uint32_t off, int tr_mode, int bass_policy)
{
    acc_resolved r = resolve(s, s->key);
    acc_notes nt; int nb;
    target_notes(s, &r, s->key, &nt, &nb);
    move_treble(s, off, &nt, tr_mode);
    move_bass(s, off, nb, bass_policy);
    s->res = r;
    refresh_name(s);
    s->sounding = 1;
}

static void all_off(acc_state *s, uint32_t off)
{
    acc_notes none; none.n = 0;
    move_treble(s, off, &none, TR_FULL);
    move_bass(s, off, -1, BASS_KEEP_IF_SAME);
    s->sounding = 0;
}

/* Ricalcola le note dello stesso accordo dopo un cambio di voicing, Split/Octave o
 * transpose; ri-attacca solo ciò che cambia (ACC-077, ACC-081, ACC-085). */
static void revoice(acc_state *s, uint32_t off, bool bass_too)
{
    if (!s->sounding || s->key < 0) return;
    acc_notes nt; int nb;
    target_notes(s, &s->res, s->key, &nt, &nb);
    if (!notes_equal(&nt, &s->treble))
        move_treble(s, off, &nt, s->compat_partial_retrigger ? TR_PARTIAL : TR_FULL);
    if (bass_too && nb != s->bass_note) move_bass(s, off, nb, BASS_OFF_ON);
    refresh_name(s);
}

/* ---------------------------------------------------------------- comandi */

static void type_remove(acc_state *s, int t)
{
    int j = 0;
    for (int i = 0; i < s->n_types; i++) if (s->types_order[i] != t) s->types_order[j++] = s->types_order[i];
    s->n_types = (uint8_t)j;
}

static bool type_held(const acc_state *s, int t)
{
    for (int i = 0; i < s->n_types; i++) if (s->types_order[i] == t) return true;
    return false;
}

static void set_option(acc_state *s, int opt, int val)
{
    switch (opt) {
    case ACC_OPT_PLAY_STYLE:   s->style = (uint8_t)clampi(val, 0, 2); break;
    case ACC_OPT_EXT_ADD:      s->ext_add = (uint8_t)clampi(val, 0, 1); break;
    case ACC_OPT_SECRET:       s->secret = (uint8_t)clampi(val, 0, 2); break;
    case ACC_OPT_SINGLE_NOTES: s->single_notes = (uint8_t)clampi(val, 0, 1); break;
    case ACC_OPT_VEL_SENSE:    s->vel_sense = val != 0; break;
    case ACC_OPT_BASS_MODE:    s->bass_mode = (uint8_t)clampi(val, 0, 3); break;
    case ACC_OPT_BASS_ON:      s->bass_on = val != 0; break;
    case ACC_OPT_KEY_ON:       s->key_on = val != 0; break;
    case ACC_OPT_KEY_INDEX:    s->key_index = (uint8_t)clampi(val, 0, ACC_KEY_COUNT - 1); break;
    case ACC_OPT_TRANSPOSE:    s->transpose = (int8_t)clampi(val, ACC_TRANSPOSE_MIN, ACC_TRANSPOSE_MAX); break;
    case ACC_OPT_VOICING:      s->v = (uint8_t)clampi(val, ACC_V_MIN, ACC_V_MAX); break;
    case ACC_OPT_BASS_VOICING: s->vb = (uint8_t)clampi(val, ACC_VB_MIN, ACC_VB_MAX); break;
    case ACC_OPT_COMPAT_DIM7_TRUE:         s->compat_dim7_true = val != 0; break;
    case ACC_OPT_COMPAT_PARTIAL_RETRIGGER: s->compat_partial_retrigger = val != 0; break;
    case ACC_OPT_COMPAT_FREE_2025:         s->compat_free_2025 = val != 0; break;
    default: break;
    }
}

int acc_option_get(const acc_state *s, int opt)
{
    switch (opt) {
    case ACC_OPT_PLAY_STYLE:   return s->style;
    case ACC_OPT_EXT_ADD:      return s->ext_add;
    case ACC_OPT_SECRET:       return s->secret;
    case ACC_OPT_SINGLE_NOTES: return s->single_notes;
    case ACC_OPT_VEL_SENSE:    return s->vel_sense;
    case ACC_OPT_BASS_MODE:    return s->bass_mode;
    case ACC_OPT_BASS_ON:      return s->bass_on;
    case ACC_OPT_KEY_ON:       return s->key_on;
    case ACC_OPT_KEY_INDEX:    return s->key_index;
    case ACC_OPT_TRANSPOSE:    return s->transpose;
    case ACC_OPT_VOICING:      return s->v;
    case ACC_OPT_BASS_VOICING: return s->vb;
    case ACC_OPT_COMPAT_DIM7_TRUE:         return s->compat_dim7_true;
    case ACC_OPT_COMPAT_PARTIAL_RETRIGGER: return s->compat_partial_retrigger;
    case ACC_OPT_COMPAT_FREE_2025:         return s->compat_free_2025;
    default: return 0;
    }
}

static void handle(acc_state *s, const acc_in *in)
{
    uint32_t off = in->offset;
    int a = in->a, b = in->b;

    switch (in->type) {
    case ACC_IN_KEY_DOWN: {
        if (a > 11 || (s->keys_held & (1u << a))) return;          /* ACC-007 */
        s->keys_held |= (uint16_t)(1u << a);
        bool had = s->sounding != 0;
        s->key = (int8_t)a;
        s->key_vel = (uint8_t)(s->vel_sense ? clampi(b, 1, 127) : ACC_VEL_FIXED);   /* ACC-014 */
        s->locked = 0;
        play(s, off, TR_FULL, had ? BASS_RETRIGGER : BASS_KEEP_IF_SAME);           /* ACC-082 */
        return;
    }
    case ACC_IN_KEY_UP:
        if (a > 11 || !(s->keys_held & (1u << a))) return;         /* ACC-007 */
        s->keys_held &= (uint16_t)~(1u << a);
        if (a != s->key) return;                                    /* tasto già sostituito (ACC-082) */
        all_off(s, off);
        s->key = -1;
        s->locked = 0;
        return;

    case ACC_IN_TYPE_DOWN:
        if (a >= ACC_TYPE_COUNT || type_held(s, a)) return;
        s->types_order[s->n_types++] = (uint8_t)a;
        if (s->key < 0 || s->style == ACC_STYLE_SIMPLE) return;     /* ACC-112: vale dal tasto successivo */
        if (s->style == ACC_STYLE_ADVANCED && s->locked) return;    /* ACC-113 */
        play(s, off, TR_FULL, BASS_KEEP_IF_SAME);                   /* ri-attacco (ACC-113, ACC-114) */
        return;

    case ACC_IN_TYPE_UP:
        if (a >= ACC_TYPE_COUNT || !type_held(s, a)) return;
        type_remove(s, a);
        if (s->key < 0 || s->n_types > 0 || !s->res.from_type) return;
        if (s->style == ACC_STYLE_ADVANCED) s->locked = 1;          /* ACC-113 */
        else if (s->style == ACC_STYLE_FREE && s->compat_free_2025)
            play(s, off, TR_FULL, BASS_KEEP_IF_SAME);               /* ACC-115: torna la nota singola */
        return;

    case ACC_IN_EXT_DOWN:
        if (a >= ACC_EXT_COUNT || (s->exts & EB(a))) return;
        s->exts |= (uint8_t)EB(a);
        if (s->key < 0 || s->style == ACC_STYLE_SIMPLE || !s->sounding) return;
        if (s->locked || s->res.kind == ACC_KIND_SINGLE) return;              /* ACC-113 */
        if (s->n_types == 0 && s->res.kind != ACC_KIND_KEYCHORD) return;      /* ACC-114 */
        play(s, off, s->ext_add == ACC_EXTADD_ADD_NOTE ? TR_ADD : TR_FULL, BASS_KEEP_IF_SAME);   /* ACC-116 */
        return;

    case ACC_IN_EXT_UP:
        if (a < ACC_EXT_COUNT) s->exts &= (uint8_t)~EB(a);          /* nessun effetto sul suono */
        return;

    case ACC_IN_VOICING_STEP: {
        int nv = clampi(s->v + b, ACC_V_MIN, ACC_V_MAX);           /* ACC-072: saturazione */
        if (nv == s->v) return;
        s->v = (uint8_t)nv;
        revoice(s, off, false);
        return;
    }
    case ACC_IN_BASS_VOICING_STEP: {
        int nv = clampi(s->vb + b, ACC_VB_MIN, ACC_VB_MAX);
        if (nv == s->vb) return;
        s->vb = (uint8_t)nv;
        revoice(s, off, true);                                      /* ACC-078 */
        return;
    }
    case ACC_IN_SINGLE_NOTES_TOGGLE:
        s->single_notes = s->single_notes == ACC_SINGLE_SPLIT ? ACC_SINGLE_FULL_OCTAVE : ACC_SINGLE_SPLIT;
        if (s->res.kind == ACC_KIND_SINGLE) revoice(s, off, false); /* ACC-081 */
        return;

    case ACC_IN_KEY_MODE_TOGGLE:
        s->key_on = !s->key_on;                                      /* ACC-100: vale dal tasto successivo */
        return;
    case ACC_IN_KEY_SELECT:
        if (a < ACC_KEY_COUNT) s->key_index = (uint8_t)a;
        return;

    case ACC_IN_TRANSPOSE_STEP: {
        int nt = clampi(s->transpose + b, ACC_TRANSPOSE_MIN, ACC_TRANSPOSE_MAX);
        if (nt == s->transpose) return;
        s->transpose = (int8_t)nt;
        revoice(s, off, true);                                      /* ACC-085, ACC-055 */
        return;
    }
    case ACC_IN_BASS_TOGGLE:
        s->bass_on = !s->bass_on;
        if (!s->bass_on && s->bass_note >= 0) move_bass(s, off, -1, BASS_KEEP_IF_SAME);   /* ACC-148 */
        return;
    case ACC_IN_BASS_MODE_SET:
        if (a <= ACC_BASS_SOLO) s->bass_mode = (uint8_t)a;
        return;
    case ACC_IN_OPTION_SET:
        set_option(s, a, b);
        return;
    default:
        return;
    }
}

/* ------------------------------------------------------------------- API */

void acc_init(acc_state *s)
{
    memset(s, 0, sizeof *s);
    s->style = ACC_STYLE_SIMPLE;
    s->ext_add = ACC_EXTADD_ADD_NOTE;
    s->secret = ACC_SECRET_OFF;
    s->single_notes = ACC_SINGLE_FULL_OCTAVE;
    s->vel_sense = 1;
    s->bass_mode = ACC_BASS_CHORDS_ONLY;
    s->v = ACC_V_DEFAULT;
    s->vb = ACC_VB_DEFAULT;
    s->key = -1;
    s->bass_note = -1;
    s->res.secret = -1;
}

int acc_process(acc_state *s, const acc_in *in, int n_in, acc_note_ev *out, int max)
{
    s->out = out; s->out_n = 0; s->out_max = max;
    for (int i = 0; i < n_in; i++) handle(s, &in[i]);
    s->out = NULL;
    return s->out_n;
}

int acc_input(acc_state *s, uint8_t type, uint8_t a, int16_t b, uint32_t offset, acc_note_ev *out, int max)
{
    acc_in in;
    in.offset = offset; in.type = type; in.a = a; in.b = b;
    return acc_process(s, &in, 1, out, max);
}
