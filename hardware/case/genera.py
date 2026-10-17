"""genera.py — genera i pezzi del case di Stame da misure.py (bozza 4, 17/10/2026).

Uso: python -I hardware/case/genera.py            scrive in hardware/case/out/

Laser (SVG in millimetri, 1:1, per LightBurn): rosso = taglio, nero pieno = incisione,
blu = segno leggero. Le scritte usano gli stessi caratteri della plancia: Matrice a punti per le
funzioni principali, Spleen a pixel per le legende piccole. Così il case e lo schermo parlano la
stessa lingua (docs/identita/README.md).
Stampa (STL, PETG): culla della Flip, cornice del macro pad, visiera, piedini, squadrette, fermo
dell'hub, copritasti.
Fogli di taglio: i pezzi del laser impaginati per materiale, in SVG (LightBurn) e DXF.
Dima (SVG da stampare su carta al 100%): la mascherina sopra il contorno della MK4.

Ogni pezzo si registra con il suo riferimento nello spazio del case: da qui nascono anche il
modello 3D, il modello SketchUp e le tavole del montaggio (assieme.py). Il riferimento del case è
x verso destra, y dal retro verso il musicista, z in su: è sinistrorso, quindi ogni esportazione
3D lo specchia su y (SPECCHIO) per avere i pezzi nel verso fisico giusto.

Bozza 4: la torre si monta a linguette nelle asole (pareti nella base e nel piano), come il
listello del retro e il divisorio; la culla è un vassoio basso che lascia libere le spalle della
Flip (L1 L2 R1 R2, sempre vive dal 17/10/2026); la visiera segue lo schermo a 65°.
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
from mesh import Mesh, rett, cerchio, triangola, sposta, IDENTITA  # noqa: E402
from matrice import GLIFI           # noqa: E402

OUT = os.path.join(QUI, 'out')
SPECCHIO = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0))   # case -> destrorso

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


def matrice_punti(testo, passo):
    """centri dei punti accesi di un testo Matrice, con la linea di base a y = 0 (y in giù)"""
    out, x = [], 0.0
    for ch in testo:
        righe = GLIFI.get(ch, GLIFI['?'])
        for ri, riga in enumerate(righe):
            for ci, c in enumerate(riga):
                if c == '#':
                    out.append((x + (ci + 0.5) * passo, (ri - 7 + 0.5) * passo))
        x += (len(righe[0]) + 1) * passo
    return out


# ---------------------------------------------------------------------------------------------
# SVG per il laser e registro dei pezzi

LASER = []      # dict(nome, svg, frames, t, materiale, passo, quanti)


class Svg:
    def __init__(self, nome, w, h, nota=''):
        self.nome, self.w, self.h, self.nota = nome, w, h, nota
        self.taglio, self.incisione, self.segno = [], [], []
        self._loops = []                                    # contorni di taglio come poligoni

    def _lista(self, livello):
        return {'taglio': self.taglio, 'incisione': self.incisione, 'segno': self.segno}[livello]

    def poligono(self, pts, livello='taglio'):
        d = 'M' + ' L'.join(f'{x:.3f},{y:.3f}' for x, y in pts) + ' Z'
        self._lista(livello).append(f'<path d="{d}"/>')
        if livello == 'taglio':
            self._loops.append(list(pts))

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
        if livello == 'taglio':
            self._loops.append(rett(x, y, x + w, y + h, min(r, w / 2, h / 2)))

    def cerchio(self, cx, cy, r, livello='taglio'):
        self._lista(livello).append(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}"/>')
        if livello == 'taglio':
            self._loops.append(cerchio(cx, cy, r, 24 if r > 3 else 12))

    def punti(self, x, base, passo, testo, allinea='sinistra', livello='incisione', diametro=0.78):
        """Matrice: un cerchio per punto acceso; base = linea di base (y in basso)."""
        w = matrice_w(testo, passo)
        if allinea == 'centro':
            x -= w / 2
        elif allinea == 'destra':
            x -= w
        for px, py in matrice_punti(testo, passo):
            self.cerchio(x + px, base + py, passo * diametro / 2, livello)
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

    def contorni(self):
        """il contorno esterno (il più grande) e i fori del taglio, in coordinate del disegno"""
        def area(p):
            return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2
        loops = sorted(self._loops, key=area, reverse=True)
        return loops[0], loops[1:]

    def contenuto(self):
        return ('<g id="incisione" fill="#000000" stroke="none">\n' + '\n'.join(self.incisione) + '\n</g>\n'
                '<g id="segno" fill="none" stroke="#0000FF" stroke-width="0.1">\n' + '\n'.join(self.segno) + '\n</g>\n'
                '<g id="taglio" fill="none" stroke="#FF0000" stroke-width="0.1">\n' + '\n'.join(self.taglio) + '\n</g>\n')

    def salva(self, cartella=None):
        cartella = cartella or OUT
        os.makedirs(cartella, exist_ok=True)
        p = os.path.join(cartella, self.nome + '.svg')
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(f'<!-- Stame, {self.nome}: {self.nota} Scala 1:1, millimetri. Rosso taglio, nero incisione, blu segno. -->\n')
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w:.2f}mm" height="{self.h:.2f}mm" '
                    f'viewBox="0 0 {self.w:.3f} {self.h:.3f}">\n')
            f.write(f'<title>Stame — {self.nome}</title>\n')
            f.write(self.contenuto())
            f.write('</svg>\n')
        return p


def registra(svg, frames, t, materiale, passo, quanti=None):
    """salva il pezzo del laser e lo registra con i suoi riferimenti (uno per copia montata)"""
    if not isinstance(frames, list):
        frames = [frames]
    LASER.append(dict(nome=svg.nome, svg=svg, frames=frames, t=t, materiale=materiale, passo=passo,
                      quanti=quanti or len(frames)))
    return svg.salva()


def piano(O, U, V):
    """riferimento di un pezzo piano: (u, v) del disegno -> O + u U + v V; lo spessore va lungo
    N = U x V nel riferimento destrorso dei conti, cioè dalla faccia disegnata verso il dietro"""
    N = (U[1] * V[2] - U[2] * V[1], U[2] * V[0] - U[0] * V[2], U[0] * V[1] - U[1] * V[0])
    return (O, U, V, N)


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
# linguette e asole (bozza 4)

def bordo_linguette(s0, s1, z, centri, profondita, w=None):
    """lato orizzontale da s0 a s1 alla quota z, con linguette larghe w centrate in centri che
    sporgono di profondita (negativa = verso il basso); punti nell'ordine da s0 a s1"""
    w = w or M.LINGUETTA
    verso = 1 if s1 > s0 else -1
    pts = [(s0, z)]
    for c in sorted(centri, reverse=verso < 0):
        a, b = c - verso * w / 2, c + verso * w / 2
        pts += [(a, z), (a, z + profondita), (b, z + profondita), (b, z)]
    pts.append((s1, z))
    return pts


def asola(svg, cx, cy, lx, ly):
    """asola centrata in (cx, cy) del disegno per una linguetta lx × ly, con il gioco"""
    g = M.GIOCO
    svg.rett(cx - lx / 2 - g, cy - ly / 2 - g, lx + 2 * g, ly + 2 * g)


X_INT = (M.FIANCO, M.LARGHEZZA - M.FIANCO)     # fra i fianchi
RETRO_H = 30.0
TORRE_LING = (M.TORRE_X0 + 25.0, M.TORRE_X1 - 25.0)                 # linguette delle pareti della torre
DIV_LING = (M.MK4_Y0 + 80.0, M.MK4_Y0 + 170.0)                      # linguette del divisorio
SQUADRETTE_Y = (20.0, 130.0, 230.0)                                   # squadrette fra base e fianchi


