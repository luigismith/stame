"""curve.py — genera src/dsp/curves.c e curves.h con le curve raw → grandezza fisica.

Specifica 20, §3 (SND-150): ogni conversione è una tabella di 128 float, generata dalle formule
di default di Stame. Una curva misurata si mette in tools/curve/<nome>.csv (128 righe, un valore
per riga, nell'ordine dei raw 0…127) e sostituisce la formula senza toccare il resto del codice.

    python -I tools/curve.py
"""
import math
import os

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)


def x(r):
    return r / 127.0


def lfo_rate(r):
    """Interpolazione logaritmica tra i punti (x, Hz) di §3 (QA-SND-06)."""
    punti = [(0.0, 0.033), (0.2, 0.1), (0.3, 1.0), (0.6, 4.0), (0.7, 8.0), (1.0, 60.0)]
    v = x(r)
    for (x0, f0), (x1, f1) in zip(punti, punti[1:]):
        if v <= x1:
            t = (v - x0) / (x1 - x0)
            return math.exp(math.log(f0) + t * (math.log(f1) - math.log(f0)))
    return punti[-1][1]


# nome, unità, formula, requisito
CURVE = [
    ('T_ATT', 's', lambda r: 0.0005 + 1.5 * x(r) ** 1.585, 'attacco (QA-SND-05)'),
    ('T_HOLD', 's', lambda r: 2.0 * x(r) ** 1.585, 'hold / delay (QA-SND-05)'),
    ('T_DEC', 's', lambda r: 0.002 + 6.0 * x(r) ** 1.585, 'decay e release, tempo per -60 dB (QA-SND-05)'),
    ('T_GLIDE', 's', lambda r: 0.0 if r == 0 else 0.003 + 2.0 * x(r) ** 1.585, 'glide, 0 = spento (QA-SND-07)'),
    ('F_LFO', 'Hz', lfo_rate, 'rate degli LFO (QA-SND-06)'),
    ('F_CUT', 'Hz', lambda r: 20.0 * 1000.0 ** x(r), 'cutoff, limitato a 0,45 fs da chi lo usa (QA-SND-04)'),
    ('K_RES', '', lambda r: math.sqrt(2.0) * (1.0 - x(r) ** 0.8),
     'smorzamento dell\'SVF: raw 0 = Butterworth (-3 dB a f_cut), 127 = auto-oscillazione (QA-SND-04)'),
    ('F_HP', 'Hz', lambda r: 0.0 if r == 0 else 20.0 * 100.0 ** x(r), 'passa-alto di tastiera, 0 = spento (QA-SND-04)'),
    ('G_VOL', '', lambda r: (r / 64.0) ** 2, 'GAIN di patch e RPVOL (QA-SND-28)'),
    ('G_OSC', '', lambda r: r / 64.0, 'GAIN dell\'oscillatore VA (QA-SND-28)'),
    ('F_FX_RATE', 'Hz', lambda r: 0.05 * 200.0 ** x(r), 'rate di chorus, phaser, flanger, tremolo (QA-SND-20)'),
    ('T_DELAY', 's', lambda r: 0.0 if r < 3 else 0.010 * 150.0 ** ((r - 3) / 124.0), 'tempo libero del delay, raw 3…127 (QA-SND-08)'),
    ('T_RP_DECAY', 's', lambda r: 0.3 * (20.0 / 0.3) ** x(r), 'T60 della lamella RP a C4 (QA-SND-15)'),
    ('T_RP_RELEASE', 's', lambda r: 0.02 * (3.0 / 0.02) ** x(r), 'T60 dopo il rilascio, RP (QA-SND-15)'),
    ('F_RP_TREM', 'Hz', lambda r: 0.5 * 24.0 ** x(r), 'tremolo interno RP (QA-SND-15)'),
    ('T_REV', 's', lambda r: 0.3 * (10.0 / 0.3) ** x(r), 'RT60 del riverbero da REVSIZE (QA-SND-09)'),
    ('F_REVLP', 'Hz', lambda r: 1000.0 * 20.0 ** x(r), 'passa-basso nelle linee del riverbero'),
    ('F_REVHP', 'Hz', lambda r: 20.0 * 50.0 ** x(r), 'passa-alto all\'ingresso del riverbero'),
    ('F_DLYLP', 'Hz', lambda r: 500.0 * 40.0 ** x(r), 'passa-basso nel loop del delay (QA-SND-08)'),
    ('F_DLYHP', 'Hz', lambda r: 0.0 if r == 0 else 20.0 * 100.0 ** x(r), 'passa-alto nel loop del delay, 0 = spento'),
]


