/* test_acc.c — vettori di test del motore degli accordi (sezione 10, §13). */
#include "test.h"
#include "core/acc.h"
#include <stdlib.h>
#include <string.h>

static acc_state S;
static acc_note_ev EV[64];
static int NEV;
static const char *ID = "";

enum { C = 0, Cs, D, Ds, E, F, Fs, G, Gs, A, As, B };

static void reset(void) { acc_init(&S); NEV = 0; }

static int in(int type, int a, int b)
{
    NEV = acc_input(&S, (uint8_t)type, (uint8_t)a, (int16_t)b, 0, EV, 64);
    return NEV;
}

static void opt(int o, int v) { in(ACC_IN_OPTION_SET, o, v); }

static int type_of(char c)
{
    switch (c) { case 'D': return ACC_DIM; case 'm': return ACC_MIN; case 'M': return ACC_MAJ; default: return ACC_SUS; }
}

static int ext_of(char c)
{
    switch (c) { case '6': return ACC_E6; case '7': return ACC_E7MIN; case 'J': return ACC_E7MAJ; default: return ACC_E9; }
}

/* Tiene i tipi nell'ordine dato (D = Dim, m = Min, M = Maj, S = Sus), le estensioni
 * (6, 7 = m7, J = M7, 9), poi preme il tasto k a velocity 100. */
static void chord(const char *types, const char *exts, int k)
{
    for (const char *p = types; *p; p++) in(ACC_IN_TYPE_DOWN, type_of(*p), 0);
    for (const char *p = exts; *p; p++) in(ACC_IN_EXT_DOWN, ext_of(*p), 0);
    in(ACC_IN_KEY_DOWN, k, 100);
}

static void notes_str(const acc_notes *n, char *buf)
{
    buf[0] = 0;
    for (int i = 0; i < n->n; i++) sprintf(buf + strlen(buf), i ? " %d" : "%d", n->note[i]);
}

static bool notes_eq(const acc_notes *n, const char *spec)
{
    const char *p = spec; int i = 0;
    while (*p) {
        while (*p == ' ') p++;
        if (!*p) break;
        char *end; long v = strtol(p, &end, 10);
        if (end == p) return false;
        if (i >= n->n || n->note[i] != v) return false;
        i++; p = end;
    }
    return i == n->n;
}

static void check_treble(const char *spec)
{
    char got[64]; notes_str(&S.treble, got);
    CHECKM(notes_eq(&S.treble, spec), "%s: treble [%s], atteso [%s]", ID, got, spec);
}

static void check_bass(int note)
{
    CHECKM(S.bass_note == note, "%s: basso %d, atteso %d", ID, S.bass_note, note);
}

static void check_name(const char *exp)
{
    char b[32]; acc_name_text(&S.name, b, sizeof b);
    CHECKM(strcmp(b, exp) == 0, "%s: nome %s, atteso %s", ID, b, exp);
}

static char role_ch(int role)
{
    return role == ACC_ROLE_TREBLE ? 'T' : role == ACC_ROLE_BASS ? 'B' : role == ACC_ROLE_CHORD_BLOCK ? 'H' : 'D';
}

static void ev_str(char *buf)
{
    buf[0] = 0;
    for (int i = 0; i < NEV; i++)
        sprintf(buf + strlen(buf), "%s%c%c%d", i ? " " : "", role_ch(EV[i].role), EV[i].on ? '+' : '-', EV[i].note);
}

/* spec: "H+48 T+48 B-36" = ruolo (T, B, H, D), + note-on o - note-off, nota; nell'ordine */
static bool ev_eq(const char *spec)
{
    const char *p = spec; int i = 0;
    while (*p) {
        while (*p == ' ') p++;
        if (!*p) break;
        char r = *p++, sg = *p++;
        char *end; long v = strtol(p, &end, 10);
        if (end == p) return false;
        if (i >= NEV) return false;
        if (role_ch(EV[i].role) != r || (EV[i].on ? '+' : '-') != sg || EV[i].note != v) return false;
        i++; p = end;
    }
    return i == NEV;
}

