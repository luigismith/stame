/* beat.c — i pattern dei Beat, il catalogo dei kit e il metronomo (beat.h). */
#include "beat.h"

/* una riga per strumento: 16 passi, 'X' = colpo forte (110), 'x' = colpo (80), '.' = niente */
typedef struct { uint8_t inst; const char *steps; } beat_line_t;
typedef struct { const char *name; uint8_t kit; beat_line_t line[6]; } beat_def_t;

static const beat_def_t BEATS[BEAT_COUNT] STAME_ROM = {
    /* ACC-210: il provvisorio della specifica, velocity 110 sui battiti e 80 sugli altri passi */
    { "Provvisorio", KIT_CHIP, { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "....X.......X..." },
                             { DRUM_CLOSED_HAT, "X.x.X.x.X.x.X.x." } } },
    /* i Beat della vetrina (nomi e pattern di Stame, nessun dato dell'originale); i primi 6 dal 14/10,
     * gli altri dal 15/10/2026 con i kit a campioni (SND-537) */
    { "Funk", KIT_STUDIO, { { DRUM_KICK, "X.....X...X..x.." }, { DRUM_SNARE, "....X..x.x..X..x" },
                            { DRUM_CLOSED_HAT, "XxxxXxxxXxxxXxx." }, { DRUM_OPEN_HAT, "..............x." } } },
    { "Bossa", KIT_JAZZ, { { DRUM_KICK, "X..xX..xX..xX..x" }, { DRUM_RIMSHOT, "X..X..X...X..X.." },
                           { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." }, { DRUM_MARACAS, "..x...x...x...x." } } },
    { "Motorik", KIT_808, { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "....X.......X..." },
                            { DRUM_CLOSED_HAT, "X.x.X.x.X.x.X.x." } } },
    { "Lounge", KIT_JAZZ, { { DRUM_KICK, "X.......X.x....." }, { DRUM_RIMSHOT, "....X.......X..." },
                            { DRUM_CLOSED_HAT, "x.xxx.xxx.xxx.xx" }, { DRUM_MARACAS, "..x...x...x...x." } } },
    { "Shuffle", KIT_STUDIO, { { DRUM_KICK, "X.......X..x...." }, { DRUM_SNARE, "....X.......X..." },
                               { DRUM_CLOSED_HAT, "X..xX..xX..xX..x" } } },
    { "Halftime", KIT_808, { { DRUM_KICK, "X.........X....." }, { DRUM_SNARE, "........X......." },
                             { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." }, { DRUM_CLAP, "........X......." } } },
    { "Boom Bap", KIT_808, { { DRUM_KICK, "X..x......X.x..." }, { DRUM_SNARE, "....X.......X..." },
                             { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.xx" }, { DRUM_OPEN_HAT, "......x........." } } },
    { "Disco", KIT_STUDIO, { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "....X.......X..." },
                             { DRUM_CLOSED_HAT, "x...x...x...x..." }, { DRUM_OPEN_HAT, "..X...X...X...X." },
                             { DRUM_CLAP, "....x.......x..." } } },
    { "Samba", KIT_JAZZ, { { DRUM_KICK, "X..xX..xX..xX..x" }, { DRUM_RIMSHOT, "..x..x..x...x.x." },
                           { DRUM_MARACAS, "xxxxxxxxxxxxxxxx" }, { DRUM_CONGA, ".x.x..x..x.x..x." },
                           { DRUM_COWBELL, "X...X...X...X..." } } },
    { "Ballad", KIT_STUDIO, { { DRUM_KICK, "X.......x.X....." }, { DRUM_SNARE, "....X.......X..." },
                              { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." }, { DRUM_CYMBAL, "X..............." } } },
    { "Train", KIT_JAZZ, { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "x.xXx.xXx.xXx.xX" },
                           { DRUM_CLOSED_HAT, "X.x.X.x.X.x.X.x." } } },
    { "Chip", KIT_CHIP, { { DRUM_KICK, "X...X..xX...X..." }, { DRUM_SNARE, "....X.......X..x" },
                      { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." }, { DRUM_COWBELL, "..x...x...x...x." },
                      { DRUM_TOM_HI, "..............x." } } },
    /* 15/10/2026 sera, Luigi: «più cupi e più tecno». Il kit techno è di campioni Sonic Pi (CC0) */
    { "Techno", KIT_TECHNO, { { DRUM_KICK, "X...X...X...X..." }, { DRUM_CLAP, "....X.......X..." },
                              { DRUM_CLOSED_HAT, "xx.xxx.xxx.xxx.x" }, { DRUM_OPEN_HAT, "..X...X...X...X." },
                              { DRUM_RIMSHOT, "...x..x....x..x." } } },
    { "Dub", KIT_TECHNO, { { DRUM_KICK, "X...X...X...X..." }, { DRUM_RIMSHOT, "....x.......x..x" },
                           { DRUM_OPEN_HAT, "..x...x...x...x." }, { DRUM_MARACAS, "x.xxx.xxx.xxx.xx" } } },
    /* 18/10/2026, Luigi: «più cupi, più profondi, più grevi, più bassi, più acidi» */
    { "Acid", KIT_808, { { DRUM_KICK, "X...X...X...X..." }, { DRUM_CLAP, "....X.......X..." },
                         { DRUM_CLOSED_HAT, "xx.xxx.xxx.xxx.x" }, { DRUM_OPEN_HAT, "..X...X...X...X." },
                         { DRUM_RIMSHOT, "......x.......x." } } },
    { "Industrial", KIT_TECHNO, { { DRUM_KICK, "X..xX...X..xX..." }, { DRUM_SNARE, "....X.......X..." },
                                  { DRUM_RIMSHOT, "..x...x.x.....x." }, { DRUM_COWBELL, "...x.......x...." },
                                  { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." } } },
    { "Minimal", KIT_TECHNO, { { DRUM_KICK, "X...X...X...X..." }, { DRUM_RIMSHOT, "..x..x....x..x.." },
                               { DRUM_CLOSED_HAT, "..x...x...x...x." }, { DRUM_CLAP, "............X..." },
                               { DRUM_MARACAS, "x.xxx.xxx.xxx.xx" } } },
    { "Electro", KIT_808, { { DRUM_KICK, "X.....X...X..X.." }, { DRUM_CLAP, "....X.......X..." },
                            { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." }, { DRUM_COWBELL, "...x......x....." } } },
    { "Trap", KIT_808, { { DRUM_KICK, "X......X..X....." }, { DRUM_CLAP, "........X......." },
                         { DRUM_CLOSED_HAT, "x.x.x.xxx.x.xxxx" } } },
};

/* i fill (MIDI-133, 16/10/2026): una battuta di riempimento per Beat, nello stesso kit, che suona finché
 * T4 è tenuto; rullate di rullante o rimshot nella seconda metà e i tom dove il kit li ha */
typedef struct { beat_line_t line[6]; } beat_fill_t;
static const beat_fill_t FILLS[BEAT_COUNT] STAME_ROM = {
    { { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "....X...X.X.XxXx" }, { DRUM_CLOSED_HAT, "X.x.X.x.X.x.X.x." } } },
    { { { DRUM_KICK, "X.....X.X.....X." }, { DRUM_SNARE, "..X..X..XxXxXXXX" }, { DRUM_CLOSED_HAT, "XxxxXxxxXxxx...." },
        { DRUM_OPEN_HAT, "..............X." } } },
    { { { DRUM_KICK, "X..xX..xX..xX..x" }, { DRUM_RIMSHOT, "X..X..X.xxxxxxxx" }, { DRUM_MARACAS, "..x...x...x...x." },
        { DRUM_CONGA, "........x.x.xx.x" } } },
    { { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "....X.......XXXX" }, { DRUM_TOM_LO, "........x.x....." },
        { DRUM_CLOSED_HAT, "X.x.X.x.X.x.X.x." } } },
    { { { DRUM_KICK, "X.......X.x....." }, { DRUM_RIMSHOT, "....X.....x.x.X." }, { DRUM_CLOSED_HAT, "x.xxx.xxx.xx...." },
        { DRUM_TOM_HI, "............x.x." } } },
    { { { DRUM_KICK, "X.......X..x...." }, { DRUM_SNARE, "....X.....X..X.X" }, { DRUM_TOM_LO, "..............x." },
        { DRUM_CLOSED_HAT, "X..xX..xX..x...." } } },
    { { { DRUM_KICK, "X.........X.X..." }, { DRUM_SNARE, "........X...XXXX" }, { DRUM_CLOSED_HAT, "x.x.x.x.x.x....." },
        { DRUM_CLAP, "........X......." } } },
    { { { DRUM_KICK, "X..x......X.x..." }, { DRUM_SNARE, "....X....x.xX.xX" }, { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x..." },
        { DRUM_OPEN_HAT, "..............x." } } },
    { { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "....X...XxXxXXXX" }, { DRUM_CLOSED_HAT, "x...x...x...x..." },
        { DRUM_OPEN_HAT, "..X...X...X...X." }, { DRUM_CLAP, "....x.......x..." } } },
    { { { DRUM_KICK, "X..xX..xX..xX..x" }, { DRUM_RIMSHOT, "..x..x..xxxxxxxx" }, { DRUM_MARACAS, "xxxxxxxxxxxxxxxx" },
        { DRUM_CONGA, ".x.x..x.x.xx.xxx" }, { DRUM_COWBELL, "X...X...X.X.X.X." } } },
    { { { DRUM_KICK, "X.......x.X....." }, { DRUM_SNARE, "....X.......X.xX" }, { DRUM_TOM_HI, "..........x.x..." },
        { DRUM_TOM_LO, "............x..." }, { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." }, { DRUM_CYMBAL, "X..............." } } },
    { { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "x.xXx.xXXXXXXXXX" }, { DRUM_CLOSED_HAT, "X.x.X.x.X.x.X.x." } } },
    { { { DRUM_KICK, "X...X..xX...X..." }, { DRUM_SNARE, "....X...x.x.xXXX" }, { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." },
        { DRUM_TOM_HI, "..........x.x.x." }, { DRUM_COWBELL, "..x...x........." } } },
    { { { DRUM_KICK, "X...X...X...X..." }, { DRUM_CLAP, "....X.......XXXX" }, { DRUM_CLOSED_HAT, "xx.xxx.xxx.xxxxx" },
        { DRUM_OPEN_HAT, "..X...X...X...X." }, { DRUM_RIMSHOT, "...x..x.xxxxxxxx" } } },
    { { { DRUM_KICK, "X...X...X...X.X." }, { DRUM_RIMSHOT, "....x.......xxxx" }, { DRUM_OPEN_HAT, "..x...x...x...x." },
        { DRUM_MARACAS, "x.xxx.xxx.xxxxxx" }, { DRUM_TOM_LO, "..........x.x..." } } },
    { { { DRUM_KICK, "X...X...X...X.X." }, { DRUM_CLAP, "....X.......XXXX" }, { DRUM_CLOSED_HAT, "xx.xxx.xxx.xxxxx" },
        { DRUM_OPEN_HAT, "..X...X...X....." }, { DRUM_TOM_LO, "..........x.x..." } } },
    { { { DRUM_KICK, "X..xX...X..xXXXX" }, { DRUM_SNARE, "....X...X.X.XXXX" }, { DRUM_RIMSHOT, "..x...x.xxxxxxxx" },
        { DRUM_COWBELL, "...x.......x...." }, { DRUM_CLOSED_HAT, "x.x.x.x.x.x....." } } },
    { { { DRUM_KICK, "X...X...X...X.X." }, { DRUM_RIMSHOT, "..x..x..x.x.xxxx" }, { DRUM_CLOSED_HAT, "..x...x...x...x." },
        { DRUM_CLAP, "........X...X.XX" }, { DRUM_MARACAS, "x.xxx.xxx.xxxxxx" } } },
    { { { DRUM_KICK, "X.....X...X.X.X." }, { DRUM_CLAP, "....X...X.X.XXXX" }, { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." },
        { DRUM_TOM_HI, "..........x.x.x." }, { DRUM_TOM_LO, "...........x.x.x" } } },
    { { { DRUM_KICK, "X......X..X.X.X." }, { DRUM_CLAP, "........X...XXXX" }, { DRUM_CLOSED_HAT, "xxxxxxxxxxxxxxxx" } } },
};

static int line_hits(const beat_line_t *lines, int s, beat_hit_t *out, int max)
{
    int k = 0;
    for (int i = 0; i < 6 && k < max; i++) {
        const beat_line_t *l = &lines[i];
        if (!l->steps) continue;
        char c = l->steps[s];
        if (c == 'X' || c == 'x') { out[k].inst = l->inst; out[k].vel = c == 'X' ? 110 : 80; k++; }
    }
    return k;
}

int beat_fill_hits(int b, int s, beat_hit_t *out, int max)
{
    if (b < 0 || b >= BEAT_COUNT || s < 0 || s > 15) return 0;
    return line_hits(FILLS[b].line, s, out, max);
}

int beat_hits(int b, int s, beat_hit_t *out, int max)
{
    if (b < 0 || b >= BEAT_COUNT || s < 0 || s > 15) return 0;
    int k = 0;
    for (int i = 0; i < 6 && k < max; i++) {
        const beat_line_t *l = &BEATS[b].line[i];
        if (!l->steps) continue;
        char c = l->steps[s];
        if (c == 'X' || c == 'x') { out[k].inst = l->inst; out[k].vel = c == 'X' ? 110 : 80; k++; }
    }
    return k;
}

uint32_t meter_bar(int meter)
{
    static const uint16_t BAR[4] = { 192, 288, 384, 288 };       /* ACC-206 */
    return meter >= 0 && meter < 4 ? BAR[meter] : 384u;
}

uint32_t meter_click(int meter) { return meter == METER_6_8 ? 48u : 96u; }

int metro_hits(int meter, uint32_t pos, beat_hit_t *out, int max)
{
    uint32_t b = pos % meter_bar(meter);
    if (max < 1 || b % meter_click(meter) != 0) return 0;
    out[0].inst = b == 0 || (meter == METER_6_8 && b == 144u) ? DRUM_CLICK_ACCENT : DRUM_CLICK;
    out[0].vel = 100;
    return 1;
}

const char *beat_name(int b) { return b >= 0 && b < BEAT_COUNT ? BEATS[b].name : ""; }

/* il catalogo dei kit (SND-541): i primi cinque qui, gli altri da drum_kits[] */
static const char *const KIT_SET[KIT_SYNTH0] STAME_ROM = { "kit_studio", "kit_jazz", "kit_808", "kit_techno", NULL };
static const char *const KIT_LABEL[KIT_SYNTH0] STAME_ROM = { "Studio", "Jazz", "808", "Techno", "Chip" };

const char *beat_kit_name(int i) { return i >= 0 && i < KIT_SYNTH0 ? KIT_SET[i] : NULL; }

const char *beat_kit_label(int i)
{
    if (i >= 0 && i < KIT_SYNTH0) return KIT_LABEL[i];
    return i >= KIT_SYNTH0 && i < KIT_COUNT ? drum_kits[i - KIT_SYNTH0].name : "";
}

const char *beat_kit_style(int i)
{
    static const char *const STYLE[KIT_SYNTH0] STAME_ROM = { "acoustic", "jazz", "analog", "techno", "classic" };
    if (i >= 0 && i < KIT_SYNTH0) return STYLE[i];
    return i >= KIT_SYNTH0 && i < KIT_COUNT ? drum_kits[i - KIT_SYNTH0].style : "";
}

const drum_kit_t *beat_kit_synth(int i) { return i >= KIT_SYNTH0 && i < KIT_COUNT ? &drum_kits[i - KIT_SYNTH0] : NULL; }
int beat_kit_of(int b) { return b >= 0 && b < BEAT_COUNT ? BEATS[b].kit : KIT_CHIP; }
const char *beat_kit(int b) { return beat_kit_name(beat_kit_of(b)); }
