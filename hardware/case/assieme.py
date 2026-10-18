"""assieme.py — la console montata: modello 3D, dati per SketchUp e tavole del montaggio.

Uso: python -I hardware/case/assieme.py           scrive in hardware/case/out/ e out/montaggio/

Parte dai pezzi registrati da genera.py (contorni del taglio e riferimenti nello spazio del case)
e aggiunge gli apparecchi semplificati: MPK mini IV, macro pad, Miyoo Flip aperta, hub. Il
riferimento del case è sinistrorso (x a destra, y verso il musicista, z in su): tutto ciò che esce
in 3D passa per SPECCHIO, così il modello non è al rovescio.

Escono:
- stame_console.obj e .mtl: il modello in millimetri, un oggetto per pezzo;
- stame_sketchup.json: i prismi in pollici, per costruire il modello in SketchUp (un livello per
  passo del montaggio);
- montaggio/passo_N.png: le tavole del montaggio, con i pezzi nuovi in ambra.
"""
import json
import math
import os
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import genera as G                   # noqa: E402
import misure as M                   # noqa: E402
from mesh import Mesh, rett, cerchio, sposta, componi, applica, IDENTITA  # noqa: E402

OUT = G.OUT
MONTAGGIO = os.path.join(OUT, 'montaggio')

COLORI = {
    'betulla4': (214, 182, 135), 'betulla6': (205, 172, 124), 'acrilico3': (28, 28, 31),
    'petg_nero': (48, 48, 52), 'petg_sabbia': (204, 189, 158), 'tpu': (70, 70, 72),
    'mk4': (232, 232, 226), 'mk4_tasti': (247, 247, 242), 'mk4_neri': (34, 34, 36), 'mk4_pad': (82, 82, 86),
    'manopole': (52, 52, 56), 'pad': (38, 38, 42), 'trasparente': (214, 222, 226), 'flip': (64, 66, 72), 'schermo': (14, 44, 40), 'hub': (96, 98, 104),
    'pad_fondo': (30, 30, 34), 'pad_trasparente': (206, 218, 222), 'pad_satinata': (188, 200, 206), 'alluminio': (196, 198, 202),
}
AMBRA = (236, 150, 40)

PASSI = {
    1: ('La base', 'Unire le due metà della base a coda di rondine, con la colla vinilica. Piedini in gomma sotto.'),
    2: ('Retro, costola e parete davanti', 'Il retro nelle tacche del bordo posteriore, con lo strato d\'appoggio incollato davanti; i due strati della costola incollati fra loro e nelle asole; la parete davanti nelle sue. Colla nelle linguette.'),
    3: ('I fianchi', 'Incollare i quattro strati di ogni fianco: fuori quello inciso, dentro quello d\'appoggio, più basso dietro. Poi avvitarli alla base con le sei squadrette M3.'),
    4: ('L\'hub e i cavi', 'Fermo dell\'hub avvitato alla base, hub dentro. Il cavo USB della MK4 passa dietro, sotto la costola; quello del pad arriva dalla culla. Strisce di feltro sugli appoggi.'),
    5: ('La culla del pad', 'La culla sulla base, fra costola, fianco e parete davanti. Il pad dentro, con il cavo a 90° nella finestra di dietro.'),
    6: ('Il piano della Flip', 'Culla della Flip e visiera avvitate al piano (viti M3 da sopra, dadi sotto); il piano sugli appoggi, con il bordo davanti sul dente della culla del pad.'),
    7: ('MK4 e mascherina', 'La MK4 nel suo posto, con il cavo USB a 90°; la mascherina sopra: appoggia sulla MK4 e sugli strati d\'appoggio, ogni controllo nel suo foro.'),
    8: ('La Flip e i cavi', 'La Flip aperta nella culla; OTG nella fessura dietro, verso l\'hub; jack e ricarica nella fessura davanti, verso il retro.'),
    9: ('Le etichette', 'Togliere i tasti del pad e mettere i tasti trasparenti; sotto ogni coperchio la sua etichetta (etichette_pad.pdf).'),
}


# ---------------------------------------------------------------------------------------------
# le parti: dict(nome, passo, colore, mesh)

def _laser_mesh(p, frame):
    outer, holes = p['svg'].contorni()
    m = Mesh(p['nome'])
    m.prisma(outer, 0.0, p['t'], holes=holes, frame=frame)
    return m