static void check_ev(const char *spec)
{
    char got[512]; ev_str(got);
    CHECKM(ev_eq(spec), "%s: eventi [%s], attesi [%s]", ID, got, spec);
}

static void check_vel(int vel)
{
    bool ok = true;
    for (int i = 0; i < NEV; i++) if (EV[i].on && EV[i].vel != vel) ok = false;
    CHECKM(ok, "%s: velocity dei note-on diversa da %d", ID, vel);
}

/* ------------------------------------------------------------ §13.1 */

static void t_accordi_e_nomi(void)
{
    struct { const char *id, *types, *exts; int k; const char *notes, *name; } tv[] = {
        { "TV-01", "M", "",     C,  "48 52 55",             "C" },
        { "TV-02", "M", "",     G,  "50 55 59",             "G" },
        { "TV-03", "M", "",     F,  "48 53 57",             "F" },
        { "TV-04", "m", "",     A,  "48 52 57",             "Am" },
        { "TV-05", "D", "",     B,  "50 53 59",             "Bdim" },
        { "TV-06", "S", "",     D,  "50 55 57",             "Dsus" },
        { "TV-07", "M", "J",    C,  "48 52 55 59",          "C^M7" },
        { "TV-08", "M", "7",    C,  "48 52 55 58",          "C^7" },
        { "TV-09", "S", "7",    C,  "48 53 55 58",          "Csus^m7" },
        { "TV-10", "M", "9",    C,  "48 50 52 55",          "C^9" },
        { "TV-11", "m", "79",   D,  "48 50 52 53 57",       "Dm^79" },
        { "TV-12", "M", "J6",   C,  "48 52 55 57 59",       "C^M76" },
        { "TV-13", "D", "7",    C,  "48 51 54 58",          "Cdim^7" },
        { "TV-14", "D", "6",    C,  "48 51 54 57",          "Cdim^6" },
        { "TV-15", "m", "7J9",  C,  "48 50 51 55 58 59",    "Cm^JAZZ" },
        { "TV-16", "D", "67J9", C,  "48 50 51 54 57 58 59", "Cdim^WTF" },
        { "TV-17", "M", "",     Cs, "49 53 56",             "C#" },
        { "TV-18", "",  "6",    C,  "48",                   "C" },
        { "TV-19", "Mm", "",    C,  "48 51 55",             "Cm" },
    };
    for (size_t i = 0; i < sizeof tv / sizeof tv[0]; i++) {
        ID = tv[i].id; reset();
        chord(tv[i].types, tv[i].exts, tv[i].k);
        check_treble(tv[i].notes);
        check_name(tv[i].name);
    }
    ID = "TV-18"; reset(); chord("", "6", C);
    CHECK(S.name.single == 1 && S.name.single_note == 48);

    /* ACC-026: tutte le 64 combinazioni hanno da 3 a 7 note e seguono ACC-021 */
    ID = "ACC-026";
    for (int t = 0; t < ACC_TYPE_COUNT; t++)
        for (int e = 0; e < 16; e++) {
            uint16_t m = acc_chord_mask(t, (uint8_t)e, false);
            int n = 0; for (int i = 0; i < 12; i++) n += (m >> i) & 1;
            CHECKM(n >= 3 && n <= 7, "tipo %d exts %d: %d note", t, e, n);
        }
}

/* ------------------------------------------------------------ §13.2 */

