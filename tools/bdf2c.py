"""bdf2c.py — converte i font Spleen (BDF) in tabelle C per gfx (UI-144).

Uso: python -I tools/bdf2c.py <cartella con spleen-*.bdf> src/gfx

Per ogni misura scrive src/gfx/font_spleen_<W>x<H>.c con un sottoinsieme di caratteri: ASCII
stampabile, Latin-1 e i pochi simboli di Spleen che la plancia usa. I glifi che Spleen non ha
(♯, ♭, ✓, ▶ …) li disegna tools/simboli.py nel font dei simboli.

Formato (gfx/font.h): righe di (w + 7) / 8 byte, bit più alto = pixel a sinistra; i codepoint sono
ordinati, così gfx li cerca per bisezione. La licenza di Spleen (BSD 2-Clause) va in testa a ogni
file generato e in third_party/spleen/LICENSE.
"""
import os
import sys

MISURE = {          # misura -> sottoinsieme
    '6x12': 'tutto',
    '8x16': 'tutto',
    '12x24': 'tutto',
    '16x32': 'tutto',
    '32x64': 'ascii',
}

EXTRA = [0x2022, 0x2026, 0x2190, 0x2191, 0x2192, 0x2193, 0x25A0, 0x25B2, 0x25BC, 0x25CB, 0x25CF,
         0x2500, 0x2502, 0x2588]

LICENZA = """/*
 * Spleen {misura} — Copyright (c) 2018-2024, Frederic Cambus. https://www.cambus.net/
 * Spleen is released under the BSD 2-Clause license (third_party/spleen/LICENSE):
 *
 * Redistribution and use in source and binary forms, with or without modification, are permitted
 * provided that the following conditions are met: redistributions of source code must retain the
 * above copyright notice, this list of conditions and the following disclaimer; redistributions in
 * binary form must reproduce the above copyright notice, this list of conditions and the following
 * disclaimer in the documentation and/or other materials provided with the distribution.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
 * IMPLIED WARRANTIES ARE DISCLAIMED.
 *
 * File generato da tools/bdf2c.py: non modificarlo a mano.
 */
"""


def voluti(cp, sottoinsieme):
    if 0x20 <= cp <= 0x7E:
        return True
    if sottoinsieme == 'ascii':
        return False
    return 0xA0 <= cp <= 0xFF or cp in EXTRA


def leggi_bdf(percorso):
    font = {'glifi': {}}
    with open(percorso, encoding='latin-1') as f:
        righe = f.read().splitlines()
    i = 0
    while i < len(righe):
        r = righe[i]
        if r.startswith('FONTBOUNDINGBOX'):
            _, w, h, x0, y0 = r.split()
            font['bbx'] = (int(w), int(h), int(x0), int(y0))
        elif r.startswith('FONT_ASCENT'):
            font['ascent'] = int(r.split()[1])
        elif r.startswith('STARTCHAR'):
            cp = None
            bbx = None
            bitmap = []
            i += 1
            while not righe[i].startswith('ENDCHAR'):
                t = righe[i]
                if t.startswith('ENCODING'):
                    cp = int(t.split()[1])
                elif t.startswith('BBX'):
                    _, w, h, x0, y0 = t.split()
                    bbx = (int(w), int(h), int(x0), int(y0))
                elif t.startswith('BITMAP'):
                    i += 1
                    while not righe[i].startswith('ENDCHAR'):
                        bitmap.append(righe[i].strip())
                        i += 1
                    break
                i += 1
            if cp is not None and cp >= 0:
                font['glifi'][cp] = (bbx, bitmap)
        i += 1
    return font


def cella(font, cp):
    """Glifo come lista di h righe, ognuna lista di w bit, nella cella del font."""
    W, H, X0, Y0 = font['bbx']
    (w, h, x0, y0), bitmap = font['glifi'][cp]
    px = [[0] * W for _ in range(H)]
    top = (H + Y0) - (h + y0)          # riga della cella dove comincia la bitmap
    for r, hexa in enumerate(bitmap):
        v = int(hexa, 16)
        nbit = len(hexa) * 4
        for c in range(w):
            if v >> (nbit - 1 - c) & 1:
                y, x = top + r, (x0 - X0) + c
                if 0 <= y < H and 0 <= x < W:
                    px[y][x] = 1
    return px


def scrivi(font, misura, sottoinsieme, out_dir):
    W, H, _, Y0 = font['bbx']
    bpr = (W + 7) // 8
    cps = sorted(cp for cp in font['glifi'] if voluti(cp, sottoinsieme))
    nome = 'spleen_' + misura
    righe = [LICENZA.format(misura=misura), '#include "font.h"', '']
    righe.append(f'static const uint16_t CP[{len(cps)}] STAME_ROM = {{')
    for k in range(0, len(cps), 12):
        righe.append('    ' + ', '.join(f'0x{c:04X}' for c in cps[k:k + 12]) + ',')
    righe.append('};')
    righe.append('')
    righe.append(f'static const uint8_t BITS[{len(cps) * H * bpr}] STAME_ROM = {{')
    for cp in cps:
        px = cella(font, cp)
        byte = []
        for riga in px:
            for b in range(bpr):
                v = 0
                for c in range(8):
                    x = b * 8 + c
                    if x < W and riga[x]:
                        v |= 0x80 >> c
                byte.append(v)
        etichetta = chr(cp) if 0x20 < cp < 0x7F and cp not in (0x5C, 0x2A, 0x2F) else f'U+{cp:04X}'
        righe.append('    ' + ', '.join(f'0x{v:02X}' for v in byte) + f',   /* {etichetta} */')
    righe.append('};')
    righe.append('')
    ascent = H + Y0                   # righe sopra la linea di base
    righe.append(f'const gfx_font_t GFX_FONT_{misura.upper()} = '
                 f'{{ {W}, {H}, {ascent}, {bpr}, {len(cps)}, CP, BITS }};')
    righe.append('')
    percorso = os.path.join(out_dir, f'font_{nome}.c')
    with open(percorso, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(righe))
    print(f'{percorso}: {len(cps)} glifi, cella {W}x{H}, ascent {ascent}')


def main():
    src, out_dir = sys.argv[1], sys.argv[2]
    for misura, sottoinsieme in MISURE.items():
        font = leggi_bdf(os.path.join(src, f'spleen-{misura}.bdf'))
        scrivi(font, misura, sottoinsieme, out_dir)


if __name__ == '__main__':
    main()
