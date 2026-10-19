"""genera.py — genera i pezzi del case di Stame da misure.py (bozza 5, 18/10/2026).

Uso: python -I hardware/case/genera.py            scrive in hardware/case/out/

Laser (SVG in millimetri, 1:1, per LightBurn): rosso = taglio, nero pieno = incisione,
blu = segno leggero. Le scritte usano gli stessi caratteri della plancia: Matrice a punti per le
funzioni principali, Spleen a pixel per le legende piccole. Così il case e lo schermo parlano la
stessa lingua (docs/identita/README.md).
Stampa (STL, PETG): culla della Flip, culla del macro pad, visiera, squadrette, fermo dell'hub. I
tasti del pad sono trasparenti, con le etichette di carta di etichette.py.
Fogli di taglio: i pezzi del laser impaginati per materiale, in SVG (LightBurn) e DXF.
Dima (SVG da stampare su carta al 100%): la mascherina sopra il contorno della MK4.

Ogni pezzo si registra con il suo riferimento nello spazio del case: da qui nascono anche il
modello 3D, il modello SketchUp e le tavole del montaggio (assieme.py). Il riferimento del case è
x verso destra, y dal retro verso il musicista, z in su: è sinistrorso, quindi ogni esportazione
3D lo specchia su y (SPECCHIO) per avere i pezzi nel verso fisico giusto.

Bozza 5 (Luigi, 18/10/2026: «deve essere tutto coperto e omogeneo»): un telaio di betulla con la
cima alla stessa quota (fianchi, retro, costola, parete davanti) e dentro un piano di acrilico nero
in due pezzi: la mascherina, che appoggia sulla MK4 con un foro per ogni controllo e copre la zona
dei cavi, e il piano della Flip. Il pad sta nella sua culla, come la Flip nella sua; hub e cavi
sotto il piano. Gli strati d'appoggio (fianchi, retro, costola) reggono il piano con il feltro.
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
from mesh import Mesh, rett, cerchio, triangola, sposta, taglia, area, IDENTITA  # noqa: E402
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
        # le scritte incise: testo, tipo (pixel o punti), passo e gli elementi di self.incisione che le
        # disegnano (i0…i1), così la versione stampata a più colori le può ridisegnare (stampa3d.py)
        self.scritte = []

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
        i0 = len(self.incisione)
        for px, py in matrice_punti(testo, passo):
            self.cerchio(x + px, base + py, passo * diametro / 2, livello)
        if livello == 'incisione':
            self.scritte.append(dict(tipo='punti', testo=testo, passo=passo, tratto=passo * diametro, allinea=allinea,
                                     i0=i0, i1=len(self.incisione)))
        return w

    def pixel(self, x, top, px, testo, allinea='sinistra', livello='incisione'):
        """Spleen 8x16: rettangoli per righe di pixel accesi; top = cima della cella."""
        cw, ch, glifi = SPLEEN
        w = pixel_w(testo, px)
        if allinea == 'centro':
            x -= w / 2
        elif allinea == 'destra':
            x -= w
        i0 = len(self.incisione)
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
        if livello == 'incisione':
            self.scritte.append(dict(tipo='pixel', testo=testo, passo=px, tratto=px, allinea=allinea,
                                     i0=i0, i1=len(self.incisione)))
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
    if svg.incisione:
        for O, U, V, N in frames:
            # nel mondo vero (y specchiata) U x V deve andare come N, dalla faccia incisa dentro il
            # pezzo: altrimenti, con la faccia incisa fuori, le scritte si leggono a specchio
            u, v, n = (U[0], -U[1], U[2]), (V[0], -V[1], V[2]), (N[0], -N[1], N[2])
            c = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
            assert sum(a * b for a, b in zip(c, n)) > 0, f'{svg.nome}: le incisioni uscirebbero a specchio'
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
RETRO_H = M.Z_PIANO - M.BASE_T                 # 40: il retro arriva in cima, come i fianchi
COSTOLA_LING = (100.0, 205.0)                  # linguette della costola nella base (y)
FRONTE_LING = (M.DESTRA_X0 + 40.0, M.DESTRA_X1 - 40.0)
SQUADRETTE_Y = (28.0, 130.0, 230.0)            # squadrette fra base e fianchi (la prima davanti al retro)
CAVI_Z = 30.0                                  # dietro la MK4 la costola lascia passare i cavi fin qui
USCITE = {'sx': (280.0,), 'dx': (430.0, 500.0)}   # finestre del retro: pedale; alimentazione e audio
# cima delle finestre sopra la base: a destra stanno sopra l'hub, che è contro il retro, e i cavi
# passano fra l'hub e il piano
USCITE_Z = {'sx': 20.0, 'dx': M.HUB['h'] + 2.0 + 14.0}


def retro_ling(lato):
    a, b = (X_INT[0], M.GIUNTA - 0.2) if lato == 'sx' else (M.GIUNTA + 0.2, X_INT[1])
    return a, b, (a + 40.0, b - 40.0)


# ---------------------------------------------------------------------------------------------
# mascherina della MK4 (CASE-030, CASE-031): appoggia sul pannello della MK4 e copre la zona dei
# cavi fino al retro. Un foro per ogni controllo (Luigi, 18/10/2026); le legende di Stame solo dove il
# comando non dice niente o fa un'altra cosa (19/10/2026). Mappa del 16-17/10/2026 (40 MIDI-130, MIDI-135)

ETICHETTE_K = {'K1': 'SOUND', 'K2': 'PERFORM', 'K3': 'FX', 'K4': 'KEY',
               'K5': 'BASS', 'K6': 'LOOP', 'K7': 'BPM', 'K8': 'VOLUME'}
# banco A: tipi sopra, estensioni sotto; banco B: la batteria (MIDI-135), sopra i piatti, sotto i tamburi
PAD_SOPRA = {'PAD5': ('DIM', 'B:CHH'), 'PAD6': ('MIN', 'B:OHH'), 'PAD7': ('MAJ', 'B:TOM'), 'PAD8': ('SUS', 'B:CYM')}
PAD_SOTTO = {'PAD1': ('6', 'B:KICK'), 'PAD2': ('m7', 'B:SNARE'), 'PAD3': ('M7', 'B:RIM'), 'PAD4': ('9', 'B:CLAP')}
# Luigi, 19/10/2026: si scrive solo dove il comando non dice niente (pad, ruote, manopole: i loro nomi
# sono sul pannello, sotto la mascherina) o dove Stame gli dà un'altra funzione. I tasti piccoli hanno
# il nome stampato sopra: UNDO resta Undo, e si scrive solo il suo SHIFT
TRASPORTO = {'UNDO': ('', 'S:CLEAR'), 'LOOP': ('PAUSE', ''), 'PLAY': ('BEAT', 'S:PANIC'),
             'REC': ('LOOP', ''), 'DUB': ('DUB', '')}
PULSANTI = {'SHIFT': 'PUSH', 'MINUS': 'BACK', 'PLUS': 'MENU'}
# i comandi della MK4 stessa (OCT −/+, ARP, LATCH, NOTE REPEAT, TAP TEMPO, PLUGIN DAW) hanno il nome
# sul tasto e Stame non li usa: niente scritte. BANK A/B sì, perché per Stame il banco B è la batteria
PROPRI = {'BANK': 'B: DRUMS'}

MASC_X0, MASC_X1 = M.FIANCO - M.PLY + 0.2, M.GIUNTA_PIANO - 0.2
MASC_Y0, MASC_Y1 = M.RETRO_Y + 0.2, M.MASCHERINA_Y1


def ctrl(nome):
    """centro di un controllo della MK4 nel riferimento del case"""
    x, y, _ = M.MK4_CTRL[nome]
    return M.MK4_X0 + x, M.MK4_Y0 + y


def foro(svg, nome, ox, oy):
    """foro di un controllo; (ox, oy) è l'origine del disegno nel riferimento del case"""
    x, y = ctrl(nome)
    w, h, r = M.FORO[M.MK4_CTRL[nome][2]]
    if M.MK4_CTRL[nome][2] in ('k', 'e'):
        svg.cerchio(x - ox, y - oy, w / 2)
    else:
        svg.rett(x - ox - w / 2, y - oy - h / 2, w, h, r)