def retro_ling(lato):
    a, b = (X_INT[0], M.GIUNTA - 0.2) if lato == 'sx' else (M.GIUNTA + 0.2, X_INT[1])
    return a, b, (a + 40.0, b - 40.0)


# ---------------------------------------------------------------------------------------------
# mascherina della MK4 (CASE-030, CASE-031): un pezzo solo, con le legende di Stame
# mappa dei comandi del 16-17/10/2026 (specifica 40 MIDI-130, MIDI-135)

ETICHETTE_K = {'K1': 'SOUND', 'K2': 'PERFORM', 'K3': 'FX', 'K4': 'KEY',
               'K5': 'BASS', 'K6': 'LOOP', 'K7': 'BPM', 'K8': 'VOLUME'}
# banco A: tipi sopra, estensioni sotto; banco B: la batteria (MIDI-135), sopra i piatti, sotto i tamburi
PAD_SOPRA = {'PAD5': ('DIM', 'B:CHH'), 'PAD6': ('MIN', 'B:OHH'), 'PAD7': ('MAJ', 'B:TOM'), 'PAD8': ('SUS', 'B:CYM')}
PAD_SOTTO = {'PAD1': ('6', 'B:KICK'), 'PAD2': ('m7', 'B:SNARE'), 'PAD3': ('M7', 'B:RIM'), 'PAD4': ('9', 'B:CLAP')}
TRASPORTO = {'UNDO': ('UNDO', 'S:CLEAR'), 'LOOP': ('PAUSE', ''), 'PLAY': ('BEAT', 'S:PANIC'),
             'REC': ('LOOP', ''), 'DUB': ('DUB', '')}
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
    P = 0.5                          # passo dei punti delle manopole: lettere alte 3,5 mm
    for k, nome in ETICHETTE_K.items():
        x, y, _ = M.MK4_CTRL[k]
        base = y + M.FORO['k'][1] / 2 + 1.0 + 7 * P
        svg.punti(x - ox, base - oy, P, nome, 'centro')
    hp = M.FORO['p'][1]
    for pad, (nome, banco_b) in PAD_SOPRA.items():
        x, y, _ = M.MK4_CTRL[pad]
        gap0 = y + hp / 2
        gap1 = M.MK4_CTRL['PAD1'][1] - hp / 2
        top = (gap0 + gap1) / 2 - 1.44 - oy
        svg.pixel(x - ox - 2.0, top, 0.18, nome, 'destra')
        svg.pixel(x - ox + 2.0, top + 0.4, 0.13, banco_b)
    for pad, (nome, banco_b) in PAD_SOTTO.items():
        x, y, _ = M.MK4_CTRL[pad]
        Pp = 0.55
        base = y + hp / 2 + 1.2 + 7 * Pp
        svg.punti(x - ox, base - oy, Pp, nome, 'centro')
        svg.pixel(x - ox, base + 1.2 - oy, 0.15, banco_b, 'centro')
    for nome, testo in (('PITCH', 'BEND'), ('MOD', 'MOD')):
        x, y, _ = M.MK4_CTRL[nome]
        svg.pixel(x - ox, y + M.FORO['w'][1] / 2 + 1.5 - oy, 0.2, testo, 'centro')
    x, y, _ = M.MK4_CTRL['NAV']
    svg.pixel(x - ox, y + M.FORO['e'][1] / 2 + 1.5 - oy, 0.2, 'LIST', 'centro')
    for nome, testo in PULSANTI.items():
        x, y, _ = M.MK4_CTRL[nome]
        svg.pixel(x - ox, y + M.FORO['b'][1] / 2 + 1.5 - oy, 0.2, testo, 'centro')
    for nome, (testo, con_shift) in TRASPORTO.items():
        x, y, _ = M.MK4_CTRL[nome]
        svg.pixel(x - ox, y + M.FORO['b'][1] / 2 + 1.5 - oy, 0.2, testo, 'centro')
        if con_shift:
            svg.pixel(x - ox, y + M.FORO['b'][1] / 2 + 5.0 - oy, 0.14, con_shift, 'centro')
    logo(svg, 38.0 - ox, 80.0 - oy, 11.0)
    svg.punti(38.0 - ox, 91.5 - oy, 0.35, 'STAME', 'centro')
    z = M.BASE_T + M.MK4['h'] + m['piede_h']
    fr = piano((M.MK4_X0 + ox, M.MK4_Y0 + oy, z + M.ACR), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    return registra(svg, _verso(fr, -1), M.ACR, 'acrilico3', 7)


def _verso(frame, segno):
    """riferimento con lo spessore nel verso N (segno +1) o opposto (-1): la faccia disegnata resta in O"""
    if segno > 0:
        return frame
    O, U, V, N = frame
    return (O, U, V, (-N[0], -N[1], -N[2]))


def dima():
    """mascherina sopra il contorno della MK4, da stampare su carta al 100%"""
    m = M.MASCHERINA
    svg = Svg('dima_mascherina', M.MK4['w'] + 20, 130,
              'dima 1:1 della mascherina sul contorno della MK4; stampare al 100%, controllare il righello.')
    ox, oy = -10, -10
    svg.rett(0 - ox, 0 - oy, M.MK4['w'], 104, 0, 'segno')
    svg.linea([(0 - ox, M.MK4_KEYBED_Y - oy), (M.MK4['w'] - ox, M.MK4_KEYBED_Y - oy)], 'segno')
    for nome, (x, y, tipo) in M.MK4_CTRL.items():
        svg.cerchio(x - ox, y - oy, 1.0, 'segno')
        if nome in M.SCOPERTI:
            foro(svg, nome, ox, oy)
        else:
            w, h, r = M.FORO[tipo]
            svg.rett(x - ox - w / 2, y - oy - h / 2, w, h, r, 'segno')
    svg.rett(m['x0'] - ox, m['y0'] - oy, m['x1'] - m['x0'], m['y1'] - m['y0'], 4, 'taglio')
    for (px, py) in M.PIEDINI:
        svg.cerchio(px - ox, py - oy, M.MASCHERINA['piede_d'] / 2, 'segno')
        svg.cerchio(px - ox, py - oy, 0.6, 'incisione')
    svg.tratto([(10 - ox, 112 - oy), (110 - ox, 112 - oy)], 0.3)
    for k in range(11):
        svg.tratto([(10 + k * 10 - ox, 110 - oy), (10 + k * 10 - ox, 114 - oy)], 0.3)
    svg.pixel(120 - ox, 108 - oy, 0.35, '100 mm: misurare dopo la stampa')
    svg.pixel(120 - ox, 116 - oy, 0.35, 'cerchi blu: piedini sotto la mascherina; rettangoli blu: pulsanti coperti')
    return svg.salva()


# ---------------------------------------------------------------------------------------------
# telaio: retro, fianchi, base, divisorio

def retro(lato):
    """listello del retro: chiude la zona dei cavi, con le uscite; si incastra nella base con due
    linguette nelle tacche del bordo posteriore"""
    a, b, ling = retro_ling(lato)
    h = RETRO_H
    svg = Svg(f'retro_{lato}', b - a + 2, h + M.BASE_T + 2,
              f'listello del retro, compensato {M.PLY} mm, alto {h:.0f} più le linguette; sta sulla base.')
    def P(x, z):
        return (x - a + 1, h - z + 1)
    pts = bordo_linguette(a, b, 0.0, ling, -M.BASE_T) + [(b, h), (a, h)]
    svg.poligono([P(x, z) for x, z in pts])
    for cx in ((120.0, 230.0) if lato == 'sx' else (400.0, 500.0)):     # alimentazione, audio, pedale
        x, y = P(cx - 14, 20)
        svg.rett(x, y, 28, 12, 6)
    fr = piano((a - 1, 0.0, M.BASE_T + h + 1), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0))
    return registra(svg, _orienta(fr, (0.0, 1.0, 0.0)), M.PLY, 'betulla4', 2)


