/* input_evdev.c — tasti della Flip letti da evdev (PLT-052..PLT-055).
 *
 * Il pad si cerca per nome («MIYOO Player1»), non per numero: un dispositivo HID collegato
 * all'avvio lo sposta (PLT-053). I codici PAD_* coincidono con quelli evdev: i controlli qui
 * sotto bloccano la compilazione se un nome si confonde con le macro BTN_* (PLT-054).
 */
#define _GNU_SOURCE
#include <fcntl.h>
#include <linux/input.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "flip.h"
#include "../../core/input/pad_codes.h"

_Static_assert(PAD_A == BTN_EAST, "PAD_A deve essere il codice evdev 305");
_Static_assert(PAD_B == BTN_SOUTH, "PAD_B deve essere il codice evdev 304");
_Static_assert(PAD_X == BTN_WEST, "PAD_X deve essere il codice evdev 308");
_Static_assert(PAD_Y == BTN_NORTH, "PAD_Y deve essere il codice evdev 307");
_Static_assert(PAD_L1 == BTN_TL && PAD_R1 == BTN_TR, "L1/R1");
_Static_assert(PAD_SELECT == BTN_SELECT && PAD_START == BTN_START && PAD_MENU == BTN_MODE, "SELECT/START/MENU");

static int hat_x, hat_y;

int pad_open(void)
{
    for (int i = 0; i < 16; i++) {
        char path[32], name[64] = { 0 };
        snprintf(path, sizeof path, "/dev/input/event%d", i);
        int fd = open(path, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
        if (fd < 0) continue;
        if (ioctl(fd, EVIOCGNAME(sizeof name - 1), name) >= 0 && strstr(name, "MIYOO Player1")) {
            log_msg("tasti: %s (%s)", path, name);
            return fd;
        }
        close(fd);
    }
    log_msg("tasti: «MIYOO Player1» non trovato");
    return -1;
}

static void hat(pad_cb_t cb, void *ctx, int *state, int v, uint16_t neg, uint16_t pos)
{
    if (v == *state) return;
    if (*state < 0) cb(ctx, neg, 0);
    if (*state > 0) cb(ctx, pos, 0);
    *state = v;
    if (v < 0) cb(ctx, neg, 1);
    if (v > 0) cb(ctx, pos, 1);
}

void pad_read(int fd, pad_cb_t cb, void *ctx)
{
    struct input_event ev[32];
    for (;;) {
        ssize_t n = read(fd, ev, sizeof ev);
        if (n <= 0) return;
        for (int i = 0; i < (int)(n / (ssize_t)sizeof ev[0]); i++) {
            if (ev[i].type == EV_KEY) {
                cb(ctx, ev[i].code, ev[i].value);
            } else if (ev[i].type == EV_ABS) {
                if (ev[i].code == ABS_HAT0X) hat(cb, ctx, &hat_x, ev[i].value, PAD_LEFT, PAD_RIGHT);
                else if (ev[i].code == ABS_HAT0Y) hat(cb, ctx, &hat_y, ev[i].value, PAD_UP, PAD_DOWN);
            }
        }
    }
}

void pad_close(int fd)
{
    if (fd >= 0) close(fd);
}
