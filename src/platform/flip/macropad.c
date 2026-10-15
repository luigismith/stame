/* macropad.c — il macro pad BRIMFORD sulla Flip (sezione 40, MIDI-122…127).
 *
 * Si riconosce dal VID:PID (1189:8840, VP-1 del 15/10/2026). Si aprono tutti i suoi nodi evdev
 * (tastiera, tasti multimediali, mouse) in esclusiva con EVIOCGRAB: spruce e PyUI non vedono i
 * tasti. I codici diventano i MPAD_* del profilo pad_brimford. La mappa vale per le configurazioni
 * di fabbrica:
 *   - strati 2 e 3: tasti A…O in ordine di lettura (manopole a destra), che mpad_tasto traduce nei
 *     tasti della mappa di §8.10 (la quinta colonna, E J O, è T13–T15); manopole sulle cifre:
 *     piccola vicina ai tasti 1 antiorario, 2 pressione, 3 orario; l'altra piccola 4, 5, 6;
 *     la grande 9 antiorario, 8 pressione, 7 orario;
 *   - strato 1 (quello dell'accensione): Win+L sul primo tasto, «K, Ctrl+C» e «L, Ctrl+V» sui
 *     tasti 11 e 12, volume giù, muto e su sulla manopola grande.
 * I tasti premuti con Ctrl, Alt o Shift sono le sequenze dello strato 1 e si ignorano.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/input.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "flip.h"
#include "../../core/input/pad_codes.h"

#define MPAD_VID 0x1189
#define MPAD_PID 0x8840
#define MAXFD 6

enum { MOD_CTRL = 1, MOD_SHIFT = 2, MOD_ALT = 4, MOD_META = 8 };

static int fds[MAXFD], nfd;
static uint8_t mods;
static uint16_t down_as[KEY_MAX + 1];     /* tasto evdev giù → codice MPAD dato alla pressione */
static int unknown;

static uint8_t mod_bit(uint16_t code)
{
    switch (code) {
    case KEY_LEFTCTRL: case KEY_RIGHTCTRL: return MOD_CTRL;
    case KEY_LEFTSHIFT: case KEY_RIGHTSHIFT: return MOD_SHIFT;
    case KEY_LEFTALT: case KEY_RIGHTALT: return MOD_ALT;
    case KEY_LEFTMETA: case KEY_RIGHTMETA: return MOD_META;
    default: return 0;
    }
}

static uint16_t map(uint16_t code)
{
    static const uint16_t LETTERE[15] = { KEY_A, KEY_B, KEY_C, KEY_D, KEY_E, KEY_F, KEY_G, KEY_H, KEY_I,
                                          KEY_J, KEY_K, KEY_L, KEY_M, KEY_N, KEY_O };
    if (mods & (MOD_CTRL | MOD_SHIFT | MOD_ALT)) return 0;            /* Ctrl+C, Ctrl+V dello strato 1 */
    if (mods & MOD_META) return code == KEY_L ? mpad_tasto(0) : 0;   /* Win+L dello strato 1, sul primo tasto */
    for (int i = 0; i < 15; i++) if (LETTERE[i] == code) return mpad_tasto(i);   /* posizione → tasto (MIDI-120) */
    switch (code) {
    case KEY_1: return MPAD_M1_CCW;
    case KEY_2: return MPAD_M1_PUSH;
    case KEY_3: return MPAD_M1_CW;
    case KEY_4: return MPAD_M2_CCW;
    case KEY_5: return MPAD_M2_PUSH;
    case KEY_6: return MPAD_M2_CW;
    case KEY_9: case KEY_VOLUMEDOWN: return MPAD_M_CCW;
    case KEY_8: case KEY_MUTE: return MPAD_M_PUSH;
    case KEY_7: case KEY_VOLUMEUP: return MPAD_M_CW;
    default: return 0;
    }
}

int macropad_open(void)
{
    nfd = 0;
    mods = 0;
    unknown = 0;
    memset(down_as, 0, sizeof down_as);
    int grab_failed = 0;
    for (int i = 0; i < 32 && nfd < MAXFD; i++) {
        char path[32];
        snprintf(path, sizeof path, "/dev/input/event%d", i);
        int fd = open(path, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
        if (fd < 0) continue;
        struct input_id id;
        if (ioctl(fd, EVIOCGID, &id) < 0 || id.vendor != MPAD_VID || id.product != MPAD_PID) { close(fd); continue; }
        if (ioctl(fd, EVIOCGRAB, 1) < 0) {                           /* MIDI-124: tutti i nodi in esclusiva */
            log_msg("pad: EVIOCGRAB fallito su %s (%s)", path, strerror(errno));
            close(fd);
            grab_failed = 1;
            continue;
        }
        char name[64] = { 0 };
        ioctl(fd, EVIOCGNAME(sizeof name - 1), name);
        log_msg("pad: %s «%s»", path, name);
        fds[nfd++] = fd;
    }
    if (grab_failed && nfd == 0) return -2;
    return nfd;
}

void macropad_close(void)
{
    for (int i = 0; i < nfd; i++) close(fds[i]);
    nfd = 0;
}

int macropad_fds(int *out, int max)
{
    int n = nfd < max ? nfd : max;
    for (int i = 0; i < n; i++) out[i] = fds[i];
    return n;
}

/* legge tutti i nodi; restituisce −1 se il pad è sparito, altrimenti il numero di codici ignorati di fila */
int macropad_read(pad_cb_t cb, void *ctx)
{
    struct input_event ev[32];
    for (int k = 0; k < nfd; k++) {
        for (;;) {
            ssize_t n = read(fds[k], ev, sizeof ev);
            if (n < 0) {
                if (errno == EAGAIN || errno == EWOULDBLOCK) break;
                return -1;                                            /* ENODEV: scollegato (MIDI-127) */
            }
            if (n == 0) break;
            for (int i = 0; i < (int)(n / (ssize_t)sizeof ev[0]); i++) {
                if (ev[i].type != EV_KEY || ev[i].code > KEY_MAX) continue;
                uint16_t code = ev[i].code;
                int value = ev[i].value;
                if (value == 2) continue;                             /* ripetizione del kernel (MIDI-125) */
                uint8_t mb = mod_bit(code);
                if (mb) { if (value) mods |= mb; else mods &= (uint8_t)~mb; continue; }
                if (value == 1) {
                    uint16_t m = map(code);
                    down_as[code] = m;
                    if (m) { unknown = 0; cb(ctx, m, 1); }
                    else if (!(mods & (MOD_CTRL | MOD_SHIFT | MOD_ALT))) unknown++;
                } else if (down_as[code]) {
                    cb(ctx, down_as[code], 0);
                    down_as[code] = 0;
                }
            }
        }
    }
    return unknown;
}
