"""simboli.py — font dei simboli di Stame nelle celle di Spleen (UI-144).

Uso: python -I tools/simboli.py src/gfx          scrive src/gfx/font_simboli.c
     python -I tools/simboli.py --mostra 16x32   stampa i glifi in ASCII per controllarli

Spleen non ha ♯, ♭, ✓, ✚, ▶ e gli altri segni della plancia: qui si disegnano nelle stesse
celle, così gfx li usa come riserva del font principale. Nelle due misure piccole i glifi sono
disegnati a mano pixel per pixel; nelle altre si ricavano da forme geometriche campionate 8×8 per
pixel e soglia al 50%, con lo spessore dei tratti di Spleen.

U+E000 è il marchio di Stame: tre stami (filamento e antera) che salgono da un punto solo, come i
tre suoni di una triade. Le stesse proporzioni stanno nel logo grande (gfx_logo, tools/identita.py).
"""
import math
import os
import sys

# misura: (W, H, riga alta delle maiuscole, riga della linea di base, x0, x1, tratto)
METRICHE = {
    '6x12': (6, 12, 1, 8, 0, 4, 1),
    '8x16': (8, 16, 2, 11, 0, 6, 2),
    '12x24': (12, 24, 4, 18, 1, 10, 2),
    '16x32': (16, 32, 6, 25, 2, 13, 2),
    '32x64': (32, 64, 12, 51, 4, 27, 4),
}

SHARP, FLAT = 0x266F, 0x266D
DISC, RING, FISHEYE, CHECK, CROSS = 0x25CF, 0x25CB, 0x25C9, 0x2713, 0x271A
TRI_R, TRI_L, TRI_U, TRI_D, SQUARE = 0x25B6, 0x25C0, 0x25B2, 0x25BC, 0x25A0
BAR, BOLT, ELLIPSIS, STAME = 0x275A, 0x26A1, 0x2026, 0xE000
EN_DASH, EM_DASH = 0x2013, 0x2014

# --- glifi disegnati a mano: righe dalla 0, '#' acceso -------------------------------------------
A_MANO = {
    '6x12': {
        SHARP: (1, ['.#.#.', '.#.##', '.###.', '##.#.', '.#.##', '.###.', '##.#.', '.#.#.']),
        FLAT: (1, ['#....', '#....', '#....', '#.##.', '##..#', '#...#', '#..#.', '###..']),
        DISC: (2, ['.###.', '#####', '#####', '#####', '.###.']),
        RING: (2, ['.###.', '#...#', '#...#', '#...#', '.###.']),
        FISHEYE: (2, ['.###.', '#...#', '#.#.#', '#...#', '.###.']),
        CHECK: (2, ['....#', '...#.', '#.#..', '.#...']),
        CROSS: (2, ['.###.', '.###.', '#####', '.###.', '.###.']),
        TRI_R: (1, ['#....', '##...', '###..', '####.', '###..', '##...', '#....']),
        TRI_L: (1, ['...#.', '..##.', '.###.', '####.', '.###.', '..##.', '...#.']),
        TRI_U: (3, ['..#..', '.###.', '#####']),
        TRI_D: (3, ['#####', '.###.', '..#..']),
        SQUARE: (2, ['#####', '#####', '#####', '#####', '#####']),
        BAR: (1, ['.##..'] * 8),
        BOLT: (1, ['...##', '..##.', '.##..', '#####', '..##.', '.##..', '##...']),
        ELLIPSIS: (8, ['#.#.#']),
        EN_DASH: (5, ['.###.']),
        EM_DASH: (5, ['######']),
        STAME: (1, ['#.#.#', '#.#.#', '#.#.#', '.###.', '..#..', '..#..', '..#..', '.###.']),
    },
    '8x16': {
        SHARP: (1, ['.#..#..', '.#..#..', '.#..###', '.#####.', '###.#..', '.#..#..', '.#..#..',
                    '.#..###', '.#####.', '###.#..', '.#..#..', '.#..#..']),
        FLAT: (1, ['##.....', '##.....', '##.....', '##.....', '##.##..', '###.##.', '##...##',
                   '##...##', '##..##.', '##.##..', '####...']),
        DISC: (3, ['..###..', '.#####.', '#######', '#######', '#######', '.#####.', '..###..']),
        RING: (3, ['..###..', '.##.##.', '##...##', '#.....#', '##...##', '.##.##.', '..###..']),
        FISHEYE: (3, ['..###..', '.#...#.', '#..#..#', '#.###.#', '#..#..#', '.#...#.', '..###..']),
        CHECK: (3, ['......#', '.....##', '....##.', '#..##..', '####...', '.##....']),
        CROSS: (3, ['..###..', '..###..', '#######', '#######', '#######', '..###..', '..###..']),
        TRI_R: (2, ['#......', '###....', '#####..', '#######', '#####..', '###....', '#......']),
        TRI_L: (2, ['......#', '....###', '..#####', '#######', '..#####', '....###', '......#']),
        TRI_U: (4, ['...#...', '..###..', '.#####.', '#######']),
        TRI_D: (5, ['#######', '.#####.', '..###..', '...#...']),
        SQUARE: (3, ['#######', '#######', '#######', '#######', '#######', '#######', '#######']),
        BAR: (2, ['.###...'] * 10),
        BOLT: (1, ['....##.', '...##..', '..##...', '.##....', '#######', '...##..', '..##...',
                   '.##....', '##.....']),
        ELLIPSIS: (10, ['##.##.##', '##.##.##']),
        EN_DASH: (6, ['.#####.', '.#####.']),
        EM_DASH: (6, ['########', '########']),
        STAME: (1, ['#..#..#', '##.#.##', '##.#.##', '.#.#.#.', '.##.##.', '..###..', '...#...',
                    '...#...', '...#...', '.#####.']),
    },
}


