/* test_input.c — profili dei controller, stato unito, gesti e fuoco (sezione 40, §8–§11):
 * esempio di §10.5, T-MIDI-11, 12, 14, 15, 16–21 e le regole MIDI-072…105, 112, 120…127. */
#include "test.h"
#include "core/input/input.h"
#include <string.h>

#define T0    1000000u
#define MAXEV 256

static inp_t H;
static midi_parser_t MP;
static pnl_event_t EV[MAXEV];
static int NEV;
static uint32_t NOW;
static uint32_t DROPPED;        /* eventi persi nei banchi di prova precedenti: deve restare 0 */

static void clear(void) { NEV = 0; }

/* tutto da capo: MPK, Flip e macro pad collegati, fuoco su Sound */
static void reset(void)
{
    DROPPED += inp_dropped(&H);
    inp_init(&H);
    midi_parser_init(&MP, MIDI_PORT_CTL);
    NOW = T0;
    NEV = 0;
    for (uint8_t s = 0; s < SRC_COUNT; s++) NEV += inp_connected(&H, s, NOW, EV + NEV, MAXEV - NEV);
    clear();
}

static unsigned hexbyte(const char **p)
{
    unsigned v = 0;
    for (int i = 0; i < 2; i++, (*p)++) v = v * 16 + (unsigned)(**p <= '9' ? **p - '0' : **p - 'A' + 10);
    return v;
}

/* byte della porta 1 della MPK, in esadecimale, all'istante NOW, attraverso il parser */
static void mpk(const char *hex)
{
    midi_msg_t m[MIDI_PARSE_MAX_OUT];
    for (const char *p = hex; *p; ) {
        while (*p == ' ') p++;
        if (!*p) break;
        int k = midi_parse_byte(&MP, (uint8_t)hexbyte(&p), NOW, m);
        for (int j = 0; j < k; j++) NEV += inp_midi(&H, &m[j], EV + NEV, MAXEV - NEV);
    }
}

static void pad(uint16_t code, int32_t value)
{
    NEV += inp_pad(&H, code, value, NOW, EV + NEV, MAXEV - NEV);
}

static void tap(uint16_t code) { pad(code, 1); pad(code, 0); }

static void lost(uint8_t src) { NEV += inp_lost(&H, src, NOW, EV + NEV, MAXEV - NEV); }
static void connected(uint8_t src) { NEV += inp_connected(&H, src, NOW, EV + NEV, MAXEV - NEV); }

/* fa passare dt µs, con un tick ogni 10 ms */
static void wait_us(uint32_t dt)
{
    uint32_t end = NOW + dt;
    while (pnl_dt(end, NOW) > 0) {
        NOW += PNL_TICK_US;
        if (pnl_dt(NOW, end) > 0) NOW = end;
        NEV += inp_tick(&H, NOW, EV + NEV, MAXEV - NEV);
    }
}

static int count(uint8_t type, uint8_t a)
{
    int c = 0;
    for (int i = 0; i < NEV; i++) if (EV[i].type == type && EV[i].a == a) c++;
    return c;
}

static int find(uint8_t type, uint8_t a)
{
    for (int i = 0; i < NEV; i++) if (EV[i].type == type && EV[i].a == a) return i;
    return -1;
}

static int sum_b(uint8_t type, uint8_t a)
{
    int s = 0;
    for (int i = 0; i < NEV; i++) if (EV[i].type == type && EV[i].a == a) s += EV[i].b;
    return s;
}

/* l'unico evento registrato è type/a/b */
static bool only(uint8_t type, uint8_t a, int b)
{
    return NEV == 1 && EV[0].type == type && EV[0].a == a && EV[0].b == b;
}

/* ------------------------------------------------------------------ MPK */

/* §10.5: dal byte al gesto */
static void t_esempio(void)
{
    reset();
    mpk("B0 46 01");
    CHECK_EQ(NEV, 0);
    mpk("B0 46 01");
    CHECK(only(G_TURN, ENC_SOUND, 1));
}

/* MIDI-079, T-MIDI-12 */
static void t_tastiera(void)
{
    reset();
    mpk("90 30 64 90 3C 50");                                 /* due Do: 48 e 60 */
    CHECK(only(PNL_KEY_DOWN, 0, 100));
    clear();
    mpk("80 30 00");
    CHECK_EQ(NEV, 0);
    mpk("80 3C 00");
    CHECK(only(PNL_KEY_UP, 0, 0));

    /* velocity invariata, Note On a velocity 0, Note On doppio, Note Off orfano */
    clear();
    mpk("90 3E 21 3E 00 90 41 64 41 64 80 43 00");
    CHECK_EQ(NEV, 3);
    CHECK(EV[0].type == PNL_KEY_DOWN && EV[0].a == 2 && EV[0].b == 0x21);
    CHECK(EV[1].type == PNL_KEY_UP && EV[1].a == 2);
    CHECK(EV[2].type == PNL_KEY_DOWN && EV[2].a == 5);
}

/* MIDI-078, MIDI-080: banco A = tasti accordo; velocity e aftertouch dei pad ignorati */
static void t_pad_accordi(void)
{
    static const uint8_t WANT[8] = { CHB_6, CHB_MIN7, CHB_MAJ7, CHB_9, CHB_DIM, CHB_MIN, CHB_MAJ, CHB_SUS };
    char msg[16];
    reset();
    for (int i = 0; i < 8; i++) {
        clear();
        snprintf(msg, sizeof msg, "99 %02X 10", (unsigned)(36 + i));
        mpk(msg);
        CHECKM(only(PNL_CHORD_DOWN, WANT[i], 0), "nota %d", 36 + i);
        clear();
        snprintf(msg, sizeof msg, "89 %02X 00", (unsigned)(36 + i));
        mpk(msg);
        CHECKM(only(PNL_CHORD_UP, WANT[i], 0), "nota %d", 36 + i);
    }
    clear();
    mpk("99 28 7F A9 28 40 D9 40 89 29 00");                  /* aftertouch e Note Off orfano */
    CHECK(only(PNL_CHORD_DOWN, CHB_DIM, 0));
    CHECK_EQ(H.mpk.bank, MPK_BANK_A);
}