def _orienta(frame, verso):
    """porta lo spessore N nel verso dato (vettore del case)"""
    O, U, V, N = frame
    if N[0] * verso[0] + N[1] * verso[1] + N[2] * verso[2] < 0:
        N = (-N[0], -N[1], -N[2])
    return (O, U, V, N)


def profilo_fianco():
    """profilo (y, z) del fianco, dal retro in basso in senso antiorario"""
    Y = M.BASE_Y1
    zf, zb = M.FIANCO_Z['front'], M.FIANCO_Z['back']
    pts = [(0.0, 0.0), (Y, 0.0), (Y, zf - 10.0)]
    for k in range(1, 9):
        t = math.radians(90 * k / 8)
        pts.append((Y - 10 + 10 * math.cos(t), zf - 10 + 10 * math.sin(t)))
    pts += [(M.FIANCO_Z['y_front'], zf), (M.FIANCO_Z['y_back'], zb)]
    for k in range(0, 9):
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
    sp = lato == 'sx'
    def P(y, z):
        u = (Y - y) if sp else y
        return (u + 1, H - z + 1)
    svg.poligono([P(y, z) for y, z in prof])
    if not esterno:                               # viti delle squadrette (CASE-003): a 6 mm sopra la base
        for y in SQUADRETTE_Y:
            svg.cerchio(*P(y, M.BASE_T + 6.0), 1.25)
    if esterno:
        cx, cy = P(40.0, 30.0)
        logo(svg, cx, cy, 28.0)
        x, y = P(72.0, 22.0)
        if sp:
            svg.punti(x, y, 1.3, 'STAME', 'destra')
            svg.pixel(x, y + 3, 0.26, 'STAMEN HARMONICUM', 'destra')
        else:
            svg.punti(x, y, 1.3, 'STAME')
            svg.pixel(x, y + 3, 0.26, 'STAMEN HARMONICUM')
    # riferimenti: strato k (0 = esterno) da fuori verso dentro
    L = M.LARGHEZZA
    def fr_sx(k):
        return _orienta(piano((k * M.PLY, Y + 1, H + 1), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0)), (1.0, 0.0, 0.0))
    def fr_dx(k, disegno_sx):
        x0 = L - (k + 1) * M.PLY
        if disegno_sx:                            # gli strati interni sono tutti uguali: si girano
            return _orienta(piano((x0, Y + 1, H + 1), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0)), (1.0, 0.0, 0.0))
        return _orienta(piano((L, -1.0, H + 1), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0)), (-1.0, 0.0, 0.0))
    if esterno:
        frames = [fr_sx(0) if sp else fr_dx(0, False)]
    else:
        frames = [fr_sx(k) for k in range(1, M.FIANCO_STRATI)] + [fr_dx(k, True) for k in range(1, M.FIANCO_STRATI)]
    return registra(svg, frames, M.PLY, 'betulla4', 3)


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


def _tacche_retro(a, b):
    """bordo posteriore della base da a a b con le tacche per le linguette del retro"""
    g, hw = M.GIOCO, M.LINGUETTA / 2 + M.GIOCO
    pts = []
    for lato in ('sx', 'dx'):
        for c in retro_ling(lato)[2]:
            if a < c < b:
                pts.append(c)
    out = []
    for c in sorted(pts):
        out += [(c - hw, 0.0), (c - hw, M.PLY + g), (c + hw, M.PLY + g), (c + hw, 0.0)]
    return out


def base(lato):
    a, b = (M.FIANCO, M.GIUNTA) if lato == 'sx' else (M.GIUNTA, M.LARGHEZZA - M.FIANCO)
    Y = M.BASE_Y1
    svg = Svg(f'base_{lato}', b - a + 14, Y + 2, f'base, compensato {M.BASE_T} mm; le due metà si incastrano a coda di rondine.')
    def P(x, y):
        return (x - a + 1, y + 1)
    giunta = _bordo_giunta(Y)
    tacche = _tacche_retro(a, b)
    if lato == 'sx':
        pts = [(a, 0.0)] + tacche + giunta + [(a, Y)]
    else:
        pts = [(b, 0.0), (b, Y)] + list(reversed(giunta)) + tacche
    svg.poligono([P(x, y) for x, y in pts])
    # piedini in gomma (segno) e viti delle squadrette dei fianchi
    for x, y in ((M.FIANCO + 25, 20), (M.FIANCO + 25, Y - 20), (M.LARGHEZZA - M.FIANCO - 25, 20),
                 (M.LARGHEZZA - M.FIANCO - 25, Y - 20), (M.GIUNTA - 30, 20), (M.GIUNTA - 30, Y - 20)):
        if a < x < b:
            svg.cerchio(*P(x, y), 6.0, 'segno')
    for x in (M.FIANCO + 6.0, M.LARGHEZZA - M.FIANCO - 6.0):
        for y in SQUADRETTE_Y:
            if a < x < b:
                svg.cerchio(*P(x, y), 1.7)
    # asole: divisorio e pareti della torre
    for yc in DIV_LING:
        if a < M.DIV_X < b:
            asola(svg, *P(M.DIV_X + M.PLY / 2, yc), M.PLY, M.LINGUETTA)
    for yw in (M.MENSOLA_Y[0], M.TORRE_FRONTE_Y):
        for xc in TORRE_LING:
            if a < xc < b:
                asola(svg, *P(xc, yw + M.PLY / 2), M.LINGUETTA, M.PLY)
    # viti del fermo dell'hub
    for x in (M.HUB_X0 - 10.0, M.HUB_X0 + M.HUB['w'] + 0.8 + 10.0):
        if a < x < b:
            svg.cerchio(*P(x, M.HUB_Y0 + (M.HUB['d'] + 0.8) / 2), 1.25)
    # segni per la posa: MK4, pad
    def area(x0, y0, w, h, r=0.0):
        xa, xb = max(x0, a + 0.5), min(x0 + w, b - 0.5)
        if xb > xa:
            svg.rett(*P(xa, y0), xb - xa, h, r if xa == x0 and xb == x0 + w else 0, 'segno')
    area(M.MK4_X0, M.MK4_Y0, M.MK4['w'], M.MK4['d'], 3)
    area(M.PAD_X0, M.PAD_Y0, M.PAD['w'], M.PAD['d'], 4)
    fr = piano((a - 1, -1.0, M.BASE_T), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    return registra(svg, _orienta(fr, (0.0, 0.0, -1.0)), M.BASE_T, 'betulla6', 1)


def divisorio():
    """parete fra la MK4 e la torre: copre il fianco della MK4; due linguette nella base; dietro
    lascia passare i cavi"""
    y0, y1 = M.MK4_Y0, M.MK4_Y0 + M.MK4['d']
    z1 = M.MENSOLA_Z
    svg = Svg('divisorio', y1 - y0 + 2, z1 + 2, f'divisorio fra MK4 e torre, compensato {M.PLY} mm; si incastra nella base.')
    def P(y, z):
        return (y - y0 + 1, z1 - z + 1)
    pts = ([(y0, 20.0), (y0 + 26.0, 20.0)] + bordo_linguette(y0 + 26.0, y1, M.BASE_T, DIV_LING, -M.BASE_T)
           + [(y1, z1), (y0, z1)])
    svg.poligono([P(y, z) for y, z in pts])
    fr = piano((M.DIV_X, y0 - 1, z1 + 1), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0))
    return registra(svg, _orienta(fr, (1.0, 0.0, 0.0)), M.PLY, 'betulla4', 2)


# ---------------------------------------------------------------------------------------------
# torre: piano della mensola, pareti davanti e dietro, cartellino del pad