static void t_secret(void)
{
    struct { const char *id, *types, *exts; int k; const char *notes, *name; } tv[] = {
        { "TV-20", "DS", "",  C, "48 55",          "C^5" },
        { "TV-21", "MS", "",  C, "48 52 56",       "C+" },
        { "TV-22", "mS", "",  C, "48 51 53 55",    "Cm^add4" },
        { "TV-23", "mD", "6", C, "48 51 55 56",    "Cm^m6" },
        { "TV-24", "MD", "",  C, "48 52 55 56",    "C^m6" },
        { "TV-25", "Mm", "7", C, "48 51 52 55 58", "C7#^9" },
        { "TV-26", "Mm", "",  C, "48 51 55",       "Cm" },
    };
    for (size_t i = 0; i < sizeof tv / sizeof tv[0]; i++) {
        ID = tv[i].id; reset(); opt(ACC_OPT_SECRET, ACC_SECRET_ALL);
        chord(tv[i].types, tv[i].exts, tv[i].k);
        check_treble(tv[i].notes);
        check_name(tv[i].name);
    }
    ID = "TV-27"; reset();
    opt(ACC_OPT_SECRET, ACC_SECRET_SIMPLE_ONLY); opt(ACC_OPT_PLAY_STYLE, ACC_STYLE_ADVANCED);
    chord("MS", "", C);
    check_treble("48 53 55"); check_name("Csus");

    /* ACC-044: estensione extra aggiunta, nome invariato */
    ID = "ACC-044"; reset(); opt(ACC_OPT_SECRET, ACC_SECRET_ALL);
    chord("MS", "9", C);
    check_treble("48 50 52 56"); check_name("C+");
    /* ACC-042: con tre tipi tenuti niente Secret, vale l'ultimo */
    ID = "ACC-042"; reset(); opt(ACC_OPT_SECRET, ACC_SECRET_ALL);
    chord("DSM", "", C);
    check_treble("48 52 55"); check_name("C");
}

/* ------------------------------------------------------------ §13.3 */

static void t_voicing_e_basso(void)
{
    struct { const char *id; int v; const char *exts, *notes; } tv[] = {
        { "TV-30", 25, "",  "52 55 60" },
        { "TV-31", 28, "",  "52 55 60" },
        { "TV-32", 29, "",  "55 60 64" },
        { "TV-33", 32, "",  "60 64 67" },
        { "TV-34", 1,  "",  "28 31 36" },
        { "TV-35", 60, "",  "84 88 91" },
        { "TV-36", 25, "J", "52 55 59 60" },
    };
    for (size_t i = 0; i < sizeof tv / sizeof tv[0]; i++) {
        ID = tv[i].id; reset(); opt(ACC_OPT_VOICING, tv[i].v);
        chord("M", tv[i].exts, C);
        check_treble(tv[i].notes);
    }
    ID = "TV-37"; reset(); opt(ACC_OPT_VOICING, 60);
    in(ACC_IN_VOICING_STEP, 0, 1);
    CHECK_EQ(NEV, 0); CHECK_EQ(S.v, 60);

    ID = "TV-38"; reset(); opt(ACC_OPT_BASS_ON, 1); chord("M", "", C);
    check_treble("48 52 55"); check_bass(36);
    ID = "TV-39"; reset(); opt(ACC_OPT_BASS_ON, 1); chord("M", "", G);
    check_treble("50 55 59"); check_bass(43);
    ID = "TV-40"; reset(); opt(ACC_OPT_BASS_ON, 1); opt(ACC_OPT_BASS_VOICING, 24); chord("M", "", C);
    check_bass(48);
    ID = "TV-41"; reset(); opt(ACC_OPT_BASS_ON, 1); opt(ACC_OPT_BASS_VOICING, 0); chord("M", "", C);
    check_bass(24);
    reset(); opt(ACC_OPT_BASS_ON, 1); opt(ACC_OPT_BASS_VOICING, 48); chord("M", "", C);
    check_bass(72);
    ID = "TV-42"; reset(); opt(ACC_OPT_BASS_ON, 1); opt(ACC_OPT_TRANSPOSE, 2); chord("M", "", C);
    check_treble("50 54 57"); check_bass(38); check_name("D");
    ID = "TV-43"; reset(); opt(ACC_OPT_TRANSPOSE, -12); opt(ACC_OPT_VOICING, 1); chord("M", "", C);
    check_treble("16 19 24");

    /* il transpose vale anche per il basso; con i limiti di v, vb e transpose nessuna
     * nota esce da 0..127, quindi lo scarto di ACC-083 non è provabile da qui */
    ID = "transpose-basso"; reset(); opt(ACC_OPT_TRANSPOSE, -12); opt(ACC_OPT_VOICING, 1); opt(ACC_OPT_BASS_ON, 1);
    opt(ACC_OPT_BASS_VOICING, 0); chord("M", "", C);
    check_bass(12);
    ID = "acc_place"; CHECK_EQ(acc_place(0, 48), 48); CHECK_EQ(acc_place(11, 48), 59); CHECK_EQ(acc_place(0, 49), 60);
}