/* MIDI-089: banco stimato; una nota di un banco rilascia ciò che è premuto nell'altro */
static void t_banco(void)
{
    mpk_state_t s;
    pnl_event_t raw[PNL_MAX_OUT];
    static const uint8_t DIM_ON[3] = { 0x99, 40, 127 }, KEY_ON[3] = { 0x99, 44, 127 };
    MPK_STAME.reset(&s);
    CHECK_EQ(s.bank, MPK_BANK_UNKNOWN);
    CHECK_EQ(MPK_STAME.on_midi(&s, MIDI_PORT_CTL, DIM_ON, 3, T0, raw, PNL_MAX_OUT), 1);
    CHECK_EQ(s.bank, MPK_BANK_A);
    CHECK_EQ(MPK_STAME.on_midi(&s, MIDI_PORT_CTL, KEY_ON, 3, T0, raw, PNL_MAX_OUT), 2);
    CHECK(raw[0].type == PNL_CHORD_UP && raw[0].a == CHB_DIM);        /* prima l'accordo appeso */
    CHECK(raw[1].type == PNL_ENC_DOWN && raw[1].a == ENC_KEY);
    CHECK_EQ(s.bank, MPK_BANK_B);

    /* tocco di B1 = premere Key */
    reset();
    mpk("99 2C 7F 89 2C 00");
    CHECK_EQ(count(G_PRESS, ENC_KEY), 1);

    /* VM-30, se il Note Off porta la nota del banco nuovo: Dim tenuto, BANK, rilascio del pad =
     * Note Off 48 (B5, mai premuto). L'accordo non resta appeso. */
    reset();
    mpk("99 28 7F");
    clear();
    mpk("89 30 00");
    CHECK(only(PNL_CHORD_UP, CHB_DIM, 0));
    CHECK_EQ(H.mpk.bank, MPK_BANK_B);

    /* al contrario: B1 tenuto, poi un pad del banco A. [D] Il rilascio è sintetico: niente G_PRESS */
    clear();
    mpk("99 2C 7F 99 24 7F");
    CHECK_EQ(count(G_PRESS, ENC_KEY), 0);
    CHECK_EQ(count(G_RELEASE, ENC_KEY), 1);
    CHECK_EQ(count(PNL_CHORD_DOWN, CHB_6), 1);
    CHECK_EQ(H.mpk.bank, MPK_BANK_A);

    /* anche il PUSH di B8: Key selezionato, poi un pad del banco A */
    clear();
    mpk("99 33 7F B0 49 01 99 25 7F");
    CHECK_EQ(count(G_RELEASE, ENC_KEY), 1);
    CHECK_EQ(count(G_PRESS, ENC_KEY), 0);
    CHECK_EQ(H.mpk.push, MPK_PUSH_IDLE);
}

/* MIDI-084: macchina a stati del PUSH, con B8 e con X della Flip; T-MIDI-11 */
static void t_push(void)
{
    /* T-MIDI-11: B8 giù, K4 +1, B8 su entro 1 s */
    reset();
    mpk("99 33 7F B0 49 01");
    wait_us(300000);
    mpk("89 33 00");
    CHECK_EQ(count(G_PRESS, ENC_KEY), 1);
    CHECK_EQ(count(G_TURN, ENC_KEY) + count(G_PRESS_TURN, ENC_KEY), 0);

    /* tocco e rotazione della stessa manopola = premere e ruotare; tremolio entro 150 ms scartato */
    reset();
    mpk("99 33 7F B0 49 01");
    wait_us(100000);
    mpk("B0 49 02");
    CHECK_EQ(NEV, 0);
    wait_us(60000);
    mpk("B0 49 02");
    CHECK(only(G_PRESS_TURN, ENC_KEY, 1));
    clear();
    mpk("89 33 00");
    CHECK_EQ(count(G_PRESS, ENC_KEY), 0);
    CHECK_EQ(count(G_RELEASE, ENC_KEY), 1);

    /* un'altra manopola con il PUSH tenuto ruota normalmente */
    reset();
    mpk("99 33 7F B0 49 01 B0 46 02");
    CHECK(only(G_TURN, ENC_SOUND, 1));

    /* B8 + tocco a K1, tenuto 1 s = tenere Sound */
    reset();
    mpk("99 33 7F B0 46 7F");
    wait_us(GEST_T_HOLD_US);
    CHECK(only(G_HOLD, ENC_SOUND, 0));
    clear();
    mpk("89 33 00");
    CHECK_EQ(count(G_PRESS, ENC_SOUND), 0);
    CHECK_EQ(count(G_RELEASE, ENC_SOUND), 1);

    /* X della Flip come B8; con B8 e X tenuti insieme conta l'ultimo rilascio */
    reset();
    pad(PAD_X, 1);
    mpk("B0 49 01");
    pad(PAD_X, 0);
    CHECK_EQ(count(G_PRESS, ENC_KEY), 1);
    reset();
    mpk("99 33 7F");
    pad(PAD_X, 1);
    mpk("B0 49 01 89 33 00");
    CHECK_EQ(NEV, 0);
    pad(PAD_X, 0);
    CHECK_EQ(count(G_PRESS, ENC_KEY), 1);

    /* PUSH + Stop = Panic, senza Loop Stop né Clear */
    reset();
    mpk("B0 75 00 99 33 7F B0 75 7F");
    wait_us(1500000);
    CHECK_EQ(count(PNL_MACRO, MACRO_PANIC), 1);
    CHECK_EQ(count(PNL_MACRO, MACRO_LOOP_STOP), 0);
    CHECK_EQ(count(PNL_MACRO, MACRO_LOOP_CLEAR), 0);
}

/* MIDI-081: complemento a due, step 2 per K1–K6 e 1 per K7–K8, accelerazione sommata */
static void t_manopole(void)
{
    reset();
    mpk("B0 4C 01");
    CHECK(only(G_TURN, ENC_BPM, 1));
    clear();
    mpk("B0 4D 7E");
    CHECK(only(G_TURN, ENC_VOLUME, -2));
    clear();
    mpk("B0 46 7F B0 46 7F");
    CHECK(only(G_TURN, ENC_SOUND, -1));
    clear();
    mpk("B0 47 05");                                          /* 5 unità: 2 scatti, 1 resta */
    CHECK(only(G_TURN, ENC_PERFORM, 2));
    clear();
    mpk("B0 47 01");
    CHECK(only(G_TURN, ENC_PERFORM, 1));
    clear();
    mpk("B0 48 00 B0 48 01 B0 48 7F");                        /* 0 non muove; +1 e −1 si annullano */
    CHECK_EQ(NEV, 0);
    CHECK(strcmp(mpk_profile_name(&H.mpk), "mpk_stame") == 0);
}

