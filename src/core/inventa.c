/* inventa.c — la batteria che si inventa (inventa.h). Stili e priorità sono di Stame. */
#include "inventa.h"
#include "../dsp/drums.h"

/* uno stile: nome, kit di beat.h, strumento del rullante, tre percussioni fra cui la variazione sceglie, e
 * per ogni parte le priorità dei 16 passi della battuta, '0' (mai) … '9' (lo scheletro, sempre) */
typedef struct {
    const char *name;
    uint8_t kit, snare, perc[3];
    char lv[INV_PARTS][17];
} groove_def_t;

enum { KIT_I_STUDIO, KIT_I_JAZZ, KIT_I_808, KIT_I_TECHNO };   /* indici di beat_kit_name */

static const groove_def_t GROOVES[INV_GROOVES] STAME_ROM = {
    /*                                                       0123456789abcdef */
    { "Techno", KIT_I_TECHNO, DRUM_CLAP, { DRUM_RIMSHOT, DRUM_COWBELL, DRUM_TOM_HI },
      { "9000900190009030",                                  /* cassa in quattro, una spinta prima del 4 */
        "0000800100008002",                                  /* battimani sul 2 e sul 4 */
        "3504350435043504",                                  /* sedicesimi fra un aperto e l'altro */
        "0070007000700070",                                  /* aperto in levare */
        "0002000300020020" } },
    { "Rock", KIT_I_STUDIO, DRUM_SNARE, { DRUM_TOM_LO, DRUM_TOM_HI, DRUM_COWBELL },
      { "9001000290500030",
        "0000900201009103",
        "8272827282728272",                                  /* crome, i sedicesimi solo in alto */
        "0000001000000030",
        "0000000000000223" } },                              /* i tom chiudono la battuta */
    { "Funk", KIT_I_STUDIO, DRUM_SNARE, { DRUM_CONGA, DRUM_COWBELL, DRUM_RIMSHOT },
      { "9003006020700401",
        "0200900403029031",                                  /* note fantasma attorno al 2 e al 4 */
        "7565756575657565",
        "0000002000000050",
        "0030000300300003" } },
    { "Break", KIT_I_808, DRUM_SNARE, { DRUM_RIMSHOT, DRUM_TOM_LO, DRUM_CONGA },
      { "9060000200840000",                                  /* la cassa spezzata del breakbeat */
        "0000900506009024",
        "7363736373637363",
        "0000000000000050",
        "0000000000000303" } },
    { "Halftime", KIT_I_808, DRUM_SNARE, { DRUM_CLAP, DRUM_RIMSHOT, DRUM_TOM_HI },
      { "9003002000620000",
        "0000000090000012",                                  /* il rullante sul 3 */
        "6353635363536353",
        "0000003000000020",
        "0000000060000000" } },
    { "Dub", KIT_I_TECHNO, DRUM_RIMSHOT, { DRUM_MARACAS, DRUM_CONGA, DRUM_TOM_LO },
      { "6000700090007000",                                  /* one drop in basso, steppers in alto */
        "0000300090004002",
        "0373037303730373",
        "0000000000000040",
        "4243424342434243" } },
    { "Bossa", KIT_I_JAZZ, DRUM_RIMSHOT, { DRUM_MARACAS, DRUM_CONGA, DRUM_COWBELL },
      { "9006800690068006",
        "8008008000800800",                                  /* la clave sul rimshot */
        "6262626262626262",
        "0000000000000000",
        "0404040404040404" } },
    { "Electro", KIT_I_808, DRUM_CLAP, { DRUM_COWBELL, DRUM_TOM_HI, DRUM_CONGA },
      { "9002006000703000",
        "0000900001009003",
        "6464646464646464",
        "0000000000000040",
        "0000030000030000" } },
};

/* quanto la variazione può spostare ogni parte, in quarti: cassa e rullante tengono lo stile, le
 * percussioni si muovono di più */
static const uint8_t PESO[INV_PARTS] STAME_ROM = { 3, 3, 4, 3, 5 };

static uint32_t mix(uint32_t x)
{
    x ^= x >> 16; x *= 0x7FEB352Du;
    x ^= x >> 15; x *= 0x846CA68Bu;
    x ^= x >> 16;
    return x;
}

/* −128…127, sempre lo stesso per lo stesso stile, variazione, parte, passo e chiusa */
static int rnd(int groove, int var, int part, int s, int tail)
{
    uint32_t h = (uint32_t)var * 0x9E3779B9u ^ (uint32_t)groove << 24 ^ (uint32_t)part << 8 ^ (uint32_t)s ^
                 (uint32_t)tail << 16;
    return (int)(mix(h) & 0xFFu) - 128;
}

