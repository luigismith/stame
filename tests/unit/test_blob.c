/* test_blob.c — salvataggi (sezione 50): contenitore con CRC-32 (PLT-065, PLT-068), righe
 * chiave=valore (PLT-066) e opzioni del motore degli accordi (acc_kv). */
#include "test.h"
#include "core/blob.h"
#include "core/kv.h"
#include "core/acc_kv.h"
#include <string.h>

static uint8_t BUF[512];
static acc_state A, B;

/* CRC-32 IEEE 802.3: valore di controllo e calcolo a pezzi */
static void t_crc(void)
{
    CHECK_EQ(blob_crc32(0, "123456789", 9), 0xCBF43926u);
    CHECK_EQ(blob_crc32(blob_crc32(0, "1234", 4), "56789", 5), 0xCBF43926u);
    CHECK_EQ(blob_crc32(0, "", 0), 0u);
}

/* PLT-065: intestazione, campi little-endian, letture oltre la fine */
static void t_blob(void)
{
    blob_w_t w;
    blob_r_t r;
    char abc[3];

    blob_w_begin(&w, BUF, sizeof BUF, BLOB_PRESET, 3);
    blob_w_u8(&w, 0xA5);
    blob_w_u16(&w, 0x1234);
    blob_w_u32(&w, 0xDEADBEEFu);
    blob_w_bytes(&w, "abc", 3);
    size_t n = blob_w_end(&w);
    CHECK_EQ(n, BLOB_OVERHEAD + 10);
    CHECK(memcmp(BUF, "STP1", 4) == 0);
    CHECK(BUF[4] == 3 && BUF[5] == 0);                                    /* versione */
    CHECK(BUF[6] == 10 && BUF[7] == 0 && BUF[8] == 0 && BUF[9] == 0);     /* lunghezza */
    CHECK(BUF[10] == 0xA5 && BUF[11] == 0x34 && BUF[12] == 0x12);
    CHECK(BUF[13] == 0xEF && BUF[14] == 0xBE && BUF[15] == 0xAD && BUF[16] == 0xDE);
    uint32_t crc = blob_crc32(0, BUF, 20);
    CHECK(BUF[20] == (uint8_t)crc && BUF[23] == (uint8_t)(crc >> 24));

    CHECK_EQ(blob_r_open(&r, BUF, n, BLOB_PRESET), BLOB_OK);
    CHECK_EQ(r.version, 3);
    CHECK_EQ(r.n, 10);
    CHECK_EQ(blob_r_u8(&r, 0), 0xA5);
    CHECK_EQ(blob_r_u16(&r, 0), 0x1234);
    CHECK_EQ(blob_r_u32(&r, 0), 0xDEADBEEFu);
    CHECK(blob_r_bytes(&r, abc, 3) && memcmp(abc, "abc", 3) == 0);
    /* oltre la fine: i default, così un blob di una versione vecchia resta leggibile */
    CHECK_EQ(blob_r_u8(&r, 7), 7);
    CHECK_EQ(blob_r_u16(&r, 0xBEEF), 0xBEEF);
    CHECK_EQ(blob_r_u32(&r, 42), 42u);
    CHECK(!blob_r_bytes(&r, abc, 1));

    /* un campo a metà: default, e la lettura finisce lì */
    CHECK_EQ(blob_r_open(&r, BUF, n, BLOB_PRESET), BLOB_OK);
    blob_r_u32(&r, 0);
    blob_r_u32(&r, 0);
    CHECK_EQ(blob_r_u32(&r, 99), 99u);                                    /* restano 2 byte */
    CHECK_EQ(blob_r_u8(&r, 5), 5);

    /* contenuto vuoto */
    blob_w_begin(&w, BUF + 100, BLOB_OVERHEAD, BLOB_SETTINGS, 1);
    CHECK_EQ(blob_w_end(&w), BLOB_OVERHEAD);
    CHECK_EQ(blob_r_open(&r, BUF + 100, BLOB_OVERHEAD, BLOB_SETTINGS), BLOB_OK);
    CHECK_EQ(r.n, 0);
}

