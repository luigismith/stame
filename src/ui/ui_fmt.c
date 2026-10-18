/* ui_fmt.c — testi derivati dai valori (UI-029). */
#include "ui_fmt.h"

char *ui_fmt_copy(char *buf, int n, const char *s)
{
    if (n <= 0) return buf;
    int i = 0;
    for (; s && s[i] && i < n - 1; i++) buf[i] = s[i];
    /* non spezzare un carattere UTF-8 a metà: l'ultimo si tiene solo se è completo (anche quando il
     * taglio cade subito dopo il suo primo byte) */
    int j = i;
    while (j > 0 && ((unsigned char)buf[j - 1] & 0xC0) == 0x80) j--;
    if (j > 0 && (unsigned char)buf[j - 1] >= 0xC0) {
        unsigned char c = (unsigned char)buf[j - 1];
        int need = c >= 0xF0 ? 4 : c >= 0xE0 ? 3 : 2;
        if (i - (j - 1) < need) i = j - 1;
    }
    buf[i] = 0;
    return buf;
}

char *ui_fmt_cat(char *buf, int n, const char *a, const char *b)
{
    ui_fmt_copy(buf, n, a);
    int l = (int)strlen(buf);
    ui_fmt_copy(buf + l, n - l, b);
    return buf;
}

char *ui_fmt_int(char *buf, int n, int v, int digits)
{
    char tmp[12];
    int i = 0;
    bool neg = v < 0;
    unsigned u = neg ? (unsigned)(-v) : (unsigned)v;
    do { tmp[i++] = (char)('0' + u % 10); u /= 10; } while (u && i < 11);
    while (i < digits && i < 11) tmp[i++] = '0';
    int k = 0;
    if (neg && k < n - 1) buf[k++] = '-';
    while (i > 0 && k < n - 1) buf[k++] = tmp[--i];
    if (n > 0) buf[k] = 0;
    return buf;
}

char *ui_fmt_signed(char *buf, int n, int v)
{
    if (v > 0 && n > 1) {
        buf[0] = '+';
        ui_fmt_int(buf + 1, n - 1, v, 1);
        return buf;
    }
    return ui_fmt_int(buf, n, v, 1);
}

const char *ui_fmt_kit(uint8_t kit)
{
    static const char *const N[6] = { "Beat", "Studio", "Jazz", "808", "Techno", "Chip" };
    return kit < 6 ? N[kit] : "?";
}

/* la parte che M regola nella batteria che si inventa (MIDI-139): 0 = tutto */
const char *ui_fmt_part(uint8_t part)
{
    static const char *const N[6] = { "All", "Kick", "Snare", "Hat", "Open Hat", "Perc" };
    return part < 6 ? N[part] : "?";
}

const char *ui_fmt_roll(uint8_t roll)
{
    static const char *const N[7] = { "Off", "1/4", "1/8", "1/8T", "1/16", "1/16T", "1/32" };
    return roll < 7 ? N[roll] : "?";
}

const char *ui_fmt_perf_short(uint8_t mode)
{
    static const char *const N[PERF_COUNT] = {
        "Off", "Strum", "Strum 2 Oct", "Slop", "Arpeggiate", "Arp 2 Oct", "Pattern", "Harp"
    };
    return mode < PERF_COUNT ? N[mode] : "?";
}

const char *ui_fmt_perf_long(uint8_t mode)
{
    static const char *const N[PERF_COUNT] = {
        "Off", "Strum", "Strum 2 Octaves", "Slop", "Arpeggiate", "Arpeggiate 2 Octaves", "Pattern", "Harp"
    };
    return mode < PERF_COUNT ? N[mode] : "?";
}

const char *ui_fmt_fx_abbr(uint8_t type)
{
    static const char *const N[FX_COUNT] = { "REV", "CHO", "ENS", "PHA", "FLA", "DRV", "TRM", "DLY", "FLT" };
    return type < FX_COUNT ? N[type] : "?";
}

const char *ui_fmt_fx_name(uint8_t type)
{
    static const char *const N[FX_COUNT] = {
        "Reverb", "Chorus", "Ensemble", "Phaser", "Flanger", "Drive", "Tremolo", "Delay", "Filter"
    };
    return type < FX_COUNT ? N[type] : "?";
}

const char *ui_fmt_engine(uint8_t engine)
{
    switch (engine) {
    case ENGINE_VA: return "VA";
    case ENGINE_FM: return "FM";
    case ENGINE_RP: return "RP";
    case ENGINE_SMP: return "SMP";
    default:        return "??";
    }
}

const char *ui_fmt_view_short(uint8_t view)
{
    static const char *const N[VIEW_COUNT] = { "React", "Chord", "Keybd", "Ch+Kb", "Notes", "Geek" };
    return view < VIEW_COUNT ? N[view] : "?";
}

const char *ui_fmt_play_style(uint8_t style)
{
    switch (style) {
    case 0:  return "Simple";
    case 1:  return "Advanced";
    case 2:  return "Free";
    default: return "?";
    }
}

/* Linneo classificava le piante contando gli stami (Systema Naturae, 1735): una nota per stame. */
const char *ui_fmt_linnaeus(int n_pcs)
{
    static const char *const N[] = {
        "", "MONANDRIA", "DIANDRIA", "TRIANDRIA", "TETRANDRIA", "PENTANDRIA", "HEXANDRIA",
        "HEPTANDRIA", "OCTANDRIA", "ENNEANDRIA", "DECANDRIA", "DODECANDRIA", "DODECANDRIA"
    };
    if (n_pcs <= 0) return "";
    if (n_pcs >= (int)STAME_COUNT(N)) return "POLYANDRIA";
    return N[n_pcs];
}
