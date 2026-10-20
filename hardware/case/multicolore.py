"""multicolore.py — la console stampata a più colori, con le scritte fatte dalla stampante (Luigi,
19/10/2026: «ho una anycubic kobra s1. credo che tu possa preparare i pezzi per il modello da stampare
in multicolor per far si che scriva le etichette direttamente la stampa (magari la faccia superiore deve
essere quella appoggiata sul piatto che viene meglio)»).

Uso: python -I hardware/case/multicolore.py [--piatto 240]     scrive in hardware/case/out/stampa3d_multicolore/

Le stesse vasche di stampa3d.py (60-case.md §7c, CASE-067…070; con il piatto da 240 tre, intere davanti-dietro),
con le scritte stampate in un secondo filamento, incassate a filo per SCRITTA_H (tre strati da 0,2):
- mascherina (in due metà) e piano della Flip si stampano con la faccia in vista sul piatto: viene liscia (o con
  la grana del piatto) e il cambio di colore serve solo nei primi tre strati;
- le vasche con i fianchi hanno il marchio e il nome incassati nella faccia di fuori del fianco, che stampata in
  piedi è verticale: lì il filamento cambia in ogni strato dove ci sono le scritte.
Ogni pezzo con le scritte esce in due STL allineati (_corpo e _scritte) e in un 3MF che li tiene insieme come due
parti di un oggetto, con i filamenti già assegnati.
Le incisioni del laser sono troppo fini per un ugello da 0,4 (pixel da 0,12–0,26 mm): le scritte si
ridisegnano con Matrice, il carattere 5×7 di Stame, a quadretti da 0,45 mm (lettere alte 3,15 mm). Le
scritte vicine fanno un blocco, che si impagina di nuovo (righe una sotto l'altra, colonne che non si
toccano) e si appoggia dove stava l'incisione: in alto, in basso o al centro, a sinistra, a destra o
com'era, finché non tocca fori, bordo e altre scritte. Se non c'entra si prova a 0,40; se ancora non
c'entra resta fuori, e pezzi.md lo dice. Logo e punti grossi (da 0,7 mm in su) restano le forme del laser.
Le zone con le scritte si fanno su una griglia di 0,05 mm: le celle accese vanno nel pezzo delle scritte,
le spente nel corpo, così i due pezzi combaciano senza operazioni fra poligoni.
"""
import math
import os
import sys
import zipfile

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import genera as G                   # noqa: E402
import misure as M                   # noqa: E402
import stampa3d as S                 # noqa: E402
from matrice import GLIFI            # noqa: E402  (tools/, nel percorso di genera)
from mesh import Mesh, rett, sposta, applica   # noqa: E402

OUT = os.path.join(G.OUT, 'stampa3d_multicolore')
SCRITTA_H = 0.6             # profondità delle scritte: tre strati da 0,2
PASSI = (0.45, 0.40)        # lato del quadretto di Matrice: il primo che ci sta
RES = 0.05                  # griglia delle zone con le scritte
MARGINE_FORO = 0.6          # una scritta sta ad almeno 0,6 mm da un foro
MARGINE_BORDO = 1.0         # e a 1 mm dal bordo del pezzo
MARGINE_SCRITTA = 0.6       # e a 0,6 mm da un'altra scritta o da una forma
VICINE = (5.0, 2.0)         # scritte incise più vicine di così (in x, in y) fanno un blocco: le tabelle restano insieme
DISCENDENTI = set('gjpqy')
# due filamenti in tutto, che si scambiano il ruolo: 1 nero, 2 sabbia (o il colore del telaio). I piani
# sono neri con le scritte sabbia, come l'incisione del laser sull'acrilico; i fianchi sono del telaio con
# le scritte nere, come la bruciatura sul legno
FILAMENTI = {'piano': (1, 2), 'telaio': (2, 1)}       # (corpo, scritte)
TINTA = {1: (34, 36, 38), 2: (226, 212, 176)}
FLIP = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0))   # 180° attorno a x: la faccia giù


# ---------------------------------------------------------------------------------------------
# le scritte e le forme incise di un pezzo del laser, in coordinate del disegno

def _bbox(loops):
    xs = [p[0] for L in loops for p in L]
    ys = [p[1] for L in loops for p in L]
    return (min(xs), min(ys), max(xs), max(ys))


def _spessore(el, loop):
    b = _bbox([loop])
    if el.startswith('<circle'):
        return b[2] - b[0]
    if el.startswith('<rect'):
        return min(b[2] - b[0], b[3] - b[1])
    per = sum(math.dist(loop[i - 1], loop[i]) for i in range(len(loop)))
    return 2 * abs(S.area(loop)) / per if per else 0.0


def leggi(svg):
    """(etichette, forme, scartate): le scritte troppo fini da ridisegnare, i contorni da tenere come
    sono (logo, punti grossi) e quante incisioni fini non sono scritte (restano fuori)"""
    loops = [G._parse_svg_el(el)[0] for el in svg.incisione]
    usati, etichette, forme = set(), [], []
    for r in svg.scritte:
        idx = list(range(r['i0'], r['i1']))
        usati.update(idx)
        if not idx:
            continue
        if r['tratto'] >= M.DETTAGLIO_MIN:
            forme += [loops[i] for i in idx]
        else:
            etichette.append(dict(testo=r['testo'], allinea=r['allinea'], bbox=_bbox([loops[i] for i in idx])))
    scartate = 0
    for i, el in enumerate(svg.incisione):
        if i in usati:
            continue
        if _spessore(el, loops[i]) >= M.DETTAGLIO_MIN:
            forme.append(loops[i])
        else:
            scartate += 1
    return etichette, forme, scartate


