"""stampa3d.py — la console tutta stampata, a vasche, per chi non ha il laser.

Luigi, 18/10/2026: «crea anche tutto quello che serve per farla tutta stampata 3d (per chi non ha il laser)»;
19/10/2026: «per la versione totalmente stampata in 3d, credo che non sia necessario replicare gli stessi pezzi
che vengono tagliati, sono sicuro che si possa ridurre il numero di pezzi e stampare più parti già assemblate in
un unico modello».

Uso: python -I hardware/case/stampa3d.py [--piatto 210]      scrive in hardware/case/out/stampa3d/

60-case.md §7b, CASE-060…CASE-066. Il telaio non ricopia i pezzi del laser: si stampa in vasche. Una vasca è un
tratto di console già montato, stampato in piedi con il fondo sul piatto: il fondo, il fianco con il suo profilo,
il retro arretrato con le finestre, la costola con il passaggio dei cavi, la parete davanti, gli appoggi del piano
alla quota del feltro e, nella vasca di destra, il fermo dell'hub, la colonnina e la culla del pad. Niente
squadrette, niente linguette, niente strati da incollare; le sagome esterne e le sedi interne sono quelle di
misure.py e di genera.py.
- Tre colonne (TAGLI_X): una giunta a metà sotto la MK4, una fra la costola e la culla del pad, che resta intera
  nella vasca di destra. Con un piatto da 240 (la Kobra S1; la console è profonda 240) ogni colonna è una vasca
  intera davanti-dietro; con un piatto più piccolo, da 208 in su, le colonne si dividono anche a y = TAGLIO_Y,
  fra la colonnina e la culla: sei vasche.
- Le giunte: nel fondo code di rondine verticali, che si infilano dall'alto calando una vasca accanto all'altra;
  le pareti che attraversano la giunta (il retro, e con sei vasche i fianchi e la costola) si sormontano a mezzo
  spessore per SORMONTO mm, chiuse da due viti M3 con il dado nella sua sede. Le code tengono le vasche
  allineate nel piano, le viti le tengono insieme in altezza: niente colla, e la console si smonta.
- Restano a parte i pezzi che si tolgono per arrivare ai cavi: la mascherina, in due metà accostate (i fori sui
  comandi della MK4 tengono ogni metà al suo posto), e il piano della Flip, tutti e due con le tasche delle
  etichette di carta; la culla della Flip e la cornice dello schermo sono quelle di genera.py.
- Sui fianchi il marchio e il nome escono in rilievo dalla faccia di fuori, che stampata in piedi è verticale.
Ogni STL esce nel verso fisico giusto (il riferimento del case si specchia su y), con la faccia giusta sul piatto,
e ogni guscio è chiuso; le vasche vicine non si compenetrano e lasciano libere le sedi (sedi_occupate).
pezzi.md elenca pezzi, viti e impostazioni; prova_giunta.stl è un pezzetto di giunta da stampare prima delle
vasche.
"""
import math
import os
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import genera as G                   # noqa: E402
import misure as M                   # noqa: E402
from mesh import Mesh, rett, cerchio, applica, taglia, area, sposta, IDENTITA   # noqa: E402

OUT3D = os.path.join(G.OUT, 'stampa3d')
SOVRAPPOSTO = 0.2           # due solidi di uno stesso pezzo si compenetrano: lo slicer li fonde
MARGINE_TAGLIO = 1.5        # il taglio fra le due metà della mascherina passa ad almeno 1,5 mm da fori e tasche
DENSITA = 1.27              # g/cm³, PETG (il PLA è 1,24)

# ---- le vasche ----
FONDO = 3.0                 # il fondo dove non appoggia niente; sotto la MK4 (la pedana), dietro il retro e lungo le
                            # giunte è pieno fino a BASE_T, la quota su cui stanno MK4, culla e fermo nella console laser
SORMONTO = 12.0             # le pareti che attraversano una giunta si sormontano a mezzo spessore per 12 mm
FASCIA = SORMONTO           # lungo ogni giunta il fondo è pieno per 12 mm: lì stanno le code e le loro sedi
TAGLI_X = (M.COSTOLA_X1 / 2, M.COSTOLA_X1)   # 187,75: a metà sotto la MK4; 375,5: fra costola e culla del pad
TAGLIO_Y = 143.0            # solo per i piatti sotto i 240: davanti alla colonnina (fino a 138), dietro la culla (da 148,3,
                            # il dente; le viti del sormonto a 149 restano fuori dalle sue pareti, da 152,3)
INTERNO = (M.FIANCO, M.LARGHEZZA - M.FIANCO)  # 16 e 567,5: le facce dentro dei fianchi
PASSO_CODE = 55.0           # una coda di rondine ogni 55 mm circa
VITI_Z = (12.0, 32.0)       # le due viti di ogni sormonto, sotto gli appoggi del piano
FORO_VITE = 1.7             # M3, foro passante
TESTA = 3.1                 # sede della testa di una vite a brugola M3 (⌀ 5,5 × 3)
SEDE_TESTA = {8.0: 3.4, 16.0: 4.2}   # profondità della sede per pareti da 8 e da 16: restano 4,8 e 12 mm da stringere
VITE = {8.0: 6, 16.0: 12}            # la vite che ci va: la punta passa tutto il dado
DADO = (3.3, 2.8)           # sede del dado M3 (5,5 fra le facce): raggio del cerchio circoscritto, profondità


# ---------------------------------------------------------------------------------------------
# riferimenti: il piano di un pezzo stampato è (O, U, V, N); (u, v) sul piano, w lungo lo spessore

def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def locale(F, P):
    O, U, V, N = F
    d = (P[0] - O[0], P[1] - O[1], P[2] - O[2])
    return (_dot(d, U), _dot(d, V), _dot(d, N))


def _det(F):
    _, U, V, N = F
    c = (U[1] * V[2] - U[2] * V[1], U[2] * V[0] - U[0] * V[2], U[0] * V[1] - U[1] * V[0])
    return _dot(c, N)


def inversa(fr):
    """l'inversa di un riferimento ortonormale (O, U, V, N)"""
    O, U, V, N = fr
    o = (-_dot(O, U), -_dot(O, V), -_dot(O, N))
    return (o, (U[0], V[0], N[0]), (U[1], V[1], N[1]), (U[2], V[2], N[2]))


def _laser(nome):
    return next(p for p in G.LASER if p['nome'] == nome)


def strato(nome, F, copia=0):
    """uno strato di un pezzo del laser nel piano F: contorno, fori e quote w0, w1"""
    p = _laser(nome)
    fr = p['frames'][copia]
    outer, holes = p['svg'].contorni()

    def uv(loop):
        return [tuple(round(c, 4) for c in locale(F, applica(fr, (x, y, 0.0)))[:2]) for x, y in loop]
    wa = locale(F, applica(fr, (outer[0][0], outer[0][1], 0.0)))[2]
    wb = locale(F, applica(fr, (outer[0][0], outer[0][1], p['t'])))[2]
    return dict(outer=uv(outer), holes=[uv(h) for h in holes], w0=round(min(wa, wb), 4), w1=round(max(wa, wb), 4))


def _bbox(loop):
    xs = [p[0] for p in loop]
    ys = [p[1] for p in loop]
    return (min(xs), min(ys), max(xs), max(ys))


def incisioni(nome, F, copia=0):
    """le incisioni di un pezzo del laser nel piano F, con lo spessore del tratto (per sapere se un
    ugello da 0,4 mm ce la fa): cerchio = diametro, rettangolo = lato corto, tratto = 2 area/perimetro"""
    p = _laser(nome)
    fr = p['frames'][copia]
    out = []
    for el in p['svg'].incisione:
        for loop in G._parse_svg_el(el):
            uv = [tuple(round(c, 4) for c in locale(F, applica(fr, (x, y, 0.0)))[:2]) for x, y in loop]
            b = _bbox(loop)
            if el.startswith('<circle'):
                s = b[2] - b[0]
            elif el.startswith('<rect'):
                s = min(b[2] - b[0], b[3] - b[1])
            else:
                per = sum(math.dist(loop[i - 1], loop[i]) for i in range(len(loop)))
                s = 2 * abs(area(loop)) / per if per else 0.0
            out.append(dict(loop=uv, spessore=s, el=el, disegno=loop))
    return out


# ---------------------------------------------------------------------------------------------
# i pezzi nel loro piano: le pareti delle vasche, la mascherina e il piano della Flip

class Pezzo:
    def __init__(self, nome, F, colore, nota):
        self.nome, self.F, self.colore, self.nota = nome, F, colore, nota
        self.strati = []        # (contorno, fori, w0, w1)
        self.rilievi = []       # (contorno, w0, w1)
        self.tasche = []        # dict(rett=(u0, v0, u1, v1), n, elementi)
        self.regioni = []       # scritte stampate a più colori (multicolore.py): dict(rett, testo, fondo)
        self.faccia = None      # quota w della faccia in vista, dove stanno le tasche
        self.T = None           # pareti: lo spessore; w = 0 è la faccia dei dadi, w = T quella delle teste
        self.sotto = []         # pareti: [(w0, w1, profilo, fori)], la metà dentro (w < T/2) e quella fuori


def _finestre():
    """le finestre del retro (pedale; alimentazione e audio sopra l'hub), nel piano (x, z)"""
    out = []
    for lato in ('sx', 'dx'):
        zt = M.BASE_T + G.USCITE_Z[lato]
        for cx in G.USCITE[lato]:
            out.append(rett(cx - 14.0, zt - 12.0, cx + 14.0, zt, 6.0))
    return out