/* MIDI-088, T-MIDI-14: programma di fabbrica riconosciuto mentre si suona */
static void t_fabbrica(void)
{
    reset();
    mpk("B0 46 28");                                          /* 40: Absolute, solo riferimento */
    CHECK_EQ(NEV, 0);
    CHECK(strcmp(mpk_profile_name(&H.mpk), "mpk_fabbrica") == 0);
    mpk("B0 46 29 B0 46 2A B0 46 2B B0 46 2C");               /* fino a 44 */
    CHECK_EQ(sum_b(G_TURN, ENC_SOUND), 2);
    CHECK_EQ(count(G_TURN, ENC_SOUND), 2);

    /* joystick di fabbrica: CC 12 e CC 2 a 127 in entrambi i versi, nessun evento */
    clear();
    mpk("B0 0C 7F B0 0C 00 B0 02 7F B0 02 00");
    CHECK_EQ(NEV, 0);

    /* [D] CC 13 o CC 3 = joystick di STAME: si torna a mpk_stame, manopole di nuovo Relative */
    mpk("B0 0D 00");
    CHECK(strcmp(mpk_profile_name(&H.mpk), "mpk_stame") == 0);
    mpk("B0 46 01 B0 46 01");
    CHECK(only(G_TURN, ENC_SOUND, 1));
}

/* MIDI-083: senza rilascio (Trpt = On) finché non arriva uno 0, poi la mappa completa */
static void t_trasporto(void)
{
    reset();
    mpk("B0 77 7F");                                          /* Rec: pressione e rilascio insieme */
    CHECK_EQ(count(G_PRESS, ENC_LOOP), 1);
    CHECK_EQ(count(G_RELEASE, ENC_LOOP), 1);
    clear();
    mpk("B0 76 7F");                                          /* Play */
    CHECK_EQ(count(G_PRESS, ENC_BPM), 1);
    clear();
    mpk("B0 75 7F");                                          /* Stop: solo Loop Stop, niente Clear */
    wait_us(1500000);
    CHECK(only(PNL_MACRO, MACRO_LOOP_STOP, 0));

    /* dal primo 0: pressione e rilascio separati, quindi anche tenere */
    clear();
    mpk("B0 75 00 B0 77 7F");
    CHECK_EQ(NEV, 0);
    mpk("B0 77 00");
    CHECK_EQ(count(G_PRESS, ENC_LOOP), 1);
    clear();
    mpk("B0 77 7F");
    wait_us(GEST_T_HOLD2_US);
    CHECK_EQ(count(G_HOLD, ENC_LOOP), 1);
    CHECK_EQ(count(G_HOLD_LONG, ENC_LOOP), 1);
    mpk("B0 77 00");
    CHECK_EQ(count(G_PRESS, ENC_LOOP), 0);

    /* Stop tenuto 1 s: Loop Stop, poi Clear una volta; rilasciato prima: niente Clear */
    clear();
    mpk("B0 75 7F");
    wait_us(990000);
    CHECK(only(PNL_MACRO, MACRO_LOOP_STOP, 0));
    wait_us(10000);
    CHECK_EQ(count(PNL_MACRO, MACRO_LOOP_CLEAR), 1);
    wait_us(1000000);
    mpk("B0 75 00");
    CHECK_EQ(count(PNL_MACRO, MACRO_LOOP_CLEAR), 1);
    clear();
    mpk("B0 75 7F");
    wait_us(500000);
    mpk("B0 75 00");
    wait_us(1000000);
    CHECK(only(PNL_MACRO, MACRO_LOOP_STOP, 0));

    /* « » ruotano l'encoder con il fuoco, alla pressione */
    clear();
    mpk("B0 73 7F B0 73 00 B0 74 7F B0 74 00");
    CHECK_EQ(NEV, 2);
    CHECK(EV[0].type == G_TURN && EV[0].a == gest_target(&H.gest) && EV[0].b == -1);
    CHECK(EV[1].type == G_TURN && EV[1].a == gest_target(&H.gest) && EV[1].b == 1);
}

/* MIDI-082, MIDI-105: soglie 100/60, ripetizione di su e giù, destra = conferma, sinistra = Back */
static void t_joystick(void)
{
    reset();
    mpk("B0 03 7F");                                          /* su: primo passo all'attivazione */
    CHECK(only(G_TURN, ENC_SOUND, 1));
    wait_us(390000);
    CHECK_EQ(NEV, 1);
    wait_us(610000);                                          /* ripetizioni a 400, 600, 800, 1000 ms */
    CHECK_EQ(count(G_TURN, ENC_SOUND), 5);
    mpk("B0 03 46");                                          /* 70: sopra la soglia di riarmo */
    wait_us(200000);
    CHECK_EQ(count(G_TURN, ENC_SOUND), 6);
    mpk("B0 03 3C");                                          /* 60: rilasciato */
    wait_us(1000000);
    CHECK_EQ(count(G_TURN, ENC_SOUND), 6);
    clear();
    mpk("B0 03 63 B0 03 64");                                 /* 99 non basta, 100 sì */
    CHECK(only(G_TURN, ENC_SOUND, 1));
    mpk("B0 03 00");

    clear();
    mpk("B0 02 7F B0 02 00");                                 /* giù */
    CHECK(only(G_TURN, ENC_SOUND, -1));
    clear();
    mpk("B0 0D 7F B0 0D 00");                                 /* destra: pressione dell'encoder con il fuoco */
    CHECK_EQ(count(G_PRESS, ENC_SOUND), 1);
    CHECK_EQ(gest_target(&H.gest), ENC_SOUND);
    clear();
    mpk("B0 0C 7F B0 0C 00");                                 /* sinistra: Back */
    CHECK(only(PNL_BACK, 0, 0));

    /* lista aperta: su = voce precedente; « » non portano il flag */
    clear();
    gest_set_owner(&H.gest, ENC_SOUND, true);
    mpk("B0 03 7F B0 03 00 B0 74 7F B0 74 00");
    CHECK_EQ(NEV, 2);
    CHECK(EV[0].type == G_TURN && EV[0].b == -1);
    CHECK(EV[1].type == G_TURN && EV[1].b == 1);
    /* overlay senza lista: su = valore più alto */
    clear();
    gest_set_owner(&H.gest, ENC_VOLUME, false);
    mpk("B0 03 7F B0 03 00");
    CHECK(only(G_TURN, ENC_VOLUME, 1));
}