# ---------------------------------------------------------------------------------------------
# impaginazione: i blocchi di scritte, ridisegnati a quadretti

def _tocca(a, b, d=0.0, dy=None):
    dy = d if dy is None else dy
    return a[0] < b[2] + d and b[0] < a[2] + d and a[1] < b[3] + dy and b[1] < a[3] + dy


def _blocchi(etichette):
    padre = list(range(len(etichette)))

    def radice(a):
        while padre[a] != a:
            a = padre[a]
        return a
    for i in range(len(etichette)):
        for j in range(i + 1, len(etichette)):
            if _tocca(etichette[i]['bbox'], etichette[j]['bbox'], *VICINE):
                padre[radice(i)] = radice(j)
    gruppi = {}
    for i, e in enumerate(etichette):
        gruppi.setdefault(radice(i), []).append(e)
    return list(gruppi.values())


def _larga(testo, P):
    return G.matrice_w(testo, P)


def _alta(testo, P):
    return (9 if DISCENDENTI & set(testo) else 7) * P


def _ancora(e):
    b = e['bbox']
    return {'sinistra': b[0], 'destra': b[2]}.get(e['allinea'], (b[0] + b[2]) / 2)


def _impagina(blocco, P):
    """le scritte del blocco a quadretti P: righe una sotto l'altra (due quadretti fra due righe),
    colonne allineate come nell'incisione e spinte a destra quanto serve perché non si tocchino.
    Torna [(testo, x0, top)] e l'ingombro, con la cima della prima riga a 0"""
    righe = []
    for e in sorted(blocco, key=lambda e: (e['bbox'][1] + e['bbox'][3]) / 2):
        cy, h = (e['bbox'][1] + e['bbox'][3]) / 2, e['bbox'][3] - e['bbox'][1]
        if righe and abs(cy - righe[-1]['cy']) < 0.6 * min(h, righe[-1]['h']):
            righe[-1]['el'].append(e)
        else:
            righe.append(dict(cy=cy, h=h, el=[e]))
    colonne = []
    for e in sorted(blocco, key=_ancora):
        for c in colonne:
            if c['allinea'] == e['allinea'] and abs(c['x'] - _ancora(e)) < 1.0:
                c['el'].append(e)
                break
        else:
            colonne.append(dict(x=_ancora(e), allinea=e['allinea'], el=[e]))
    colonne.sort(key=lambda c: c['x'])
    pos, spinta, destra_prec = {}, 0.0, None
    for c in colonne:
        lw = max(_larga(e['testo'], P) for e in c['el'])
        x = c['x'] + spinta
        sinistra = {'sinistra': x, 'destra': x - lw}.get(c['allinea'], x - lw / 2)
        if destra_prec is not None and sinistra < destra_prec + 3 * P:
            d = destra_prec + 3 * P - sinistra
            spinta += d
            sinistra += d
        for e in c['el']:
            w = _larga(e['testo'], P)
            pos[id(e)] = {'sinistra': sinistra, 'destra': sinistra + lw - w}.get(c['allinea'], sinistra + (lw - w) / 2)
        destra_prec = sinistra + lw
    out, y = [], 0.0
    for r in righe:
        h = max(_alta(e['testo'], P) for e in r['el'])
        for e in r['el']:
            out.append((e['testo'], pos[id(e)], y))
        y += h + 2 * P
    xs = [x for _, x, _ in out] + [x + _larga(t, P) for t, x, _ in out]
    return out, (min(xs), 0.0, max(xs), y - 2 * P)


def _dentro(p, poly):
    x, y, c = p[0], p[1], False
    for i in range(len(poly)):
        (x0, y0), (x1, y1) = poly[i - 1], poly[i]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    return c


def _nel_bordo(r, outer):
    """il rettangolo, allargato del margine, sta tutto dentro il contorno (un punto ogni 0,5 mm)"""
    x0, y0, x1, y1 = r[0] - MARGINE_BORDO, r[1] - MARGINE_BORDO, r[2] + MARGINE_BORDO, r[3] + MARGINE_BORDO
    nx, ny = max(2, int((x1 - x0) / 0.5)), max(2, int((y1 - y0) / 0.5))
    pts = [(x0 + (x1 - x0) * i / nx, y) for i in range(nx + 1) for y in (y0, y1)]
    pts += [(x, y0 + (y1 - y0) * j / ny) for j in range(ny + 1) for x in (x0, x1)]
    return all(_dentro(p, outer) for p in pts)