def culla_viti():
    """viti M3 che fissano la culla al piano (sotto la Flip: teste svasate)"""
    return [(M.FLIP_X + sx * 30.0, M.FLIP_Y0 + dy) for sx in (-1, 1) for dy in (15.0, 65.0)]


def visiera_viti():
    return [(M.FLIP_X + sx * (M.FLIP['w'] / 2 + 14.0), M.FLIP_Y0 + 12.0) for sx in (-1, 1)]


def torre_piano():
    """piano della mensola della Flip: sporge di 3 mm oltre le pareti, che entrano con le linguette
    nelle asole; porta la culla e la visiera, avvitate da sopra con i dadi sotto"""
    x0, x1 = M.TORRE_X0, M.TORRE_X1
    y0, y1 = M.PIANO_Y
    svg = Svg('torre_piano', x1 - x0 + 2, y1 - y0 + 2, f'piano della mensola della Flip, compensato {M.BASE_T} mm.')
    def P(x, y):
        return (x - x0 + 1, y - y0 + 1)
    svg.poligono([P(x0, y0), P(x1, y0), P(x1, y1), P(x0, y1)])
    for yw in (M.MENSOLA_Y[0], M.TORRE_FRONTE_Y):
        for xc in TORRE_LING:
            asola(svg, *P(xc, yw + M.PLY / 2), M.LINGUETTA, M.PLY)
    for x, y in culla_viti() + visiera_viti():
        svg.cerchio(*P(x, y), 1.7)
    x, y = P(x0 + 6, y1 - 7)
    svg.pixel(x, y, 0.22, 'TAB. I')
    fr = piano((x0 - 1, y0 - 1, M.MENSOLA_Z), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    return registra(svg, _orienta(fr, (0.0, 0.0, -1.0)), M.BASE_T, 'betulla6', 5)


def torre_parete(dove):
    """pareti del vano dell'hub, sotto il piano: due linguette in basso nella base e due in alto
    nel piano. Davanti il passaggio del cavo del pad, accanto al cartellino; dietro la finestra dei
    cavi (OTG della Flip, USB della MK4)"""
    x0, x1 = M.TORRE_X0, M.TORRE_X1
    zt = M.PIANO_Z0
    svg = Svg(f'torre_{dove}', x1 - x0 + 2, M.MENSOLA_Z + 2,
              f'parete {"davanti" if dove == "fronte" else "dietro"} della mensola, compensato {M.PLY} mm.')
    def P(x, z):
        return (x - x0 + 1, M.MENSOLA_Z - z + 1)
    pts = (bordo_linguette(x0, x1, M.BASE_T, TORRE_LING, -M.BASE_T)
           + bordo_linguette(x1, x0, zt, TORRE_LING, M.BASE_T)[0:])
    svg.poligono([P(x, z) for x, z in pts])
    if dove == 'fronte':
        x, y = P(PAD_CAVO_X - 9.0, M.BASE_T + 16.0)
        svg.rett(x, y, 18.0, 12.0, 4.0)
    else:
        x, y = P(M.FLIP_X - 20, M.BASE_T + 26)
        svg.rett(x, y, 40, 14, 5)
    yw = M.TORRE_FRONTE_Y if dove == 'fronte' else M.MENSOLA_Y[0]
    fr = piano((x0 - 1, yw, M.MENSOLA_Z + 1), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0))
    return registra(svg, _orienta(fr, (0.0, 1.0, 0.0)), M.PLY, 'betulla4', 4)


# il cavo del pad passa dalla parete davanti a destra del cartellino
CARTELLINO_X0 = M.TORRE_X0 + 2.0
CARTELLINO_W = 152.0
PAD_CAVO_X = CARTELLINO_X0 + CARTELLINO_W + 9.5

# la mappa del macro pad con una tastiera collegata (specifica 40 MIDI-120, MIDI-133); senza
# tastiera il pad è lo strumento (MIDI-136): le note stanno in piccolo in basso a destra
LEGENDA_PAD = [[('T1', 'HOLD'), ('T2', 'TAP'), ('T3', 'METRO'), ('T4', 'FILL'), ('T13', 'LOCK')],
               [('T5', 'SCENE 1'), ('T6', 'SCENE 2'), ('T7', 'SCENE 3'), ('T8', 'SCENE 4'), ('T14', 'VIEW')],
               [('T9', 'OPTIONS'), ('T10', 'SAVE LP'), ('T11', 'DRUMS'), ('T12', 'PANIC'), ('T15', 'PAGE')]]
NOTE_PAD = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
# manopole: con la tastiera, con il Lock, con il solo pad
MANOPOLE_PAD = {'m1': ('BASS VOIC', 'PERFORM', 'EXT'), 'm2': ('BEAT VOL', 'KEY', 'FOCUS'), 'M': ('CHORD VOIC', 'SOUND', 'TYPE')}


def cartellino_pad():
    """striscia di acrilico incollata sulla parete davanti della mensola: la mappa dei 15 tasti e
    delle 3 manopole del macro pad, nello stesso ordine in cui stanno sul pad"""
    W, H = CARTELLINO_W, M.CARTELLINO['h']
    svg = Svg('cartellino_pad', W + 2, H + 2, f'cartellino del macro pad, acrilico nero {M.ACR} mm; si incolla sulla parete davanti della mensola.')
    svg.rett(1, 1, W, H, 3)
    cw, ch = 19.0, 10.0
    x0, y0 = 5.0, 2.5
    for r, riga in enumerate(LEGENDA_PAD):
        for c, (sigla, nome) in enumerate(riga):
            x, y = x0 + c * (cw + 1.5), y0 + r * ch
            svg.tratto([(x, y), (x + cw, y), (x + cw, y + ch - 1.2), (x, y + ch - 1.2), (x, y)], 0.25)
            svg.pixel(x + 1.4, y + 0.9, 0.15, sigla)
            svg.pixel(x + cw - 1.4, y + 0.9, 0.15, nome, 'destra')
            if c < 4:                                                # la nota del pad strumento
                svg.pixel(x + cw - 1.4, y + 4.8, 0.14, NOTE_PAD[r * 4 + c], 'destra')
            else:                                                    # le aggiunte di Stame: un segno sotto
                svg.tratto([(x + 1.2, y + ch - 2.6), (x + cw - 1.2, y + ch - 2.6)], 0.5)
    kx = x0 + 5 * (cw + 1.5) + 3.0
    for nome, (cx, cy, r) in (('m1', (kx + 7, 8.5, 4.0)), ('m2', (kx + 31, 8.5, 4.0)), ('M', (kx + 19, 22.5, 5.0))):
        anello = [(cx + r * math.cos(2 * math.pi * k / 40), cy + r * math.sin(2 * math.pi * k / 40)) for k in range(41)]
        svg.tratto(anello, 0.45)
        svg.tratto([(cx, cy - r + 0.8), (cx, cy - r + 2.4)], 0.6)
        svg.pixel(cx, cy - 1.3, 0.16, nome, 'centro')
    # sotto ogni manopola: il mestiere con la tastiera e, piccolo, quello del pad strumento
    for k, (cx, y) in (('m1', (kx + 7, 13.3)), ('m2', (kx + 31, 13.3)), ('M', (kx + 19, 28.0))):
        svg.pixel(cx, y, 0.13, MANOPOLE_PAD[k][0], 'centro')
        svg.pixel(cx, y + 2.3, 0.11, 'PAD:' + MANOPOLE_PAD[k][2], 'centro')
    svg.pixel(kx + 19, 1.2, 0.12, 'LOCK: ' + ' '.join(MANOPOLE_PAD[k][1] for k in ('M', 'm1', 'm2')), 'centro')
    fr = piano((CARTELLINO_X0 - 1, M.TORRE_FRONTE_Y + M.PLY + M.ACR, M.BASE_T + H + 1), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0))
    return registra(svg, _orienta(fr, (0.0, -1.0, 0.0)), M.ACR, 'acrilico3', 4)