/* PLT-068: ogni guasto si riconosce; dopo un errore il lettore dà solo i default */
static void t_blob_errori(void)
{
    blob_w_t w;
    blob_r_t r;

    blob_w_begin(&w, BUF, sizeof BUF, BLOB_PRESET, 3);
    blob_w_u32(&w, 0x01020304u);
    blob_w_u32(&w, 0x05060708u);
    blob_w_u16(&w, 0x090A);
    size_t n = blob_w_end(&w);
    CHECK_EQ(blob_r_open(&r, BUF, n, BLOB_PRESET), BLOB_OK);

    CHECK_EQ(blob_r_open(&r, BUF, n, BLOB_LOOP), BLOB_E_MAGIC);          /* blob di un altro tipo */
    CHECK_EQ(blob_r_open(&r, BUF, n, BLOB_KIND_COUNT), BLOB_E_MAGIC);
    CHECK_EQ(blob_r_u8(&r, 9), 9);
    CHECK_EQ(blob_r_open(&r, BUF, n - 1, BLOB_PRESET), BLOB_E_LENGTH);   /* file troncato */
    CHECK_EQ(blob_r_open(&r, BUF, BLOB_OVERHEAD - 1, BLOB_PRESET), BLOB_E_SHORT);
    BUF[12] ^= 0x01;                                                      /* un bit del contenuto */
    CHECK_EQ(blob_r_open(&r, BUF, n, BLOB_PRESET), BLOB_E_CRC);
    BUF[12] ^= 0x01;
    BUF[n - 1] ^= 0x80;                                                   /* un bit del CRC */
    CHECK_EQ(blob_r_open(&r, BUF, n, BLOB_PRESET), BLOB_E_CRC);
    CHECK(!blob_r_bytes(&r, BUF + 200, 1));
    BUF[n - 1] ^= 0x80;
    BUF[6] = 11;                                                          /* lunghezza falsa */
    CHECK_EQ(blob_r_open(&r, BUF, n, BLOB_PRESET), BLOB_E_LENGTH);
    BUF[6] = 10;
    BUF[0] = 's';
    CHECK_EQ(blob_r_open(&r, BUF, n, BLOB_PRESET), BLOB_E_MAGIC);
    BUF[0] = 'S';
    CHECK_EQ(blob_r_open(&r, BUF, n, BLOB_PRESET), BLOB_OK);

    /* in scrittura: contenuto troppo lungo, buffer più corto dell'intestazione, tipo sconosciuto */
    memset(BUF, 0xEE, sizeof BUF);
    blob_w_begin(&w, BUF, 20, BLOB_LOOP, 1);
    blob_w_u32(&w, 1);
    blob_w_u16(&w, 2);
    CHECK(!w.over);
    blob_w_u8(&w, 3);
    CHECK(w.over);
    CHECK_EQ(blob_w_end(&w), 0);
    CHECK_EQ(BUF[16], 0xEE);                                              /* niente CRC scritto */
    blob_w_begin(&w, BUF, BLOB_OVERHEAD - 1, BLOB_LOOP, 1);
    CHECK_EQ(blob_w_end(&w), 0);
    blob_w_begin(&w, BUF, sizeof BUF, BLOB_KIND_COUNT, 1);
    CHECK_EQ(blob_w_end(&w), 0);
}

/* blob_w_room e blob_w_skip: il contenuto lo scrive il chiamante, senza copie */
static void t_blob_room(void)
{
    blob_w_t w;
    blob_r_t r;
    size_t room;

    blob_w_begin(&w, BUF, 32, BLOB_SETTINGS, 1);
    uint8_t *p = blob_w_room(&w, &room);
    CHECK_EQ(room, 32 - BLOB_OVERHEAD);
    CHECK(p == BUF + BLOB_HEAD);
    memcpy(p, "x=1\n", 4);
    blob_w_skip(&w, 4);
    (void)blob_w_room(&w, &room);
    CHECK_EQ(room, 32 - BLOB_OVERHEAD - 4);
    size_t n = blob_w_end(&w);
    CHECK_EQ(n, BLOB_OVERHEAD + 4);
    CHECK_EQ(blob_r_open(&r, BUF, n, BLOB_SETTINGS), BLOB_OK);
    CHECK(r.n == 4 && memcmp(r.p, "x=1\n", 4) == 0);

    blob_w_begin(&w, BUF, 32, BLOB_SETTINGS, 1);
    blob_w_skip(&w, 32 - BLOB_OVERHEAD + 1);
    CHECK(w.over);
    (void)blob_w_room(&w, &room);
    CHECK_EQ(room, 0);
    CHECK_EQ(blob_w_end(&w), 0);
}

/* PLT-066: scrittura */
static void t_kv_scrittura(void)
{
    static const char WANT[] = "a=0\nb=-12\nc=2147483647\nd=-2147483648\nnome=Pad caldo\n";
    char txt[128];
    kv_w_t w;

    kv_w_begin(&w, txt, sizeof txt);
    kv_w_int(&w, "a", 0);
    kv_w_int(&w, "b", -12);
    kv_w_int(&w, "c", INT32_MAX);
    kv_w_int(&w, "d", INT32_MIN);
    kv_w_str(&w, "nome", "Pad caldo");
    size_t n = kv_w_end(&w);
    CHECK_EQ(n, sizeof WANT - 1);
    CHECK(memcmp(txt, WANT, sizeof WANT - 1) == 0);

    /* il testo non sta: 0 */
    kv_w_begin(&w, txt, 5);
    kv_w_int(&w, "a", 1);
    CHECK_EQ(kv_w_end(&w), 4);
    kv_w_int(&w, "b", 2);
    CHECK(w.over);
    CHECK_EQ(kv_w_end(&w), 0);
}