/* MIDI-072…075: identità, porta, canali, real time e SysEx diversi dall'Identity Reply */
static void t_filtri(void)
{
    reset();
    mpk("F0 7E 7F 06 02 47 54 00 19 00 01 01 03 F7");
    CHECK_EQ(H.mpk.identity, MPK_ID_PLUS);
    CHECK(H.mpk.fw[0] == 1 && H.mpk.fw[1] == 1 && H.mpk.fw[2] == 3);
    mpk("F0 7E 7F 06 02 47 54 00 31 00 01 00 00 F7");
    CHECK_EQ(H.mpk.identity, MPK_ID_OTHER);
    mpk("F0 47 7F 19 66 00 01 00 F7 F8 FA FC FE FF");         /* SysEx di programma e real time */
    mpk("92 3C 64 9A 3C 64 B2 46 01 BA 49 01 C0 05");         /* sequencer (ch3, ch11), Program Change */
    CHECK_EQ(NEV, 0);

    /* porta 2: va all'ingresso MIDI, non al profilo */
    midi_msg_t m;
    memset(&m, 0, sizeof m);
    m.port = MIDI_PORT_DIN; m.n = 3; m.valid = 1;
    m.b[0] = 0x90; m.b[1] = 0x3C; m.b[2] = 0x64;
    CHECK_EQ(inp_midi(&H, &m, EV, MAXEV), 0);

    /* bend, mod e sustain passano */
    mpk("E0 00 40 E0 7F 7F E0 00 00 B0 01 40 B0 40 7F B0 40 00");
    CHECK_EQ(NEV, 6);
    CHECK(EV[0].type == PNL_BEND && EV[0].b == 0);
    CHECK(EV[1].type == PNL_BEND && EV[1].b == 8191);
    CHECK(EV[2].type == PNL_BEND && EV[2].b == -8192);
    CHECK(EV[3].type == PNL_MOD && EV[3].b == 64);
    CHECK(EV[4].type == PNL_SUSTAIN && EV[4].b == 1);
    CHECK(EV[5].type == PNL_SUSTAIN && EV[5].b == 0);
}

/* ----------------------------------------------------------- riconoscitore */

/* MIDI-103: premere, tenere 1 s, Loop tenuto 2 s, premere e ruotare; tenuto ignora le rotazioni */
static void t_gesti(void)
{
    reset();
    pad(MPAD_T1, 1);
    wait_us(GEST_T_HOLD_US - PNL_TICK_US);
    CHECK_EQ(NEV, 0);
    wait_us(PNL_TICK_US);
    CHECK(only(G_HOLD, ENC_SOUND, 0));
    CHECK_EQ(EV[0].t_us, T0 + GEST_T_HOLD_US);
    CHECK_EQ(EV[0].src, SRC_MACROPAD);
    clear();
    mpk("B0 46 02");                                          /* tenuto: la rotazione si ignora */
    pad(MPAD_T1, 0);
    CHECK(only(G_RELEASE, ENC_SOUND, 0));

    clear();
    tap(MPAD_T2);
    CHECK_EQ(NEV, 2);
    CHECK(EV[0].type == G_PRESS && EV[0].a == ENC_PERFORM && EV[0].src == SRC_MACROPAD);
    CHECK(EV[1].type == G_RELEASE && EV[1].a == ENC_PERFORM);

    /* Loop: G_HOLD a 1 s e G_HOLD_LONG a 2 s, una volta sola; gli altri non hanno G_HOLD_LONG */
    clear();
    pad(MPAD_T6, 1);
    wait_us(3000000);
    pad(MPAD_T6, 0);
    CHECK_EQ(count(G_HOLD, ENC_LOOP), 1);
    CHECK_EQ(count(G_HOLD_LONG, ENC_LOOP), 1);
    CHECK_EQ(count(G_PRESS, ENC_LOOP), 0);
    CHECK_EQ(count(G_RELEASE, ENC_LOOP), 1);
    clear();
    pad(MPAD_T7, 1);
    wait_us(3000000);
    pad(MPAD_T7, 0);
    CHECK_EQ(count(G_HOLD, ENC_BPM), 1);
    CHECK_EQ(count(G_HOLD_LONG, ENC_BPM), 0);

    /* premere e ruotare: né G_HOLD né G_PRESS, anche oltre 1 s */
    clear();
    pad(MPAD_T1, 1);
    mpk("B0 46 02 B0 46 7E");
    wait_us(1500000);
    pad(MPAD_T1, 0);
    CHECK_EQ(NEV, 3);
    CHECK(EV[0].type == G_PRESS_TURN && EV[0].a == ENC_SOUND && EV[0].b == 1);
    CHECK(EV[1].type == G_PRESS_TURN && EV[1].a == ENC_SOUND && EV[1].b == -1);
    CHECK(EV[2].type == G_RELEASE && EV[2].a == ENC_SOUND);
}

/* MIDI-104, MIDI-105, MIDI-092: fuoco del pannello, owner, ENC_FOCUS premuto con A */
static void t_fuoco(void)
{
    reset();
    CHECK_EQ(gest_target(&H.gest), ENC_SOUND);                /* all'avvio il fuoco è su Sound */
    tap(PAD_RIGHT);
    CHECK(only(G_TURN, ENC_SOUND, 1));
    clear();
    tap(PAD_R1);                                              /* sposta il fuoco, nessun evento */
    CHECK_EQ(NEV, 0);
    CHECK_EQ(gest_target(&H.gest), ENC_PERFORM);
    tap(PAD_L1);
    tap(PAD_L1);                                              /* in giro: Sound, poi Bass Voicing */
    CHECK_EQ(gest_target(&H.gest), ENC_BASS_VOICING);
    tap(PAD_LEFT);
    CHECK(only(G_TURN, ENC_BASS_VOICING, -1));

    /* la pressione di un encoder porta il fuoco, da qualunque sorgente */
    clear();
    tap(MPAD_T4);
    CHECK_EQ(gest_target(&H.gest), ENC_KEY);
    clear();
    tap(MPAD_M2_CW);
    CHECK(only(G_TURN, ENC_KEY, 1));

    /* l'owner vince sul fuoco; con una lista su e giù della croce sono invertiti */
    gest_set_owner(&H.gest, ENC_OPTIONS, true);
    clear();
    tap(MPAD_M2_CW);
    tap(PAD_UP);
    tap(PAD_DOWN);
    CHECK_EQ(NEV, 3);
    CHECK(EV[0].a == ENC_OPTIONS && EV[0].b == 1);
    CHECK(EV[1].a == ENC_OPTIONS && EV[1].b == -1);
    CHECK(EV[2].a == ENC_OPTIONS && EV[2].b == 1);
    gest_set_owner(&H.gest, ENC_COUNT, false);
    clear();
    tap(PAD_UP);
    CHECK(only(G_TURN, ENC_KEY, 1));

    /* A preme l'encoder con il fuoco senza spostarlo; A tenuto + croce = premere e ruotare */
    clear();
    tap(PAD_A);
    CHECK_EQ(count(G_PRESS, ENC_KEY), 1);
    clear();
    pad(PAD_A, 1);
    tap(PAD_RIGHT);
    pad(PAD_A, 0);
    CHECK_EQ(NEV, 2);
    CHECK(EV[0].type == G_PRESS_TURN && EV[0].a == ENC_KEY && EV[0].b == 1);
    CHECK(EV[1].type == G_RELEASE && EV[1].a == ENC_KEY);
    /* il rilascio di A va all'encoder premuto, anche se intanto si è aperta una lista */
    clear();
    pad(PAD_A, 1);
    gest_set_owner(&H.gest, ENC_SOUND, true);
    pad(PAD_A, 0);
    CHECK_EQ(count(G_PRESS, ENC_KEY), 1);
    gest_set_owner(&H.gest, ENC_COUNT, false);
}