/* ------------------------------------------------------------ §13.4 */

static void t_note_singole(void)
{
    struct { const char *id; int mode, v, k, note; } tv[] = {
        { "TV-45", ACC_SINGLE_FULL_OCTAVE, 24, E, 52 },
        { "TV-46", ACC_SINGLE_FULL_OCTAVE, 29, E, 52 },
        { "TV-47", ACC_SINGLE_SPLIT,       29, E, 64 },
        { "TV-48", ACC_SINGLE_SPLIT,       29, G, 55 },
        { "TV-49", ACC_SINGLE_SPLIT,       24, C, 48 },
    };
    for (size_t i = 0; i < sizeof tv / sizeof tv[0]; i++) {
        ID = tv[i].id; reset();
        opt(ACC_OPT_SINGLE_NOTES, tv[i].mode); opt(ACC_OPT_VOICING, tv[i].v);
        in(ACC_IN_KEY_DOWN, tv[i].k, 100);
        char exp[8]; sprintf(exp, "%d", tv[i].note);
        check_treble(exp);
        CHECK(S.name.single && S.name.single_note == tv[i].note);
    }
    /* ACC-081: il toggle con la nota che suona la ri-attacca se cambia altezza */
    ID = "ACC-081"; reset(); opt(ACC_OPT_VOICING, 29); in(ACC_IN_KEY_DOWN, E, 100);
    in(ACC_IN_SINGLE_NOTES_TOGGLE, 0, 0);
    check_ev("H-52 T-52 H+64 T+64");
}

/* ------------------------------------------------------------ §13.5 */

