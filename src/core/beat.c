/* beat.c — i pattern dei Beat e il metronomo (beat.h). */
#include "beat.h"
#include "../dsp/drums.h"

/* una riga per strumento: 16 passi, 'X' = colpo forte (110), 'x' = colpo (80), '.' = niente */
typedef struct { uint8_t inst; const char *steps; } beat_line_t;
typedef struct { const char *name; beat_line_t line[5]; } beat_def_t;

static const beat_def_t BEATS[BEAT_COUNT] STAME_ROM = {
    /* ACC-210: il provvisorio della specifica, velocity 110 sui battiti e 80 sugli altri passi */
    { "Provvisorio", { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "....X.......X..." },
                       { DRUM_CLOSED_HAT, "X.x.X.x.X.x.X.x." } } },
    /* i 6 Beat della vetrina (nomi e pattern di Stame, nessun dato dell'Orchid) */
    { "Funk",     { { DRUM_KICK, "X.....X...X..x.." }, { DRUM_SNARE, "....X..x.x..X..x" },
                    { DRUM_CLOSED_HAT, "XxxxXxxxXxxxXxx." }, { DRUM_OPEN_HAT, "..............x." } } },
    { "Bossa",    { { DRUM_KICK, "X..xX..xX..xX..x" }, { DRUM_RIMSHOT, "X..X..X...X..X.." },
                    { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." } } },
    { "Motorik",  { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "....X.......X..." },
                    { DRUM_CLOSED_HAT, "X.x.X.x.X.x.X.x." } } },
    { "Lounge",   { { DRUM_KICK, "X.......X.x....." }, { DRUM_RIMSHOT, "....X.......X..." },
                    { DRUM_CLOSED_HAT, "x.xxx.xxx.xxx.xx" }, { DRUM_MARACAS, "..x...x...x...x." } } },
    { "Shuffle",  { { DRUM_KICK, "X.......X..x...." }, { DRUM_SNARE, "....X.......X..." },
                    { DRUM_CLOSED_HAT, "X..xX..xX..xX..x" } } },
    { "Halftime", { { DRUM_KICK, "X.........X....." }, { DRUM_SNARE, "........X......." },
                    { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." }, { DRUM_CLAP, "........X......." } } },
};

int beat_hits(int b, int s, beat_hit_t *out, int max)
{
    if (b < 0 || b >= BEAT_COUNT || s < 0 || s > 15) return 0;
    int k = 0;
    for (int i = 0; i < 5 && k < max; i++) {
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