/* PLT-066: lettura tollerante */
static void t_kv_lettura(void)
{
    static const char TXT[] =
        "# commento\n"
        "\n"
        "  a = 5 \r\n"
        "b=-7\n"
        "riga senza uguale\n"
        "c=12 # commento in coda\n"
        "n=4\t# dopo un tab\n"
        "d=x#y\n"
        "=senza chiave\n"
        "e=\n"
        "f=2147483648\n"
        "g=-2147483648\n"
        "h=+3\n"
        "i=1x\n"
        "j=-\n"
        "k=3";                                                            /* ultima riga senza LF */
    kv_r_t r;
    kv_pair_t kv;
    int32_t v;

    kv_r_begin(&r, TXT, sizeof TXT - 1);
    CHECK(kv_r_next(&r, &kv) && kv_key_is(&kv, "a") && kv_val_int(&kv, &v) && v == 5);
    CHECK(kv_r_next(&r, &kv) && kv_key_is(&kv, "b") && kv_val_int(&kv, &v) && v == -7);
    CHECK(kv_r_next(&r, &kv) && kv_key_is(&kv, "c") && kv_val_int(&kv, &v) && v == 12);
    CHECK(kv_r_next(&r, &kv) && kv_key_is(&kv, "n") && kv_val_int(&kv, &v) && v == 4);
    CHECK(kv_r_next(&r, &kv) && kv_key_is(&kv, "d") && kv.vlen == 3 && memcmp(kv.val, "x#y", 3) == 0);
    CHECK(kv_r_next(&r, &kv) && kv_key_is(&kv, "e") && kv.vlen == 0 && !kv_val_int(&kv, &v));
    CHECK(kv_r_next(&r, &kv) && kv_key_is(&kv, "f") && !kv_val_int(&kv, &v));         /* fuori da int32 */
    CHECK(kv_r_next(&r, &kv) && kv_key_is(&kv, "g") && kv_val_int(&kv, &v) && v == INT32_MIN);
    CHECK(kv_r_next(&r, &kv) && kv_key_is(&kv, "h") && kv_val_int(&kv, &v) && v == 3);
    CHECK(kv_r_next(&r, &kv) && kv_key_is(&kv, "i") && !kv_val_int(&kv, &v));
    CHECK(kv_r_next(&r, &kv) && kv_key_is(&kv, "j") && !kv_val_int(&kv, &v));
    CHECK(kv_r_next(&r, &kv) && kv_key_is(&kv, "k") && !kv_key_is(&kv, "kk") && kv_val_int(&kv, &v) && v == 3);
    CHECK(!kv_r_next(&r, &kv));

    kv_r_begin(&r, "", 0);
    CHECK(!kv_r_next(&r, &kv));
}

/* righe lette -> acc_kv_apply; ritorna quante erano del motore degli accordi */
static int apply_text(acc_state *s, const char *txt, size_t n)
{
    kv_r_t r;
    kv_pair_t kv;
    int applied = 0;
    kv_r_begin(&r, txt, n);
    while (kv_r_next(&r, &kv)) applied += acc_kv_apply(s, &kv);
    return applied;
}

