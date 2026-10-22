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

static const groove_def_t GROOVES[INV_GROOVES] STAME_ROM = {
    /*                                                       0123456789abcdef */
    { "Techno", KIT_TECHNO, DRUM_CLAP, { DRUM_RIMSHOT, DRUM_COWBELL, DRUM_TOM_HI },
      { "9000900190009030",                                  /* cassa in quattro, una spinta prima del 4 */
        "0000800100008002",                                  /* battimani sul 2 e sul 4 */
        "3504350435043504",                                  /* sedicesimi fra un aperto e l'altro */
        "0070007000700070",                                  /* aperto in levare */
        "0002000300020020" } },
    { "Rock", KIT_STUDIO, DRUM_SNARE, { DRUM_TOM_LO, DRUM_TOM_HI, DRUM_COWBELL },
      { "9001000290500030",
        "0000900201009103",
        "8272827282728272",                                  /* crome, i sedicesimi solo in alto */
        "0000001000000030",
        "0000000000000223" } },                              /* i tom chiudono la battuta */
    { "Funk", KIT_STUDIO, DRUM_SNARE, { DRUM_CONGA, DRUM_COWBELL, DRUM_RIMSHOT },
      { "9003006020700401",
        "0200900403029031",                                  /* note fantasma attorno al 2 e al 4 */
        "7565756575657565",
        "0000002000000050",
        "0030000300300003" } },
    { "Break", KIT_808, DRUM_SNARE, { DRUM_RIMSHOT, DRUM_TOM_LO, DRUM_CONGA },
      { "9060000200840000",                                  /* la cassa spezzata del breakbeat */
        "0000900506009024",
        "7363736373637363",
        "0000000000000050",
        "0000000000000303" } },
    { "Halftime", KIT_808, DRUM_SNARE, { DRUM_CLAP, DRUM_RIMSHOT, DRUM_TOM_HI },
      { "9003002000620000",
        "0000000090000012",                                  /* il rullante sul 3 */
        "6353635363536353",
        "0000003000000020",
        "0000000060000000" } },
    { "Dub", KIT_TECHNO, DRUM_RIMSHOT, { DRUM_MARACAS, DRUM_CONGA, DRUM_TOM_LO },
      { "6000700090007000",                                  /* one drop in basso, steppers in alto */
        "0000300090004002",
        "0373037303730373",
        "0000000000000040",
        "4243424342434243" } },
    { "Bossa", KIT_JAZZ, DRUM_RIMSHOT, { DRUM_MARACAS, DRUM_CONGA, DRUM_COWBELL },
      { "9006800690068006",
        "8008008000800800",                                  /* la clave sul rimshot */
        "6262626262626262",
        "0000000000000000",
        "0404040404040404" } },
    { "Electro", KIT_808, DRUM_CLAP, { DRUM_COWBELL, DRUM_TOM_HI, DRUM_CONGA },
      { "9002006000703000",
        "0000900001009003",
        "6464646464646464",
        "0000000000000040",
        "0000030000030000" } },
    /* 18/10/2026, Luigi: «più cupi, più profondi, più grevi, più bassi, più acidi» */
    { "Acid", KIT_808, DRUM_CLAP, { DRUM_RIMSHOT, DRUM_COWBELL, DRUM_TOM_LO },
      { "9000900290009003",                                  /* cassa in quattro e due spinte */
        "0000800000008002",
        "4646464646464646",                                  /* i sedicesimi in levare più forti */
        "0070007000700070",
        "0003002000030020" } },
    { "Industrial", KIT_TECHNO, DRUM_SNARE, { DRUM_RIMSHOT, DRUM_COWBELL, DRUM_TOM_LO },
      { "9002700090027000",                                  /* la cassa che inciampa prima del 2 e del 4 */
        "0000900030009004",
        "5050505050505050",
        "0000000000000000",
        "0300030003000300" } },                              /* colpi di metallo in levare */
    /* 19/10/2026, Luigi: «una libreria enorme di batterie» (ACC-215, ACC-218): venti stili di genere, ognuno
     * con un kit della libreria sintetizzata (20 SND-541) */
    /*                                                       0123456789abcdef */
    { "House", KIT_SYN(DK_KIT_909_HOUSE), DRUM_CLAP, { DRUM_RIMSHOT, DRUM_CONGA, DRUM_COWBELL },
      { "9000900090009000",
        "0000900000009003",
        "7030603070306030",                                  /* il chiuso sui quarti strozza l'aperto */
        "0080008000800080",
        "0003002000300020" } },
    { "Garage", KIT_SYN(DK_KIT_2_STEP), DRUM_SNARE, { DRUM_RIMSHOT, DRUM_MARACAS, DRUM_CONGA },
      { "9000000020900030",                                  /* il due passi: la cassa salta il 2 e il 4 */
        "0000900000009002",
        "3060306030603060",
        "0000000000000040",
        "0002002000020020" } },
    { "Jungle", KIT_SYN(DK_KIT_JUNGLE), DRUM_SNARE, { DRUM_RIMSHOT, DRUM_TOM_HI, DRUM_CYMBAL },
      { "9070000000980000",                                  /* il break tagliato */
        "0000900603009006",
        "6464646464646464",
        "0000000000000050",
        "0000000000000303" } },
    { "DnB", KIT_SYN(DK_KIT_JUNGLE), DRUM_SNARE, { DRUM_RIMSHOT, DRUM_MARACAS, DRUM_CYMBAL },
      { "9000000000900030",
        "0000900000009002",
        "7363736373637363",
        "0000000000000040",
        "4242424242424242" } },
    { "Dubstep", KIT_SYN(DK_KIT_808_TRAP), DRUM_SNARE, { DRUM_RIMSHOT, DRUM_TOM_LO, DRUM_CLAP },
      { "9000000003600000",                                  /* metà tempo: il rullante sul 3 */
        "0000000090000001",
        "6030603060306030",
        "0000000000000050",
        "0000030000030000" } },
    { "Trap", KIT_SYN(DK_KIT_808_TRAP), DRUM_CLAP, { DRUM_RIMSHOT, DRUM_COWBELL, DRUM_TOM_HI },
      { "9000000300900000",
        "0000000090000000",
        "7474747474747575",                                  /* alle densità alte i rulli di charleston */
        "0000000000000030",
        "0000000000000203" } },
    { "Synthwave", KIT_SYN(DK_KIT_GATED_80S), DRUM_SNARE, { DRUM_TOM_HI, DRUM_CONGA, DRUM_TOM_LO },
      { "9000000090600000",
        "0000900000009000",
        "8282828282828282",
        "0000000000000030",
        "0000000000000234" } },                              /* i tom con il gate chiudono */
    { "Synthpop", KIT_SYN(DK_KIT_HEX_TOMS), DRUM_SNARE, { DRUM_TOM_HI, DRUM_TOM_LO, DRUM_CONGA },
      { "9000900090009000",
        "0000900000009000",
        "7373737373737373",
        "0000003000000030",
        "0000000300000032" } },
    { "Lo-Fi", KIT_SYN(DK_KIT_LO_FI_DUST), DRUM_SNARE, { DRUM_RIMSHOT, DRUM_MARACAS, DRUM_CONGA },
      { "9000000500900020",
        "0000900000009003",
        "7363736373637363",
        "0000000000000040",
        "0000000000030000" } },
    { "Trip Hop", KIT_SYN(DK_KIT_TAPE_CRATE), DRUM_SNARE, { DRUM_RIMSHOT, DRUM_TOM_LO, DRUM_CYMBAL },
      { "9000000090600000",
        "0000900000009000",
        "6262626262626262",
        "0000000000000300",
        "0000003000000000" } },
    { "Chiptune", KIT_SYN(DK_KIT_8_BIT), DRUM_SNARE, { DRUM_CONGA, DRUM_TOM_HI, DRUM_COWBELL },
      { "9003009090030090",
        "0000900000009002",
        "6565656565656565",
        "0000000000000000",
        "0040004000400040" } },
    { "Glitch", KIT_SYN(DK_KIT_GLITCH_BITS), DRUM_SNARE, { DRUM_CLAP, DRUM_TOM_LO, DRUM_CYMBAL },
      { "9004000402904000",
        "0000900300009300",
        "6353536356353563",
        "0000000000000000",
        "0300000300030003" } },
    { "EBM", KIT_SYN(DK_KIT_IRON_MILL), DRUM_SNARE, { DRUM_COWBELL, DRUM_TOM_LO, DRUM_RIMSHOT },
      { "9090909090909090",                                  /* la cassa a crome */
        "0000900000009000",
        "0070007000700070",
        "0000000000000000",
        "0000003000000030" } },
    { "Afrobeat", KIT_SYN(DK_KIT_AFRO_HAND), DRUM_SNARE, { DRUM_COWBELL, DRUM_CONGA, DRUM_MARACAS },
      { "9000009000900000",
        "0000900300009030",
        "7575757575757575",
        "0000000000000000",
        "8080080808008080" } },                              /* la campana */
    { "Tabla", KIT_SYN(DK_KIT_TABLA_MIST), DRUM_SNARE, { DRUM_RIMSHOT, DRUM_CONGA, DRUM_TOM_HI },
      { "9779977900000779",                                  /* il teental: il bayan tace nel khali */
        "0770077007700770",
        "3000300030003000",
        "0000000000000000",
        "9009900990099009" } },
    { "Salsa", KIT_SYN(DK_KIT_LATIN_PERC), DRUM_RIMSHOT, { DRUM_COWBELL, DRUM_CONGA, DRUM_TOM_HI },
      { "0006000000060000",
        "9009009000909000",                                  /* la clave 3-2 */
        "4343434343434343",
        "0000000000000000",
        "8080808080808080" } },
    { "Reggaeton", KIT_SYN(DK_KIT_808_BOOM), DRUM_SNARE, { DRUM_RIMSHOT, DRUM_CLAP, DRUM_TOM_HI },
      { "9000900090009000",
        "0009009000090090",                                  /* il dembow */
        "6363636363636363",
        "0000000000000000",
        "0000000000000303" } },
    { "Jazz", KIT_SYN(DK_KIT_BRUSHES), DRUM_SNARE, { DRUM_CYMBAL, DRUM_RIMSHOT, DRUM_TOM_LO },
      { "5000300050003000",
        "0000004000000040",
        "0000900000009000",                                  /* il piede sul 2 e sul 4 */
        "0000000000000000",
        "9000900690009006" } },                              /* il ride: ding, ding-a-ding */
    { "Arena", KIT_SYN(DK_KIT_STADIUM_ROCK), DRUM_SNARE, { DRUM_CYMBAL, DRUM_TOM_LO, DRUM_TOM_HI },
      { "9000000090500000",
        "0000900000009000",
        "8383838383838383",
        "0000000000000040",
        "7000000000000034" } },
    { "Preset", KIT_SYN(DK_KIT_606_TICK), DRUM_SNARE, { DRUM_COWBELL, DRUM_CONGA, DRUM_RIMSHOT },
      { "9000900090009000",                                  /* la scatola ritmica dei preset */
        "0000900000009000",
        "7575757575757575",
        "0000000000000060",
        "0030000300300003" } },
    /* 22/10/2026, Luigi: «suoni per fare PSYtrance e trance». Cassa in quattro e l'aperto in levare; nella
     * psy il battimani è leggero e i sedicesimi fra una cassa e l'altra li lascia al basso che rotola */
    /*                                                       0123456789abcdef */
    { "Trance", KIT_SYN(DK_KIT_TRANCE_ARENA), DRUM_CLAP, { DRUM_MARACAS, DRUM_RIMSHOT, DRUM_CYMBAL },
      { "9000900090009000",
        "0000900000009002",
        "6006600660066006",                                  /* il chiuso sul battito e sull'ultimo sedicesimo */
        "0090009000900090",
        "3434343434343434" } },                              /* lo shaker che corre */
    { "Psytrance", KIT_SYN(DK_KIT_PSY_FOREST), DRUM_CLAP, { DRUM_CONGA, DRUM_COWBELL, DRUM_TOM_HI },
      { "9000900090009000",
        "0000500000005003",
        "5450545054505450",
        "0080008000800080",
        "0003000200030020" } },                              /* i blip FM fra un battito e l'altro */
    { "Goa", KIT_SYN(DK_KIT_GOA_TEMPLE), DRUM_SNARE, { DRUM_CONGA, DRUM_COWBELL, DRUM_RIMSHOT },
      { "9000900090009003",
        "0000700000007003",
        "5454545454545454",
        "0070007000700070",
        "0002003000020030" } },                              /* il tamburo e la campanella del tempio */
    { "Progressive", KIT_SYN(DK_KIT_TRANCE_ARENA), DRUM_CLAP, { DRUM_RIMSHOT, DRUM_CONGA, DRUM_MARACAS },
      { "9000900090009000",
        "0000800000008000",
        "5363536353635363",
        "0060006000600060",
        "0002000200020302" } },
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

int inv_groove_kit(int groove) { return groove >= 0 && groove < INV_GROOVES ? GROOVES[groove].kit : KIT_STUDIO; }

int inv_groove_of_beat(int beat)
{
    /* Provvisorio, Funk, Bossa, Motorik, Lounge, Shuffle, Halftime, Boom Bap, Disco, Samba, Ballad, Train,
     * Chip, Techno, Dub, Acid, Industrial, Minimal, Electro, Trap; poi i Beat di genere del 19/10/2026: House,
     * Deep House, Tech House, Garage, Breakbeat, Jungle, Drum & Bass, Dubstep, Footwork, Robot, Synthwave,
     * Italo, Lo-Fi, Trip Hop, Ambient Pulse, Chiptune, Arcade, Glitch, IDM, EBM, Factory, Rave, Rock, Swing
     * Jazz, Brush Ballad, Afrobeat, Djembe, Teental, Rhythm Box, Gamelan, Salsa, Cumbia, Reggaeton, Dancehall,
     * Taiko, Maqsum, Flamenco, Unplugged, Sci-Fi, Steppers, Syndrum; Trance, Psytrance, Goa, Progressive
     * del 22/10/2026 (beat.c) */
    static const uint8_t G[BEAT_COUNT] = {
        1, 2, 6, 0, 6, 1, 4, 3, 0, 6, 1, 1, 7, 0, 5, 8, 9, 0, 7, 4,
        10, 10, 0, 11, 3, 12, 13, 14, 15, 7, 16, 17, 18, 19, 19, 20, 20, 21, 21, 22, 9,
        0, 28, 27, 27, 23, 23, 24, 29, 24, 25, 25, 26, 26, 23, 24, 25, 1, 7, 5, 17,
        30, 31, 32, 33 };
    return beat >= 0 && beat < BEAT_COUNT ? G[beat] : 0;
}

int inv_var_next(int var, uint32_t salt)
{
    int n = 1 + (int)(mix(salt * 0x85EBCA6Bu ^ (uint32_t)var * 0xC2B2AE35u) % (uint32_t)INV_VAR_MAX);
    return n == var ? n % INV_VAR_MAX + 1 : n;
}
