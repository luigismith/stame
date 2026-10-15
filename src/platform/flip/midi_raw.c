/* midi_raw.c — MIDI grezzo da /dev/snd/midiC*D0, senza alsa-lib (sezione 50, §6.1–§6.3).
 *
 * Si preferisce una scheda con «MPK» nel nome; altrimenti la prima tastiera MIDI. Il sottodispositivo
 * si sceglie come fa alsa-lib: SNDRV_CTL_IOCTL_RAWMIDI_PREFER_SUBDEVICE sul controllo della scheda,
 * poi l'apertura del rawmidi. Porta 1 = sottodispositivo 0. La MPK mini IV manda manopole, SHIFT e
 * trasporto sulla porta 2 (DAW, sottodispositivo 1): per lei si aprono tutte e due (§8.9b).
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <sound/asound.h>
#include "flip.h"

static void card_name(int card, char *out, int n)
{
    char path[64];
    snprintf(path, sizeof path, "/proc/asound/card%d/id", card);
    FILE *f = fopen(path, "r");
    out[0] = 0;
    if (!f) return;
    if (fgets(out, n, f)) out[strcspn(out, "\r\n")] = 0;
    fclose(f);
    /* il nome lungo sta in /proc/asound/cards: «N [id ]: driver - nome» */
    f = fopen("/proc/asound/cards", "r");
    if (!f) return;
    char line[256];
    while (fgets(line, sizeof line, f)) {
        int c;
        if (sscanf(line, " %d [", &c) == 1 && c == card) {
            char *dash = strstr(line, " - ");
            if (dash) { snprintf(out, (size_t)n, "%s", dash + 3); out[strcspn(out, "\r\n")] = 0; }
            break;
        }
    }
    fclose(f);
}

/* apre il sottodispositivo sub del rawmidi 0 della scheda; −1 se non si apre */
static int open_sub(int card, int sub)
{
    char cpath[32], path[32];
    snprintf(cpath, sizeof cpath, "/dev/snd/controlC%d", card);
    int cfd = open(cpath, O_RDWR | O_CLOEXEC);
    if (cfd >= 0 && ioctl(cfd, SNDRV_CTL_IOCTL_RAWMIDI_PREFER_SUBDEVICE, &sub) < 0)
        log_msg("MIDI: preferenza del sottodispositivo %d rifiutata (%s)", sub, strerror(errno));
    snprintf(path, sizeof path, "/dev/snd/midiC%dD0", card);
    int fd = open(path, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
    if (cfd >= 0) close(cfd);
    if (fd < 0) { log_msg("MIDI: %s non si apre (%s)", path, strerror(errno)); return -1; }
    struct snd_rawmidi_info info;
    memset(&info, 0, sizeof info);
    info.stream = SNDRV_RAWMIDI_STREAM_INPUT;
    if (ioctl(fd, SNDRV_RAWMIDI_IOCTL_INFO, &info) == 0 && (int)info.subdevice != sub) {
        log_msg("MIDI: chiesto il sottodispositivo %d, aperto il %u", sub, info.subdevice);
        close(fd);
        return -1;
    }
    return fd;
}

bool midi_scan(midi_dev_t *d)
{
    int best = -1;
    char best_name[48] = { 0 };
    for (int c = 0; c < 8; c++) {
        char path[32];
        snprintf(path, sizeof path, "/dev/snd/midiC%dD0", c);
        if (access(path, R_OK) != 0) continue;
        char name[48];
        card_name(c, name, sizeof name);
        bool mpk = strstr(name, "MPK") != NULL;
        if (best < 0 || mpk) { best = c; snprintf(best_name, sizeof best_name, "%s", name); }
        if (mpk) break;
    }
    if (best < 0) return false;
    bool mk4 = strstr(best_name, "MPK mini IV") != NULL || strstr(best_name, "MPK Mini IV") != NULL;
    int fd = open_sub(best, 0);
    if (fd < 0) return false;
    d->fd = fd;
    d->fd2 = -1;
    d->card = best;
    d->model = mk4 ? 1 : 0;
    snprintf(d->name, sizeof d->name, "%s", best_name);
    if (mk4) {
        d->fd2 = open_sub(best, 1);
        if (d->fd2 < 0) log_msg("MIDI: porta 2 della MK4 non aperta: manopole e trasporto non arriveranno");
    }
    log_msg("MIDI: scheda %d «%s»%s", best, d->name, mk4 ? ", MPK mini IV: porte 1 e 2" : ", porta 1");
    return true;
}

int midi_read(midi_dev_t *d, int port, uint8_t *buf, int max)
{
    int fd = port ? d->fd2 : d->fd;
    if (fd < 0) return 0;
    ssize_t n = read(fd, buf, (size_t)max);
    if (n > 0) return (int)n;
    if (n < 0 && (errno == EAGAIN || errno == EINTR)) return 0;
    return -1;                        /* ENODEV: la MPK è stata scollegata */
}

void midi_close(midi_dev_t *d)
{
    if (d->fd >= 0) close(d->fd);
    if (d->fd2 >= 0) close(d->fd2);
    d->fd = d->fd2 = -1;
}
