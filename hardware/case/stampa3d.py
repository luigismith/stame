"""stampa3d.py — la console tutta stampata, per chi non ha il laser (Luigi, 18/10/2026: «crea anche
tutto quello che serve per farla tutta stampata 3d»).

Uso: python -I hardware/case/stampa3d.py [--piatto 210]      scrive in hardware/case/out/stampa3d/

Gli stessi pezzi di genera.py, presi con i loro riferimenti nello spazio del case, diventano pezzi da
stampare (60-case.md §7b, CASE-060…CASE-066):
- gli strati incollati diventano un pezzo solo: ogni fianco (quattro strati), ogni metà del retro con
  il suo strato d'appoggio, la costola (due strati); la base è una lastra sola invece di due metà;
- quello che non sta sul piatto (210 × 210 mm di default, cioè le stampanti da 220 in su) si divide
  in tasselli con le code di rondine, da incollare; i pezzi lunghi che entrano in diagonale escono già
  ruotati;
- le incisioni del laser sono troppo fini per un ugello da 0,4 mm: sui fianchi il marchio e il nome
  escono in rilievo (cambiando filamento alla quota della faccia vengono di un altro colore); sulla
  mascherina e sul piano della Flip ogni scritta ha una tasca profonda 0,4 mm, e le scritte si
  stampano su carta adesiva (etichette_mascherina.pdf), una per tasca;
- culle, visiera, fermo dell'hub e squadrette sono già pezzi stampati: si copiano come sono.
Gli STL escono nel verso fisico giusto, con la faccia in vista in alto. pezzi.md elenca i pezzi, il
filamento e le impostazioni; tasselli.svg mostra come si uniscono.
"""
import math
import os
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import genera as G                   # noqa: E402
import misure as M                   # noqa: E402
from mesh import Mesh, rett, applica, taglia, area, IDENTITA   # noqa: E402

OUT3D = os.path.join(G.OUT, 'stampa3d')
SOVRAPPOSTO = 0.2           # gli strati di uno stesso pezzo si compenetrano: lo slicer li fonde
MARGINE_TAGLIO = 1.5        # un taglio fra tasselli passa ad almeno 1,5 mm da fori, tasche e rilievi
DENSITA = 1.27              # g/cm³, PETG (il PLA è 1,24)


# ---------------------------------------------------------------------------------------------
# riferimenti: il piano di un pezzo stampato è (O, U, V, N); (u, v) sul piano, w lungo lo spessore,
# con la faccia in vista dalla parte di w alto

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
# i pezzi da stampare

class Pezzo:
    def __init__(self, nome, F, colore, nota):
        self.nome, self.F, self.colore, self.nota = nome, F, colore, nota
        self.strati = []        # (contorno, fori, w0, w1)
        self.rilievi = []       # (contorno, w0, w1)
        self.tasche = []        # dict(rett=(u0, v0, u1, v1), n, elementi)
        self.regioni = []       # scritte stampate a più colori (multicolore.py): dict(rett, testo, fondo)
        self.faccia = None      # quota w della faccia in vista, dove stanno le tasche


def _pezzo_da_strati(nome, F, colore, nota, strati):
    """un pezzo da strati del laser in ordine di w: dal secondo in giù ognuno scende di SOVRAPPOSTO
    nel precedente, così lo slicer li fonde in un solido solo"""
    pz = Pezzo(nome, F, colore, nota)
    for i, s in enumerate(sorted(strati, key=lambda s: s['w0'])):
        pz.strati.append((s['outer'], s['holes'], s['w0'] - (SOVRAPPOSTO if i else 0.0), s['w1']))
    return pz


def base():
    """la base in una lastra sola: il contorno di tutte e due le metà, senza la coda di rondine"""
    F = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    a, b, Y = M.FIANCO, M.LARGHEZZA - M.FIANCO, M.BASE_Y1
    outer = [(a, 0.0)] + G._tacche_retro(a, b) + [(b, 0.0), (b, Y)] + G._tacche_fronte(a, b) + [(a, Y)]
    holes = strato('base_sx', F)['holes'] + strato('base_dx', F)['holes']
    pz = Pezzo('base', F, 'telaio', 'lastra da 6 mm; i tasselli si incollano a coda di rondine')
    pz.strati.append(([(round(x, 4), round(y, 4)) for x, y in outer], holes, 0.0, M.BASE_T))
    return pz


