"""genera.py — genera i pezzi del case di Stame da misure.py.

Uso: python -I hardware/case/genera.py            scrive in hardware/case/out/

Laser (SVG in millimetri, 1:1, per LightBurn): rosso = taglio, nero pieno = incisione,
blu = segno leggero. Le scritte usano gli stessi caratteri della plancia: Matrice a punti per le
funzioni principali, Spleen a pixel per le legende piccole. Così il case e lo schermo parlano la
stessa lingua (docs/identita/README.md).
Stampa (STL, PETG): culla della Flip, visiera, vassoio del macro pad, piedini, squadrette, fermo hub.
Dima (SVG da stampare su carta al 100%): la mascherina sopra il contorno della MPK, da provare
prima di tagliare.
"""
import math
import os
import re
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.normpath(os.path.join(QUI, '..', '..'))
sys.path.insert(0, QUI)
sys.path.insert(0, os.path.join(RADICE, 'tools'))
import misure as M                  # noqa: E402
from mesh import Mesh, rett, cerchio  # noqa: E402
from matrice import GLIFI           # noqa: E402

OUT = os.path.join(QUI, 'out')

# ---------------------------------------------------------------------------------------------
# caratteri

def _spleen(misura='8x16'):
    src = open(os.path.join(RADICE, 'src', 'gfx', f'font_spleen_{misura}.c'), encoding='utf-8').read()
    cps = [int(v, 16) for v in re.findall(r'0x([0-9A-F]{4})', src.split('static const uint8_t')[0])]
    bits = [int(v, 16) for v in re.findall(r'0x([0-9A-F]{2})\b', src.split('static const uint8_t')[1].split('};')[0])]
    w, h = (int(v) for v in misura.split('x'))
    bpr = (w + 7) // 8
    glifi = {}
    for i, cp in enumerate(cps):
        righe = []
        for r in range(h):
            row = bits[(i * h + r) * bpr:(i * h + r + 1) * bpr]
            righe.append([(row[c >> 3] >> (7 - (c & 7))) & 1 for c in range(w)])
        glifi[cp] = righe
    return w, h, glifi


SPLEEN = _spleen('8x16')


def matrice_w(testo, passo):
    cols = sum(len(GLIFI.get(ch, GLIFI['?'])[0]) for ch in testo)
    return (cols + len(testo) - 1) * passo if testo else 0


def pixel_w(testo, px):
    return len(testo) * SPLEEN[0] * px


# ---------------------------------------------------------------------------------------------
# SVG per il laser

class Svg:
    def __init__(self, nome, w, h, nota=''):
        self.nome, self.w, self.h, self.nota = nome, w, h, nota
        self.taglio, self.incisione, self.segno = [], [], []

    def _lista(self, livello):
        return {'taglio': self.taglio, 'incisione': self.incisione, 'segno': self.segno}[livello]

    def poligono(self, pts, livello='taglio'):
        d = 'M' + ' L'.join(f'{x:.3f},{y:.3f}' for x, y in pts) + ' Z'
        self._lista(livello).append(f'<path d="{d}"/>')

    def linea(self, pts, livello='segno'):
        """polilinea aperta: solo per i livelli a tratto (taglio, segno)"""
        assert livello != 'incisione', 'nel livello pieno una linea va disegnata con tratto()'
        d = 'M' + ' L'.join(f'{x:.3f},{y:.3f}' for x, y in pts)
        self._lista(livello).append(f'<path d="{d}"/>')

    def tratto(self, pts, w=0.3, livello='incisione'):
        """linea spessa w come poligono pieno (per l'incisione)"""
        for a, b in zip(pts, pts[1:]):
            self.poligono(_contorno_tratto([a, b], w), livello)

    def rett(self, x, y, w, h, r=0.0, livello='taglio'):
        if r > 0:
            self._lista(livello).append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" rx="{r:.3f}" ry="{r:.3f}"/>')
        else:
            self._lista(livello).append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}"/>')

    def cerchio(self, cx, cy, r, livello='taglio'):
        self._lista(livello).append(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}"/>')

    def punti(self, x, base, passo, testo, allinea='sinistra', livello='incisione', diametro=0.78):
        """Matrice: un cerchio per punto acceso; base = linea di base (y in basso)."""
        w = matrice_w(testo, passo)
        if allinea == 'centro':
            x -= w / 2
        elif allinea == 'destra':
            x -= w
        r = passo * diametro / 2
        for ch in testo:
            righe = GLIFI.get(ch, GLIFI['?'])
            gw = len(righe[0])
            for ri, riga in enumerate(righe):
                for ci, c in enumerate(riga):
                    if c == '#':
                        self.cerchio(x + (ci + 0.5) * passo, base + (ri - 7 + 0.5) * passo, r, livello)
            x += (gw + 1) * passo
        return w

    def pixel(self, x, top, px, testo, allinea='sinistra', livello='incisione'):
        """Spleen 8x16: rettangoli per righe di pixel accesi; top = cima della cella."""
        cw, ch, glifi = SPLEEN
        w = pixel_w(testo, px)
        if allinea == 'centro':
            x -= w / 2
        elif allinea == 'destra':
            x -= w
        for k, c in enumerate(testo):
            g = glifi.get(ord(c), glifi.get(ord('?')))
            for r in range(ch):
                c0 = None
                for col in range(cw + 1):
                    on = col < cw and g[r][col]
                    if on and c0 is None:
                        c0 = col
                    elif not on and c0 is not None:
                        self.rett(x + (k * cw + c0) * px, top + r * px, (col - c0) * px, px, livello=livello)
                        c0 = None
        return w

    def salva(self):
        os.makedirs(OUT, exist_ok=True)
        p = os.path.join(OUT, self.nome + '.svg')
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(f'<!-- Stame, {self.nome}: {self.nota} Scala 1:1, millimetri. Rosso taglio, nero incisione, blu segno. -->\n')
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w:.2f}mm" height="{self.h:.2f}mm" '
                    f'viewBox="0 0 {self.w:.3f} {self.h:.3f}">\n')
            f.write(f'<title>Stame — {self.nome}</title>\n')
            f.write('<g id="incisione" fill="#000000" stroke="none">\n' + '\n'.join(self.incisione) + '\n</g>\n')
            f.write('<g id="segno" fill="none" stroke="#0000FF" stroke-width="0.1">\n' + '\n'.join(self.segno) + '\n</g>\n')
            f.write('<g id="taglio" fill="none" stroke="#FF0000" stroke-width="0.1">\n' + '\n'.join(self.taglio) + '\n</g>\n')
            f.write('</svg>\n')
        return p


