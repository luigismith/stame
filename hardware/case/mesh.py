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


def ccw(poly):
    return poly if _area(poly) > 0 else poly[::-1]


def cw(poly):
    return poly if _area(poly) < 0 else poly[::-1]


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
    """Un poligono solo: ogni foro (orario) si collega all'esterno (antiorario) con un ponte."""
    poly = list(outer)
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
            if ok:
                for k in range(len(h)):
                    a, b = h[k], h[(k + 1) % len(h)]
                    if _segs_cross(hp, p, a, b):
                        ok = False
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
        outer, holes, z0, z1, frame = p['outer'], p['holes'], p['z0'], p['z1'], p['frame']
        poly, tris = triangola(outer, holes)
        out = []
        for i, j, k in tris:
            a, b, c = poly[i], poly[j], poly[k]
            out.append(((a[0], a[1], z1), (b[0], b[1], z1), (c[0], c[1], z1)))     # sopra
            out.append(((a[0], a[1], z0), (c[0], c[1], z0), (b[0], b[1], z0)))     # sotto
        for ring in [ccw(outer)] + [cw(h) for h in holes]:
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

    def prisma(self, outer, z0, z1, holes=(), frame=IDENTITA):
        """profilo 2D (con fori) estruso da z0 a z1, nel riferimento frame"""
        self.prismi.append(dict(outer=list(outer), holes=[list(h) for h in holes], z0=z0, z1=z1, frame=frame))

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