def mascherina():
    svg = Svg('mascherina', MASC_X1 - MASC_X0 + 2, MASC_Y1 - MASC_Y0 + 2,
              f'mascherina della MK4, acrilico nero {M.ACR} mm: appoggia sulla MK4 e copre i cavi fino al retro.')
    ox, oy = MASC_X0 - 1, MASC_Y0 - 1
    svg.poligono(rett(1, 1, MASC_X1 - ox, MASC_Y1 - oy, 0.6))
    for nome in M.MK4_CTRL:
        foro(svg, nome, ox, oy)
    def C(nome):
        x, y = ctrl(nome)
        return x - ox, y - oy
    P = 0.5                          # passo dei punti delle manopole: lettere alte 3,5 mm
    for k, nome in ETICHETTE_K.items():
        x, y = C(k)
        svg.punti(x, y + M.FORO['k'][1] / 2 + 1.0 + 7 * P, P, nome, 'centro')
    hp = M.FORO['p'][1]
    for pad, (nome, banco_b) in PAD_SOPRA.items():
        x, y = C(pad)
        gap1 = C('PAD1')[1] - hp / 2
        top = (y + hp / 2 + gap1) / 2 - 1.44
        svg.pixel(x - 2.0, top, 0.18, nome, 'destra')
        svg.pixel(x + 2.0, top + 0.4, 0.13, banco_b)
    for pad, (nome, banco_b) in PAD_SOTTO.items():
        x, y = C(pad)
        Pp = 0.55
        base = y + hp / 2 + 1.2 + 7 * Pp
        svg.punti(x, base, Pp, nome, 'centro')
        svg.pixel(x, base + 1.2, 0.15, banco_b, 'centro')
    for nome, testo in (('PITCH', 'BEND'), ('MOD', 'MOD')):
        x, y = C(nome)
        svg.pixel(x, y + M.FORO['w'][1] / 2 + 1.5, 0.2, testo, 'centro')
    x, y = C('NAV')
    svg.pixel(x, y + M.FORO['e'][1] / 2 + 1.5, 0.2, 'LIST', 'centro')
    hb = M.FORO['b'][1]
    for nome, testo in PULSANTI.items():
        x, y = C(nome)
        if nome == 'SHIFT':
            svg.pixel(x, y + hb / 2 + 1.5, 0.2, testo, 'centro')
        else:                        # BACK e MENU sopra: sotto c'è il foro di SHIFT, a 3 mm
            svg.pixel(x, y - hb / 2 - 3.8, 0.2, testo, 'centro')
    for nome, (testo, con_shift) in TRASPORTO.items():
        x, y = C(nome)
        if testo:
            svg.pixel(x, y + hb / 2 + 1.5, 0.2, testo, 'centro')
        if con_shift:
            svg.pixel(x, y + hb / 2 + (5.0 if testo else 1.5), 0.14, con_shift, 'centro')
    for nome, testo in PROPRI.items():
        x, y = C(nome)
        svg.pixel(x, y + hb / 2 + 1.5, 0.15, testo, 'centro')
    # la targa sulla zona dei cavi, dietro la MK4: il marchio e il nome
    yc = (M.RETRO_Y + M.MK4_Y0) / 2
    logo(svg, M.MK4_X0 + 24.0 - ox, yc - oy, 26.0)
    svg.punti(M.MK4_X0 + 44.0 - ox, yc + 3.5 - oy, 1.0, 'STAME')
    svg.pixel(M.MK4_X0 + 44.0 - ox, yc + 6.5 - oy, 0.25, 'STAMEN HARMONICUM')
    fr = piano((ox, oy, M.Z_PIANO), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    return registra(svg, _verso(fr, -1), M.ACR, 'acrilico', 7)


def _verso(frame, segno):
    """riferimento con lo spessore nel verso N (segno +1) o opposto (-1): la faccia disegnata resta in O"""
    if segno > 0:
        return frame
    O, U, V, N = frame
    return (O, U, V, (-N[0], -N[1], -N[2]))


def dima():
    """la mascherina sopra il contorno della MK4, da stampare su carta al 100%"""
    ox, oy = MASC_X0 - 10, MASC_Y0 - 10
    yk = M.MK4_Y0 + M.MK4_KEYBED_Y
    svg = Svg('dima_mascherina', MASC_X1 - MASC_X0 + 20, yk + 34 - oy,
              'dima 1:1 della mascherina sul contorno della MK4; stampare al 100%, controllare il righello.')
    svg.rett(M.MK4_X0 - ox, M.MK4_Y0 - oy, M.MK4['w'], M.MK4_KEYBED_Y + 6, 0, 'segno')
    svg.linea([(M.MK4_X0 - ox, yk - oy), (M.MK4_X0 + M.MK4['w'] - ox, yk - oy)], 'segno')
    for nome in M.MK4_CTRL:
        x, y = ctrl(nome)
        svg.cerchio(x - ox, y - oy, 1.0, 'segno')
        foro(svg, nome, ox, oy)
    svg.rett(MASC_X0 - ox, MASC_Y0 - oy, MASC_X1 - MASC_X0, MASC_Y1 - MASC_Y0, 0.6, 'taglio')
    y = yk + 16 - oy
    svg.tratto([(10, y), (110, y)], 0.3)
    for k in range(11):
        svg.tratto([(10 + k * 10, y - 2), (10 + k * 10, y + 2)], 0.3)
    svg.pixel(120, y - 4, 0.35, '100 mm: misurare dopo la stampa')
    svg.pixel(120, y + 4, 0.35, 'la mascherina appoggia sulla MK4: ogni foro deve lasciare libero il suo controllo')
    return svg.salva()


# ---------------------------------------------------------------------------------------------
# telaio: retro e strato d'appoggio, fianchi, base, costola, parete davanti

def retro(lato):
    """retro: chiude la zona dei cavi e arriva in cima, arretrato fin dove finisce la curva dei fianchi;
    si incastra nella base con due linguette nelle asole. Le finestre per pedale, alimentazione e audio"""
    a, b, ling = retro_ling(lato)
    h = RETRO_H
    svg = Svg(f'retro_{lato}', b - a + 2, h + M.BASE_T + 2,
              f'retro, compensato {M.PLY} mm, alto {h:.0f} più le linguette; sta sulla base.')
    def P(x, z):
        return (x - a + 1, h - z + 1)
    pts = bordo_linguette(a, b, 0.0, ling, -M.BASE_T) + [(b, h), (a, h)]
    svg.poligono([P(x, z) for x, z in pts])
    for cx in USCITE[lato]:
        x, y = P(cx - 14, USCITE_Z[lato])
        svg.rett(x, y, 28, 12, 6)
    fr = piano((a - 1, M.RETRO_Y0, M.BASE_T + h + 1), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0))
    return registra(svg, _orienta(fr, (0.0, 1.0, 0.0)), M.PLY, 'betulla4', 2)