static int clampi(int v, int a, int b) { return v < a ? a : v > b ? b : v; }

void inv_build(inv_t *g, int groove, int var)
{
    groove = ((groove % INV_GROOVES) + INV_GROOVES) % INV_GROOVES;
    var = clampi(var, 0, INV_VAR_MAX);
    const groove_def_t *d = &GROOVES[groove];
    g->groove = (uint8_t)groove;
    g->var = (uint8_t)var;
    g->inst[INV_KICK] = DRUM_KICK;
    g->inst[INV_SNARE] = d->snare;
    g->inst[INV_HAT] = DRUM_CLOSED_HAT;
    g->inst[INV_OPEN] = DRUM_OPEN_HAT;
    g->inst[INV_PERC] = d->perc[var ? mix((uint32_t)var * 0x85EBCA6Bu ^ (uint32_t)groove) % 3u : 0u];
    /* lo spostamento massimo, in sedicesimi di livello: uno alla variazione 1, poi mezzo in più a scatto
     * fino a tre livelli */
    int a16 = var ? clampi(12 + 6 * (var - 1), 0, 48) : 0;
    for (int p = 0; p < INV_PARTS; p++)
        for (int step = 0; step < INV_STEPS; step++) {
            int s = step & 15, tail = step >= 28;              /* la chiusa: le ultime quattro sedicesimi */
            char c = d->lv[p][s];
            int lv = c >= '0' && c <= '9' ? c - '0' : 0, v;
            if (lv == 9) v = 144;                               /* lo scheletro non si sposta */
            else {
                v = lv * 16 + rnd(groove, var, p, s, tail) * a16 * PESO[p] / 512;
                if (tail && var && (p == INV_SNARE || p == INV_PERC)) v += 24;
                v = clampi(v, 0, 143);
            }
            g->lv[p][step] = (uint8_t)v;
        }
}

int inv_hits(const inv_t *g, const uint8_t dens[INV_PARTS], int step, bool fill, beat_hit_t *out, int max)
{
    static const uint8_t ORDINE[INV_PARTS] = { INV_KICK, INV_SNARE, INV_OPEN, INV_HAT, INV_PERC };
    if (step < 0 || step >= INV_STEPS) return 0;
    int s = step & 15, k = 0;
    bool open = false;
    for (int i = 0; i < INV_PARTS && k < max; i++) {
        int p = ORDINE[i], d = dens[p] > INV_DENS_MAX ? INV_DENS_MAX : dens[p], lv = g->lv[p][step];
        if (d == 0) continue;                                   /* una parte a 0 tace anche nel fill */
        if (fill) {
            d = d + 3 > INV_DENS_MAX ? INV_DENS_MAX : d + 3;
            if (s >= 12 && (p == INV_SNARE || p == INV_PERC)) lv += 48;
        }
        if (lv == 0 || lv < (INV_DENS_MAX - d) * 16) continue;
        if (p == INV_HAT && open) continue;                    /* aperto e chiuso non suonano insieme */
        if (p == INV_OPEN) open = true;
        int vel = 52 + lv * 7 / 16 + (s % 4 == 0 ? 6 : 0);
        out[k].inst = g->inst[p];
        out[k].vel = (uint8_t)(vel > 127 ? 127 : vel);
        k++;
    }
    return k;
}

const char *inv_groove_name(int groove)
{
    return groove >= 0 && groove < INV_GROOVES ? GROOVES[groove].name : "";
}

int inv_groove_kit(int groove) { return groove >= 0 && groove < INV_GROOVES ? GROOVES[groove].kit : KIT_I_STUDIO; }

int inv_groove_of_beat(int beat)
{
    /* Provvisorio, Funk, Bossa, Motorik, Lounge, Shuffle, Halftime, Boom Bap, Disco, Samba, Ballad, Train,
     * Chip, Techno, Dub (beat.c) */
    static const uint8_t G[BEAT_COUNT] = { 1, 2, 6, 0, 6, 1, 4, 3, 0, 6, 1, 1, 7, 0, 5 };
    return beat >= 0 && beat < BEAT_COUNT ? G[beat] : 0;
}

int inv_var_next(int var, uint32_t salt)
{
    int n = 1 + (int)(mix(salt * 0x85EBCA6Bu ^ (uint32_t)var * 0xC2B2AE35u) % (uint32_t)INV_VAR_MAX);
    return n == var ? n % INV_VAR_MAX + 1 : n;
}
