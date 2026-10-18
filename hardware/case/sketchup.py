"""sketchup.py — prepara il modello SketchUp della console dai dati di assieme.py.

Uso: python -I hardware/case/sketchup.py           scrive out/sketchup/parte_N.py

Il modello si costruisce con lo strumento SketchUp (build_model, nel cloud, in Python): ogni file
parte_N.py è il codice di una chiamata. parte_0.py definisce materiali, livelli (uno per passo del
montaggio) e la funzione che costruisce un pezzo; le altre aggiungono i pezzi; scene.py (dal modello SCENE) fa una
scena per passo. I prismi arrivano già nel riferimento destrorso (y specchiato), in millimetri.
"""
import json
import math
import os

QUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(QUI, 'out')
CART = os.path.join(OUT, 'sketchup')


def _num(v, d):
    s = f'{v:.{d}f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def _rr(loop):
    """rettangolo arrotondato di mesh.rett (4 archi da 7 punti, dal centro in alto a destra)?"""
    if len(loop) == 4:
        xs, ys = sorted({round(p[0], 3) for p in loop}), sorted({round(p[1], 3) for p in loop})
        if len(xs) == 2 and len(ys) == 2:
            return [xs[0], ys[0], xs[1], ys[1], 0.0]
        return None
    if len(loop) != 28:
        return None
    x0, x1 = min(p[0] for p in loop), max(p[0] for p in loop)
    y0, y1 = min(p[1] for p in loop), max(p[1] for p in loop)
    r = x1 - loop[0][0]
    if r <= 0:
        return None
    for k, (cx, cy) in enumerate(((x1 - r, y0 + r), (x1 - r, y1 - r), (x0 + r, y1 - r), (x0 + r, y0 + r))):
        for p in loop[k * 7:(k + 1) * 7]:
            if abs(math.hypot(p[0] - cx, p[1] - cy) - r) > 0.02:
                return None
    return [x0, y0, x1, y1, r]


def compatta(sh):
    if 'c' in sh:
        return 'c', [_num(v, 2) for v in sh['c']]
    rr = _rr(sh['p'])
    if rr:
        return 'r', [_num(v, 2) for v in rr]
    return 'p', [_num(v, 2) for xy in sh['p'] for v in xy]


def codice_dati(parti):
    righe = []
    for p in parti:
        prismi = []
        for q in p['p']:
            f = ','.join(_num(v, 4) for vec in q['f'] for v in vec)
            o = compatta(q['o'])
            hs = ';'.join(f'{k}{",".join(v)}' for k, v in (compatta(h) for h in q['h']))
            prismi.append(f'{f}|{_num(q["t"][0], 3)},{_num(q["t"][1], 3)}|{o[0]}{",".join(o[1])}|{hs}')
        righe.append(f'{p["n"]}#{p["s"]}#{p["c"][0]},{p["c"][1]},{p["c"][2]}#' + '/'.join(prismi))
    return righe