def appoggio_retro(lato):
    """strato incollato davanti al retro, più basso: regge il bordo di dietro del piano (feltro)"""
    a, b, _ = retro_ling(lato)
    h = M.Z_APPOGGIO - M.BASE_T
    svg = Svg(f'appoggio_retro_{lato}', b - a + 2, h + 2,
              f'strato d\'appoggio del retro, compensato {M.PLY} mm, alto {h:.0f}; si incolla davanti al retro.')
    def P(x, z):
        return (x - a + 1, h - z + 1)
    svg.poligono([P(a, 0.0), P(b, 0.0), P(b, h), P(a, h)])
    for cx in USCITE[lato]:
        x, y = P(cx - 14, USCITE_Z[lato])
        svg.rett(x, y, 28, 12, 6)
    fr = piano((a - 1, M.RETRO_Y, M.BASE_T + h + 1), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0))
    return registra(svg, _orienta(fr, (0.0, 1.0, 0.0)), M.PLY, 'betulla4', 2)


def _orienta(frame, verso):
    """porta lo spessore N nel verso dato (vettore del case)"""
    O, U, V, N = frame
    if N[0] * verso[0] + N[1] * verso[1] + N[2] * verso[2] < 0:
        N = (-N[0], -N[1], -N[2])
    return (O, U, V, N)


def _arco(c, r, a0, a1, n=8):
    return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def profilo_fianco(basso=None):
    """profilo (y, z) dei fianchi, dal retro in basso in senso antiorario: cima piana alla quota del
    piano e spigoli arrotondati; basso = (y0, y1) dove lo strato d'appoggio scende sotto il piano.
    Se il tratto basso entra sotto uno spigolo (y0 = 4 e raggio 8, dietro), l'arco si ferma lì:
    altrimenti il contorno tornava su se stesso e lasciava un ritaglio di pochi millimetri"""
    Y, H, R = M.BASE_Y1, M.Z_PIANO, M.FIANCO_R
    y0, y1 = basso or (R, Y - R)
    dav = _arco((Y - R, H - R), R, 0, math.degrees(math.acos(min(1.0, (y1 - Y + R) / R))) if y1 > Y - R else 90)
    ret = _arco((R, H - R), R, math.degrees(math.acos(max(-1.0, (y0 - R) / R))) if y0 < R else 90, 180)
    pts = [(0.0, 0.0), (Y, 0.0)] + dav
    if basso:
        pts += [(y1, dav[-1][1]), (y1, M.Z_APPOGGIO), (y0, M.Z_APPOGGIO), (y0, ret[0][1])]
    pts += ret
    return [p for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > 1e-6]


def fianco(nome, copie, basso=None, incisa=False, viti=False):
    """uno strato dei fianchi per le copie [(lato, k)], k = 0 l'esterno. L'esterno sinistro si disegna
    con il davanti a destra, come si legge da fuori; tutti gli altri con il davanti a sinistra"""
    prof = profilo_fianco(basso)
    H, Y, L = M.Z_PIANO, M.BASE_Y1, M.LARGHEZZA
    rovescio = not (incisa and copie[0][0] == 'sx')
    if incisa:
        nota = f'fianco {"sinistro" if copie[0][0] == "sx" else "destro"}, strato esterno con le incisioni'
    elif basso:
        nota = f'fianco {"sinistro" if copie[0][0] == "sx" else "destro"}, strato d\'appoggio (il più interno)'
    else:
        nota = f'strato di mezzo dei fianchi: tagliarne {len(copie)}'
    svg = Svg(nome, Y + 2, H + 2, nota + f', compensato {M.PLY} mm.')
    def P(y, z):
        return (((Y - y) if rovescio else y) + 1, H - z + 1)
    svg.poligono([P(y, z) for y, z in prof])
    if viti:                                      # viti delle squadrette (CASE-003): a 6 mm sopra la base
        for y in SQUADRETTE_Y:
            svg.cerchio(*P(y, M.BASE_T + 6.0), 1.25)
    if incisa:
        logo(svg, *P(40.0, 24.0), 26.0)
        x, y = P(70.0, 26.0)
        svg.punti(x, y, 1.3, 'STAME', 'destra' if rovescio else 'sinistra')
        svg.pixel(x, y + 3, 0.26, 'STAMEN HARMONICUM', 'destra' if rovescio else 'sinistra')
    frames = []
    for lato, k in copie:
        if k == 0 and lato == 'sx':
            frames.append(_orienta(piano((0.0, -1.0, H + 1), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0)), (1.0, 0.0, 0.0)))
        elif k == 0:
            frames.append(_orienta(piano((L, Y + 1, H + 1), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0)), (-1.0, 0.0, 0.0)))
        else:
            x0 = k * M.PLY if lato == 'sx' else L - (k + 1) * M.PLY
            frames.append(_orienta(piano((x0, Y + 1, H + 1), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0)), (1.0, 0.0, 0.0)))
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


def _tacche_fronte(a, b):
    """bordo davanti della base da b ad a (x che cala) con le tacche per le linguette della parete
    davanti: la parete sta sul bordo, quindi le sedi sono tacche aperte come quelle del retro"""
    g, hw, Y = M.GIOCO, M.LINGUETTA / 2 + M.GIOCO, M.BASE_Y1
    out = []
    for c in sorted((c for c in FRONTE_LING if a < c < b), reverse=True):
        out += [(c + hw, Y), (c + hw, Y - M.PLY - g), (c - hw, Y - M.PLY - g), (c - hw, Y)]
    return out