def impagina(etichette, forme, outer, holes, extra=()):
    """[(testo, x0, top, P)] delle scritte che stanno, e i testi dei blocchi che non ci stanno; extra sono
    rettangoli dove non si scrive (le culle e i piedi appoggiati sul pezzo)"""
    ostacoli = list(extra) + [(b[0] - MARGINE_FORO, b[1] - MARGINE_FORO, b[2] + MARGINE_FORO, b[3] + MARGINE_FORO)
                for b in (_bbox([h]) for h in holes)]
    ostacoli += [(b[0] - MARGINE_SCRITTA, b[1] - MARGINE_SCRITTA, b[2] + MARGINE_SCRITTA, b[3] + MARGINE_SCRITTA)
                 for b in (_bbox([f]) for f in forme)]
    posate, fuori = [], []
    # prima i blocchi grandi, che hanno meno posti dove stare
    for blocco in sorted(_blocchi(etichette), key=lambda b: -sum(len(e['testo']) for e in b)):
        lb = _bbox([[(e['bbox'][0], e['bbox'][1]), (e['bbox'][2], e['bbox'][3])] for e in blocco])
        trovato = None
        for P in PASSI:
            righe, (ix0, iy0, ix1, iy1) = _impagina(blocco, P)
            w, h = ix1 - ix0, iy1 - iy0
            # dove appoggiarlo: la cima, il fondo o il centro dell'incisione; com'era, a sinistra, a destra
            ys = [lb[1], lb[3] - h, (lb[1] + lb[3] - h) / 2]
            xs = [0.0, lb[0] - ix0, lb[2] - ix1]
            for top in ys:
                for dx in xs:
                    r = (ix0 + dx, top, ix1 + dx, top + h)
                    if any(_tocca(r, o) for o in ostacoli) or not _nel_bordo(r, outer):
                        continue
                    trovato = (P, [(t, x + dx, top + y) for t, x, y in righe], r)
                    break
                if trovato:
                    break
            if trovato:
                break
        if not trovato:
            fuori.append(' / '.join(e['testo'] for e in blocco))
            continue
        P, righe, r = trovato
        posate += [(t, x, y, P) for t, x, y in righe]
        ostacoli.append((r[0] - MARGINE_SCRITTA, r[1] - MARGINE_SCRITTA, r[2] + MARGINE_SCRITTA, r[3] + MARGINE_SCRITTA))
    return posate, fuori


def quadretti(testo, x0, top, P):
    """i quadretti accesi di una scritta Matrice: (x0, y0, x1, y1) nel disegno, y in giù"""
    out, x = [], x0
    for ch in testo:
        g = GLIFI.get(ch, GLIFI['?'])
        for ri, riga in enumerate(g):
            for ci, c in enumerate(riga):
                if c == '#':
                    out.append((x + ci * P, top + ri * P, x + (ci + 1) * P, top + (ri + 1) * P))
        x += (len(g[0]) + 1) * P
    return out


# ---------------------------------------------------------------------------------------------
# dal disegno al pezzo: le zone con le scritte, su una griglia, divise fra scritte e fondo

def _uv(F, fr, p):
    return tuple(round(c, 4) for c in S.locale(F, applica(fr, (p[0], p[1], 0.0)))[:2])


def _rett_uv(F, fr, r):
    a, b = _uv(F, fr, (r[0], r[1])), _uv(F, fr, (r[2], r[3]))
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))


def _griglia(v, su):
    return (math.ceil(v / RES - 1e-6) if su else math.floor(v / RES + 1e-6)) * RES


def regioni(svg, F, fr, posate, forme):
    """le zone rettangolari (sulla griglia) con dentro i rettangoli delle scritte e quelli del fondo"""
    from PIL import Image, ImageDraw
    pezzi = []       # (rett uv, quadretti uv, forme uv)
    for t, x, y, P in posate:
        q = [_rett_uv(F, fr, r) for r in quadretti(t, x, y, P)]
        pezzi.append(dict(r=_bbox([[(a[0], a[1]), (a[2], a[3])] for a in q]), q=q, f=[]))
    for f in forme:
        fu = [_uv(F, fr, p) for p in f]
        pezzi.append(dict(r=_bbox([fu]), q=[], f=[fu]))
    # le zone: ogni pezzo con 0,2 mm attorno; quelle che si toccano diventano una
    zone = [dict(r=(p['r'][0] - 0.2, p['r'][1] - 0.2, p['r'][2] + 0.2, p['r'][3] + 0.2), q=list(p['q']), f=list(p['f']))
            for p in pezzi]
    cambiato = True
    while cambiato:
        cambiato = False
        for i in range(len(zone)):
            for j in range(i + 1, len(zone)):
                if _tocca(zone[i]['r'], zone[j]['r'], 0.4):
                    a, b = zone[i], zone[j]
                    zone[i] = dict(r=(min(a['r'][0], b['r'][0]), min(a['r'][1], b['r'][1]),
                                      max(a['r'][2], b['r'][2]), max(a['r'][3], b['r'][3])), q=a['q'] + b['q'], f=a['f'] + b['f'])
                    del zone[j]
                    cambiato = True
                    break
            if cambiato:
                break
    out = []
    for z in zone:
        u0, v0 = _griglia(z['r'][0], False), _griglia(z['r'][1], False)
        u1, v1 = _griglia(z['r'][2], True), _griglia(z['r'][3], True)
        W, H = round((u1 - u0) / RES), round((v1 - v0) / RES)
        img = Image.new('L', (W, H), 0)
        d = ImageDraw.Draw(img)
        for a in z['q']:
            c0, r0 = round((a[0] - u0) / RES), round((a[1] - v0) / RES)
            c1, r1 = round((a[2] - u0) / RES), round((a[3] - v0) / RES)
            if c1 > c0 and r1 > r0:
                d.rectangle([c0, r0, c1 - 1, r1 - 1], fill=255)
        for f in z['f']:
            d.polygon([((p[0] - u0) / RES - 0.5, (p[1] - v0) / RES - 0.5) for p in f], fill=255)
        px = img.load()
        testo, fondo, prec, banda = [], [], None, None

        def chiudi(sig, ra, rb):
            for c0, c1, on in sig:
                q = (round(u0 + c0 * RES, 4), round(v0 + ra * RES, 4), round(u0 + c1 * RES, 4), round(v0 + rb * RES, 4))
                (testo if on else fondo).append(q)
        for r in range(H + 1):
            sig = None
            if r < H:
                sig, c0 = [], 0
                for c in range(1, W + 1):
                    if c == W or (px[c, r] > 127) != (px[c0, r] > 127):
                        sig.append((c0, c, px[c0, r] > 127))
                        c0 = c
                sig = tuple(sig)
            if sig != prec:
                if prec is not None:
                    chiudi(prec, banda, r)
                prec, banda = sig, r
        out.append(dict(rett=(round(u0, 4), round(v0, 4), round(u1, 4), round(v1, 4)), testo=testo, fondo=fondo))
    return out