# ---------------------------------------------------------------------------------------------
# il marchio: tre stami (stesse proporzioni di ui_flip_logo)

def _bez(a, b, c, d, t):
    u = 1 - t
    return (u ** 3 * a[0] + 3 * t * u * u * b[0] + 3 * t * t * u * c[0] + t ** 3 * d[0],
            u ** 3 * a[1] + 3 * t * u * u * b[1] + 3 * t * t * u * c[1] + t ** 3 * d[1])


def _contorno_tratto(pts, w):
    """poligono attorno a una polilinea spessa w (estremi tondi)"""
    sx, dx = [], []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1
        nx, ny = -ty / L * w / 2, tx / L * w / 2
        sx.append((p[0] + nx, p[1] + ny))
        dx.append((p[0] - nx, p[1] - ny))
    def tappo(p, q, verso):
        ang = math.atan2(q[1] - p[1], q[0] - p[0])
        return [(p[0] + w / 2 * math.cos(ang + verso * math.pi / 2 + k * math.pi / 8 * -verso),
                 p[1] + w / 2 * math.sin(ang + verso * math.pi / 2 + k * math.pi / 8 * -verso)) for k in range(9)]
    return sx + list(reversed(dx))


def logo(svg, cx, cy, s, livello='incisione'):
    """Marchio centrato in (cx, cy), alto circa s mm."""
    def Q(u, v):
        return (cx + (u - 0.5) * s, cy + (v - 0.5) * s)
    w = max(s * 0.035, 0.6)
    base = Q(0.5, 0.98)
    curve = [(base, Q(0.47, 0.62), Q(0.22, 0.52), Q(0.16, 0.36)),
             (base, Q(0.50, 0.75), Q(0.50, 0.50), Q(0.50, 0.30)),
             (base, Q(0.53, 0.62), Q(0.78, 0.52), Q(0.84, 0.36))]
    for c in curve:
        pts = [_bez(*c, k / 24) for k in range(25)]
        svg.poligono(_contorno_tratto(pts, w), livello)
    a, b = Q(0.30, 0.98), Q(0.70, 0.98)
    svg.poligono(_contorno_tratto([a, b], w), livello)
    for (tx, ty), ang in ((Q(0.16, 0.36), -0.45), (Q(0.50, 0.30), 0.0), (Q(0.84, 0.36), 0.45)):
        ex, ey = tx, ty - s * 0.10
        rx, ry = s * 0.105, s * 0.17
        pts = []
        for k in range(36):
            t = 2 * math.pi * k / 36
            x, y = rx * math.cos(t), ry * math.sin(t)
            pts.append((ex + x * math.cos(ang) - y * math.sin(ang), ey + x * math.sin(ang) + y * math.cos(ang)))
        svg.poligono(pts, livello)


# ---------------------------------------------------------------------------------------------
# mascherina della MPK

ETICHETTE_K = {'K1': 'SOUND', 'K2': 'PERFORM', 'K3': 'FX', 'K4': 'KEY',
               'K5': 'BASS', 'K6': 'LOOP', 'K7': 'BPM', 'K8': 'VOLUME'}
PAD_SOPRA = {'PAD5': ('DIM', 'LOOP'), 'PAD6': ('MIN', 'BPM'), 'PAD7': ('MAJ', 'OPT'), 'PAD8': ('SUS', 'PUSH')}
PAD_SOTTO = {'PAD1': ('6', 'KEY'), 'PAD2': ('m7', 'BASS'), 'PAD3': ('M7', 'PERF'), 'PAD4': ('9', 'VOIC')}
TRASPORTO = {'REW': '<<', 'FWD': '>>', 'STOP': 'PAUSE', 'PLAY': 'BEAT', 'REC': 'LOOP'}


def foro(svg, nome, ox, oy):
    x, y, tipo = M.MPK_CTRL[nome]
    w, h, r = M.FORO[tipo]
    if tipo in ('k', 'e', 'j'):
        svg.cerchio(x - ox, y - oy, w / 2)
    else:
        svg.rett(x - ox - w / 2, y - oy - h / 2, w, h, r)


def mascherina(lato):
    m = M.MASCHERINA
    x0, x1 = (m['x0'], m['taglio'] - 0.25) if lato == 'sx' else (m['taglio'] + 0.25, m['x1'])
    y0, y1 = m['y0'], m['y1']
    svg = Svg(f'mascherina_{lato}', x1 - x0 + 2, y1 - y0 + 2,
              f'mascherina {"sinistra" if lato == "sx" else "destra"} della MPK, acrilico nero {M.ACR} mm.')
    ox, oy = x0 - 1, y0 - 1          # origine del disegno nel riferimento della MPK
    r = 4.0
    # contorno: angoli tondi solo sui lati esterni
    if lato == 'sx':
        pts = rett(1, 1, x1 - ox, y1 - oy, 0)
        svg.poligono(_angoli(pts, {0: r, 3: r}))
    else:
        pts = rett(1, 1, x1 - ox, y1 - oy, 0)
        svg.poligono(_angoli(pts, {1: r, 2: r}))
    for nome, (x, y, tipo) in M.MPK_CTRL.items():
        if nome in M.SCOPERTI and x0 + 2 < x < x1 - 2:
            foro(svg, nome, ox, oy)
    # i piedini si incollano sotto: le loro posizioni stanno solo sulla dima

    P = 0.5                          # passo dei punti delle manopole: lettere alte 3,5 mm
    for k, nome in ETICHETTE_K.items():
        x, y, _ = M.MPK_CTRL[k]
        if x0 < x < x1:
            base = y + M.FORO['k'][1] / 2 + 1.0 + 7 * P
            svg.punti(x - ox, base - oy, P, nome, 'centro')
    for pad, (nome, riserva) in list(PAD_SOPRA.items()) + list(PAD_SOTTO.items()):
        x, y, _ = M.MPK_CTRL[pad]
        if not (x0 < x < x1):
            continue
        w, h, _ = M.FORO['p']
        sopra = pad in PAD_SOPRA
        Pp = 0.7
        if sopra:
            base = y - h / 2 - 1.2
        else:
            base = y + h / 2 + 1.2 + 7 * Pp
        svg.punti(x - w / 2 - ox, base - oy, Pp, nome, 'sinistra')
        svg.pixel(x + w / 2 - ox, base - oy - 12 * 0.2, 0.2, riserva, 'destra')
    if lato == 'sx':
        for nome, testo in (('PITCH', 'BEND'), ('MOD', 'MOD')):
            x, y, _ = M.MPK_CTRL[nome]
            svg.pixel(x - ox, y + M.FORO['w'][1] / 2 + 1.0 - oy, 0.22, testo, 'centro')
        x, y, _ = M.MPK_CTRL['JOY']
        svg.pixel(x - ox, y + 10.0 - oy, 0.2, 'FOCUS', 'centro')
        # pulsanti coperti (ARP … OCT): qui va il marchio
        logo(svg, 89.5 - ox, 56.0 - oy, 26.0)
        svg.punti(89.5 - ox, 86.5 - oy, 0.45, 'STAME', 'centro')
    else:
        for nome in ('BANK', 'PROG', 'SHIFT'):
            x, y, _ = M.MPK_CTRL[nome]
            svg.pixel(x - ox, y + 4.5 - oy, 0.2, nome, 'centro')
        for nome, testo in TRASPORTO.items():
            x, y, _ = M.MPK_CTRL[nome]
            svg.pixel(x - ox, y + 5.0 - oy, 0.2, testo, 'centro')
        x, y, _ = M.MPK_CTRL['DISP']
        svg.pixel(x - ox, y + 8.0 - oy, 0.2, 'MPK', 'centro')
        # i due pulsanti « » ruotano l'encoder con il fuoco: una parentesi li unisce sopra «TURN»
        xr, xf = M.MPK_CTRL['REW'][0], M.MPK_CTRL['FWD'][0]
        svg.tratto([(xr - ox, 80.6 - oy), (xr - ox, 81.6 - oy), (xf - ox, 81.6 - oy), (xf - ox, 80.6 - oy)], 0.3)
        svg.pixel((xr + xf) / 2 - ox, 82.6 - oy, 0.2, 'TURN', 'centro')
    return svg.salva()