def fianco(lato):
    """i quattro strati di un fianco in un pezzo: la faccia esterna in alto, con il marchio e il nome in
    rilievo; i fori delle viti delle squadrette proseguono 6 mm oltre lo strato d'appoggio"""
    L = M.LARGHEZZA
    if lato == 'sx':
        F = ((M.FIANCO, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (-1.0, 0.0, 0.0))
    else:
        F = ((L - M.FIANCO, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
    est = strato(f'fianco_{lato}_esterno', F)
    app = strato(f'fianco_{lato}_appoggio', F)
    pz = Pezzo(f'fianco_{lato}', F, 'telaio',
               'quattro strati in uno; faccia esterna in alto, marchio e nome in rilievo')
    w1 = app['w1']
    pz.strati.append((app['outer'], app['holes'], app['w0'], w1))
    pz.strati.append((est['outer'], app['holes'], w1 - SOVRAPPOSTO, w1 + 6.0))
    pz.strati.append((est['outer'], [], w1 + 6.0 - SOVRAPPOSTO, est['w1']))
    for inc in incisioni(f'fianco_{lato}_esterno', F):
        if inc['spessore'] >= M.DETTAGLIO_MIN:
            pz.rilievi.append((inc['loop'], est['w1'] - SOVRAPPOSTO, est['w1'] + M.RILIEVO))
    return pz


def retro(lato):
    """una metà del retro con il suo strato d'appoggio, la faccia di dietro in alto"""
    F = ((0.0, M.APPOGGIO_Y, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0))
    return _pezzo_da_strati(f'retro_{lato}', F, 'telaio', 'retro e strato d\'appoggio in un pezzo',
                            [strato(f'retro_{lato}', F), strato(f'appoggio_retro_{lato}', F)])


def costola():
    F = ((M.COSTOLA_X0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
    return _pezzo_da_strati('costola', F, 'telaio', 'i due strati della costola in un pezzo',
                            [strato('costola_sx', F), strato('costola_dx', F)])


def fronte():
    F = ((0.0, M.FRONTE_Y, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0))
    return _pezzo_da_strati('fronte', F, 'telaio', 'parete davanti, la faccia esterna in alto',
                            [strato('fronte_dx', F)])


def piano(nome, n0):
    """mascherina o piano della Flip: lastra da 3 mm, nera, con una tasca per ogni gruppo di scritte"""
    F = ((0.0, 0.0, M.Z_PIANO0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    s = strato(nome, F)
    pz = Pezzo(nome, F, 'piano', 'lastra da 3 mm; le scritte su carta adesiva, nelle tasche')
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
# tasselli: tagli dritti che non toccano fori, tasche e rilievi; code di rondine sui tagli

def _intervalli(loop, asse, c):
    """intervalli dell'altra coordinata dove la linea coord[asse] = c sta dentro il contorno"""
    altro, ts = 1 - asse, []
    for i in range(len(loop)):
        p, q = loop[i - 1], loop[i]
        if (p[asse] - c) * (q[asse] - c) < 0:
            ts.append(p[altro] + (q[altro] - p[altro]) * (c - p[asse]) / (q[asse] - p[asse]))
    ts.sort()
    return [(ts[k], ts[k + 1]) for k in range(0, len(ts) - 1, 2)]


def _interseca(a, b):
    out = []
    for x0, x1 in a:
        for y0, y1 in b:
            lo, hi = max(x0, y0), min(x1, y1)
            if hi > lo:
                out.append((lo, hi))
    return out


def _ostacoli(pz):
    """rettangoli che un taglio o una coda non devono toccare"""
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
    """n - 1 tagli fra lo e hi, fuori dagli intervalli vietati, con le celle non più larghe di lim"""
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


def _sagoma(asse, c, t, verso, sede):
    """la coda (sede=False) o la sua sede con il gioco, come punti (u, v) in ordine di t crescente"""
    g = M.GIOCO_STAMPA if sede else 0.0
    a, b, d = M.CODA['collo'] / 2 + g, M.CODA['testa'] / 2 + g, M.CODA['prof'] + g
    nt = [(c, t - a), (c + verso * d, t - b), (c + verso * d, t + b), (c, t + a)]
    return [(round(n, 4), round(tt, 4)) if asse == 0 else (round(tt, 4), round(n, 4)) for n, tt in nt]


def _con_code(poly, asse, c, code, lato):
    """inserisce nei lati del poligono che stanno sulla linea coord[asse] = c le code (dalla parte che
    sporge) o le sedi; lato = -1 se il tassello sta sotto c, +1 sopra"""
    altro, out = 1 - asse, []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        out.append(p)
        if abs(p[asse] - c) < 1e-6 and abs(q[asse] - c) < 1e-6:
            t0, t1 = p[altro], q[altro]
            dentro = sorted((cd for cd in code if min(t0, t1) < cd[0] < max(t0, t1)), key=lambda cd: cd[0],
                            reverse=t1 < t0)
            for t, verso in dentro:
                pts = _sagoma(asse, c, t, verso, sede=(verso == lato))
                out += pts if t1 > t0 else pts[::-1]
    return out


def _posa_code(pz, asse, c, t_lo, t_hi, obs):
    """dove mettere le code lungo il taglio coord[asse] = c fra t_lo e t_hi: dentro tutti gli strati che
    toccano il taglio, lontano dagli angoli delle celle e dagli ostacoli; verso +1 o -1"""
    validi = [(t_lo, t_hi)]
    for outer, _, _, _ in pz.strati:
        iv = _intervalli(outer, asse, c)
        if iv:
            validi = _interseca(validi, iv)
    b2 = M.CODA['testa'] / 2 + M.GIOCO_STAMPA
    d = M.CODA['prof'] + M.GIOCO_STAMPA
    m = b2 + 3.0
    validi = [(lo + m, hi - m) for lo, hi in validi if hi - lo > 2 * m]
    code = []
    for lo, hi in validi:
        n = max(1, round((hi - lo + 2 * m) / 50.0))
        for k in range(n):
            ideale = lo + (hi - lo) * (k + 0.5) / n if n > 1 else (lo + hi) / 2
            fatto = False
            for i in range(120):
                t = ideale + (i + 1) // 2 * 0.5 * (1 if i % 2 else -1)
                if not lo <= t <= hi or any(abs(t - q[0]) < 2 * b2 + 6.0 for q in code):
                    continue
                for verso in (1, -1):
                    n0, n1 = sorted((c, c + verso * (d + 1.5)))
                    zona = (n0, t - b2 - 1.5, n1, t + b2 + 1.5) if asse == 0 else (t - b2 - 1.5, n0, t + b2 + 1.5, n1)
                    if any(_tocca(zona, o) for o in obs):
                        continue
                    ok = True
                    for outer, _, _, _ in pz.strati:      # la sede non buca il bordo del pezzo
                        for cc in (c + verso * 0.5, c + verso * (d + 1.5)):
                            if _intervalli(outer, asse, c) and not any(a <= t - b2 - 1.5 and t + b2 + 1.5 <= b
                                                                       for a, b in _intervalli(outer, asse, cc)):
                                ok = False
                    if ok:
                        code.append((round(t, 3), verso))
                        fatto = True
                        break
                if fatto:
                    break
    return code


def _ingombro(pz):
    pts = [p for outer, _, _, _ in pz.strati for p in outer]
    return _bbox(pts)


def _angolo_che_entra(pts, lato):
    """l'angolo (gradi) a cui il pezzo entra nel quadrato lato × lato, o None: dritto se entra dritto,
    altrimenti l'angolo con più margine, purché restino 1,5 mm per lato (per il bordo dello slicer)"""
    def ingombro(gradi):
        a = math.radians(gradi)
        ca, sa = math.cos(a), math.sin(a)
        us = [p[0] * ca - p[1] * sa for p in pts]
        vs = [p[0] * sa + p[1] * ca for p in pts]
        return max(max(us) - min(us), max(vs) - min(vs)), max(us) - min(us) <= lato and max(vs) - min(vs) <= lato
    for gradi in (0, 90):
        if ingombro(gradi)[1]:
            return gradi
    m, gradi = min((ingombro(g)[0], g) for g in range(1, 90))
    return gradi if m <= lato - 3.0 else None


def dividi(pz, piatto):
    """i tasselli: dict(strati, rilievi, tasche, angolo, cella, code) nel piano del pezzo"""
    pts = [p for outer, _, _, _ in pz.strati for p in outer]
    if _det(G.SPECCHIO) * _det(pz.F) < 0:          # come uscirà sul piatto, specchiato
        pts = [(-u, v) for u, v in pts]
    ang = _angolo_che_entra(pts, piatto)
    if ang is not None:
        return [dict(strati=pz.strati, rilievi=pz.rilievi, tasche=pz.tasche, regioni=pz.regioni, angolo=ang, cella=None, giunte=[])]
    u0, v0, u1, v1 = _ingombro(pz)
    lim = piatto - M.CODA['prof'] - M.GIOCO_STAMPA - 2.0
    obs = _ostacoli(pz)
    tagli = {}
    for asse, lo, hi in ((0, u0, u1), (1, v0, v1)):
        vietati = [(o[asse] - MARGINE_TAGLIO, o[asse + 2] + MARGINE_TAGLIO) for o in obs]
        vietati += [(x - MARGINE_TAGLIO, x + MARGINE_TAGLIO) for x in _vertici_interni(pz, asse)]
        n = max(1, math.ceil((hi - lo) / lim))
        t = _scegli_tagli(lo, hi, n, lim, vietati) if n > 1 else []
        while t is None:
            n += 1
            t = _scegli_tagli(lo, hi, n, lim, vietati)
        tagli[asse] = [lo] + t + [hi]
    us, vs = tagli[0], tagli[1]
    # le code: per ogni taglio, cella per cella
    code = {}
    for i in range(1, len(us) - 1):
        for j in range(len(vs) - 1):
            code[(0, i, j)] = _posa_code(pz, 0, us[i], vs[j], vs[j + 1], obs)
    for j in range(1, len(vs) - 1):
        for i in range(len(us) - 1):
            code[(1, j, i)] = _posa_code(pz, 1, vs[j], us[i], us[i + 1], obs)
    out = []
    for j in range(len(vs) - 1):
        for i in range(len(us) - 1):
            cella = (us[i], vs[j], us[i + 1], vs[j + 1])
            strati = []
            for outer, holes, w0, w1 in pz.strati:
                p = outer
                for asse, c, sotto in ((0, cella[0], False), (0, cella[2], True), (1, cella[1], False), (1, cella[3], True)):
                    p = taglia(p, asse, c, sotto)
                    if len(p) < 3:
                        break
                if len(p) < 3 or abs(area(p)) < 1.0:
                    continue
                if i > 0:
                    p = _con_code(p, 0, us[i], code[(0, i, j)], +1)
                if i < len(us) - 2:
                    p = _con_code(p, 0, us[i + 1], code[(0, i + 1, j)], -1)
                if j > 0:
                    p = _con_code(p, 1, vs[j], code[(1, j, i)], +1)
                if j < len(vs) - 2:
                    p = _con_code(p, 1, vs[j + 1], code[(1, j + 1, i)], -1)

                def nella(loop):
                    b = _bbox(loop)
                    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
                    return cella[0] <= cx < cella[2] and cella[1] <= cy < cella[3]
                strati.append((p, [h for h in holes if nella(h)], w0, w1))
            if not strati:
                continue

            def dentro(r):
                cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
                return cella[0] <= cx < cella[2] and cella[1] <= cy < cella[3]
            giunte = [len(code.get((0, i, j), [])) if i > 0 else None, len(code.get((0, i + 1, j), [])) if i < len(us) - 2 else None,
                      len(code.get((1, j, i), [])) if j > 0 else None, len(code.get((1, j + 1, i), [])) if j < len(vs) - 2 else None]
            out.append(dict(strati=strati, rilievi=[r for r in pz.rilievi if dentro(_bbox(r[0]))],
                            tasche=[t for t in pz.tasche if dentro(t['rett'])],
                            regioni=[r for r in pz.regioni if dentro(r['rett'])], angolo=0, cella=cella, giunte=giunte))
    return out


# ---------------------------------------------------------------------------------------------
# solidi e STL

def solido(pz, t):
    """il tassello come Mesh nel piano del pezzo (u, v, w)"""
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


def per_la_stampa(pz, t, ms):
    """nel verso fisico giusto (specchiato se il piano del pezzo è sinistrorso nel mondo), ruotato se
    entra solo in diagonale, appoggiato sul piatto"""
    if _det(G.SPECCHIO) * _det(pz.F) < 0:
        ms = ms.portato(((0.0, 0.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))
    if t['angolo']:
        a = math.radians(t['angolo'])
        ms = ms.portato(((0.0, 0.0, 0.0), (math.cos(a), math.sin(a), 0.0), (-math.sin(a), math.cos(a), 0.0), (0.0, 0.0, 1.0)))
    return ms.a_terra()


def grammi(ms):
    """stima del filamento: 3 perimetri da 0,4, 4 strati pieni sopra e sotto, riempimento al 20 %"""
    g = 0.0
    for p in ms.prismi:
        h = p['z1'] - p['z0']
        a = abs(area(p['outer'])) - sum(abs(area(hh)) for hh in p['holes'])
        per = sum(math.dist(L[i - 1], L[i]) for L in [p['outer']] + p['holes'] for i in range(len(L)))
        v = a * h
        guscio = min(v, per * h * 1.2 + 2 * a * min(0.8, h / 2))
        g += (guscio + 0.2 * (v - guscio)) * DENSITA / 1000.0
    return g


# ---------------------------------------------------------------------------------------------
# il foglio delle etichette e la tavola dei tasselli

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


def tavola_tasselli(divisi, cartella):
    """i pezzi divisi, come stanno sul piatto (faccia in vista in alto) e uniti: numero di ogni tassello,
    code di rondine"""
    W, H, mar = 297.0, 210.0, 10.0
    corpo = [_testo(mar, mar + 5, 'Stame — i tasselli della console stampata, visti dall\'alto come escono dal piatto', 5.0, '#141B18', 700)]
    x, y, riga_h = mar, mar + 14.0, 0.0
    for pz, tasselli in divisi:
        if len(tasselli) < 2:
            continue
        specchio = _det(G.SPECCHIO) * _det(pz.F) < 0
        pts = [p for t in tasselli for o, _, _, _ in t['strati'] for p in o]
        b = _bbox(pts)
        s = 0.3
        w, h = (b[2] - b[0]) * s, (b[3] - b[1]) * s
        if x + w > W - mar:
            x, y, riga_h = mar, y + riga_h + 14.0, 0.0

        def T(p):
            u = (b[2] - p[0]) if specchio else (p[0] - b[0])
            return (x + u * s, y + (b[3] - p[1]) * s)
        corpo.append(_testo(x, y - 2.0, f'{pz.nome}: {len(tasselli)} tasselli', 3.2, '#333', 700))
        for k, t in enumerate(tasselli, 1):
            o = t['strati'][-1][0]
            d = 'M' + ' L'.join(f'{a:.2f},{c:.2f}' for a, c in map(T, o)) + ' Z'
            corpo.append(f'<path d="{d}" fill="{"#D9C3A0" if pz.colore == "telaio" else "#3A3C3F"}" stroke="#222" stroke-width="0.25"/>')
            for hh in t['strati'][-1][1]:
                d = 'M' + ' L'.join(f'{a:.2f},{c:.2f}' for a, c in map(T, hh)) + ' Z'
                corpo.append(f'<path d="{d}" fill="#FFFFFF" stroke="#222" stroke-width="0.15"/>')
            bb = _bbox(o)
            cx, cy = T(((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2))
            corpo.append(_testo(cx, cy + 1.4, str(k), 4.0, '#B86A00' if pz.colore == 'telaio' else '#FFFFFF', 700, 'middle'))
        x += w + 14.0
        riga_h = max(riga_h, h)
    p = os.path.join(cartella, 'tasselli.svg')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(_svg_testa(W, H, 'Stame — tasselli') + ''.join(corpo) + '</svg>\n')
    return p


# ---------------------------------------------------------------------------------------------

COLORI = {'telaio': 'telaio: PLA o PETG color legno o sabbia', 'piano': 'piani: nero',
          'petg_nero': 'nero', 'petg_sabbia': 'sabbia'}
TINTE = {'telaio': (216, 198, 160), 'piano': (40, 40, 44)}


def disegni(divisi, cartella):
    """la console stampata montata, vista davanti e dietro, con le giunte dei tasselli (assieme.py)"""
    import assieme as A
    parti = []
    for pz, tasselli in divisi:
        for k, t in enumerate(tasselli, 1):
            parti.append(dict(nome=f'{pz.nome}_{k}', passo=1, colore=TINTE[pz.colore], mesh=solido(pz, t).portato(pz.F)))
    for s in G.STAMPATI:
        for i, fr in enumerate(s['frames'] or [IDENTITA]):
            parti.append(dict(nome=f'{s["nome"]}_{i}', passo=1, colore=A.COLORI[s['materiale']], mesh=s['mesh'].portato(fr)))
    parti += A.apparecchi()
    out = [A.disegna(parti, os.path.join(cartella, 'console_stampata.png'), titolo='Stame, la console tutta stampata',
                     testo='Gli stessi pezzi del laser, stampati: telaio color sabbia, piani neri, tasselli incollati a coda di rondine.'),
           A.disegna(parti, os.path.join(cartella, 'console_stampata_retro.png'), vista=(-0.7, 0.9, 0.7))]
    return out


def genera(piatto=None):
    piatto = piatto or M.PIATTO_COMUNE[0]
    G.genera()
    os.makedirs(OUT3D, exist_ok=True)
    for n in os.listdir(OUT3D):
        if n.endswith(('.stl', '.svg', '.md', '.png', '.pdf')):
            os.remove(os.path.join(OUT3D, n))
    masch = piano('mascherina', 1)
    pf = piano('piano_flip', 1 + len(masch.tasche))
    pezzi = [base(), fianco('sx'), fianco('dx'), retro('sx'), retro('dx'), costola(), fronte(), masch, pf]
    righe, divisi, totale = [], [], 0.0
    for pz in pezzi:
        tasselli = dividi(pz, piatto)
        divisi.append((pz, tasselli))
        for k, t in enumerate(tasselli, 1):
            nome = pz.nome if len(tasselli) == 1 else f'{pz.nome}_{k}'
            ms = per_la_stampa(pz, t, solido(pz, t))
            ms.nome = f'Stame {nome}'
            chiuso = ms.controlla()
            (x0, y0, z0), (x1, y1, z1) = ms.ingombro()
            ms.salva(os.path.join(OUT3D, nome + '.stl'))
            g = grammi(ms)
            totale += g
            senza = [s for s in ('sinistra', 'destra', 'sotto', 'sopra') if t['giunte'] and t['giunte'][('sinistra', 'destra', 'sotto', 'sopra').index(s)] == 0]
            righe.append(dict(nome=nome, quanti=1, dim=(x1 - x0, y1 - y0, z1 - z0), colore=pz.colore, nota=pz.nota,
                              angolo=t['angolo'], grammi=g, chiuso=chiuso, sta=(x1 - x0) <= piatto + 0.01 and (y1 - y0) <= piatto + 0.01,
                              senza_code=senza))
    for s in G.STAMPATI:
        ms = s['mesh'].portato(G.SPECCHIO).portato(s['posa']).a_terra()
        ms.salva(os.path.join(OUT3D, s['nome'] + '.stl'))
        (x0, y0, z0), (x1, y1, z1) = ms.ingombro()
        g = grammi(ms) * s['quanti']
        totale += g
        righe.append(dict(nome=s['nome'], quanti=s['quanti'], dim=(x1 - x0, y1 - y0, z1 - z0), colore=s['materiale'], nota=s['nota'],
                          angolo=0, grammi=g, chiuso=ms.controlla(), sta=(x1 - x0) <= piatto and (y1 - y0) <= piatto, senza_code=[]))
    svgs, n_etichette = etichette([masch, pf], OUT3D)
    tav = tavola_tasselli(divisi, OUT3D)
    scrivi_elenco(righe, totale, piatto, n_etichette)
    pngs = disegni(divisi, OUT3D)
    return righe, totale, svgs + [tav] + pngs


def _v(x, d=1):
    return f'{x:.{d}f}'.replace('.', ',')


def scrivi_elenco(righe, totale, piatto, n_etichette):
    L = [f'# Stame — la console tutta stampata', '',
         f'Generato da `hardware/case/stampa3d.py` (piatto {piatto:.0f} × {piatto:.0f} mm). Ogni pezzo sta sul piatto '
         'così com\'è nel file: nel verso giusto, con la faccia in vista in alto; quelli lunghi sono già ruotati in diagonale.', '',
         '| File | Quanti | Ingombro (mm) | Colore | Note |', '|---|---|---|---|---|']
    for r in righe:
        dx, dy, dz = r['dim']
        nota = r['nota'] + (f'; ruotato di {r["angolo"]}° per stare sul piatto' if r['angolo'] else '')
        L.append(f'| `{r["nome"]}.stl` | {r["quanti"]} | {dx:.0f} × {dy:.0f} × {_v(dz)} | '
                 f'{COLORI.get(r["colore"], r["colore"])} | {nota} |')
    L += ['', f'Filamento: circa {_v(totale / 1000)} kg in tutto (stima con 3 perimetri, 4 strati pieni sopra e sotto, '
          'riempimento al 20 %).', '',
          '## Impostazioni', '',
          '- PETG o PLA, ugello 0,4, strati da 0,2. Telaio (base, fianchi, retro, costola, parete davanti) in un colore '
          'legno o sabbia; mascherina, piano della Flip e culle in nero.',
          '- 3 perimetri, 4 strati pieni sopra e sotto, riempimento giroide al 20 %. Senza supporti, tranne la visiera.',
          f'- Fianchi: il marchio e il nome escono di {_v(M.RILIEVO)} mm dalla faccia esterna. Per averli in un altro colore, '
          f'cambio di filamento (M600) alla quota {_v(M.FIANCO)} mm, cioè all\'inizio del rilievo.',
          f'- Mascherina e piano della Flip: {n_etichette} tasche profonde {_v(M.TASCA)} mm per le etichette '
          '(`etichette_mascherina.svg`, da stampare al 100 % su carta adesiva; `etichette_mappa.svg` dice dove va ogni numero).',
          f'- Tasselli: code di rondine con {_v(M.GIOCO_STAMPA, 2)} mm di gioco per lato. Si incollano su un piano dritto con '
          'colla cianoacrilica o epossidica bicomponente; `tasselli.svg` mostra come stanno insieme.', '']
    with open(os.path.join(OUT3D, 'pezzi.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


def main():
    piatto = None
    if '--piatto' in sys.argv:
        piatto = float(sys.argv[sys.argv.index('--piatto') + 1])
    righe, totale, svgs = genera(piatto)
    print(f'STAMPA 3D (piatto {piatto or M.PIATTO_COMUNE[0]:.0f} mm) -> {OUT3D}')
    for r in righe:
        dx, dy, dz = r['dim']
        avvisi = ('' if r['chiuso'] else '  GUSCIO APERTO') + ('' if r['sta'] else '  NON STA NEL PIATTO')
        avvisi += f'  senza code: {", ".join(r["senza_code"])}' if r['senza_code'] else ''
        rot = f'  ruotato {r["angolo"]}°' if r['angolo'] else ''
        print(f'  {r["nome"] + ".stl":22s} x{r["quanti"]:<2d} {dx:6.1f} x {dy:6.1f} x {dz:5.1f}  {r["grammi"]:6.0f} g{rot}{avvisi}')
    print(f'  filamento: circa {totale / 1000:.2f} kg')
    for p in svgs:
        print('  ' + os.path.basename(p))


if __name__ == '__main__':
    main()