# ---------------------------------------------------------------------------------------------
# tavola d'insieme (vista dall'alto e fianco), non va al laser

def flip_aperta():
    """sagome (y, z) della Flip aperta sulla culla: metà con i tasti in piano, schermo a
    SCHERMO_DEG dall'orizzontale verso il retro; e la visiera"""
    a = math.radians(M.SCHERMO_DEG)
    d, t = M.FLIP['d'], M.FLIP['half']
    z0 = M.FLIP_Z0
    y1 = M.FLIP_Y0
    y0 = y1 + d
    sotto = [(y0, z0), (y1, z0), (y1, z0 + t), (y0, z0 + t)]
    h = (y1, z0 + t)
    v = (-math.cos(a), math.sin(a))
    w = (math.sin(a), math.cos(a))
    s1 = (h[0] + v[0] * d, h[1] + v[1] * d)
    sopra = [h, s1, (s1[0] - w[0] * t, s1[1] - w[1] * t), (h[0] - w[0] * t, h[1] - w[1] * t)]
    return sotto, sopra, visiera_profilo()


def visiera_profilo():
    """fianco della visiera nel piano (y, z): dal piano della mensola dietro la cerniera, lungo lo
    schermo fino sopra il bordo alto, e 24 mm davanti allo schermo"""
    a = math.radians(M.SCHERMO_DEG)
    d, t = M.FLIP['d'], M.FLIP['half']
    h = (M.FLIP_Y0, M.FLIP_Z0 + t)
    v = (-math.cos(a), math.sin(a))
    w = (math.sin(a), math.cos(a))
    def p(sv, sw):
        return (h[0] + v[0] * sv + w[0] * sw, h[1] + v[1] * sv + w[1] * sw)
    alto_dietro = p(d + 4.0, -t - 3.0)
    alto_davanti = p(d + 4.0, 24.0)
    basso_davanti = p(6.0, 24.0)
    return [(M.FLIP_Y0 - 6.0, M.MENSOLA_Z), (M.FLIP_Y0 + 4.0, M.MENSOLA_Z), (basso_davanti[0], basso_davanti[1]),
            alto_davanti, alto_dietro, (alto_dietro[0], M.MENSOLA_Z + 20.0)]


def tavola():
    W, Y = M.LARGHEZZA, M.BASE_Y1
    svg = Svg('tavola_insieme', W + 40, Y + 300, 'tavola d\'insieme: vista dall\'alto e fianco; non è un pezzo da tagliare.')
    ox, oy = 20, 20
    def T(x, y):
        return (x + ox, y + oy)
    svg.rett(*T(0, 0), M.FIANCO, Y, 2, 'taglio')
    svg.rett(*T(W - M.FIANCO, 0), M.FIANCO, Y, 2, 'taglio')
    svg.rett(*T(M.FIANCO, 0), W - 2 * M.FIANCO, M.PLY, 0, 'taglio')
    svg.rett(*T(M.MK4_X0, M.MK4_Y0), M.MK4['w'], M.MK4['d'], 3, 'segno')
    for k in range(16):
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
    svg.rett(*T(M.DIV_X, M.MK4_Y0), M.PLY, M.MK4['d'], 0, 'taglio')
    svg.rett(*T(M.TORRE_X0, M.PIANO_Y[0]), M.TORRE_W, M.PIANO_Y[1] - M.PIANO_Y[0], 0, 'taglio')
    cw = M.FLIP['w'] + 2 * (0.6 + M.CULLA_PARETE)
    svg.rett(*T(M.FLIP_X - cw / 2, M.FLIP_Y0), cw, M.FLIP['d'] + 3.6, 2, 'segno')
    svg.rett(*T(M.FLIP_X - M.FLIP['w'] / 2, M.FLIP_Y0), M.FLIP['w'], M.FLIP['d'], 3, 'segno')
    sch = M.FLIP['d'] * math.cos(math.radians(M.SCHERMO_DEG))
    svg.rett(*T(M.FLIP_X - M.FLIP['w'] / 2, M.FLIP_Y0 - sch), M.FLIP['w'], sch, 3, 'segno')
    svg.rett(*T(CARTELLINO_X0, M.TORRE_FRONTE_Y + M.PLY), CARTELLINO_W, M.ACR, 0, 'taglio')
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
    # vista di fianco (da destra)
    z_max = 240.0
    oy2 = oy + Y + 40
    def S(y, z):
        return (y + ox, oy2 + z_max - z)
    prof = profilo_fianco()
    svg.poligono([S(y, z) for y, z in prof], 'taglio')
    svg.poligono([S(0, 0), S(Y, 0), S(Y, M.BASE_T), S(0, M.BASE_T)], 'segno')
    svg.poligono([S(0, M.BASE_T), S(M.PLY, M.BASE_T), S(M.PLY, M.BASE_T + RETRO_H), S(0, M.BASE_T + RETRO_H)], 'segno')
    y0, y1 = M.MK4_Y0, M.MK4_Y0 + M.MK4['d']
    zt = M.BASE_T + M.MK4['h']
    yk = M.MK4_Y0 + M.MK4_KEYBED_Y
    svg.poligono([S(y0, M.BASE_T), S(y1, M.BASE_T), S(y1, M.BASE_T + M.MK4['key_top']), S(yk, M.BASE_T + M.MK4['key_top']),
                  S(yk, zt), S(y0, zt)], 'segno')
    pm0, pm1 = M.MK4_Y0 + m['y0'], M.MK4_Y0 + m['y1']
    zp = zt + m['piede_h']
    svg.poligono([S(pm0, zp), S(pm1, zp), S(pm1, zp + M.ACR), S(pm0, zp + M.ACR)], 'segno')
    svg.poligono([S(M.PIANO_Y[0], M.PIANO_Z0), S(M.PIANO_Y[1], M.PIANO_Z0), S(M.PIANO_Y[1], M.MENSOLA_Z), S(M.PIANO_Y[0], M.MENSOLA_Z)], 'taglio')
    for yw in (M.MENSOLA_Y[0], M.TORRE_FRONTE_Y):
        svg.poligono([S(yw, M.BASE_T), S(yw + M.PLY, M.BASE_T), S(yw + M.PLY, M.PIANO_Z0), S(yw, M.PIANO_Z0)], 'taglio')
    svg.poligono([S(M.HUB_Y0, M.BASE_T), S(M.HUB_Y0 + M.HUB['d'], M.BASE_T), S(M.HUB_Y0 + M.HUB['d'], M.BASE_T + M.HUB['h']),
                  S(M.HUB_Y0, M.BASE_T + M.HUB['h'])], 'segno')
    cy0 = M.TORRE_FRONTE_Y + M.PLY
    svg.poligono([S(cy0, M.BASE_T), S(cy0 + M.ACR, M.BASE_T), S(cy0 + M.ACR, M.BASE_T + M.CARTELLINO['h']), S(cy0, M.BASE_T + M.CARTELLINO['h'])], 'taglio')
    sotto, sopra, vis = flip_aperta()
    svg.poligono([S(*p) for p in sotto], 'taglio')
    svg.poligono([S(*p) for p in sopra], 'taglio')
    svg.poligono([S(*p) for p in vis], 'segno')
    py0, py1 = M.PAD_Y0, M.PAD_Y0 + M.PAD['d']
    svg.poligono([S(py0, M.BASE_T), S(py1, M.BASE_T), S(py1, M.BASE_T + M.PAD['h']), S(py0, M.BASE_T + M.PAD['h'])], 'taglio')
    svg.poligono([S(py0 - 6, M.BASE_T), S(py1 + 6, M.BASE_T), S(py1 + 6, M.BASE_T + 8), S(py0 - 6, M.BASE_T + 8)], 'segno')
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
# pezzi stampati: costruiti nel riferimento del case, dove stanno montati (STAMPATI registra il
# riferimento delle copie); per la stampa si specchiano su y e si portano a terra