static void t_key_mode(void)
{
    enum { CMAJ = 0, DsMAJ = 4, FMAJ = 9, AMAJ = 15, CMIN = 21 };
    struct { const char *id; int key; const char *types, *exts; int k; const char *notes; int bass; const char *name; } tv[] = {
        { "TV-50", CMAJ,  "",  "",  D,  "50 53 57",    38, "Dm" },
        { "TV-51", CMAJ,  "",  "",  Cs, "48 53 55",    36, "Csus" },
        { "TV-52", CMAJ,  "",  "",  Fs, "48 53 57",    41, "F" },
        { "TV-53", CMAJ,  "",  "",  As, "50 53 57",    45, "Dm/A" },
        { "TV-54", CMAJ,  "",  "",  B,  "50 53 59",    47, "Bdim" },
        { "TV-55", CMAJ,  "",  "J", G,  "50 53 55 59", 43, "G^7" },
        { "TV-56", CMAJ,  "",  "9", E,  "52 53 55 59", 40, "Em^9" },
        { "TV-57", CMAJ,  "",  "6", C,  "48 52 55 57", 36, "C^6" },
        { "TV-58", CMAJ,  "M", "",  D,  "50 54 57",    38, "D" },
        { "TV-59", CMIN,  "",  "",  G,  "50 55 58",    43, "Gm" },
        { "TV-60", CMIN,  "",  "",  Cs, "48 53 56",    36, "Fm/C" },
        { "TV-61", CMIN,  "",  "",  E,  "51 56 58",    39, "Ebsus" },
        { "TV-62", AMAJ,  "",  "",  F,  "52 57 59",    40, "Esus" },
        { "TV-63", FMAJ,  "M", "",  As, "50 53 58",    46, "Bb" },
        { "TV-64", DsMAJ, "",  "J", E,  "50 51 56 58", 39, "D#sus^M7" },
    };
    for (size_t i = 0; i < sizeof tv / sizeof tv[0]; i++) {
        ID = tv[i].id; reset();
        opt(ACC_OPT_KEY_ON, 1); opt(ACC_OPT_KEY_INDEX, tv[i].key); opt(ACC_OPT_BASS_ON, 1);
        chord(tv[i].types, tv[i].exts, tv[i].k);
        check_treble(tv[i].notes); check_bass(tv[i].bass); check_name(tv[i].name);
    }
    /* TV-64: la nota aggiunta (pc 2) in Re# maggiore si scrive Cx */
    ID = "TV-64"; acc_spelled sp = acc_spell_pc(&S, 2);
    CHECK(sp.letter == 'C' && sp.acc == ACC_ACC_DSHARP);

    /* ACC-093: Fa♭ maggiore ha B𝄫 */
    ID = "ACC-093"; acc_key_degree_spelling(8, 3, &sp);
    CHECK(sp.letter == 'B' && sp.acc == ACC_ACC_DFLAT);

    /* ACC-055: C maggiore + transpose 1 → Re♭ maggiore (5 bemolli, non Do# con 7 diesis) */
    ID = "ACC-055"; CHECK_EQ(acc_effective_key(0, 1), 2);
    CHECK_EQ(acc_effective_key(0, -1), 18);      /* Si maggiore (5 diesis) e non Do♭ (7 bemolli) */
    CHECK_EQ(acc_effective_key(0, 6), 10);       /* parità 6 e 6: vincono i diesis (Fa#) */
    CHECK_EQ(acc_effective_key(21, 2), 24);      /* Do minore + 2 = Re minore */
    reset(); opt(ACC_OPT_KEY_ON, 1); opt(ACC_OPT_TRANSPOSE, 1); chord("", "", C);
    check_name("Db"); check_treble("49 53 56");

    /* ACC-054: fuori scala in Fa maggiore (bemolli) → Db; in Do maggiore → C# */
    ID = "ACC-054"; reset(); opt(ACC_OPT_KEY_ON, 1); opt(ACC_OPT_KEY_INDEX, FMAJ);
    sp = acc_spell_pc(&S, 1); CHECK(sp.letter == 'D' && sp.acc == ACC_ACC_FLAT);
    opt(ACC_OPT_KEY_INDEX, CMAJ);
    sp = acc_spell_pc(&S, 1); CHECK(sp.letter == 'C' && sp.acc == ACC_ACC_SHARP);

    /* ACC-100: il cambio di tonalità con l'accordo tenuto non ri-attacca */
    ID = "ACC-100"; reset(); opt(ACC_OPT_KEY_ON, 1); chord("", "", D);
    in(ACC_IN_KEY_SELECT, 33, 0); CHECK_EQ(NEV, 0);
    in(ACC_IN_KEY_MODE_TOGGLE, 0, 0); CHECK_EQ(NEV, 0); check_treble("50 53 57");
}

/* ------------------------------------------------------------ §13.6 */