def _angoli(pts, raggi):
    """arrotonda gli spigoli di un rettangolo (indici 0..3) con i raggi dati"""
    out = []
    n = len(pts)
    for i, p in enumerate(pts):
        r = raggi.get(i, 0)
        if not r:
            out.append(p)
            continue
        a, b = pts[i - 1], pts[(i + 1) % n]
        da = (a[0] - p[0], a[1] - p[1])
        db = (b[0] - p[0], b[1] - p[1])
        la, lb = math.hypot(*da), math.hypot(*db)
        ua, ub = (da[0] / la, da[1] / la), (db[0] / lb, db[1] / lb)
        c = (p[0] + (ua[0] + ub[0]) * r, p[1] + (ua[1] + ub[1]) * r)
        s = (p[0] + ua[0] * r, p[1] + ua[1] * r)
        e = (p[0] + ub[0] * r, p[1] + ub[1] * r)
        a0 = math.atan2(s[1] - c[1], s[0] - c[0])
        a1 = math.atan2(e[1] - c[1], e[0] - c[0])
        d = a1 - a0
        while d > math.pi:
            d -= 2 * math.pi
        while d < -math.pi:
            d += 2 * math.pi
        for k in range(9):
            t = a0 + d * k / 8
            out.append((c[0] + r * math.cos(t), c[1] + r * math.sin(t)))
    return out


def dima():
    """mascherina intera sopra il contorno della MPK, da stampare su carta al 100%"""
    m = M.MASCHERINA
    svg = Svg('dima_mascherina', M.MPK['w'] + 20, 125,
              'dima 1:1 della mascherina sul contorno della MPK; stampare al 100%, controllare il righello.')
    ox, oy = -10, -10
    svg.rett(0 - ox, 0 - oy, M.MPK['w'], M.MPK['d'] * 0 + 100, 0, 'segno')       # retro della MPK fino ai tasti
    svg.linea([(0 - ox, M.MPK_KEYBED_Y - oy), (M.MPK['w'] - ox, M.MPK_KEYBED_Y - oy)], 'segno')
    for nome, (x, y, tipo) in M.MPK_CTRL.items():
        svg.cerchio(x - ox, y - oy, 1.0, 'segno')            # centro dei controlli [D]
        if nome in M.SCOPERTI:
            foro(svg, nome, ox, oy)
    svg.rett(m['x0'] - ox, m['y0'] - oy, m['x1'] - m['x0'], m['y1'] - m['y0'], 4, 'taglio')
    svg.linea([(m['taglio'] - ox, m['y0'] - oy), (m['taglio'] - ox, m['y1'] - oy)], 'segno')
    # piedini sotto la mascherina: qui la MPK deve essere piana e senza pulsanti
    for (px, py) in M.PIEDINI:
        svg.cerchio(px - ox, py - oy, M.MASCHERINA['piede_d'] / 2, 'segno')
        svg.cerchio(px - ox, py - oy, 0.6, 'incisione')
    # righello di controllo: 100 mm
    svg.tratto([(10 - ox, 108 - oy), (110 - ox, 108 - oy)], 0.3)
    for k in range(11):
        svg.tratto([(10 + k * 10 - ox, 106 - oy), (10 + k * 10 - ox, 110 - oy)], 0.3)
    svg.pixel(120 - ox, 104 - oy, 0.35, '100 mm: misurare dopo la stampa')
    svg.pixel(120 - ox, 112 - oy, 0.35, 'cerchi blu: piedini sotto la mascherina')
    return svg.salva()


# ---------------------------------------------------------------------------------------------
# ponte posteriore: sopra (inclinato 15°), fronte, retro, centine

def z_ponte(y):
    """altezza del piano superiore del ponte alla profondità y"""
    return M.PONTE_Z_FRONT + (M.PONTE_Y[1] - y) * math.tan(math.radians(M.INCLINAZIONE))


X_INT = (M.FIANCO, M.LARGHEZZA - M.FIANCO)     # fra i fianchi
GIUNTA_SOPRA = 310.0
GIUNTA_FRONTE = 265.0
GIUNTA_RETRO = 310.0
TASCA_FLIP = (M.FLIP['w'] + 8.0, M.FLIP['d'] + 7.6)   # la culla stampata scende qui dentro