# ---------------------------------------------------------------------------------------------
# i pezzi, i solidi, i file

def _pad_in_colonna(etichette):
    """mascherina: fra le due file di pad della MK4 ci sono 2,8 mm, troppo pochi per una scritta stampata.
    I tipi d'accordo e i piatti del banco B (sopra) vanno sotto, con l'estensione e il tamburo della stessa
    colonna: alto/basso, come stanno i pad («DIM/6», «B:CHH/KICK»)"""
    sopra = {G.PAD_SOTTO[f'PAD{k}'][i]: G.PAD_SOPRA[f'PAD{k + 4}'][i] for k in range(1, 5) for i in (0, 1)}
    togli = {v for v in sopra.values()}
    out = []
    for e in etichette:
        if e['testo'] in togli:
            continue
        if e['testo'] in sopra:
            a, b = sopra[e['testo']], e['testo']
            e = dict(e, testo=f'{a}/{b}' if not a.startswith('B:') else f'{a}/{b[2:]}')
        out.append(e)
    return out


def _appoggiati(nome_laser, F, fr):
    """i pezzi stampati che appoggiano sul piano della Flip (la culla), nel disegno"""
    if nome_laser != 'piano_flip':
        return []
    out = []
    inv = _inversa(fr)
    for s in G.STAMPATI:
        if s['nome'] != 'culla_flip':
            continue
        for f in s['frames'] or [None]:
            ms = s['mesh'].portato(f) if f else s['mesh']
            for g in ms.gusci:
                pts = [p for t in g for p in t if abs(p[2] - M.Z_PIANO) < 0.05]
                if pts:
                    q = [applica(inv, p)[:2] for p in pts]
                    b = _bbox([q])
                    out.append((b[0] - MARGINE_SCRITTA, b[1] - MARGINE_SCRITTA, b[2] + MARGINE_SCRITTA, b[3] + MARGINE_SCRITTA))
    return out


def _inversa(fr):
    """l'inversa di un riferimento ortonormale (O, U, V, N)"""
    O, U, V, N = fr
    o = (-sum(O[i] * U[i] for i in range(3)), -sum(O[i] * V[i] for i in range(3)), -sum(O[i] * N[i] for i in range(3)))
    return (o, (U[0], V[0], N[0]), (U[1], V[1], N[1]), (U[2], V[2], N[2]))


def con_scritte(pz, nome_laser, copia=0):
    """dà al pezzo le regioni delle scritte stampate; torna (scritte posate, blocchi fuori, incisioni scartate)"""
    p = S._laser(nome_laser)
    svg, fr = p['svg'], p['frames'][copia]
    etichette, forme, scartate = leggi(svg)
    if nome_laser == 'mascherina':
        etichette = _pad_in_colonna(etichette)
    outer, holes = svg.contorni()
    posate, fuori = impagina(etichette, forme, outer, holes, _appoggiati(nome_laser, pz.F, fr))
    pz.tasche, pz.rilievi = [], []
    pz.regioni = regioni(svg, pz.F, fr, posate, forme)
    pz.disegno = fr                   # per l'anteprima: dove va la riga di scrittura
    pz.faccia = pz.T if pz.T else max(w1 for _, _, _, w1 in pz.strati)     # le pareti: la faccia di fuori
    return posate, fuori, scartate


def solidi(pz, t):
    corpo, scritte = Mesh(f'Stame {pz.nome} corpo'), Mesh(f'Stame {pz.nome} scritte')
    zone = [rett(*r['rett']) for r in t['regioni']]
    zf = pz.faccia
    for outer, holes, w0, w1 in t['strati']:
        if abs(w1 - zf) < 1e-6 and zone:
            corpo.prisma(outer, w0, w1 - SCRITTA_H, holes=holes)
            corpo.prisma(outer, w1 - SCRITTA_H - S.SOVRAPPOSTO, w1, holes=holes + zone)
        else:
            corpo.prisma(outer, w0, w1, holes=holes)
    for r in t['regioni']:
        for q in r['fondo']:
            corpo.prisma(rett(*q), zf - SCRITTA_H - S.SOVRAPPOSTO, zf)
        for q in r['testo']:
            scritte.prisma(rett(*q), zf - SCRITTA_H, zf)
    return corpo, scritte