PARTE_0 = r'''
# Stame, la console (bozza 5): materiali, livelli dei passi, costruttore dei pezzi
def get_or_create_material(name, r, g, b, a=255):
    existing = {m.get_name(): m for m in model.get_materials()}
    if name in existing:
        return existing[name]
    mat = Material()
    mat.set_name(name)
    mat.set_color(SUColor(r, g, b, a))
    model.add_materials([mat])
    return mat

PASSI = __PASSI__
layers = {}
for k, nome in PASSI:
    ly = Layer()
    ly.set_name(nome)
    layers[k] = ly
model.add_layers(list(layers.values()))
console = Group()
model.get_entities().add_group(console)
console.set_name('Stame console')
session_state['layers'] = layers
session_state['console'] = console

def anello(kind, vals):
    v = [float(x) for x in vals.split(',')]
    if kind == 'c':
        cx, cy, r = v
        n = 24 if r > 3 else 12
        return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    if kind == 'r':
        x0, y0, x1, y1, r = v
        if r <= 0:
            return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        pts = []
        for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
            for k in range(7):
                a = math.radians(a0 + 90 * k / 6)
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return pts
    return [(v[i], v[i + 1]) for i in range(0, len(v), 2)]

def area(l):
    return sum(l[i][0] * l[(i + 1) % len(l)][1] - l[(i + 1) % len(l)][0] * l[i][1] for i in range(len(l))) / 2

def prisma(ents, spec):
    f, t, o, hs = spec.split('|')
    fv = [float(x) for x in f.split(',')]
    O, U, V, N = fv[0:3], fv[3:6], fv[6:9], fv[9:12]
    t0, t1 = [float(x) for x in t.split(',')]
    outer = anello(o[0], o[1:])
    if area(outer) < 0:
        outer = outer[::-1]
    holes = []
    for h in (hs.split(';') if hs else []):
        l = anello(h[0], h[1:])
        if area(l) > 0:
            l = l[::-1]
        holes.append(l)
    def W(u, v, tt):
        return SUPoint3D((O[0] + u * U[0] + v * V[0] + tt * N[0]) / 25.4,
                         (O[1] + u * U[1] + v * V[1] + tt * N[1]) / 25.4,
                         (O[2] + u * U[2] + v * V[2] + tt * N[2]) / 25.4)
    verts = []
    rings = []
    for l in [outer] + holes:
        b = len(verts)
        verts += [W(x, y, t0) for x, y in l]
        tp = len(verts)
        verts += [W(x, y, t1) for x, y in l]
        rings.append((list(range(b, b + len(l))), list(range(tp, tp + len(l)))))
    gi = GeometryInput()
    gi.set_vertices(verts)
    for lato in (0, 1):
        lp = LoopInput()
        for i in rings[0][lato]:
            lp.add_vertex_index(i)
        fi, gi = gi.add_face(lp)
        for r in rings[1:]:
            il = LoopInput()
            for i in r[lato]:
                il.add_vertex_index(i)
            gi = gi.face_add_inner_loop(fi, il)
    for b, tp in rings:
        n = len(b)
        for i in range(n):
            j = (i + 1) % n
            lp = LoopInput()
            for x in (b[i], b[j], tp[j], tp[i]):
                lp.add_vertex_index(x)
            _, gi = gi.add_face(lp)
    ents.fill(gi, weld_vertices=True)

def pezzo(riga):
    nome, passo, col, prismi = riga.split('#')
    r, g, b = [int(x) for x in col.split(',')]
    mat = get_or_create_material(f'stame_{r}_{g}_{b}', r, g, b)
    grp = Group()
    session_state['console'].get_entities().add_group(grp)
    grp.set_name(nome)
    for spec in prismi.split('/'):
        try:
            prisma(grp.get_entities(), spec)
        except Exception as e:
            session_state.setdefault('errori', []).append(nome + ': ' + str(e))
    for face in grp.get_entities().get_faces():
        face.set_front_material(mat)
        face.set_back_material(mat)
    for edge in grp.get_entities().get_edges():
        fs = edge.get_faces()
        if len(fs) == 2:
            n0, n1 = fs[0].get_normal(), fs[1].get_normal()
            if abs(n0.x * n1.x + n0.y * n1.y + n0.z * n1.z) > 0.9999:
                edge.set_soft(True)
                edge.set_smooth(True)
    grp.set_layer(session_state['layers'][int(passo)])
    return nome

session_state['pezzo'] = pezzo
result = {'layers': len(layers)}
'''

PARTE_N = r'''
pezzo = session_state['pezzo']
DATI = __DATI__
fatti = [pezzo(r) for r in DATI]
result = {'pezzi': fatti, 'errori': session_state.get('errori', [])}
'''


