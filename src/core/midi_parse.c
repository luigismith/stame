/* midi_parse.c — parser MIDI con running status, real time ovunque e SysEx in un buffer statico
 * (MIDI-005). Riprende il codice della guida alla Plus, §17.4. */
#include "midi_parse.h"

/* byte di dati che seguono uno status; 0 per i messaggi di un byte solo */
static uint8_t data_len(uint8_t st)
{
    switch (st & 0xF0) {
    case 0xC0: case 0xD0: return 1;
    case 0xF0: return st == 0xF2 ? 2 : (st == 0xF1 || st == 0xF3) ? 1 : 0;
    default:   return 2;
    }
}

static void short_msg(const midi_parser_t *p, midi_msg_t *m, uint32_t t_us,
                      uint8_t st, uint8_t d0, uint8_t d1, uint8_t n)
{
    memset(m, 0, sizeof *m);
    if ((st & 0xF0) == 0x90 && n == 3 && d1 == 0) st = (uint8_t)(0x80 | (st & 0x0F));   /* MIDI-005 */
    m->t_us = t_us;
    m->port = p->port;
    m->n = n;
    m->valid = 1;
    m->b[0] = st; m->b[1] = d0; m->b[2] = d1;
}

/* chiude il SysEx in corso con il suo F7: c'è sempre posto, perché i dati si fermano a
 * MIDI_SX_MAX - 1 byte */
static void close_sysex(midi_parser_t *p, midi_msg_t *m, uint32_t t_us)
{
    p->sx[p->sx_n++] = 0xF7;
    memset(m, 0, sizeof *m);
    m->t_us = t_us;
    m->port = p->port;
    m->sysex = 1;
    m->valid = !p->sx_over;
    m->sx_n = p->sx_n;
    m->sx = p->sx;
    p->in_sx = 0;
}

void midi_parser_init(midi_parser_t *p, uint8_t port)
{
    memset(p, 0, sizeof *p);
    p->port = port;
}

int midi_parse_byte(midi_parser_t *p, uint8_t b, uint32_t t_us, midi_msg_t out[MIDI_PARSE_MAX_OUT])
{
    int k = 0;

    if (b >= 0xF8) {                                    /* real time: ovunque, senza toccare lo stato */
        short_msg(p, &out[k++], t_us, b, 0, 0, 1);
        return k;
    }
    if (p->in_sx) {
        if (b < 0x80) {
            if (p->sx_n < MIDI_SX_MAX - 1) p->sx[p->sx_n++] = b;
            else p->sx_over = 1;                        /* troncato: non valido */
            return 0;
        }
        close_sysex(p, &out[k++], t_us);                /* F7 o qualunque altro status */
        if (b == 0xF7) return k;
    }
    if (b == 0xF0) {
        p->in_sx = 1;
        p->sx_over = 0;
        p->sx_n = 0;
        p->sx[p->sx_n++] = b;
        p->st = 0;
        p->n = 0;
        return k;
    }
    if (b >= 0x80) {
        p->n = 0;
        if (b == 0xF7) { p->st = 0; return k; }         /* F7 senza SysEx: ignorato */
        p->need = data_len(b);
        if (p->need == 0) {                             /* F4, F5, F6: un byte, niente running status */
            short_msg(p, &out[k++], t_us, b, 0, 0, 1);
            p->st = 0;
            return k;
        }
        p->st = b;
        return k;
    }
    if (!p->st) return k;                               /* dato orfano */
    p->d[p->n++] = b;
    if (p->n == p->need) {
        short_msg(p, &out[k++], t_us, p->st, p->d[0], p->need > 1 ? p->d[1] : 0, (uint8_t)(1 + p->need));
        p->n = 0;
        if (p->st >= 0xF0) p->st = 0;                   /* F1–F3: niente running status */
    }
    return k;
}