/* MIDI-102: stato per sorgente; SRC_LOST come rete di sicurezza */
static void t_unione(void)
{
    gest_t g;
    pnl_event_t o[16];
    gest_init(&g);

    pnl_event_t e = { PNL_KEY_DOWN, SRC_MPK, 3, 90, T0 };
    CHECK_EQ(gest_feed(&g, &e, o, 16), 1);
    e.src = SRC_FLIP;
    CHECK_EQ(gest_feed(&g, &e, o, 16), 0);                    /* già tenuto dalla MPK */
    e.type = PNL_KEY_UP; e.src = SRC_MPK;
    CHECK_EQ(gest_feed(&g, &e, o, 16), 0);                    /* lo tiene ancora l'altra sorgente */
    e.src = SRC_FLIP;
    CHECK_EQ(gest_feed(&g, &e, o, 16), 1);
    CHECK(o[0].type == PNL_KEY_UP && o[0].a == 3);

    pnl_event_t c = { PNL_CHORD_DOWN, SRC_MACROPAD, CHB_SUS, 0, T0 };
    CHECK_EQ(gest_feed(&g, &c, o, 16), 1);
    c.src = SRC_MPK;
    CHECK_EQ(gest_feed(&g, &c, o, 16), 0);
    c.type = PNL_CHORD_UP;
    CHECK_EQ(gest_feed(&g, &c, o, 16), 0);
    c.src = SRC_MACROPAD;
    CHECK_EQ(gest_feed(&g, &c, o, 16), 1);

    /* encoder: l'ENC_UP di una sorgente non rilascia quello tenuto da un'altra */
    pnl_event_t d = { PNL_ENC_DOWN, SRC_MPK, ENC_FX, 0, T0 };
    gest_feed(&g, &d, o, 16);
    d.src = SRC_MACROPAD;
    gest_feed(&g, &d, o, 16);
    d.type = PNL_ENC_UP; d.src = SRC_FLIP;                    /* mai premuto dalla Flip: ignorato */
    CHECK_EQ(gest_feed(&g, &d, o, 16), 0);
    d.src = SRC_MPK;
    CHECK_EQ(gest_feed(&g, &d, o, 16), 0);
    CHECK(gest_held(&g, ENC_FX));
    d.src = SRC_MACROPAD;
    CHECK_EQ(gest_feed(&g, &d, o, 16), 2);
    CHECK(o[0].type == G_PRESS && o[0].a == ENC_FX);

    /* sorgente persa senza i rilasci del profilo: li fa il riconoscitore, senza G_PRESS */
    d.type = PNL_ENC_DOWN; d.src = SRC_MPK;
    gest_feed(&g, &d, o, 16);
    e.type = PNL_KEY_DOWN; e.src = SRC_MPK; e.a = 7;
    gest_feed(&g, &e, o, 16);
    pnl_event_t l = { PNL_SRC_LOST, SRC_MPK, SRC_MPK, 0, T0 };
    CHECK_EQ(gest_feed(&g, &l, o, 16), 3);
    CHECK(o[0].type == G_RELEASE && o[0].a == ENC_FX);
    CHECK(o[1].type == PNL_KEY_UP && o[1].a == 7);
    CHECK(o[2].type == PNL_SRC_LOST && o[2].a == SRC_MPK);
    CHECK(!gest_held(&g, ENC_FX));
    CHECK_EQ(g.dropped, 0);
}

/* ------------------------------------------------------- Flip e macro pad */

/* MIDI-092: schema a fuoco della Flip */
static void t_flip(void)
{
    reset();
    tap(PAD_SELECT);
    CHECK_EQ(count(G_PRESS, ENC_OPTIONS), 1);
    clear();
    tap(PAD_START);
    CHECK_EQ(count(G_PRESS, ENC_BPM), 1);
    clear();
    tap(PAD_B);
    CHECK(only(PNL_BACK, 0, 0));
    clear();
    tap(PAD_MENU);
    CHECK(only(PNL_MACRO, MACRO_SYSTEM_MENU, 0));
    clear();
    pad(PAD_Y, 1);
    CHECK(gest_held(&H.gest, ENC_BASS_VOICING));
    pad(PAD_Y, 2);                                            /* ripetizione del kernel: ignorata */
    pad(PAD_Y, 0);
    CHECK(!gest_held(&H.gest, ENC_BASS_VOICING));
    CHECK_EQ(count(G_PRESS, ENC_BASS_VOICING), 1);

    /* tasti liberi, assi e X senza manopole: nessun evento */
    clear();
    tap(PAD_X);
    tap(PAD_L3);
    tap(PAD_R3);
    pad(PAD_L2, 255);
    pad(PAD_L2, 0);
    pad(PAD_LSTICK_X, 32767);
    pad(PAD_LSTICK_X, 0);
    CHECK_EQ(NEV, 0);

    /* ripetizione della croce come MIDI-082: 0, 400 e 600 ms, poi si ferma al rilascio */
    uint8_t tgt = gest_target(&H.gest);
    pad(PAD_UP, 1);
    wait_us(650000);
    pad(PAD_UP, 0);
    wait_us(1000000);
    CHECK_EQ(count(G_TURN, tgt), 3);
}