# ultima chiamata: stile, telecamera e una scena per passo (ingombro in pollici)
SCENE = '''ro = model.get_rendering_options()
def set_ro(name, value):
    try:
        ro[RenderingOptionKey[name]] = value
    except Exception:
        pass
set_ro("BACKGROUND_COLOR", TypedValue(color_value=SUColor(246, 244, 238, 255)))
set_ro("DRAW_SILHOUETTES", TypedValue(bool_value=True))
set_ro("SILHOUETTE_WIDTH", TypedValue(int_value=2))
set_ro("DRAW_DEPTH_QUE", TypedValue(bool_value=False))
set_ro("DRAW_GROUND", TypedValue(bool_value=False))
set_ro("HIGHLIGHT_COLOR", TypedValue(color_value=SUColor(0, 1, 255, 255)))
set_ro("LOCKED_COLOR", TypedValue(color_value=SUColor(255, 0, 0, 255)))

xmin, ymin, zmin = 0.0, __YMIN__, 0.0
xmax, ymax, zmax = __XMAX__, 0.0, __ZMAX__
cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
w, d, h = xmax - xmin, ymax - ymin, zmax - zmin

def camera(az, el, fov=30.0, margin=1.15):
    dx = math.cos(math.radians(el)) * math.sin(math.radians(az))
    dy = -math.cos(math.radians(el)) * math.cos(math.radians(az))
    dz = math.sin(math.radians(el))
    rl = math.sqrt(dx * dx + dy * dy)
    rx, ry = -dy / rl, dx / rl
    ux, uy, uz = -dz * ry, dz * rx, dx * ry - dy * rx
    he = abs(rx) * w + abs(ry) * d
    ve = abs(ux) * w + abs(uy) * d + abs(uz) * h
    hv = math.radians(fov / 2)
    hh = math.atan(1.6 * math.tan(hv))
    dist = max((ve / 2) / math.tan(hv), (he / 2) / math.tan(hh)) * margin
    cz = zmin + h * 0.35
    cam = Camera()
    cam.set_orientation(SUPoint3D(cx + dist * dx, cy + dist * dy, cz + dist * dz), SUPoint3D(cx, cy, cz), SUVector3D(0, 0, 1))
    cam.enable_perspective()
    cam.set_perspective_frustum_fov(fov)
    return cam

layers = session_state['layers']
nomi = __NOMI__
scenes = []
for nome in nomi + ['Console']:
    sc = Scene()
    sc.set_name(nome)
    scenes.append(sc)
model.add_scenes(scenes)
for i, sc in enumerate(scenes):
    k = i + 1 if i < 9 else 9
    sc.set_use_camera(True)
    sc.set_camera(camera(32, 34))
    sc.set_use_hidden_layers(True)
    for j in range(k + 1, 10):
        sc.add_layer(layers[j])
model.set_active_scene(scenes[-1])
model.set_camera(camera(32, 34))
check = model.get_camera()
o = check.get_orientation()
result = {'scene': [s.get_name() for s in scenes], 'eye': [round(o[0].x, 1), round(o[0].y, 1), round(o[0].z, 1)],
          'persp': check.is_perspective(), 'fov': check.get_perspective_frustum_fov()}
'''


def main():
    import sys
    sys.path.insert(0, QUI)
    import assieme as A
    parti = json.load(open(os.path.join(OUT, 'stame_sketchup.json'), encoding='utf-8'))
    righe = codice_dati(parti)
    os.makedirs(CART, exist_ok=True)
    for n in os.listdir(CART):
        os.remove(os.path.join(CART, n))
    passi = [(k, f'{k} {t}') for k, (t, _) in A.PASSI.items()]
    with open(os.path.join(CART, 'parte_0.py'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(PARTE_0.replace('__PASSI__', repr(passi)))
    gruppi, cur, size = [], [], 0
    for r in righe:
        if size + len(r) > 14000 and cur:
            gruppi.append(cur)
            cur, size = [], 0
        cur.append(r)
        size += len(r)
    gruppi.append(cur)
    for i, g in enumerate(gruppi, 1):
        with open(os.path.join(CART, f'parte_{i}.py'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(PARTE_N.replace('__DATI__', repr(g)))
    import misure as M
    nomi = [f'{k} {t}' for k, (t, _) in A.PASSI.items()]
    with open(os.path.join(CART, 'scene.py'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(SCENE.replace('__YMIN__', f'{-M.BASE_Y1 / 25.4:.2f}').replace('__XMAX__', f'{M.LARGHEZZA / 25.4:.2f}')
                .replace('__ZMAX__', '5.89').replace('__NOMI__', repr(nomi)))
    tot = sum(len(r) for r in righe)
    print(f'{len(righe)} pezzi, {tot} caratteri di dati in {len(gruppi)} chiamate')
    for i, g in enumerate(gruppi, 1):
        print(f'  parte_{i}.py: {sum(len(r) for r in g)} caratteri, {len(g)} pezzi')


if __name__ == '__main__':
    main()