def base(lato):
    a, b = (M.FIANCO, M.GIUNTA) if lato == 'sx' else (M.GIUNTA, M.LARGHEZZA - M.FIANCO)
    Y = M.BASE_Y1
    svg = Svg(f'base_{lato}', b - a + 14, Y + 2, f'base, compensato {M.BASE_T} mm; le due metà si incastrano a coda di rondine.')
    def P(x, y):
        return (x - a + 1, y + 1)
    giunta = _bordo_giunta(Y)
    tacche = _tacche_retro(a, b) if M.RETRO_Y0 == 0 else []     # il retro sul bordo: tacche; arretrato: asole
    if lato == 'sx':
        pts = [(a, 0.0)] + tacche + giunta + _tacche_fronte(a, b) + [(a, Y)]
    else:
        pts = [(b, 0.0), (b, Y)] + _tacche_fronte(a, b) + list(reversed(giunta)) + tacche
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
    # asole del retro, se è arretrato dal bordo
    if M.RETRO_Y0 > 0:
        for c in (c for s in ('sx', 'dx') for c in retro_ling(s)[2]):
            if a < c < b:
                asola(svg, *P(c, M.RETRO_Y0 + M.PLY / 2), M.LINGUETTA, M.PLY)
    # asole della costola (due strati incollati, linguette insieme); la parete davanti ha le tacche nel bordo
    for yc in COSTOLA_LING:
        if a < M.GIUNTA_PIANO < b:
            asola(svg, *P(M.GIUNTA_PIANO, yc), 2 * M.PLY, M.LINGUETTA)
    # viti del fermo dell'hub
    for x in (M.HUB_X0 - 10.0, M.HUB_X0 + M.HUB['w'] + 0.8 + 10.0):
        if a < x < b:
            svg.cerchio(*P(x, M.HUB_Y0 + (M.HUB['d'] + 0.8) / 2), 1.25)
    # la vite della colonnina, da sotto
    if a < COLONNINA[0] < b:
        svg.cerchio(*P(*COLONNINA), 1.7)
    # segni per la posa: MK4, culla del pad
    def area(x0, y0, w, h, r=0.0):
        xa, xb = max(x0, a + 0.5), min(x0 + w, b - 0.5)
        if xb > xa:
            svg.rett(*P(xa, y0), xb - xa, h, r if xa == x0 and xb == x0 + w else 0, 'segno')
    area(M.MK4_X0, M.MK4_Y0, M.MK4['w'], M.MK4['d'], 3)
    area(M.DESTRA_X0 + 0.3, M.CULLA_PAD_Y0, M.DESTRA_X1 - M.DESTRA_X0 - 0.6, M.CULLA_PAD_Y1 - M.CULLA_PAD_Y0, 1)
    fr = piano((a - 1, -1.0, M.BASE_T), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    return registra(svg, _orienta(fr, (0.0, 0.0, -1.0)), M.BASE_T, 'betulla6', 1)


def costola(lato):
    """costola fra la MK4 e la culla del pad, due strati incollati con le linguette insieme. Dietro
    reggono la mascherina (sx) e il piano della Flip (dx) con il feltro, e sotto lasciano passare i
    cavi della MK4 verso l'hub; davanti salgono in cima, sono la guancia dei tasti, e lo spigolo in cima
    ha l'arco dei fianchi"""
    y0, Y, H = M.APPOGGIO_Y, M.BASE_Y1, M.Z_PIANO
    yb = M.MASCHERINA_Y1 if lato == 'sx' else M.CULLA_PAD_Y0
    svg = Svg(f'costola_{lato}', Y - y0 + 2, H + 2,
              f'costola, strato {"verso la MK4" if lato == "sx" else "verso il pad"}, compensato {M.PLY} mm; '
              'i due strati si incollano.')
    def P(y, z):
        return (y - y0 + 1, H - z + 1)
    pts = ([(y0, CAVI_Z), (M.MK4_Y0, CAVI_Z)] + bordo_linguette(M.MK4_Y0, Y, M.BASE_T, COSTOLA_LING, -M.BASE_T)
           + _arco((Y - M.FIANCO_R, H - M.FIANCO_R), M.FIANCO_R, 0, 90) + [(yb, H), (yb, M.Z_APPOGGIO), (y0, M.Z_APPOGGIO)])
    svg.poligono([P(y, z) for y, z in pts])
    x = M.COSTOLA_X0 + (0.0 if lato == 'sx' else M.PLY)
    fr = piano((x, y0 - 1, H + 1), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0))
    return registra(svg, _orienta(fr, (1.0, 0.0, 0.0)), M.PLY, 'betulla4', 2)


def fronte():
    """parete davanti della parte destra, davanti alla culla del pad: si ferma dove comincia la curva
    dei fianchi, e sopra la curva la continua il bordo della culla"""
    x0, x1, H = M.DESTRA_X0, M.DESTRA_X1, M.FRONTE_Z
    svg = Svg('fronte_dx', x1 - x0 + 2, H + 2, f'parete davanti della culla del pad, compensato {M.PLY} mm.')
    def P(x, z):
        return (x - x0 + 1, H - z + 1)
    pts = bordo_linguette(x0, x1, M.BASE_T, FRONTE_LING, -M.BASE_T) + [(x1, H), (x0, H)]
    svg.poligono([P(x, z) for x, z in pts])
    fr = piano((x0 - 1, M.FRONTE_Y, H + 1), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0))
    return registra(svg, _orienta(fr, (0.0, 1.0, 0.0)), M.PLY, 'betulla4', 2)


# ---------------------------------------------------------------------------------------------
# il macro pad: il suo contorno vero (foto di Luigi del 18/10/2026), per la culla, la tavola e il modello

