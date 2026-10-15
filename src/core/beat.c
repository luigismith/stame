/* beat.c — i pattern dei Beat, i loro kit e il metronomo (beat.h). */
#include "beat.h"
#include "../dsp/drums.h"

/* una riga per strumento: 16 passi, 'X' = colpo forte (110), 'x' = colpo (80), '.' = niente */
typedef struct { uint8_t inst; const char *steps; } beat_line_t;
typedef struct { const char *name; const char *kit; beat_line_t line[6]; } beat_def_t;

#define KIT_STUDIO "kit_studio"
#define KIT_JAZZ   "kit_jazz"
#define KIT_808    "kit_808"

static const beat_def_t BEATS[BEAT_COUNT] STAME_ROM = {
    /* ACC-210: il provvisorio della specifica, velocity 110 sui battiti e 80 sugli altri passi */
    { "Provvisorio", NULL, { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "....X.......X..." },
                             { DRUM_CLOSED_HAT, "X.x.X.x.X.x.X.x." } } },
    /* i Beat della vetrina (nomi e pattern di Stame, nessun dato dell'Orchid); i primi 6 dal 14/10,
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
    { "Chip", NULL, { { DRUM_KICK, "X...X..xX...X..." }, { DRUM_SNARE, "....X.......X..x" },
                      { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." }, { DRUM_COWBELL, "..x...x...x...x." },
                      { DRUM_TOM_HI, "..............x." } } },
};

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
const char *beat_kit(int b) { return b >= 0 && b < BEAT_COUNT ? BEATS[b].kit : NULL; }