def parti_case():
    G.genera()
    out = []
    for p in G.LASER:
        for i, fr in enumerate(p['frames']):
            nome = p['nome'] if len(p['frames']) == 1 else f'{p["nome"]}_{i + 1}'
            out.append(dict(nome=nome, passo=p['passo'], colore=COLORI[p['materiale']], mesh=_laser_mesh(p, fr)))
    for s in G.STAMPATI:
        frames = s['frames'] or [IDENTITA]
        for i, fr in enumerate(frames):
            nome = s['nome'] if len(frames) == 1 else f'{s["nome"]}_{i + 1}'
            out.append(dict(nome=nome, passo=s['passo'], colore=COLORI[s['materiale']], mesh=s['mesh'].portato(fr)))
    return out


def apparecchi():
    """MPK mini IV, macro pad con i tasti trasparenti, Flip aperta, hub: forme semplici, misure di misure.py"""
    out = []
    def parte(nome, passo, colore):
        m = Mesh(nome)
        out.append(dict(nome=nome, passo=passo, colore=COLORI[colore], mesh=m))
        return m
    # ---- MPK mini IV ----
    x0, y0, z0 = M.MK4_X0, M.MK4_Y0, M.BASE_T
    W, D = M.MK4['w'], M.MK4['d']
    yk = y0 + M.MK4_KEYBED_Y
    corpo = parte('MPK mini IV', 7, 'mk4')
    corpo.prisma_x([(y0, z0), (y0 + D, z0), (y0 + D, z0 + 20.0), (yk, z0 + 20.0), (yk, z0 + M.MK4['h']), (y0, z0 + M.MK4['h'])],
                   x0, x0 + W)
    bianchi = parte('MPK tasti', 7, 'mk4_tasti')
    neri = parte('MPK tasti neri', 7, 'mk4_neri')
    kw = (W - 12.0) / 15
    for i in range(15):
        a = x0 + 6.0 + i * kw
        bianchi.box(a + 0.4, yk + 2.0, z0 + 20.0, a + kw - 0.4, y0 + D - 3.0, z0 + M.MK4['key_top'])
    for i in (0, 1, 3, 4, 5, 7, 8, 10, 11, 12):
        a = x0 + 6.0 + (i + 1) * kw
        neri.box(a - 4.5, yk + 2.0, z0 + M.MK4['key_top'], a + 4.5, yk + 52.0, z0 + M.MK4['key_top'] + 5.0)
    pads = parte('MPK pad', 7, 'mk4_pad')
    man = parte('MPK manopole', 7, 'manopole')
    zt = z0 + M.MK4['h']
    for nome, (x, y, tipo) in M.MK4_CTRL.items():
        cx, cy = x0 + x, y0 + y
        if tipo == 'p':
            pads.box(cx - 12.5, cy - 12.5, zt, cx + 12.5, cy + 12.5, zt + 2.5)
        elif tipo in ('k', 'e'):
            man.cilindro(cx, cy, zt, z0 + M.MK4['h_knobs'], 9.5 if tipo == 'k' else 9.0, 20)
        elif tipo == 'w':
            man.box(cx - 5.5, cy - 21.0, zt, cx + 5.5, cy + 21.0, zt + 6.0)
        elif tipo == 'd':
            pads.box(cx - 12.0, cy - 6.0, zt, cx + 12.0, cy + 6.0, zt + 0.6)
        else:
            pads.box(cx - 7.5, cy - 4.0, zt, cx + 7.5, cy + 4.0, zt + 1.5)
    # ---- macro pad (foto di Luigi del 18/10/2026): fondo scuro, acrilico trasparente e piastra
    # satinata sul contorno con il lobo; manopole d'alluminio, la grande con la flangia, le piccole sul
    # loro dado; i tasti trasparenti con le etichette ----
    contorno = G.contorno_pad()[0]
    px0, py0 = M.PAD_X0, M.PAD_Y0
    pz1 = M.PAD_Z1
    z = M.PAD_Z0
    for nome, h in M.PAD_STRATI:
        parte(f'Macro pad, {nome}', 5, f'pad_{nome}').prisma(contorno, z, z + h)
        z += h
    allu = parte('Manopole del pad', 5, 'alluminio')
    for k, (kx, ky, kr) in M.PAD_KNOB.items():
        cx, cy = px0 + kx, py0 + ky
        if k == 'M':
            allu.cilindro(cx, cy, pz1, pz1 + 3.0, M.PAD_FLANGIA, 40)
            allu.cilindro(cx, cy, pz1 + 3.0, pz1 + M.PAD_KNOB_H, kr, 40)
        else:
            allu.cilindro(cx, cy, pz1, pz1 + 5.0, kr * 0.62, 6)
            allu.cilindro(cx, cy, pz1 + 5.5, pz1 + M.PAD_KNOB_H, kr, 32)
    tasti = parte('Interruttori del pad', 5, 'pad')
    caps = parte('Tasti trasparenti', 9, 'trasparente')
    C = M.TASTO_PAD
    zc = pz1 + C['z']
    for r in range(3):
        for c in range(5):
            cx = px0 + M.PAD['k0'][0] + c * M.PAD['pitch_x']
            cy = py0 + M.PAD['k0'][1] + r * M.PAD['pitch_y']
            tasti.box(cx - 7.0, cy - 7.0, pz1, cx + 7.0, cy + 7.0, zc)
            caps.prisma(rett(cx - C['w'] / 2, cy - C['d'] / 2, cx + C['w'] / 2, cy + C['d'] / 2, 1.5), zc, zc + C['h'] - 3.0)
            t = C['top_w'] / 2
            caps.prisma(rett(cx - t, cy - t, cx + t, cy + t, 1.0), zc + C['h'] - 3.0, zc + C['h'])
    # ---- Miyoo Flip aperta ----
    fl = parte('Miyoo Flip', 8, 'flip')
    sch = parte('Schermo della Flip', 8, 'schermo')
    fw, fd, t = M.FLIP['w'], M.FLIP['d'], M.FLIP['half']
    fx0 = M.FLIP_X - fw / 2
    fl.prisma(rett(fx0, M.FLIP_Y0, fx0 + fw, M.FLIP_Y0 + fd, 4.0), M.FLIP_Z0, M.FLIP_Z0 + t)
    a = math.radians(M.SCHERMO_DEG)
    O = (fx0, M.FLIP_Y0, M.FLIP_Z0 + t)
    U, V = (1.0, 0.0, 0.0), (0.0, -math.cos(a), math.sin(a))
    N = (0.0, -math.sin(a), -math.cos(a))                     # lo spessore va dietro lo schermo
    fl.prisma(rett(0.0, 0.0, fw, fd, 4.0), 0.0, t, frame=(O, U, V, N))
    sch.prisma(rett(6.0, 8.0, fw - 6.0, fd - 6.0, 1.0), -0.4, 0.0, frame=(O, U, V, N))
    # ---- hub ----
    hb = parte('Hub USB', 4, 'hub')
    hb.box(M.HUB_X0 + 0.4, M.HUB_Y0 + 0.4, z0 + 2.0, M.HUB_X0 + 0.4 + M.HUB['w'], M.HUB_Y0 + 0.4 + M.HUB['d'], z0 + 2.0 + M.HUB['h'])
    return out


