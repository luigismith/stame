/* acc_kv.c — opzioni del motore degli accordi in righe chiave=valore (PLT-066). */
#include "acc_kv.h"

typedef struct {
    const char *key;
    uint8_t opt;     /* acc_option */
    uint8_t file;    /* kv_file_t */
} acc_key_t;

static const acc_key_t KEYS[] STAME_ROM = {
    { "acc.play_style",               ACC_OPT_PLAY_STYLE,               KV_IMPOSTAZIONI },  /* 0 Simple, 1 Advanced, 2 Free */
    { "acc.secret_chords",            ACC_OPT_SECRET,                   KV_IMPOSTAZIONI },  /* 0 Off, 1 solo Simple, 2 tutti */
    { "acc.single_notes",             ACC_OPT_SINGLE_NOTES,             KV_IMPOSTAZIONI },  /* 0 Split, 1 Full Octave */
    { "acc.extension_addition",       ACC_OPT_EXT_ADD,                  KV_IMPOSTAZIONI },  /* 0 Add Note, 1 Play Chord */
    { "acc.velocity_sense",           ACC_OPT_VEL_SENSE,                KV_IMPOSTAZIONI },  /* 0 Off, 1 On */
    { "acc.bass_mode",                ACC_OPT_BASS_MODE,                KV_IMPOSTAZIONI },  /* 0 Chords Only … 3 Solo */
    { "acc.compat_dim7_true",         ACC_OPT_COMPAT_DIM7_TRUE,         KV_IMPOSTAZIONI },  /* ACC-023 */
    { "acc.compat_partial_retrigger", ACC_OPT_COMPAT_PARTIAL_RETRIGGER, KV_IMPOSTAZIONI },  /* ACC-077 */
    { "acc.compat_free_2025",         ACC_OPT_COMPAT_FREE_2025,         KV_IMPOSTAZIONI },  /* ACC-115 */
    { "acc.key_mode",                 ACC_OPT_KEY_ON,                   KV_STATO },
    { "acc.key",                      ACC_OPT_KEY_INDEX,                KV_STATO },         /* 0..41 */
    { "acc.transpose",                ACC_OPT_TRANSPOSE,                KV_STATO },         /* -12..12 (UI-093) */
    { "acc.bass",                     ACC_OPT_BASS_ON,                  KV_STATO },
    { "acc.chord_voicing",            ACC_OPT_VOICING,                  KV_STATO },         /* 1..60 */
    { "acc.bass_voicing",             ACC_OPT_BASS_VOICING,             KV_STATO },         /* 0..48 */
};

void acc_kv_save(const acc_state *s, kv_w_t *w, kv_file_t file)
{
    for (size_t i = 0; i < STAME_COUNT(KEYS); i++)
        if (KEYS[i].file == file) kv_w_int(w, KEYS[i].key, acc_option_get(s, KEYS[i].opt));
}

bool acc_kv_apply(acc_state *s, const kv_pair_t *kv)
{
    for (size_t i = 0; i < STAME_COUNT(KEYS); i++) {
        if (!kv_key_is(kv, KEYS[i].key)) continue;
        int32_t v;
        if (!kv_val_int(kv, &v)) return false;
        if (v < INT16_MIN) v = INT16_MIN;                           /* acc_in.b è a 16 bit */
        if (v > INT16_MAX) v = INT16_MAX;
        acc_input(s, ACC_IN_OPTION_SET, KEYS[i].opt, (int16_t)v, 0, NULL, 0);
        return true;
    }
    return false;
}
