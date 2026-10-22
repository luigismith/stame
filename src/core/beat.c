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
    /* 19/10/2026, Luigi: «voglio anche una libreria enorme di batterie» (ACC-218): quarantuno Beat di
     * genere, ognuno con un kit della libreria sintetizzata (20 SND-541) */
    { "House", KIT_SYN(DK_KIT_909_HOUSE), { { DRUM_KICK, "X...X...X...X..." }, { DRUM_CLAP, "....X.......X..." },
        { DRUM_CLOSED_HAT, "x...x...x...x..." }, { DRUM_OPEN_HAT, "..X...X...X...X." }, { DRUM_RIMSHOT, ".......x......x." } } },
    { "Deep House", KIT_SYN(DK_KIT_909_HOUSE), { { DRUM_KICK, "X...X...X...X..." }, { DRUM_RIMSHOT, "...x..x....x..x." },
        { DRUM_OPEN_HAT, "..x...x...x...x." }, { DRUM_CLAP, "....X.......X..." }, { DRUM_MARACAS, "x.xxx.xxx.xxx.xx" },
        { DRUM_CONGA, "......x.......x." } } },
    { "Tech House", KIT_SYN(DK_KIT_MINIMAL_CLICK), { { DRUM_KICK, "X...X...X...X..." }, { DRUM_CLAP, "....X.......X..." },
        { DRUM_CLOSED_HAT, "x.xxx.xxx.xxx.xx" }, { DRUM_RIMSHOT, "..x....x..x..x.." }, { DRUM_COWBELL, "......x.......x." },
        { DRUM_CONGA, "...x.......x...." } } },
    { "Garage", KIT_SYN(DK_KIT_2_STEP), { { DRUM_KICK, "X.........X..x.." }, { DRUM_SNARE, "....X.......X..." },
        { DRUM_CLOSED_HAT, "..x...x...x...x." }, { DRUM_RIMSHOT, "...x..x.....x..." }, { DRUM_MARACAS, "x.xxx.xxx.xxx.xx" } } },
    { "Breakbeat", KIT_SYN(DK_KIT_JUNGLE), { { DRUM_KICK, "X.....X...X....." }, { DRUM_SNARE, "....X.......X..." },
        { DRUM_CLOSED_HAT, "x.x.x...x.x.x..." }, { DRUM_OPEN_HAT, "......x.......x." } } },
    { "Jungle", KIT_SYN(DK_KIT_JUNGLE), { { DRUM_KICK, "X.X.......XX...." }, { DRUM_SNARE, "....X..X.X..X..X" },
        { DRUM_CLOSED_HAT, "x.xxx.xxx.xxx.xx" }, { DRUM_CYMBAL, "X..............." } } },
    { "Drum & Bass", KIT_SYN(DK_KIT_JUNGLE), { { DRUM_KICK, "X.........X....." }, { DRUM_SNARE, "....X.......X..." },
        { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." }, { DRUM_MARACAS, "xxxxxxxxxxxxxxxx" } } },
    { "Dubstep", KIT_SYN(DK_KIT_IRON_MILL), { { DRUM_KICK, "X.........X....." }, { DRUM_SNARE, "........X......." },
        { DRUM_CLOSED_HAT, "x..x..x.x..x..x." }, { DRUM_RIMSHOT, ".....x.......x.." } } },
    { "Footwork", KIT_SYN(DK_KIT_808_TRAP), { { DRUM_KICK, "X..X..X.X..X..X." }, { DRUM_CLAP, "....X.......X..." },
        { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." }, { DRUM_RIMSHOT, "..x..x....x..x.." } } },
    { "Robot", KIT_SYN(DK_KIT_ROBOT_POP), { { DRUM_KICK, "X.....X.X......." }, { DRUM_SNARE, "....X.......X..." },
        { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." }, { DRUM_TOM_HI, "...x......x....." }, { DRUM_COWBELL, "..x.....x.x....." } } },
    { "Synthwave", KIT_SYN(DK_KIT_GATED_80S), { { DRUM_KICK, "X.......X.X....." }, { DRUM_SNARE, "....X.......X..." },
        { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." }, { DRUM_CYMBAL, "X..............." } } },
    { "Italo", KIT_SYN(DK_KIT_LINN_POP), { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "....X.......X..." },
        { DRUM_OPEN_HAT, "..X...X...X...X." }, { DRUM_CLOSED_HAT, "x...x...x...x..." }, { DRUM_MARACAS, "....x.......x..." } } },
    { "Lo-Fi", KIT_SYN(DK_KIT_LO_FI_DUST), { { DRUM_KICK, "X......X..X....." }, { DRUM_SNARE, "....X.......X..." },
        { DRUM_CLOSED_HAT, "x.x.x.xxx.x.x.x." }, { DRUM_RIMSHOT, "...........x...." } } },
    { "Trip Hop", KIT_SYN(DK_KIT_TAPE_CRATE), { { DRUM_KICK, "X.......X.x....." }, { DRUM_SNARE, "....X.......X..." },
        { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." }, { DRUM_OPEN_HAT, ".............x.." }, { DRUM_RIMSHOT, "......x........." } } },
    { "Ambient Pulse", KIT_SYN(DK_KIT_DEEP_SPACE), { { DRUM_KICK, "X.......X......." }, { DRUM_RIMSHOT, "......x.......x." },
        { DRUM_OPEN_HAT, "....x.......x..." }, { DRUM_MARACAS, "x.x.x.x.x.x.x.x." }, { DRUM_CYMBAL, "X..............." } } },
    { "Chiptune", KIT_SYN(DK_KIT_8_BIT), { { DRUM_KICK, "X..X..X.X..X..X." }, { DRUM_SNARE, "....X.......X..." },
        { DRUM_CLOSED_HAT, "xxxxxxxxxxxxxxxx" }, { DRUM_CONGA, "..x...x...x...x." } } },
    { "Arcade", KIT_SYN(DK_KIT_ARCADE), { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "....X.......X..." },
        { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." }, { DRUM_COWBELL, "..x.......x....." }, { DRUM_TOM_HI, ".......x.......x" } } },
    { "Glitch", KIT_SYN(DK_KIT_GLITCH_BITS), { { DRUM_KICK, "X..x...x..X.x..." }, { DRUM_SNARE, "....X..x....Xx.." },
        { DRUM_CLOSED_HAT, "x.xx.x..xx.x.xx." }, { DRUM_CLAP, "...........x..x." }, { DRUM_CYMBAL, "........X......." } } },
    { "IDM", KIT_SYN(DK_KIT_DATA_ROT), { { DRUM_KICK, "X....x..X..x...." }, { DRUM_SNARE, "....X.....x.X..." },
        { DRUM_CLOSED_HAT, "xx.x.xx.xx.x.xx." }, { DRUM_TOM_LO, "......x.......x." }, { DRUM_COWBELL, "...x.......x...." } } },
    { "EBM", KIT_SYN(DK_KIT_IRON_MILL), { { DRUM_KICK, "X.X.X.X.X.X.X.X." }, { DRUM_SNARE, "....X.......X..." },
        { DRUM_CLOSED_HAT, "..x...x...x...x." }, { DRUM_COWBELL, "......x.......x." } } },
    { "Factory", KIT_SYN(DK_KIT_SCRAP_YARD), { { DRUM_KICK, "X...X..xX...X..." }, { DRUM_SNARE, "....X.......X..x" },
        { DRUM_RIMSHOT, "..x...x...x...x." }, { DRUM_COWBELL, "x...x...x...x..." }, { DRUM_CONGA, ".x.....x.x.....x" } } },
    { "Rave", KIT_SYN(DK_KIT_909_RAVE), { { DRUM_KICK, "X...X...X...X..." }, { DRUM_CLAP, "....X.......X..." },
        { DRUM_OPEN_HAT, "..X...X...X...X." }, { DRUM_CLOSED_HAT, "x...x...x...x..." }, { DRUM_TOM_HI, "..........x....x" } } },
    { "Rock", KIT_SYN(DK_KIT_ACOUSTIC_ROOM), { { DRUM_KICK, "X.......X.X....." }, { DRUM_SNARE, "....X.......X..." },
        { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." }, { DRUM_CYMBAL, "X..............." } } },
    { "Swing Jazz", KIT_SYN(DK_KIT_BRUSHES), { { DRUM_CYMBAL, "X...X..xX...X..x" }, { DRUM_CLOSED_HAT, "....X.......X..." },
        { DRUM_KICK, "x.......x......." }, { DRUM_SNARE, "......x.......x." }, { DRUM_RIMSHOT, "..........x....." } } },
    { "Brush Ballad", KIT_SYN(DK_KIT_BRUSHES), { { DRUM_SNARE, "x.x.x.x.x.x.x.x." }, { DRUM_KICK, "X.......X......." },
        { DRUM_CLOSED_HAT, "....x.......x..." }, { DRUM_CLAP, "x.......x......." }, { DRUM_CYMBAL, "X..............." } } },
    { "Afrobeat", KIT_SYN(DK_KIT_AFRO_HAND), { { DRUM_KICK, "X.....X...X....." }, { DRUM_SNARE, "....X..x....X.x." },
        { DRUM_CLOSED_HAT, "xxxxxxxxxxxxxxxx" }, { DRUM_COWBELL, "X.X..X.X.X..X.X." }, { DRUM_CONGA, "..x...x...xx..x." } } },
    { "Djembe", KIT_SYN(DK_KIT_AFRO_HAND), { { DRUM_KICK, "X.....X...X....." }, { DRUM_RIMSHOT, "...X......X..X.." },
        { DRUM_SNARE, ".x..x.x.x..x.x.." }, { DRUM_TOM_LO, "X.......X......." }, { DRUM_TOM_HI, "....x.x.....x.x." },
        { DRUM_OPEN_HAT, "..x...x...x...x." } } },
    /* il teental in sedici matra: dha dhin dhin dha | dha dhin dhin dha | dha tin tin ta | ta dhin dhin dha;
     * il bayan sui dha e i dhin (non nel khali), il dayan na sui dha e i ta, tin sui dhin e i tin */
    { "Teental", KIT_SYN(DK_KIT_TABLA_MIST), { { DRUM_KICK, "XxxXXxxX.....xxX" }, { DRUM_RIMSHOT, "X..XX..XX..XX..X" },
        { DRUM_SNARE, ".xx..xx..xx..xx." } } },
    { "Rhythm Box", KIT_SYN(DK_KIT_CR_RHYTHM), { { DRUM_KICK, "X.....X.X......." }, { DRUM_RIMSHOT, "X..X..X...X.X..." },
        { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." }, { DRUM_TOM_LO, "......x.......x." }, { DRUM_TOM_HI, "..x.x...x.x....x" },
        { DRUM_MARACAS, "xxxxxxxxxxxxxxxx" } } },
    /* il ciclo del gamelan in una battuta: il gong all'inizio, kempul a metà, kenong sui quarti pari */
    { "Gamelan", KIT_SYN(DK_KIT_GAMELAN), { { DRUM_CYMBAL, "X..............." }, { DRUM_TOM_LO, "........X......." },
        { DRUM_COWBELL, "....X.......X..." }, { DRUM_OPEN_HAT, "..x...x...x...x." }, { DRUM_CONGA, "x.x.x.x.x.x.x.x." },
        { DRUM_KICK, "X..x..x...x..x.." } } },
    { "Salsa", KIT_SYN(DK_KIT_LATIN_PERC), { { DRUM_RIMSHOT, "X..X..X...X.X..." }, { DRUM_COWBELL, "X...X...X...X..." },
        { DRUM_CONGA, "..x...X...x...X." }, { DRUM_TOM_HI, "x.xxx.xxx.xxx.xx" }, { DRUM_KICK, "...x.......x...." },
        { DRUM_MARACAS, "x.x.x.x.x.x.x.x." } } },
    { "Cumbia", KIT_SYN(DK_KIT_LATIN_PERC), { { DRUM_KICK, "X...X...X...X..." }, { DRUM_CLAP, "X.xXX.xXX.xXX.xX" },
        { DRUM_CONGA, "..X...X...X...X." }, { DRUM_MARACAS, "x.x.x.x.x.x.x.x." } } },
    { "Reggaeton", KIT_SYN(DK_KIT_808_BOOM), { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "...X..X....X..X." },
        { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." } } },
    { "Dancehall", KIT_SYN(DK_KIT_808_BOOM), { { DRUM_KICK, "X.....X.X......." }, { DRUM_SNARE, "....X.......X..." },
        { DRUM_RIMSHOT, "...x..x....x..x." }, { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." } } },
    { "Taiko", KIT_SYN(DK_KIT_TAIKO), { { DRUM_KICK, "X.......X.X....." }, { DRUM_SNARE, "x.x.x.x.x.x.x.x." },
        { DRUM_RIMSHOT, "....X.......X..." }, { DRUM_COWBELL, "X...X...X...X..." }, { DRUM_TOM_LO, "......X.......X." } } },
    /* il maqsum: dum tek . tek dum . tek . in crome */
    { "Maqsum", KIT_SYN(DK_KIT_DARBUKA_SAND), { { DRUM_KICK, "X.......X......." }, { DRUM_RIMSHOT, "..X...X.....X..." },
        { DRUM_SNARE, ".x.x...x.x.x...x" }, { DRUM_CLAP, "x...x...x...x..." }, { DRUM_TOM_LO, "X..............." } } },
    { "Flamenco", KIT_SYN(DK_KIT_CAJON_BOX), { { DRUM_KICK, "X..X..X...X..X.." }, { DRUM_SNARE, "....X.......X..." },
        { DRUM_CLAP, "..x..x..x...x.x." }, { DRUM_CLOSED_HAT, "xxxxxxxxxxxxxxxx" } } },
    { "Unplugged", KIT_SYN(DK_KIT_CAJON_BOX), { { DRUM_KICK, "X.......X.X....." }, { DRUM_SNARE, "....X.......X..." },
        { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." }, { DRUM_MARACAS, "x.xxx.xxx.xxx.xx" }, { DRUM_COWBELL, "..............x." } } },
    { "Sci-Fi", KIT_SYN(DK_KIT_LASER_LAB), { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "....X.......X..." },
        { DRUM_TOM_LO, "..x.......x....." }, { DRUM_TOM_HI, "......x.......x." }, { DRUM_CLOSED_HAT, "xx.xxx.xxx.xxx.x" } } },
    { "Steppers", KIT_SYN(DK_KIT_DUB_YARD), { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "........X......." },
        { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." }, { DRUM_RIMSHOT, "....x.......x..." }, { DRUM_TOM_HI, "..............x." } } },
    { "Syndrum", KIT_SYN(DK_KIT_SYNDRUM_DISCO), { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "....X.......X..." },
        { DRUM_OPEN_HAT, "..X...X...X...X." }, { DRUM_CLOSED_HAT, "x...x...x...x..." }, { DRUM_CONGA, ".......x........" },
        { DRUM_TOM_HI, "...............x" } } },
    /* 22/10/2026, Luigi: «suoni per fare PSYtrance e trance» (ACC-218): i kit della trance e della psy */
    { "Trance", KIT_SYN(DK_KIT_TRANCE_ARENA), { { DRUM_KICK, "X...X...X...X..." }, { DRUM_CLAP, "....X.......X..." },
        { DRUM_OPEN_HAT, "..X...X...X...X." }, { DRUM_CLOSED_HAT, "x..xx..xx..xx..x" }, { DRUM_MARACAS, ".x.x.x.x.x.x.x.x" } } },
    { "Psytrance", KIT_SYN(DK_KIT_PSY_FOREST), { { DRUM_KICK, "X...X...X...X..." }, { DRUM_OPEN_HAT, "..X...X...X...X." },
        { DRUM_CLOSED_HAT, "xx.xxx.xxx.xxx.x" }, { DRUM_CLAP, "....x.......x..." }, { DRUM_CONGA, ".......x.....x.." } } },
    { "Goa", KIT_SYN(DK_KIT_GOA_TEMPLE), { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "....X.......X..." },
        { DRUM_OPEN_HAT, "..X...X...X...X." }, { DRUM_CLOSED_HAT, "xx.xxx.xxx.xxx.x" }, { DRUM_CONGA, "......x.......x." },
        { DRUM_COWBELL, "...........x...." } } },
    { "Progressive", KIT_SYN(DK_KIT_TRANCE_ARENA), { { DRUM_KICK, "X...X...X...X..." }, { DRUM_CLAP, "....x.......x..." },
        { DRUM_CLOSED_HAT, "xx.xxx.xxx.xxx.x" }, { DRUM_OPEN_HAT, "..x...x...x...x." }, { DRUM_RIMSHOT, "......x.....x..x" },
        { DRUM_CONGA, ".x.......x......" } } },
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
    /* i fill dei Beat di genere (19/10/2026, ACC-218) */
    { { { DRUM_KICK, "X...X...X...X.X." }, { DRUM_CLAP, "....X...X.X.XXXX" }, { DRUM_OPEN_HAT, "..X...X...X....." },
        { DRUM_CLOSED_HAT, "x...x...x...x..." }, { DRUM_TOM_HI, "..........x.x..." }, { DRUM_TOM_LO, "...........x.x.." } } },
    { { { DRUM_KICK, "X...X...X...X..." }, { DRUM_RIMSHOT, "...x..x..x.xxxxx" }, { DRUM_OPEN_HAT, "..x...x...x....." },
        { DRUM_CLAP, "....X.......X.X." }, { DRUM_MARACAS, "x.xxx.xxx.xxxxxx" }, { DRUM_CONGA, "......x...x.x.xx" } } },
    { { { DRUM_KICK, "X...X...X...X..." }, { DRUM_CLAP, "....X.......XXXX" }, { DRUM_CLOSED_HAT, "x.xxx.xxx.xxxxxx" },
        { DRUM_RIMSHOT, "..x....x.xxx.xxx" }, { DRUM_COWBELL, "......x...x.x.x." }, { DRUM_CONGA, "...x.......x.x.x" } } },
    { { { DRUM_KICK, "X.........X.X.X." }, { DRUM_SNARE, "....X.....X.XXXX" }, { DRUM_CLOSED_HAT, "..x...x...x....." },
        { DRUM_RIMSHOT, "...x..x..x.x.xxx" }, { DRUM_MARACAS, "x.xxx.xxx.xxxxxx" } } },
    { { { DRUM_KICK, "X.....X...X.X..." }, { DRUM_SNARE, "....X...X.XxXXXX" }, { DRUM_CLOSED_HAT, "x.x.x...x.x....." },
        { DRUM_OPEN_HAT, "......x........." }, { DRUM_TOM_LO, "..........x...x." } } },
    { { { DRUM_KICK, "X.X.......X.X..." }, { DRUM_SNARE, "....X..X.XxXXxXX" }, { DRUM_CLOSED_HAT, "x.xxx.xxx......." },
        { DRUM_CYMBAL, "X..............." }, { DRUM_TOM_HI, "........x..x...." }, { DRUM_TOM_LO, "..........x..x.." } } },
    { { { DRUM_KICK, "X.........X.X..." }, { DRUM_SNARE, "....X...X.XxXXXX" }, { DRUM_CLOSED_HAT, "x.x.x.x.x.x....." },
        { DRUM_MARACAS, "xxxxxxxxxxxxxxxx" }, { DRUM_CYMBAL, "X..............." } } },
    { { { DRUM_KICK, "X.........X.X.X." }, { DRUM_SNARE, "........X...XXXX" }, { DRUM_CLOSED_HAT, "x..x..x.x..x...." },
        { DRUM_TOM_LO, "..........x.x..." } } },
    { { { DRUM_KICK, "X..X..X.X..X.XXX" }, { DRUM_CLAP, "....X...X...XXXX" }, { DRUM_CLOSED_HAT, "x.x.x.x.xxxxxxxx" },
        { DRUM_RIMSHOT, "..x..x....x..x.." } } },
    { { { DRUM_KICK, "X.....X.X.....X." }, { DRUM_SNARE, "....X.......X.XX" }, { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." },
        { DRUM_TOM_HI, "...x..x...x.x.x." }, { DRUM_TOM_LO, "............x.x." }, { DRUM_COWBELL, "..x.....x.x....." } } },
    { { { DRUM_KICK, "X.......X.X....." }, { DRUM_SNARE, "....X.......X..." }, { DRUM_CLOSED_HAT, "x.x.x.x.x......." },
        { DRUM_TOM_HI, "........X.X....." }, { DRUM_CONGA, "............X.X." }, { DRUM_TOM_LO, ".............X.X" } } },
    { { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "....X...X.X.XXXX" }, { DRUM_OPEN_HAT, "..X...X........." },
        { DRUM_CLOSED_HAT, "x...x...x......." }, { DRUM_TOM_HI, "..........x.x..." }, { DRUM_TOM_LO, "............x.x." } } },
    { { { DRUM_KICK, "X......X..X....." }, { DRUM_SNARE, "....X.......X.xX" }, { DRUM_CLOSED_HAT, "x.x.x.xxx.x....." },
        { DRUM_RIMSHOT, "...........x...." }, { DRUM_TOM_LO, "..........x...x." } } },
    { { { DRUM_KICK, "X.......X.x....." }, { DRUM_SNARE, "....X.......X.XX" }, { DRUM_CLOSED_HAT, "x.x.x.x.x.x....." },
        { DRUM_TOM_LO, "..........x.x..." }, { DRUM_CYMBAL, "X..............." } } },
    { { { DRUM_KICK, "X.......X...X..." }, { DRUM_RIMSHOT, "......x...x.x.x." }, { DRUM_OPEN_HAT, "....x.......x..." },
        { DRUM_MARACAS, "x.x.x.x.xxxxxxxx" }, { DRUM_CYMBAL, "X..............." } } },
    { { { DRUM_KICK, "X..X..X.X..X..X." }, { DRUM_SNARE, "....X...X.X.XXXX" }, { DRUM_CLOSED_HAT, "xxxxxxxxxxxx...." },
        { DRUM_TOM_HI, "............X.X." }, { DRUM_TOM_LO, ".............X.X" } } },
    { { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "....X...XXXXXXXX" }, { DRUM_CLOSED_HAT, "x.x.x.x........." },
        { DRUM_TOM_HI, "........x.x.x.x." }, { DRUM_TOM_LO, ".........x.x.x.x" } } },
    { { { DRUM_KICK, "X..x...x..X.xxxx" }, { DRUM_SNARE, "....X..x..xxXXXX" }, { DRUM_CLOSED_HAT, "x.xx.x..xx.x...." },
        { DRUM_CLAP, "...........x.xxx" } } },
    { { { DRUM_KICK, "X....x..X..x.xxx" }, { DRUM_SNARE, "....X.....x.XXXX" }, { DRUM_CLOSED_HAT, "xx.x.xx.xx.x...." },
        { DRUM_TOM_LO, "......x...x.x.x." }, { DRUM_TOM_HI, "...........x.x.x" } } },
    { { { DRUM_KICK, "X.X.X.X.X.X.X.X." }, { DRUM_SNARE, "....X.......XXXX" }, { DRUM_CLOSED_HAT, "..x...x...x....." },
        { DRUM_TOM_LO, "..........x.x..." }, { DRUM_TOM_HI, "...........x.x.." } } },
    { { { DRUM_KICK, "X...X..xX...X.X." }, { DRUM_SNARE, "....X.......XXXX" }, { DRUM_RIMSHOT, "..x...x.xxxxxxxx" },
        { DRUM_COWBELL, "x...x...x......." }, { DRUM_CONGA, ".x.....x.x.x.x.x" } } },
    { { { DRUM_KICK, "X...X...X...X..." }, { DRUM_CLAP, "....X...X.X.XXXX" }, { DRUM_OPEN_HAT, "..X...X...X....." },
        { DRUM_CLOSED_HAT, "x...x...x...x..." }, { DRUM_TOM_HI, "........x.x.x.x." }, { DRUM_TOM_LO, ".........x.x.x.x" } } },
    { { { DRUM_KICK, "X.......X......." }, { DRUM_SNARE, "....X...X.X....." }, { DRUM_TOM_HI, "............X.X." },
        { DRUM_CONGA, ".............X.X" }, { DRUM_TOM_LO, "..............XX" }, { DRUM_CYMBAL, "X..............." } } },
    { { { DRUM_CYMBAL, "X...X..xX...X..x" }, { DRUM_CLOSED_HAT, "....X.......X..." }, { DRUM_KICK, "x.......x.....X." },
        { DRUM_SNARE, "......x.x.x.xxxx" }, { DRUM_TOM_HI, "..........x.x..." }, { DRUM_TOM_LO, "...........x.x.." } } },
    { { { DRUM_SNARE, "x.x.x.x.x.xxxxxx" }, { DRUM_KICK, "X.......X......." }, { DRUM_CLOSED_HAT, "....x.......x..." },
        { DRUM_TOM_LO, "............x.x." }, { DRUM_CYMBAL, "X..............." } } },
    { { { DRUM_KICK, "X.....X...X.X.X." }, { DRUM_SNARE, "....X..x..x.XXXX" }, { DRUM_CLOSED_HAT, "xxxxxxxxxxxxxxxx" },
        { DRUM_COWBELL, "X.X..X.X.X..X.X." }, { DRUM_CONGA, "..x...x...xx.xxx" } } },
    { { { DRUM_KICK, "X.....X...X....." }, { DRUM_RIMSHOT, "...X......XXXXXX" }, { DRUM_SNARE, ".x..x.x.x......." },
        { DRUM_TOM_LO, "X.......X......." }, { DRUM_TOM_HI, "....x.x.....x.x." }, { DRUM_OPEN_HAT, "..x...x...x...x." } } },
    /* la chiusa del teental: il ritornello del dayan tre volte, come una tihai */
    { { { DRUM_KICK, "XxxXXxxX.....xxX" }, { DRUM_RIMSHOT, "X..XX..XX.XXX.XX" }, { DRUM_SNARE, ".xx..xx..x...x.." },
        { DRUM_CONGA, "........x.x.x.x." } } },
    { { { DRUM_KICK, "X.....X.X......." }, { DRUM_RIMSHOT, "X..X..X...X.X..." }, { DRUM_CLOSED_HAT, "x.x.x.x.x.x.x.x." },
        { DRUM_TOM_LO, "......x...x.x.x." }, { DRUM_TOM_HI, "..x.x...x.x.xxxx" }, { DRUM_COWBELL, "X..............." } } },
    { { { DRUM_CYMBAL, "X..............." }, { DRUM_TOM_LO, "........X......." }, { DRUM_COWBELL, "....X...X...X..." },
        { DRUM_OPEN_HAT, "..x...x...x...x." }, { DRUM_CONGA, "xxxxxxxxxxxxxxxx" }, { DRUM_KICK, "X..x..x.X.x.xxxx" } } },
    { { { DRUM_RIMSHOT, "X..X..X...X.X..." }, { DRUM_COWBELL, "X...X...X...X..." }, { DRUM_CONGA, "..x...X...x.xxXX" },
        { DRUM_TOM_HI, "x.xxx.xxx.xxxxxx" }, { DRUM_SNARE, "........x.x.xxxx" }, { DRUM_KICK, "...x.......x...." } } },
    { { { DRUM_KICK, "X...X...X...X..." }, { DRUM_CLAP, "X.xXX.xXX.xXX.xX" }, { DRUM_CONGA, "..X...X...X.XXXX" },
        { DRUM_SNARE, "............x.xx" }, { DRUM_MARACAS, "x.x.x.x.x.x.x.x." } } },
    { { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "...X..X..X.XXXXX" }, { DRUM_CLOSED_HAT, "x.x.x.x.x.x....." },
        { DRUM_TOM_LO, "............x.x." } } },
    { { { DRUM_KICK, "X.....X.X.....X." }, { DRUM_SNARE, "....X.......XXXX" }, { DRUM_RIMSHOT, "...x..x.xxxx..x." },
        { DRUM_CLOSED_HAT, "x.x.x.x.x.x....." } } },
    { { { DRUM_KICK, "X.......X.X.X.X." }, { DRUM_SNARE, "x.x.x.x.xxxxxxxx" }, { DRUM_RIMSHOT, "....X.......X..." },
        { DRUM_COWBELL, "X...X...X...X..." }, { DRUM_TOM_LO, "......X...X.X.XX" }, { DRUM_TOM_HI, "...........X.X.X" } } },
    { { { DRUM_KICK, "X.......X......." }, { DRUM_RIMSHOT, "..X...X.....XXXX" }, { DRUM_SNARE, ".x.x...x.xxx...." },
        { DRUM_CLAP, "x...x...x...x..." }, { DRUM_TOM_LO, "........X.X.X..." } } },
    { { { DRUM_KICK, "X..X..X...X..X.." }, { DRUM_SNARE, "....X...X.X.XXXX" }, { DRUM_CLAP, "..x..x..x.x.x.xx" },
        { DRUM_CLOSED_HAT, "xxxxxxxxxxxxxxxx" } } },
    { { { DRUM_KICK, "X.......X.X....." }, { DRUM_SNARE, "....X...X.X.XXXX" }, { DRUM_CLOSED_HAT, "x.x.x.x.x.x....." },
        { DRUM_MARACAS, "x.xxx.xxx.xxxxxx" }, { DRUM_TOM_HI, "............x.x." }, { DRUM_TOM_LO, ".............x.x" } } },
    { { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "....X...X.X.XXXX" }, { DRUM_TOM_LO, "..x.......x.x.x." },
        { DRUM_TOM_HI, "......x....x.x.x" }, { DRUM_CLOSED_HAT, "xx.xxx.xxx......" }, { DRUM_CYMBAL, "........X......." } } },
    { { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "........X...X.XX" }, { DRUM_CLOSED_HAT, "x.x.x.x.x.x....." },
        { DRUM_RIMSHOT, "....x.......x..." }, { DRUM_TOM_HI, "..........x...x." }, { DRUM_TOM_LO, "...........x.x.x" } } },
    { { { DRUM_KICK, "X...X...X...X..." }, { DRUM_SNARE, "....X.......X..." }, { DRUM_OPEN_HAT, "..X...X...X....." },
        { DRUM_TOM_HI, "........x.x.x.x." }, { DRUM_CONGA, ".........x.x.x.x" }, { DRUM_TOM_LO, "............X..X" } } },
    /* trance e psy (22/10/2026): la cassa non si ferma, il battimani o i tom rullano, la psy chiude con i blip */
    { { { DRUM_KICK, "X...X...X...X..." }, { DRUM_CLAP, "....X...X.X.XXXX" }, { DRUM_OPEN_HAT, "..X...X...X....." },
        { DRUM_CLOSED_HAT, "x..xx..xx..x...." }, { DRUM_CYMBAL, "...............X" } } },
    { { { DRUM_KICK, "X...X...X...X..." }, { DRUM_OPEN_HAT, "..X...X...X....." }, { DRUM_TOM_HI, "........x.x.x.x." },
        { DRUM_TOM_LO, ".........x.x.x.x" }, { DRUM_CONGA, "..x...x.xxxxxxxx" } } },
    { { { DRUM_KICK, "X...X...X...X.X." }, { DRUM_SNARE, "....X...X.X.XXXX" }, { DRUM_OPEN_HAT, "..X...X...X....." },
        { DRUM_CONGA, "......x...x.xxxx" }, { DRUM_COWBELL, "x.......x.x.x.x." } } },
    { { { DRUM_KICK, "X...X...X...X..." }, { DRUM_CLAP, "....x...x.x.xxXX" }, { DRUM_RIMSHOT, "......x.x.xxxxxx" },
        { DRUM_OPEN_HAT, "..x...x...x....." }, { DRUM_CLOSED_HAT, "xx.xxx.xxx......" } } },
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