def retro():
    """il retro, arretrato fin dove finisce la curva dei fianchi: fuori arriva in cima, dentro si ferma
    all'appoggio del piano (il feltro sopra); le finestre passano tutti e due"""
    F = ((0.0, M.APPOGGIO_Y, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0))     # w = 16 - y
    a, b = INTERNO[0] - SOVRAPPOSTO, INTERNO[1] + SOVRAPPOSTO
    pz = Pezzo('retro', F, 'telaio', '')
    pz.T = 2 * M.PLY
    fin = _finestre()
    pz.sotto = [(0.0, M.PLY, rett(a, 0.0, b, M.Z_APPOGGIO), fin), (M.PLY, 2 * M.PLY, rett(a, 0.0, b, M.Z_PIANO), fin)]
    return pz


def _profilo_costola(yb):
    """la costola di fianco (y, z): dietro un ponte sopra il passaggio dei cavi, da yb in poi la cima a filo
    del piano, davanti l'arco dei fianchi"""
    y0, Y, H, R = M.APPOGGIO_Y - SOVRAPPOSTO, M.BASE_Y1, M.Z_PIANO, M.FIANCO_R
    return ([(y0, G.CAVI_Z), (M.MK4_Y0, G.CAVI_Z), (M.MK4_Y0, 0.0), (Y, 0.0)]
            + G._arco((Y - R, H - R), R, 0, 90) + [(yb, H), (yb, M.Z_APPOGGIO), (y0, M.Z_APPOGGIO)])