def orienta(pz, t, ms, faccia_giu):
    """come S.per_la_stampa, senza appoggiare: nel verso fisico giusto, ruotato se serve e, per i pezzi con
    le scritte, girato con la faccia in vista sul piatto"""
    if S._det(G.SPECCHIO) * S._det(pz.F) < 0:
        ms = ms.portato(((0.0, 0.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))
    if t['angolo']:
        a = math.radians(t['angolo'])
        ms = ms.portato(((0.0, 0.0, 0.0), (math.cos(a), math.sin(a), 0.0), (-math.sin(a), math.cos(a), 0.0), (0.0, 0.0, 1.0)))
    return ms.portato(FLIP) if faccia_giu else ms


def salva_3mf(path, nome, parti):
    """un oggetto con più parti (core 3MF, componenti): [(nome, Mesh, filamento)]"""
    risorse, componenti = [], []
    for k, (pn, ms, _) in enumerate(parti, 1):
        idx, vert, tri = {}, [], []
        for g in ms.gusci:
            for t in g:
                ii = []
                for v in t:
                    key = tuple(round(c, 4) for c in v)
                    if key not in idx:
                        idx[key] = len(vert)
                        vert.append(key)
                    ii.append(idx[key])
                if len(set(ii)) == 3:
                    tri.append(ii)
        vs = ''.join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in vert)
        ts = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tri)
        risorse.append(f'<object id="{k}" type="model" name="{pn}"><mesh><vertices>{vs}</vertices>'
                       f'<triangles>{ts}</triangles></mesh></object>')
        componenti.append(f'<component objectid="{k}"/>')
    oid = len(parti) + 1
    modello = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<model unit="millimeter" xml:lang="it-IT" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
               '<metadata name="Title">' + nome + '</metadata>\n<metadata name="Application">Stame multicolore.py</metadata>\n'
               '<resources>\n' + '\n'.join(risorse) + f'\n<object id="{oid}" type="model" name="{nome}"><components>'
               + ''.join(componenti) + '</components></object>\n</resources>\n'
               f'<build><item objectid="{oid}"/></build>\n</model>\n')
    impostazioni = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n'
                    f'  <object id="{oid}">\n    <metadata key="name" value="{nome}"/>\n    <metadata key="extruder" value="1"/>\n'
                    + ''.join(f'    <part id="{k}" subtype="normal_part">\n      <metadata key="name" value="{pn}"/>\n'
                              f'      <metadata key="extruder" value="{fil}"/>\n    </part>\n'
                              for k, (pn, _, fil) in enumerate(parti, 1))
                    + '  </object>\n</config>\n')
    tipi = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
            '<Default Extension="config" ContentType="text/xml"/></Types>\n')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>\n')
    # data fissa nello zip: rigenerare lo stesso pezzo dà lo stesso file
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for nome, testo in (('[Content_Types].xml', tipi), ('_rels/.rels', rels),
                            ('3D/3dmodel.model', modello),
                            ('Metadata/model_settings.config', impostazioni)):
            info = zipfile.ZipInfo(nome, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, testo)


def _verso_scrittura(pz, t):
    """angolo (gradi, antiorario) della riga di scrittura nel pezzo orientato a faccia in su"""
    a, b = _uv(pz.F, pz.disegno, (0.0, 0.0)), _uv(pz.F, pz.disegno, (10.0, 0.0))
    ms = Mesh('verso')
    for u, v in (a, b):
        ms.box(u - 0.01, v - 0.01, 0.0, u + 0.01, v + 0.01, 0.01)
    ms = orienta(pz, t, ms, False)
    c = [tuple(sum(p[i] for t_ in g for p in t_) / (3 * len(g)) for i in range(2)) for g in ms.gusci]
    return math.degrees(math.atan2(c[1][1] - c[0][1], c[1][0] - c[0][0]))


def anteprima(path, corpo, scritte, titolo, verso=0.0, filamenti=(1, 2)):
    """la faccia in vista come la si guarda, con il pezzo girato a faccia in su e la riga di scrittura
    orizzontale: nero e sabbia, 8 px/mm"""
    from PIL import Image, ImageDraw
    def facce(ms):
        tris = [t for g in ms.gusci for t in g]
        zt = max(p[2] for t in tris for p in t)
        return [t for t in tris if all(abs(p[2] - zt) < 1e-4 for p in t)]
    fc, fs = facce(corpo), facce(scritte)
    pts = [p for t in fc for p in t]
    x0, y0 = min(p[0] for p in pts), min(p[1] for p in pts)
    x1, y1 = max(p[0] for p in pts), max(p[1] for p in pts)
    k, m, fondo = 8.0, 20, (246, 245, 239)
    img = Image.new('RGB', (int((x1 - x0) * k) + 2 * m, int((y1 - y0) * k) + 2 * m), fondo)
    d = ImageDraw.Draw(img)

    def T(p):
        return (m + (p[0] - x0) * k, m + (y1 - p[1]) * k)
    for t in fc:
        d.polygon([T(p) for p in t], fill=TINTA[filamenti[0]])
    for t in fs:
        d.polygon([T(p) for p in t], fill=TINTA[filamenti[1]])
    img = img.rotate(-verso, expand=True, fillcolor=fondo)
    bb = Image.eval(img.convert('L'), lambda v: 255 if v < 240 else 0).getbbox()
    if bb:
        img = img.crop((max(bb[0] - m, 0), max(bb[1] - m, 0), min(bb[2] + m, img.width), min(bb[3] + m, img.height)))
    out = Image.new('RGB', (img.width, img.height + 30), fondo)
    out.paste(img, (0, 30))
    ImageDraw.Draw(out).text((m, 8), titolo, fill=(20, 27, 24))
    out.save(path, optimize=True)