def ponte_sopra(lato):
    L = (M.PONTE_Y[1] - M.PONTE_Y[0]) / math.cos(math.radians(M.INCLINAZIONE))
    a, b = (X_INT[0], GIUNTA_SOPRA - 0.2) if lato == 'sx' else (GIUNTA_SOPRA + 0.2, X_INT[1])
    svg = Svg(f'ponte_sopra_{lato}', b - a + 2, L + 2, f'piano del ponte, inclinato di {M.INCLINAZIONE:.0f}°, compensato {M.PLY} mm.')
    # v = 0 sul bordo davanti (vicino al musicista), cresce verso il retro; nel disegno il davanti sta in basso
    def P(x, v):
        return (x - a + 1, L - v + 1)
    svg.poligono([P(a, 0), P(b, 0), P(b, L), P(a, L)])
    # le centine stanno sotto, incollate e fermate con le squadrette: niente asole in vista
    if lato == 'sx':
        tw, td = TASCA_FLIP
        x, y = P(M.FLIP_X - tw / 2, 6.0 + td)
        svg.rett(x, y, tw, td, 2.0)
        # legende dei tasti della Flip ai lati della tasca: tasto in negativo, funzione accanto
        px = 0.3
        sx = [('L1 R1', 'FOCUS'), ('+', 'TURN'), ('A', 'PRESS'), ('B', 'BACK')]
        dx = [('X', 'PUSH'), ('Y', 'BS.VOIC'), ('SEL', 'OPTIONS'), ('START', 'BPM'), ('MENU', 'MENU')]
        xs = M.FLIP_X - tw / 2 - 4
        for i, (k, f) in enumerate(sx):
            x, y = P(xs, 82.0 - i * 9)
            w = svg.pixel(x, y, px, f, 'destra')
            svg.pixel(x - w - 2.4, y, px, k, 'destra')
        xd = M.FLIP_X + tw / 2 + 4
        for i, (k, f) in enumerate(dx):
            x, y = P(xd, 82.0 - i * 9)
            w = svg.pixel(x, y, px, k)
            svg.pixel(x + w + 2.4, y, px, f)
        # marchio, nome e classe a sinistra, lontani dalle legende
        cx, cy = P(40.0, 52.0)
        logo(svg, cx, cy, 34.0)
        x, y = P(63.0, 50.0)
        svg.punti(x, y, 1.45, 'STAME')
        x, y = P(63.0, 37.0)
        svg.pixel(x, y, 0.28, 'STAMEN HARMONICUM')
        x, y = P(63.0, 30.0)
        svg.pixel(x, y, 0.28, 'CLASSIS TRIANDRIA')
    else:
        # griglia di aerazione a nido d'ape sopra il vano dei cavi: un ricordo delle radio d'epoca
        passo = 6.0
        for j in range(9):
            for i in range(40):
                x = 340.0 + i * passo + (passo / 2 if j % 2 else 0)
                v = 18.0 + j * passo * 0.866
                if 336 < x < 560 and v < 85:
                    svg.cerchio(*P(x, v), 1.6)
        x, y = P(M.LARGHEZZA - M.FIANCO - 6.0, 46.0)
        svg.pixel(x, y, 0.28, 'TAB. I', 'destra')
    return svg.salva()


def ponte_fronte(lato):
    a, b = (X_INT[0], GIUNTA_FRONTE - 0.2) if lato == 'sx' else (GIUNTA_FRONTE + 0.2, X_INT[1])
    h = M.PONTE_Z_FRONT - M.BASE_T - M.PLY * math.cos(math.radians(M.INCLINAZIONE))
    svg = Svg(f'ponte_fronte_{lato}', b - a + 2, h + 2, f'fronte del ponte, compensato {M.PLY} mm.')
    def P(x, z):
        return (x - a + 1, h - (z - M.BASE_T) + 1)
    svg.poligono([P(a, M.BASE_T), P(b, M.BASE_T), P(b, M.BASE_T + h), P(a, M.BASE_T + h)])
    # bocca per i connettori della MPK (CASE-004, CASE-012)
    c0 = M.MPK_X0 + M.MPK_CONN_X[0] - 14
    c1 = M.MPK_X0 + M.MPK_CONN_X[1] + 14
    if lato == 'dx':
        x, y = P(max(c0, a + 6), M.BASE_T + 34)
        svg.rett(x, y, min(c1, b - 6) - max(c0, a + 6), 31, 4)
    return svg.salva()


def ponte_retro(lato):
    a, b = (X_INT[0], GIUNTA_RETRO - 0.2) if lato == 'sx' else (GIUNTA_RETRO + 0.2, X_INT[1])
    h = z_ponte(M.PONTE_Y[0]) - M.BASE_T - M.PLY
    svg = Svg(f'ponte_retro_{lato}', b - a + 2, h + 2, f'retro del ponte, compensato {M.PLY} mm.')
    def P(x, z):
        return (x - a + 1, h - (z - M.BASE_T) + 1)
    svg.poligono([P(a, M.BASE_T), P(b, M.BASE_T), P(b, M.BASE_T + h), P(a, M.BASE_T + h)])
    # uscite dei cavi (alimentazione, audio della Flip)
    for cx in ((120.0, 230.0) if lato == 'sx' else (420.0, 540.0)):
        x, y = P(cx - 14, M.BASE_T + 16)
        svg.rett(x, y, 28, 12, 6)
    return svg.salva()


def centine():
    """centine interne del ponte (profilo yz): reggono il piano e uniscono le due metà"""
    svg = Svg('centine', 3 * 104 + 6, 90, f'{len(M.CENTINE_X)} centine del ponte, compensato {M.PLY} mm.')
    for k in range(len(M.CENTINE_X)):
        ox = 2 + k * 104
        y0, y1 = M.PONTE_Y[0] + M.PLY, M.PONTE_Y[1] - M.PLY
        zt = lambda y: z_ponte(y) - M.PLY / math.cos(math.radians(M.INCLINAZIONE))
        H = zt(y0) - M.BASE_T
        def P(y, z):
            return (ox + (y - y0), 2 + H - (z - M.BASE_T))
        svg.poligono([P(y1, M.BASE_T), P(y0, M.BASE_T), P(y0, zt(y0)), P(y1, zt(y1))])
        # passaggio per i cavi in basso
        x, y = P((y0 + y1) / 2 + 15, M.BASE_T + 22)
        svg.rett(x, y, 30, 18, 6)
    return svg.salva()


# ---------------------------------------------------------------------------------------------
# fianchi