def costola():
    """la costola fra MK4 e culla del pad: la metà verso la MK4 regge la mascherina fino al suo bordo, quella
    verso il pad il piano della Flip fino alla culla"""
    F = ((M.COSTOLA_X1, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (-1.0, 0.0, 0.0))     # w = 375,5 - x
    pz = Pezzo('costola', F, 'telaio', '')
    pz.T = 2 * M.PLY
    pz.sotto = [(0.0, M.PLY, _profilo_costola(M.CULLA_PAD_Y0), []), (M.PLY, 2 * M.PLY, _profilo_costola(M.MASCHERINA_Y1), [])]
    return pz


def fianco(lato):
    """un fianco intero, 16 mm: dentro lo strato d'appoggio più basso sotto il piano, fuori il marchio e il nome
    in rilievo (le incisioni più fini di DETTAGLIO_MIN non si stampano)"""
    if lato == 'sx':
        F = ((INTERNO[0], 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (-1.0, 0.0, 0.0))  # w = 16 - x
        basso = (M.RETRO_Y, M.MASCHERINA_Y1)
    else:
        F = ((INTERNO[1], 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))   # w = x - 567,5
        basso = (M.RETRO_Y, M.CULLA_PAD_Y0)
    pz = Pezzo(f'fianco_{lato}', F, 'telaio', '')
    pz.T = M.FIANCO
    pieno = G.profilo_fianco()
    pz.sotto = [(0.0, M.PLY + SOVRAPPOSTO, G.profilo_fianco(basso), []), (M.PLY, M.FIANCO / 2, pieno, []),
                (M.FIANCO / 2, M.FIANCO, pieno, [])]
    for inc in incisioni(f'fianco_{lato}_esterno', F):
        if inc['spessore'] >= M.DETTAGLIO_MIN:
            pz.rilievi.append((inc['loop'], M.FIANCO - SOVRAPPOSTO, M.FIANCO + M.RILIEVO))
    return pz


def _esagono(cx, cy, r):
    """la sede del dado, con uno spigolo in alto: stampata in piedi, il tetto regge da sé"""
    return [(cx + r * math.cos(math.radians(90 + 60 * k)), cy + r * math.sin(math.radians(90 + 60 * k))) for k in range(6)]


def _ritaglia(prof, a, b):
    p = prof
    if a is not None:
        p = taglia(p, 0, a, False)
    if b is not None and len(p) >= 3:
        p = taglia(p, 0, b, True)
    return p if len(p) >= 3 and abs(area(p)) > 0.01 else None


def _nel_tratto(loop, a, b, nome):
    bb = _bbox(loop)
    if (a is not None and bb[2] <= a) or (b is not None and bb[0] >= b):
        return False
    assert (a is None or bb[0] >= a) and (b is None or bb[2] <= b), f'{nome}: un foro o una scritta sulla giunta'
    return True


def tratto(pz, lo=None, hi=None, giunta_lo=True, giunta_hi=True):
    """il tratto di una parete fra lo e hi (lungo u; None: la parete finisce da sé). A una giunta la metà
    dentro si ferma sulla giunta e quella fuori la passa di SORMONTO (dalla parte di hi) o comincia SORMONTO dopo
    (dalla parte di lo): così le due vasche si sormontano a mezzo spessore. Nel sormonto due viti, con la testa
    nella faccia di fuori della vasca di prima e il dado in quella di dentro della vasca dopo. Un taglio libero
    (giunta False, la prova) taglia dritto. Torna dict(strati, rilievi, tasche, regioni, viti) come i pezzi"""
    T = pz.T

    def campo(fuori):
        a = None if lo is None else lo + (SORMONTO if fuori and giunta_lo else 0.0)
        b = None if hi is None else hi + (SORMONTO if fuori and giunta_hi else 0.0)
        return a, b
    teste = [(hi + SORMONTO / 2, z) for z in VITI_Z] if hi is not None and giunta_hi else []
    dadi = [(lo + SORMONTO / 2, z) for z in VITI_Z] if lo is not None and giunta_lo else []
    sede = SEDE_TESTA[T]
    strati = []
    for w0, w1, prof, fori in pz.sotto:
        fuori = w0 >= T / 2 - 1e-6
        a, b = campo(fuori)
        p = _ritaglia(prof, a, b)
        if p is None:
            continue
        f = [h for h in fori if _nel_tratto(h, a, b, pz.nome)]
        viti = [v for v in teste + dadi if (a is None or v[0] > a) and (b is None or v[0] < b)]
        tondi = [cerchio(u, v, FORO_VITE, 16) for u, v in viti]
        if fuori and abs(w1 - T) < 1e-6 and viti:          # la sede delle teste, nella faccia di fuori
            strati.append((p, f + tondi, w0, T - sede + SOVRAPPOSTO))
            strati.append((p, f + [cerchio(u, v, TESTA, 24) for u, v in viti], T - sede, T))
        elif not fuori and w0 < 1e-6 and viti:             # la sede dei dadi, nella faccia di dentro
            strati.append((p, f + [_esagono(u, v, DADO[0]) for u, v in viti], 0.0, DADO[1]))
            strati.append((p, f + tondi, DADO[1] - SOVRAPPOSTO, w1))
        else:
            strati.append((p, f + tondi, w0, w1))
    # la cucitura fra le due metà, dove ci sono tutte e due: lo slicer le fonde
    (ai, bi), (ao, bo) = campo(False), campo(True)
    a = None if ai is None and ao is None else max(x for x in (ai, ao) if x is not None)
    b = None if bi is None and bo is None else min(x for x in (bi, bo) if x is not None)
    w0, w1, prof, fori = max((s for s in pz.sotto if s[0] < T / 2 - 1e-6), key=lambda s: s[1])
    p = _ritaglia(prof, a, b)
    if p is not None:
        strati.append((p, [h for h in fori if _nel_tratto(h, a, b, pz.nome)], T / 2 - SOVRAPPOSTO, T / 2 + SOVRAPPOSTO))
    return dict(strati=strati, tasche=[], angolo=0,
                rilievi=[r for r in pz.rilievi if _nel_tratto(r[0], ao, bo, pz.nome)],
                regioni=[r for r in pz.regioni if _nel_tratto(rett(*r['rett']), ao, bo, pz.nome)],
                viti=[(T, VITE[T])] * len(teste))


def piano(nome, n0):
    """mascherina o piano della Flip: lastra nera spessa come l'acrilico, con una tasca per ogni gruppo di scritte"""
    F = ((0.0, 0.0, M.Z_PIANO0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    s = strato(nome, F)
    pz = Pezzo(nome, F, 'piano', f'lastra da {_v(M.ACR)} mm, la faccia in vista in alto; le scritte su carta adesiva, nelle tasche')
    pz.strati.append((s['outer'], s['holes'], s['w0'], s['w1']))
    pz.faccia = s['w1']
    pz.tasche = tasche(incisioni(nome, F), s['holes'], s['outer'], n0)
    return pz


# ---------------------------------------------------------------------------------------------
# tasche delle etichette: le scritte vicine fanno un gruppo; la tasca è il gruppo con 0,8 mm di
# margine, a 0,6 mm almeno da ogni foro, e due tasche non si toccano

TASCA_MARGINE = 0.8
TASCA_PARETE = 0.6


def _tocca(a, b, d=0.0):
    return a[0] < b[2] + d and b[0] < a[2] + d and a[1] < b[3] + d and b[1] < a[3] + d


def _unione(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def tasche(incs, holes, outer, n0):
    vicino = 2 * TASCA_MARGINE + TASCA_PARETE
    # prima i gruppi per vicinanza fra le singole scritte (union-find su una griglia di 5 mm)...
    rr = [_bbox(i['loop']) for i in incs]
    padre = list(range(len(rr)))

    def radice(a):
        while padre[a] != a:
            padre[a] = padre[padre[a]]
            a = padre[a]
        return a
    griglia = {}
    for k, r in enumerate(rr):
        for gx in range(int((r[0] - vicino) // 5), int((r[2] + vicino) // 5) + 1):
            for gy in range(int((r[1] - vicino) // 5), int((r[3] + vicino) // 5) + 1):
                griglia.setdefault((gx, gy), []).append(k)
    for lista in griglia.values():
        for a in range(len(lista)):
            for b in range(a + 1, len(lista)):
                if radice(lista[a]) != radice(lista[b]) and _tocca(rr[lista[a]], rr[lista[b]], vicino):
                    padre[radice(lista[a])] = radice(lista[b])
    per_radice = {}
    for k, i in enumerate(incs):
        g = per_radice.setdefault(radice(k), dict(r=rr[k], el=[]))
        g['r'] = _unione(g['r'], rr[k])
        g['el'].append(i)
    # ...poi i gruppi i cui ingombri si avvicinano troppo diventano uno: due tasche non si toccano
    gruppi = list(per_radice.values())
    cambiato = True
    while cambiato:
        cambiato = False
        for i in range(len(gruppi)):
            for j in range(i + 1, len(gruppi)):
                if _tocca(gruppi[i]['r'], gruppi[j]['r'], vicino):
                    gruppi[i] = dict(r=_unione(gruppi[i]['r'], gruppi[j]['r']), el=gruppi[i]['el'] + gruppi[j]['el'])
                    del gruppi[j]
                    cambiato = True
                    break
            if cambiato:
                break
    fori = [_bbox(h) for h in holes]
    ob = _bbox(outer)

    def stringi(r, parete):
        """stringe r dal lato di ogni foro che tocca (con la parete), senza entrare nelle scritte;
        torna False se un foro resta troppo vicino"""
        for f in fori:
            fa = (f[0] - parete, f[1] - parete, f[2] + parete, f[3] + parete)
            if not _tocca(r, fa):
                continue
            prove = [(fa[0] - r[2], 2, fa[0]), (r[0] - fa[2], 0, fa[2]), (fa[1] - r[3], 3, fa[1]), (r[1] - fa[3], 1, fa[3])]
            for _, k, val in sorted(prove, key=lambda t: -t[0]):
                if (k == 2 and val >= x1) or (k == 0 and val <= x0) or (k == 3 and val >= y1) or (k == 1 and val <= y0):
                    r[k] = val
                    break
            else:
                return False
        return True
    out = []
    for g in sorted(gruppi, key=lambda g: (round(g['r'][1] / 10), g['r'][0])):
        x0, y0, x1, y1 = g['r']
        r = [x0 - TASCA_MARGINE, y0 - TASCA_MARGINE, x1 + TASCA_MARGINE, y1 + TASCA_MARGINE]
        tasca = stringi(r, TASCA_PARETE)
        if not tasca:          # fra due fori vicini non c'è posto per la parete: etichetta piana, senza tasca
            r = [x0 - 0.3, y0 - 0.3, x1 + 0.3, y1 + 0.3]
            stringi(r, 0.0)
        r = [max(r[0], ob[0] + 1.0), max(r[1], ob[1] + 1.0), min(r[2], ob[2] - 1.0), min(r[3], ob[3] - 1.0)]
        out.append(dict(rett=tuple(round(c, 3) for c in r), elementi=g['el'], tasca=tasca))
    for k, t in enumerate(out):
        t['n'] = n0 + k
    return out


# ---------------------------------------------------------------------------------------------
# la mascherina in due metà: un taglio dritto, lontano da fori, tasche e scritte; niente giunta

def _ostacoli(pz):
    """rettangoli che il taglio non deve toccare"""
    obs = []
    for _, holes, _, _ in pz.strati:
        obs += [_bbox(h) for h in holes]
    obs += [t['rett'] for t in pz.tasche]
    obs += [_bbox(r[0]) for r in pz.rilievi]
    obs += [r['rett'] for r in pz.regioni]
    return obs


def _vertici_interni(pz, asse):
    """coordinate dei vertici dei contorni che non stanno sui lati dell'ingombro: un taglio che ci passa
    sopra lascerebbe una scheggia"""
    out = []
    for outer, _, _, _ in pz.strati:
        b = _bbox(outer)
        lo, hi = b[asse], b[asse + 2]
        out += [p[asse] for p in outer if lo + 0.01 < p[asse] < hi - 0.01]
    return out


def _scegli_tagli(lo, hi, n, lim, vietati):
    """n - 1 tagli fra lo e hi, fuori dagli intervalli vietati, con le parti non più larghe di lim"""
    tagli, prec = [], lo
    for k in range(1, n):
        ideale = lo + (hi - lo) * k / n
        trovato = None
        for i in range(int(2 * lim)):
            c = ideale + (i + 1) // 2 * 0.5 * (1 if i % 2 else -1)
            if c - prec > lim or hi - c > lim * (n - k) or c - prec < 20.0:
                continue
            if any(a <= c <= b for a, b in vietati):
                continue
            trovato = c
            break
        if trovato is None:
            return None
        tagli.append(round(trovato, 3))
        prec = trovato
    return tagli


def _ingombro(pz):
    pts = [p for outer, _, _, _ in pz.strati for p in outer]
    return _bbox(pts)


def dividi(pz, piatto):
    """il pezzo intero se sta sul piatto, altrimenti in metà accostate con tagli dritti lungo u (la mascherina:
    i fori sui comandi della MK4 tengono ogni metà al suo posto, e si tolgono una per volta). Torna le parti
    come dict(strati, rilievi, tasche, regioni, angolo)"""
    u0, v0, u1, v1 = _ingombro(pz)
    if u1 - u0 <= piatto and v1 - v0 <= piatto:
        return [dict(strati=pz.strati, rilievi=pz.rilievi, tasche=pz.tasche, regioni=pz.regioni, angolo=0)]
    assert v1 - v0 <= piatto, f'{pz.nome}: non sta sul piatto nemmeno in metà'
    obs = _ostacoli(pz)
    vietati = [(o[0] - MARGINE_TAGLIO, o[2] + MARGINE_TAGLIO) for o in obs]
    vietati += [(x - MARGINE_TAGLIO, x + MARGINE_TAGLIO) for x in _vertici_interni(pz, 0)]
    n, tagli = math.ceil((u1 - u0) / (piatto - 2.0)), None
    while tagli is None:
        tagli = _scegli_tagli(u0, u1, n, piatto - 2.0, vietati)
        n += 1
    us = [u0] + tagli + [u1]
    out = []
    for a, b in zip(us, us[1:]):
        def dentro(r):
            c = (r[0] + r[2]) / 2
            return a <= c < b
        strati = []
        for outer, holes, w0, w1 in pz.strati:
            p = _ritaglia(outer, a if a > u0 else None, b if b < u1 else None)
            if p is not None:
                strati.append((p, [h for h in holes if dentro(_bbox(h))], w0, w1))
        out.append(dict(strati=strati, rilievi=[r for r in pz.rilievi if dentro(_bbox(r[0]))],
                        tasche=[t for t in pz.tasche if dentro(t['rett'])],
                        regioni=[r for r in pz.regioni if dentro(r['rett'])], angolo=0))
    return out


# ---------------------------------------------------------------------------------------------
# le vasche: dove passano le giunte, il fondo con le code, la parte di destra

def _inter(a, b):
    r = (max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]))
    return r if r[2] - r[0] > 1e-6 and r[3] - r[1] > 1e-6 else None


# il fondo: da 3 mm fra le pareti; la pedana della MK4 e la striscia dietro il retro piene fino a BASE_T
IMPRONTA = [(INTERNO[0] - SOVRAPPOSTO, M.APPOGGIO_Y - SOVRAPPOSTO, M.COSTOLA_X0, M.BASE_Y1),          # MK4 e cavi
            (M.COSTOLA_X0, M.APPOGGIO_Y - SOVRAPPOSTO, M.COSTOLA_X1, M.MK4_Y0 + SOVRAPPOSTO),         # sotto il ponte della costola
            (M.COSTOLA_X1, M.APPOGGIO_Y - SOVRAPPOSTO, INTERNO[1] + SOVRAPPOSTO, M.FRONTE_Y + SOVRAPPOSTO)]   # la parte di destra
PEDANA = (INTERNO[0] - SOVRAPPOSTO, M.MK4_Y0 - 2.0, M.COSTOLA_X0, M.BASE_Y1)
STRISCIA = (INTERNO[0] - SOVRAPPOSTO, 0.0, INTERNO[1] + SOVRAPPOSTO, M.RETRO_Y0)


def disposizione(piatto):
    """le vasche per il piatto: tre colonne (la culla del pad sta intera in quella di destra) e una riga sola
    se la console, profonda 240, ci sta davanti-dietro; altrimenti due. Ogni lato è None (la vasca finisce
    con una parete) o 'g' (una giunta)"""
    colonne = [('sx', 0.0, TAGLI_X[0]), ('centro', TAGLI_X[0], TAGLI_X[1]), ('dx', TAGLI_X[1], M.LARGHEZZA)]
    if piatto >= M.BASE_Y1 - 1e-6:
        righe = [('', 0.0, M.BASE_Y1)]
    else:
        righe = [('dietro', 0.0, TAGLIO_Y), ('davanti', TAGLIO_Y, M.BASE_Y1)]
    out = []
    for j, (rn, y0, y1) in enumerate(righe):
        for i, (cn, x0, x1) in enumerate(colonne):
            out.append(dict(nome='vasca_' + cn + ('_' + rn if rn else ''), x0=x0, x1=x1, y0=y0, y1=y1,
                            lati=dict(sx='g' if i > 0 else None, dx='g' if i < 2 else None,
                                      dietro='g' if j > 0 else None, davanti='g' if j < len(righe) - 1 else None)))
    return out


def posa_code(reg, lato):
    """le code di rondine di una giunta del fondo, uguali per le due vasche che la fanno: lungo la giunta, lontano
    dalle fasce delle altre giunte, dalla culla del pad (le sue pareti arrivano alla giunta) e dalla colonnina.
    Torna la quota della giunta e [(t, verso)]: verso è dove punta la coda (+x dalla vasca di sinistra, -y da quella
    davanti)"""
    x0, x1, y0, y1, L = reg['x0'], reg['x1'], reg['y0'], reg['y1'], reg['lati']
    if lato in ('sx', 'dx'):
        c, verso = (x0 if lato == 'sx' else x1), 1
        lo, hi, via = max(y0, M.APPOGGIO_Y), y1, []
        if L['dietro'] == 'g':
            via.append((y0, y0 + FASCIA))
        if L['davanti'] == 'g':
            via.append((y1 - FASCIA, y1))
        if abs(c - TAGLI_X[1]) < 1e-6:
            via.append((M.CULLA_PAD_Y0 - 2.0, M.BASE_Y1))
    else:
        c, verso = (y0 if lato == 'dietro' else y1), -1
        lo, hi = max(x0, INTERNO[0]), min(x1, INTERNO[1])
        via = [(M.COSTOLA_X0, M.COSTOLA_X1), (G.COLONNINA[0] - 12.0, G.COLONNINA[0] + 12.0)]
        if L['sx'] == 'g':
            via.append((x0, x0 + FASCIA))
        if L['dx'] == 'g':
            via.append((x1 - FASCIA, x1))
    liberi = [(lo, hi)]
    for a, b in via:
        liberi = [q for p0, p1 in liberi for q in ((p0, min(p1, a)), (max(p0, b), p1)) if q[1] - q[0] > 1e-6]
    m = M.CODA['testa'] / 2 + M.GIOCO_STAMPA + 3.0
    code = []
    for p0, p1 in liberi:
        if p1 - p0 < 2 * m:
            continue
        n = max(1, min(round((p1 - p0) / PASSO_CODE), int((p1 - p0 - 2 * m) / (M.CODA['testa'] + 6.0)) + 1))
        for k in range(n):
            t = (p0 + p1) / 2 if n == 1 else p0 + m + (p1 - p0 - 2 * m) * k / (n - 1)
            code.append((round(t, 3), verso))
    return c, code


def coda(asse, c, t, verso):
    """la coda che sporge dalla giunta, con il collo che entra di SOVRAPPOSTO nella sua vasca"""
    a, b, d = M.CODA['collo'] / 2, M.CODA['testa'] / 2, M.CODA['prof']
    pts = [(c - verso * SOVRAPPOSTO, t - a), (c, t - a), (c + verso * d, t - b), (c + verso * d, t + b), (c, t + a),
           (c - verso * SOVRAPPOSTO, t + a)]
    return pts if asse == 0 else [(q, p) for p, q in pts]


def _sagoma(asse, c, t, verso):
    """la sede di una coda, con il gioco, come punti (u, v) in ordine di t crescente"""
    g = M.GIOCO_STAMPA
    a, b, d = M.CODA['collo'] / 2 + g, M.CODA['testa'] / 2 + g, M.CODA['prof'] + g
    nt = [(c, t - a), (c + verso * d, t - b), (c + verso * d, t + b), (c, t + a)]
    return [(round(n, 4), round(tt, 4)) if asse == 0 else (round(tt, 4), round(n, 4)) for n, tt in nt]


def _con_sedi(poly, asse, c, code):
    """inserisce le sedi delle code nei lati del poligono che stanno sulla linea coord[asse] = c"""
    altro, out = 1 - asse, []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        out.append(p)
        if abs(p[asse] - c) < 1e-6 and abs(q[asse] - c) < 1e-6:
            t0, t1 = p[altro], q[altro]
            dentro = sorted((cd for cd in code if min(t0, t1) < cd[0] < max(t0, t1)), key=lambda cd: cd[0], reverse=t1 < t0)
            for t, verso in dentro:
                pts = _sagoma(asse, c, t, verso)
                out += pts if t1 > t0 else pts[::-1]
    return out


def fondo(ms, reg):
    """il fondo della vasca: 3 mm, con la pedana della MK4 e la striscia dietro il retro piene; lungo ogni giunta
    una fascia piena con le code (dalla vasca di sinistra e da quella davanti) o le loro sedi"""
    x0, x1, y0, y1, L = reg['x0'], reg['x1'], reg['y0'], reg['y1'], reg['lati']
    stretto = (x0 + (FASCIA if L['sx'] == 'g' else 0.0), y0 + (FASCIA if L['dietro'] == 'g' else 0.0),
               x1 - (FASCIA if L['dx'] == 'g' else 0.0), y1 - (FASCIA if L['davanti'] == 'g' else 0.0))
    for r in IMPRONTA:
        q = _inter(r, stretto)
        if q:
            ms.prisma(rett(*q), 0.0, FONDO)
    q = _inter(PEDANA, stretto)
    if q:
        ms.prisma(rett(*q), FONDO - SOVRAPPOSTO, M.BASE_T)
    q = _inter(STRISCIA, (x0, y0, x1, y1))
    if q:
        ms.prisma(rett(*q), 0.0, M.BASE_T)
    fasce = {'sx': (x0, y0, x0 + FASCIA, y1), 'dx': (x1 - FASCIA, y0, x1, y1),
             'dietro': (x0, y0, x1, y0 + FASCIA), 'davanti': (x0, y1 - FASCIA, x1, y1)}
    for lato, fr in fasce.items():
        if L[lato] != 'g':
            continue
        asse = 0 if lato in ('sx', 'dx') else 1
        c, code = posa_code(reg, lato)
        ha_sedi = lato in ('sx', 'davanti')
        for r in IMPRONTA:
            q = _inter(r, fr)
            if q:
                ms.prisma(_con_sedi(rett(*q), asse, c, code) if ha_sedi else rett(*q), 0.0, M.BASE_T)
        if not ha_sedi:
            for t, verso in code:
                ms.prisma(coda(asse, c, t, verso), 0.0, M.BASE_T)


def _sta(reg, bb, cosa):
    """True se l'ingombro (x0, y0, x1, y1) sta nella vasca, False se ne è fuori; a metà è un errore"""
    r = (reg['x0'], reg['y0'], reg['x1'], reg['y1'])
    if bb[2] <= r[0] or bb[0] >= r[2] or bb[3] <= r[1] or bb[1] >= r[3]:
        return False
    assert bb[0] >= r[0] - 1e-6 and bb[2] <= r[2] + 1e-6 and bb[1] >= r[1] - 1e-6 and bb[3] <= r[3] + 1e-6, \
        f'{reg["nome"]}: {cosa} sulla giunta'
    return True


def destra(ms, reg):
    """la parte di destra: il fermo dell'hub, la colonnina sotto la culla della Flip, la culla del pad con la sua
    parete davanti e il bordo arrotondato che continua la curva dei fianchi"""
    w, d, h = M.HUB['w'] + 0.8, M.HUB['d'] + 0.8, M.HUB['h']
    if _sta(reg, (M.HUB_X0 - 3.0, M.HUB_Y0 - 3.0, M.HUB_X0 + w + 3.0, M.HUB_Y0 + d + 3.0), 'il fermo dell\'hub'):
        fr = sposta(M.HUB_X0, M.HUB_Y0, 0.0)
        zb = M.BASE_T + 2.0                            # il fondo dell'hub, come nel fermo di genera.py
        ms.prisma(rett(-3, -3, w + 3, d + 3, 2), FONDO - SOVRAPPOSTO, zb, frame=fr)
        ms.prisma(rett(-3, -3, w + 3, d + 3, 2), zb, zb + 3.0, holes=[rett(0, 0, w, d, 1)], frame=fr)
        ms.prisma(rett(-3, -3, w + 3, 0, 0.5), zb + 3.0, M.BASE_T + h * 0.6, frame=fr)
        ms.prisma(rett(-3, 0, 0, d + 3, 0.5), zb + 3.0, M.BASE_T + h * 0.6, frame=fr)
    x, y = G.COLONNINA
    if _sta(reg, (x - 10.0, y - 10.0, x + 10.0, y + 10.0), 'la colonnina'):
        ms.cilindro(x, y, FONDO - SOVRAPPOSTO, M.BASE_T, 10.0, 40)
        ms.cilindro(x, y, M.BASE_T - SOVRAPPOSTO, M.Z_APPOGGIO, 6.0, 32)
    x0, x1 = TAGLI_X[1], INTERNO[1] + SOVRAPPOSTO
    if _sta(reg, (x0, M.CULLA_PAD_Y0 - M.CULLA_DENTE, x1, M.BASE_Y1), 'la culla del pad'):
        culla = G.culla_pad()
        for p in culla.prismi:
            if p.get('sopra') is None and p['frame'] == IDENTITA and abs(p['z0'] - M.BASE_T) < 1e-6:
                p['z0'] = FONDO - SOVRAPPOSTO          # le pareti e le costole scendono fino al fondo
        # il bordo arrotondato davanti si rifà da fianco a costola, qui sotto
        culla.prismi = [p for p in culla.prismi
                        if p['frame'] == IDENTITA or not any(abs(q[0] - M.BASE_Y1) < 1e-6 for q in p['outer'])]
        ms.unisci(culla)
        cx0, cx1 = M.DESTRA_X0 + 0.3, M.DESTRA_X1 - 0.3
        ms.box(x0, M.CULLA_PAD_Y0, FONDO - SOVRAPPOSTO, cx0 + SOVRAPPOSTO, M.CULLA_PAD_Y1, M.Z_PIANO)
        ms.box(cx1 - SOVRAPPOSTO, M.CULLA_PAD_Y0, FONDO - SOVRAPPOSTO, x1, M.CULLA_PAD_Y1, M.Z_PIANO)
        ms.box(x0, M.CULLA_PAD_Y1 - SOVRAPPOSTO, 0.0, x1, M.BASE_Y1, M.FRONTE_Z)          # la parete davanti
        R, ya, Y, H = M.FIANCO_R, M.PAD_Y1 + M.CULLA_PAD_GIOCO + 0.5, M.BASE_Y1, M.Z_PIANO
        arco = [p for p in G._arco((Y - R, H - R), R, 0, 90, 16) if p[0] >= ya]
        ms.prisma_x([(ya, M.FRONTE_Z - SOVRAPPOSTO), (Y, M.FRONTE_Z - SOVRAPPOSTO)] + arco + [(ya, arco[-1][1])], x0, x1)


def vasca(reg, pareti, solido_parete):
    """una vasca nel riferimento del case: torna (corpo, scritte, facce, viti); facce sono le pareti con le
    scritte [(pezzo, tratto)], per le anteprime; viti [(spessore, lunghezza)] quelle con la testa in questa vasca"""
    corpo, scritte = Mesh(f'Stame {reg["nome"]}'), Mesh(f'Stame {reg["nome"]} scritte')
    facce, viti = [], []
    x0, x1, y0, y1, L = reg['x0'], reg['x1'], reg['y0'], reg['y1'], reg['lati']

    def parete(pz, lato_lo, lato_hi, lo, hi):
        t = tratto(pz, lo if L[lato_lo] else None, hi if L[lato_hi] else None, L[lato_lo] == 'g', L[lato_hi] == 'g')
        c, s = solido_parete(pz, t)
        corpo.unisci(c, pz.F)
        if s is not None and s.prismi:
            scritte.unisci(s, pz.F)
        if t['rilievi'] or t['regioni']:
            facce.append((pz, t))
        viti.extend(t['viti'])
    if y0 <= 0.0:
        parete(pareti['retro'], 'sx', 'dx', x0, x1)
    if x0 <= 0.0:
        parete(pareti['fianco_sx'], 'dietro', 'davanti', y0, y1)
    if x0 <= M.COSTOLA_X0 and x1 >= M.COSTOLA_X1 - 1e-6:
        parete(pareti['costola'], 'dietro', 'davanti', y0, y1)
    if x1 >= M.LARGHEZZA:
        parete(pareti['fianco_dx'], 'dietro', 'davanti', y0, y1)
    fondo(corpo, reg)
    if x1 >= M.LARGHEZZA:
        destra(corpo, reg)
    return corpo, scritte, facce, viti


def pareti(fianchi=None):
    """le pareti del telaio nel loro piano; i fianchi si possono passare già con le scritte (multicolore.py)"""
    fianchi = fianchi or {'sx': fianco('sx'), 'dx': fianco('dx')}
    return {'retro': retro(), 'costola': costola(), 'fianco_sx': fianchi['sx'], 'fianco_dx': fianchi['dx']}


def _solido_parete(pz, t):
    return solido(pz, t), None


def vasche(piatto, fianchi=None, solido_parete=_solido_parete):
    """le vasche per il piatto: [dict(nome, reg, corpo, scritte, facce, viti, nota)] nel riferimento del case"""
    par = pareti(fianchi)
    out = []
    for reg in disposizione(piatto):
        corpo, scritte, facce, viti = vasca(reg, par, solido_parete)
        out.append(dict(nome=reg['nome'], reg=reg, corpo=corpo, scritte=scritte, facce=facce, viti=viti,
                        nota=_nota_vasca(reg)))
    lato = max(max(b[0] - a[0], b[1] - a[1]) for a, b in (v['corpo'].ingombro() for v in out))
    if lato > piatto + 0.01:
        raise SystemExit(f'piatto da {piatto:.0f} troppo piccolo: le vasche sono larghe fino a {_v(lato)} mm (la culla del '
                         'pad sta intera nella vasca di destra)')
    sovrapposte = [(a['nome'], b['nome']) for i, a in enumerate(out) for b in out[i + 1:]
                   if compenetrano(a['corpo'], b['corpo'])]
    assert not sovrapposte, f'vasche che si compenetrano: {sovrapposte}'
    occupate = sedi_occupate([v['corpo'] for v in out])
    assert not occupate, f'sedi occupate dalle vasche: {occupate}'
    return out


def _nota_vasca(reg):
    x0, x1, y0, y1 = reg['x0'], reg['x1'], reg['y0'], reg['y1']
    cose = []
    if x0 <= 0.0:
        cose.append('fianco sinistro' + (' con marchio e nome' if y0 <= 0.0 else ''))
    if y0 <= 0.0:
        cose.append('retro' + (' con la finestra del pedale' if x0 < 280.0 < x1 else '')
                    + (' con le finestre di alimentazione e audio' if x1 >= M.LARGHEZZA else ''))
    if x0 < M.MK4_X0 + M.MK4['w'] and x1 > M.MK4_X0:
        cose.append('pedana della MK4')
    if x0 <= M.COSTOLA_X0 and x1 >= M.COSTOLA_X1 - 1e-6:
        cose.append('costola')
    if x1 >= M.LARGHEZZA:
        if y0 <= 0.0:
            cose.append('fermo dell\'hub, colonnina')
        if y1 >= M.BASE_Y1:
            cose.append('culla del pad, parete davanti')
        cose.append('fianco destro' + (' con marchio e nome' if y0 <= 0.0 else ''))
    return ', '.join(cose)


def prova_giunta(solido_parete=_solido_parete):
    """la giunta sotto la MK4 in piccolo, da stampare prima: retro con il sormonto e le due viti, fondo con una
    coda e la sua sede; le due metà vicine sul piatto"""
    c, par = TAGLI_X[0], pareti()
    a = dict(nome='prova_sinistra', x0=c - 30.0, x1=c, y0=0.0, y1=60.0, lati=dict(sx='l', dx='g', dietro=None, davanti='l'))
    b = dict(nome='prova_destra', x0=c, x1=c + 30.0, y0=0.0, y1=60.0, lati=dict(sx='g', dx='l', dietro=None, davanti='l'))
    ma, mb = vasca(a, par, solido_parete)[0], vasca(b, par, solido_parete)[0]
    assert not compenetrano(ma, mb), 'la prova di giunta si compenetra'
    ms = Mesh('Stame prova della giunta')
    ms.unisci(ma)
    ms.unisci(mb, sposta(15.0, 0.0, 0.0))
    return ms


# ---------------------------------------------------------------------------------------------
# controlli: due vasche non si compenetrano; la faccia giusta sta sul piatto

def _box(p):
    xs = [q[0] for q in p['outer']]
    ys = [q[1] for q in p['outer']]
    pts = [applica(p['frame'], (u, v, t)) for u in (min(xs), max(xs)) for v in (min(ys), max(ys)) for t in (p['z0'], p['z1'])]
    return tuple(min(q[i] for q in pts) for i in range(3)) + tuple(max(q[i] for q in pts) for i in range(3))


def _nel_poligono(x, y, poly):
    c = False
    for i in range(len(poly)):
        (x0, y0), (x1, y1) = poly[i - 1], poly[i]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    return c


def _nel_prisma(p, P):
    u, v, t = applica(inversa(p['frame']), P)
    if not min(p['z0'], p['z1']) < t < max(p['z0'], p['z1']):
        return False
    return _nel_poligono(u, v, p['outer']) and not any(_nel_poligono(u, v, h) for h in p['holes'])


def compenetrano(a, b, passi=5):
    """True se due pezzi si compenetrano per più di un decimo di millimetro: per ogni coppia di prismi i cui
    ingombri si sovrappongono, una griglia di punti nella parte comune"""
    ba = [(p, _box(p)) for p in a.prismi]
    bb = [(p, _box(p)) for p in b.prismi]
    for p, r in ba:
        for q, s in bb:
            lo = [max(r[i], s[i]) + 0.05 for i in range(3)]
            hi = [min(r[i + 3], s[i + 3]) - 0.05 for i in range(3)]
            if any(hi[i] <= lo[i] for i in range(3)):
                continue
            for i in range(passi):
                for j in range(passi):
                    for k in range(passi):
                        P = tuple(lo[n] + (hi[n] - lo[n]) * (m + 0.5) / passi for n, m in ((0, i), (1, j), (2, k)))
                        if _nel_prisma(p, P) and _nel_prisma(q, P):
                            return True
    return False


def _passi(a, b, passo):
    n = max(1, math.ceil((b - a) / passo))
    return [a + (b - a) * k / n for k in range(n + 1)]


def _punti_box(x0, y0, z0, x1, y1, z1, passo=3.0):
    """i punti di una scatola: sulle sei facce ogni passo mm (lì arriverebbe una parete o un fondo sbagliati) e,
    più radi, dentro"""
    xs, ys, zs = _passi(x0, x1, passo), _passi(y0, y1, passo), _passi(z0, z1, passo)
    out = {(x, y, z) for x in xs for y in ys for z in (z0, z1)}
    out |= {(x, y, z) for x in xs for z in zs for y in (y0, y1)}
    out |= {(x, y, z) for y in ys for z in zs for x in (x0, x1)}
    out |= {(x, y, z) for x in _passi(x0, x1, 15.0) for y in _passi(y0, y1, 15.0) for z in _passi(z0, z1, 6.0)}
    return sorted(out)


def sedi():
    """le sedi che le vasche devono lasciare libere, come punti a 0,2 mm dentro le quote della console laser: la
    MK4, il pad nella culla, l'hub nel fermo, il passaggio dei cavi sotto la costola, le finestre del retro, lo
    spessore della mascherina e del piano della Flip sopra gli appoggi"""
    g = 0.2
    K, H = M.MK4, M.HUB
    out = {'MK4': _punti_box(M.MK4_X0 + g, M.MK4_Y0 + g, M.BASE_T + g, M.MK4_X0 + K['w'] - g, M.MK4_Y0 + K['d'] - g,
                             M.Z_MK4 - g)}
    contorno = G.contorno_pad(-g)[0]
    b = _bbox(contorno)
    zs = _passi(M.PAD_Z0 + g, M.PAD_Z1 - g, 3.0)
    pad = [(x, y, z) for i in range(len(contorno)) for x, y in [contorno[i]] for z in zs]
    for (xa, ya), (xb, yb) in zip(contorno, contorno[1:] + contorno[:1]):      # il contorno, ogni 3 mm
        n = max(1, math.ceil(math.dist((xa, ya), (xb, yb)) / 3.0))
        pad += [(xa + (xb - xa) * k / n, ya + (yb - ya) * k / n, z) for k in range(n) for z in zs]
    pad += [p for p in _punti_box(b[0], b[1], M.PAD_Z0 + g, b[2], b[3], M.PAD_Z1 - g) if _nel_poligono(p[0], p[1], contorno)
            and p[0] not in (b[0], b[2]) and p[1] not in (b[1], b[3])]
    out['pad'] = pad
    hx, hy, hz = M.HUB_X0 + 0.4, M.HUB_Y0 + 0.4, M.BASE_T + 2.0
    out['hub'] = _punti_box(hx + g, hy + g, hz + g, hx + H['w'] - g, hy + H['d'] - g, hz + H['h'] - g)
    out['passaggio dei cavi'] = _punti_box(M.COSTOLA_X0 + g, M.APPOGGIO_Y + g, M.BASE_T + g, M.COSTOLA_X1 - g,
                                           M.MK4_Y0 - g, G.CAVI_Z - g)
    fin = []
    for lato in ('sx', 'dx'):
        zt = M.BASE_T + G.USCITE_Z[lato]
        for cx in G.USCITE[lato]:
            fin += _punti_box(cx - 8.0, M.RETRO_Y0 + g, zt - 12.0 + g, cx + 8.0, M.APPOGGIO_Y - g, zt - g, 2.0)
    out['finestre del retro'] = fin
    out['mascherina'] = _punti_box(G.MASC_X0 + g, G.MASC_Y0 + g, M.Z_PIANO0 + g, G.MASC_X1 - g, G.MASC_Y1 - g, M.Z_PIANO - g)
    out['piano della Flip'] = _punti_box(G.PIANO_X0 + g, G.PIANO_Y0 + g, M.Z_PIANO0 + g, G.PIANO_X1 - g, M.PIANO_Y1 - g,
                                         M.Z_PIANO - g)
    return out


def sedi_occupate(pezzi):
    """[(sede, punto)]: per ogni sede il primo punto che sta dentro un prisma dei pezzi (prima l'ingombro, con
    numpy, poi il prisma)"""
    import numpy as np
    prismi = [(p, _box(p)) for ms in pezzi for p in ms.prismi]
    out = []
    for nome, punti in sedi().items():
        P = np.array(punti)
        trovato = None
        for p, r in prismi:
            dentro = np.nonzero((P[:, 0] > r[0]) & (P[:, 0] < r[3]) & (P[:, 1] > r[1]) & (P[:, 1] < r[4])
                                & (P[:, 2] > r[2]) & (P[:, 2] < r[5]))[0]
            for i in dentro:
                if _nel_prisma(p, tuple(P[i])):
                    trovato = tuple(round(float(c), 1) for c in P[i])
                    break
            if trovato:
                break
        if trovato:
            out.append((nome, trovato))
    return out


def appoggio(ms):
    """quanto della faccia di sotto (in mm²) sta sul piatto: i triangoli a z minima rivolti in giù, uniti su
    una griglia di 0,5 mm"""
    from PIL import Image, ImageDraw
    tris = [t for g in ms.gusci for t in g]
    z0 = min(p[2] for t in tris for p in t)
    x0, y0 = min(p[0] for t in tris for p in t), min(p[1] for t in tris for p in t)
    x1, y1 = max(p[0] for t in tris for p in t), max(p[1] for t in tris for p in t)
    k = 2.0
    img = Image.new('L', (int((x1 - x0) * k) + 2, int((y1 - y0) * k) + 2), 0)
    d = ImageDraw.Draw(img)
    for t in tris:
        if all(abs(p[2] - z0) < 1e-4 for p in t):
            d.polygon([((p[0] - x0) * k, (p[1] - y0) * k) for p in t], fill=255)
    return img.histogram()[255] / (k * k)


# ---------------------------------------------------------------------------------------------
# solidi e STL

def solido(pz, t):
    """la parte come Mesh nel piano del pezzo (u, v, w)"""
    ms = Mesh(f'Stame {pz.nome}')
    for outer, holes, w0, w1 in t['strati']:
        tasche = [rett(*q['rett']) for q in t['tasche'] if q['tasca']]
        if pz.faccia is not None and abs(w1 - pz.faccia) < 1e-6 and tasche:
            ms.prisma(outer, w0, w1 - M.TASCA, holes=holes)
            ms.prisma(outer, w1 - M.TASCA - SOVRAPPOSTO, w1, holes=holes + tasche)
        else:
            ms.prisma(outer, w0, w1, holes=holes)
    for loop, w0, w1 in t['rilievi']:
        ms.prisma(loop, w0, w1)
    return ms


def per_la_stampa(pz, ms):
    """una parte di un pezzo piano nel verso fisico giusto (specchiata se il piano del pezzo è sinistrorso nel
    mondo), appoggiata sul piatto"""
    if _det(G.SPECCHIO) * _det(pz.F) < 0:
        ms = ms.portato(((0.0, 0.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))
    return ms.a_terra()


def _grammi_prismi(ms):
    """stima prisma per prisma (per i pezzi con prismi inclinati, come la cornice): 3 perimetri da 0,4, 4 strati
    pieni sopra e sotto, riempimento al 20 %; due prismi che si compenetrano contano due volte"""
    g = 0.0
    for p in ms.prismi:
        h = abs(p['z1'] - p['z0'])
        a = abs(area(p['outer'])) - sum(abs(area(hh)) for hh in p['holes'])
        per = sum(math.dist(L[i - 1], L[i]) for L in [p['outer']] + p['holes'] for i in range(len(L)))
        v = a * h
        guscio = min(v, per * h * 1.2 + 2 * a * min(0.8, h / 2))
        g += (guscio + 0.2 * (v - guscio)) * DENSITA / 1000.0
    return g


def _sezione(p, z):
    """la sezione di un prisma alla quota z, in (x, y): [(contorno, fori)]; None se il prisma è inclinato"""
    O, U, V, N = p['frame']
    if p.get('sopra') is not None:
        return None
    if abs(N[2]) > 0.999 and abs(U[2]) < 1e-9 and abs(V[2]) < 1e-9:        # profilo orizzontale
        za, zb = sorted((O[2] + p['z0'] * N[2], O[2] + p['z1'] * N[2]))
        if not za <= z <= zb:
            return []

        def xy(q):
            return (O[0] + q[0] * U[0] + q[1] * V[0], O[1] + q[0] * U[1] + q[1] * V[1])
        return [([xy(q) for q in p['outer']], [[xy(q) for q in h] for h in p['holes']])]
    if abs(abs(V[2]) - 1.0) < 1e-9 and abs(U[2]) < 1e-9 and abs(N[2]) < 1e-9:   # profilo verticale
        v = (z - O[2]) / V[2]
        xs = []
        for L in [p['outer']] + p['holes']:
            for i in range(len(L)):
                (ua, va), (ub, vb) = L[i - 1], L[i]
                if (va > v) != (vb > v):
                    xs.append(ua + (v - va) * (ub - ua) / (vb - va))
        xs.sort()
        out = []
        for ua, ub in zip(xs[0::2], xs[1::2]):
            q = [(O[0] + u * U[0] + w * N[0], O[1] + u * U[1] + w * N[1]) for u, w in
                 ((ua, p['z0']), (ub, p['z0']), (ub, p['z1']), (ua, p['z1']))]
            out.append((q, []))
        return out
    return None


def grammi(ms, passo=0.5, fetta=1.0):
    """stima del filamento come la fa lo slicer: il pezzo a fette da 1 mm su una griglia di 0,5 mm, così i solidi
    che si compenetrano contano una volta; per ogni fetta 3 perimetri da 0,4 (1,2 mm), 4 strati pieni da 0,2 dove
    sopra o sotto c'è aria, riempimento al 20 % nel resto"""
    import numpy as np
    from PIL import Image, ImageDraw
    (x0, y0, z0), (x1, y1, z1) = ms.ingombro()
    W, H = int((x1 - x0) / passo) + 3, int((y1 - y0) / passo) + 3
    nz = max(1, round((z1 - z0) / fetta))
    hz = (z1 - z0) / nz

    def px(q):
        return ((q[0] - x0) / passo + 1.0, (q[1] - y0) / passo + 1.0)
    fette = []
    for k in range(nz):
        zc = z0 + (k + 0.5) * hz
        img = Image.new('L', (W, H), 0)
        d = ImageDraw.Draw(img)
        for p in ms.prismi:
            sez = _sezione(p, zc)
            if sez is None:
                return _grammi_prismi(ms)
            for outer, holes in sez:
                if holes:
                    m = Image.new('L', (W, H), 0)
                    dm = ImageDraw.Draw(m)
                    dm.polygon([px(q) for q in outer], fill=255)
                    for h in holes:
                        dm.polygon([px(q) for q in h], fill=0)
                    img.paste(255, mask=m)
                else:
                    d.polygon([px(q) for q in outer], fill=255)
        fette.append(np.asarray(img) > 127)
    a, vuoto, mm3 = passo * passo, np.zeros((H, W), dtype=bool), 0.0
    for k, m in enumerate(fette):
        n = int(m.sum())
        if not n:
            continue
        pad = np.pad(m, 1)
        bordo = m & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
        sotto = fette[k - 1] if k else vuoto
        sopra = fette[k + 1] if k + 1 < nz else vuoto
        pelle = m & ~(sotto & sopra)
        pieno = min(n * a, bordo.sum() * passo * 1.2 + pelle.sum() * a * min(1.0, 0.8 / hz))
        mm3 += (pieno + 0.2 * (n * a - pieno)) * hz
    return mm3 * DENSITA / 1000.0


def verifica(ms, piatto, minimo=0.0):
    """chiuso, dentro il piatto, appoggiato: torna (ingombro, chiuso, sta, appoggio in mm²)"""
    (x0, y0, z0), (x1, y1, z1) = ms.ingombro()
    ap = appoggio(ms)
    assert ap > minimo * (x1 - x0) * (y1 - y0), f'{ms.nome}: la faccia sul piatto è troppo piccola ({ap:.0f} mm²)'
    return (x1 - x0, y1 - y0, z1 - z0), ms.controlla(), (x1 - x0) <= piatto + 0.01 and (y1 - y0) <= piatto + 0.01, ap


# ---------------------------------------------------------------------------------------------
# il foglio delle etichette

def _svg_testa(w, h, titolo):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" '
            f'height="{h}mm" viewBox="0 0 {w} {h}">\n<title>{titolo}</title>\n<rect width="{w}" height="{h}" fill="#FFFFFF"/>\n')


FONT = "Bahnschrift, 'Segoe UI', Arial, sans-serif"


def _testo(x, y, s, size=3.0, colore='#333', peso=400, ancora='start'):
    s = s.replace('&', '&amp;').replace('<', '&lt;')
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-family="{FONT}" font-size="{size}" font-weight="{peso}" '
            f'fill="{colore}" text-anchor="{ancora}">{s}</text>\n')


def etichette(pezzi, cartella):
    """A4 1:1: ogni tasca ha la sua etichetta, nera con le scritte chiare come l'incisione, 0,2 mm più
    piccola per lato; un numero accanto. Una seconda pagina mostra dove va ogni numero."""
    W, H, mar, gap = 210.0, 297.0, 12.0, 4.5
    tutte = [(pz, t) for pz in pezzi for t in pz.tasche]
    corpo, x, y, riga_h = [], mar, mar + 16.0, 0.0
    corpo.append(_testo(mar, mar + 4, 'Stame — etichette della mascherina e del piano della Flip', 5.0, '#141B18', 700))
    corpo.append(_testo(mar, mar + 10, 'Stampare al 100 % su carta adesiva (o vinile da stampa), ritagliare lungo il '
                        'bordo grigio e posare nella tasca con lo stesso numero. Due serie: una è di ricambio.', 2.8, '#555'))
    for serie, (pz, t) in [(s, q) for s in (0, 1) for q in tutte]:
        if serie and (pz, t) == tutte[0]:
            x, y, riga_h = mar, y + riga_h + 12.0, 0.0
            corpo.append(f'<line x1="{mar}" y1="{y - 7:.2f}" x2="{W - mar}" y2="{y - 7:.2f}" stroke="#CCC" stroke-width="0.2" stroke-dasharray="1.5 1"/>')
        u0, v0, u1, v1 = t['rett']
        g = 0.2 if t['tasca'] else 0.0             # nella tasca l'etichetta è 0,2 mm più piccola per lato
        w, h = u1 - u0 - 2 * g, v1 - v0 - 2 * g
        if x + w > W - mar:
            x, y, riga_h = mar, y + riga_h + gap + 3.0, 0.0
        assert y + h < H - mar, 'le etichette non stanno in una pagina'
        corpo.append(f'<g transform="translate({x - u0 - g:.3f},{y - v0 - g:.3f})">')
        corpo.append(f'<rect x="{u0 + g:.3f}" y="{v0 + g:.3f}" width="{w:.3f}" height="{h:.3f}" fill="#16181A"/>')
        for e in t['elementi']:
            d = 'M' + ' L'.join(f'{a:.3f},{b:.3f}' for a, b in e['loop']) + ' Z'
            corpo.append(f'<path d="{d}" fill="#ECE5CF"/>')
        corpo.append(f'<rect x="{u0 + g:.3f}" y="{v0 + g:.3f}" width="{w:.3f}" height="{h:.3f}" fill="none" '
                     f'stroke="#9A9A9A" stroke-width="0.12"/>')
        corpo.append('</g>')
        corpo.append(_testo(x, y - 0.8, str(t['n']), 2.2, '#888'))
        x += w + gap
        riga_h = max(riga_h, h)
    p1 = os.path.join(cartella, 'etichette_mascherina.svg')
    with open(p1, 'w', encoding='utf-8', newline='\n') as f:
        f.write(_svg_testa(W, H, 'Stame — etichette della mascherina') + ''.join(corpo) + '</svg>\n')
    # la mappa: i due piani dall'alto, con le tasche numerate
    corpo = [_testo(mar, mar + 4, 'Dove va ogni etichetta', 5.0, '#141B18', 700)]
    y = mar + 12.0
    for pz in pezzi:
        outer = pz.strati[0][0]
        b = _bbox(outer)
        s = min((W - 2 * mar) / (b[2] - b[0]), 0.62)
        corpo.append(_testo(mar, y + 3, 'mascherina della MK4' if pz.nome == 'mascherina' else 'piano della Flip',
                            3.4, '#333', 700))
        y += 6.0

        def T(p):
            return (mar + (p[0] - b[0]) * s, y + (p[1] - b[1]) * s)
        d = 'M' + ' L'.join(f'{a:.2f},{c:.2f}' for a, c in map(T, outer)) + ' Z'
        corpo.append(f'<path d="{d}" fill="#2A2C2E" stroke="#111" stroke-width="0.2"/>')
        for h in pz.strati[0][1]:
            d = 'M' + ' L'.join(f'{a:.2f},{c:.2f}' for a, c in map(T, h)) + ' Z'
            corpo.append(f'<path d="{d}" fill="#FFFFFF"/>')
        for t in pz.tasche:
            (a0, c0), (a1, c1) = T(t['rett'][:2]), T(t['rett'][2:])
            stile = 'fill="#E8B04A"' if t['tasca'] else 'fill="none" stroke="#E8B04A" stroke-width="0.35"'
            corpo.append(f'<rect x="{a0:.2f}" y="{c0:.2f}" width="{a1 - a0:.2f}" height="{c1 - c0:.2f}" {stile}/>')
            corpo.append(_testo((a0 + a1) / 2, c0 - 0.6, str(t['n']), 2.0, '#B86A00', 700, 'middle'))
        y += (b[3] - b[1]) * s + 14.0
    corpo.append(_testo(mar, y, 'Pieno: la tasca, profonda 0,4 mm. Solo il bordo: fra due fori non c\'è posto per una '
                        'tasca, l\'etichetta si posa sulla faccia.', 2.8, '#555'))
    p2 = os.path.join(cartella, 'etichette_mappa.svg')
    with open(p2, 'w', encoding='utf-8', newline='\n') as f:
        f.write(_svg_testa(W, H, 'Stame — dove vanno le etichette') + ''.join(corpo) + '</svg>\n')
    return [p1, p2], len(tutte)


# ---------------------------------------------------------------------------------------------
# i disegni: la console montata, le vasche staccate, la giunta (assieme.disegna: numpy e PIL)

COLORI = {'telaio': 'telaio: PLA o PETG color legno o sabbia', 'piano': 'piani: nero',
          'petg_nero': 'nero', 'petg_sabbia': 'sabbia'}
TINTE = {'telaio': (216, 198, 160), 'telaio2': (204, 184, 142), 'piano': (40, 40, 44)}


def _parti_console(vv, piani):
    """le vasche (una sì e una no un po' più scure, così si vedono le giunte), i piani e gli stampati sopra"""
    parti = []
    for k, v in enumerate(vv):
        tinta = TINTE['telaio2'] if (k + v['reg']['y0'] > 0) % 2 else TINTE['telaio']
        parti.append(dict(nome=v['nome'], passo=1, colore=tinta, mesh=v['corpo']))
    for nome, pz, t in piani:
        parti.append(dict(nome=nome, passo=2, colore=TINTE['piano'], mesh=solido(pz, t).portato(pz.F)))
    for s in G.STAMPATI:
        if s['nome'] in ('culla_flip', 'visiera'):
            parti.append(dict(nome=s['nome'], passo=2, colore=(48, 48, 52), mesh=s['mesh']))
    return parti


def disegni(vv, piani, prova, cartella):
    import assieme as A
    parti = _parti_console(vv, piani) + A.apparecchi()
    out = [A.disegna(parti, os.path.join(cartella, 'console_stampata.png'), titolo='Stame, la console tutta stampata',
                     testo=f'{len(vv)} vasche già montate, unite a coda di rondine e con due viti per giunta; '
                           'mascherina in due metà e piano della Flip, neri.'),
           A.disegna(parti, os.path.join(cartella, 'console_stampata_retro.png'), vista=(-0.7, 0.9, 0.7))]
    # le vasche staccate: si calano una accanto all'altra; i piani sopra, sollevati
    esploso = []
    for p in _parti_console(vv, piani):
        if p['passo'] == 1:
            reg = next(v['reg'] for v in vv if v['nome'] == p['nome'])
            i = TAGLI_X.index(reg['x0']) + 1 if reg['x0'] in TAGLI_X else 0
            j = 1 if reg['y0'] > 0 else 0
            esploso.append(dict(p, mesh=p['mesh'].portato(sposta(45.0 * i, 45.0 * j, 0.0))))
        else:
            esploso.append(dict(p, mesh=p['mesh'].portato(sposta(45.0, 0.0, 70.0))))
    out.append(A.disegna(esploso, os.path.join(cartella, 'vasche.png'), vista=(0.45, -1.0, 1.05), larghezza=1500, altezza=900))
    out.append(A.disegna([dict(nome='prova', passo=1, colore=TINTE['telaio'], mesh=prova)], os.path.join(cartella, 'giunta.png'),
                         vista=(0.55, -1.0, 0.95), larghezza=1100, altezza=800))
    return out


# ---------------------------------------------------------------------------------------------

def _v(x, d=1):
    return f'{x:.{d}f}'.replace('.', ',')


def pezzi_piani(piatto, masch, pf):
    """mascherina e piano della Flip, divisi se serve: [(nome, pezzo, parte)]"""
    out = []
    for pz in (masch, pf):
        parti = dividi(pz, piatto)
        for k, t in enumerate(parti, 1):
            out.append((pz.nome if len(parti) == 1 else f'{pz.nome}_{k}', pz, t))
    return out


def genera(piatto=None):
    piatto = piatto or M.PIATTO_COMUNE[0]
    G.genera()
    masch = piano('mascherina', 1)
    pf = piano('piano_flip', 1 + len(masch.tasche))
    vv = vasche(piatto)                      # prima le vasche: se il piatto non basta, la cartella resta com'è
    os.makedirs(OUT3D, exist_ok=True)
    for n in os.listdir(OUT3D):              # il resto (i PDF di manuale.py, file d'altri) resta
        if n.endswith(('.stl', '.svg', '.md', '.png')):
            os.remove(os.path.join(OUT3D, n))
    righe, totale, viti = [], 0.0, []
    for v in vv:
        ms = v['corpo'].portato(G.SPECCHIO).a_terra()
        ms.nome = f'Stame {v["nome"]}'
        dim, chiuso, sta, ap = verifica(ms, piatto, 0.5)
        ms.salva(os.path.join(OUT3D, v['nome'] + '.stl'))
        g = grammi(ms)
        totale += g
        viti += v['viti']
        righe.append(dict(nome=v['nome'], quanti=1, dim=dim, colore='telaio', nota=v['nota'] + '; in piedi, il fondo sul piatto',
                          grammi=g, chiuso=chiuso, sta=sta))
    piani = pezzi_piani(piatto, masch, pf)
    for nome, pz, t in piani:
        ms = per_la_stampa(pz, solido(pz, t))
        ms.nome = f'Stame {nome}'
        dim, chiuso, sta, ap = verifica(ms, piatto, 0.5)
        ms.salva(os.path.join(OUT3D, nome + '.stl'))
        g = grammi(ms)
        totale += g
        nota = pz.nota + ('; la metà ' + ('sinistra' if nome.endswith('_1') else 'destra') if nome[-2] == '_' else '')
        righe.append(dict(nome=nome, quanti=1, dim=dim, colore=pz.colore, nota=nota, grammi=g, chiuso=chiuso, sta=sta))
    for s in G.STAMPATI:
        if s['nome'] not in ('culla_flip', 'visiera'):
            continue
        ms = s['mesh'].portato(G.SPECCHIO).portato(s['posa']).a_terra()
        dim, chiuso, sta, ap = verifica(ms, piatto)
        ms.salva(os.path.join(OUT3D, s['nome'] + '.stl'))
        g = grammi(ms) * s['quanti']
        totale += g
        righe.append(dict(nome=s['nome'], quanti=s['quanti'], dim=dim, colore=s['materiale'], nota=s['nota'],
                          grammi=g, chiuso=chiuso, sta=sta))
    prova = prova_giunta()
    ms = prova.portato(G.SPECCHIO).a_terra()
    ms.nome = 'Stame prova della giunta'
    dim, chiuso, sta, ap = verifica(ms, piatto, 0.3)
    ms.salva(os.path.join(OUT3D, 'prova_giunta.stl'))
    righe.append(dict(nome='prova_giunta', quanti=1, dim=dim, colore='telaio', grammi=grammi(ms), chiuso=chiuso, sta=sta,
                      nota='la giunta sotto la MK4 in piccolo, le due metà insieme: da stampare prima delle vasche'))
    svgs, n_etichette = etichette([masch, pf], OUT3D)
    scrivi_elenco(righe, totale, piatto, n_etichette, viti, len(vv))
    pngs = disegni(vv, piani, prova, OUT3D)
    return righe, totale, svgs + pngs, viti


def minuteria_viti(viti):
    """le viti delle giunte, per lunghezza: [(lunghezza, quante)]"""
    conta = {}
    for _, lung in viti:
        conta[lung] = conta.get(lung, 0) + 1
    return sorted(conta.items())


def testo_viti(viti):
    return ', '.join(f'{n} viti M3 × {lung} a testa cilindrica (brugola)' for lung, n in minuteria_viti(viti)) + ' con i dadi'


def scrivi_elenco(righe, totale, piatto, n_etichette, viti, n_vasche):
    L = ['# Stame — la console tutta stampata, a vasche', '',
         f'Generato da `hardware/case/stampa3d.py` (piatto {piatto:.0f} × {piatto:.0f} mm; `--piatto 240` per la Kobra S1 '
         'e le altre da 250: tre vasche intere). Il telaio è in vasche: ogni vasca è un tratto di console già montato, '
         'con fondo, pareti, appoggi del piano e sedi, e si stampa in piedi con il fondo sul piatto. Ogni file sta sul '
         'piatto così com\'è, nel verso giusto.', '',
         '| File | Quanti | Ingombro (mm) | Grammi | Colore | Note |', '|---|---|---|---|---|---|']
    for r in righe:
        dx, dy, dz = r['dim']
        L.append(f'| `{r["nome"]}.stl` | {r["quanti"]} | {dx:.0f} × {dy:.0f} × {_v(dz)} | {r["grammi"]:.0f} | '
                 f'{COLORI.get(r["colore"], r["colore"])} | {r["nota"]} |')
    L += ['', f'Filamento: circa {_v(totale / 1000)} kg in tutto (stima a fette, come lo slicer: 3 perimetri, 4 strati pieni '
          'sopra e sotto, riempimento al 20 %).', '',
          '## Le giunte', '',
          f'Le {n_vasche} vasche si uniscono senza colla. Nel fondo ci sono code di rondine verticali (collo '
          f'{_v(M.CODA["collo"], 0)}, testa {_v(M.CODA["testa"], 0)}, profondità {_v(M.CODA["prof"], 0)} mm; nella sede '
          f'{_v(M.GIOCO_STAMPA, 2)} mm di gioco per lato): stampate in piedi sono prismi dritti, senza sbalzi, e si infilano '
          'calando una vasca accanto all\'altra. Tengono le vasche allineate nel piano, non in altezza: per questo le '
          f'pareti che attraversano la giunta (il retro e, con sei vasche, i fianchi e la costola) si sormontano a mezzo '
          f'spessore per {_v(SORMONTO, 0)} mm e due viti M3 le stringono, con la testa nella sua sede nella faccia di fuori '
          'e il dado nella sua sede in quella di dentro. Le giunte stanno dove non tagliano sedi né appoggi: a metà sotto '
          'la MK4, che ci appoggia sopra; fra la costola e la culla del pad, che resta intera; con sei vasche, fra la '
          'colonnina e la culla.', '',
          f'Viti: {testo_viti(viti)}.', '',
          '## Impostazioni', '',
          '- PETG o PLA, ugello 0,4, strati da 0,2. Le vasche in un colore legno o sabbia; mascherina, piano della Flip, '
          'culla della Flip e cornice in nero.',
          '- 3 perimetri, 4 strati pieni sopra e sotto, riempimento giroide al 20 %. Senza supporti: le vasche hanno solo '
          'ponti corti (il passaggio dei cavi sotto la costola, 28 mm; le finestre della culla del pad) e le sedi delle viti, '
          'orizzontali e piccole. La cornice dello schermo si stampa sul bordo davanti.',
          '- Le vasche sono alte 45 mm e larghe fino al piatto: piatto pulito, tesa (brim) di 5 mm se gli angoli si alzano.',
          f'- Fianchi: il marchio e il nome escono di {_v(M.RILIEVO)} mm dalla faccia di fuori, che stampata in piedi è '
          'verticale: vengono del colore della vasca (a più colori: `../stampa3d_multicolore/`).',
          f'- Mascherina e piano della Flip: {n_etichette} tasche profonde {_v(M.TASCA)} mm per le etichette '
          '(`etichette_mascherina.svg`, da stampare al 100 % su carta adesiva; `etichette_mappa.svg` dice dove va ogni numero). '
          'La mascherina è in due metà accostate, senza giunta: i fori sui comandi della MK4 tengono ogni metà al suo posto.',
          '- Prima delle vasche, `prova_giunta.stl`: le due metà devono calarsi l\'una nell\'altra a mano, e le viti '
          'stringere con il dado nella sua sede. Se la coda è dura, carta abrasiva sui fianchi della coda.', '',
          '## Montaggio', '',
          '1. Le vasche: si calano una accanto all\'altra, in qualunque ordine, sul tavolo; poi le viti delle giunte. '
          'Piedini in gomma sotto, due per colonna.',
          '2. L\'hub nel fermo, con le porte verso il davanti; i cavi come nella console laser (passo 4 di '
          '`istruzioni_montaggio.pdf`). Feltro sugli appoggi del piano (retro, fianchi, costola, colonnina, dente della culla).',
          '3. Il pad nella sua culla, con il cavo a 90° nella finestra di dietro.',
          '4. La culla della Flip avvitata al piano (4 viti M3 svasate, dadi sotto), la cornice sullo schermo; il piano '
          'sugli appoggi.',
          '5. La MK4 sulla pedana, le due metà della mascherina sopra, ogni controllo nel suo foro.',
          '6. Le etichette nelle tasche; la Flip nella culla; i tasti trasparenti del pad con le loro etichette.', '']
    with open(os.path.join(OUT3D, 'pezzi.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


def main():
    piatto = None
    if '--piatto' in sys.argv:
        piatto = float(sys.argv[sys.argv.index('--piatto') + 1])
    righe, totale, files, viti = genera(piatto)
    print(f'STAMPA 3D A VASCHE (piatto {piatto or M.PIATTO_COMUNE[0]:.0f} mm) -> {OUT3D}')
    for r in righe:
        dx, dy, dz = r['dim']
        avvisi = ('' if r['chiuso'] else '  GUSCIO APERTO') + ('' if r['sta'] else '  NON STA NEL PIATTO')
        print(f'  {r["nome"] + ".stl":28s} x{r["quanti"]:<2d} {dx:6.1f} x {dy:6.1f} x {dz:5.1f}  {r["grammi"]:6.0f} g{avvisi}')
    print(f'  filamento: circa {totale / 1000:.2f} kg; viti: {testo_viti(viti)}')
    for p in files:
        print('  ' + os.path.basename(p))


if __name__ == '__main__':
    main()
