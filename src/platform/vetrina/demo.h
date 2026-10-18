/* demo.h — il copione della demo della vetrina.
 *
 * Il brano è una lista di passi a tempo musicale: tick a 96 PPQN dall'inizio del brano. Ogni passo è
 * un gesto che un musicista farebbe sulla plancia (un accordo, una nota, un encoder girato o premuto,
 * un comando del looper), così la plancia mostra quello che si sente. Il brano sta in demo_song.c,
 * generato da tools/demo.py: si cambia lì, non a mano.
 */
#ifndef STAME_DEMO_H
#define STAME_DEMO_H
#include <stdint.h>

enum {
    D_CHORD,    /* a = tipi (bit ACC_DIM…ACC_SUS), b = estensioni (bit ACC_E6…ACC_E9), c = tasto 0…11,
                   d = velocity; senza tipi è una nota singola */
    D_OFF,      /* rilascia l'accordo o la nota */
    D_TURN,     /* a = encoder (ENC_*), b = scatti con segno */
    D_PTURN,    /* premi e ruota: a = encoder, b = scatti */
    D_PRESS,    /* a = encoder */
    D_HOLD,     /* a = encoder tenuto 1 s: Lock del Perform, lista dei Beat */
    D_BACK,
    D_FOCUS,    /* a = encoder */
    D_VIEW,     /* a = VIEW_* */
    D_THEME,    /* a = THEME_DARK: il tema di chi suona (salvato all'avvio della demo); THEME_LIGHT: l'altro.
                   Così la demo parte nel tema scelto e cambia solo dove mostra i due temi */
    D_LOOP,     /* a = LOOP_C_* */
    D_BEATON,   /* a = 1 acceso, 0 spento (TRANSPORT_TOGGLE) */
    D_MENU,
    D_PAGE,     /* a = secondi della pagina dei comandi */
    D_SOUND,    /* c = suono: ci arriva girando Sound */
    D_PERF,     /* a = modo (PERF_*), b = amount */
    D_VOICING,  /* c = Chord Voicing 1…60: ci arriva girando il voicing */
    D_BASS,     /* c = suono del basso: ci arriva girando Bass */
    D_BEAT,     /* a = Beat 0…18 della vetrina, scelto senza la lista */
    D_BPM,      /* c = BPM: ci arriva girando BPM */
    D_OPT,      /* a = ACC_OPT_*, b = valore: preparazione, senza overlay */
    D_TITLE,    /* il titolo del brano nel messaggio della piattaforma */
    D_DRUMS,    /* batteria a tastiera on/off (Mod + BPM, ACC-211) */
    D_HIT,      /* a = tasto 0…11 (strumento del kit), d = velocity: un colpo della batteria a tastiera */
    D_MACRO,    /* a = MACRO_*, b = valore con segno: un comando del macro pad (m2 girata sotto DRUMS, MIDI-139) */
    D_END       /* fine: il brano ricomincia */
};

typedef struct { uint32_t t; uint8_t act; int8_t a, b; uint8_t c, d; } dstep_t;

/* un brano: titolo per il messaggio, passi, quanti, durata in ms con i suoi cambi di tempo */
typedef struct { const char *title; const dstep_t *steps; uint16_t n; uint32_t ms; } dsong_t;

extern const dsong_t vet_demo_songs[];      /* i brani della demo, uno dopo l'altro (demo_song.c) */
extern const uint8_t vet_demo_songs_n;

#endif