def _scrivi(nome, corpo, scritte, colore, piatto, minimo):
    """corpo e scritte già nel verso della stampa: appoggiati insieme sul piatto, in due STL e in un 3MF; torna la
    riga dell'elenco (ingombro, chiuso, sta, grammi) e gli strati con il cambio di filamento"""
    tutto = Mesh(f'Stame {nome}')
    tutto.unisci(corpo)
    tutto.unisci(scritte)
    (x0, y0, z0), _ = tutto.ingombro()
    corpo, scritte, tutto = (m.portato(sposta(-x0, -y0, -z0)) for m in (corpo, scritte, tutto))
    corpo.nome, scritte.nome = f'Stame {nome} corpo', f'Stame {nome} scritte'
    corpo.salva(os.path.join(OUT, f'{nome}_corpo.stl'))
    scritte.salva(os.path.join(OUT, f'{nome}_scritte.stl'))
    fil_c, fil_s = FILAMENTI[colore]
    salva_3mf(os.path.join(OUT, f'{nome}.3mf'), nome, [('corpo', corpo, fil_c), ('scritte', scritte, fil_s)])
    dim, _, sta, _ = S.verifica(tutto, piatto, minimo)
    (_, _, za), (_, _, zb) = scritte.ingombro()
    return dict(nome=nome, file=f'`{nome}.3mf` (o `{nome}_corpo.stl` + `{nome}_scritte.stl`)', dim=dim, colore=colore,
                chiuso=corpo.controlla() and scritte.controlla(), sta=sta, grammi=S.grammi(corpo) + S.grammi(scritte),
                cambi=round((zb - za) / 0.2))


def genera(piatto=None):
    piatto = piatto or M.PRINT_BED[0]
    G.genera()
    report = {}
    masch, pf = S.piano('mascherina', 1), S.piano('piano_flip', 1)
    fianchi = {'sx': S.fianco('sx'), 'dx': S.fianco('dx')}
    for pz, nl in ((masch, 'mascherina'), (pf, 'piano_flip'), (fianchi['sx'], 'fianco_sx_esterno'), (fianchi['dx'], 'fianco_dx_esterno')):
        report[pz.nome] = con_scritte(pz, nl)
    vv = S.vasche(piatto, fianchi, lambda pz, t: solidi(pz, t) if t['regioni'] else (S.solido(pz, t), None))
    os.makedirs(OUT, exist_ok=True)          # dopo le vasche: se il piatto non basta, la cartella resta com'è
    for n in os.listdir(OUT):                # il resto (il PDF di manuale.py) resta
        if n.endswith(('.stl', '.3mf', '.md', '.png')):
            os.remove(os.path.join(OUT, n))
    righe, totale, viti = [], 0.0, []
    # le vasche, in piedi: il marchio e il nome nella faccia di fuori dei fianchi
    for v in vv:
        nota = v['nota'] + '; in piedi, il fondo sul piatto'
        viti += v['viti']
        if v['scritte'].prismi:
            r = _scrivi(v['nome'], v['corpo'].portato(G.SPECCHIO), v['scritte'].portato(G.SPECCHIO), 'telaio', piatto, 0.5)
            r['nota'] = nota + f'; marchio e nome nel fianco, che è verticale: il filamento cambia in {r["cambi"]} strati'
            for pz, t in v['facce']:
                vc, vs = solidi(pz, t)
                anteprima(os.path.join(OUT, f'anteprima_{pz.nome}.png'), orienta(pz, t, vc, False), orienta(pz, t, vs, False),
                          f'{pz.nome}: la faccia di fuori di {v["nome"]}', _verso_scrittura(pz, t), FILAMENTI[pz.colore])
        else:
            ms = v['corpo'].portato(G.SPECCHIO).a_terra()
            ms.nome = f'Stame {v["nome"]}'
            ms.salva(os.path.join(OUT, v['nome'] + '.stl'))
            dim, chiuso, sta, _ = S.verifica(ms, piatto, 0.5)
            r = dict(nome=v['nome'], file=f'`{v["nome"]}.stl`', dim=dim, colore='telaio', chiuso=chiuso, sta=sta,
                     grammi=S.grammi(ms), nota=nota)
        righe.append(r)
    # mascherina e piano della Flip, con la faccia in vista sul piatto
    for nome, pz, t in S.pezzi_piani(piatto, masch, pf):
        corpo, scritte = solidi(pz, t)
        r = _scrivi(nome, orienta(pz, t, corpo, True), orienta(pz, t, scritte, True), pz.colore, piatto, 0.3)
        r['nota'] = ('la metà ' + ('sinistra' if nome.endswith('_1') else 'destra') + ' della mascherina; '
                     if nome[-2] == '_' else '') + 'scritte incassate nella faccia in vista, che sta sul piatto'
        vc, vs = solidi(pz, t)
        anteprima(os.path.join(OUT, f'anteprima_{nome}.png'), orienta(pz, t, vc, False), orienta(pz, t, vs, False),
                  f'{nome}: la faccia in vista', _verso_scrittura(pz, t), FILAMENTI[pz.colore])
        righe.append(r)
    for s in G.STAMPATI:
        if s['nome'] not in ('culla_flip', 'visiera'):
            continue
        ms = s['mesh'].portato(G.SPECCHIO).portato(s['posa']).a_terra()
        ms.salva(os.path.join(OUT, s['nome'] + '.stl'))
        dim, chiuso, sta, _ = S.verifica(ms, piatto)
        righe.append(dict(nome=s['nome'], file=f'`{s["nome"]}.stl`', dim=dim, colore=s['materiale'], nota=s['nota'],
                          grammi=S.grammi(ms) * s['quanti'], chiuso=chiuso, sta=sta))
    ms = S.prova_giunta().portato(G.SPECCHIO).a_terra()
    ms.nome = 'Stame prova della giunta'
    ms.salva(os.path.join(OUT, 'prova_giunta.stl'))
    dim, chiuso, sta, _ = S.verifica(ms, piatto, 0.3)
    righe.append(dict(nome='prova_giunta', file='`prova_giunta.stl`', dim=dim, colore='telaio', chiuso=chiuso, sta=sta,
                      grammi=S.grammi(ms), nota='la giunta sotto la MK4 in piccolo, le due metà insieme: da stampare prima'))
    totale = sum(r['grammi'] for r in righe)
    scrivi_elenco(righe, totale, piatto, report, viti)
    return righe, totale, report, viti


