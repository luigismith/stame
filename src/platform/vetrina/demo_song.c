/* demo_song.c — i brani della demo (demo.h): «Acacia», «Felce» e «Pistillo», brani originali di Stame.
 *
 * Generato da tools/demo.py: non va modificato a mano. Tick a 96 PPQN dall'inizio di ogni brano.
 */
#include "demo.h"
#include "vetrina.h"

/* Demo song: Acacia: 96 BPM, 89 battute, 428 passi, 3:50 */
static const dstep_t SONG_0[] = {
    {      0, D_TITLE, 0, 0, 0, 0 },
    {      0, D_THEME, THEME_DARK, 0, 0, 0 },
    {      0, D_VIEW, VIEW_CHORD, 0, 0, 0 },
    {      0, D_OPT, ACC_OPT_KEY_ON, 0, 0, 0 },
    {      0, D_OPT, ACC_OPT_BASS_ON, 0, 0, 0 },
    {      0, D_OPT, ACC_OPT_SINGLE_NOTES, 1, 0, 0 },
    {      0, D_OPT, ACC_OPT_BASS_VOICING, 23, 0, 0 },
    {      0, D_OPT, ACC_OPT_VOICING, 36, 0, 0 },
    {      0, D_FOCUS, ENC_BPM, 0, 0, 0 },
    {      0, D_BPM, 0, 0, 96, 0 },                           /* 96 BPM */
    {     48, D_FOCUS, ENC_SOUND, 0, 0, 0 },
    {     48, D_SOUND, 0, 0, 0, 0 },                          /* Glass Pollen, Harp 3 */
    {    120, D_FOCUS, ENC_FX, 0, 0, 0 },
    {    120, D_TURN, ENC_FX, 2, 0, 0 },                      /* più riverbero */
    {    192, D_CHORD, 0x4, 0xc, 2, 84 },                     /* Dmaj9: C#4 D4 E4 F#4 A4 */
    {    576, D_VOICING, 0, 0, 41, 0 },                       /* voicing 41: finestra da F */
    {    960, D_OFF, 0, 0, 0, 0 },
    {    960, D_CHORD, 0x2, 0xa, 11, 80 },                    /* Bm9: F#4 A4 B4 C#5 D5 */
    {   1344, D_VOICING, 0, 0, 36, 0 },                       /* voicing 36: finestra da C */
    {   1728, D_OFF, 0, 0, 0, 0 },
    {   1728, D_CHORD, 0x4, 0xc, 7, 86 },                     /* Gmaj9: D4 F#4 G4 A4 B4 */
    {   2112, D_VOICING, 0, 0, 43, 0 },                       /* voicing 43: finestra da G */
    {   2496, D_OFF, 0, 0, 0, 0 },
    {   2496, D_CHORD, 0x8, 0x8, 9, 82 },                     /* Asus9: A4 B4 D5 E5 */
    {   2688, D_CHORD, 0x4, 0x0, 9, 78 },                     /* A: A4 C#5 E5 */
    {   2880, D_HOLD, ENC_BPM, 0, 0, 0 },                     /* lista dei Beat */
    {   2928, D_TURN, ENC_BPM, 1, 0, 0 },
    {   2976, D_TURN, ENC_BPM, 1, 0, 0 },
    {   3024, D_TURN, ENC_BPM, 1, 0, 0 },
    {   3072, D_PRESS, ENC_BPM, 0, 0, 0 },                    /* 04 Lounge */
    {   3120, D_BACK, 0, 0, 0, 0 },
    {   3264, D_OFF, 0, 0, 0, 0 },
    {   3264, D_LOOP, LOOP_C_PRESS, 0, 0, 0 },                /* REC: una battuta di count-in, poi 4 da registrare */
    {   3264, D_FOCUS, ENC_SOUND, 0, 0, 0 },
    {   3264, D_SOUND, 0, 0, 8, 0 },                          /* Dew Mallet */
    {   3264, D_PERF, PERF_PATTERN, 13, 0, 0 },               /* Pattern 13: gruppi di tre sedicesimi */
    {   3360, D_FOCUS, ENC_BASS, 0, 0, 0 },
    {   3360, D_PRESS, ENC_BASS, 0, 0, 0 },                   /* basso acceso */
    {   3408, D_BASS, 0, 0, 5, 0 },                           /* Wood Bass */
    {   3456, D_VOICING, 0, 0, 24, 0 },                       /* voicing 24: finestra da C */
    {   3648, D_BEATON, 1, 0, 0, 0 },                         /* Beat: Lounge */
    {   3648, D_CHORD, 0x4, 0x4, 7, 92 },                     /* Gmaj7: D3 F#3 G3 B3 */
    {   3816, D_OFF, 0, 0, 0, 0 },
    {   3840, D_CHORD, 0x4, 0x4, 7, 84 },                     /* Gmaj7: D3 F#3 G3 B3 */
    {   4008, D_OFF, 0, 0, 0, 0 },
    {   4032, D_CHORD, 0x8, 0x0, 9, 92 },                     /* Asus: D3 E3 A3 */
    {   4200, D_OFF, 0, 0, 0, 0 },
    {   4224, D_CHORD, 0x4, 0x0, 9, 84 },                     /* A: C#3 E3 A3 */
    {   4392, D_OFF, 0, 0, 0, 0 },
    {   4416, D_CHORD, 0x2, 0x2, 6, 92 },                     /* F#m7: C#3 E3 F#3 A3 */
    {   4584, D_OFF, 0, 0, 0, 0 },
    {   4608, D_CHORD, 0x2, 0x2, 6, 84 },                     /* F#m7: C#3 E3 F#3 A3 */
    {   4776, D_OFF, 0, 0, 0, 0 },
    {   4800, D_CHORD, 0x2, 0x2, 11, 92 },                    /* Bm7: D3 F#3 A3 B3 */
    {   4968, D_OFF, 0, 0, 0, 0 },
    {   4992, D_CHORD, 0x2, 0x0, 11, 84 },                    /* Bm: D3 F#3 B3 */
    {   5160, D_OFF, 0, 0, 0, 0 },
    {   5184, D_VIEW, VIEW_CHORD_KB, 0, 0, 0 },
    {   6432, D_FOCUS, ENC_PERFORM, 0, 0, 0 },
    {   6432, D_PERF, PERF_OFF, 0, 0, 0 },                    /* Perform spento */
    {   6480, D_HOLD, ENC_PERFORM, 0, 0, 0 },                 /* Lock del Perform acceso */
    {   6528, D_FOCUS, ENC_CHORD_VOICING, 0, 0, 0 },
    {   6528, D_PRESS, ENC_CHORD_VOICING, 0, 0, 0 },          /* note singole: Split */
    {   6624, D_VOICING, 0, 0, 48, 0 },                       /* voicing 48: finestra da C */
    {   6672, D_CHORD, 0, 0, 2, 88 },                         /* D5 */
    {   6720, D_OFF, 0, 0, 0, 0 },
    {   6720, D_VIEW, VIEW_NOTES, 0, 0, 0 },
    {   6720, D_CHORD, 0, 0, 11, 104 },                       /* B5 */
    {   6864, D_CHORD, 0, 0, 9, 88 },                         /* A5 */
    {   6912, D_CHORD, 0, 0, 6, 98 },                         /* F#5 */
    {   7008, D_CHORD, 0, 0, 4, 86 },                         /* E5 */
    {   7056, D_CHORD, 0, 0, 6, 90 },                         /* F#5 */
    {   7104, D_CHORD, 0, 0, 4, 100 },                        /* E5 */
    {   7296, D_CHORD, 0, 0, 1, 90 },                         /* C#5 */
    {   7344, D_CHORD, 0, 0, 2, 84 },                         /* D5 */
    {   7392, D_CHORD, 0, 0, 4, 94 },                         /* E5 */
    {   7488, D_CHORD, 0, 0, 9, 102 },                        /* A5 */
    {   7632, D_CHORD, 0, 0, 6, 86 },                         /* F#5 */
    {   7680, D_CHORD, 0, 0, 4, 96 },                         /* E5 */
    {   7776, D_CHORD, 0, 0, 1, 86 },                         /* C#5 */
    {   7824, D_CHORD, 0, 0, 2, 90 },                         /* D5 */
    {   7872, D_CHORD, 0, 0, 2, 98 },                         /* D5 */
    {   8064, D_CHORD, 0, 0, 1, 84 },                         /* C#5 */
    {   8112, D_CHORD, 0, 0, 2, 92 },                         /* D5 */
    {   8256, D_CHORD, 0, 0, 11, 106 },                       /* B5 */
    {   8400, D_CHORD, 0, 0, 9, 90 },                         /* A5 */
    {   8448, D_CHORD, 0, 0, 6, 100 },                        /* F#5 */
    {   8544, D_CHORD, 0, 0, 4, 88 },                         /* E5 */
    {   8592, D_CHORD, 0, 0, 6, 92 },                         /* F#5 */
    {   8640, D_CHORD, 0, 0, 4, 100 },                        /* E5 */
    {   8832, D_CHORD, 0, 0, 1, 90 },                         /* C#5 */
    {   8880, D_CHORD, 0, 0, 4, 92 },                         /* E5 */
    {   8928, D_CHORD, 0, 0, 9, 104 },                        /* A5 */
    {   9024, D_CHORD, 0, 0, 11, 110 },                       /* B5 */
    {   9168, D_CHORD, 0, 0, 9, 94 },                         /* A5 */
    {   9216, D_CHORD, 0, 0, 6, 96 },                         /* F#5 */
    {   9264, D_CHORD, 0, 0, 4, 90 },                         /* E5 */
    {   9312, D_CHORD, 0, 0, 1, 94 },                         /* C#5 */
    {   9408, D_CHORD, 0, 0, 2, 96 },                         /* D5 */
    {   9696, D_OFF, 0, 0, 0, 0 },
    {   9696, D_VOICING, 0, 0, 36, 0 },                       /* voicing 36: finestra da C */
    {   9792, D_LOOP, LOOP_C_OVERDUB, 0, 0, 0 },              /* overdub */
    {   9792, D_VIEW, VIEW_CHORD, 0, 0, 0 },
    {   9792, D_CHORD, 0, 0, 11, 100 },                       /* B4 */
    {   9850, D_OFF, 0, 0, 0, 0 },
    {   9864, D_CHORD, 0, 0, 9, 84 },                         /* A4 */
    {   9922, D_OFF, 0, 0, 0, 0 },
    {   9936, D_CHORD, 0, 0, 6, 90 },                         /* F#4 */
    {   9974, D_OFF, 0, 0, 0, 0 },
    {   9984, D_CHORD, 0, 0, 2, 94 },                         /* D4 */
    {  10022, D_OFF, 0, 0, 0, 0 },
    {  10032, D_CHORD, 0, 0, 4, 80 },                         /* E4 */
    {  10070, D_OFF, 0, 0, 0, 0 },
    {  10080, D_CHORD, 0, 0, 6, 88 },                         /* F#4 */
    {  10118, D_OFF, 0, 0, 0, 0 },
    {  10128, D_CHORD, 0, 0, 9, 82 },                         /* A4 */
    {  10166, D_OFF, 0, 0, 0, 0 },
    {  10176, D_CHORD, 0, 0, 9, 100 },                        /* A4 */
    {  10234, D_OFF, 0, 0, 0, 0 },
    {  10248, D_CHORD, 0, 0, 4, 84 },                         /* E4 */
    {  10306, D_OFF, 0, 0, 0, 0 },
    {  10320, D_CHORD, 0, 0, 2, 90 },                         /* D4 */
    {  10358, D_OFF, 0, 0, 0, 0 },
    {  10368, D_CHORD, 0, 0, 1, 94 },                         /* C#4 */
    {  10406, D_OFF, 0, 0, 0, 0 },
    {  10416, D_CHORD, 0, 0, 4, 80 },                         /* E4 */
    {  10454, D_OFF, 0, 0, 0, 0 },
    {  10464, D_CHORD, 0, 0, 9, 88 },                         /* A4 */
    {  10502, D_OFF, 0, 0, 0, 0 },
    {  10512, D_CHORD, 0, 0, 11, 82 },                        /* B4 */
    {  10550, D_OFF, 0, 0, 0, 0 },
    {  10560, D_CHORD, 0, 0, 9, 100 },                        /* A4 */
    {  10618, D_OFF, 0, 0, 0, 0 },
    {  10632, D_CHORD, 0, 0, 6, 84 },                         /* F#4 */
    {  10690, D_OFF, 0, 0, 0, 0 },
    {  10704, D_CHORD, 0, 0, 4, 90 },                         /* E4 */
    {  10742, D_OFF, 0, 0, 0, 0 },
    {  10752, D_CHORD, 0, 0, 1, 94 },                         /* C#4 */
    {  10790, D_OFF, 0, 0, 0, 0 },
    {  10800, D_CHORD, 0, 0, 4, 80 },                         /* E4 */
    {  10838, D_OFF, 0, 0, 0, 0 },
    {  10848, D_CHORD, 0, 0, 6, 88 },                         /* F#4 */
    {  10886, D_OFF, 0, 0, 0, 0 },
    {  10896, D_CHORD, 0, 0, 9, 82 },                         /* A4 */
    {  10934, D_OFF, 0, 0, 0, 0 },
    {  10944, D_CHORD, 0, 0, 6, 100 },                        /* F#4 */
    {  11002, D_OFF, 0, 0, 0, 0 },
    {  11016, D_CHORD, 0, 0, 2, 84 },                         /* D4 */
    {  11074, D_OFF, 0, 0, 0, 0 },
    {  11088, D_CHORD, 0, 0, 1, 90 },                         /* C#4 */
    {  11126, D_OFF, 0, 0, 0, 0 },
    {  11136, D_CHORD, 0, 0, 2, 94 },                         /* D4 */
    {  11174, D_OFF, 0, 0, 0, 0 },
    {  11184, D_CHORD, 0, 0, 6, 80 },                         /* F#4 */
    {  11222, D_OFF, 0, 0, 0, 0 },
    {  11232, D_CHORD, 0, 0, 11, 88 },                        /* B4 */
    {  11270, D_OFF, 0, 0, 0, 0 },
    {  11280, D_CHORD, 0, 0, 9, 82 },                         /* A4 */
    {  11318, D_OFF, 0, 0, 0, 0 },
    {  11328, D_LOOP, LOOP_C_OVERDUB, 0, 0, 0 },              /* fine dell'overdub: due strati */
    {  11328, D_VIEW, VIEW_GEEK, 0, 0, 0 },
    {  12672, D_VOICING, 0, 0, 54, 0 },                       /* voicing 54: finestra da F# */
    {  12864, D_FOCUS, ENC_SOUND, 0, 0, 0 },
    {  12864, D_SOUND, 0, 0, 11, 0 },                         /* Sun Room: anche il loop cambia suono (ACC-221) */
    {  12864, D_THEME, THEME_LIGHT, 0, 0, 0 },
    {  12864, D_VIEW, VIEW_CHORD, 0, 0, 0 },
    {  12864, D_CHORD, 0, 0, 2, 108 },                        /* D6 */
    {  12960, D_CHORD, 0, 0, 1, 94 },                         /* C#6 */
    {  13008, D_CHORD, 0, 0, 11, 100 },                       /* B5 */
    {  13104, D_CHORD, 0, 0, 9, 98 },                         /* A5 */
    {  13248, D_OFF, 0, 0, 0, 0 },
    {  13296, D_CHORD, 0, 0, 11, 90 },                        /* B5 */
    {  13344, D_CHORD, 0, 0, 9, 96 },                         /* A5 */
    {  13440, D_CHORD, 0, 0, 1, 104 },                        /* C#6 */
    {  13584, D_CHORD, 0, 0, 4, 100 },                        /* E6 */
    {  13632, D_CHORD, 0, 0, 4, 110 },                        /* E6 */
    {  13776, D_CHORD, 0, 0, 1, 94 },                         /* C#6 */
    {  13824, D_CHORD, 0, 0, 9, 98 },                         /* A5 */
    {  13920, D_CHORD, 0, 0, 11, 90 },                        /* B5 */
    {  13968, D_CHORD, 0, 0, 9, 88 },                         /* A5 */
    {  14016, D_CHORD, 0, 0, 6, 96 },                         /* F#5 */
    {  14160, D_CHORD, 0, 0, 9, 92 },                         /* A5 */
    {  14208, D_CHORD, 0, 0, 11, 100 },                       /* B5 */
    {  14400, D_CHORD, 0, 0, 2, 110 },                        /* D6 */
    {  14496, D_CHORD, 0, 0, 1, 96 },                         /* C#6 */
    {  14544, D_CHORD, 0, 0, 11, 102 },                       /* B5 */
    {  14640, D_CHORD, 0, 0, 9, 98 },                         /* A5 */
    {  14736, D_CHORD, 0, 0, 11, 94 },                        /* B5 */
    {  14784, D_CHORD, 0, 0, 2, 104 },                        /* D6 */
    {  14880, D_CHORD, 0, 0, 4, 100 },                        /* E6 */
    {  14928, D_CHORD, 0, 0, 2, 94 },                         /* D6 */
    {  14976, D_CHORD, 0, 0, 1, 104 },                        /* C#6 */
    {  15072, D_CHORD, 0, 0, 4, 108 },                        /* E6 */
    {  15168, D_CHORD, 0, 0, 4, 114 },                        /* E6 */
    {  15312, D_CHORD, 0, 0, 2, 98 },                         /* D6 */
    {  15360, D_CHORD, 0, 0, 1, 104 },                        /* C#6 */
    {  15456, D_CHORD, 0, 0, 11, 94 },                        /* B5 */
    {  15504, D_CHORD, 0, 0, 1, 98 },                         /* C#6 */
    {  15552, D_CHORD, 0, 0, 2, 108 },                        /* D6 */
    {  15744, D_CHORD, 0, 0, 1, 96 },                         /* C#6 */
    {  15792, D_CHORD, 0, 0, 11, 100 },                       /* B5 */
    {  15936, D_OFF, 0, 0, 0, 0 },
    {  15936, D_VOICING, 0, 0, 48, 0 },                       /* voicing 48: finestra da C */
    {  15936, D_VIEW, VIEW_KEYBOARD, 0, 0, 0 },
    {  15936, D_CHORD, 0, 0, 11, 100 },                       /* B5 */
    {  16032, D_CHORD, 0, 0, 9, 86 },                         /* A5 */
    {  16080, D_CHORD, 0, 0, 11, 92 },                        /* B5 */
    {  16128, D_CHORD, 0, 0, 6, 98 },                         /* F#5 */
    {  16224, D_CHORD, 0, 0, 4, 86 },                         /* E5 */
    {  16272, D_CHORD, 0, 0, 6, 90 },                         /* F#5 */
    {  16320, D_CHORD, 0, 0, 4, 98 },                         /* E5 */
    {  16464, D_CHORD, 0, 0, 2, 86 },                         /* D5 */
    {  16512, D_CHORD, 0, 0, 1, 94 },                         /* C#5 */
    {  16608, D_CHORD, 0, 0, 4, 88 },                         /* E5 */
    {  16656, D_CHORD, 0, 0, 9, 96 },                         /* A5 */
    {  16704, D_CHORD, 0, 0, 9, 100 },                        /* A5 */
    {  16800, D_CHORD, 0, 0, 11, 92 },                        /* B5 */
    {  16848, D_CHORD, 0, 0, 9, 88 },                         /* A5 */
    {  16896, D_CHORD, 0, 0, 4, 96 },                         /* E5 */
    {  16992, D_CHORD, 0, 0, 1, 86 },                         /* C#5 */
    {  17040, D_CHORD, 0, 0, 2, 90 },                         /* D5 */
    {  17088, D_CHORD, 0, 0, 2, 96 },                         /* D5 */
    {  17232, D_CHORD, 0, 0, 6, 90 },                         /* F#5 */
    {  17280, D_CHORD, 0, 0, 4, 86 },                         /* E5 */
    {  17328, D_CHORD, 0, 0, 2, 92 },                         /* D5 */
    {  17472, D_CHORD, 0, 0, 11, 106 },                       /* B5 */
    {  17616, D_CHORD, 0, 0, 9, 90 },                         /* A5 */
    {  17664, D_CHORD, 0, 0, 6, 98 },                         /* F#5 */
    {  17760, D_CHORD, 0, 0, 7, 90 },                         /* G5 */
    {  17808, D_CHORD, 0, 0, 9, 96 },                         /* A5 */
    {  17856, D_CHORD, 0, 0, 11, 108 },                       /* B5 */
    {  17952, D_CHORD, 0, 0, 9, 96 },                         /* A5 */
    {  18048, D_CHORD, 0, 0, 4, 94 },                         /* E5 */
    {  18144, D_CHORD, 0, 0, 9, 102 },                        /* A5 */
    {  18240, D_CHORD, 0, 0, 11, 110 },                       /* B5 */
    {  18384, D_CHORD, 0, 0, 9, 94 },                         /* A5 */
    {  18432, D_CHORD, 0, 0, 6, 96 },                         /* F#5 */
    {  18480, D_CHORD, 0, 0, 4, 90 },                         /* E5 */
    {  18528, D_CHORD, 0, 0, 1, 94 },                         /* C#5 */
    {  18624, D_CHORD, 0, 0, 2, 96 },                         /* D5 */
    {  18816, D_OFF, 0, 0, 0, 0 },
    {  18816, D_HOLD, ENC_PERFORM, 0, 0, 0 },                 /* Lock del Perform spento */
    {  18816, D_HOLD, ENC_BPM, 0, 0, 0 },                     /* lista dei Beat */
    {  18864, D_TURN, ENC_BPM, 1, 0, 0 },
    {  18912, D_TURN, ENC_BPM, 1, 0, 0 },
    {  19008, D_PRESS, ENC_BPM, 0, 0, 0 },                    /* 06 Halftime */
    {  19008, D_BACK, 0, 0, 0, 0 },
    {  19008, D_LOOP, LOOP_C_STOP, 0, 0, 0 },                 /* pausa del loop */
    {  19008, D_FOCUS, ENC_SOUND, 0, 0, 0 },
    {  19008, D_SOUND, 0, 0, 4, 0 },                          /* Fern Pluck: Arpeggiate 6, sedicesimi su e giù */
    {  19008, D_VOICING, 0, 0, 36, 0 },                       /* voicing 36: finestra da C */
    {  19008, D_THEME, THEME_DARK, 0, 0, 0 },
    {  19008, D_VIEW, VIEW_REACT, 0, 0, 0 },
    {  19008, D_CHORD, 0x2, 0xa, 4, 88 },                     /* Em9: D4 E4 F#4 G4 B4 */
    {  19056, D_FOCUS, ENC_FX, 0, 0, 0 },
    {  19056, D_TURN, ENC_FX, 2, 0, 0 },
    {  19368, D_OFF, 0, 0, 0, 0 },
    {  19392, D_CHORD, 0x2, 0x2, 6, 86 },                     /* F#m7: C#4 E4 F#4 A4 */
    {  19752, D_OFF, 0, 0, 0, 0 },
    {  19776, D_CHORD, 0x4, 0xc, 7, 90 },                     /* Gmaj9: D4 F#4 G4 A4 B4 */
    {  20136, D_OFF, 0, 0, 0, 0 },
    {  20160, D_CHORD, 0x8, 0x2, 9, 92 },                     /* A7sus: D4 E4 G4 A4 */
    {  20520, D_OFF, 0, 0, 0, 0 },
    {  20544, D_CHORD, 0x2, 0xa, 4, 92 },                     /* Em9: D4 E4 F#4 G4 B4 */
    {  20904, D_OFF, 0, 0, 0, 0 },
    {  20928, D_CHORD, 0x2, 0x2, 6, 94 },                     /* F#m7: C#4 E4 F#4 A4 */
    {  21288, D_OFF, 0, 0, 0, 0 },
    {  21312, D_CHORD, 0x2, 0x1, 7, 98 },                     /* Gm6: D4 E4 G4 A#4 */
    {  21672, D_OFF, 0, 0, 0, 0 },
    {  21696, D_BEATON, 0, 0, 0, 0 },                         /* ultima battuta senza batteria */
    {  21696, D_CHORD, 0x8, 0x2, 9, 100 },                    /* A7sus: D4 E4 G4 A4 */
    {  21864, D_OFF, 0, 0, 0, 0 },
    {  21888, D_CHORD, 0x4, 0x0, 9, 104 },                    /* A: C#4 E4 A4 */
    {  22056, D_OFF, 0, 0, 0, 0 },
    {  22056, D_FOCUS, ENC_SOUND, 0, 0, 0 },
    {  22056, D_SOUND, 0, 0, 8, 0 },
    {  22056, D_PERF, PERF_OFF, 0, 0, 0 },
    {  22056, D_HOLD, ENC_PERFORM, 0, 0, 0 },                 /* Lock del Perform acceso */
    {  22056, D_VOICING, 0, 0, 48, 0 },                       /* voicing 48: finestra da C */
    {  22080, D_FOCUS, ENC_KEY, 0, 0, 0 },
    {  22080, D_PTURN, ENC_KEY, 2, 0, 0 },                    /* transpose +2: anche il loop sale (ACC-221) */
    {  22080, D_BEAT, 3, 0, 0, 0 },
    {  22080, D_BEATON, 1, 0, 0, 0 },
    {  22080, D_LOOP, LOOP_C_STOP, 0, 0, 0 },                 /* il loop riprende da capo, con il trasporto */
    {  22080, D_THEME, THEME_LIGHT, 0, 0, 0 },
    {  22080, D_VIEW, VIEW_CHORD, 0, 0, 0 },
    {  22080, D_CHORD, 0, 0, 11, 104 },                       /* B5 */
    {  22224, D_CHORD, 0, 0, 9, 88 },                         /* A5 */
    {  22272, D_CHORD, 0, 0, 6, 98 },                         /* F#5 */
    {  22368, D_CHORD, 0, 0, 4, 86 },                         /* E5 */
    {  22416, D_CHORD, 0, 0, 6, 90 },                         /* F#5 */
    {  22464, D_CHORD, 0, 0, 4, 100 },                        /* E5 */
    {  22656, D_CHORD, 0, 0, 1, 90 },                         /* C#5 */
    {  22704, D_CHORD, 0, 0, 2, 84 },                         /* D5 */
    {  22752, D_CHORD, 0, 0, 4, 94 },                         /* E5 */
    {  22848, D_CHORD, 0, 0, 9, 102 },                        /* A5 */
    {  22992, D_CHORD, 0, 0, 6, 86 },                         /* F#5 */
    {  23040, D_CHORD, 0, 0, 4, 96 },                         /* E5 */
    {  23136, D_CHORD, 0, 0, 1, 86 },                         /* C#5 */
    {  23184, D_CHORD, 0, 0, 2, 90 },                         /* D5 */
    {  23232, D_CHORD, 0, 0, 2, 98 },                         /* D5 */
    {  23424, D_CHORD, 0, 0, 1, 84 },                         /* C#5 */
    {  23472, D_CHORD, 0, 0, 2, 92 },                         /* D5 */
    {  23616, D_CHORD, 0, 0, 11, 106 },                       /* B5 */
    {  23760, D_CHORD, 0, 0, 9, 90 },                         /* A5 */
    {  23808, D_CHORD, 0, 0, 6, 100 },                        /* F#5 */
    {  23904, D_CHORD, 0, 0, 4, 88 },                         /* E5 */
    {  23952, D_CHORD, 0, 0, 6, 92 },                         /* F#5 */
    {  24000, D_CHORD, 0, 0, 4, 100 },                        /* E5 */
    {  24192, D_CHORD, 0, 0, 1, 90 },                         /* C#5 */
    {  24240, D_CHORD, 0, 0, 4, 92 },                         /* E5 */
    {  24288, D_CHORD, 0, 0, 9, 104 },                        /* A5 */
    {  24384, D_CHORD, 0, 0, 11, 110 },                       /* B5 */
    {  24528, D_CHORD, 0, 0, 9, 94 },                         /* A5 */
    {  24576, D_CHORD, 0, 0, 6, 96 },                         /* F#5 */
    {  24624, D_CHORD, 0, 0, 4, 90 },                         /* E5 */
    {  24672, D_CHORD, 0, 0, 1, 94 },                         /* C#5 */
    {  24768, D_CHORD, 0, 0, 2, 96 },                         /* D5 */
    {  24960, D_CHORD, 0, 0, 4, 92 },                         /* E5 */
    {  25008, D_CHORD, 0, 0, 6, 96 },                         /* F#5 */
    {  25056, D_CHORD, 0, 0, 9, 104 },                        /* A5 */
    {  25152, D_OFF, 0, 0, 0, 0 },
    {  25152, D_VOICING, 0, 0, 54, 0 },                       /* voicing 54: finestra da F# */
    {  25152, D_FOCUS, ENC_SOUND, 0, 0, 0 },
    {  25152, D_SOUND, 0, 0, 11, 0 },
    {  25152, D_BEAT, 0, 0, 0, 0 },
    {  25152, D_VIEW, VIEW_CHORD_KB, 0, 0, 0 },
    {  25152, D_CHORD, 0, 0, 2, 108 },                        /* D6 */
    {  25248, D_CHORD, 0, 0, 1, 94 },                         /* C#6 */
    {  25296, D_CHORD, 0, 0, 11, 100 },                       /* B5 */
    {  25392, D_CHORD, 0, 0, 9, 98 },                         /* A5 */
    {  25536, D_OFF, 0, 0, 0, 0 },
    {  25584, D_CHORD, 0, 0, 11, 90 },                        /* B5 */
    {  25632, D_CHORD, 0, 0, 9, 96 },                         /* A5 */
    {  25728, D_CHORD, 0, 0, 1, 104 },                        /* C#6 */
    {  25872, D_CHORD, 0, 0, 4, 100 },                        /* E6 */
    {  25920, D_CHORD, 0, 0, 4, 110 },                        /* E6 */
    {  26064, D_CHORD, 0, 0, 1, 94 },                         /* C#6 */
    {  26112, D_CHORD, 0, 0, 9, 98 },                         /* A5 */
    {  26208, D_CHORD, 0, 0, 11, 90 },                        /* B5 */
    {  26256, D_CHORD, 0, 0, 9, 88 },                         /* A5 */
    {  26304, D_CHORD, 0, 0, 6, 96 },                         /* F#5 */
    {  26448, D_CHORD, 0, 0, 9, 92 },                         /* A5 */
    {  26496, D_CHORD, 0, 0, 11, 100 },                       /* B5 */
    {  26688, D_CHORD, 0, 0, 2, 110 },                        /* D6 */
    {  26784, D_CHORD, 0, 0, 1, 96 },                         /* C#6 */
    {  26832, D_CHORD, 0, 0, 11, 102 },                       /* B5 */
    {  26928, D_CHORD, 0, 0, 9, 98 },                         /* A5 */
    {  27024, D_CHORD, 0, 0, 11, 94 },                        /* B5 */
    {  27072, D_CHORD, 0, 0, 2, 104 },                        /* D6 */
    {  27168, D_CHORD, 0, 0, 4, 100 },                        /* E6 */
    {  27216, D_CHORD, 0, 0, 2, 94 },                         /* D6 */
    {  27264, D_CHORD, 0, 0, 1, 104 },                        /* C#6 */
    {  27360, D_CHORD, 0, 0, 4, 108 },                        /* E6 */
    {  27456, D_CHORD, 0, 0, 4, 114 },                        /* E6 */
    {  27600, D_CHORD, 0, 0, 2, 98 },                         /* D6 */
    {  27648, D_CHORD, 0, 0, 1, 104 },                        /* C#6 */
    {  27744, D_CHORD, 0, 0, 11, 94 },                        /* B5 */
    {  27792, D_CHORD, 0, 0, 1, 98 },                         /* C#6 */
    {  27840, D_CHORD, 0, 0, 2, 108 },                        /* D6 */
    {  28032, D_CHORD, 0, 0, 1, 96 },                         /* C#6 */
    {  28080, D_CHORD, 0, 0, 11, 100 },                       /* B5 */
    {  28224, D_OFF, 0, 0, 0, 0 },
    {  28224, D_SOUND, 0, 0, 0, 0 },                          /* Glass Pollen: il Lock tiene il Perform spento */
    {  28224, D_VIEW, VIEW_NOTES, 0, 0, 0 },
    {  28224, D_CHORD, 0, 0, 2, 110 },                        /* D6 */
    {  28320, D_CHORD, 0, 0, 1, 96 },                         /* C#6 */
    {  28368, D_CHORD, 0, 0, 11, 102 },                       /* B5 */
    {  28464, D_CHORD, 0, 0, 9, 100 },                        /* A5 */
    {  28608, D_OFF, 0, 0, 0, 0 },
    {  28656, D_CHORD, 0, 0, 11, 92 },                        /* B5 */
    {  28704, D_CHORD, 0, 0, 9, 98 },                         /* A5 */
    {  28800, D_CHORD, 0, 0, 1, 106 },                        /* C#6 */
    {  28944, D_CHORD, 0, 0, 4, 102 },                        /* E6 */
    {  28992, D_CHORD, 0, 0, 4, 112 },                        /* E6 */
    {  29136, D_CHORD, 0, 0, 1, 96 },                         /* C#6 */
    {  29184, D_CHORD, 0, 0, 9, 100 },                        /* A5 */
    {  29280, D_CHORD, 0, 0, 11, 92 },                        /* B5 */
    {  29328, D_CHORD, 0, 0, 1, 96 },                         /* C#6 */
    {  29376, D_CHORD, 0, 0, 2, 104 },                        /* D6 */
    {  29520, D_CHORD, 0, 0, 1, 94 },                         /* C#6 */
    {  29568, D_CHORD, 0, 0, 11, 100 },                       /* B5 */
    {  29760, D_CHORD, 0, 0, 2, 112 },                        /* D6 */
    {  29856, D_CHORD, 0, 0, 4, 104 },                        /* E6 */
    {  29904, D_CHORD, 0, 0, 2, 100 },                        /* D6 */
    {  30000, D_CHORD, 0, 0, 11, 96 },                        /* B5 */
    {  30096, D_CHORD, 0, 0, 2, 100 },                        /* D6 */
    {  30144, D_CHORD, 0, 0, 4, 114 },                        /* E6 */
    {  30336, D_CHORD, 0, 0, 1, 104 },                        /* C#6 */
    {  30432, D_CHORD, 0, 0, 4, 110 },                        /* E6 */
    {  30528, D_CHORD, 0, 0, 4, 116 },                        /* E6 */
    {  30672, D_CHORD, 0, 0, 2, 100 },                        /* D6 */
    {  30720, D_CHORD, 0, 0, 1, 106 },                        /* C#6 */
    {  30816, D_CHORD, 0, 0, 11, 96 },                        /* B5 */
    {  30864, D_CHORD, 0, 0, 1, 100 },                        /* C#6 */
    {  30912, D_CHORD, 0, 0, 2, 110 },                        /* D6 */
    {  31104, D_CHORD, 0, 0, 1, 98 },                         /* C#6 */
    {  31152, D_CHORD, 0, 0, 11, 104 },                       /* B5 */
    {  31296, D_OFF, 0, 0, 0, 0 },
    {  31296, D_LOOP, LOOP_C_UNDO, 0, 0, 0 },                 /* Undo: via il riff */
    {  31296, D_BEATON, 0, 0, 0, 0 },
    {  31296, D_THEME, THEME_DARK, 0, 0, 0 },
    {  31296, D_VIEW, VIEW_CHORD, 0, 0, 0 },
    {  31296, D_FOCUS, ENC_BPM, 0, 0, 0 },
    {  31296, D_BPM, 0, 0, 88, 0 },                           /* ritardando: 88 BPM */
    {  31680, D_BPM, 0, 0, 80, 0 },                           /* ritardando: 80 BPM */
    {  32064, D_BPM, 0, 0, 72, 0 },                           /* ritardando: 72 BPM */
    {  32448, D_BPM, 0, 0, 66, 0 },                           /* ritardando: 66 BPM */
    {  32832, D_LOOP, LOOP_C_CLEAR, 0, 0, 0 },                /* Clear */
    {  32832, D_HOLD, ENC_PERFORM, 0, 0, 0 },                 /* Lock del Perform spento */
    {  32832, D_FOCUS, ENC_PERFORM, 0, 0, 0 },
    {  32832, D_PERF, PERF_HARP, 3, 0, 0 },                   /* Harp 3 */
    {  32832, D_VOICING, 0, 0, 36, 0 },                       /* voicing 36: finestra da C */
    {  32832, D_TURN, ENC_FX, 2, 0, 0 },
    {  32832, D_CHORD, 0x4, 0xc, 2, 92 },                     /* Dmaj9: C#4 D4 E4 F#4 A4 */
    {  33024, D_VOICING, 0, 0, 41, 0 },                       /* voicing 41: finestra da F */
    {  33216, D_VOICING, 0, 0, 46, 0 },                       /* voicing 46: finestra da A# */
    {  33408, D_VOICING, 0, 0, 50, 0 },                       /* voicing 50: finestra da D */
    {  33600, D_OFF, 0, 0, 0, 0 },
    {  33792, D_MENU, 0, 0, 0, 0 },                           /* il menu, con «Play Demo Song» */
    {  33840, D_TURN, ENC_OPTIONS, 1, 0, 0 },
    {  33864, D_TURN, ENC_OPTIONS, 1, 0, 0 },
    {  33888, D_TURN, ENC_OPTIONS, 1, 0, 0 },
    {  33912, D_TURN, ENC_OPTIONS, 1, 0, 0 },
    {  33936, D_TURN, ENC_OPTIONS, 1, 0, 0 },
    {  33960, D_TURN, ENC_OPTIONS, 1, 0, 0 },
    {  34272, D_BACK, 0, 0, 0, 0 },
    {  34368, D_END, 0, 0, 0, 0 },
};