static void t_play_style(void)
{
    ID = "TV-70"; reset();
    in(ACC_IN_TYPE_DOWN, ACC_MAJ, 0);  check_ev("");
    in(ACC_IN_KEY_DOWN, C, 100);       check_ev("H+48 H+52 H+55 T+48 T+52 T+55"); check_vel(100);
    in(ACC_IN_TYPE_UP, ACC_MAJ, 0);    check_ev("");
    in(ACC_IN_TYPE_DOWN, ACC_MIN, 0);  check_ev("");
    in(ACC_IN_KEY_UP, C, 0);           check_ev("H-48 H-52 H-55 T-48 T-52 T-55");

    ID = "TV-71"; reset(); opt(ACC_OPT_PLAY_STYLE, ACC_STYLE_ADVANCED); opt(ACC_OPT_BASS_ON, 1);
    in(ACC_IN_KEY_DOWN, C, 90);        check_ev("H+48 T+48"); check_vel(90);
    in(ACC_IN_TYPE_DOWN, ACC_MIN, 0);  check_ev("H-48 T-48 H+48 H+51 H+55 T+48 T+51 T+55 B+36"); check_vel(90);
    in(ACC_IN_EXT_DOWN, ACC_E7MAJ, 0); check_ev("H+59 T+59"); check_vel(90);
    in(ACC_IN_EXT_UP, ACC_E7MAJ, 0);   check_ev("");
    in(ACC_IN_KEY_UP, C, 0);           check_ev("H-48 H-51 H-55 H-59 T-48 T-51 T-55 T-59 B-36");

    ID = "TV-72"; reset(); opt(ACC_OPT_PLAY_STYLE, ACC_STYLE_ADVANCED); opt(ACC_OPT_EXT_ADD, ACC_EXTADD_PLAY_CHORD);
    chord("M", "", C);
    in(ACC_IN_EXT_DOWN, ACC_E9, 0);
    check_ev("H-48 H-52 H-55 T-48 T-52 T-55 H+48 H+50 H+52 H+55 T+48 T+50 T+52 T+55");

    ID = "TV-73"; reset(); opt(ACC_OPT_PLAY_STYLE, ACC_STYLE_ADVANCED);
    chord("M", "", C);
    in(ACC_IN_TYPE_UP, ACC_MAJ, 0);    check_ev("");
    in(ACC_IN_TYPE_DOWN, ACC_MIN, 0);  check_ev(""); check_treble("48 52 55");
    in(ACC_IN_EXT_DOWN, ACC_E9, 0);    check_ev("");   /* bloccato: anche le estensioni sono ignorate */

    ID = "TV-74"; reset(); opt(ACC_OPT_PLAY_STYLE, ACC_STYLE_FREE);
    chord("M", "", C);
    in(ACC_IN_TYPE_UP, ACC_MAJ, 0);    check_ev("");
    in(ACC_IN_TYPE_DOWN, ACC_MIN, 0);  check_ev("H-48 H-52 H-55 T-48 T-52 T-55 H+48 H+51 H+55 T+48 T+51 T+55");

    ID = "TV-75"; reset(); opt(ACC_OPT_PLAY_STYLE, ACC_STYLE_FREE); opt(ACC_OPT_COMPAT_FREE_2025, 1);
    chord("M", "", C);
    in(ACC_IN_TYPE_UP, ACC_MAJ, 0);    check_ev("H-48 H-52 H-55 T-48 T-52 T-55 H+48 T+48");

    ID = "TV-76"; reset();
    chord("M", "", C);
    in(ACC_IN_KEY_DOWN, G, 100);       check_ev("H-48 H-52 H-55 T-48 T-52 T-55 H+50 H+55 H+59 T+50 T+55 T+59");
    in(ACC_IN_KEY_UP, C, 0);           check_ev("");
    in(ACC_IN_KEY_UP, G, 0);           check_ev("H-50 H-55 H-59 T-50 T-55 T-59");

    ID = "TV-77"; reset();
    chord("M", "", C);
    in(ACC_IN_VOICING_STEP, 0, 1);     check_ev("H-48 H-52 H-55 T-48 T-52 T-55 H+52 H+55 H+60 T+52 T+55 T+60");
    in(ACC_IN_VOICING_STEP, 0, 1);     check_ev(""); CHECK_EQ(S.v, 26);

    ID = "TV-78"; reset(); opt(ACC_OPT_BASS_ON, 1);
    chord("M", "", C);
    in(ACC_IN_KEY_DOWN, G, 100);
    check_ev("H-48 H-52 H-55 T-48 T-52 T-55 H+50 H+55 H+59 T+50 T+55 T+59 B+43 B-36");

    /* ACC-007: pressioni e rilasci doppi ignorati */
    ID = "ACC-007"; reset();
    in(ACC_IN_KEY_DOWN, C, 100); in(ACC_IN_KEY_DOWN, C, 100); check_ev("");
    in(ACC_IN_KEY_UP, D, 0); check_ev("");
    in(ACC_IN_KEY_UP, C, 0); check_ev("H-48 T-48");
    in(ACC_IN_KEY_UP, C, 0); check_ev("");

    /* ACC-077 variante parziale: solo le note che cambiano */
    ID = "ACC-077p"; reset(); opt(ACC_OPT_COMPAT_PARTIAL_RETRIGGER, 1);
    chord("M", "", C);
    in(ACC_IN_VOICING_STEP, 0, 1);     check_ev("H-48 T-48 H+60 T+60");

    /* ACC-085: il transpose ri-attacca e rinomina */
    ID = "ACC-085"; reset(); opt(ACC_OPT_BASS_ON, 1);
    chord("M", "", C);
    in(ACC_IN_TRANSPOSE_STEP, 0, 2);
    check_ev("H-48 H-52 H-55 T-48 T-52 T-55 H+50 H+54 H+57 T+50 T+54 T+57 B-36 B+38");
    check_name("D");

    /* ACC-148: spegnere il basso mentre suona */
    ID = "ACC-148"; reset(); opt(ACC_OPT_BASS_ON, 1);
    chord("M", "", C);
    in(ACC_IN_BASS_TOGGLE, 0, 0);      check_ev("B-36");
    in(ACC_IN_KEY_UP, C, 0);           check_ev("H-48 H-52 H-55 T-48 T-52 T-55");

    /* ACC-014: Velocity Sense Off → 100 */
    ID = "ACC-014"; reset(); opt(ACC_OPT_VEL_SENSE, 0);
    in(ACC_IN_KEY_DOWN, C, 37);        check_vel(100);
}