STAMPATI = []   # dict(nome, mesh, frames, passo, quanti, nota, materiale)


CAPOVOLTO = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0))   # giro di 180° attorno a x


def stampato(nome, mesh, frames, passo, nota, materiale='petg_nero', posa=IDENTITA):
    """posa: come il pezzo va sul piatto, dopo lo specchio (per esempio capovolto)"""
    if not isinstance(frames, list):
        frames = [frames]
    STAMPATI.append(dict(nome=nome, mesh=mesh, frames=frames, passo=passo, quanti=len(frames), nota=nota,
                         materiale=materiale, posa=posa))


def culla_flip():
    """Vassoio basso sul piano della mensola: fondo da 2 mm, bordi da 5 mm davanti e ai lati,
    aperto dietro (spalle L1 L2 R1 R2, cerniera, USB-C OTG). Davanti gli intagli del jack e della
    USB-C di ricarica, ai lati le finestre dei tasti del volume [V: posizioni]. Quattro fori per
    viti M3 svasate, sotto la Flip."""
    fw, fd = M.FLIP['w'] + 1.2, M.FLIP['d'] + 1.0
    p, h = M.CULLA_PARETE, M.CULLA_BORDO
    x0, x1 = M.FLIP_X - fw / 2, M.FLIP_X + fw / 2
    y0, y1 = M.FLIP_Y0 - 0.6, M.FLIP_Y0 - 0.6 + fd
    z0, zf = M.MENSOLA_Z, M.MENSOLA_Z + M.CULLA_FONDO
    ms = Mesh('Stame culla della Flip')
    viti = [cerchio(x, y, 1.7, 16) for x, y in culla_viti()]
    ms.prisma(rett(x0 - p, y0, x1 + p, y1 + p, 2.0), z0, zf, holes=viti)                  # fondo
    for a, b in ((x0 - p, M.FLIP_X - 22.0), (M.FLIP_X - 12.0, M.FLIP_X - 4.0), (M.FLIP_X + 10.0, x1 + p)):
        ms.box(a, y1, zf, b, y1 + p, zf + h)                                               # bordo davanti
    for xa, xb in ((x0 - p, x0), (x1, x1 + p)):                                            # bordi laterali
        ms.box(xa, y0 + 12.0, zf, xb, y0 + 30.0, zf + h)
        ms.box(xa, y0 + 60.0, zf, xb, y1, zf + h)
    return ms


def cornice_pad():
    """cornice che tiene fermo il macro pad sulla base (si incolla), con l'intaglio per il cavo"""
    ms = Mesh('Stame cornice del macro pad')
    pw, pd = M.PAD['w'] + 0.8, M.PAD['d'] + 0.8
    s, h = 6.0, 8.0
    ox, oy = M.PAD_X0 - 0.4, M.PAD_Y0 - 0.4
    fr = sposta(ox, oy, M.BASE_T)
    ms.box(-s, -s, 0, 0, pd + s, h, frame=fr)
    ms.box(pw, -s, 0, pw + s, pd + s, h, frame=fr)
    ms.box(0, pd, 0, pw, pd + s, h, frame=fr)
    ux = M.PAD_USB_X
    ms.box(0, -s, 0, ux - 10, 0, h, frame=fr)
    ms.box(ux + 10, -s, 0, pw, 0, h, frame=fr)
    return ms


def visiera():
    """Visiera attorno allo schermo aperto: due fianchi che seguono lo schermo a 65°, un tettuccio
    sopra il bordo alto e due piedi avvitati al piano dietro la culla. Non tocca la Flip."""
    ms = Mesh('Stame visiera')
    prof = visiera_profilo()
    w_int = M.FLIP['w'] + 10.0
    sp = 3.0
    xa, xb = M.FLIP_X - w_int / 2 - sp, M.FLIP_X + w_int / 2
    for x in (xa, xb):
        ms.prisma_x(prof, x, x + sp)
    # tettuccio: il lato alto del profilo (fra alto_davanti e alto_dietro), spesso 3 mm, da fianco a fianco
    a, b = prof[3], prof[4]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = ((b[1] - a[1]) / L * sp, -(b[0] - a[0]) / L * sp)
    tetto = [a, b, (b[0] + n[0], b[1] + n[1]), (a[0] + n[0], a[1] + n[1])]
    ms.prisma_x(tetto, xa, xb + sp)
    for (x, y) in visiera_viti():
        ms.prisma(rett(x - 7, y - 7, x + 7, y + 7, 2), M.MENSOLA_Z, M.MENSOLA_Z + 4.0, holes=[cerchio(x, y, 1.7, 16)])
        # piede collegato al fianco
        xf = xa if x < M.FLIP_X else xb
        ms.box(min(x, xf), y - 3, M.MENSOLA_Z, max(x, xf + sp), y + 3, M.MENSOLA_Z + 4.0)
    return ms


def piedino():
    ms = Mesh('Stame piedino della mascherina')
    ms.cilindro(0, 0, 0, M.MASCHERINA['piede_h'], M.MASCHERINA['piede_d'] / 2, 32)
    return ms


def squadretta():
    """squadretta M3: ala orizzontale (sulla base) e ala verticale (sul fianco) lungo x, rinforzo"""
    ms = Mesh('Stame squadretta M3')
    ms.prisma(rett(0, 0, 20, 12), 0, 3.0, holes=[cerchio(10, 6, 1.7, 16)])
    ms.prisma(rett(0, 0, 20, 12), 0, 3.0, holes=[cerchio(10, 6, 1.7, 16)],
              frame=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)))
    ms.prisma_x([(3, 3), (12, 3), (3, 12)], 8.5, 11.5)
    return ms


def squadrette_frames():
    """riferimenti delle squadrette fra base e fianchi: l'ala verticale sul fianco, l'orizzontale
    sulla base; il foro nella base a 6 mm dal fianco, quello nel fianco a 6 mm sopra la base"""
    out = []
    for y in SQUADRETTE_Y:
        out.append(((M.FIANCO, y - 10.0, M.BASE_T), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)))
        out.append(((M.LARGHEZZA - M.FIANCO, y + 10.0, M.BASE_T), (0.0, -1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)))
    return out


def fermo_hub():
    ms = Mesh('Stame fermo dell\'hub')
    w, d, h = M.HUB['w'] + 0.8, M.HUB['d'] + 0.8, M.HUB['h']
    fr = sposta(M.HUB_X0, M.HUB_Y0, M.BASE_T)
    ms.prisma(rett(-3, -3, w + 3, d + 3, 2), 0, 2.0, frame=fr)
    ms.prisma(rett(-3, -3, w + 3, d + 3, 2), 2.0, h * 0.6, holes=[rett(0, 0, w, d, 1)], frame=fr)
    for x in (-10, w + 10):
        ms.prisma(rett(x - 6, d / 2 - 6, x + 6, d / 2 + 6, 3), 0, 2.0, holes=[cerchio(x, d / 2, 1.25, 16)], frame=fr)
    return ms