def parti_console(piatto=None):
    """la console montata, per rendering.py --stampata: vasche, piani, culla della Flip e visiera nel riferimento
    del case, come le parti di assieme.py; ogni pezzo con le scritte in due parti, «nome» e «nome_scritte»"""
    piatto = piatto or M.PRINT_BED[0]
    G.genera()
    masch, pf = S.piano('mascherina', 1), S.piano('piano_flip', 1)
    fianchi = {'sx': S.fianco('sx'), 'dx': S.fianco('dx')}
    for pz, nl in ((masch, 'mascherina'), (pf, 'piano_flip'), (fianchi['sx'], 'fianco_sx_esterno'), (fianchi['dx'], 'fianco_dx_esterno')):
        con_scritte(pz, nl)
    vv = S.vasche(piatto, fianchi, lambda pz, t: solidi(pz, t) if t['regioni'] else (S.solido(pz, t), None))
    out = []
    for v in vv:
        out.append(dict(nome=v['nome'], passo=1, colore=TINTA[2], mesh=v['corpo']))
        if v['scritte'].prismi:
            out.append(dict(nome=v['nome'] + '_scritte', passo=1, colore=TINTA[1], mesh=v['scritte']))
    for nome, pz, t in S.pezzi_piani(piatto, masch, pf):
        corpo, scritte = solidi(pz, t)
        out.append(dict(nome=nome, passo=2, colore=TINTA[1], mesh=corpo.portato(pz.F)))
        out.append(dict(nome=nome + '_scritte', passo=2, colore=TINTA[2], mesh=scritte.portato(pz.F)))
    for s in G.STAMPATI:
        if s['nome'] in ('culla_flip', 'visiera'):
            out.append(dict(nome=s['nome'], passo=2, colore=TINTA[1], mesh=s['mesh']))
    return out