/* MIDI-120…126, T-MIDI-16…21: macro pad BRIMFORD */
static void t_macro_pad(void)
{
    mpad_state_t s;
    pnl_event_t raw[PNL_MAX_OUT];

    /* T-MIDI-16: T4 tenuto + K4 della MPK = premere e ruotare Key */
    reset();
    pad(MPAD_T4, 1);
    mpk("B0 49 02");
    pad(MPAD_T4, 0);
    CHECK_EQ(count(G_PRESS_TURN, ENC_KEY), 1);
    CHECK_EQ(sum_b(G_PRESS_TURN, ENC_KEY), 1);
    CHECK_EQ(count(G_PRESS, ENC_KEY), 0);

    /* T-MIDI-17: T12 tenuto 0,5 s: niente; tenuto 1,2 s: un solo Panic, a 1 s */
    clear();
    pad(MPAD_T12, 1);
    wait_us(500000);
    pad(MPAD_T12, 0);
    CHECK_EQ(NEV, 0);
    uint32_t t1 = NOW;
    pad(MPAD_T12, 1);
    wait_us(1200000);
    pad(MPAD_T12, 0);
    CHECK(only(PNL_MACRO, MACRO_PANIC, 0));
    CHECK_EQ(EV[0].t_us, t1 + MPAD_PANIC_HOLD_US);
    /* tenuto 3 s: dopo il Panic anche il Reset, una volta sola (MIDI-126) */
    clear();
    t1 = NOW;
    pad(MPAD_T12, 1);
    wait_us(3500000);
    pad(MPAD_T12, 0);
    CHECK_EQ(NEV, 2);
    CHECK(EV[0].type == PNL_MACRO && EV[0].a == MACRO_PANIC);
    CHECK(EV[1].type == PNL_MACRO && EV[1].a == MACRO_RESET && EV[1].t_us == t1 + MPAD_RESET_HOLD_US);

    /* T-MIDI-18: m1 premuta (Bass Voicing tenuto) + tocco di T6: premere Loop col modificatore */
    clear();
    pad(MPAD_M1_PUSH, 1);
    tap(MPAD_T6);
    CHECK_EQ(count(G_PRESS, ENC_LOOP), 1);
    CHECK(gest_held(&H.gest, ENC_BASS_VOICING));
    pad(MPAD_M1_PUSH, 0);
    CHECK(!gest_held(&H.gest, ENC_BASS_VOICING));

    /* T-MIDI-19: lista dei suoni aperta, m2 orario = voce successiva, antiorario = precedente */
    clear();
    gest_set_owner(&H.gest, ENC_SOUND, true);
    tap(MPAD_M2_CW);
    tap(MPAD_M2_CCW);
    CHECK_EQ(NEV, 2);
    CHECK(EV[0].type == G_TURN && EV[0].a == ENC_SOUND && EV[0].b == 1);
    CHECK(EV[1].type == G_TURN && EV[1].a == ENC_SOUND && EV[1].b == -1);
    gest_set_owner(&H.gest, ENC_COUNT, false);
    PAD_BRIMFORD.reset(&s);
    CHECK_EQ(PAD_BRIMFORD.on_pad(&s, MPAD_M2_CW, 1, T0, raw, PNL_MAX_OUT), 1);
    CHECK(raw[0].type == PNL_ENC_TURN && raw[0].a == ENC_FOCUS && raw[0].b == 1);   /* senza PNL_F_VERTICAL */
    CHECK_EQ(PAD_BRIMFORD.on_pad(&s, MPAD_M2_CW, 0, T0, raw, PNL_MAX_OUT), 0);      /* il rilascio non conta */

    /* MIDI-131: T13 = Lock delle manopole, a scatto come il Caps Lock. Acceso, M, m1 e m2 sono Sound,
     * Perform e Key, con premere e ruotare; una pressione cominciata prima del cambio finisce sul suo encoder */
    clear();
    tap(MPAD_T13);
    CHECK(only(PNL_MACRO, MACRO_KNOB_LOCK, 1));
    clear();
    tap(MPAD_M_CW);
    tap(MPAD_M1_CCW);
    CHECK_EQ(NEV, 2);
    CHECK(EV[0].type == G_TURN && EV[0].a == ENC_SOUND && EV[0].b == 1);
    CHECK(EV[1].type == G_TURN && EV[1].a == ENC_PERFORM && EV[1].b == -1);
    clear();
    pad(MPAD_M2_PUSH, 1);                                     /* m2 premuta e girata = transpose */
    tap(MPAD_M2_CW);
    pad(MPAD_M2_PUSH, 0);
    CHECK_EQ(count(G_PRESS_TURN, ENC_KEY), 1);
    CHECK_EQ(count(G_PRESS, ENC_KEY), 0);
    clear();
    pad(MPAD_M_PUSH, 1);
    tap(MPAD_T13);                                            /* spento con M premuta: il rilascio resta a Sound */
    pad(MPAD_M_PUSH, 0);
    CHECK_EQ(count(PNL_MACRO, MACRO_KNOB_LOCK), 1);
    CHECK_EQ(sum_b(PNL_MACRO, MACRO_KNOB_LOCK), 0);
    CHECK_EQ(count(G_PRESS, ENC_SOUND), 1);
    CHECK_EQ(count(G_PRESS, ENC_CHORD_VOICING), 0);
    clear();
    tap(MPAD_M_CW);
    CHECK(only(G_TURN, ENC_CHORD_VOICING, 1));
    PAD_BRIMFORD.reset(&s);                                   /* scollegato con il Lock acceso: si spegne prima di SRC_LOST */
    PAD_BRIMFORD.on_pad(&s, MPAD_T13, 1, T0, raw, PNL_MAX_OUT);
    PAD_BRIMFORD.on_pad(&s, MPAD_T13, 0, T0, raw, PNL_MAX_OUT);
    CHECK_EQ(PAD_BRIMFORD.on_lost(&s, T0, raw, PNL_MAX_OUT), 2);
    CHECK(raw[0].type == PNL_MACRO && raw[0].a == MACRO_KNOB_LOCK && raw[0].b == 0);
    CHECK(raw[1].type == PNL_SRC_LOST);

    /* MIDI-132: T14 vista (Geek Out e ritorno), T15 pagina dei comandi; solo alla pressione, anche tenuti */
    clear();
    tap(MPAD_T14);
    CHECK(only(PNL_MACRO, MACRO_VIEW_TOGGLE, 0));
    clear();
    pad(MPAD_T15, 1);
    wait_us(1200000);
    pad(MPAD_T15, 0);
    CHECK(only(PNL_MACRO, MACRO_CONTROLS_PAGE, 0));

    /* T-MIDI-20: scollegato con T1 tenuto: rilascio sintetico, poi SRC_LOST; niente G_HOLD dopo */
    PAD_BRIMFORD.reset(&s);
    PAD_BRIMFORD.on_pad(&s, MPAD_T1, 1, T0, raw, PNL_MAX_OUT);
    CHECK_EQ(PAD_BRIMFORD.on_lost(&s, T0, raw, PNL_MAX_OUT), 2);
    CHECK(raw[0].type == PNL_ENC_UP && raw[0].a == ENC_SOUND && raw[0].b == PNL_B_SYNTH);
    CHECK(raw[1].type == PNL_SRC_LOST && raw[1].a == SRC_MACROPAD);
    clear();
    pad(MPAD_T1, 1);
    lost(SRC_MACROPAD);
    wait_us(1500000);
    CHECK_EQ(NEV, 2);
    CHECK(EV[0].type == G_RELEASE && EV[0].a == ENC_SOUND);
    CHECK(EV[1].type == PNL_SRC_LOST && EV[1].a == SRC_MACROPAD);

    /* T-MIDI-21: T5 con la ripetizione automatica (1, 2, 2, 2, 0) */
    static const int32_t V[5] = { 1, 2, 2, 2, 0 };
    int downs = 0, ups = 0;
    PAD_BRIMFORD.reset(&s);
    for (int i = 0; i < 5; i++) {
        int n = PAD_BRIMFORD.on_pad(&s, MPAD_T5, V[i], T0, raw, PNL_MAX_OUT);
        for (int j = 0; j < n; j++) {
            downs += raw[j].type == PNL_ENC_DOWN && raw[j].a == ENC_BASS;
            ups += raw[j].type == PNL_ENC_UP && raw[j].a == ENC_BASS;
        }
    }
    CHECK_EQ(downs, 1);
    CHECK_EQ(ups, 1);
    reset();
    for (int i = 0; i < 5; i++) pad(MPAD_T5, V[i]);
    CHECK_EQ(count(G_PRESS, ENC_BASS), 1);
    CHECK_EQ(count(G_RELEASE, ENC_BASS), 1);

    /* il resto della mappa */
    clear();
    tap(MPAD_T9);
    tap(MPAD_T10);
    tap(MPAD_T11);
    tap(MPAD_M_CW);
    tap(MPAD_M1_CCW);
    tap(MPAD_M_PUSH);
    tap(MPAD_M2_PUSH);
    CHECK_EQ(count(G_PRESS, ENC_OPTIONS), 1);
    CHECK_EQ(count(PNL_BACK, 0), 1);
    CHECK_EQ(count(PNL_MACRO, MACRO_SYSTEM_MENU), 1);
    CHECK_EQ(sum_b(G_TURN, ENC_CHORD_VOICING), 1);
    CHECK_EQ(sum_b(G_TURN, ENC_BASS_VOICING), -1);
    CHECK_EQ(count(G_PRESS, ENC_CHORD_VOICING), 2);           /* M, poi m2 con il fuoco su Chord Voicing */
}