# copritasti del macro pad (CASE-043): una scritta per la mappa con la tastiera e, sotto, la nota
# del pad strumento; punti Matrice in rilievo di 0,5 mm sulla faccia di sopra. Si stampano dritti,
# con il cambio di filamento all'altezza dei punti (neri sul sabbia) e il supporto solo sotto lo stelo
COPRITASTI = [(['HOLD'], 'C'), (['TAP'], 'C♯'), (['METRO'], 'D'), (['FILL'], 'D♯'), (['LOCK'], ''),
              (['SCENE', '1'], 'E'), (['SCENE', '2'], 'F'), (['SCENE', '3'], 'F♯'), (['SCENE', '4'], 'G'), (['VIEW'], ''),
              (['OPT'], 'G♯'), (['SAVE', 'LOOP'], 'A'), (['DRUMS'], 'A♯'), (['PANIC'], 'B'), (['PAGE'], '')]


def copritasto(righe, nota):
    """un copritasto nel suo riferimento: base aperta a z = 0, faccia di sopra a z = h"""
    C = M.COPRITASTO
    w, d, h, top = C['w'], C['d'], C['h'], C['top']
    ms = Mesh('Stame copritasto')
    ms.prisma(rett(-w / 2, -d / 2, w / 2, d / 2, 1.5), 0.0, h - top, holes=[rett(-w / 2 + 1.2, -d / 2 + 1.2, w / 2 - 1.2, d / 2 - 1.2, 0.8)])
    ms.prisma(rett(-w / 2, -d / 2, w / 2, d / 2, 1.5), h - top, h)
    passo = 0.5
    buchi = []                                   # i punti in rilievo
    righe_h = len(righe) * 7 * passo + (len(righe) - 1) * 1.2
    y = -d / 2 + 2.2 + (d - 4.4 - righe_h - (3.2 if nota else 0)) / 2 + 7 * passo
    for testo in righe:
        x = -matrice_w(testo, passo) / 2
        for px, py in matrice_punti(testo, passo):
            buchi.append(cerchio(x + px, y + py, passo * 0.45, 8))
        y += 7 * passo + 1.2
    if nota:
        pn = 0.4
        x = w / 2 - 1.6 - matrice_w(nota, pn)
        yb = d / 2 - 1.6
        for px, py in matrice_punti(nota, pn):
            buchi.append(cerchio(x + px, yb + py, pn * 0.45, 8))
    # punti sulla faccia di sopra: la y del disegno della scritta è verso il musicista
    for b in buchi:
        ms.prisma(b, h, h + 0.5)
    cx, cy = C['croce']
    croce = [(-cx / 2, -cy / 2), (-cy / 2, -cy / 2), (-cy / 2, -cx / 2), (cy / 2, -cx / 2), (cy / 2, -cy / 2), (cx / 2, -cy / 2),
             (cx / 2, cy / 2), (cy / 2, cy / 2), (cy / 2, cx / 2), (-cy / 2, cx / 2), (-cy / 2, cy / 2), (-cx / 2, cy / 2)]
    ms.prisma(cerchio(0, 0, C['stelo_d'] / 2, 24), h - top - C['stelo_h'], h - top, holes=[croce])
    return ms


def copritasti():
    """i 15 copritasti in un pezzo solo da stampare, in tre file da cinque come sul pad, e le
    copie montate per il modello 3D"""
    tutti = Mesh('Stame copritasti')
    montati = []
    for i, (righe, nota) in enumerate(COPRITASTI):
        r, c = i // 5, i % 5
        k = copritasto(righe, nota)
        tutti.unisci(k, sposta(c * (M.COPRITASTO['w'] + 3.0), r * (M.COPRITASTO['d'] + 3.0), 0.0))
        cx = M.PAD_X0 + M.PAD['k0'][0] + c * M.PAD['pitch_x']
        cy = M.PAD_Y0 + M.PAD['k0'][1] + r * M.PAD['pitch_y']
        montati.append((k, sposta(cx, cy, M.BASE_T + M.PAD['h'] - M.COPRITASTO['h'] + 1.0)))
    return tutti, montati


# ---------------------------------------------------------------------------------------------
# fogli di taglio: i pezzi del laser impaginati per materiale (CASE-003: piano del laser)

MATERIALI = {'betulla4': f'compensato di betulla {M.PLY:.0f} mm', 'betulla6': f'compensato di betulla {M.BASE_T:.0f} mm',
             'acrilico3': f'acrilico nero {M.ACR:.0f} mm'}
FOGLIO = M.LASER_BED
STACCO = 4.0


def impagina():
    """scaffali: pezzi per altezza decrescente, ruotati di 90° se così stanno meglio"""
    fogli = []
    for mat in MATERIALI:
        pezzi = []
        for p in LASER:
            if p['materiale'] != mat:
                continue
            for k in range(p['quanti']):
                w, h = p['svg'].w, p['svg'].h
                ruota = w > FOGLIO[0] - 2 * STACCO or (h > w and h <= FOGLIO[0] - 2 * STACCO)
                pezzi.append((p, k, ruota, (h, w) if ruota else (w, h)))
        pezzi.sort(key=lambda q: -q[3][1])
        aperti = []
        for q in pezzi:
            w, h = q[3]
            messo = False
            for f in aperti:
                for sc in f['scaffali']:
                    if h <= sc['h'] and sc['x'] + w <= FOGLIO[0] - STACCO:
                        f['pezzi'].append((q, sc['x'], sc['y']))
                        sc['x'] += w + STACCO
                        messo = True
                        break
                if messo:
                    break
                y = f['y']
                if y + h <= FOGLIO[1] - STACCO:
                    f['scaffali'].append(dict(y=y, h=h, x=STACCO + w + STACCO))
                    f['pezzi'].append((q, STACCO, y))
                    f['y'] = y + h + STACCO
                    messo = True
                    break
            if not messo:
                f = dict(mat=mat, scaffali=[dict(y=STACCO, h=h, x=STACCO + w + STACCO)], pezzi=[(q, STACCO, STACCO)], y=STACCO + h + STACCO)
                aperti.append(f)
        for i, f in enumerate(aperti):
            f['nome'] = f'taglio_{mat}_{i + 1}'
            fogli.append(f)
    return fogli


def scrivi_fogli(fogli):
    cart = os.path.join(OUT, 'taglio')
    os.makedirs(cart, exist_ok=True)
    for n in os.listdir(cart):
        if n.startswith('taglio_'):
            os.remove(os.path.join(cart, n))
    righe = []
    for f in fogli:
        W, H = FOGLIO
        corpo = []
        for (p, k, ruota, (w, h)), x, y in f['pezzi']:
            svg = p['svg']
            tr = f'translate({x:.2f},{y:.2f})' + (f' translate({w:.2f},0) rotate(90)' if ruota else '')
            corpo.append(f'<g transform="{tr}"><title>{svg.nome}</title>\n{svg.contenuto()}</g>')
        with open(os.path.join(cart, f['nome'] + '.svg'), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            fh.write(f'<!-- Stame, {f["nome"]}: {MATERIALI[f["mat"]]}, foglio {W:.0f} x {H:.0f} mm. Rosso taglio, nero incisione, blu segno. -->\n')
            fh.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.2f}mm" height="{H:.2f}mm" viewBox="0 0 {W:.3f} {H:.3f}">\n')
            fh.write(f'<title>Stame — {f["nome"]}</title>\n')
            fh.write(f'<rect x="0" y="0" width="{W}" height="{H}" fill="none" stroke="#0000FF" stroke-width="0.2"/>\n')
            fh.write('\n'.join(corpo) + '\n</svg>\n')
        scrivi_dxf(f, os.path.join(cart, f['nome'] + '.dxf'))
        nomi = ', '.join(sorted({q[0][0]['nome'] for q in f['pezzi']}))
        usato = (max(x + q[3][0] for q, x, y in f['pezzi']) + STACCO, max(y + q[3][1] for q, x, y in f['pezzi']) + STACCO)
        f['usato'] = usato
        righe.append((f['nome'], MATERIALI[f['mat']], len(f['pezzi']), nomi, usato))
    return righe