def contorno_pad(o=0.0):
    """Contorno del macro pad nel riferimento del case, allargato di o: angoli R 5; davanti, dal lato
    delle manopole, il lobo che sporge 2 mm negli ultimi 40 mm, con l'angolo R 30 e un gradino fatto
    di due curve da 1 mm. Torna (punti, mezzi): mezzi sono gli indici dei punti a metà degli angoli
    (dietro a sinistra, dietro a destra, il lobo, davanti a sinistra), da cui la culla si divide nelle
    sue quattro pareti."""
    x0, y0, w, L = M.PAD_X0, M.PAD_Y0, M.PAD['w'], M.PAD_LOBO
    r, R, g = M.PAD_R, L['r'], 1.0
    xa = x0 + w - L['lungo']                         # dove comincia il lobo
    yf, yl = y0 + M.PAD['d'], M.PAD_Y1                # davanti dei tasti, davanti del lobo
    archi = [((x0 + r, y0 + r), r + o, 180, 270, 8, True),      # dietro a sinistra
             ((x0 + w - r, y0 + r), r + o, 270, 360, 8, True),  # dietro a destra
             ((x0 + w - R, yl - R), R + o, 0, 90, 16, True),    # il lobo, davanti a destra
             ((xa + g, yl - g), g + o, 90, 180, 4, False),      # il gradino: la curva convessa
             ((xa - g, yf + g), max(g - o, 0.05), 0, -90, 4, False),   # e quella concava
             ((x0 + r, yf - r), r + o, 90, 180, 8, True)]       # davanti a sinistra
    pts, mezzi = [], []
    for c, rr, a0, a1, n, angolo in archi:
        if angolo:
            mezzi.append(len(pts) + n // 2)
        pts += _arco(c, rr, a0, a1, n)
    return pts, mezzi


# ---------------------------------------------------------------------------------------------
# piano della Flip: acrilico nero come la mascherina, con la culla e la visiera avvitate sopra

def culla_viti():
    """viti M3 che fissano la culla al piano (sotto la Flip: teste svasate)"""
    return [(M.FLIP_X + sx * 30.0, M.FLIP_Y0 + dy) for sx in (-1, 1) for dy in (15.0, 65.0)]


def visiera_viti():
    return [(M.FLIP_X + sx * (M.FLIP['w'] / 2 + 14.0), M.FLIP_Y0 + 12.0) for sx in (-1, 1)]


CULLA_FLIP_Y1 = M.FLIP_Y0 - 0.6 + M.FLIP['d'] + 1.0 + M.CULLA_PARETE   # davanti della culla della Flip
PIANO_X0, PIANO_X1 = M.GIUNTA_PIANO + 0.2, M.DESTRA_X1 + M.PLY - 0.2
PIANO_Y0 = M.RETRO_Y + 0.2
# fessure dei cavi: OTG della Flip dietro la cerniera; jack e ricarica davanti alla culla
FESSURA_OTG = (M.FLIP_X - 16.0, M.FLIP_Y0 - 13.0, 32.0, 8.0)
FESSURA_FRONTE = (M.FLIP_X + M.FLIP_JACK_DX - 9.0, CULLA_FLIP_Y1 + 2.0,
                  M.FLIP_USBC_DX - M.FLIP_JACK_DX + 18.0, 8.0)
SPINA_PAD_X = M.PAD_X0 + M.PAD_USB_X
SPINA_PAD_TOP = M.PAD_Z0 + M.PAD_USB_Z + 3.5        # la spina a 90° è alta circa 7 mm

# le manopole del pad (40 MIDI-120, MIDI-139): normale e sotto DRUMS. La colonna del Lock (SOUND,
# PERFORM, KEY) è tolta con il Lock, il 19/10/2026
MANOPOLE_PAD = [('M', 'CH. VOICING', 'DENSITY'), ('m1', 'BASS VOICING', 'GROOVE'), ('m2', 'BEAT VOL', 'VARIATION')]


def piano_flip():
    x0, x1, y0, y1 = PIANO_X0, PIANO_X1, PIANO_Y0, M.PIANO_Y1
    svg = Svg('piano_flip', x1 - x0 + 2, y1 - y0 + 2,
              f'piano della Flip, acrilico nero {M.ACR} mm: appoggia su retro, costola, fianco e culla del pad.')
    def P(x, y):
        return (x - x0 + 1, y - y0 + 1)
    pts = [(x0, y0), (x1, y0), (x1, y1)]
    fessure = [FESSURA_OTG, FESSURA_FRONTE]
    if SPINA_PAD_TOP > M.Z_PIANO0 - 0.3:            # la spina del pad tocca il piano: una tacca nel bordo
        na, nb, ny = SPINA_PAD_X - 12.0, SPINA_PAD_X + 12.0, y1 - 8.0
        fx, fy, fw, fh = FESSURA_FRONTE
        if ny - (fy + fh) < 6.0 and fx < nb and fx + fw > na:    # la fessura della Flip è a due passi: una apertura sola
            na, nb, ny = min(na, fx), max(nb, fx + fw), fy
            fessure = [FESSURA_OTG]
        pts += [(nb, y1), (nb, ny), (na, ny), (na, y1)]
    pts.append((x0, y1))
    svg.poligono([P(x, y) for x, y in pts])
    for x, y in culla_viti() + visiera_viti():
        svg.cerchio(*P(x, y), 1.7)
    for fx, fy, fw, fh in fessure:
        svg.rett(*P(fx, fy), fw, fh, 3.0)
    # le manopole del pad, fra le due culle: dietro i tasti del pad ne resta in vista una striscia. La
    # legenda sta a sinistra della fessura della Flip: a destra, dietro m1 e m2, c'è la tacca della spina
    ya = CULLA_FLIP_Y1 + 3.0
    px = 0.12
    colonne = (0.0, 5.0, 21.0)
    largo = max(c + pixel_w(t, px) for riga in MANOPOLE_PAD for c, t in zip(colonne, riga))
    xa = FESSURA_FRONTE[0] - 3.0 - largo
    for c, testo in zip(colonne[1:], ('', 'DRUMS')):
        if testo:
            svg.pixel(*P(xa + c, ya), px, testo)
    for r, riga in enumerate(MANOPOLE_PAD):
        for c, testo in zip(colonne, riga):
            svg.pixel(*P(xa + c, ya + 3.1 * (r + 1)), px, testo)
    fr = piano((x0 - 1, y0 - 1, M.Z_PIANO), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    return registra(svg, _verso(fr, -1), M.ACR, 'acrilico', 6)


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
    """fianco della visiera nel piano (y, z): dal piano dietro la cerniera, lungo lo schermo fino
    sopra il bordo alto, e 24 mm davanti allo schermo"""
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
    return [(M.FLIP_Y0 - 6.0, M.Z_PIANO), (M.FLIP_Y0 + 4.0, M.Z_PIANO), (basso_davanti[0], basso_davanti[1]),
            alto_davanti, alto_dietro, (alto_dietro[0], M.Z_PIANO + 20.0)]


def tavola():
    W, Y = M.LARGHEZZA, M.BASE_Y1
    svg = Svg('tavola_insieme', W + 40, Y + 260, 'tavola d\'insieme: vista dall\'alto e fianco; non è un pezzo da tagliare.')
    ox, oy = 20, 20
    def T(x, y):
        return (x + ox, y + oy)
    # telaio: fianchi, retro, costola, parete davanti
    svg.rett(*T(0, 0), M.FIANCO, Y, 2, 'taglio')
    svg.rett(*T(W - M.FIANCO, 0), M.FIANCO, Y, 2, 'taglio')
    svg.rett(*T(M.FIANCO, M.RETRO_Y0), W - 2 * M.FIANCO, M.PLY, 0, 'taglio')
    svg.rett(*T(M.COSTOLA_X0, M.APPOGGIO_Y), 2 * M.PLY, Y - M.APPOGGIO_Y, 0, 'taglio')
    svg.rett(*T(M.DESTRA_X0, M.FRONTE_Y), M.DESTRA_X1 - M.DESTRA_X0, M.PLY, 0, 'taglio')
    # MK4 e mascherina con i fori
    svg.rett(*T(M.MK4_X0, M.MK4_Y0), M.MK4['w'], M.MK4['d'], 3, 'segno')
    g = M.MK4['guancia']
    for x in (M.MK4_X0 + g, M.MK4_X0 + M.MK4['w'] - g):          # le guance ai lati dei tasti
        svg.linea([T(x, M.MK4_Y0 + M.MK4_KEYBED_Y), T(x, M.MK4_Y0 + M.MK4['d'])], 'segno')
    for k in range(16):
        x = M.MK4_X0 + g + 1 + k * (M.MK4['w'] - 2 * g - 2) / 15
        svg.linea([T(x, M.MK4_Y0 + M.MK4_KEYBED_Y + 2), T(x, M.MK4_Y0 + M.MK4['d'] - 4.5)], 'segno')
    svg.rett(*T(MASC_X0, MASC_Y0), MASC_X1 - MASC_X0, MASC_Y1 - MASC_Y0, 0.6, 'taglio')
    for nome, (x, y, tipo) in M.MK4_CTRL.items():
        w, h, r = M.FORO[tipo]
        cx, cy = ctrl(nome)
        if tipo in ('k', 'e'):
            svg.cerchio(*T(cx, cy), w / 2, 'segno')
        else:
            svg.rett(*T(cx - w / 2, cy - h / 2), w, h, r, 'segno')
    # piano della Flip, culla, Flip e schermo aperto
    svg.rett(*T(PIANO_X0, PIANO_Y0), PIANO_X1 - PIANO_X0, M.PIANO_Y1 - PIANO_Y0, 0, 'taglio')
    cw = M.FLIP['w'] + 1.2 + 2 * M.CULLA_PARETE
    svg.rett(*T(M.FLIP_X - cw / 2, M.FLIP_Y0 - 0.6), cw, M.FLIP['d'] + 1.0 + M.CULLA_PARETE, 2, 'segno')
    svg.rett(*T(M.FLIP_X - M.FLIP['w'] / 2, M.FLIP_Y0), M.FLIP['w'], M.FLIP['d'], 3, 'segno')
    sch = M.FLIP['d'] * math.cos(math.radians(M.SCHERMO_DEG))
    svg.rett(*T(M.FLIP_X - M.FLIP['w'] / 2, M.FLIP_Y0 - sch), M.FLIP['w'], sch, 3, 'segno')
    # culla del pad e pad con tasti e manopole
    svg.rett(*T(M.DESTRA_X0 + 0.3, M.CULLA_PAD_Y0), M.DESTRA_X1 - M.DESTRA_X0 - 0.6, M.CULLA_PAD_Y1 - M.CULLA_PAD_Y0, 1, 'taglio')
    svg.poligono([T(x, y) for x, y in contorno_pad()[0]], 'segno')
    for r in range(3):
        for c in range(5):
            cx = M.PAD_X0 + M.PAD['k0'][0] + c * M.PAD['pitch_x']
            cy = M.PAD_Y0 + M.PAD['k0'][1] + r * M.PAD['pitch_y']
            svg.rett(*T(cx - 8, cy - 8), 16, 16, 1.5, 'segno')
    for nome, (kx, ky, kr) in M.PAD_KNOB.items():
        svg.cerchio(*T(M.PAD_X0 + kx, M.PAD_Y0 + ky), kr, 'segno')
    for txt, x, y in (('MPK MINI IV', M.MK4_X0 + 150, M.MK4_Y0 + 150), ('MASCHERINA', M.MK4_X0 + 150, 12),
                      ('FLIP', M.FLIP_X - 10, M.FLIP_Y0 - 22), ('PIANO DELLA FLIP', PIANO_X0 + 4, 12),
                      ('CULLA DEL PAD', M.DESTRA_X0 + 4, M.CULLA_PAD_Y0 - 4), ('COSTOLA', M.COSTOLA_X0 - 40, Y - 30)):
        svg.pixel(*T(x, y), 0.45, txt)
    svg.pixel(*T(0, Y + 8), 0.7, f'VISTA DALL\'ALTO   {W:.0f} x {Y:.0f} mm')
    # vista di fianco (da destra), sezione nella parte destra
    z_max = 200.0
    oy2 = oy + Y + 30
    def S(y, z):
        return (y + ox, oy2 + z_max - z)
    svg.poligono([S(y, z) for y, z in profilo_fianco()], 'taglio')
    svg.poligono([S(0, 0), S(Y, 0), S(Y, M.BASE_T), S(0, M.BASE_T)], 'segno')
    svg.poligono([S(0, M.BASE_T), S(M.PLY, M.BASE_T), S(M.PLY, M.Z_PIANO), S(0, M.Z_PIANO)], 'segno')
    svg.poligono([S(M.PLY, M.BASE_T), S(2 * M.PLY, M.BASE_T), S(2 * M.PLY, M.Z_APPOGGIO), S(M.PLY, M.Z_APPOGGIO)], 'segno')
    # piano della Flip e culla del pad in sezione
    svg.poligono([S(PIANO_Y0, M.Z_PIANO0), S(M.PIANO_Y1, M.Z_PIANO0), S(M.PIANO_Y1, M.Z_PIANO), S(PIANO_Y0, M.Z_PIANO)], 'taglio')
    c0, c1 = M.CULLA_PAD_Y0, M.CULLA_PAD_Y1
    zr = M.PAD_Z1 + M.CULLA_PAD_BORDO
    s = M.CULLA_PAD_PARETE
    svg.poligono([S(c0, M.BASE_T), S(c0 + s, M.BASE_T), S(c0 + s, zr), S(c0, zr)], 'taglio')
    svg.poligono([S(c1 - s, M.BASE_T), S(c1, M.BASE_T), S(c1, zr), S(c1 - s, zr)], 'taglio')
    svg.poligono([S(M.FRONTE_Y, M.BASE_T), S(Y, M.BASE_T), S(Y, M.Z_PIANO), S(M.FRONTE_Y, M.Z_PIANO)], 'segno')
    svg.poligono([S(M.PAD_Y0, M.PAD_Z0), S(M.PAD_Y1, M.PAD_Z0), S(M.PAD_Y1, M.PAD_Z1), S(M.PAD_Y0, M.PAD_Z1)], 'taglio')
    zt = M.PAD_Z1 + M.TASTO_PAD['z'] + M.TASTO_PAD['h']
    svg.poligono([S(M.PAD_Y0 + 5, M.PAD_Z1), S(M.PAD_Y1 - 5, M.PAD_Z1), S(M.PAD_Y1 - 5, zt), S(M.PAD_Y0 + 5, zt)], 'segno')
    zh0, zh1 = M.BASE_T + 2.0, M.BASE_T + 2.0 + M.HUB['h']             # l'hub sul fondo del fermo
    svg.poligono([S(M.HUB_Y0, zh0), S(M.HUB_Y0 + M.HUB['d'], zh0), S(M.HUB_Y0 + M.HUB['d'], zh1), S(M.HUB_Y0, zh1)], 'segno')
    sotto, sopra, vis = flip_aperta()
    svg.poligono([S(*p) for p in sotto], 'taglio')
    svg.poligono([S(*p) for p in sopra], 'taglio')
    svg.poligono([S(*p) for p in vis], 'segno')
    # la MK4 in trasparenza, dietro: la guancia di fianco ai tasti e il pannello
    y0m, y1m = M.MK4_Y0, M.MK4_Y0 + M.MK4['d']
    yk = M.MK4_Y0 + M.MK4_KEYBED_Y
    zg = M.BASE_T + M.MK4['guancia_h']
    svg.poligono([S(y0m, M.BASE_T), S(y1m, M.BASE_T), S(y1m, zg), S(yk, zg), S(yk, M.Z_MK4), S(y0m, M.Z_MK4)], 'segno')
    sc = ((sopra[0][0] + sopra[1][0]) / 2, (sopra[0][1] + sopra[1][1]) / 2)
    ey, ez = Y + 500.0, 350.0
    k = (Y + 30 - sc[0]) / (ey - sc[0])
    svg.linea([S(*sc), S(sc[0] + (ey - sc[0]) * k, sc[1] + (ez - sc[1]) * k)], 'segno')
    for txt, y, z in (('MK4 (DIETRO)', 120, 20), ('PIANO', 20, 52), ('HUB', M.HUB_Y0, zh1 + 5),
                      (f'SCHERMO {M.SCHERMO_DEG:.0f} GRADI', -8, 150), ('VISIERA', 40, 140), ('PAD', M.PAD_Y0 + 20, 74),
                      ('CULLA', M.CULLA_PAD_Y0 + 10, 14), ('SGUARDO 60 CM', 200, 120)):
        svg.pixel(*S(y, z), 0.45, txt)
    alt = max(p[1] for p in sopra)
    svg.pixel(*S(0, -14), 0.7, f'FIANCO   CIMA A {M.Z_PIANO:.0f} mm   CON LO SCHERMO APERTO {alt:.0f} mm   CENTRO DELLO SCHERMO A {sc[1]:.0f} mm')
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
    """Vassoio basso sul piano: fondo da 2 mm, bordi da 5 mm davanti e ai lati, aperto dietro
    (spalle L1 L2 R1 R2, cerniera, USB-C OTG). Davanti l'intaglio del jack e della USB-C di
    ricarica, ai lati le finestre dei tasti del volume [V: posizioni]. Quattro fori per viti M3
    svasate, sotto la Flip."""
    fw, fd = M.FLIP['w'] + 1.2, M.FLIP['d'] + 1.0
    p, h = M.CULLA_PARETE, M.CULLA_BORDO
    x0, x1 = M.FLIP_X - fw / 2, M.FLIP_X + fw / 2
    y0, y1 = M.FLIP_Y0 - 0.6, M.FLIP_Y0 - 0.6 + fd
    z0, zf = M.Z_PIANO, M.Z_PIANO + M.CULLA_FONDO
    ms = Mesh('Stame culla della Flip')
    viti = [cerchio(x, y, 1.7, 16) for x, y in culla_viti()]
    ms.prisma(rett(x0 - p, y0, x1 + p, y1 + p, 2.0), z0, zf, holes=viti)                  # fondo
    # bordo davanti con un intaglio solo per jack e USB-C, che stanno a 12 mm l'uno dall'altra
    ia, ib = M.FLIP_X + M.FLIP_JACK_DX - 6.5, M.FLIP_X + M.FLIP_USBC_DX + 7.0
    for a, b in ((x0 - p, ia), (ib, x1 + p)):
        ms.box(a, y1, zf, b, y1 + p, zf + h)
    # bordi laterali: liberi i tasti sul fianco, vicino alla cerniera
    ya = M.FLIP_Y0 + M.FLIP_TASTI_LATO[1] + 4.0
    for xa, xb in ((x0 - p, x0), (x1, x1 + p)):
        ms.box(xa, ya, zf, xb, ya + 18.0, zf + h)
        ms.box(xa, y0 + 60.0, zf, xb, y1, zf + h)
    return ms


def _sezioni_y(loop, x):
    """intervalli di y dove la verticale x sta dentro il contorno"""
    ys = []
    for i in range(len(loop)):
        (xa, ya), (xb, yb) = loop[i - 1], loop[i]
        if (xa - x) * (xb - x) < 0:
            ys.append(ya + (yb - ya) * (x - xa) / (xb - xa))
    ys.sort()
    return [(ys[k], ys[k + 1]) for k in range(0, len(ys) - 1, 2)]


def culla_pad():
    """Culla del macro pad (Luigi, 18/10/2026: «per il pad vorrei una culla simile a quella che hai
    fatto per il flip»), sul contorno vero del pad (foto del 18/10/2026). Sta in piedi sulla base e
    riempie la parte destra davanti, fra costola, fianco e parete davanti; dentro ha la sagoma del pad
    con 0,5 mm di gioco, lobo compreso. Il pad poggia su sei costole con la piastra a filo del piano, e
    la culla finisce lì (Luigi, 19/10/2026: tutto a pari); se CULLA_PAD_BORDO la fa salire oltre la
    piastra, davanti si apre la tacca per la flangia della manopola grande. Dietro un dente regge il
    bordo del piano della Flip e una finestra fa passare la spina del pad (a 90°, verso il basso). Le pareti vanno dagli
    angoli della culla a quelli del pad: dove serve un'apertura si taglia solo la parete che la porta.
    Si stampa in piedi, senza supporti."""
    x0, x1 = M.DESTRA_X0 + 0.3, M.DESTRA_X1 - 0.3
    y0, y1 = M.CULLA_PAD_Y0, M.CULLA_PAD_Y1
    z0, zr = M.BASE_T, M.PAD_Z1 + M.CULLA_PAD_BORDO
    dentro, (m0, m1, m2, m3) = contorno_pad(M.CULLA_PAD_GIOCO)
    ms = Mesh('Stame culla del macro pad')
    retro = [(x0, y0), (x1, y0)] + dentro[m0:m1 + 1][::-1]
    destra = [(x1, y0), (x1, y1)] + dentro[m1:m2 + 1][::-1]
    davanti = [(x1, y1), (x0, y1)] + dentro[m2:m3 + 1][::-1]
    sinistra = [(x0, y1), (x0, y0)] + (dentro[m3:] + dentro[:m0 + 1])[::-1]

    def parete(poly, za, zb, aperture=()):
        """la parete da za a zb, con le aperture (xa, xb) lasciate vuote"""
        pezzi = [poly]
        for a, b in aperture:
            pezzi = [q for p in pezzi for q in (taglia(p, 0, a, True), taglia(p, 0, b, False))
                     if len(q) >= 3 and abs(area(q)) > 0.01]
        for p in pezzi:
            ms.prisma(p, za, zb)
    # dietro: la finestra della spina, che esce dal pad 9 mm sopra il fondo e scende verso l'hub, e
    # quella della levetta dell'interruttore, che sporge dal retro più del gioco
    fa, fb = SPINA_PAD_X - 11.0, SPINA_PAD_X + 11.0
    sa, sb = M.PAD_X0 + M.PAD_INTERRUTTORE_X - 5.0, M.PAD_X0 + M.PAD_INTERRUTTORE_X + 5.0
    zf = min(SPINA_PAD_TOP + 1.0, zr - 2.0)
    parete(retro, z0, zf, [(sa, sb), (fa, fb)])
    parete(retro, zf, zr)
    parete(destra, z0, zr)
    parete(sinistra, z0, zr)
    # davanti: fino alla piastra; se il bordo sale oltre, la tacca per la flangia della manopola grande
    mx = M.PAD_X0 + M.PAD_KNOB['M'][0]
    # davanti la betulla si ferma a FRONTE_Z; sopra, il bordo arrotondato continua la curva dei fianchi
    # fino alla piastra (sporge 4 mm sopra la parete di betulla: si stampa senza supporti)
    R, ya = M.FIANCO_R, M.PAD_Y1 + M.CULLA_PAD_GIOCO + 0.5      # 0,5 dietro il lobo: niente strisce di spessore zero
    parete(davanti, z0, M.FRONTE_Z)
    dietro = taglia(davanti, 1, ya, True)
    if len(dietro) >= 3 and abs(area(dietro)) > 0.01:
        ms.prisma(dietro, M.FRONTE_Z, M.PAD_Z1)
    arco = [p for p in _arco((M.BASE_Y1 - R, M.Z_PIANO - R), R, 0, 90, 16) if p[0] >= ya]
    ms.prisma_x([(ya, M.FRONTE_Z), (M.BASE_Y1, M.FRONTE_Z)] + arco + [(ya, arco[-1][1])], x0, x1)
    if zr > M.PAD_Z1:
        parete(davanti, M.PAD_Z1, zr, [(mx - M.PAD_FLANGIA - 2.0, mx + M.PAD_FLANGIA + 2.0)])
    # dente per il bordo del piano della Flip, con lo smusso a 45° sotto (si stampa senza supporti)
    d = M.CULLA_DENTE
    za = M.Z_APPOGGIO
    dente = [(y0 - d, za), (y0 - d, za - 2.0), (y0, za - 2.0 - d), (y0, za)]
    for a, b in ((x0, sa), (sb, fa), (fb, x1)):
        ms.prisma_x(dente, a, b)
    # sei costole sotto il pad, da parete a parete
    for k in range(1, 7):
        cx = M.PAD_X0 + M.PAD['w'] * k / 7
        for ya, yb in _sezioni_y(dentro, cx):
            ms.box(cx - 1.2, ya - 0.5, z0, cx + 1.2, yb + 0.5, M.PAD_Z0)
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
        ms.prisma(rett(x - 7, y - 7, x + 7, y + 7, 2), M.Z_PIANO, M.Z_PIANO + 4.0, holes=[cerchio(x, y, 1.7, 16)])
        # piede collegato al fianco
        xf = xa if x < M.FLIP_X else xb
        ms.box(min(x, xf), y - 3, M.Z_PIANO, max(x, xf + sp), y + 3, M.Z_PIANO + 4.0)
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
    """vassoio dell'hub: dietro e a sinistra la sponda sale a 0,6 dell'hub; davanti, dove sono le
    porte, e a destra, dove esce il cavo, resta un bordino di 3 mm sotto le prese"""
    ms = Mesh('Stame fermo dell\'hub')
    w, d, h = M.HUB['w'] + 0.8, M.HUB['d'] + 0.8, M.HUB['h']
    fr = sposta(M.HUB_X0, M.HUB_Y0, M.BASE_T)
    ms.prisma(rett(-3, -3, w + 3, d + 3, 2), 0, 2.0, frame=fr)
    ms.prisma(rett(-3, -3, w + 3, d + 3, 2), 2.0, 5.0, holes=[rett(0, 0, w, d, 1)], frame=fr)
    ms.prisma(rett(-3, -3, w + 3, 0, 0.5), 5.0, h * 0.6, frame=fr)
    ms.prisma(rett(-3, 0, 0, d + 3, 0.5), 5.0, h * 0.6, frame=fr)
    for x in (-10, w + 10):
        ms.prisma(rett(x - 6, d / 2 - 6, x + 6, d / 2 + 6, 3), 0, 2.0, holes=[cerchio(x, d / 2, 1.25, 16)], frame=fr)
    return ms


# colonnina sotto il piano della Flip (CASE-046): con l'acrilico da 2 mm il piano, che poggia solo sui
# bordi, regge la culla e la Flip anche nel mezzo. Sta sotto la culla, davanti alle spine dell'hub e a
# 30 mm dalle viti della culla; una vite 3 × 12 da sotto la base, feltro in cima come sugli appoggi
COLONNINA = (M.FLIP_X, 128.0)


def colonnina():
    ms = Mesh('Stame colonnina del piano')
    x, y = COLONNINA
    ms.cilindro(x, y, M.BASE_T, M.BASE_T + 2.0, 10.0, 40)
    ms.prisma(cerchio(x, y, 6.0, 32), M.BASE_T + 2.0, M.Z_APPOGGIO, holes=[cerchio(x, y, 1.3, 16)])
    return ms


# scritte dei tasti del macro pad (CASE-043, 40 MIDI-120, MIDI-133): il nome nella mappa del pad.
# Vanno sulle etichette di carta dei tasti trasparenti (etichette.py)
COPRITASTI = [['HOLD'], ['TAP'], ['METRO'], ['FILL'], ['DROP'],
              ['SCENE', '1'], ['SCENE', '2'], ['SCENE', '3'], ['SCENE', '4'], ['VIEW'],
              ['OPT'], ['SAVE', 'LOOP'], ['DRUMS'], ['PANIC'], ['PAGE']]


# ---------------------------------------------------------------------------------------------
# fogli di taglio: i pezzi del laser impaginati per materiale (CASE-003: piano del laser)

MATERIALI = {'betulla4': f'compensato di betulla {M.PLY:.0f} mm', 'betulla6': f'compensato di betulla {M.BASE_T:.0f} mm',
             'acrilico': f'acrilico nero {M.ACR:.0f} mm'}
FOGLIO = M.LASER_BED
STACCO = 4.0


def _in_colonna(f, q):
    """il pezzo, girato in piedi, nella colonna libera a destra degli scaffali del foglio"""
    p, k, ruota, (w, h) = q
    if 'col' not in f:
        x0 = max(sc['x'] for sc in f['scaffali'])
        if x0 + h > FOGLIO[0] - STACCO or STACCO + w > FOGLIO[1] - STACCO:
            return False
        f['col'] = dict(x=x0, y=STACCO, w=FOGLIO[0] - STACCO - x0)
        f['xmax'] = x0 - STACCO
    c = f['col']
    if h > c['w'] or c['y'] + w > FOGLIO[1] - STACCO:
        return False
    f['pezzi'].append(((p, k, not ruota, (h, w)), c['x'], c['y']))
    c['y'] += w + STACCO
    return True


def impagina():
    """scaffali: pezzi per altezza decrescente, ruotati di 90° se così stanno meglio; quello che non
    entra più negli scaffali va in piedi nella colonna libera a destra, prima di aprire un altro foglio"""
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
                    if h <= sc['h'] and sc['x'] + w <= f.get('xmax', FOGLIO[0] - STACCO):
                        f['pezzi'].append((q, sc['x'], sc['y']))
                        sc['x'] += w + STACCO
                        messo = True
                        break
                if messo:
                    break
                y = f['y']
                if y + h <= FOGLIO[1] - STACCO and STACCO + w <= f.get('xmax', FOGLIO[0] - STACCO):
                    f['scaffali'].append(dict(y=y, h=h, x=STACCO + w + STACCO))
                    f['pezzi'].append((q, STACCO, y))
                    f['y'] = y + h + STACCO
                    messo = True
                    break
            for f in ([] if messo else aperti):
                if _in_colonna(f, q):
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

# pezzi delle bozze 2-4 che non esistono più: si tolgono da out/
OBSOLETI = ['mascherina_sx.svg', 'mascherina_dx.svg', 'ponte_sopra_sx.svg', 'ponte_sopra_dx.svg',
            'ponte_fronte_sx.svg', 'ponte_fronte_dx.svg', 'ponte_retro_sx.svg', 'ponte_retro_dx.svg',
            'centine.svg', 'vassoio_pad.stl', 'colonnina.stl', 'divisorio.svg', 'torre_piano.svg',
            'torre_fronte.svg', 'torre_retro.svg', 'cartellino_pad.svg', 'cornice_pad.stl',
            'piedino_mascherina.stl']


def genera():
    """tutti i pezzi; torna le liste per la stampa a video e per assieme.py"""
    os.makedirs(OUT, exist_ok=True)
    for n in OBSOLETI:
        p = os.path.join(OUT, n)
        if os.path.exists(p):
            os.remove(p)
    LASER.clear()
    STAMPATI.clear()
    laser = [mascherina(), dima(), retro('sx'), retro('dx'), appoggio_retro('sx'), appoggio_retro('dx'),
             fianco('fianco_sx_esterno', [('sx', 0)], incisa=True),
             fianco('fianco_dx_esterno', [('dx', 0)], incisa=True),
             fianco('fianco_interno', [('sx', 1), ('sx', 2), ('dx', 1), ('dx', 2)]),
             fianco('fianco_sx_appoggio', [('sx', 3)], basso=(M.RETRO_Y, M.MASCHERINA_Y1), viti=True),
             fianco('fianco_dx_appoggio', [('dx', 3)], basso=(M.RETRO_Y, M.CULLA_PAD_Y0), viti=True),
             base('sx'), base('dx'), costola('sx'), costola('dx'), fronte(), piano_flip(), tavola()]
    stampato('culla_flip', culla_flip(), IDENTITA, 6, 'vassoio sul piano della Flip, 4 viti M3 svasate')
    stampato('visiera', visiera(), IDENTITA, 6, 'si avvita al piano dietro la culla; stampare sul tettuccio, con supporti')
    stampato('culla_pad', culla_pad(), IDENTITA, 5, 'sta sulla base fra costola, fianco e parete davanti; si stampa in piedi')
    stampato('fermo_hub', fermo_hub(), IDENTITA, 4, 'tiene l\'hub sotto il piano, 2 viti nella base')
    stampato('colonnina', colonnina(), IDENTITA, 4, 'regge il piano della Flip sotto la culla; una vite 3 × 12 da sotto la base')
    stampato('squadretta_m3', squadretta(), squadrette_frames(), 3, 'base e fianchi, viti M3')
    return laser


def main():
    laser = genera()
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
    print(f'INGOMBRO {M.LARGHEZZA:.1f} x {M.BASE_Y1:.1f} mm, cima a {M.Z_PIANO:.0f} mm')


if __name__ == '__main__':
    main()