/* ----------------------------------------------------------- scollegamento */

/* MIDI-112: MPK scollegata con accordo, tasto accordo, Rec e sustain tenuti (T-MIDI-13, prima
 * parte: i rilasci sintetici; il panic sul DIN al ricollegamento arriva con midi_out) */
static void t_scollegamento(void)
{
    reset();
    mpk("B0 77 00");                                          /* trasporto con il rilascio */
    mpk("90 30 64 90 34 64 90 37 64 99 2A 7F B0 77 7F B0 40 7F E0 00 50");
    clear();
    lost(SRC_MPK);
    CHECK_EQ(count(PNL_KEY_UP, 0) + count(PNL_KEY_UP, 4) + count(PNL_KEY_UP, 7), 3);
    CHECK_EQ(count(PNL_CHORD_UP, CHB_MAJ), 1);
    CHECK_EQ(count(G_RELEASE, ENC_LOOP), 1);
    CHECK_EQ(count(G_PRESS, ENC_LOOP), 0);                    /* lo scollegamento non è un tocco di Rec */
    int i = find(PNL_SUSTAIN, 0), j = find(PNL_BEND, 0), k = find(PNL_SRC_LOST, SRC_MPK);
    CHECK(i >= 0 && j > i && k > j && k == NEV - 1);
    CHECK(i >= 0 && j >= 0 && EV[i].b == 0 && EV[j].b == 0);
    clear();
    wait_us(2500000);
    CHECK_EQ(NEV, 0);

    /* Flip persa con X tenuto e Key selezionato: rilascio sintetico, poi K4 ruota di nuovo */
    reset();
    pad(PAD_X, 1);
    mpk("B0 49 01");
    lost(SRC_FLIP);
    CHECK_EQ(count(G_RELEASE, ENC_KEY), 1);
    CHECK_EQ(count(G_PRESS, ENC_KEY), 0);
    CHECK_EQ(count(PNL_SRC_LOST, SRC_FLIP), 1);
    connected(SRC_FLIP);
    clear();
    mpk("B0 49 02");
    CHECK(only(G_TURN, ENC_KEY, 1));

    /* MPK ricollegata con X già tenuto: il PUSH è subito armato */
    reset();
    pad(PAD_X, 1);
    lost(SRC_MPK);
    connected(SRC_MPK);
    clear();
    mpk("B0 49 01");
    CHECK_EQ(NEV, 0);
    pad(PAD_X, 0);
    CHECK_EQ(count(G_PRESS, ENC_KEY), 1);
}

/* T-MIDI-15: nessun nome esposto comincia con "orchid", in nessuna grafia */
static bool starts_orchid(const char *s)
{
    while (*s == ' ') s++;
    for (int i = 0; i < 6; i++) {
        char c = s[i];
        if (c >= 'A' && c <= 'Z') c = (char)(c - 'A' + 'a');
        if (c != "orchid"[i]) return false;
    }
    return true;
}

static void t_nomi(void)
{
    mpk_state_t s;
    MPK_STAME.reset(&s);
    CHECK(starts_orchid(" ORCHID 1") && starts_orchid("Orchid"));
    CHECK(!starts_orchid(MPK_STAME.name));
    CHECK(!starts_orchid(FLIP_TASTI.name));
    CHECK(!starts_orchid(PAD_BRIMFORD.name));
    CHECK(!starts_orchid(mpk_profile_name(&s)));
    s.factory = 1;
    CHECK(!starts_orchid(mpk_profile_name(&s)));
}