def tutte():
    return parti_case() + apparecchi()


# ---------------------------------------------------------------------------------------------
# esportazioni: OBJ e dati per SketchUp (nel riferimento destrorso: y specchiato)

def _tris_destrorsi(mesh):
    return [t for g in mesh.portato(G.SPECCHIO).gusci for t in g]


def scrivi_obj(parti, path):
    mtl = os.path.splitext(path)[0] + '.mtl'
    with open(mtl, 'w', encoding='utf-8', newline='\n') as f:
        for i, p in enumerate(parti):
            r, g, b = (c / 255 for c in p['colore'])
            f.write(f'newmtl m{i}\nKd {r:.3f} {g:.3f} {b:.3f}\nKa 0 0 0\nKs 0.05 0.05 0.05\nNs 10\n\n')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# Stame, la console (bozza 5): millimetri, z in su\n')
        f.write(f'mtllib {os.path.basename(mtl)}\n')
        base = 1
        for i, p in enumerate(parti):
            tris = _tris_destrorsi(p['mesh'])
            f.write(f'o {p["nome"].replace(" ", "_")}\nusemtl m{i}\n')
            idx = {}
            vs, fs = [], []
            for t in tris:
                ids = []
                for v in t:
                    k = (round(v[0], 3), round(v[1], 3), round(v[2], 3))
                    if k not in idx:
                        idx[k] = base + len(vs)
                        vs.append(k)
                    ids.append(idx[k])
                fs.append(ids)
            f.writelines(f'v {x:.3f} {y:.3f} {z:.3f}\n' for x, y, z in vs)
            f.writelines(f'f {a} {b} {c}\n' for a, b, c in fs)
            base += len(vs)