def profilo_fianco():
    """profilo (y, z) del fianco, dal retro in basso in senso antiorario"""
    Y = M.BASE_Y1
    zb = z_ponte(0) + 2
    pts = [(0.0, 0.0), (Y, 0.0), (Y, 30.0)]
    for k in range(1, 9):                         # angolo tondo davanti, raggio 10
        t = math.radians(90 * k / 8)
        pts.append((Y - 10 + 10 * math.cos(t), 30 + 10 * math.sin(t)))
    zf = lambda y: M.BASE_T + M.MPK['h_back'] - (y - M.MPK_Y0) / M.MPK['d'] * (M.MPK['h_back'] - M.MPK['h_front'])
    pts += [(190.0, zf(190.0) + M.MASCHERINA['piede_h'] + M.ACR + 2.0), (M.PONTE_Y[1], M.PONTE_Z_FRONT + 2.0)]
    for k in range(0, 9):                         # angolo tondo dietro, raggio 6: finisce in (0, zb - 6)
        t = math.radians(90 + 90 * k / 8)
        pts.append((6 + 6 * math.cos(t), zb - 6 + 6 * math.sin(t)))
    return pts


def fianco(lato, strato):
    prof = profilo_fianco()
    H = max(z for _, z in prof)
    Y = M.BASE_Y1
    esterno = strato == 'esterno'
    svg = Svg(f'fianco_{lato}_{strato}' if esterno else 'fianco_interno', Y + 2, H + 2,
              (f'fianco {"sinistro" if lato == "sx" else "destro"}, strato esterno con le incisioni'
               if esterno else f'strato interno dei fianchi: tagliarne {2 * (M.FIANCO_STRATI - 1)}') +
              f', compensato {M.PLY} mm.')
    # sulla faccia esterna del fianco sinistro il davanti sta a sinistra: si specchia
    sp = lato == 'sx'
    def P(y, z):
        u = (Y - y) if sp else y
        return (u + 1, H - z + 1)
    svg.poligono([P(y, z) for y, z in prof])
    # fori per le viti delle squadrette (base e ponte): solo negli strati interni, la faccia
    # esterna resta intera
    if not esterno:
        for y, z in ((30.0, 10.0), (150.0, 10.0), (260.0, 10.0), (20.0, 40.0), (80.0, 30.0)):
            svg.cerchio(*P(y, z), 1.25)
    if esterno:
        # targhetta: marchio verso il retro, nome e classe verso il davanti
        cx, cy = P(40.0, 42.0)
        logo(svg, cx, cy, 34.0)
        ytxt = 75.0
        x, y = P(ytxt if not sp else ytxt, 32.0)
        if sp:
            svg.punti(x, y, 1.5, 'STAME', 'destra')
            svg.pixel(x, y + 3, 0.28, 'STAMEN HARMONICUM', 'destra')
        else:
            svg.punti(x, y, 1.5, 'STAME')
            svg.pixel(x, y + 3, 0.28, 'STAMEN HARMONICUM')
    return svg.salva()


# ---------------------------------------------------------------------------------------------
# base e cartellino del macro pad

def base(lato):
    a, b = (M.FIANCO, GIUNTA_SOPRA) if lato == 'sx' else (GIUNTA_SOPRA, M.LARGHEZZA - M.FIANCO)
    Y = M.BASE_Y1
    svg = Svg(f'base_{lato}', b - a + 14, Y + 2, f'base, compensato {M.BASE_T} mm; le due metà si incastrano a coda di rondine.')
    def P(x, y):
        return (x - a + 1, y + 1)
    # giunta a coda di rondine: due code sulla metà sinistra
    code = []
    for yc in (60.0, 200.0):
        code.append(yc)
    def bordo_giunta(verso):
        pts = []
        ys = [0.0]
        for yc in code:
            ys += [yc - 14, yc - 18, yc + 18, yc + 14]
        ys.append(Y)
        pts = []
        x0 = GIUNTA_SOPRA
        k = 0
        for i, y in enumerate(ys):
            if i == 0 or i == len(ys) - 1:
                pts.append((x0, y))
            else:
                j = (i - 1) % 4
                dx = 10.0 if j in (1, 2) else 0.0
                pts.append((x0 + dx, y))
        return pts
    if lato == 'sx':
        pts = [P(a, 0)] + [P(x, y) for x, y in bordo_giunta(1)] + [P(a, Y)]
    else:
        pts = [P(b, Y), P(b, 0)] + [P(x, y) for x, y in bordo_giunta(1)][::-1][::-1]
        pts = [P(b, 0), P(b, Y)] + [P(x, y) for x, y in reversed(bordo_giunta(1))]
    svg.poligono(pts)
    # piedini in gomma e viti delle squadrette
    for x, y in ((M.FIANCO + 25, 20), (M.FIANCO + 25, Y - 20), (M.LARGHEZZA - M.FIANCO - 25, 20),
                 (M.LARGHEZZA - M.FIANCO - 25, Y - 20), (GIUNTA_SOPRA - 30, 20), (GIUNTA_SOPRA - 30, Y - 20)):
        if a < x < b:
            svg.cerchio(*P(x, y), 6.0, 'segno')
    for x in (M.FIANCO + 12, M.LARGHEZZA - M.FIANCO - 12):
        for y in (30.0, 150.0, 260.0):
            if a < x < b:
                svg.cerchio(*P(x, y), 1.7)
    # area della MPK e del macro pad (segno per la posa)
    if lato == 'sx':
        svg.rett(*P(M.MPK_X0, M.MPK_Y0), GIUNTA_SOPRA - M.MPK_X0 - 1, M.MPK['d'], 0, 'segno')
    else:
        svg.rett(*P(GIUNTA_SOPRA + 11, M.MPK_Y0), M.MPK_X0 + M.MPK['w'] - GIUNTA_SOPRA - 11, M.MPK['d'], 0, 'segno')
        svg.rett(*P(M.PAD_X0, M.MPK_Y0), M.POD_W, M.MPK['d'], 0, 'segno')
    return svg.salva()


PROFILO_DIVISORIO = [(100.0, 0.0), (284.0, 0.0), (284.0, 24.0), (278.0, 34.0), (190.0, 42.0), (100.0, 46.5)]


def divisorio():
    """listello fra la MPK e il vano del macro pad: copre la guancia rossa e unisce il piano"""
    H = max(z for _, z in PROFILO_DIVISORIO)
    svg = Svg('divisorio', 190.0, H + 2, f'divisorio fra MPK e macro pad, compensato {M.PLY} mm; sta sulla base.')
    svg.poligono([(y - 99.0, H + 1 - z) for y, z in PROFILO_DIVISORIO])
    for y in (130.0, 250.0):                                   # viti delle squadrette
        svg.cerchio(y - 99.0, H + 1 - 6.0, 1.25)
    return svg.salva()