/* acc_kv: ogni opzione nel suo file, andata e ritorno nel blob STM1, limiti e default */
static void t_acc_kv(void)
{
    static const char IMP[] =
        "acc.play_style=0\n"
        "acc.secret_chords=0\n"
        "acc.single_notes=1\n"
        "acc.extension_addition=0\n"
        "acc.velocity_sense=1\n"
        "acc.bass_mode=0\n"
        "acc.compat_dim7_true=0\n"
        "acc.compat_partial_retrigger=0\n"
        "acc.compat_free_2025=0\n";
    static const char STA[] =
        "acc.key_mode=0\n"
        "acc.key=0\n"
        "acc.transpose=0\n"
        "acc.bass=0\n"
        "acc.chord_voicing=24\n"
        "acc.bass_voicing=23\n";
    /* tutte diverse dai default */
    static const int16_t VAL[ACC_OPT_COUNT] = {
        [ACC_OPT_PLAY_STYLE] = ACC_STYLE_FREE, [ACC_OPT_EXT_ADD] = ACC_EXTADD_PLAY_CHORD,
        [ACC_OPT_SECRET] = ACC_SECRET_ALL, [ACC_OPT_SINGLE_NOTES] = ACC_SINGLE_SPLIT,
        [ACC_OPT_VEL_SENSE] = 0, [ACC_OPT_BASS_MODE] = ACC_BASS_SOLO, [ACC_OPT_BASS_ON] = 1,
        [ACC_OPT_KEY_ON] = 1, [ACC_OPT_KEY_INDEX] = ACC_KEY_COUNT - 1, [ACC_OPT_TRANSPOSE] = ACC_TRANSPOSE_MIN,
        [ACC_OPT_VOICING] = ACC_V_MAX, [ACC_OPT_BASS_VOICING] = ACC_VB_MIN,
        [ACC_OPT_COMPAT_DIM7_TRUE] = 1, [ACC_OPT_COMPAT_PARTIAL_RETRIGGER] = 1, [ACC_OPT_COMPAT_FREE_2025] = 1,
    };
    static const char FUORI[] =
        "acc.chord_voicing=999\n"
        "acc.transpose=-40000\n"
        "acc.key=-1\n"
        "acc.play_style=7\n"
        "acc.bass_voicing=abc\n"
        "acc.key_mode=2147483647\n"
        "acc.keyx=1\n"
        "ui.lingua=it\n"
        "acc.velocity_sense = 0   # commento\n";
    char txt[512];
    kv_w_t w;
    blob_w_t bw;
    blob_r_t br;
    size_t room;

    /* i default, ciascuno nel suo file (sezione 50 §9.1) */
    acc_init(&A);
    kv_w_begin(&w, txt, sizeof txt);
    acc_kv_save(&A, &w, KV_IMPOSTAZIONI);
    size_t n = kv_w_end(&w);
    CHECK_EQ(n, sizeof IMP - 1);
    CHECK(n == sizeof IMP - 1 && memcmp(txt, IMP, n) == 0);
    kv_w_begin(&w, txt, sizeof txt);
    acc_kv_save(&A, &w, KV_STATO);
    n = kv_w_end(&w);
    CHECK_EQ(n, sizeof STA - 1);
    CHECK(n == sizeof STA - 1 && memcmp(txt, STA, n) == 0);

    /* andata e ritorno: il contenuto di STM1 è il testo chiave=valore dei due file (PLT-065) */
    for (int o = 0; o < ACC_OPT_COUNT; o++) acc_input(&A, ACC_IN_OPTION_SET, (uint8_t)o, VAL[o], 0, NULL, 0);
    for (int o = 0; o < ACC_OPT_COUNT; o++) CHECKM(acc_option_get(&A, o) == VAL[o], "opzione %d", o);
    blob_w_begin(&bw, BUF, sizeof BUF, BLOB_SETTINGS, 1);
    char *dst = (char *)blob_w_room(&bw, &room);
    kv_w_begin(&w, dst, room);
    acc_kv_save(&A, &w, KV_IMPOSTAZIONI);
    acc_kv_save(&A, &w, KV_STATO);
    n = kv_w_end(&w);
    CHECK(n > 0);
    blob_w_skip(&bw, n);
    size_t total = blob_w_end(&bw);
    CHECK_EQ(total, BLOB_OVERHEAD + n);
    acc_init(&B);
    CHECK_EQ(blob_r_open(&br, BUF, total, BLOB_SETTINGS), BLOB_OK);
    CHECK_EQ(apply_text(&B, (const char *)br.p, br.n), ACC_OPT_COUNT);
    for (int o = 0; o < ACC_OPT_COUNT; o++) CHECKM(acc_option_get(&B, o) == VAL[o], "opzione %d", o);

    /* valori fuori dai limiti riportati dentro; non numerici e chiavi d'altri moduli lasciati */
    acc_init(&B);
    CHECK_EQ(apply_text(&B, FUORI, sizeof FUORI - 1), 6);
    CHECK_EQ(acc_option_get(&B, ACC_OPT_VOICING), ACC_V_MAX);
    CHECK_EQ(acc_option_get(&B, ACC_OPT_TRANSPOSE), ACC_TRANSPOSE_MIN);
    CHECK_EQ(acc_option_get(&B, ACC_OPT_KEY_INDEX), 0);
    CHECK_EQ(acc_option_get(&B, ACC_OPT_PLAY_STYLE), ACC_STYLE_FREE);
    CHECK_EQ(acc_option_get(&B, ACC_OPT_BASS_VOICING), ACC_VB_DEFAULT);
    CHECK_EQ(acc_option_get(&B, ACC_OPT_KEY_ON), 1);
    CHECK_EQ(acc_option_get(&B, ACC_OPT_VEL_SENSE), 0);
    CHECK_EQ(acc_option_get(&B, ACC_OPT_BASS_MODE), ACC_BASS_CHORDS_ONLY);  /* chiave mancante: default */
    CHECK_EQ(acc_option_get(&B, ACC_OPT_COUNT), 0);
}

void test_blob(void)
{
    t_crc();
    t_blob();
    t_blob_errori();
    t_blob_room();
    t_kv_scrittura();
    t_kv_lettura();
    t_acc_kv();
}