/* MPK mini IV nel preset DAW (§8.9b): i messaggi sono quelli catturati il 15/10/2026 */
static midi_parser_t MP2;

static void mk4_daw(const char *hex)              /* byte della porta 2 (DAW) */
{
    midi_msg_t m[MIDI_PARSE_MAX_OUT];
    for (const char *p = hex; *p; ) {
        while (*p == ' ') p++;
        if (!*p) break;
        int k = midi_parse_byte(&MP2, (uint8_t)hexbyte(&p), NOW, m);
        for (int j = 0; j < k; j++) NEV += inp_midi(&H, &m[j], EV + NEV, MAXEV - NEV);
    }
}

static void t_mk4(void)
{
    reset();
    lost(SRC_MPK);
    inp_set_mpk_model(&H, MPK_MODEL_MK4);
    connected(SRC_MPK);
    midi_parser_init(&MP2, MIDI_PORT_DIN);
    clear();

    /* tasti sulla porta 1: il Do3 (48) è la classe 0 */
    mpk("90 30 77");
    CHECK(only(PNL_KEY_DOWN, 0, 119));
    clear();
    mpk("80 30 00");
    CHECK(only(PNL_KEY_UP, 0, 0));

    /* pad: in alto a sinistra 40 = Dim, in basso a destra 39 = 9; la copia sulla porta 2 si ignora */
    clear();
    mpk("99 28 4A");
    mk4_daw("99 28 4A");
    CHECK(only(PNL_CHORD_DOWN, CHB_DIM, 0));
    clear();
    mpk("A9 28 7F 89 28 00");
    CHECK(only(PNL_CHORD_UP, CHB_DIM, 0));
    clear();
    mpk("99 27 3D");
    CHECK(only(PNL_CHORD_DOWN, CHB_9, 0));
    mpk("89 27 00");

    /* K1 relativa: 12 unità = uno scatto di Sound, in tutti e due i versi */
    clear();
    for (int i = 0; i < 6; i++) mk4_daw("B0 18 02");
    CHECK(only(G_TURN, ENC_SOUND, 1));
    clear();
    for (int i = 0; i < 12; i++) mk4_daw("B0 18 7F");
    CHECK(only(G_TURN, ENC_SOUND, -1));

    /* SHIFT = PUSH: SHIFT + K4 toccata e poi girata = premi e ruota Key; toccata e lasciata = premi Key */
    clear();
    mk4_daw("B0 11 7F");
    mk4_daw("B0 1B 01");
    wait_us(400000);
    for (int i = 0; i < 12; i++) mk4_daw("B0 1B 01");
    mk4_daw("B0 11 00");
    CHECK_EQ(count(G_PRESS_TURN, ENC_KEY), 1);
    CHECK_EQ(count(G_PRESS, ENC_KEY), 0);
    clear();
    mk4_daw("B0 11 7F B0 1B 01 B0 11 00");
    CHECK_EQ(count(G_PRESS, ENC_KEY), 1);

    /* trasporto (solo pressione) */
    clear();
    mk4_daw("B0 4D 7F");
    CHECK_EQ(count(G_PRESS, ENC_LOOP), 1);                        /* REC = Loop */
    clear();
    mk4_daw("B0 4C 7F");
    CHECK_EQ(count(G_PRESS, ENC_BPM), 1);                         /* STOP/PLAY = BPM */
    clear();
    mk4_daw("B0 11 7F B0 4C 7F B0 11 00");
    CHECK(only(PNL_MACRO, MACRO_PANIC, 0));                       /* SHIFT + STOP/PLAY */
    clear();
    mk4_daw("B0 49 7F");
    CHECK(only(PNL_MACRO, MACRO_LOOP_UNDO, 0));
    clear();
    mk4_daw("B0 11 7F B0 49 7F B0 11 00");
    CHECK(only(PNL_MACRO, MACRO_LOOP_CLEAR, 0));                  /* SHIFT + UNDO */
    clear();
    mk4_daw("B0 4E 7F");
    CHECK(only(PNL_MACRO, MACRO_LOOP_OVERDUB, 0));                /* ⊕ */
    clear();
    mk4_daw("B0 4A 7F");
    CHECK(only(PNL_MACRO, MACRO_LOOP_STOP, 0));                   /* LOOP */

    /* − = Back, + = menu della piattaforma */
    clear();
    mk4_daw("B0 50 7F B0 50 00");
    CHECK(only(PNL_BACK, 0, 0));
    clear();
    mk4_daw("B0 51 7F B0 51 00");
    CHECK(only(PNL_MACRO, MACRO_SYSTEM_MENU, 0));

    /* manopola di navigazione con la lista dei suoni aperta: orario = voce successiva */
    clear();
    gest_set_owner(&H.gest, ENC_SOUND, true);
    mk4_daw("B0 0E 01 B0 0E 7F");
    CHECK_EQ(NEV, 2);
    CHECK(EV[0].type == G_TURN && EV[0].a == ENC_SOUND && EV[0].b == 1);
    CHECK(EV[1].type == G_TURN && EV[1].a == ENC_SOUND && EV[1].b == -1);
    gest_set_owner(&H.gest, ENC_COUNT, false);

    /* pitch bend a riposo; scollegamento con un tasto tenuto */
    clear();
    mpk("E0 00 40");
    CHECK(only(PNL_BEND, 0, 0));
    clear();
    mpk("90 3C 40");
    lost(SRC_MPK);
    CHECK_EQ(count(PNL_KEY_UP, 0), 1);
    CHECK_EQ(count(PNL_SRC_LOST, SRC_MPK), 1);
    inp_set_mpk_model(&H, MPK_MODEL_PLUS);
    connected(SRC_MPK);
}

void test_input(void)
{
    t_esempio();
    t_tastiera();
    t_pad_accordi();
    t_banco();
    t_push();
    t_manopole();
    t_fabbrica();
    t_trasporto();
    t_joystick();
    t_filtri();
    t_gesti();
    t_fuoco();
    t_unione();
    t_flip();
    t_macro_pad();
    t_scollegamento();
    t_nomi();
    t_mk4();
    CHECK_EQ(DROPPED + inp_dropped(&H), 0);                   /* nessun evento perso */
}