LEGENDA_PAD = [['SOUND', 'PERFORM', 'FX', 'KEY'], ['BASS', 'LOOP', 'BPM', 'VOLUME'],
               ['OPTIONS', 'BACK', 'MENU', 'PANIC']]


def cartellino_pad():
    """coperchio del vano dietro il macro pad: la mappa dei 12 tasti e delle 3 manopole"""
    W, H = M.POD_W - 4, 72.0
    svg = Svg('cartellino_pad', W + 2, H + 2, f'coperchio del vano del macro pad con la sua legenda, acrilico nero {M.ACR} mm.')
    svg.rett(1, 1, W, H, 4)
    for x, y in ((5, 5), (W - 3, 5), (5, H - 3), (W - 3, H - 3)):
        svg.cerchio(x, y, 1.7)
    # manopole: un anello inciso con la tacca, la funzione sotto
    for cx, r, sotto in ((24, 9, 'VOICING'), (60, 6.5, 'BASS V.'), (94, 6.5, 'LIST')):
        anello = [(cx + r * math.cos(2 * math.pi * k / 48), 16 + r * math.sin(2 * math.pi * k / 48)) for k in range(49)]
        svg.tratto(anello, 0.5)
        svg.tratto([(cx, 16 - r + 1.2), (cx, 16 - r + 3.6)], 0.6)
        svg.pixel(cx, 16 + r + 2, 0.22, sotto, 'centro')
    # tasti T1–T12: la griglia del macro pad, con il nome della funzione
    for r, riga in enumerate(LEGENDA_PAD):
        for c, nome in enumerate(riga):
            x, y = 10 + c * 26.5, 36 + r * 11.0
            svg.tratto([(x, y), (x + 24, y), (x + 24, y + 9.4), (x, y + 9.4), (x, y)], 0.25)
            svg.pixel(x + 12, y + 1.4, 0.2, f'T{r * 4 + c + 1}', 'centro')
            svg.pixel(x + 12, y + 4.8, 0.2, nome, 'centro')
    return svg.salva()


# ---------------------------------------------------------------------------------------------
# tavola d'insieme (vista dall'alto e fianco), non va al laser

def zf_mpk(y):
    """altezza del pannello della MPK alla profondità y (profilo a cuneo)"""
    return M.BASE_T + M.MPK['h_back'] - (y - M.MPK_Y0) / M.MPK['d'] * (M.MPK['h_back'] - M.MPK['h_front'])


def flip_aperta():
    """sagome (y, z) della Flip aperta nella culla: metà con i tasti sul piano a 15°, schermo a 70°,
    e la visiera attorno allo schermo"""
    a15, a70 = math.radians(M.INCLINAZIONE), math.radians(70)
    d, t = M.FLIP['d'], M.FLIP['half']
    # spigolo davanti in basso della metà con i tasti, affondata nella culla
    y0 = M.PONTE_Y[1] - 6.0
    z0 = z_ponte(y0) - t + 1.0
    u = (-math.cos(a15), math.sin(a15))          # lungo il piano, verso il retro
    n = (math.sin(a15), math.cos(a15))           # perpendicolare al piano, verso l'alto
    b0 = (y0, z0)
    b1 = (y0 + u[0] * d, z0 + u[1] * d)
    b2 = (b1[0] + n[0] * t, b1[1] + n[1] * t)
    b3 = (y0 + n[0] * t, z0 + n[1] * t)
    sotto = [b0, b1, b2, b3]
    # schermo: cerniera sullo spigolo posteriore, sale inclinato all'indietro
    h = b2
    v = (-math.cos(a70), math.sin(a70))          # lungo lo schermo
    w = (math.sin(a70), math.cos(a70))           # normale dello schermo, verso il musicista
    s1 = (h[0] + v[0] * d, h[1] + v[1] * d)
    sopra = [h, s1, (s1[0] - w[0] * t, s1[1] - w[1] * t), (h[0] - w[0] * t, h[1] - w[1] * t)]
    vis = [(h[0] + w[0] * 2, h[1] + w[1] * 2), (s1[0] + w[0] * 2 + v[0] * 4, s1[1] + w[1] * 2 + v[1] * 4),
           (s1[0] + w[0] * 26 + v[0] * 4, s1[1] + w[1] * 26 + v[1] * 4), (h[0] + w[0] * 26, h[1] + w[1] * 26)]
    return sotto, sopra, vis