# --- forme geometriche per le misure grandi --------------------------------------------------------
def _dentro_poligono(px, py, pts):
    dentro = False
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if (y1 > py) != (y2 > py):
            xc = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if px < xc:
                dentro = not dentro
    return dentro


def _dist_segmento(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    qx, qy = ax + t * dx, ay + t * dy
    return math.hypot(px - qx, py - qy)


class Tela:
    """Glifo in pixel della cella; le forme lavorano in coordinate di pixel (float)."""

    def __init__(self, misura):
        W, H, top, base, x0, x1, tratto = METRICHE[misura]
        self.W, self.H, self.tratto = W, H, tratto
        self.box = (x0, top, x1 + 1, base + 1)           # x0, y0, x1, y1 (esclusi)
        self.forme = []                                  # (segno, funzione dentro(x, y))

    # coordinate unitarie del riquadro delle maiuscole -> pixel
    def p(self, u, v):
        x0, y0, x1, y1 = self.box
        return x0 + u * (x1 - x0), y0 + v * (y1 - y0)

    def quadrato(self):
        """riquadro quadrato centrato nel box, per le forme che non vanno deformate"""
        x0, y0, x1, y1 = self.box
        lato = min(x1 - x0, y1 - y0)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        return cx - lato / 2, cy - lato / 2, lato

    def q(self, u, v):
        x, y, lato = self.quadrato()
        return x + u * lato, y + v * lato

    def poligono(self, pts, segno=1):
        self.forme.append((segno, lambda x, y, pts=pts: _dentro_poligono(x, y, pts)))

    def disco(self, cx, cy, r, segno=1):
        self.forme.append((segno, lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 <= r * r))

    def ellisse(self, cx, cy, rx, ry, ang, segno=1):
        c, s = math.cos(ang), math.sin(ang)

        def f(x, y):
            dx, dy = x - cx, y - cy
            u, v = dx * c + dy * s, -dx * s + dy * c
            return (u / rx) ** 2 + (v / ry) ** 2 <= 1
        self.forme.append((segno, f))

    def linea(self, pts, spessore, segno=1):
        segs = list(zip(pts, pts[1:]))
        r = spessore / 2

        def f(x, y):
            return any(_dist_segmento(x, y, a[0], a[1], b[0], b[1]) <= r for a, b in segs)
        self.forme.append((segno, f))

    def bitmap(self):
        out = []
        n = 8
        for y in range(self.H):
            riga = []
            for x in range(self.W):
                acceso = 0
                for sy in range(n):
                    for sx in range(n):
                        px, py = x + (sx + 0.5) / n, y + (sy + 0.5) / n
                        v = False
                        for segno, f in self.forme:
                            if f(px, py):
                                v = segno > 0
                        acceso += v
                riga.append(1 if acceso * 2 >= n * n else 0)
            out.append(riga)
        return out


def bezier(p0, p1, p2, p3, n=24):
    pts = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        pts.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return pts


def disegna(misura, cp):
    t = Tela(misura)
    s = t.tratto
    if cp == SHARP:
        for u in (0.33, 0.67):
            t.linea([t.p(u, -0.08), t.p(u, 1.08)], s)
        for v in (0.36, 0.76):
            t.poligono([t.p(0.04, v + 0.04), t.p(0.96, v - 0.04), t.p(0.96, v - 0.04 + 0.17),
                        t.p(0.04, v + 0.04 + 0.17)])
    elif cp == FLAT:
        t.linea([t.p(0.18, -0.12), t.p(0.18, 1.0)], s)
        t.linea(bezier(t.p(0.18, 0.56), t.p(0.55, 0.30), t.p(1.05, 0.62), t.p(0.18, 0.99)), s * 1.15)
    elif cp in (DISC, RING, FISHEYE):
        cx, cy = t.q(0.5, 0.5)
        r = t.quadrato()[2] * 0.40
        if cp == DISC:
            t.disco(cx, cy, r)
        else:
            t.disco(cx, cy, r)
            t.disco(cx, cy, r - s * 1.1, -1)
            if cp == FISHEYE:
                t.disco(cx, cy, r * 0.42)
    elif cp == CHECK:
        t.linea([t.q(0.06, 0.55), t.q(0.38, 0.86), t.q(0.96, 0.14)], s * 1.3)
    elif cp == CROSS:
        a = 0.17
        t.poligono([t.q(0.5 - a, 0.06), t.q(0.5 + a, 0.06), t.q(0.5 + a, 0.94), t.q(0.5 - a, 0.94)])
        t.poligono([t.q(0.06, 0.5 - a), t.q(0.94, 0.5 - a), t.q(0.94, 0.5 + a), t.q(0.06, 0.5 + a)])
    elif cp == TRI_R:
        t.poligono([t.q(0.14, 0.06), t.q(0.92, 0.5), t.q(0.14, 0.94)])
    elif cp == TRI_L:
        t.poligono([t.q(0.86, 0.06), t.q(0.08, 0.5), t.q(0.86, 0.94)])
    elif cp == TRI_U:
        t.poligono([t.q(0.04, 0.80), t.q(0.5, 0.18), t.q(0.96, 0.80)])
    elif cp == TRI_D:
        t.poligono([t.q(0.04, 0.20), t.q(0.96, 0.20), t.q(0.5, 0.82)])
    elif cp == SQUARE:
        t.poligono([t.q(0.12, 0.12), t.q(0.88, 0.12), t.q(0.88, 0.88), t.q(0.12, 0.88)])
    elif cp == BAR:
        t.poligono([t.p(0.18, 0.06), t.p(0.56, 0.06), t.p(0.56, 0.94), t.p(0.18, 0.94)])
    elif cp == BOLT:
        t.poligono([t.p(0.62, -0.05), t.p(0.10, 0.58), t.p(0.46, 0.58), t.p(0.30, 1.05),
                    t.p(0.92, 0.38), t.p(0.55, 0.38), t.p(0.80, -0.05)])
    elif cp in (EN_DASH, EM_DASH):
        W = t.W
        a, b = (0.12, 0.88) if cp == EN_DASH else (0.0, 1.0)
        y0 = t.p(0, 0.52)[1]
        x0 = W * a if cp == EM_DASH else t.p(a, 0)[0]
        x1 = W * b if cp == EM_DASH else t.p(b, 0)[0]
        t.poligono([(x0, y0 - s / 2), (x1, y0 - s / 2), (x1, y0 + s / 2), (x0, y0 + s / 2)])
    elif cp == ELLIPSIS:
        for u in (0.12, 0.5, 0.88):
            x, y = t.p(u, 0.9)
            t.disco(x, y, s * 0.9)
    elif cp == STAME:
        stame(t)
    return t.bitmap()


def stame(t):
    """Il marchio: filamento centrale dritto, due laterali ad arco, antere ovali inclinate."""
    s = t.tratto
    base = t.q(0.5, 0.98)
    centro = t.q(0.5, 0.30)
    sx = bezier(base, t.q(0.47, 0.62), t.q(0.22, 0.52), t.q(0.16, 0.36), 16)
    dx = bezier(base, t.q(0.53, 0.62), t.q(0.78, 0.52), t.q(0.84, 0.36), 16)
    t.linea([base, centro], s)
    t.linea(sx, s)
    t.linea(dx, s)
    lato = t.quadrato()[2]
    for (x, y), ang in ((centro, 0.0), (sx[-1], -0.45), (dx[-1], 0.45)):
        t.ellisse(x, y - lato * 0.10, lato * 0.105, lato * 0.17, ang)
    t.linea([t.q(0.30, 0.98), t.q(0.70, 0.98)], s)


def glifo(misura, cp):
    W, H, *_ = METRICHE[misura]
    if misura in A_MANO and cp in A_MANO[misura]:
        riga0, righe = A_MANO[misura][cp]
        px = [[0] * W for _ in range(H)]
        for r, testo in enumerate(righe):
            for c, ch in enumerate(testo):
                if ch == '#' and c < W:
                    px[riga0 + r][c] = 1
        return px
    return disegna(misura, cp)


SIMBOLI = sorted([SHARP, FLAT, DISC, RING, FISHEYE, CHECK, CROSS, TRI_R, TRI_L, TRI_U, TRI_D, SQUARE,
                  BAR, BOLT, ELLIPSIS, STAME, EN_DASH, EM_DASH])


def scrivi(out_dir):
    righe = ['/* font_simboli.c — simboli di Stame nelle celle di Spleen (UI-144).',
             ' * File generato da tools/simboli.py: non modificarlo a mano. */',
             '#include "font.h"', '',
             f'static const uint16_t CP[{len(SIMBOLI)}] STAME_ROM = {{',
             '    ' + ', '.join(f'0x{c:04X}' for c in SIMBOLI) + ',', '};', '']
    for misura, (W, H, top, base, *_rest) in METRICHE.items():
        bpr = (W + 7) // 8
        nome = misura.upper()
        righe.append(f'static const uint8_t BITS_{nome}[{len(SIMBOLI) * H * bpr}] STAME_ROM = {{')
        for cp in SIMBOLI:
            px = glifo(misura, cp)
            byte = []
            for riga in px:
                for b in range(bpr):
                    v = 0
                    for c in range(8):
                        x = b * 8 + c
                        if x < W and riga[x]:
                            v |= 0x80 >> c
                    byte.append(v)
            righe.append('    ' + ', '.join(f'0x{v:02X}' for v in byte) + f',   /* U+{cp:04X} */')
        righe.append('};')
        ascent = base + 1
        righe.append(f'const gfx_font_t GFX_SIMB_{nome} = {{ {W}, {H}, {ascent}, {bpr}, {len(SIMBOLI)}, CP, BITS_{nome} }};')
        righe.append('')
    percorso = os.path.join(out_dir, 'font_simboli.c')
    with open(percorso, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(righe))
    print(f'{percorso}: {len(SIMBOLI)} simboli in {len(METRICHE)} misure')


def mostra(misura):
    W, H, *_ = METRICHE[misura]
    blocchi = [glifo(misura, cp) for cp in SIMBOLI]
    for y in range(H):
        print(f'{y:2d} ' + '  '.join(''.join('#' if b[y][x] else '.' for x in range(W)) for b in blocchi))


if __name__ == '__main__':
    if sys.argv[1] == '--mostra':
        mostra(sys.argv[2])
    else:
        scrivi(sys.argv[1])
