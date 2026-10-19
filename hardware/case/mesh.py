"""mesh.py — solidi semplici per i pezzi stampati del case, scritti in STL binario.

Solo libreria standard. Un pezzo è un insieme di gusci chiusi (scatole, cilindri, profili 2D con
fori estrusi); i gusci possono sovrapporsi: lo slicer li unisce. Ogni guscio viene controllato:
ogni spigolo deve stare in due triangoli con versi opposti (guscio chiuso e orientato).
"""
import math
import struct


def _area(poly):
    a = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        a += x1 * y2 - x2 * y1
    return a / 2


def area(poly):
    """area con il segno (positiva se il poligono gira in senso antiorario)"""
    return _area(poly)


def taglia(poly, asse, c, sotto):
    """la parte del poligono con la coordinata asse (0 = x, 1 = y) <= c (sotto) o >= c
    (Sutherland-Hodgman); i punti nuovi stanno esattamente sulla linea"""
    def dentro(p):
        return p[asse] <= c if sotto else p[asse] >= c
    out = []
    for i in range(len(poly)):
        a, b = poly[i - 1], poly[i]
        if dentro(b):
            if not dentro(a):
                out.append(_incrocio(a, b, asse, c))
            out.append(b)
        elif dentro(a):
            out.append(_incrocio(a, b, asse, c))
    return [p for i, p in enumerate(out) if not i or p != out[i - 1]]


def _incrocio(a, b, asse, c):
    t = (c - a[asse]) / (b[asse] - a[asse])
    p = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]
    p[asse] = c
    return (p[0], p[1])


def ccw(poly):
    return poly if _area(poly) > 0 else poly[::-1]


def cw(poly):
    return poly if _area(poly) < 0 else poly[::-1]


GRIGLIA = 4      # decimali dei millimetri: 0,1 µm, sopra la risoluzione dei float dell'STL fino a 1 m


def pulisci(loop):
    """punti sulla griglia di 0,1 µm, senza i punti uguali al precedente (gli archi di un rettangolo
    con raggio pari a metà lato si toccano) né quello di chiusura ripetuto: uno spigolo lungo zero, o
    due quote che differiscono di un errore di arrotondamento, lascerebbero il guscio aperto"""
    out = []
    for x, y in loop:
        p = (round(x, GRIGLIA), round(y, GRIGLIA))
        if not out or p != out[-1]:
            out.append(p)
    while len(out) > 1 and out[0] == out[-1]:
        out.pop()
    return out


def cerchio(cx, cy, r, n=40):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def rett(x0, y0, x1, y1, r=0.0, n=6):
    """rettangolo, con gli angoli arrotondati se r > 0 (senso antiorario)"""
    if r <= 0:
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


# ---- triangolazione di un poligono con fori (ear clipping con ponti verso i fori) ----