/* Demo song: Felce: 112 BPM, 49 battute, 274 passi, 1:48 */
static const dstep_t SONG_1[] = {
    {      0, D_TITLE, 0, 0, 0, 0 },
    {      0, D_THEME, THEME_DARK, 0, 0, 0 },
    {      0, D_VIEW, VIEW_CHORD, 0, 0, 0 },
    {      0, D_OPT, ACC_OPT_KEY_ON, 0, 0, 0 },
    {      0, D_OPT, ACC_OPT_BASS_ON, 0, 0, 0 },
    {      0, D_OPT, ACC_OPT_SINGLE_NOTES, 1, 0, 0 },
    {      0, D_OPT, ACC_OPT_BASS_VOICING, 23, 0, 0 },
    {      0, D_OPT, ACC_OPT_VOICING, 36, 0, 0 },
    {      0, D_FOCUS, ENC_BPM, 0, 0, 0 },
    {      0, D_BPM, 0, 0, 112, 0 },                          /* 112 BPM */
    {     48, D_FOCUS, ENC_SOUND, 0, 0, 0 },
    {     48, D_SOUND, 0, 0, 16, 0 },                         /* Grand Piano, Strum 2 */
    {     48, D_PERF, PERF_STRUM, 2, 0, 0 },
    {    120, D_FOCUS, ENC_FX, 0, 0, 0 },
    {    120, D_TURN, ENC_FX, 1, 0, 0 },                      /* un po' di riverbero */
    {    192, D_CHORD, 0x2, 0xa, 9, 88 },                     /* Am9: C4 E4 G4 A4 B4 */
    {    576, D_CHORD, 0x4, 0x4, 5, 86 },                     /* Fmaj7: C4 E4 F4 A4 */
    {    960, D_CHORD, 0x2, 0x2, 2, 86 },                     /* Dm7: C4 D4 F4 A4 */
    {   1152, D_CHORD, 0x4, 0x2, 7, 88 },                     /* G7: D4 F4 G4 B4 */
    {   1344, D_CHORD, 0x4, 0x4, 0, 90 },                     /* Cmaj7: C4 E4 G4 B4 */
    {   1536, D_CHORD, 0x4, 0x2, 4, 92 },                     /* E7: D4 E4 G#4 B4 */
    {   1728, D_OFF, 0, 0, 0, 0 },
    {   1728, D_BEAT, 1, 0, 0, 0 },                           /* Beat: Bossa, kit jazz */
    {   1728, D_BEATON, 1, 0, 0, 0 },
    {   1728, D_FOCUS, ENC_BASS, 0, 0, 0 },
    {   1728, D_PRESS, ENC_BASS, 0, 0, 0 },                   /* basso acceso */
    {   1728, D_VOICING, 0, 0, 24, 0 },                       /* voicing 24: finestra da C */
    {   1728, D_CHORD, 0x2, 0x2, 9, 92 },                     /* Am7: C3 E3 G3 A3 */
    {   1776, D_BASS, 0, 0, 0, 0 },                           /* Round Root */
    {   1896, D_OFF, 0, 0, 0, 0 },
    {   1920, D_CHORD, 0x2, 0x0, 9, 84 },                     /* Am: C3 E3 A3 */
    {   2088, D_OFF, 0, 0, 0, 0 },
    {   2112, D_CHORD, 0x4, 0x4, 5, 92 },                     /* Fmaj7: C3 E3 F3 A3 */
    {   2280, D_OFF, 0, 0, 0, 0 },
    {   2304, D_CHORD, 0x4, 0x0, 5, 84 },                     /* F: C3 F3 A3 */
    {   2472, D_OFF, 0, 0, 0, 0 },
    {   2496, D_CHORD, 0x2, 0x2, 2, 92 },                     /* Dm7: C3 D3 F3 A3 */
    {   2664, D_OFF, 0, 0, 0, 0 },
    {   2688, D_CHORD, 0x4, 0x2, 7, 84 },                     /* G7: D3 F3 G3 B3 */
    {   2856, D_OFF, 0, 0, 0, 0 },
    {   2880, D_CHORD, 0x4, 0x4, 0, 92 },                     /* Cmaj7: C3 E3 G3 B3 */
    {   3048, D_OFF, 0, 0, 0, 0 },
    {   3072, D_CHORD, 0x4, 0x2, 4, 84 },                     /* E7: D3 E3 G#3 B3 */
    {   3240, D_OFF, 0, 0, 0, 0 },
    {   3264, D_CHORD, 0x2, 0x2, 9, 92 },                     /* Am7: C3 E3 G3 A3 */
    {   3432, D_OFF, 0, 0, 0, 0 },
    {   3456, D_CHORD, 0x2, 0x0, 9, 84 },                     /* Am: C3 E3 A3 */
    {   3624, D_OFF, 0, 0, 0, 0 },
    {   3648, D_CHORD, 0x4, 0x4, 5, 92 },                     /* Fmaj7: C3 E3 F3 A3 */
    {   3816, D_OFF, 0, 0, 0, 0 },
    {   3840, D_CHORD, 0x4, 0x0, 5, 84 },                     /* F: C3 F3 A3 */
    {   4008, D_OFF, 0, 0, 0, 0 },
    {   4032, D_CHORD, 0x2, 0x2, 2, 92 },                     /* Dm7: C3 D3 F3 A3 */
    {   4200, D_OFF, 0, 0, 0, 0 },
    {   4224, D_CHORD, 0x4, 0x2, 7, 84 },                     /* G7: D3 F3 G3 B3 */
    {   4392, D_OFF, 0, 0, 0, 0 },
    {   4416, D_CHORD, 0x4, 0x4, 0, 92 },                     /* Cmaj7: C3 E3 G3 B3 */
    {   4584, D_OFF, 0, 0, 0, 0 },
    {   4608, D_CHORD, 0x4, 0x2, 4, 84 },                     /* E7: D3 E3 G#3 B3 */
    {   4776, D_OFF, 0, 0, 0, 0 },
    {   4800, D_LOOP, LOOP_C_PRESS, 0, 0, 0 },                /* REC: count-in, poi 4 battute */
    {   4800, D_VIEW, VIEW_CHORD_KB, 0, 0, 0 },
    {   5184, D_CHORD, 0x2, 0x2, 9, 82 },                     /* Am7: C3 E3 G3 A3 */
    {   5352, D_OFF, 0, 0, 0, 0 },
    {   5376, D_CHORD, 0x2, 0x0, 9, 74 },                     /* Am: C3 E3 A3 */
    {   5544, D_OFF, 0, 0, 0, 0 },
    {   5568, D_CHORD, 0x4, 0x4, 5, 82 },                     /* Fmaj7: C3 E3 F3 A3 */
    {   5736, D_OFF, 0, 0, 0, 0 },
    {   5760, D_CHORD, 0x4, 0x0, 5, 74 },                     /* F: C3 F3 A3 */
    {   5928, D_OFF, 0, 0, 0, 0 },
    {   5952, D_CHORD, 0x2, 0x2, 2, 82 },                     /* Dm7: C3 D3 F3 A3 */
    {   6120, D_OFF, 0, 0, 0, 0 },
    {   6144, D_CHORD, 0x4, 0x2, 7, 74 },                     /* G7: D3 F3 G3 B3 */
    {   6312, D_OFF, 0, 0, 0, 0 },
    {   6336, D_CHORD, 0x4, 0x4, 0, 82 },                     /* Cmaj7: C3 E3 G3 B3 */
    {   6504, D_OFF, 0, 0, 0, 0 },
    {   6528, D_CHORD, 0x4, 0x2, 4, 74 },                     /* E7: D3 E3 G#3 B3 */
    {   6624, D_FOCUS, ENC_SOUND, 0, 0, 0 },
    {   6624, D_SOUND, 0, 0, 19, 0 },                         /* Vibraphone */
    {   6624, D_PERF, PERF_OFF, 0, 0, 0 },
    {   6648, D_HOLD, ENC_PERFORM, 0, 0, 0 },                 /* Lock del Perform acceso */
    {   6672, D_VOICING, 0, 0, 48, 0 },                       /* voicing 48: finestra da C */
    {   6696, D_OFF, 0, 0, 0, 0 },
    {   6720, D_VIEW, VIEW_NOTES, 0, 0, 0 },
    {   6720, D_CHORD, 0, 0, 4, 96 },                         /* E5 */
    {   6864, D_CHORD, 0, 0, 7, 84 },                         /* G5 */
    {   6912, D_CHORD, 0, 0, 9, 92 },                         /* A5 */
    {   7008, D_CHORD, 0, 0, 11, 88 },                        /* B5 */
    {   7104, D_CHORD, 0, 0, 11, 98 },                        /* B5 */
    {   7248, D_CHORD, 0, 0, 9, 84 },                         /* A5 */
    {   7296, D_CHORD, 0, 0, 7, 90 },                         /* G5 */
    {   7440, D_CHORD, 0, 0, 4, 82 },                         /* E5 */
    {   7488, D_CHORD, 0, 0, 9, 94 },                         /* A5 */
    {   7584, D_CHORD, 0, 0, 5, 88 },                         /* F5 */
    {   7680, D_CHORD, 0, 0, 4, 92 },                         /* E5 */
    {   7824, D_CHORD, 0, 0, 2, 80 },                         /* D5 */
    {   7872, D_CHORD, 0, 0, 4, 90 },                         /* E5 */
    {   8160, D_CHORD, 0, 0, 11, 86 },                        /* B5 */
    {   8256, D_CHORD, 0, 0, 11, 98 },                        /* B5 */
    {   8352, D_CHORD, 0, 0, 9, 86 },                         /* A5 */
    {   8400, D_CHORD, 0, 0, 7, 84 },                         /* G5 */
    {   8448, D_CHORD, 0, 0, 4, 92 },                         /* E5 */
    {   8544, D_CHORD, 0, 0, 2, 88 },                         /* D5 */
    {   8640, D_CHORD, 0, 0, 5, 94 },                         /* F5 */
    {   8784, D_CHORD, 0, 0, 9, 84 },                         /* A5 */
    {   8832, D_CHORD, 0, 0, 7, 90 },                         /* G5 */
    {   8928, D_CHORD, 0, 0, 5, 86 },                         /* F5 */
    {   9024, D_CHORD, 0, 0, 4, 96 },                         /* E5 */
    {   9120, D_CHORD, 0, 0, 2, 88 },                         /* D5 */
    {   9216, D_CHORD, 0, 0, 0, 92 },                         /* C5 */
    {   9312, D_CHORD, 0, 0, 11, 94 },                        /* B5 */
    {   9408, D_CHORD, 0, 0, 9, 96 },                         /* A5 */
    {   9696, D_FOCUS, ENC_SOUND, 0, 0, 0 },
    {   9696, D_SOUND, 0, 0, 24, 0 },                         /* Kalimba */
    {   9696, D_PERF, PERF_OFF, 0, 0, 0 },
    {   9744, D_VOICING, 0, 0, 36, 0 },                       /* voicing 36: finestra da C */
    {   9792, D_OFF, 0, 0, 0, 0 },
    {   9792, D_LOOP, LOOP_C_OVERDUB, 0, 0, 0 },              /* overdub */
    {   9792, D_VIEW, VIEW_CHORD, 0, 0, 0 },
    {   9792, D_CHORD, 0, 0, 9, 94 },                         /* A4 */
    {   9821, D_OFF, 0, 0, 0, 0 },
    {   9840, D_CHORD, 0, 0, 4, 80 },                         /* E4 */
    {   9869, D_OFF, 0, 0, 0, 0 },
    {   9888, D_CHORD, 0, 0, 0, 86 },                         /* C4 */
    {   9917, D_OFF, 0, 0, 0, 0 },
    {   9936, D_CHORD, 0, 0, 4, 78 },                         /* E4 */
    {   9965, D_OFF, 0, 0, 0, 0 },
    {   9984, D_CHORD, 0, 0, 9, 92 },                         /* A4 */
    {  10013, D_OFF, 0, 0, 0, 0 },
    {  10032, D_CHORD, 0, 0, 7, 80 },                         /* G4 */
    {  10061, D_OFF, 0, 0, 0, 0 },
    {  10080, D_CHORD, 0, 0, 4, 84 },                         /* E4 */
    {  10109, D_OFF, 0, 0, 0, 0 },
    {  10128, D_CHORD, 0, 0, 0, 76 },                         /* C4 */
    {  10157, D_OFF, 0, 0, 0, 0 },
    {  10176, D_CHORD, 0, 0, 9, 94 },                         /* A4 */
    {  10205, D_OFF, 0, 0, 0, 0 },
    {  10224, D_CHORD, 0, 0, 5, 80 },                         /* F4 */
    {  10253, D_OFF, 0, 0, 0, 0 },
    {  10272, D_CHORD, 0, 0, 0, 86 },                         /* C4 */
    {  10301, D_OFF, 0, 0, 0, 0 },
    {  10320, D_CHORD, 0, 0, 5, 78 },                         /* F4 */
    {  10349, D_OFF, 0, 0, 0, 0 },
    {  10368, D_CHORD, 0, 0, 9, 92 },                         /* A4 */
    {  10397, D_OFF, 0, 0, 0, 0 },
    {  10416, D_CHORD, 0, 0, 5, 80 },                         /* F4 */
    {  10445, D_OFF, 0, 0, 0, 0 },
    {  10464, D_CHORD, 0, 0, 4, 84 },                         /* E4 */
    {  10493, D_OFF, 0, 0, 0, 0 },
    {  10512, D_CHORD, 0, 0, 0, 76 },                         /* C4 */
    {  10541, D_OFF, 0, 0, 0, 0 },
    {  10560, D_CHORD, 0, 0, 5, 92 },                         /* F4 */
    {  10589, D_OFF, 0, 0, 0, 0 },
    {  10608, D_CHORD, 0, 0, 2, 80 },                         /* D4 */
    {  10637, D_OFF, 0, 0, 0, 0 },
    {  10656, D_CHORD, 0, 0, 9, 86 },                         /* A4 */
    {  10685, D_OFF, 0, 0, 0, 0 },
    {  10704, D_CHORD, 0, 0, 2, 78 },                         /* D4 */
    {  10733, D_OFF, 0, 0, 0, 0 },
    {  10752, D_CHORD, 0, 0, 7, 92 },                         /* G4 */
    {  10781, D_OFF, 0, 0, 0, 0 },
    {  10800, D_CHORD, 0, 0, 2, 80 },                         /* D4 */
    {  10829, D_OFF, 0, 0, 0, 0 },
    {  10848, D_CHORD, 0, 0, 11, 84 },                        /* B4 */
    {  10877, D_OFF, 0, 0, 0, 0 },
    {  10896, D_CHORD, 0, 0, 7, 76 },                         /* G4 */
    {  10925, D_OFF, 0, 0, 0, 0 },
    {  10944, D_CHORD, 0, 0, 7, 92 },                         /* G4 */
    {  10973, D_OFF, 0, 0, 0, 0 },
    {  10992, D_CHORD, 0, 0, 4, 80 },                         /* E4 */
    {  11021, D_OFF, 0, 0, 0, 0 },
    {  11040, D_CHORD, 0, 0, 0, 86 },                         /* C4 */
    {  11069, D_OFF, 0, 0, 0, 0 },
    {  11088, D_CHORD, 0, 0, 4, 78 },                         /* E4 */
    {  11117, D_OFF, 0, 0, 0, 0 },
    {  11136, D_CHORD, 0, 0, 8, 92 },                         /* G#4 */
    {  11165, D_OFF, 0, 0, 0, 0 },
    {  11184, D_CHORD, 0, 0, 4, 80 },                         /* E4 */
    {  11213, D_OFF, 0, 0, 0, 0 },
    {  11232, D_CHORD, 0, 0, 11, 84 },                        /* B4 */
    {  11261, D_OFF, 0, 0, 0, 0 },
    {  11280, D_CHORD, 0, 0, 4, 76 },                         /* E4 */
    {  11309, D_OFF, 0, 0, 0, 0 },
    {  11328, D_LOOP, LOOP_C_OVERDUB, 0, 0, 0 },              /* fine dell'overdub */
    {  11328, D_FOCUS, ENC_SOUND, 0, 0, 0 },
    {  11328, D_SOUND, 0, 0, 28, 0 },                         /* Tenor Sax */
    {  11328, D_PERF, PERF_OFF, 0, 0, 0 },
    {  11328, D_VOICING, 0, 0, 41, 0 },                       /* voicing 41: finestra da F */
    {  11328, D_THEME, THEME_LIGHT, 0, 0, 0 },
    {  11328, D_VIEW, VIEW_REACT, 0, 0, 0 },
    {  11328, D_CHORD, 0, 0, 4, 100 },                        /* E4 */
    {  11510, D_OFF, 0, 0, 0, 0 },
    {  11520, D_CHORD, 0, 0, 7, 92 },                         /* G4 */
    {  11611, D_OFF, 0, 0, 0, 0 },
    {  11616, D_CHORD, 0, 0, 9, 94 },                         /* A4 */
    {  11707, D_OFF, 0, 0, 0, 0 },
    {  11712, D_CHORD, 0, 0, 11, 104 },                       /* B4 */
    {  11940, D_OFF, 0, 0, 0, 0 },
    {  11952, D_CHORD, 0, 0, 9, 86 },                         /* A4 */
    {  11998, D_OFF, 0, 0, 0, 0 },
    {  12000, D_CHORD, 0, 0, 7, 92 },                         /* G4 */
    {  12091, D_OFF, 0, 0, 0, 0 },
    {  12096, D_CHORD, 0, 0, 7, 96 },                         /* G4 */
    {  12233, D_OFF, 0, 0, 0, 0 },
    {  12240, D_CHORD, 0, 0, 5, 86 },                         /* F4 */
    {  12286, D_OFF, 0, 0, 0, 0 },
    {  12288, D_CHORD, 0, 0, 4, 94 },                         /* E4 */
    {  12470, D_OFF, 0, 0, 0, 0 },
    {  12576, D_CHORD, 0, 0, 2, 88 },                         /* D4 */
    {  12667, D_OFF, 0, 0, 0, 0 },
    {  12672, D_CHORD, 0, 0, 4, 98 },                         /* E4 */
    {  12854, D_OFF, 0, 0, 0, 0 },
    {  12864, D_CHORD, 0, 0, 5, 100 },                        /* F4 */
    {  13001, D_OFF, 0, 0, 0, 0 },
    {  13008, D_CHORD, 0, 0, 9, 88 },                         /* A4 */
    {  13054, D_OFF, 0, 0, 0, 0 },
    {  13056, D_CHORD, 0, 0, 11, 104 },                       /* B4 */
    {  13238, D_OFF, 0, 0, 0, 0 },
    {  13248, D_CHORD, 0, 0, 11, 96 },                        /* B4 */
    {  13339, D_OFF, 0, 0, 0, 0 },
    {  13344, D_CHORD, 0, 0, 9, 86 },                         /* A4 */
    {  13390, D_OFF, 0, 0, 0, 0 },
    {  13392, D_CHORD, 0, 0, 7, 84 },                         /* G4 */
    {  13438, D_OFF, 0, 0, 0, 0 },
    {  13440, D_CHORD, 0, 0, 4, 96 },                         /* E4 */
    {  13622, D_OFF, 0, 0, 0, 0 },
    {  13632, D_CHORD, 0, 0, 9, 102 },                        /* A4 */
    {  13769, D_OFF, 0, 0, 0, 0 },
    {  13776, D_CHORD, 0, 0, 7, 90 },                         /* G4 */
    {  13822, D_OFF, 0, 0, 0, 0 },
    {  13824, D_CHORD, 0, 0, 11, 100 },                       /* B4 */
    {  13915, D_OFF, 0, 0, 0, 0 },
    {  13920, D_CHORD, 0, 0, 9, 94 },                         /* A4 */
    {  14011, D_OFF, 0, 0, 0, 0 },
    {  14016, D_CHORD, 0, 0, 9, 104 },                        /* A4 */
    {  14290, D_OFF, 0, 0, 0, 0 },
    {  14352, D_HOLD, ENC_PERFORM, 0, 0, 0 },                 /* Lock del Perform spento */
    {  14352, D_FOCUS, ENC_SOUND, 0, 0, 0 },
    {  14352, D_SOUND, 0, 0, 23, 0 },                         /* Concert Harp, Harp 4 */
    {  14352, D_PERF, PERF_HARP, 4, 0, 0 },
    {  14352, D_VOICING, 0, 0, 36, 0 },                       /* voicing 36: finestra da C */
    {  14400, D_VIEW, VIEW_CHORD, 0, 0, 0 },
    {  14400, D_CHORD, 0x4, 0x4, 5, 78 },                     /* Fmaj7: C4 E4 F4 A4 */
    {  14760, D_OFF, 0, 0, 0, 0 },
    {  14784, D_CHORD, 0x4, 0x0, 7, 80 },                     /* G: D4 G4 B4 */
    {  15144, D_OFF, 0, 0, 0, 0 },
    {  15168, D_CHORD, 0x2, 0x2, 9, 78 },                     /* Am7: C4 E4 G4 A4 */
    {  15528, D_OFF, 0, 0, 0, 0 },
    {  15552, D_CHORD, 0x4, 0x2, 4, 82 },                     /* E7: D4 E4 G#4 B4 */
    {  15912, D_OFF, 0, 0, 0, 0 },
    {  15936, D_CHORD, 0x4, 0x4, 5, 80 },                     /* Fmaj7: C4 E4 F4 A4 */
    {  15936, D_LOOP, LOOP_C_STOP, 0, 0, 0 },                 /* pausa del loop */
    {  15936, D_BEATON, 0, 0, 0, 0 },
    {  16296, D_OFF, 0, 0, 0, 0 },
    {  16320, D_CHORD, 0x4, 0x0, 7, 82 },                     /* G: D4 G4 B4 */
    {  16680, D_OFF, 0, 0, 0, 0 },
    {  16704, D_CHORD, 0x2, 0x2, 9, 84 },                     /* Am7: C4 E4 G4 A4 */
    {  17064, D_OFF, 0, 0, 0, 0 },
    {  17088, D_CHORD, 0x2, 0x2, 9, 80 },                     /* Am7: C4 E4 G4 A4 */
    {  17448, D_OFF, 0, 0, 0, 0 },
    {  17472, D_FOCUS, ENC_SOUND, 0, 0, 0 },
    {  17472, D_SOUND, 0, 0, 21, 0 },                         /* Glockenspiel, Harp 3 */
    {  17472, D_PERF, PERF_HARP, 3, 0, 0 },
    {  17472, D_THEME, THEME_DARK, 0, 0, 0 },
    {  17472, D_FOCUS, ENC_BPM, 0, 0, 0 },
    {  17472, D_BPM, 0, 0, 100, 0 },                          /* ritardando: 100 BPM */
    {  17472, D_LOOP, LOOP_C_CLEAR, 0, 0, 0 },                /* Clear */
    {  17472, D_CHORD, 0x2, 0xa, 9, 92 },                     /* Am9: C4 E4 G4 A4 B4 */
    {  17856, D_BPM, 0, 0, 88, 0 },                           /* ritardando: 88 BPM */
    {  17856, D_VOICING, 0, 0, 41, 0 },                       /* voicing 41: finestra da F */
    {  18240, D_BPM, 0, 0, 76, 0 },                           /* ritardando: 76 BPM */
    {  18240, D_OFF, 0, 0, 0, 0 },
    {  18240, D_VOICING, 0, 0, 46, 0 },                       /* voicing 46: finestra da A# */
    {  19008, D_END, 0, 0, 0, 0 },
};

