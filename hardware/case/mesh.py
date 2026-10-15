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


class Mesh:
    def __init__(self, nome):
        self.nome = nome
        self.gusci = []               # liste di triangoli ((x,y,z),(x,y,z),(x,y,z))

    def _add(self, tris):
        self.gusci.append(tris)

    def box(self, x0, y0, z0, x1, y1, z1):
        self.prisma(rett(x0, y0, x1, y1), z0, z1)

    def cilindro(self, cx, cy, z0, z1, r, n=40):
        self.prisma(cerchio(cx, cy, r, n), z0, z1)

    def prisma(self, outer, z0, z1, holes=()):
        """profilo 2D (con fori) estruso da z0 a z1"""
        poly, tris = triangola(outer, holes)
        out = []
        for i, j, k in tris:
            a, b, c = poly[i], poly[j], poly[k]
            out.append(((a[0], a[1], z1), (b[0], b[1], z1), (c[0], c[1], z1)))     # sopra
            out.append(((a[0], a[1], z0), (c[0], c[1], z0), (b[0], b[1], z0)))     # sotto
        for ring in [ccw(outer)] + [cw(h) for h in holes]:
            for i in range(len(ring)):
                p, q = ring[i], ring[(i + 1) % len(ring)]
                out.append(((p[0], p[1], z0), (q[0], q[1], z0), (q[0], q[1], z1)))
                out.append(((p[0], p[1], z0), (q[0], q[1], z1), (p[0], p[1], z1)))
        self._add(out)

    def prisma_x(self, profilo_yz, x0, x1):
        """profilo nel piano yz estruso lungo x (per fianchi e cunei)"""
        poly, tris = triangola(profilo_yz)
        out = []
        for i, j, k in tris:
            a, b, c = poly[i], poly[j], poly[k]
            out.append(((x1, a[0], a[1]), (x1, b[0], b[1]), (x1, c[0], c[1])))
            out.append(((x0, a[0], a[1]), (x0, c[0], c[1]), (x0, b[0], b[1])))
        ring = ccw(profilo_yz)
        for i in range(len(ring)):
            p, q = ring[i], ring[(i + 1) % len(ring)]
            out.append(((x0, p[0], p[1]), (x0, q[0], q[1]), (x1, q[0], q[1])))
            out.append(((x0, p[0], p[1]), (x1, q[0], q[1]), (x1, p[0], p[1])))
        self._add(out)

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