def _riconosci(loop):
    """un contorno come primitiva compatta: cerchio, rettangolo o punti"""
    n = len(loop)
    cx = sum(p[0] for p in loop) / n
    cy = sum(p[1] for p in loop) / n
    rs = [math.hypot(p[0] - cx, p[1] - cy) for p in loop]
    if n >= 8 and max(rs) - min(rs) < 1e-6 * max(rs[0], 1):
        return {'c': [round(cx, 2), round(cy, 2), round(rs[0], 2)]}
    return {'p': [[round(x, 2), round(y, 2)] for x, y in loop]}


def dati_sketchup(parti, path):
    """prismi nel riferimento destrorso, in mm (SketchUp converte in pollici): per ogni prisma il
    riferimento (O, U, V, N) già specchiato, lo spessore e i contorni"""
    out = []
    for p in parti:
        prismi = []
        for q in p['mesh'].portato(G.SPECCHIO).prismi:
            O, U, V, N = q['frame']
            prismi.append({'f': [[round(v, 3) for v in O], [round(v, 4) for v in U], [round(v, 4) for v in V], [round(v, 4) for v in N]],
                           't': [round(q['z0'], 3), round(q['z1'], 3)], 'o': _riconosci(q['outer']),
                           'h': [_riconosci(h) for h in q['holes']]})
        out.append({'n': p['nome'], 's': p['passo'], 'c': list(p['colore']), 'p': prismi})
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, separators=(',', ':'))
    return out


# ---------------------------------------------------------------------------------------------
# tavole del montaggio: rasterizzatore con z-buffer, luce e spigoli

def _norm(v):
    L = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / L for c in v)