def _tr(x, y, ruota, w, ox, oy):
    """coordinate del disegno di un pezzo -> foglio (y del DXF in su)"""
    if ruota:
        x, y = w - y, x
    return (ox + x, FOGLIO[1] - (oy + y))


def scrivi_dxf(f, path):
    """DXF R12: taglio (rosso) come polilinee chiuse, incisione (nero) come contorni, segno (blu)"""
    L = ['0', 'SECTION', '2', 'HEADER', '9', '$INSUNITS', '70', '4', '0', 'ENDSEC',
         '0', 'SECTION', '2', 'TABLES', '0', 'TABLE', '2', 'LAYER', '70', '3']
    for nome, col in (('TAGLIO', 1), ('INCISIONE', 7), ('SEGNO', 5)):
        L += ['0', 'LAYER', '2', nome, '70', '0', '62', str(col), '6', 'CONTINUOUS']
    L += ['0', 'ENDTAB', '0', 'ENDSEC', '0', 'SECTION', '2', 'ENTITIES']
    def poly(pts, layer):
        nonlocal L
        L += ['0', 'POLYLINE', '8', layer, '66', '1', '10', '0.0', '20', '0.0', '30', '0.0', '70', '1']
        for x, y in pts:
            L += ['0', 'VERTEX', '8', layer, '10', f'{x:.3f}', '20', f'{y:.3f}']
        L += ['0', 'SEQEND', '8', layer]
    W, H = FOGLIO
    poly([(0, 0), (W, 0), (W, H), (0, H)], 'SEGNO')
    for (p, k, ruota, (w, h)), ox, oy in f['pezzi']:
        svg = p['svg']
        for loop in svg._loops:
            poly([_tr(x, y, ruota, w, ox, oy) for x, y in loop], 'TAGLIO')
        for el in svg.incisione:
            for loop in _parse_svg_el(el):
                poly([_tr(x, y, ruota, w, ox, oy) for x, y in loop], 'INCISIONE')
        cx, cy = _tr(4.0, 4.0, ruota, w, ox, oy)
        L += ['0', 'TEXT', '8', 'SEGNO', '10', f'{cx:.2f}', '20', f'{cy:.2f}', '40', '3.0', '1', svg.nome]
    L += ['0', 'ENDSEC', '0', 'EOF']
    with open(path, 'w', encoding='ascii', newline='\n') as fh:
        fh.write('\n'.join(L) + '\n')


def _parse_svg_el(el):
    """un elemento SVG del livello incisione -> contorni"""
    if el.startswith('<path'):
        d = re.search(r'd="([^"]+)"', el).group(1)
        return [[tuple(float(v) for v in xy.split(',')) for xy in re.findall(r'(-?[0-9.]+,-?[0-9.]+)', d)]]
    if el.startswith('<rect'):
        g = {k: float(v) for k, v in re.findall(r'(\w+)="(-?[0-9.]+)"', el)}
        return [rett(g['x'], g['y'], g['x'] + g['width'], g['y'] + g['height'], g.get('rx', 0.0))]
    if el.startswith('<circle'):
        g = {k: float(v) for k, v in re.findall(r'(\w+)="(-?[0-9.]+)"', el)}
        return [cerchio(g['cx'], g['cy'], g['r'], 10)]
    return []


# ---------------------------------------------------------------------------------------------

# pezzi della bozza 2 e 3 che non esistono più: si tolgono da out/
OBSOLETI = ['mascherina_sx.svg', 'mascherina_dx.svg', 'ponte_sopra_sx.svg', 'ponte_sopra_dx.svg',
            'ponte_fronte_sx.svg', 'ponte_fronte_dx.svg', 'ponte_retro_sx.svg', 'ponte_retro_dx.svg',
            'centine.svg', 'vassoio_pad.stl', 'colonnina.stl']


def genera():
    """tutti i pezzi; torna le liste per la stampa a video e per assieme.py"""
    os.makedirs(OUT, exist_ok=True)
    for n in OBSOLETI:
        p = os.path.join(OUT, n)
        if os.path.exists(p):
            os.remove(p)
    LASER.clear()
    STAMPATI.clear()
    laser = [mascherina(), dima(), retro('sx'), retro('dx'),
             fianco('sx', 'esterno'), fianco('dx', 'esterno'), fianco('sx', 'interno'),
             base('sx'), base('dx'), divisorio(), torre_piano(), torre_parete('fronte'), torre_parete('retro'),
             cartellino_pad(), tavola()]
    stampato('culla_flip', culla_flip(), IDENTITA, 5, 'vassoio sul piano della mensola, 4 viti M3 svasate')
    stampato('visiera', visiera(), IDENTITA, 5, 'si avvita al piano dietro la culla; stampare sul tettuccio, con supporti')
    stampato('cornice_pad', cornice_pad(), IDENTITA, 6, 'si incolla sulla base attorno al pad')
    stampato('fermo_hub', fermo_hub(), IDENTITA, 4, 'tiene l\'hub nel vano, 2 viti nella base')
    stampato('squadretta_m3', squadretta(), squadrette_frames(), 3, 'base e fianchi, viti M3')
    m = M.MASCHERINA
    zp = M.BASE_T + M.MK4['h']
    stampato('piedino_mascherina', piedino(), [sposta(M.MK4_X0 + x, M.MK4_Y0 + y, zp) for x, y in M.PIEDINI], 7,
             'meglio TPU; si incollano sotto la mascherina dove indica la dima', 'tpu')
    tutti, montati = copritasti()
    stampato('copritasti', tutti, [], 9, 'PETG sabbia, dritti; filamento nero dai punti in su; supporto solo sotto lo stelo; '
             'stelo a croce tipo MX [V]', 'petg_sabbia')
    return laser, montati


def main():
    laser, _ = genera()
    print('LASER (SVG 1:1, mm)')
    for p in laser:
        txt = open(p, encoding='utf-8').read()
        w = float(re.search(r'width="([0-9.]+)mm"', txt).group(1))
        h = float(re.search(r'height="([0-9.]+)mm"', txt).group(1))
        sta = w <= M.LASER_BED[0] and h <= M.LASER_BED[1]
        nota = '' if sta or 'dima' in p or 'tavola' in p else '  NON STA NEL PIANO DEL LASER'
        print(f'  {os.path.basename(p):28s} {w:6.1f} x {h:6.1f}{nota}')
    print('STAMPA (STL, specchiati su y: il verso fisico giusto)')
    for s in STAMPATI:
        ms = s['mesh'].portato(SPECCHIO).portato(s['posa']).a_terra()
        ok = ms.controlla()
        (x0, y0, z0), (x1, y1, z1) = ms.ingombro()
        tri = ms.salva(os.path.join(OUT, s['nome'] + '.stl'))
        n = s['quanti'] or 1
        sta = (x1 - x0) <= M.PRINT_BED[0] and (y1 - y0) <= M.PRINT_BED[1]
        print(f'  {s["nome"] + ".stl":28s} {x1 - x0:6.1f} x {y1 - y0:6.1f} x {z1 - z0:5.1f}  x{n:<3d} '
              f'{tri:6d} triangoli  {"chiuso" if ok else "GUSCIO APERTO"}{"" if sta else "  NON STA NEL PIANO"}')
    print('FOGLI DI TAGLIO')
    for nome, mat, n, pezzi, (uw, uh) in scrivi_fogli(impagina()):
        print(f'  {nome:24s} {mat:28s} lastra da almeno {uw:3.0f} x {uh:3.0f}  {n:2d} pezzi: {pezzi}')
    print(f'INGOMBRO {M.LARGHEZZA:.1f} x {M.BASE_Y1:.1f} mm, torre alta {M.MENSOLA_Z:.0f} alla mensola')


if __name__ == '__main__':
    main()