def tavola():
    W, Y = M.LARGHEZZA, M.BASE_Y1
    svg = Svg('tavola_insieme', W + 40, Y + 230, 'tavola d\'insieme: vista dall\'alto e fianco; non è un pezzo da tagliare.')
    ox, oy = 20, 20
    def T(x, y):
        return (x + ox, y + oy)
    # ---- vista dall'alto ----
    svg.rett(*T(0, 0), M.FIANCO, Y, 2, 'taglio')
    svg.rett(*T(W - M.FIANCO, 0), M.FIANCO, Y, 2, 'taglio')
    svg.rett(*T(M.FIANCO, 0), W - 2 * M.FIANCO, M.PONTE_Y[1], 0, 'taglio')
    svg.rett(*T(M.MPK_X0, M.MPK_Y0), M.MPK['w'], M.MPK['d'], 3, 'segno')
    for k in range(37):                                       # tasti della MPK
        x = M.MPK_X0 + 13 + k * (M.MPK['w'] - 26) / 37
        svg.linea([T(x, M.MPK_Y0 + M.MPK_KEYBED_Y + 2), T(x, M.MPK_Y0 + M.MPK['d'] - 6)], 'segno')
    m = M.MASCHERINA
    svg.rett(*T(M.MPK_X0 + m['x0'], M.MPK_Y0 + m['y0']), m['taglio'] - m['x0'], m['y1'] - m['y0'], 4, 'taglio')
    svg.rett(*T(M.MPK_X0 + m['taglio'], M.MPK_Y0 + m['y0']), m['x1'] - m['taglio'], m['y1'] - m['y0'], 4, 'taglio')
    for nome, (x, y, tipo) in M.MPK_CTRL.items():
        if nome in M.SCOPERTI:
            w, h, r = M.FORO[tipo]
            if tipo in ('k', 'e', 'j'):
                svg.cerchio(*T(M.MPK_X0 + x, M.MPK_Y0 + y), w / 2, 'segno')
            else:
                svg.rett(*T(M.MPK_X0 + x - w / 2, M.MPK_Y0 + y - h / 2), w, h, r, 'segno')
    svg.rett(*T(M.PAD_X0 + 2, M.MPK_Y0 + 2), M.POD_W - 4, 66, 4, 'taglio')                 # cartellino
    svg.rett(*T(M.PAD_X0 + (M.POD_W - M.PAD['w']) / 2, M.MPK_Y0 + 74), M.PAD['w'], M.PAD['d'], 6, 'segno')
    for r in range(3):
        for c in range(4):
            svg.rett(*T(M.PAD_X0 + 26 + c * 19.5 - 8.75, M.MPK_Y0 + 74 + 39 + r * 19.5 - 8.75 + 8), 17.5, 17.5, 2, 'segno')
    tw, td = TASCA_FLIP
    dy = td * math.cos(math.radians(M.INCLINAZIONE))
    svg.rett(*T(M.FLIP_X - tw / 2, M.PONTE_Y[1] - 6 - dy), tw, dy, 2, 'segno')
    for txt, x, y in (('PONTE', 30, 60), ('MASCHERINA', M.MPK_X0 + 150, M.MPK_Y0 + 95),
                      ('MPK MINI PLUS', M.MPK_X0 + 160, M.MPK_Y0 + 150), ('FLIP', M.FLIP_X - 8, 40),
                      ('CARTELLINO', M.PAD_X0 + 30, M.MPK_Y0 + 30), ('MACRO PAD', M.PAD_X0 + 30, M.MPK_Y0 + 82),
                      ('GRIGLIA', 420, 45)):
        svg.pixel(*T(x, y), 0.45, txt)
    svg.pixel(*T(0, Y + 8), 0.7, f'VISTA DALL\'ALTO   {W:.0f} x {Y:.0f} mm')

    # ---- vista di fianco (da destra: il musicista sta a destra) ----
    z_max = 175.0
    oy2 = oy + Y + 40
    def S(y, z):
        return (y + ox, oy2 + z_max - z)
    prof = profilo_fianco()
    svg.poligono([S(y, z) for y, z in prof], 'taglio')
    svg.poligono([S(0, 0), S(Y, 0), S(Y, M.BASE_T), S(0, M.BASE_T)], 'segno')
    svg.poligono([S(M.PONTE_Y[0], M.BASE_T), S(M.PONTE_Y[1], M.BASE_T), S(M.PONTE_Y[1], M.PONTE_Z_FRONT),
                  S(M.PONTE_Y[0], z_ponte(M.PONTE_Y[0]))], 'segno')
    y1 = M.MPK_Y0 + M.MPK['d']
    svg.poligono([S(M.MPK_Y0, M.BASE_T), S(y1, M.BASE_T), S(y1, zf_mpk(y1)), S(M.MPK_Y0, zf_mpk(M.MPK_Y0))], 'segno')
    for x, _y, tipo in M.MPK_CTRL.values():                        # manopole sopra il pannello
        if tipo == 'k' and x == 340.0:
            yk = M.MPK_Y0 + _y
            svg.poligono([S(yk - 9.5, zf_mpk(yk)), S(yk + 9.5, zf_mpk(yk)), S(yk + 9.5, zf_mpk(yk) + 14.5),
                          S(yk - 9.5, zf_mpk(yk) + 14.5)], 'segno')
    pm0, pm1 = M.MPK_Y0 + m['y0'], M.MPK_Y0 + m['y1']
    zp = lambda y: zf_mpk(y) + m['piede_h']
    svg.poligono([S(pm0, zp(pm0)), S(pm1, zp(pm1)), S(pm1, zp(pm1) + M.ACR), S(pm0, zp(pm0) + M.ACR)], 'taglio')
    sotto, sopra, vis = flip_aperta()
    svg.poligono([S(*p) for p in sotto], 'taglio')
    svg.poligono([S(*p) for p in sopra], 'taglio')
    svg.poligono([S(*p) for p in vis], 'segno')
    # sguardo del musicista, da 60 cm
    svg.linea([S(sopra[0][0] + 20, (sopra[0][1] + sopra[1][1]) / 2), S(Y + 10, 150)], 'segno')
    for txt, y, z in (('PONTE 15 GRADI', 10, 30), ('MPK', 200, 20), ('MASCHERINA', 120, 60),
                      ('FLIP 70 GRADI', -10, 168), ('VISIERA', 60, 160), ('SGUARDO', 230, 158)):
        svg.pixel(*S(y, z), 0.45, txt)
    alt = max(p[1] for p in sopra)
    svg.pixel(*S(0, -14), 0.7, f'FIANCO   ALTEZZA CON LO SCHERMO APERTO {alt:.0f} mm')
    return svg.salva()


# ---------------------------------------------------------------------------------------------
# pezzi stampati

def culla_flip():
    """La Flip chiusa entra di 12 mm; aperta, la metà con i tasti resta nella culla.
    Pareti aperte dietro (porte USB-C, [V]) e sui lati (tasti del volume, [V])."""
    tw, td = TASCA_FLIP
    gi = 0.4
    fx0, fy0, fx1, fy1 = -(M.FLIP['w'] / 2 + 0.6), 0.0, M.FLIP['w'] / 2 + 0.6, M.FLIP['d'] + 1.0
    ex0, ey0, ex1, ey1 = -(tw / 2 - gi), -2.6, tw / 2 - gi, td - 2.6 - gi
    ms = Mesh('Stame culla della Flip')
    ms.box(ex0, ey0, 0, ex1, ey1, 2.0)                                # fondo
    ms.prisma(rett(ex0 - 4, ey0 - 4, ex1 + 4, ey1 + 4, 3), 14.0, 16.0,
              holes=[rett(fx0, fy0, fx1, fy1, 1.5)])                  # flangia sul piano del ponte
    # pareti: davanti bassa (i tasti restano liberi), dietro con la finestra delle porte
    ms.box(ex0, ey0, 2.0, ex1, fy0, 6.0)                              # labbro davanti
    ms.box(ex0, fy1, 2.0, -24.0, ey1, 14.0)                           # dietro, a sinistra della finestra
    ms.box(24.0, fy1, 2.0, ex1, ey1, 14.0)                            # dietro, a destra
    for x0, x1 in ((ex0, fx0), (fx1, ex1)):                           # lati con una finestra di 40 mm
        ms.box(x0, ey0, 2.0, x1, 20.0, 14.0)
        ms.box(x0, 60.0, 2.0, x1, ey1, 14.0)
    return ms


