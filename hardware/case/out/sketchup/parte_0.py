
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

PASSI = [(1, '1 La base'), (2, '2 Retro, costola e parete davanti'), (3, '3 I fianchi'), (4, "4 L'hub e i cavi"), (5, '5 La culla del pad'), (6, '6 Il piano della Flip'), (7, '7 MK4 e mascherina'), (8, '8 La Flip e i cavi'), (9, '9 Le etichette')]
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