def valori(nome, formula):
    csv = os.path.join(QUI, 'curve', nome.lower() + '.csv')
    if os.path.exists(csv):
        righe = [l.strip() for l in open(csv, encoding='utf-8') if l.strip() and not l.startswith('#')]
        if len(righe) != 128:
            raise SystemExit('%s: servono 128 righe, ce ne sono %d' % (csv, len(righe)))
        return [float(v) for v in righe], 'misurata (' + os.path.relpath(csv, RADICE).replace('\\', '/') + ')'
    return [formula(r) for r in range(128)], 'formula di default'


def flt(v):
    s = '%.9g' % v
    if 'e' not in s and '.' not in s:
        s += '.0'
    return s + 'f'


def main():
    h = ['/* curves.h — curve raw → grandezza fisica (specifica 20, §3, SND-150).',
         ' * Generato da tools/curve.py: non modificare a mano. */',
         '#ifndef STAME_DSP_CURVES_H',
         '#define STAME_DSP_CURVES_H',
         '#include "../core/stame_base.h"',
         '',
         'enum {']
    for nome, _, _, _ in CURVE:
        h.append('    CURVE_%s,' % nome)
    h += ['    CURVE_COUNT', '};', '',
          '/* tabelle da 128 valori, una per curva */',
          'extern const float dsp_curves[CURVE_COUNT][128];', '',
          '/* valore della curva c al raw r (0…127); fra due raw interpola linearmente */',
          'static inline float curve(int c, float r)',
          '{',
          '    if (!(r > 0.0f)) return dsp_curves[c][0];',
          '    if (r >= 127.0f) return dsp_curves[c][127];',
          '    int i = (int)r;',
          '    float t = r - (float)i;',
          '    return dsp_curves[c][i] + t * (dsp_curves[c][i + 1] - dsp_curves[c][i]);',
          '}', '',
          '/* valore al raw intero */',
          'static inline float curve_i(int c, int r) { return dsp_curves[c][r < 0 ? 0 : r > 127 ? 127 : r]; }',
          '',
          '#endif', '']
    c = ['/* curves.c — curve raw → grandezza fisica (specifica 20, §3, SND-150).',
         ' * Generato da tools/curve.py: non modificare a mano. Per una curva misurata: tools/curve/<nome>.csv. */',
         '#include "curves.h"',
         '',
         'const float dsp_curves[CURVE_COUNT][128] STAME_ROM = {']
    for nome, unita, formula, nota in CURVE:
        v, origine = valori(nome, formula)
        c.append('    /* %s: %s%s, %s */' % (nome, nota, (' [' + unita + ']') if unita else '', origine))
        c.append('    {')
        for i in range(0, 128, 8):
            c.append('        ' + ', '.join(flt(t) for t in v[i:i + 8]) + ',')
        c.append('    },')
    c += ['};', '']
    # seno da tabella per gli operatori FM e gli LFO (SND-306): 2048 punti più la chiusura
    c += ['/* seno su un ciclo, 2048 punti più il primo ripetuto (SND-306) */',
          'const float dsp_sin_tab[2049] STAME_ROM = {']
    seno = [math.sin(2.0 * math.pi * i / 2048.0) for i in range(2049)]
    seno[2048] = seno[0]
    for i in range(0, 2049, 8):
        c.append('    ' + ', '.join(flt(t) for t in seno[i:i + 8]) + ',')
    c += ['};', '']
    for nome, testo in (('curves.h', h), ('curves.c', c)):
        p = os.path.join(RADICE, 'src', 'dsp', nome)
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(testo))
        print('scritto', os.path.relpath(p, RADICE))


if __name__ == '__main__':
    main()