def visiera():
    """Visiera attorno allo schermo aperto: due fianchi e un tettuccio, come la cappa degli
    oscilloscopi. Si avvita al piano del ponte dietro la culla; lo schermo non tocca nulla."""
    ms = Mesh('Stame visiera')
    w_int = M.FLIP['w'] + 6.0
    sp = 3.0
    alt = 78.0                                    # lungo lo schermo
    prof = 24.0                                   # profondità della visiera
    # stampata sdraiata: x = larghezza, y = lungo lo schermo, z = profondità
    ms.box(-w_int / 2 - sp, 0, 0, -w_int / 2, alt, prof)
    ms.box(w_int / 2, 0, 0, w_int / 2 + sp, alt, prof)
    ms.box(-w_int / 2 - sp, alt, 0, w_int / 2 + sp, alt + sp, prof)
    # piedi a cuneo (55° fra visiera e piano del ponte) con il foro della vite
    for sx in (-1, 1):
        x0 = sx * (w_int / 2 + sp / 2) - 6
        ms.prisma(rett(x0, -12, x0 + 12, 0, 2), 0, 4.0, holes=[cerchio(x0 + 6, -6, 1.7, 24)])
    return ms


def piedino():
    ms = Mesh('Stame piedino della mascherina')
    ms.cilindro(0, 0, 0, M.MASCHERINA['piede_h'], M.MASCHERINA['piede_d'] / 2, 48)
    return ms


def squadretta():
    ms = Mesh('Stame squadretta M3')
    ms.prisma(rett(0, 0, 20, 12), 0, 3.0, holes=[cerchio(10, 6, 1.7, 24)])
    # seconda ala in piedi (piano xz): si scambiano y e z, che è una riflessione, quindi si
    # inverte anche il verso dei triangoli
    ala = Mesh('ala')
    ala.prisma(rett(0, 0, 20, 12), 0, 3.0, holes=[cerchio(10, 6, 1.7, 24)])
    for g in ala.gusci:
        ms.gusci.append([tuple((p[0], p[2], p[1]) for p in t)[::-1] for t in g])
    # rinforzo a triangolo
    ms.prisma_x([(3, 3), (12, 3), (3, 12)], 8.5, 11.5)
    return ms


def vassoio_pad():
    """vassoio che solleva il macro pad: i tasti arrivano all'altezza della mascherina [V]"""
    ms = Mesh('Stame vassoio del macro pad')
    W, D = M.POD_W - 2, M.MPK['d'] - 74
    pw, pd = M.PAD['w'] + 0.8, M.PAD['d'] + 0.8
    rialzo = 8.0
    ms.prisma(rett(0, 0, W, D, 4), 0, rialzo, holes=[rett(W / 2 - 30, D / 2 - 30, W / 2 + 30, D / 2 + 30, 6)])
    ms.prisma(rett(0, 0, W, D, 4), rialzo, rialzo + 10,
              holes=[rett((W - pw) / 2, (D - pd) / 2, (W + pw) / 2, (D + pd) / 2, 3)])
    return ms


def fermo_hub():
    ms = Mesh('Stame fermo dell\'hub')
    w, d, h = M.HUB['w'] + 0.8, M.HUB['d'] + 0.8, M.HUB['h']
    ms.prisma(rett(-3, -3, w + 3, d + 3, 2), 0, 2.0)
    ms.prisma(rett(-3, -3, w + 3, d + 3, 2), 2.0, h * 0.6, holes=[rett(0, 0, w, d, 1)])
    for x in (-10, w + 10):
        ms.prisma(rett(x - 6, d / 2 - 6, x + 6, d / 2 + 6, 3), 0, 2.0, holes=[cerchio(x, d / 2, 1.7, 24)])
    return ms


def colonnina():
    """colonnina del cartellino: lo tiene all'altezza della mascherina, sopra l'hub"""
    ms = Mesh('Stame colonnina del cartellino')
    ms.prisma(cerchio(0, 0, 3.5, 40), 0, 35.0, holes=[cerchio(0, 0, 1.25, 24)])
    return ms


STAMPA = {
    'culla_flip': (culla_flip, 1), 'visiera': (visiera, 1), 'piedino_mascherina': (piedino, len(M.PIEDINI)),
    'squadretta_m3': (squadretta, 12), 'vassoio_pad': (vassoio_pad, 1), 'fermo_hub': (fermo_hub, 1),
    'colonnina': (colonnina, 4),
}


# ---------------------------------------------------------------------------------------------

def main():
    os.makedirs(OUT, exist_ok=True)
    laser = [mascherina('sx'), mascherina('dx'), dima(),
             ponte_sopra('sx'), ponte_sopra('dx'), ponte_fronte('sx'), ponte_fronte('dx'),
             ponte_retro('sx'), ponte_retro('dx'), centine(),
             fianco('sx', 'esterno'), fianco('dx', 'esterno'), fianco('sx', 'interno'),
             base('sx'), base('dx'), divisorio(), cartellino_pad(), tavola()]
    print('LASER (SVG 1:1, mm)')
    for p in laser:
        txt = open(p, encoding='utf-8').read()
        w = float(re.search(r'width="([0-9.]+)mm"', txt).group(1))
        h = float(re.search(r'height="([0-9.]+)mm"', txt).group(1))
        sta = w <= M.LASER_BED[0] and h <= M.LASER_BED[1]
        nota = '' if sta or 'dima' in p or 'tavola' in p else '  NON STA NEL PIANO DEL LASER'
        print(f'  {os.path.basename(p):28s} {w:6.1f} x {h:6.1f}{nota}')
    print('STAMPA (STL)')
    for nome, (f, n) in STAMPA.items():
        ms = f()
        ok = ms.controlla()
        (x0, y0, z0), (x1, y1, z1) = ms.ingombro()
        tri = ms.salva(os.path.join(OUT, nome + '.stl'))
        sta = (x1 - x0) <= M.PRINT_BED[0] and (y1 - y0) <= M.PRINT_BED[1]
        print(f'  {nome + ".stl":28s} {x1 - x0:6.1f} x {y1 - y0:6.1f} x {z1 - z0:5.1f}  x{n:<3d} '
              f'{tri:5d} triangoli  {"chiuso" if ok else "GUSCIO APERTO"}{"" if sta else "  NON STA NEL PIANO"}')


if __name__ == '__main__':
    main()
