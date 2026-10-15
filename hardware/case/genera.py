"""genera.py — genera i pezzi del case di Stame da misure.py (bozza 3, 15/10/2026).

Uso: python -I hardware/case/genera.py            scrive in hardware/case/out/

Laser (SVG in millimetri, 1:1, per LightBurn): rosso = taglio, nero pieno = incisione,
blu = segno leggero. Le scritte usano gli stessi caratteri della plancia: Matrice a punti per le
funzioni principali, Spleen a pixel per le legende piccole. Così il case e lo schermo parlano la
stessa lingua (docs/identita/README.md).
Stampa (STL, PETG): culla della Flip, cornice del macro pad, visiera, piedini, squadrette, fermo hub.
Dima (SVG da stampare su carta al 100%): la mascherina sopra il contorno della MK4, da provare
prima di tagliare.

Composizione: MK4 a sinistra fra i fianchi; a destra la torre, con la mensola della Flip dietro
(vano dell'hub sotto, cartellino del pad sul davanti) e il macro pad davanti, in linea con i tasti.
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
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
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
    """poligono attorno a una polilinea spessa w"""
    sx, dx = [], []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1
        nx, ny = -ty / L * w / 2, tx / L * w / 2
        sx.append((p[0] + nx, p[1] + ny))
        dx.append((p[0] - nx, p[1] - ny))
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


def _angoli(pts, raggi):
    """arrotonda gli spigoli di un poligono (indici) con i raggi dati"""
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


# ---------------------------------------------------------------------------------------------
# mascherina della MK4 (CASE-030, CASE-031): un pezzo solo, con le legende di Stame

ETICHETTE_K = {'K1': 'SOUND', 'K2': 'PERFORM', 'K3': 'FX', 'K4': 'KEY',
               'K5': 'BASS', 'K6': 'LOOP', 'K7': 'BPM', 'K8': 'VOLUME'}
PAD_SOPRA = {'PAD5': 'DIM', 'PAD6': 'MIN', 'PAD7': 'MAJ', 'PAD8': 'SUS'}
PAD_SOTTO = {'PAD1': ('6', 'B:KEY'), 'PAD2': ('m7', 'B:BASS'), 'PAD3': ('M7', 'B:PERF'), 'PAD4': ('9', 'B:VOIC')}
TRASPORTO = {'UNDO': 'UNDO', 'LOOP': 'PAUSE', 'PLAY': 'BEAT', 'REC': 'LOOP', 'DUB': 'DUB'}
PULSANTI = {'SHIFT': 'PUSH', 'MINUS': 'BACK', 'PLUS': 'MENU'}


def foro(svg, nome, ox, oy):
    x, y, tipo = M.MK4_CTRL[nome]
    w, h, r = M.FORO[tipo]
    if tipo in ('k', 'e'):
        svg.cerchio(x - ox, y - oy, w / 2)
    else:
        svg.rett(x - ox - w / 2, y - oy - h / 2, w, h, r)


def mascherina():
    m = M.MASCHERINA
    x0, x1, y0, y1 = m['x0'], m['x1'], m['y0'], m['y1']
    svg = Svg('mascherina', x1 - x0 + 2, y1 - y0 + 2, f'mascherina della MK4, acrilico nero {M.ACR} mm, un pezzo solo.')
    ox, oy = x0 - 1, y0 - 1          # origine del disegno nel riferimento della MK4
    svg.poligono(_angoli(rett(1, 1, x1 - ox, y1 - oy, 0), {0: 4.0, 1: 4.0, 2: 4.0, 3: 4.0}))
    for nome in M.MK4_CTRL:
        if nome in M.SCOPERTI:
            foro(svg, nome, ox, oy)
    # i piedini si incollano sotto: le loro posizioni stanno solo sulla dima

    P = 0.5                          # passo dei punti delle manopole: lettere alte 3,5 mm
    for k, nome in ETICHETTE_K.items():
        x, y, _ = M.MK4_CTRL[k]
        base = y + M.FORO['k'][1] / 2 + 1.0 + 7 * P
        svg.punti(x - ox, base - oy, P, nome, 'centro')
    # pad: la fila alta ha i nomi nello spazio fra le due file (3 mm), la fila bassa sotto, con la
    # riserva del banco B in piccolo
    hp = M.FORO['p'][1]
    for pad, nome in PAD_SOPRA.items():
        x, y, _ = M.MK4_CTRL[pad]
        gap0 = y + hp / 2
        gap1 = M.MK4_CTRL['PAD1'][1] - hp / 2
        svg.pixel(x - ox, (gap0 + gap1) / 2 - 1.44 - oy, 0.18, nome, 'centro')
    for pad, (nome, riserva) in PAD_SOTTO.items():
        x, y, _ = M.MK4_CTRL[pad]
        Pp = 0.55
        base = y + hp / 2 + 1.2 + 7 * Pp
        svg.punti(x - ox, base - oy, Pp, nome, 'centro')
        svg.pixel(x - ox, base + 1.2 - oy, 0.15, riserva, 'centro')
    for nome, testo in (('PITCH', 'BEND'), ('MOD', 'MOD')):
        x, y, _ = M.MK4_CTRL[nome]
        svg.pixel(x - ox, y + M.FORO['w'][1] / 2 + 1.5 - oy, 0.2, testo, 'centro')
    x, y, _ = M.MK4_CTRL['NAV']
    svg.pixel(x - ox, y + M.FORO['e'][1] / 2 + 1.5 - oy, 0.2, 'LIST', 'centro')
    for nome, testo in PULSANTI.items():
        x, y, _ = M.MK4_CTRL[nome]
        svg.pixel(x - ox, y + M.FORO['b'][1] / 2 + 1.5 - oy, 0.2, testo, 'centro')
    for nome, testo in TRASPORTO.items():
        x, y, _ = M.MK4_CTRL[nome]
        svg.pixel(x - ox, y + M.FORO['b'][1] / 2 + 1.5 - oy, 0.2, testo, 'centro')
    # i pulsanti OCT, coperti, lasciano posto al marchio piccolo e al nome
    logo(svg, 38.0 - ox, 80.0 - oy, 11.0)
    svg.punti(38.0 - ox, 91.5 - oy, 0.35, 'STAME', 'centro')
    return svg.salva()


def dima():
    """mascherina sopra il contorno della MK4, da stampare su carta al 100%"""
    m = M.MASCHERINA
    svg = Svg('dima_mascherina', M.MK4['w'] + 20, 130,
              'dima 1:1 della mascherina sul contorno della MK4; stampare al 100%, controllare il righello.')
    ox, oy = -10, -10
    svg.rett(0 - ox, 0 - oy, M.MK4['w'], 104, 0, 'segno')                   # retro della MK4 fino ai tasti
    svg.linea([(0 - ox, M.MK4_KEYBED_Y - oy), (M.MK4['w'] - ox, M.MK4_KEYBED_Y - oy)], 'segno')
    for nome, (x, y, tipo) in M.MK4_CTRL.items():
        svg.cerchio(x - ox, y - oy, 1.0, 'segno')                           # centro dei controlli [D]
        if nome in M.SCOPERTI:
            foro(svg, nome, ox, oy)
        else:
            w, h, r = M.FORO[tipo]
            svg.rett(x - ox - w / 2, y - oy - h / 2, w, h, r, 'segno')      # coperto: solo segno
    svg.rett(m['x0'] - ox, m['y0'] - oy, m['x1'] - m['x0'], m['y1'] - m['y0'], 4, 'taglio')
    # piedini sotto la mascherina: qui la MK4 deve essere piana e senza pulsanti
    for (px, py) in M.PIEDINI:
        svg.cerchio(px - ox, py - oy, M.MASCHERINA['piede_d'] / 2, 'segno')
        svg.cerchio(px - ox, py - oy, 0.6, 'incisione')
    # righello di controllo: 100 mm
    svg.tratto([(10 - ox, 112 - oy), (110 - ox, 112 - oy)], 0.3)
    for k in range(11):
        svg.tratto([(10 + k * 10 - ox, 110 - oy), (10 + k * 10 - ox, 114 - oy)], 0.3)
    svg.pixel(120 - ox, 108 - oy, 0.35, '100 mm: misurare dopo la stampa')
    svg.pixel(120 - ox, 116 - oy, 0.35, 'cerchi blu: piedini sotto la mascherina; rettangoli blu: pulsanti coperti')
    return svg.salva()


# ---------------------------------------------------------------------------------------------
# telaio: retro, fianchi, base, divisorio

X_INT = (M.FIANCO, M.LARGHEZZA - M.FIANCO)     # fra i fianchi


def retro(lato):
    """listello del retro: chiude la zona dei cavi, con le uscite"""
    a, b = (X_INT[0], M.GIUNTA - 0.2) if lato == 'sx' else (M.GIUNTA + 0.2, X_INT[1])
    h = 30.0
    svg = Svg(f'retro_{lato}', b - a + 2, h + 2, f'listello del retro, compensato {M.PLY} mm, alto {h:.0f}; sta sulla base.')
    def P(x, z):
        return (x - a + 1, h - z + 1)
    svg.poligono([P(a, 0), P(b, 0), P(b, h), P(a, h)])
    # uscite dei cavi: alimentazione della Flip, audio, pedale
    for cx in ((120.0, 230.0) if lato == 'sx' else (400.0, 500.0)):
        x, y = P(cx - 14, 20)
        svg.rett(x, y, 28, 12, 6)
    for x in (a + 12, b - 12):                                 # viti delle squadrette
        svg.cerchio(*P(x, 8), 1.25)
    return svg.salva()


def profilo_fianco():
    """profilo (y, z) del fianco, dal retro in basso in senso antiorario"""
    Y = M.BASE_Y1
    zf, zb = M.FIANCO_Z['front'], M.FIANCO_Z['back']
    pts = [(0.0, 0.0), (Y, 0.0), (Y, zf - 10.0)]
    for k in range(1, 9):                         # angolo tondo davanti, raggio 10
        t = math.radians(90 * k / 8)
        pts.append((Y - 10 + 10 * math.cos(t), zf - 10 + 10 * math.sin(t)))
    pts += [(M.FIANCO_Z['y_front'], zf), (M.FIANCO_Z['y_back'], zb)]
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
    sp = lato == 'sx'                             # sulla faccia esterna del fianco sinistro il davanti sta a sinistra
    def P(y, z):
        u = (Y - y) if sp else y
        return (u + 1, H - z + 1)
    svg.poligono([P(y, z) for y, z in prof])
    if not esterno:                               # viti delle squadrette, solo negli strati interni
        for y, z in ((20.0, 10.0), (130.0, 10.0), (230.0, 10.0), (20.0, 40.0), (100.0, 40.0)):
            svg.cerchio(*P(y, z), 1.25)
    if esterno:                                   # targhetta: marchio verso il retro, nome verso il davanti
        cx, cy = P(40.0, 30.0)
        logo(svg, cx, cy, 28.0)
        x, y = P(72.0, 22.0)
        if sp:
            svg.punti(x, y, 1.3, 'STAME', 'destra')
            svg.pixel(x, y + 3, 0.26, 'STAMEN HARMONICUM', 'destra')
        else:
            svg.punti(x, y, 1.3, 'STAME')
            svg.pixel(x, y + 3, 0.26, 'STAMEN HARMONICUM')
    return svg.salva()


def _bordo_giunta(Y):
    """profilo della giunta a coda di rondine della base, dal retro al davanti (due code)"""
    ys = [0.0]
    for yc in (60.0, 190.0):
        ys += [yc - 14, yc - 18, yc + 18, yc + 14]
    ys.append(Y)
    pts = []
    for i, y in enumerate(ys):
        if i == 0 or i == len(ys) - 1:
            pts.append((M.GIUNTA, y))
        else:
            j = (i - 1) % 4
            pts.append((M.GIUNTA + (10.0 if j in (1, 2) else 0.0), y))
    return pts


def base(lato):
    a, b = (M.FIANCO, M.GIUNTA) if lato == 'sx' else (M.GIUNTA, M.LARGHEZZA - M.FIANCO)
    Y = M.BASE_Y1
    svg = Svg(f'base_{lato}', b - a + 14, Y + 2, f'base, compensato {M.BASE_T} mm; le due metà si incastrano a coda di rondine.')
    def P(x, y):
        return (x - a + 1, y + 1)
    giunta = _bordo_giunta(Y)
    if lato == 'sx':
        pts = [P(a, 0)] + [P(x, y) for x, y in giunta] + [P(a, Y)]
    else:
        pts = [P(b, 0), P(b, Y)] + [P(x, y) for x, y in reversed(giunta)]
    svg.poligono(pts)
    # piedini in gomma e viti delle squadrette
    for x, y in ((M.FIANCO + 25, 20), (M.FIANCO + 25, Y - 20), (M.LARGHEZZA - M.FIANCO - 25, 20),
                 (M.LARGHEZZA - M.FIANCO - 25, Y - 20), (M.GIUNTA - 30, 20), (M.GIUNTA - 30, Y - 20)):
        if a < x < b:
            svg.cerchio(*P(x, y), 6.0, 'segno')
    for x in (M.FIANCO + 12, M.DIV_X + M.PLY / 2, M.LARGHEZZA - M.FIANCO - 12):
        for y in (20.0, 130.0, 230.0):
            if a < x < b:
                svg.cerchio(*P(x, y), 1.7)
    # segni per la posa: MK4, divisorio, torre (mensola e pad), hub
    def area(x0, y0, w, h, r=0.0):
        xa, xb = max(x0, a + 0.5), min(x0 + w, b - 0.5)
        if xb > xa:
            svg.rett(*P(xa, y0), xb - xa, h, r if xa == x0 and xb == x0 + w else 0, 'segno')
    area(M.MK4_X0, M.MK4_Y0, M.MK4['w'], M.MK4['d'], 3)
    area(M.DIV_X, M.MK4_Y0, M.PLY, M.MK4['d'])
    area(M.TORRE_X0, M.MENSOLA_Y[0], M.TORRE_W, M.MENSOLA_Y[1] - M.MENSOLA_Y[0] + M.PLY)
    area(M.PAD_X0, M.PAD_Y0, M.PAD['w'], M.PAD['d'], 4)
    area(M.FLIP_X - M.HUB['w'] / 2, M.MENSOLA_Y[0] + 30, M.HUB['w'], M.HUB['d'], 2)
    return svg.salva()


def divisorio():
    """parete fra la MK4 e la torre: copre il fianco della MK4, regge la mensola, lascia passare i cavi"""
    y0, y1 = M.MK4_Y0, M.MK4_Y0 + MK4_D()
    z1 = M.MENSOLA_Z
    svg = Svg('divisorio', y1 - y0 + 2, z1 - M.BASE_T + 2, f'divisorio fra MK4 e torre, compensato {M.PLY} mm; sta sulla base.')
    def P(y, z):
        return (y - y0 + 1, z1 - z + 1)
    pts = [(y0, 20.0), (y0 + 26.0, 20.0), (y0 + 26.0, M.BASE_T), (y1, M.BASE_T), (y1, z1), (y0, z1)]   # passaggio dei cavi dietro
    svg.poligono([P(y, z) for y, z in pts])
    for y in (y0 + 60.0, y0 + 150.0):                             # viti delle squadrette
        svg.cerchio(*P(y, M.BASE_T + 8.0), 1.25)
    return svg.salva()


def MK4_D():
    return M.MK4['d']


# ---------------------------------------------------------------------------------------------
# torre: piano della mensola, pareti davanti e dietro, cartellino del pad

def torre_piano():
    """piano della mensola della Flip, con la tasca della culla; sotto c'è il vano dell'hub"""
    W, D = M.TORRE_W, M.MENSOLA_Y[1] - M.MENSOLA_Y[0]
    svg = Svg('torre_piano', W + 2, D + 2, f'piano della mensola della Flip, compensato {M.BASE_T} mm; la culla stampata scende nella tasca.')
    def P(x, y):
        return (x - M.TORRE_X0 + 1, y - M.MENSOLA_Y[0] + 1)
    svg.poligono([P(M.TORRE_X0, M.MENSOLA_Y[0]), P(M.TORRE_X1, M.MENSOLA_Y[0]), P(M.TORRE_X1, M.MENSOLA_Y[1]), P(M.TORRE_X0, M.MENSOLA_Y[1])])
    tw, td = M.TASCA_FLIP
    x, y = P(M.FLIP_X - tw / 2, M.MENSOLA_Y[0] + M.PLY)
    svg.rett(x, y, tw, td, 2.0)
    for x in (M.TORRE_X0 + 10, M.TORRE_X1 - 10):                   # viti verso le pareti
        for y in (M.MENSOLA_Y[0] + 6, M.MENSOLA_Y[1] - 6):
            svg.cerchio(*P(x, y), 1.7)
    x, y = P(M.TORRE_X0 + 6, M.MENSOLA_Y[1] - 9)
    svg.pixel(x, y, 0.22, 'TAB. I')
    return svg.salva()


def torre_parete(dove):
    """pareti della mensola: davanti (porta il cartellino, passaggio del cavo del pad) e dietro
    (passaggio dei cavi dell'hub: OTG della Flip, MK4)"""
    W, H = M.TORRE_W, M.MENSOLA_Z - M.BASE_T
    svg = Svg(f'torre_{dove}', W + 2, H + 2, f'parete {"davanti" if dove == "fronte" else "dietro"} della mensola, compensato {M.PLY} mm.')
    def P(x, z):
        return (x - M.TORRE_X0 + 1, H - (z - M.BASE_T) + 1)
    pts = [(M.TORRE_X0, M.BASE_T), (M.TORRE_X1, M.BASE_T), (M.TORRE_X1, M.MENSOLA_Z), (M.TORRE_X0, M.MENSOLA_Z)]
    svg.poligono([P(x, z) for x, z in pts])
    if dove == 'fronte':
        cx = M.PAD_X0 + M.PAD_USB_X                                 # il cavo del pad entra nel vano
        x, y = P(cx - 10, M.BASE_T + 12)
        svg.rett(x, y, 20, 12, 4)
        c = M.CARTELLINO
        for x in (M.TORRE_X0 + 8, M.TORRE_X1 - 8):                 # viti del cartellino
            for z in (M.BASE_T + 6, M.BASE_T + c['h'] - 4):
                svg.cerchio(*P(x, z), 1.25)
    else:
        x, y = P(M.FLIP_X - 20, M.BASE_T + 16)                      # cavi: OTG della Flip e USB della MK4
        svg.rett(x, y, 40, 14, 5)
    return svg.salva()


# la mappa del macro pad: fila alta, in mezzo, in basso (specifica 40 §8.10, MIDI-131, MIDI-132)
LEGENDA_PAD = [[('T1', 'SOUND'), ('T2', 'PERFORM'), ('T3', 'FX'), ('T4', 'KEY'), ('T13', 'LOCK')],
               [('T5', 'BASS'), ('T6', 'LOOP'), ('T7', 'BPM'), ('T8', 'VOLUME'), ('T14', 'VIEW')],
               [('T9', 'OPTIONS'), ('T10', 'BACK'), ('T11', 'MENU'), ('T12', 'PANIC'), ('T15', 'PAGE')]]
MANOPOLE_PAD = {'m1': ('BASS VOIC', 'PERFORM'), 'm2': ('LIST', 'KEY'), 'M': ('CHORD VOIC', 'SOUND')}


def cartellino_pad():
    """striscia di acrilico sulla parete davanti della mensola: la mappa dei 15 tasti e delle 3
    manopole del macro pad, nello stesso ordine in cui stanno sul pad; dopo la barra, il mestiere
    con il Lock acceso"""
    W, H = M.CARTELLINO['w'], M.CARTELLINO['h']
    svg = Svg('cartellino_pad', W + 2, H + 2, f'cartellino del macro pad, acrilico nero {M.ACR} mm; si avvita sulla parete davanti della mensola.')
    svg.rett(1, 1, W, H, 3)
    for x in (8.0, W - 8.0):
        for y in (4.5, H - 4.5):
            svg.cerchio(x + 1, y + 1, 1.7)
    # i 15 tasti: 5 colonne da 22 mm, 3 righe da 10
    cw, ch = 22.0, 10.0
    x0, y0 = 14.0, 3.0
    for r, riga in enumerate(LEGENDA_PAD):
        for c, (sigla, nome) in enumerate(riga):
            x, y = x0 + c * (cw + 1.5), y0 + r * ch
            svg.tratto([(x, y), (x + cw, y), (x + cw, y + ch - 1.2), (x, y + ch - 1.2), (x, y)], 0.25)
            svg.pixel(x + 2.0, y + 1.0, 0.16, sigla)
            svg.pixel(x + cw - 2.0, y + 1.0, 0.16, nome, 'destra')
            if sigla in ('T13', 'T14', 'T15'):                      # le aggiunte di Stame: riquadro pieno
                svg.tratto([(x + 1.2, y + ch - 2.6), (x + cw - 1.2, y + ch - 2.6)], 0.5)
    # le manopole, disposte come sul pad: due piccole in alto, la grande in basso
    kx = x0 + 5 * (cw + 1.5) + 4.0
    for nome, (cx, cy, r) in (('m1', (kx + 6, 9.0, 4.0)), ('m2', (kx + 30, 9.0, 4.0)), ('M', (kx + 18, 25.0, 6.0))):
        anello = [(cx + r * math.cos(2 * math.pi * k / 40), cy + r * math.sin(2 * math.pi * k / 40)) for k in range(41)]
        svg.tratto(anello, 0.45)
        svg.tratto([(cx, cy - r + 0.8), (cx, cy - r + 2.4)], 0.6)
        svg.pixel(cx, cy - 1.3, 0.16, nome, 'centro')
    svg.pixel(kx + 6, 15.0, 0.14, MANOPOLE_PAD['m1'][0], 'centro')
    svg.pixel(kx + 30, 15.0, 0.14, MANOPOLE_PAD['m2'][0], 'centro')
    svg.pixel(kx + 18, 32.0, 0.14, MANOPOLE_PAD['M'][0], 'centro')
    svg.pixel(kx + 18, 2.0, 0.14, 'LOCK: ' + ' '.join(MANOPOLE_PAD[k][1] for k in ('M', 'm1', 'm2')), 'centro')
    return svg.salva()


# ---------------------------------------------------------------------------------------------
# tavola d'insieme (vista dall'alto e fianco), non va al laser

def flip_aperta():
    """sagome (y, z) della Flip aperta sulla mensola: metà con i tasti in piano nella culla, schermo
    a SCHERMO_DEG dall'orizzontale verso il retro, e la visiera attorno allo schermo"""
    a = math.radians(M.SCHERMO_DEG)
    d, t = M.FLIP['d'], M.FLIP['half']
    z0 = M.MENSOLA_Z + 2.0                       # fondo della culla
    y1 = M.FLIP_Y0                               # bordo dietro (cerniera)
    y0 = y1 + d                                  # bordo davanti
    sotto = [(y0, z0), (y1, z0), (y1, z0 + t), (y0, z0 + t)]
    h = (y1, z0 + t)                             # cerniera
    v = (-math.cos(a), math.sin(a))              # lungo lo schermo, verso l'alto e il retro
    w = (math.sin(a), math.cos(a))               # normale dello schermo, verso il musicista
    s1 = (h[0] + v[0] * d, h[1] + v[1] * d)
    sopra = [h, s1, (s1[0] - w[0] * t, s1[1] - w[1] * t), (h[0] - w[0] * t, h[1] - w[1] * t)]
    vis = [(h[0] + w[0] * 2, h[1] + w[1] * 2), (s1[0] + w[0] * 2 + v[0] * 4, s1[1] + w[1] * 2 + v[1] * 4),
           (s1[0] + w[0] * 26 + v[0] * 4, s1[1] + w[1] * 26 + v[1] * 4), (h[0] + w[0] * 26, h[1] + w[1] * 26)]
    return sotto, sopra, vis


def tavola():
    W, Y = M.LARGHEZZA, M.BASE_Y1
    svg = Svg('tavola_insieme', W + 40, Y + 300, 'tavola d\'insieme: vista dall\'alto e fianco; non è un pezzo da tagliare.')
    ox, oy = 20, 20
    def T(x, y):
        return (x + ox, y + oy)
    # ---- vista dall'alto ----
    svg.rett(*T(0, 0), M.FIANCO, Y, 2, 'taglio')
    svg.rett(*T(W - M.FIANCO, 0), M.FIANCO, Y, 2, 'taglio')
    svg.rett(*T(M.FIANCO, 0), W - 2 * M.FIANCO, M.PLY, 0, 'taglio')                     # retro
    svg.rett(*T(M.MK4_X0, M.MK4_Y0), M.MK4['w'], M.MK4['d'], 3, 'segno')
    for k in range(16):                                                                 # tasti della MK4
        x = M.MK4_X0 + 6 + k * (M.MK4['w'] - 12) / 15
        svg.linea([T(x, M.MK4_Y0 + M.MK4_KEYBED_Y + 2), T(x, M.MK4_Y0 + M.MK4['d'] - 4)], 'segno')
    m = M.MASCHERINA
    svg.rett(*T(M.MK4_X0 + m['x0'], M.MK4_Y0 + m['y0']), m['x1'] - m['x0'], m['y1'] - m['y0'], 4, 'taglio')
    for nome, (x, y, tipo) in M.MK4_CTRL.items():
        if nome in M.SCOPERTI:
            w, h, r = M.FORO[tipo]
            if tipo in ('k', 'e'):
                svg.cerchio(*T(M.MK4_X0 + x, M.MK4_Y0 + y), w / 2, 'segno')
            else:
                svg.rett(*T(M.MK4_X0 + x - w / 2, M.MK4_Y0 + y - h / 2), w, h, r, 'segno')
    svg.rett(*T(M.DIV_X, M.MK4_Y0), M.PLY, M.MK4['d'], 0, 'taglio')                      # divisorio
    # torre: mensola con la tasca e la Flip, cartellino, pad con tasti e manopole
    svg.rett(*T(M.TORRE_X0, M.MENSOLA_Y[0]), M.TORRE_W, M.MENSOLA_Y[1] - M.MENSOLA_Y[0] + M.PLY, 0, 'taglio')
    tw, td = M.TASCA_FLIP
    svg.rett(*T(M.FLIP_X - tw / 2, M.MENSOLA_Y[0] + M.PLY), tw, td, 2, 'segno')
    svg.rett(*T(M.FLIP_X - M.FLIP['w'] / 2, M.FLIP_Y0), M.FLIP['w'], M.FLIP['d'], 3, 'segno')
    sch = M.FLIP['d'] * math.cos(math.radians(M.SCHERMO_DEG))
    svg.rett(*T(M.FLIP_X - M.FLIP['w'] / 2, M.FLIP_Y0 - sch), M.FLIP['w'], sch, 3, 'segno')   # schermo, in proiezione
    svg.rett(*T(M.TORRE_X0 + 2, M.TORRE_FRONTE_Y + M.PLY), M.CARTELLINO['w'], M.ACR, 0, 'taglio')
    svg.rett(*T(M.PAD_X0, M.PAD_Y0), M.PAD['w'], M.PAD['d'], 5, 'segno')
    for r in range(3):
        for c in range(5):
            cx = M.PAD_X0 + M.PAD['k0'][0] + c * M.PAD['pitch_x']
            cy = M.PAD_Y0 + M.PAD['k0'][1] + r * M.PAD['pitch_y']
            svg.rett(*T(cx - 8, cy - 8), 16, 16, 1.5, 'segno')
    for nome, (kx, ky, kr) in M.PAD_KNOB.items():
        svg.cerchio(*T(M.PAD_X0 + kx, M.PAD_Y0 + ky), kr, 'segno')
    for txt, x, y in (('MPK MINI IV', M.MK4_X0 + 150, M.MK4_Y0 + 150), ('MASCHERINA', M.MK4_X0 + 150, M.MK4_Y0 + 100),
                      ('FLIP', M.FLIP_X - 10, M.MENSOLA_Y[0] - 22), ('MENSOLA', M.TORRE_X0 + 4, M.MENSOLA_Y[1] - 12),
                      ('CARTELLINO', M.TORRE_X0 + 4, M.TORRE_FRONTE_Y + 12), ('MACRO PAD', M.PAD_X0 + 2, M.PAD_Y0 + M.PAD['d'] + 4),
                      ('CAVI', 40, 12), ('DIVISORIO', M.DIV_X - 44, M.MK4_Y0 + 180)):
        svg.pixel(*T(x, y), 0.45, txt)
    svg.pixel(*T(0, Y + 8), 0.7, f'VISTA DALL\'ALTO   {W:.0f} x {Y:.0f} mm')

    # ---- vista di fianco (da destra: il musicista sta a destra) ----
    z_max = 240.0
    oy2 = oy + Y + 40
    def S(y, z):
        return (y + ox, oy2 + z_max - z)
    prof = profilo_fianco()
    svg.poligono([S(y, z) for y, z in prof], 'taglio')
    svg.poligono([S(0, 0), S(Y, 0), S(Y, M.BASE_T), S(0, M.BASE_T)], 'segno')
    svg.poligono([S(0, M.BASE_T), S(M.PLY, M.BASE_T), S(M.PLY, M.BASE_T + 30), S(0, M.BASE_T + 30)], 'segno')
    # la MK4 (dietro la torre, in questa vista): corpo, tasti e mascherina
    y0, y1 = M.MK4_Y0, M.MK4_Y0 + M.MK4['d']
    zt = M.BASE_T + M.MK4['h']
    yk = M.MK4_Y0 + M.MK4_KEYBED_Y
    svg.poligono([S(y0, M.BASE_T), S(y1, M.BASE_T), S(y1, M.BASE_T + M.MK4['key_top']), S(yk, M.BASE_T + M.MK4['key_top']),
                  S(yk, zt), S(y0, zt)], 'segno')
    for _n, (x, y, tipo) in M.MK4_CTRL.items():
        if tipo == 'k' and x == M.MK4_CTRL['K1'][0]:
            yk2 = M.MK4_Y0 + y
            svg.poligono([S(yk2 - 9.5, zt), S(yk2 + 9.5, zt), S(yk2 + 9.5, M.BASE_T + M.MK4['h_knobs']),
                          S(yk2 - 9.5, M.BASE_T + M.MK4['h_knobs'])], 'segno')
    pm0, pm1 = M.MK4_Y0 + m['y0'], M.MK4_Y0 + m['y1']
    zp = zt + m['piede_h']
    svg.poligono([S(pm0, zp), S(pm1, zp), S(pm1, zp + M.ACR), S(pm0, zp + M.ACR)], 'segno')
    # la torre: vano, mensola, pareti, cartellino, culla, Flip, visiera, pad sulla cornice
    svg.poligono([S(M.MENSOLA_Y[0], M.BASE_T), S(M.MENSOLA_Y[1] + M.PLY, M.BASE_T), S(M.MENSOLA_Y[1] + M.PLY, M.MENSOLA_Z),
                  S(M.MENSOLA_Y[0], M.MENSOLA_Z)], 'taglio')
    svg.poligono([S(M.MENSOLA_Y[0], M.MENSOLA_Z - M.BASE_T), S(M.MENSOLA_Y[1] + M.PLY, M.MENSOLA_Z - M.BASE_T),
                  S(M.MENSOLA_Y[1] + M.PLY, M.MENSOLA_Z), S(M.MENSOLA_Y[0], M.MENSOLA_Z)], 'segno')
    hy = M.MENSOLA_Y[0] + 30
    svg.poligono([S(hy, M.BASE_T), S(hy + M.HUB['d'], M.BASE_T), S(hy + M.HUB['d'], M.BASE_T + M.HUB['h']), S(hy, M.BASE_T + M.HUB['h'])], 'segno')
    cy0 = M.TORRE_FRONTE_Y + M.PLY
    svg.poligono([S(cy0, M.BASE_T), S(cy0 + M.ACR, M.BASE_T), S(cy0 + M.ACR, M.BASE_T + M.CARTELLINO['h']), S(cy0, M.BASE_T + M.CARTELLINO['h'])], 'taglio')
    sotto, sopra, vis = flip_aperta()
    svg.poligono([S(*p) for p in sotto], 'taglio')
    svg.poligono([S(*p) for p in sopra], 'taglio')
    svg.poligono([S(*p) for p in vis], 'segno')
    py0, py1 = M.PAD_Y0, M.PAD_Y0 + M.PAD['d']
    svg.poligono([S(py0, M.BASE_T), S(py1, M.BASE_T), S(py1, M.BASE_T + M.PAD['h']), S(py0, M.BASE_T + M.PAD['h'])], 'taglio')
    svg.poligono([S(py0 - 6, M.BASE_T), S(py1 + 6, M.BASE_T), S(py1 + 6, M.BASE_T + 8), S(py0 - 6, M.BASE_T + 8)], 'segno')
    # sguardo del musicista: occhi a 60 cm, 35 cm sopra il tavolo
    sc = ((sopra[0][0] + sopra[1][0]) / 2, (sopra[0][1] + sopra[1][1]) / 2)
    ey, ez = Y + 500.0, 350.0
    k = (Y + 40 - sc[0]) / (ey - sc[0])
    svg.linea([S(*sc), S(sc[0] + (ey - sc[0]) * k, sc[1] + (ez - sc[1]) * k)], 'segno')
    for txt, y, z in (('MK4', 150, 20), ('MASCHERINA', 60, 56), ('MENSOLA', 48, 50), ('HUB', 76, 10),
                      (f'SCHERMO {M.SCHERMO_DEG:.0f} GRADI', -8, 150), ('VISIERA', 40, 140), ('PAD', 170, 42),
                      ('CARTELLINO', 150, 60), ('SGUARDO 60 CM', 210, 125)):
        svg.pixel(*S(y, z), 0.45, txt)
    alt = max(p[1] for p in sopra)
    svg.pixel(*S(0, -14), 0.7, f'FIANCO   ALTEZZA CON LO SCHERMO APERTO {alt:.0f} mm   CENTRO DELLO SCHERMO A {sc[1]:.0f} mm')
    return svg.salva()


# ---------------------------------------------------------------------------------------------
# pezzi stampati

def culla_flip():
    """La metà con i tasti della Flip sta in piano nella culla, che scende nella tasca della mensola.
    Davanti il labbro è basso e ha due intagli per il jack e la USB-C di sotto (ricarica) [V];
    dietro la finestra per la USB-C di sopra (OTG, verso l'hub) [V]; ai lati le finestre per i
    tasti del volume [V]."""
    tw, td = M.TASCA_FLIP
    gi = 0.4
    fx0, fy0, fx1, fy1 = -(M.FLIP['w'] / 2 + 0.6), 0.0, M.FLIP['w'] / 2 + 0.6, M.FLIP['d'] + 1.0
    ex0, ey0, ex1, ey1 = -(tw / 2 - gi), -2.6, tw / 2 - gi, td - 2.6 - gi
    ms = Mesh('Stame culla della Flip')
    ms.box(ex0, ey0, 0, ex1, ey1, 2.0)                                # fondo
    ms.prisma(rett(ex0 - 4, ey0 - 4, ex1 + 4, ey1 + 4, 3), 14.0, 16.0,
              holes=[rett(fx0, fy0, fx1, fy1, 1.5)])                  # flangia sul piano della mensola
    # labbro davanti, basso, con gli intagli del jack e della USB-C [V: posizioni]
    for x0, x1 in ((ex0, -18.0), (-8.0, -4.0), (10.0, ex1)):
        ms.box(x0, ey0, 2.0, x1, fy0, 6.0)
    # dietro: la finestra della porta OTG, al centro
    ms.box(ex0, fy1, 2.0, -24.0, ey1, 14.0)
    ms.box(24.0, fy1, 2.0, ex1, ey1, 14.0)
    for x0, x1 in ((ex0, fx0), (fx1, ex1)):                           # lati con una finestra di 40 mm
        ms.box(x0, ey0, 2.0, x1, 20.0, 14.0)
        ms.box(x0, 60.0, 2.0, x1, ey1, 14.0)
    return ms


def cornice_pad():
    """cornice che tiene fermo il macro pad sulla base, con l'intaglio per il cavo USB-C dietro"""
    ms = Mesh('Stame cornice del macro pad')
    pw, pd = M.PAD['w'] + 0.8, M.PAD['d'] + 0.8
    s, h = 6.0, 8.0
    ms.box(-s, -s, 0, 0, pd + s, h)                                   # sinistra
    ms.box(pw, -s, 0, pw + s, pd + s, h)                              # destra
    ms.box(0, pd, 0, pw, pd + s, h)                                   # davanti
    ux = M.PAD_USB_X
    ms.box(0, -s, 0, ux - 10, 0, h)                                   # dietro, a sinistra dell'intaglio
    ms.box(ux + 10, -s, 0, pw, 0, h)                                  # dietro, a destra
    return ms


def visiera():
    """Visiera attorno allo schermo aperto: due fianchi e un tettuccio, come la cappa degli
    oscilloscopi. Si avvita al piano della mensola dietro la culla; lo schermo non tocca nulla."""
    ms = Mesh('Stame visiera')
    w_int = M.FLIP['w'] + 6.0
    sp = 3.0
    alt = 78.0                                    # lungo lo schermo
    prof = 24.0                                   # profondità della visiera
    ms.box(-w_int / 2 - sp, 0, 0, -w_int / 2, alt, prof)
    ms.box(w_int / 2, 0, 0, w_int / 2 + sp, alt, prof)
    ms.box(-w_int / 2 - sp, alt, 0, w_int / 2 + sp, alt + sp, prof)
    for sx in (-1, 1):                            # piedi con il foro della vite
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
    ala = Mesh('ala')
    ala.prisma(rett(0, 0, 20, 12), 0, 3.0, holes=[cerchio(10, 6, 1.7, 24)])
    for g in ala.gusci:
        ms.gusci.append([tuple((p[0], p[2], p[1]) for p in t)[::-1] for t in g])
    ms.prisma_x([(3, 3), (12, 3), (3, 12)], 8.5, 11.5)
    return ms


def fermo_hub():
    ms = Mesh('Stame fermo dell\'hub')
    w, d, h = M.HUB['w'] + 0.8, M.HUB['d'] + 0.8, M.HUB['h']
    ms.prisma(rett(-3, -3, w + 3, d + 3, 2), 0, 2.0)
    ms.prisma(rett(-3, -3, w + 3, d + 3, 2), 2.0, h * 0.6, holes=[rett(0, 0, w, d, 1)])
    for x in (-10, w + 10):
        ms.prisma(rett(x - 6, d / 2 - 6, x + 6, d / 2 + 6, 3), 0, 2.0, holes=[cerchio(x, d / 2, 1.7, 24)])
    return ms


STAMPA = {
    'culla_flip': (culla_flip, 1), 'cornice_pad': (cornice_pad, 1), 'visiera': (visiera, 1),
    'piedino_mascherina': (piedino, len(M.PIEDINI)), 'squadretta_m3': (squadretta, 16), 'fermo_hub': (fermo_hub, 1),
}

# pezzi della bozza 2 che non esistono più: si tolgono da out/
OBSOLETI = ['mascherina_sx.svg', 'mascherina_dx.svg', 'ponte_sopra_sx.svg', 'ponte_sopra_dx.svg',
            'ponte_fronte_sx.svg', 'ponte_fronte_dx.svg', 'ponte_retro_sx.svg', 'ponte_retro_dx.svg',
            'centine.svg', 'vassoio_pad.stl', 'colonnina.stl']


# ---------------------------------------------------------------------------------------------

def main():
    os.makedirs(OUT, exist_ok=True)
    for n in OBSOLETI:
        p = os.path.join(OUT, n)
        if os.path.exists(p):
            os.remove(p)
    laser = [mascherina(), dima(), retro('sx'), retro('dx'),
             fianco('sx', 'esterno'), fianco('dx', 'esterno'), fianco('sx', 'interno'),
             base('sx'), base('dx'), divisorio(), torre_piano(), torre_parete('fronte'), torre_parete('retro'),
             cartellino_pad(), tavola()]
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
    print(f'INGOMBRO {M.LARGHEZZA:.1f} x {M.BASE_Y1:.1f} mm, torre alta {M.MENSOLA_Z:.0f} alla mensola')


if __name__ == '__main__':
    main()