/* ------------------------------------------------------------ §13.7 */

static void t_basso_modi(void)
{
    ID = "TV-80"; reset(); opt(ACC_OPT_BASS_ON, 1); opt(ACC_OPT_BASS_MODE, ACC_BASS_UNISON);
    in(ACC_IN_KEY_DOWN, E, 100); check_treble("52"); check_bass(40);
    ID = "TV-81"; reset(); opt(ACC_OPT_BASS_ON, 1); opt(ACC_OPT_BASS_MODE, ACC_BASS_SINGLE_NOTES);
    in(ACC_IN_KEY_DOWN, E, 100); check_treble(""); check_bass(40); check_ev("B+40");
    ID = "TV-82"; reset(); opt(ACC_OPT_BASS_MODE, ACC_BASS_SINGLE_NOTES);
    in(ACC_IN_KEY_DOWN, E, 100); check_treble("52"); check_bass(-1);
    ID = "TV-83"; reset(); opt(ACC_OPT_BASS_ON, 1); opt(ACC_OPT_BASS_MODE, ACC_BASS_SOLO);
    chord("M", "", C); check_treble(""); check_bass(36); check_ev("B+36");
    ID = "TV-84"; reset(); opt(ACC_OPT_BASS_ON, 1); opt(ACC_OPT_KEY_ON, 1);
    in(ACC_IN_KEY_DOWN, D, 100); check_treble("50 53 57"); check_bass(38);
    /* ACC-145: Solo con basso spento non suona nulla */
    ID = "ACC-145"; reset(); opt(ACC_OPT_BASS_MODE, ACC_BASS_SOLO);
    chord("M", "", C); check_ev("");
    /* ACC-147: stesso basso su cambio di tipo → nessun ri-attacco del basso */
    ID = "ACC-147"; reset(); opt(ACC_OPT_BASS_ON, 1); opt(ACC_OPT_PLAY_STYLE, ACC_STYLE_ADVANCED);
    chord("M", "", C);
    in(ACC_IN_TYPE_DOWN, ACC_MIN, 0);
    check_ev("H-48 H-52 H-55 T-48 T-52 T-55 H+48 H+51 H+55 T+48 T+51 T+55");
}

void test_acc(void)
{
    t_accordi_e_nomi();
    t_secret();
    t_voicing_e_basso();
    t_note_singole();
    t_key_mode();
    t_play_style();
    t_basso_modi();
}