/* Demo song: Pistillo: 124 BPM, 49 battute, 277 passi, 1:38 */
static const dstep_t SONG_2[] = {
    {      0, D_TITLE, 0, 0, 0, 0 },
    {      0, D_THEME, THEME_DARK, 0, 0, 0 },
    {      0, D_VIEW, VIEW_CHORD, 0, 0, 0 },
    {      0, D_OPT, ACC_OPT_KEY_ON, 0, 0, 0 },
    {      0, D_OPT, ACC_OPT_BASS_ON, 0, 0, 0 },
    {      0, D_OPT, ACC_OPT_SINGLE_NOTES, 1, 0, 0 },
    {      0, D_OPT, ACC_OPT_BASS_VOICING, 23, 0, 0 },
    {      0, D_OPT, ACC_OPT_VOICING, 36, 0, 0 },
    {      0, D_FOCUS, ENC_BPM, 0, 0, 0 },
    {      0, D_BPM, 0, 0, 124, 0 },                          /* 124 BPM */
    {     48, D_FOCUS, ENC_SOUND, 0, 0, 0 },
    {     48, D_SOUND, 0, 0, 18, 0 },                         /* FM Piano, Pattern 5 */
    {     48, D_PERF, PERF_PATTERN, 5, 0, 0 },
    {    192, D_CHORD, 0x2, 0xa, 4, 90 },                     /* Em9: D4 E4 F#4 G4 B4 */
    {    360, D_OFF, 0, 0, 0, 0 },
    {    384, D_CHORD, 0x2, 0x2, 4, 82 },                     /* Em7: D4 E4 G4 B4 */
    {    552, D_OFF, 0, 0, 0, 0 },
    {    576, D_CHORD, 0x4, 0x4, 0, 90 },                     /* Cmaj7: C4 E4 G4 B4 */
    {    744, D_OFF, 0, 0, 0, 0 },
    {    768, D_CHORD, 0x4, 0x4, 0, 82 },                     /* Cmaj7: C4 E4 G4 B4 */
    {    936, D_OFF, 0, 0, 0, 0 },
    {    960, D_CHORD, 0x4, 0x0, 7, 90 },                     /* G: D4 G4 B4 */
    {   1128, D_OFF, 0, 0, 0, 0 },
    {   1152, D_CHORD, 0x4, 0x1, 7, 82 },                     /* G6: D4 E4 G4 B4 */
    {   1320, D_OFF, 0, 0, 0, 0 },
    {   1344, D_CHORD, 0x8, 0x2, 2, 90 },                     /* D7sus: C4 D4 G4 A4 */
    {   1512, D_OFF, 0, 0, 0, 0 },
    {   1536, D_CHORD, 0x4, 0x0, 2, 82 },                     /* D: D4 F#4 A4 */
    {   1704, D_OFF, 0, 0, 0, 0 },
    {   1728, D_BEAT, 6, 0, 0, 0 },                           /* Beat: Boom Bap, kit 808 */
    {   1728, D_BEATON, 1, 0, 0, 0 },
    {   1728, D_FOCUS, ENC_BASS, 0, 0, 0 },
    {   1728, D_PRESS, ENC_BASS, 0, 0, 0 },                   /* basso acceso */
    {   1728, D_VOICING, 0, 0, 24, 0 },                       /* voicing 24: finestra da C */
    {   1728, D_CHORD, 0x2, 0xa, 4, 94 },                     /* Em9: D3 E3 F#3 G3 B3 */
    {   1776, D_BASS, 0, 0, 1, 0 },                           /* Sub Floor */
    {   1896, D_OFF, 0, 0, 0, 0 },
    {   1920, D_CHORD, 0x2, 0x2, 4, 84 },                     /* Em7: D3 E3 G3 B3 */
    {   2088, D_OFF, 0, 0, 0, 0 },
    {   2112, D_CHORD, 0x4, 0x4, 0, 94 },                     /* Cmaj7: C3 E3 G3 B3 */
    {   2280, D_OFF, 0, 0, 0, 0 },
    {   2304, D_CHORD, 0x4, 0x4, 0, 84 },                     /* Cmaj7: C3 E3 G3 B3 */
    {   2472, D_OFF, 0, 0, 0, 0 },
    {   2496, D_CHORD, 0x4, 0x0, 7, 94 },                     /* G: D3 G3 B3 */
    {   2664, D_OFF, 0, 0, 0, 0 },
    {   2688, D_CHORD, 0x4, 0x1, 7, 84 },                     /* G6: D3 E3 G3 B3 */
    {   2856, D_OFF, 0, 0, 0, 0 },
    {   2880, D_CHORD, 0x8, 0x2, 2, 94 },                     /* D7sus: C3 D3 G3 A3 */
    {   3048, D_OFF, 0, 0, 0, 0 },
    {   3072, D_CHORD, 0x4, 0x0, 2, 84 },                     /* D: D3 F#3 A3 */
    {   3240, D_OFF, 0, 0, 0, 0 },
    {   3264, D_CHORD, 0x2, 0xa, 4, 94 },                     /* Em9: D3 E3 F#3 G3 B3 */
    {   3432, D_OFF, 0, 0, 0, 0 },
    {   3456, D_CHORD, 0x2, 0x2, 4, 84 },                     /* Em7: D3 E3 G3 B3 */
    {   3624, D_OFF, 0, 0, 0, 0 },
    {   3648, D_CHORD, 0x4, 0x4, 0, 94 },                     /* Cmaj7: C3 E3 G3 B3 */
    {   3816, D_OFF, 0, 0, 0, 0 },
    {   3840, D_CHORD, 0x4, 0x4, 0, 84 },                     /* Cmaj7: C3 E3 G3 B3 */
    {   4008, D_OFF, 0, 0, 0, 0 },
    {   4032, D_CHORD, 0x4, 0x0, 7, 94 },                     /* G: D3 G3 B3 */
    {   4200, D_OFF, 0, 0, 0, 0 },
    {   4224, D_CHORD, 0x4, 0x1, 7, 84 },                     /* G6: D3 E3 G3 B3 */
    {   4392, D_OFF, 0, 0, 0, 0 },
    {   4416, D_CHORD, 0x8, 0x2, 2, 94 },                     /* D7sus: C3 D3 G3 A3 */
    {   4584, D_OFF, 0, 0, 0, 0 },
    {   4608, D_CHORD, 0x4, 0x0, 2, 84 },                     /* D: D3 F#3 A3 */
    {   4776, D_OFF, 0, 0, 0, 0 },
    {   4800, D_LOOP, LOOP_C_PRESS, 0, 0, 0 },                /* REC: count-in, poi 4 battute */
    {   4800, D_VIEW, VIEW_CHORD_KB, 0, 0, 0 },
    {   5184, D_CHORD, 0x2, 0xa, 4, 96 },                     /* Em9: D3 E3 F#3 G3 B3 */
    {   5352, D_OFF, 0, 0, 0, 0 },
    {   5376, D_CHORD, 0x2, 0x2, 4, 86 },                     /* Em7: D3 E3 G3 B3 */
    {   5544, D_OFF, 0, 0, 0, 0 },
    {   5568, D_CHORD, 0x4, 0x4, 0, 96 },                     /* Cmaj7: C3 E3 G3 B3 */
    {   5736, D_OFF, 0, 0, 0, 0 },
    {   5760, D_CHORD, 0x4, 0x4, 0, 86 },                     /* Cmaj7: C3 E3 G3 B3 */
    {   5928, D_OFF, 0, 0, 0, 0 },
    {   5952, D_CHORD, 0x4, 0x0, 7, 96 },                     /* G: D3 G3 B3 */
    {   6120, D_OFF, 0, 0, 0, 0 },
    {   6144, D_CHORD, 0x4, 0x1, 7, 86 },                     /* G6: D3 E3 G3 B3 */
    {   6312, D_OFF, 0, 0, 0, 0 },
    {   6336, D_CHORD, 0x8, 0x2, 2, 96 },                     /* D7sus: C3 D3 G3 A3 */
    {   6504, D_OFF, 0, 0, 0, 0 },
    {   6528, D_CHORD, 0x4, 0x0, 2, 86 },                     /* D: D3 F#3 A3 */
    {   6624, D_FOCUS, ENC_SOUND, 0, 0, 0 },
    {   6624, D_SOUND, 0, 0, 20, 0 },                         /* Marimba */
    {   6624, D_PERF, PERF_OFF, 0, 0, 0 },
    {   6648, D_HOLD, ENC_PERFORM, 0, 0, 0 },                 /* Lock del Perform acceso */
    {   6672, D_VOICING, 0, 0, 48, 0 },                       /* voicing 48: finestra da C */
    {   6696, D_OFF, 0, 0, 0, 0 },
    {   6720, D_VIEW, VIEW_NOTES, 0, 0, 0 },
    {   6720, D_CHORD, 0, 0, 4, 100 },                        /* E5 */
    {   6763, D_OFF, 0, 0, 0, 0 },
    {   6768, D_CHORD, 0, 0, 7, 86 },                         /* G5 */
    {   6811, D_OFF, 0, 0, 0, 0 },
    {   6816, D_CHORD, 0, 0, 11, 96 },                        /* B5 */
    {   6902, D_OFF, 0, 0, 0, 0 },
    {   6912, D_CHORD, 0, 0, 9, 90 },                         /* A5 */
    {   6955, D_OFF, 0, 0, 0, 0 },
    {   6960, D_CHORD, 0, 0, 7, 84 },                         /* G5 */
    {   7003, D_OFF, 0, 0, 0, 0 },
    {   7008, D_CHORD, 0, 0, 4, 92 },                         /* E5 */
    {   7094, D_OFF, 0, 0, 0, 0 },
    {   7104, D_CHORD, 0, 0, 9, 102 },                        /* A5 */
    {   7147, D_OFF, 0, 0, 0, 0 },
    {   7152, D_CHORD, 0, 0, 11, 88 },                        /* B5 */
    {   7195, D_OFF, 0, 0, 0, 0 },
    {   7200, D_CHORD, 0, 0, 7, 96 },                         /* G5 */
    {   7286, D_OFF, 0, 0, 0, 0 },
    {   7296, D_CHORD, 0, 0, 4, 92 },                         /* E5 */
    {   7382, D_OFF, 0, 0, 0, 0 },
    {   7392, D_CHORD, 0, 0, 2, 86 },                         /* D5 */
    {   7478, D_OFF, 0, 0, 0, 0 },
    {   7488, D_CHORD, 0, 0, 2, 98 },                         /* D5 */
    {   7531, D_OFF, 0, 0, 0, 0 },
    {   7536, D_CHORD, 0, 0, 7, 86 },                         /* G5 */
    {   7579, D_OFF, 0, 0, 0, 0 },
    {   7584, D_CHORD, 0, 0, 11, 96 },                        /* B5 */
    {   7670, D_OFF, 0, 0, 0, 0 },
    {   7680, D_CHORD, 0, 0, 9, 100 },                        /* A5 */
    {   7766, D_OFF, 0, 0, 0, 0 },
    {   7776, D_CHORD, 0, 0, 11, 90 },                        /* B5 */
    {   7862, D_OFF, 0, 0, 0, 0 },
    {   7872, D_CHORD, 0, 0, 9, 98 },                         /* A5 */
    {   8002, D_OFF, 0, 0, 0, 0 },
    {   8016, D_CHORD, 0, 0, 6, 86 },                         /* F#5 */
    {   8059, D_OFF, 0, 0, 0, 0 },
    {   8064, D_CHORD, 0, 0, 2, 94 },                         /* D5 */
    {   8237, D_OFF, 0, 0, 0, 0 },
    {   8256, D_CHORD, 0, 0, 4, 100 },                        /* E5 */
    {   8299, D_OFF, 0, 0, 0, 0 },
    {   8304, D_CHORD, 0, 0, 7, 86 },                         /* G5 */
    {   8347, D_OFF, 0, 0, 0, 0 },
    {   8352, D_CHORD, 0, 0, 11, 96 },                        /* B5 */
    {   8438, D_OFF, 0, 0, 0, 0 },
    {   8448, D_CHORD, 0, 0, 9, 92 },                         /* A5 */
    {   8491, D_OFF, 0, 0, 0, 0 },
    {   8496, D_CHORD, 0, 0, 11, 86 },                        /* B5 */
    {   8539, D_OFF, 0, 0, 0, 0 },
    {   8544, D_CHORD, 0, 0, 7, 92 },                         /* G5 */
    {   8630, D_OFF, 0, 0, 0, 0 },
    {   8640, D_CHORD, 0, 0, 11, 104 },                       /* B5 */
    {   8726, D_OFF, 0, 0, 0, 0 },
    {   8736, D_CHORD, 0, 0, 9, 90 },                         /* A5 */
    {   8779, D_OFF, 0, 0, 0, 0 },
    {   8784, D_CHORD, 0, 0, 7, 88 },                         /* G5 */
    {   8827, D_OFF, 0, 0, 0, 0 },
    {   8832, D_CHORD, 0, 0, 4, 94 },                         /* E5 */
    {   8918, D_OFF, 0, 0, 0, 0 },
    {   8928, D_CHORD, 0, 0, 2, 90 },                         /* D5 */
    {   9014, D_OFF, 0, 0, 0, 0 },
    {   9024, D_CHORD, 0, 0, 6, 96 },                         /* F#5 */
    {   9110, D_OFF, 0, 0, 0, 0 },
    {   9120, D_CHORD, 0, 0, 7, 92 },                         /* G5 */
    {   9206, D_OFF, 0, 0, 0, 0 },
    {   9216, D_CHORD, 0, 0, 9, 96 },                         /* A5 */
    {   9302, D_OFF, 0, 0, 0, 0 },
    {   9312, D_CHORD, 0, 0, 11, 100 },                       /* B5 */
    {   9398, D_OFF, 0, 0, 0, 0 },
    {   9408, D_CHORD, 0, 0, 4, 102 },                        /* E5 */
    {   9667, D_OFF, 0, 0, 0, 0 },
    {   9696, D_FOCUS, ENC_SOUND, 0, 0, 0 },
    {   9696, D_SOUND, 0, 0, 26, 0 },                         /* Pipe Organ */
    {   9696, D_PERF, PERF_OFF, 0, 0, 0 },
    {   9744, D_VOICING, 0, 0, 36, 0 },                       /* voicing 36: finestra da C */
    {   9792, D_LOOP, LOOP_C_OVERDUB, 0, 0, 0 },              /* overdub */
    {   9792, D_VIEW, VIEW_CHORD, 0, 0, 0 },
    {   9792, D_CHORD, 0x2, 0xa, 4, 80 },                     /* Em9: D4 E4 F#4 G4 B4 */
    {  10152, D_OFF, 0, 0, 0, 0 },
    {  10176, D_CHORD, 0x4, 0x4, 0, 80 },                     /* Cmaj7: C4 E4 G4 B4 */
    {  10536, D_OFF, 0, 0, 0, 0 },
    {  10560, D_CHORD, 0x4, 0x0, 7, 82 },                     /* G: D4 G4 B4 */
    {  10920, D_OFF, 0, 0, 0, 0 },
    {  10944, D_CHORD, 0x8, 0x2, 2, 82 },                     /* D7sus: C4 D4 G4 A4 */
    {  11304, D_OFF, 0, 0, 0, 0 },
    {  11328, D_LOOP, LOOP_C_OVERDUB, 0, 0, 0 },              /* fine dell'overdub */
    {  11328, D_BEAT, 7, 0, 0, 0 },                           /* Beat: Disco, kit studio */
    {  11328, D_THEME, THEME_LIGHT, 0, 0, 0 },
    {  11328, D_FOCUS, ENC_SOUND, 0, 0, 0 },
    {  11328, D_SOUND, 0, 0, 27, 0 },                         /* Alto Recorder */
    {  11328, D_PERF, PERF_OFF, 0, 0, 0 },
    {  11328, D_VOICING, 0, 0, 41, 0 },                       /* voicing 41: finestra da F */
    {  11328, D_VIEW, VIEW_REACT, 0, 0, 0 },
    {  11328, D_CHORD, 0, 0, 11, 96 },                        /* B4 */
    {  11458, D_OFF, 0, 0, 0, 0 },
    {  11472, D_CHORD, 0, 0, 9, 84 },                         /* A4 */
    {  11515, D_OFF, 0, 0, 0, 0 },
    {  11520, D_CHORD, 0, 0, 7, 92 },                         /* G4 */
    {  11606, D_OFF, 0, 0, 0, 0 },
    {  11616, D_CHORD, 0, 0, 4, 88 },                         /* E4 */
    {  11702, D_OFF, 0, 0, 0, 0 },
    {  11712, D_CHORD, 0, 0, 7, 96 },                         /* G4 */
    {  11885, D_OFF, 0, 0, 0, 0 },
    {  11904, D_CHORD, 0, 0, 9, 90 },                         /* A4 */
    {  11990, D_OFF, 0, 0, 0, 0 },
    {  12000, D_CHORD, 0, 0, 11, 94 },                        /* B4 */
    {  12086, D_OFF, 0, 0, 0, 0 },
    {  12096, D_CHORD, 0, 0, 11, 100 },                       /* B4 */
    {  12226, D_OFF, 0, 0, 0, 0 },
    {  12240, D_CHORD, 0, 0, 9, 86 },                         /* A4 */
    {  12283, D_OFF, 0, 0, 0, 0 },
    {  12288, D_CHORD, 0, 0, 7, 92 },                         /* G4 */
    {  12374, D_OFF, 0, 0, 0, 0 },
    {  12384, D_CHORD, 0, 0, 4, 88 },                         /* E4 */
    {  12470, D_OFF, 0, 0, 0, 0 },
    {  12480, D_CHORD, 0, 0, 6, 94 },                         /* F#4 */
    {  12653, D_OFF, 0, 0, 0, 0 },
    {  12672, D_CHORD, 0, 0, 2, 90 },                         /* D4 */
    {  12845, D_OFF, 0, 0, 0, 0 },
    {  12864, D_CHORD, 0, 0, 4, 92 },                         /* E4 */
    {  12950, D_OFF, 0, 0, 0, 0 },
    {  12960, D_CHORD, 0, 0, 7, 90 },                         /* G4 */
    {  13046, D_OFF, 0, 0, 0, 0 },
    {  13056, D_CHORD, 0, 0, 11, 98 },                        /* B4 */
    {  13186, D_OFF, 0, 0, 0, 0 },
    {  13200, D_CHORD, 0, 0, 9, 86 },                         /* A4 */
    {  13243, D_OFF, 0, 0, 0, 0 },
    {  13248, D_CHORD, 0, 0, 7, 94 },                         /* G4 */
    {  13334, D_OFF, 0, 0, 0, 0 },
    {  13344, D_CHORD, 0, 0, 4, 88 },                         /* E4 */
    {  13430, D_OFF, 0, 0, 0, 0 },
    {  13440, D_CHORD, 0, 0, 2, 92 },                         /* D4 */
    {  13613, D_OFF, 0, 0, 0, 0 },
    {  13632, D_CHORD, 0, 0, 11, 98 },                        /* B4 */
    {  13718, D_OFF, 0, 0, 0, 0 },
    {  13728, D_CHORD, 0, 0, 9, 100 },                        /* A4 */
    {  13814, D_OFF, 0, 0, 0, 0 },
    {  13824, D_CHORD, 0, 0, 11, 90 },                        /* B4 */
    {  13867, D_OFF, 0, 0, 0, 0 },
    {  13872, D_CHORD, 0, 0, 9, 86 },                         /* A4 */
    {  13915, D_OFF, 0, 0, 0, 0 },
    {  13920, D_CHORD, 0, 0, 7, 92 },                         /* G4 */
    {  14006, D_OFF, 0, 0, 0, 0 },
    {  14016, D_CHORD, 0, 0, 4, 96 },                         /* E4 */
    {  14275, D_OFF, 0, 0, 0, 0 },
    {  14352, D_HOLD, ENC_PERFORM, 0, 0, 0 },                 /* Lock del Perform spento */
    {  14352, D_FOCUS, ENC_SOUND, 0, 0, 0 },
    {  14352, D_SOUND, 0, 0, 22, 0 },                         /* Tubular Bells */
    {  14352, D_PERF, PERF_OFF, 0, 0, 0 },
    {  14352, D_VOICING, 0, 0, 36, 0 },                       /* voicing 36: finestra da C */
    {  14400, D_VIEW, VIEW_CHORD, 0, 0, 0 },
    {  14400, D_FOCUS, ENC_KEY, 0, 0, 0 },
    {  14400, D_PTURN, ENC_KEY, 2, 0, 0 },                    /* transpose +2: anche il loop sale (ACC-221) */
    {  14400, D_CHORD, 0x2, 0xa, 4, 96 },                     /* Em9: D4 E4 F#4 G4 B4 */
    {  14760, D_OFF, 0, 0, 0, 0 },
    {  14976, D_CHORD, 0x4, 0x4, 0, 92 },                     /* Cmaj7: C4 E4 G4 B4 */
    {  15144, D_OFF, 0, 0, 0, 0 },
    {  15168, D_CHORD, 0x4, 0x0, 7, 94 },                     /* G: D4 G4 B4 */
    {  15528, D_OFF, 0, 0, 0, 0 },
    {  15744, D_CHORD, 0x8, 0x2, 2, 92 },                     /* D7sus: C4 D4 G4 A4 */
    {  15912, D_OFF, 0, 0, 0, 0 },
    {  15936, D_CHORD, 0x2, 0xa, 4, 98 },                     /* Em9: D4 E4 F#4 G4 B4 */
    {  16296, D_OFF, 0, 0, 0, 0 },
    {  16512, D_CHORD, 0x4, 0x4, 0, 94 },                     /* Cmaj7: C4 E4 G4 B4 */
    {  16680, D_OFF, 0, 0, 0, 0 },
    {  16704, D_CHORD, 0x4, 0x0, 7, 96 },                     /* G: D4 G4 B4 */
    {  16872, D_OFF, 0, 0, 0, 0 },
    {  16896, D_CHORD, 0x4, 0x0, 2, 100 },                    /* D: D4 F#4 A4 */
    {  17064, D_OFF, 0, 0, 0, 0 },
    {  17088, D_CHORD, 0x2, 0xa, 4, 104 },                    /* Em9: D4 E4 F#4 G4 B4 */
    {  17448, D_OFF, 0, 0, 0, 0 },
    {  17472, D_LOOP, LOOP_C_UNDO, 0, 0, 0 },                 /* Undo: via l'organo */
    {  17472, D_BEATON, 0, 0, 0, 0 },
    {  17472, D_THEME, THEME_DARK, 0, 0, 0 },
    {  17472, D_FOCUS, ENC_SOUND, 0, 0, 0 },
    {  17472, D_SOUND, 0, 0, 23, 0 },                         /* Concert Harp, Harp 4 */
    {  17472, D_PERF, PERF_HARP, 4, 0, 0 },
    {  17472, D_FOCUS, ENC_BPM, 0, 0, 0 },
    {  17472, D_BPM, 0, 0, 110, 0 },                          /* ritardando: 110 BPM */
    {  17472, D_LOOP, LOOP_C_CLEAR, 0, 0, 0 },                /* Clear */
    {  17472, D_CHORD, 0x2, 0xa, 4, 96 },                     /* Em9: D4 E4 F#4 G4 B4 */
    {  17856, D_BPM, 0, 0, 96, 0 },                           /* ritardando: 96 BPM */
    {  17856, D_VOICING, 0, 0, 41, 0 },                       /* voicing 41: finestra da F */
    {  18240, D_BPM, 0, 0, 84, 0 },                           /* ritardando: 84 BPM */
    {  18240, D_OFF, 0, 0, 0, 0 },
    {  18240, D_VOICING, 0, 0, 46, 0 },                       /* voicing 46: finestra da A# */
    {  19008, D_END, 0, 0, 0, 0 },
};

const dsong_t vet_demo_songs[] = {
    { "Demo song: Acacia", SONG_0, (uint16_t)(sizeof SONG_0 / sizeof SONG_0[0]), 230992u },
    { "Demo song: Felce", SONG_1, (uint16_t)(sizeof SONG_1 / sizeof SONG_1[0]), 108943u },
    { "Demo song: Pistillo", SONG_2, (uint16_t)(sizeof SONG_2 / sizeof SONG_2[0]), 98461u },
};

const uint8_t vet_demo_songs_n = 3;