def _croce(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def disegna(parti, path, vista=(0.62, -1.0, 0.78), larghezza=1500, altezza=980, evidenzia=None, titolo=None, testo=None):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    S = 2                                                       # sovracampionamento
    Wp, Hp = larghezza * S, altezza * S
    f = _norm(tuple(-c for c in vista))
    r = _norm(_croce(f, (0.0, 0.0, 1.0)))
    u = _croce(r, f)
    tris, cols, ids = [], [], []
    for i, p in enumerate(parti):
        col = AMBRA if evidenzia and p['nome'] in evidenzia else p['colore']
        for t in _tris_destrorsi(p['mesh']):
            tris.append(t)
            cols.append(col)
            ids.append(i + 1)
    T = np.array(tris, dtype=np.float64)                        # (n, 3, 3)
    sx = T @ np.array(r)
    sy = T @ np.array(u)
    sz = T @ np.array(f)
    margine = 0.08
    xmin, xmax, ymin, ymax = sx.min(), sx.max(), sy.min(), sy.max()
    top_riservato = 150 * S if titolo else 0
    scala = min(Wp * (1 - 2 * margine) / (xmax - xmin), (Hp - top_riservato) * (1 - 2 * margine) / (ymax - ymin))
    X = (sx - (xmin + xmax) / 2) * scala + Wp / 2
    Y = Hp - ((sy - (ymin + ymax) / 2) * scala + (Hp - top_riservato) / 2)
    nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    L = np.linalg.norm(nrm, axis=1)
    ok = L > 1e-9
    nrm[ok] /= L[ok, None]
    verso = nrm @ np.array(f)
    nrm[verso > 0] *= -1
    luce = np.array(_norm((0.35, -0.55, 0.85)))
    ombra = 0.50 + 0.50 * np.clip(nrm @ luce, 0, 1)
    zb = np.full((Hp, Wp), np.inf)
    img = np.zeros((Hp, Wp, 3))
    idb = np.zeros((Hp, Wp), dtype=np.int32)
    nb = np.zeros((Hp, Wp, 3))
    cols = np.array(cols, dtype=np.float64)
    for k in range(len(T)):
        if not ok[k]:
            continue
        x0, x1 = int(max(min(X[k]), 0)), int(min(max(X[k]) + 1, Wp - 1))
        y0, y1 = int(max(min(Y[k]), 0)), int(min(max(Y[k]) + 1, Hp - 1))
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        (ax, bx, cx), (ay, by, cy) = X[k], Y[k]
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-12:
            continue
        w0 = ((by - cy) * (gx - cx) + (cx - bx) * (gy - cy)) / den
        w1 = ((cy - ay) * (gx - cx) + (ax - cx) * (gy - cy)) / den
        w2 = 1 - w0 - w1
        dentro = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not dentro.any():
            continue
        z = w0 * sz[k, 0] + w1 * sz[k, 1] + w2 * sz[k, 2]
        blocco = zb[y0:y1 + 1, x0:x1 + 1]
        vince = dentro & (z < blocco - 1e-4)
        blocco[vince] = z[vince]
        img[y0:y1 + 1, x0:x1 + 1][vince] = cols[k] * ombra[k]
        idb[y0:y1 + 1, x0:x1 + 1][vince] = ids[k]
        nb[y0:y1 + 1, x0:x1 + 1][vince] = nrm[k]
    # spigoli: fra parti diverse, sul contorno e dove la normale gira più di 25 gradi
    fondo = idb == 0
    sp = np.zeros((Hp, Wp), dtype=bool)
    for dy, dx in ((0, 1), (1, 0)):
        a_id, b_id = idb[:Hp - dy, :Wp - dx], idb[dy:, dx:]
        a_n, b_n = nb[:Hp - dy, :Wp - dx], nb[dy:, dx:]
        a_z, b_z = zb[:Hp - dy, :Wp - dx], zb[dy:, dx:]
        diversi = a_id != b_id
        piega = ((a_n * b_n).sum(axis=2) < 0.9) & (a_id > 0) & (b_id > 0)
        fin = np.isfinite(a_z) & np.isfinite(b_z)
        salto = np.zeros_like(fin)
        salto[fin] = np.abs(a_z[fin] - b_z[fin]) > 3.0
        e = diversi | piega | salto
        sp[:Hp - dy, :Wp - dx] |= e
    carta = np.array([246, 244, 238], dtype=np.float64)
    img[fondo] = carta
    img[sp] = img[sp] * 0.25 + np.array([30, 30, 32]) * 0.75
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((larghezza, altezza), Image.LANCZOS)
    if titolo:
        d = ImageDraw.Draw(im)
        try:
            ft = ImageFont.truetype('bahnschrift.ttf', 40)
            fs = ImageFont.truetype('bahnschrift.ttf', 22)
        except OSError:
            ft = fs = ImageFont.load_default()
        d.text((40, 28), titolo, fill=(30, 30, 32), font=ft)
        if testo:
            righe, riga = [], ''
            for parola in testo.split():
                prova = (riga + ' ' + parola).strip()
                if d.textlength(prova, font=fs) > larghezza - 80:
                    righe.append(riga)
                    riga = parola
                else:
                    riga = prova
            righe.append(riga)
            for i, rr in enumerate(righe):
                d.text((40, 82 + i * 28), rr, fill=(70, 70, 72), font=fs)
    im.save(path)
    return path


def tavole(parti):
    os.makedirs(MONTAGGIO, exist_ok=True)
    for n in os.listdir(MONTAGGIO):
        if n.endswith('.png'):
            os.remove(os.path.join(MONTAGGIO, n))
    out = []
    for k, (tit, txt) in PASSI.items():
        vis = [p for p in parti if p['passo'] <= k]
        nuovi = {p['nome'] for p in vis if p['passo'] == k}
        out.append(disegna(vis, os.path.join(MONTAGGIO, f'passo_{k}.png'), evidenzia=nuovi,
                           titolo=f'{k}. {tit}', testo=txt))
    finale = parti
    out.append(disegna(finale, os.path.join(MONTAGGIO, 'console.png'), titolo='Stame, la console',
                       testo='MPK mini IV, macro pad e Miyoo Flip nel telaio di betulla, sotto un piano solo (bozza 5).'))
    out.append(disegna(finale, os.path.join(MONTAGGIO, 'console_retro.png'), vista=(-0.7, 0.9, 0.7)))
    return out


def main():
    parti = tutte()
    scrivi_obj(parti, os.path.join(OUT, 'stame_console.obj'))
    dati = dati_sketchup(parti, os.path.join(OUT, 'stame_sketchup.json'))
    n = sum(len(p['p']) for p in dati)
    print(f'MODELLO: {len(parti)} parti, {n} prismi -> stame_console.obj, stame_sketchup.json')
    for p in tavole(parti):
        print('  ' + os.path.relpath(p, OUT))


if __name__ == '__main__':
    main()