def _segs_cross(p1, p2, p3, p4):
    def o(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return 0 if abs(v) < 1e-12 else (1 if v > 0 else -1)
    if p1 in (p3, p4) or p2 in (p3, p4):
        return False
    return o(p1, p2, p3) * o(p1, p2, p4) < 0 and o(p3, p4, p1) * o(p3, p4, p2) < 0


def _unisci_fori(outer, holes):
    """Un poligono solo: ogni foro (orario) si collega all'esterno (antiorario) con un ponte. Il ponte
    non deve attraversare nessun foro, nemmeno quelli non ancora collegati."""
    poly = list(outer)
    tutti = [list(h) for h in holes]
    for h in sorted(holes, key=lambda h: -max(p[0] for p in h)):
        hi = max(range(len(h)), key=lambda i: h[i][0])
        hp = h[hi]
        best, bd = None, None
        for i, p in enumerate(poly):
            d = (p[0] - hp[0]) ** 2 + (p[1] - hp[1]) ** 2
            if bd is not None and d >= bd:
                continue
            ok = True
            for j in range(len(poly)):
                a, b = poly[j], poly[(j + 1) % len(poly)]
                if _segs_cross(hp, p, a, b):
                    ok = False
                    break
            for g in (tutti if ok else ()):
                for k in range(len(g)):
                    a, b = g[k], g[(k + 1) % len(g)]
                    if _segs_cross(hp, p, a, b):
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                best, bd = i, d
        hr = h[hi:] + h[:hi]
        poly = poly[:best + 1] + hr + [hr[0]] + poly[best:]
    return poly


def _in_tri(p, a, b, c):
    def s(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    d1, d2, d3 = s(p, a, b), s(p, b, c), s(p, c, a)
    neg = d1 < -1e-12 or d2 < -1e-12 or d3 < -1e-12
    pos = d1 > 1e-12 or d2 > 1e-12 or d3 > 1e-12
    return not (neg and pos)


def triangola(outer, holes=()):
    """Triangoli (indici nella lista di vertici ritornata) di un profilo con fori. Prima le orecchie
    con i ponti verso i fori; se l'area dei triangoli non torna (molti fori vicini, come nella
    mascherina) si passa alle strisce, che non sbagliano ma non chiudono il guscio (vanno bene per
    il modello e le tavole, non per l'STL)."""
    poly, tris = _orecchie(outer, holes)
    atteso = abs(_area(outer)) - sum(abs(_area(h)) for h in holes)
    fatto = sum(abs(_area([poly[i], poly[j], poly[k]])) for i, j, k in tris)
    if atteso > 0 and abs(fatto - atteso) > 0.002 * atteso:
        return _strisce(outer, holes)
    return poly, tris


def _x_a(lato, y):
    """x del lato (basso, alto) alla quota y; esatta agli estremi, così i vertici combaciano"""
    (x0, y0), (x1, y1) = lato
    if y == y0:
        return x0
    if y == y1:
        return x1
    return round(x0 + (x1 - x0) * (y - y0) / (y1 - y0), GRIGLIA)


def _cerniera(b, t):
    """triangoli antiorari fra due catene orizzontali (b in basso, t in alto, x crescenti)"""
    out, i, j = [], 0, 0
    while i < len(b) - 1 or j < len(t) - 1:
        if j == len(t) - 1 or (i < len(b) - 1 and b[i + 1][0] <= t[j + 1][0]):
            out.append((b[i], b[i + 1], t[j]))
            i += 1
        else:
            out.append((b[i], t[j + 1], t[j]))
            j += 1
    return out


def strisce_chiuse(outer, holes=()):
    """Facce e pareti di un profilo con fori che chiudono sempre il guscio, anche con molti fori:
    strisce fra le quote dei vertici (regola pari-dispari); ogni trapezio ha i lati orizzontali
    spezzati dove cominciano o finiscono i trapezi vicini, e le pareti sono spezzate alle stesse
    quote e agli stessi punti. Niente vertici a T: ogni spigolo sta in due triangoli.
    Torna (facce, anelli): triangoli antiorari della faccia e anelli spezzati per le pareti."""
    anelli = [ccw(outer)] + [cw(h) for h in holes]
    lati = []
    for L in anelli:
        for i in range(len(L)):
            a, b = L[i], L[(i + 1) % len(L)]
            if a[1] != b[1]:
                lati.append((a, b) if a[1] < b[1] else (b, a))
    ys = sorted({p[1] for L in anelli for p in L})
    indice = {y: i for i, y in enumerate(ys)}
    tagli = {y: set() for y in ys}
    for L in anelli:
        for p in L:
            tagli[p[1]].add(p[0])
    strisce = []
    for y0, y1 in zip(ys, ys[1:]):
        ym = (y0 + y1) / 2
        attivi = sorted((l for l in lati if l[0][1] <= y0 and l[1][1] >= y1), key=lambda l: _x_a(l, ym))
        coppie = [(attivi[k], attivi[k + 1]) for k in range(0, len(attivi) - 1, 2)]
        strisce.append((y0, y1, coppie))
        for sx, dx in coppie:
            for y in (y0, y1):
                tagli[y].add(_x_a(sx, y))
                tagli[y].add(_x_a(dx, y))
    ordinati = {y: sorted(v) for y, v in tagli.items()}

    def catena(y, xa, xb):
        return [(x, y) for x in ordinati[y] if xa <= x <= xb]
    facce = []
    for y0, y1, coppie in strisce:
        for sx, dx in coppie:
            facce += _cerniera(catena(y0, _x_a(sx, y0), _x_a(dx, y0)), catena(y1, _x_a(sx, y1), _x_a(dx, y1)))
    spezzati = []
    for L in anelli:
        pts = []
        for i in range(len(L)):
            a, b = L[i], L[(i + 1) % len(L)]
            pts.append(a)
            if a[1] == b[1]:
                xs = [x for x in ordinati[a[1]] if min(a[0], b[0]) < x < max(a[0], b[0])]
                pts += [(x, a[1]) for x in sorted(xs, reverse=a[0] > b[0])]
            else:
                lato = (a, b) if a[1] < b[1] else (b, a)
                livelli = ys[indice[lato[0][1]] + 1:indice[lato[1][1]]]
                pts += [(_x_a(lato, y), y) for y in (livelli if a[1] < b[1] else livelli[::-1])]
        spezzati.append(pts)
    return facce, spezzati


def _strisce(outer, holes):
    """trapezi fra quote successive dei vertici, con la regola pari-dispari"""
    loops = [outer] + list(holes)
    lati = []
    for L in loops:
        for i in range(len(L)):
            a, b = L[i], L[(i + 1) % len(L)]
            if a[1] != b[1]:
                lati.append((a, b) if a[1] < b[1] else (b, a))
    ys = sorted({p[1] for L in loops for p in L})
    poly, tris = [], []
    def x_a(lato, y):
        (x0, y0), (x1, y1) = lato
        return x0 + (x1 - x0) * (y - y0) / (y1 - y0)
    for y0, y1 in zip(ys, ys[1:]):
        if y1 - y0 < 1e-9:
            continue
        ym = (y0 + y1) / 2
        attivi = [l for l in lati if l[0][1] <= ym <= l[1][1]]
        attivi.sort(key=lambda l: x_a(l, ym))
        for k in range(0, len(attivi) - 1, 2):
            sx, dx = attivi[k], attivi[k + 1]
            q = [(x_a(sx, y0), y0), (x_a(dx, y0), y0), (x_a(dx, y1), y1), (x_a(sx, y1), y1)]
            n = len(poly)
            poly += q
            tris += [(n, n + 1, n + 2), (n, n + 2, n + 3)]
    return poly, tris


def _orecchie(outer, holes=()):
    """Triangoli (indici nella lista di vertici ritornata) di un profilo antiorario con fori orari."""
    outer = ccw(outer)
    holes = [cw(h) for h in holes]
    poly = _unisci_fori(outer, holes) if holes else list(outer)
    idx = list(range(len(poly)))
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 100000:
        guard += 1
        n = len(idx)
        trovato = False
        for k in range(n):
            i0, i1, i2 = idx[(k - 1) % n], idx[k], idx[(k + 1) % n]
            a, b, c = poly[i0], poly[i1], poly[i2]
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if cross <= 1e-12:
                continue
            ok = True
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                q = poly[j]
                if q in (a, b, c):
                    continue
                if _in_tri(q, a, b, c):
                    ok = False
                    break
            if ok:
                tris.append((i0, i1, i2))
                idx.pop(k)
                trovato = True
                break
        if not trovato:
            break
    if len(idx) == 3:
        tris.append(tuple(idx))
    return poly, tris


IDENTITA = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def _lin(frame, v):
    """parte lineare di un riferimento (O, U, V, N) applicata a un vettore"""
    _, U, V, N = frame
    return (v[0] * U[0] + v[1] * V[0] + v[2] * N[0],
            v[0] * U[1] + v[1] * V[1] + v[2] * N[1],
            v[0] * U[2] + v[1] * V[2] + v[2] * N[2])


def applica(frame, p):
    """punto locale (u, v, t) -> mondo"""
    O = frame[0]
    q = _lin(frame, p)
    return (O[0] + q[0], O[1] + q[1], O[2] + q[2])


def componi(esterno, interno):
    """riferimento che fa prima interno e poi esterno"""
    return (applica(esterno, interno[0]), _lin(esterno, interno[1]), _lin(esterno, interno[2]), _lin(esterno, interno[3]))


def det(frame):
    _, U, V, N = frame
    return (U[0] * (V[1] * N[2] - V[2] * N[1]) - V[0] * (U[1] * N[2] - U[2] * N[1]) + N[0] * (U[1] * V[2] - U[2] * V[1]))


def ruota_z(gradi, tx=0.0, ty=0.0, tz=0.0):
    a = math.radians(gradi)
    c, s = math.cos(a), math.sin(a)
    return ((tx, ty, tz), (c, s, 0.0), (-s, c, 0.0), (0.0, 0.0, 1.0))


def sposta(tx, ty, tz):
    return ((tx, ty, tz), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


class Mesh:
    """Un pezzo come insieme di prismi: profilo 2D (con fori) estruso da z0 a z1 in un riferimento
    (O, U, V, N). Dai prismi escono i triangoli dell'STL e, uguali, le facce del modello SketchUp."""

    def __init__(self, nome):
        self.nome = nome
        self.prismi = []              # dict(outer, holes, z0, z1, frame)

    @property
    def gusci(self):
        return [self._tris(p) for p in self.prismi]

    def _tris(self, p):
        if p.get('sopra'):
            return self._tronco_tris(p)
        outer, holes, z0, z1, frame = p['outer'], p['holes'], p['z0'], p['z1'], p['frame']
        poly, tris = _orecchie(outer, holes)
        atteso = abs(_area(outer)) - sum(abs(_area(h)) for h in holes)
        fatto = sum(abs(_area([poly[i], poly[j], poly[k]])) for i, j, k in tris)
        if atteso > 0 and abs(fatto - atteso) <= 0.002 * atteso:
            facce = [(poly[i], poly[j], poly[k]) for i, j, k in tris]
            anelli = [ccw(outer)] + [cw(h) for h in holes]
        else:                         # le orecchie non bastano (molti fori): strisce, sempre chiuse
            facce, anelli = strisce_chiuse(outer, holes)
        out = []
        for a, b, c in facce:
            out.append(((a[0], a[1], z1), (b[0], b[1], z1), (c[0], c[1], z1)))     # sopra
            out.append(((a[0], a[1], z0), (c[0], c[1], z0), (b[0], b[1], z0)))     # sotto
        for ring in anelli:
            for i in range(len(ring)):
                p0, q = ring[i], ring[(i + 1) % len(ring)]
                out.append(((p0[0], p0[1], z0), (q[0], q[1], z0), (q[0], q[1], z1)))
                out.append(((p0[0], p0[1], z0), (q[0], q[1], z1), (p0[0], p0[1], z1)))
        rev = det(frame) < 0
        res = []
        for t in out:
            w = tuple(applica(frame, v) for v in t)
            res.append(w[::-1] if rev else w)
        return res

    def _tronco_tris(self, p):
        """il tronco: sotto il profilo outer a z0, sopra il profilo sopra a z1 (stessi punti, uno a uno)"""
        giu, su, z0, z1, frame = ccw(p['outer']), ccw(p['sopra']), p['z0'], p['z1'], p['frame']
        out = []
        for poly, z, alto in ((giu, z0, False), (su, z1, True)):
            pp, tris = _orecchie(poly, [])
            for i, j, k in tris:
                a, b, c = pp[i], pp[j], pp[k]
                out.append(((a[0], a[1], z), (b[0], b[1], z), (c[0], c[1], z)) if alto
                           else ((a[0], a[1], z), (c[0], c[1], z), (b[0], b[1], z)))
        n = len(giu)
        for i in range(n):
            a0, a1, b0, b1 = giu[i], giu[(i + 1) % n], su[i], su[(i + 1) % n]
            out.append(((a0[0], a0[1], z0), (a1[0], a1[1], z0), (b1[0], b1[1], z1)))
            out.append(((a0[0], a0[1], z0), (b1[0], b1[1], z1), (b0[0], b0[1], z1)))
        rev = det(frame) < 0
        return [tuple(applica(frame, v) for v in t)[::-1] if rev else tuple(applica(frame, v) for v in t) for t in out]

    def tronco(self, sotto, z0, sopra, z1, frame=IDENTITA):
        """da un profilo sotto (a z0) a uno sopra (a z1) con lo stesso numero di punti: tasti, svasature"""
        if len(sotto) != len(sopra):
            raise ValueError('tronco: i due profili devono avere gli stessi punti')
        self.prismi.append(dict(outer=list(sotto), holes=[], z0=z0, z1=z1, frame=frame, sopra=list(sopra)))

    def prisma(self, outer, z0, z1, holes=(), frame=IDENTITA):
        """profilo 2D (con fori) estruso da z0 a z1, nel riferimento frame"""
        self.prismi.append(dict(outer=pulisci(outer), holes=[pulisci(h) for h in holes], z0=z0, z1=z1, frame=frame))

    def box(self, x0, y0, z0, x1, y1, z1, frame=IDENTITA):
        self.prisma(rett(x0, y0, x1, y1), z0, z1, frame=frame)

    def cilindro(self, cx, cy, z0, z1, r, n=40, frame=IDENTITA):
        self.prisma(cerchio(cx, cy, r, n), z0, z1, frame=frame)

    def prisma_x(self, profilo_yz, x0, x1):
        """profilo nel piano yz estruso lungo x (per fianchi e cunei)"""
        self.prisma(profilo_yz, x0, x1, frame=((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)))

    def unisci(self, altro, frame=IDENTITA):
        """aggiunge i prismi di un altro pezzo, portati con frame"""
        for p in altro.prismi:
            q = dict(p)
            q['frame'] = componi(frame, p['frame'])
            self.prismi.append(q)

    def portato(self, frame, nome=None):
        m = Mesh(nome or self.nome)
        m.unisci(self, frame)
        return m

    def controlla(self):
        """True se ogni guscio è chiuso e orientato in modo coerente."""
        for g in self.gusci:
            spigoli = {}
            for t in g:
                for i in range(3):
                    a = tuple(round(v, 5) for v in t[i])
                    b = tuple(round(v, 5) for v in t[(i + 1) % 3])
                    spigoli[(a, b)] = spigoli.get((a, b), 0) + 1
            for (a, b), n in spigoli.items():
                if n != 1 or spigoli.get((b, a), 0) != 1:
                    return False
        return True

    def ingombro(self):
        pts = [p for g in self.gusci for t in g for p in t]
        return tuple(min(p[i] for p in pts) for i in range(3)), tuple(max(p[i] for p in pts) for i in range(3))

    def a_terra(self):
        """lo stesso pezzo spostato con l'angolo minimo nell'origine (per lo slicer)"""
        (x0, y0, z0), _ = self.ingombro()
        return self.portato(sposta(-x0, -y0, -z0))

    def salva(self, path):
        tris = [t for g in self.gusci for t in g]
        with open(path, 'wb') as f:
            f.write(self.nome.encode('ascii', 'replace')[:80].ljust(80, b' '))
            f.write(struct.pack('<I', len(tris)))
            for a, b, c in tris:
                u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
                v = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
                n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
                L = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2) or 1.0
                f.write(struct.pack('<12fH', n[0] / L, n[1] / L, n[2] / L, *a, *b, *c, 0))
        return len(tris)