def scrivi_elenco(righe, totale, piatto, report, viti):
    v = S._v
    n_vasche = sum(1 for r in righe if r['nome'].startswith('vasca_'))
    L = ['# Stame — la console stampata a più colori', '',
         f'Generato da `hardware/case/multicolore.py` per un piatto di {piatto:.0f} × {piatto:.0f} mm (Anycubic Kobra S1 '
         f'con l\'ACE Pro, o un\'altra stampante a più filamenti). Le stesse {n_vasche} vasche di `../stampa3d/` (con `--piatto '
         f'{piatto:.0f}`), stampate in piedi con il fondo sul piatto, e gli stessi pezzi che si tolgono; le scritte le fa la '
         'stampa, nel secondo filamento: incassate a filo nella faccia in vista di mascherina e piano della Flip, che sta sul '
         'piatto, e nella faccia di fuori dei fianchi. Le istruzioni da stampare, con le anteprime, sono in '
         '`istruzioni_multicolore.pdf`.', '',
         '| File | Ingombro (mm) | Grammi | Colore | Note |', '|---|---|---|---|---|']
    for r in righe:
        dx, dy, dz = r['dim']
        L.append(f'| {r["file"]} | {dx:.0f} × {dy:.0f} × {v(dz)} | {r["grammi"]:.0f} | '
                 f'{S.COLORI.get(r["colore"], r["colore"])} | {r["nota"]} |')
    cambi = max((r.get('cambi', 0) for r in righe if r['nome'].startswith('vasca_')), default=0)
    L += ['', f'Filamento: circa {v(totale / 1000)} kg in tutto, quasi tutto del colore del corpo. Viti delle giunte: '
          f'{S.testo_viti(viti)}.', '',
          '## In Anycubic Slicer Next', '',
          '1. Apri il `.3mf` del pezzo: arriva un oggetto con due parti, «corpo» e «scritte». Se lo slicer lo apre come due '
          'oggetti, o se preferisci gli STL: importa insieme `_corpo.stl` e `_scritte.stl` e, alla domanda, caricali come un '
          'oggetto solo con più parti.',
          '2. Due filamenti in tutto: 1 nero, 2 sabbia (o il colore scelto per il telaio). Mascherina e piano della Flip: '
          'corpo 1 e scritte 2, come l\'incisione del laser sull\'acrilico nero. Vasche: corpo 2 e scritte 1, come la '
          'bruciatura sul legno. Nel `.3mf` è già così; con gli STL si assegna a mano. La vasca di centro e la prova di '
          'giunta col 2, la culla della Flip e la visiera col 1.',
          '3. Non girare i pezzi: le vasche stanno in piedi con il fondo sul piatto, mascherina e piano con la faccia in vista '
          'sul piatto. Il piatto liscio la fa lucida, quello testurizzato le dà la sua grana.',
          f'4. Strati da 0,2 e primo strato da 0,2: nei piani le scritte sono profonde {v(SCRITTA_H)} mm, cioè i primi tre '
          f'strati. Nelle vasche il fianco è verticale e le scritte sono profonde {v(SCRITTA_H)} mm nella faccia di fuori: il '
          f'filamento cambia in ogni strato fra il basso del marchio e la cima del nome, circa {cambi} strati per vasca. '
          'Torre di spurgo sì; spurgo nel riempimento se lo slicer lo offre. Se i cambi sono troppi, le vasche di '
          '`../stampa3d/` hanno il marchio in rilievo, di un colore.',
          '5. Il resto come la console stampata a un colore: 3 perimetri, 4 strati pieni, riempimento al 20 %, senza '
          'supporti (solo la visiera, che si stampa sul tettuccio, li vuole sotto i piedi). Il primo strato deve essere '
          'perfetto: piatto pulito, '
          'livellamento fatto. Prima delle vasche, `prova_giunta.stl`.', '',
          '## Le scritte', '',
          'Le incisioni del laser sono troppo fini per un ugello da 0,4: qui le scritte sono ridisegnate con Matrice, il '
          'carattere 5×7 di Stame, a quadretti da 0,45 mm (lettere alte 3,15 mm) o da 0,40 dove non c\'è posto. Logo e punti '
          'del nome restano quelli del laser. Sulla mascherina fra le due file di pad ci sono 2,8 mm: i tipi d\'accordo e i '
          'piatti del banco B vanno sotto i pad, con l\'estensione e il tamburo della stessa colonna, alto/basso come i pad: '
          '«DIM/6» è DIM sul pad di sopra e 6 su quello di sotto, «B:CHH/KICK» il charleston sopra e la cassa sotto. Le '
          'anteprime `anteprima_*.png` mostrano ogni faccia come la si guarda.', '']
    for nome, (posate, fuori, scartate) in report.items():
        passi = sorted({P for *_, P in posate})
        riga = f'- **{nome}**: {len(posate)} {"scritta" if len(posate) == 1 else "scritte"}'
        if passi:
            riga += ' a ' + ' e '.join(f'{v(P, 2)} mm' for P in passi)
        if fuori:
            riga += f'; non ci stanno, e restano fuori: {"; ".join(fuori)}'
        if scartate:
            riga += f'; {scartate} tratti fini che non sono scritte (righe di separazione) non si stampano'
        L.append(riga + '.')
    L += ['', 'Le giunte delle vasche e il montaggio sono come nella console a un colore: `../stampa3d/pezzi.md`.', '']
    with open(os.path.join(OUT, 'pezzi.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


def main():
    piatto = None
    if '--piatto' in sys.argv:
        piatto = float(sys.argv[sys.argv.index('--piatto') + 1])
    righe, totale, report, _ = genera(piatto)
    print(f'STAMPA A PIÙ COLORI (piatto {piatto or M.PRINT_BED[0]:.0f} mm) -> {OUT}')
    for r in righe:
        dx, dy, dz = r['dim']
        avvisi = ('' if r['chiuso'] else '  GUSCIO APERTO') + ('' if r['sta'] else '  NON STA NEL PIATTO')
        cambi = f'  {r["cambi"]} strati con il cambio' if r.get('cambi') else ''
        print(f'  {r["nome"]:22s} {dx:6.1f} x {dy:6.1f} x {dz:5.1f}  {r["grammi"]:6.0f} g{cambi}{avvisi}')
    print(f'  filamento: circa {totale / 1000:.2f} kg')
    for nome, (posate, fuori, scartate) in report.items():
        print(f'  {nome}: {len(posate)} scritte, fuori {len(fuori)}: {fuori}; tratti fini scartati {scartate}')


if __name__ == '__main__':
    main()


