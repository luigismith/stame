"""blender_scena.py — la scena del rendering, dentro Blender (lo lancia rendering.py).

blender -b --factory-startup -P blender_scena.py -- build/render/scena.json

Importa stame_console.obj (mm, y già specchiata), dà a ogni pezzo il suo materiale (betulla con i
bordi bruciati dal laser e le incisioni, acrilico nero lucido con le incisioni satinate, PETG
satinato con gli strati, alluminio delle manopole del pad, tasti trasparenti con l'etichetta
dentro, Flip bianca con la sua faccia vera, schermo acceso), arrotonda gli spigoli, mette luce da
studio e tre inquadrature. Cycles su GPU (OptiX) se c'è.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

S = json.load(open(sys.argv[sys.argv.index('--') + 1], encoding='utf-8'))
MM = 0.001
PROVA = S['prova']
TEX = S['tex']


# ---------------------------------------------------------------------------------------------
# scena e import

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
bpy.ops.wm.obj_import(filepath=S['obj'], global_scale=MM, forward_axis='Y', up_axis='Z')
pezzi = {ob.name: ob for ob in scene.objects if ob.type == 'MESH'}
# l'import mette la scala sull'oggetto: la si applica, così i vertici sono in metri
for ob in pezzi.values():
    ob.select_set(True)
bpy.context.view_layer.objects.active = next(iter(pezzi.values()))
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


def attiva(ob):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def separa(ob):
    """divide un oggetto nelle sue parti sciolte"""
    attiva(ob)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE')
    bpy.ops.object.mode_set(mode='OBJECT')
    return [o for o in bpy.context.selected_objects]


def uv_riferimento(ob, frame, W, H, nome='uv'):
    """coordinate di texture dal riferimento (O, U, V) di un pezzo del laser: u lungo U, v lungo V"""
    O, U, V = (Vector(frame[0]), Vector(frame[1]), Vector(frame[2]))
    me = ob.data
    uv = me.uv_layers.new(name=nome)
    me.uv_layers.active = uv
    for li, lp in enumerate(me.loops):
        co = me.vertices[lp.vertex_index].co / MM - O
        uv.data[li].uv = (co.dot(U) / W, 1.0 - co.dot(V) / H)
    us = [d.uv[0] for d in uv.data]
    vs = [d.uv[1] for d in uv.data]
    print(f'uv {ob.name}: u {min(us):.3f}..{max(us):.3f} v {min(vs):.3f}..{max(vs):.3f}')
    return uv


# ---------------------------------------------------------------------------------------------
# materiali

def nuovo(nome):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    return m, nt, nt.nodes['Principled BSDF']


def nodo(nt, tipo, **kw):
    n = nt.nodes.new(tipo)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def lega(nt, a, b):
    nt.links.new(a, b)


def immagine(nt, path, uv='uv', colore=True):
    t = nodo(nt, 'ShaderNodeTexImage')
    t.image = bpy.data.images.load(path)
    if not colore:
        t.image.colorspace_settings.name = 'Non-Color'
    u = nodo(nt, 'ShaderNodeUVMap', uv_map=uv)
    lega(nt, u.outputs['UV'], t.inputs['Vector'])
    return t


def mix(nt, fac, a, b):
    n = nodo(nt, 'ShaderNodeMix', data_type='RGBA')
    lega(nt, fac, n.inputs['Factor'])
    for i, x in ((6, a), (7, b)):
        if isinstance(x, (tuple, list)):
            n.inputs[i].default_value = (*x, 1.0) if len(x) == 3 else x
        else:
            lega(nt, x, n.inputs[i])
    return n.outputs[2]


def mixf(nt, fac, a, b):
    n = nodo(nt, 'ShaderNodeMix', data_type='FLOAT')
    lega(nt, fac, n.inputs['Factor'])
    for i, x in ((2, a), (3, b)):
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            lega(nt, x, n.inputs[i])
    return n.outputs[0]


def bordo_laser(nt, asse):
    """1 sulle facce tagliate (normale perpendicolare allo spessore), 0 sulle facce grandi"""
    tc = nodo(nt, 'ShaderNodeTexCoord')
    d = nodo(nt, 'ShaderNodeVectorMath', operation='DOT_PRODUCT')
    lega(nt, tc.outputs['Normal'], d.inputs[0])
    d.inputs[1].default_value = asse
    a = nodo(nt, 'ShaderNodeMath', operation='ABSOLUTE')
    lega(nt, d.outputs['Value'], a.inputs[0])
    c = nodo(nt, 'ShaderNodeMath', operation='LESS_THAN')
    lega(nt, a.outputs[0], c.inputs[0])
    c.inputs[1].default_value = 0.5
    return c.outputs[0]


def betulla(ob, incisa=None):
    m, nt, b = nuovo('betulla ' + ob.name)
    dim = ob.dimensions
    assi = sorted(range(3), key=lambda i: dim[i])
    sottile, lungo = assi[0], assi[2]
    tc = nodo(nt, 'ShaderNodeTexCoord')
    mp = nodo(nt, 'ShaderNodeMapping')
    sc = [90.0, 90.0, 90.0]
    sc[lungo] = 4.0
    mp.inputs['Scale'].default_value = sc
    lega(nt, tc.outputs['Object'], mp.inputs['Vector'])
    vena = nodo(nt, 'ShaderNodeTexNoise')
    vena.inputs['Scale'].default_value = 6.0
    vena.inputs['Detail'].default_value = 8.0
    vena.inputs['Roughness'].default_value = 0.62
    lega(nt, mp.outputs['Vector'], vena.inputs['Vector'])
    rampa = nodo(nt, 'ShaderNodeValToRGB')
    rampa.color_ramp.elements[0].position = 0.38
    rampa.color_ramp.elements[0].color = (0.56, 0.38, 0.21, 1)
    rampa.color_ramp.elements[1].position = 0.66
    rampa.color_ramp.elements[1].color = (0.70, 0.52, 0.32, 1)
    lega(nt, vena.outputs['Fac'], rampa.inputs['Fac'])
    asse = [0.0, 0.0, 0.0]
    asse[sottile] = 1.0
    bordo = bordo_laser(nt, asse)
    col = mix(nt, bordo, rampa.outputs['Color'], (0.075, 0.042, 0.022))
    rough = mixf(nt, bordo, 0.62, 0.85)
    if incisa:
        t = immagine(nt, incisa, colore=False)
        col = mix(nt, t.outputs['Color'], col, (0.11, 0.055, 0.028))
        bump = nodo(nt, 'ShaderNodeBump', invert=True)
        bump.inputs['Distance'].default_value = 0.0002
        lega(nt, t.outputs['Color'], bump.inputs['Height'])
        lega(nt, bump.outputs['Normal'], b.inputs['Normal'])
    lega(nt, col, b.inputs['Base Color'])
    lega(nt, rough, b.inputs['Roughness'])
    b.inputs['Coat Weight'].default_value = 0.08
    return m


def acrilico(nome, incisa=None):
    m, nt, b = nuovo(nome)
    b.inputs['IOR'].default_value = 1.49
    col, rough = (0.006, 0.006, 0.007), 0.04
    if incisa:
        t = immagine(nt, incisa, colore=False)
        col = mix(nt, t.outputs['Color'], col, (0.30, 0.30, 0.29))
        rough = mixf(nt, t.outputs['Color'], 0.04, 0.6)
        bump = nodo(nt, 'ShaderNodeBump', invert=True)
        bump.inputs['Distance'].default_value = 0.00015
        lega(nt, t.outputs['Color'], bump.inputs['Height'])
        lega(nt, bump.outputs['Normal'], b.inputs['Normal'])
        lega(nt, col, b.inputs['Base Color'])
        lega(nt, rough, b.inputs['Roughness'])
    else:
        b.inputs['Base Color'].default_value = (*col, 1)
        b.inputs['Roughness'].default_value = rough
    return m


def plastica(nome, col, rough, strati=False, coat=0.0):
    m, nt, b = nuovo(nome)
    b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = coat
    if strati:                       # strati della stampa: 0,2 mm lungo z
        tc = nodo(nt, 'ShaderNodeTexCoord')
        sx = nodo(nt, 'ShaderNodeSeparateXYZ')
        lega(nt, tc.outputs['Object'], sx.inputs['Vector'])
        k = nodo(nt, 'ShaderNodeMath', operation='MULTIPLY')
        lega(nt, sx.outputs['Z'], k.inputs[0])
        k.inputs[1].default_value = 2 * math.pi / 0.0002
        s = nodo(nt, 'ShaderNodeMath', operation='SINE')
        lega(nt, k.outputs[0], s.inputs[0])
        bump = nodo(nt, 'ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.25
        bump.inputs['Distance'].default_value = 0.00003
        lega(nt, s.outputs[0], bump.inputs['Height'])
        lega(nt, bump.outputs['Normal'], b.inputs['Normal'])
    return m


def metallo(nome, col, rough, aniso=0.0):
    m, nt, b = nuovo(nome)
    b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Metallic'].default_value = 1.0
    b.inputs['Roughness'].default_value = rough
    b.inputs['Anisotropic'].default_value = aniso
    return m


def emissivo(nome, col, forza, rough=0.6, base=(0.02, 0.02, 0.02)):
    m, nt, b = nuovo(nome)
    b.inputs['Base Color'].default_value = (*base, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Emission Color'].default_value = (*col, 1)
    b.inputs['Emission Strength'].default_value = forza
    return m


def trasparente(nome):
    """tasto trasparente: vetro per la camera, trasparente per le ombre (così l'etichetta è in luce)"""
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    out = nt.nodes['Material Output']
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (1, 1, 1, 1)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.04
    b.inputs['IOR'].default_value = 1.49
    lp = nodo(nt, 'ShaderNodeLightPath')
    tr = nodo(nt, 'ShaderNodeBsdfTransparent')
    mx = nodo(nt, 'ShaderNodeMixShader')
    lega(nt, lp.outputs['Is Shadow Ray'], mx.inputs['Fac'])
    lega(nt, b.outputs['BSDF'], mx.inputs[1])
    lega(nt, tr.outputs['BSDF'], mx.inputs[2])
    lega(nt, mx.outputs['Shader'], out.inputs['Surface'])
    return m


def dai(ob, m):
    ob.data.materials.clear()
    ob.data.materials.append(m)


# ---------------------------------------------------------------------------------------------
# pezzi

inc = S['incisioni']
for nome, ob in list(pezzi.items()):
    if nome.startswith(('fianco', 'base_', 'retro_', 'divisorio', 'torre_')):
        tex = None
        if nome in inc:
            W, H = inc[nome]['dim']
            uv_riferimento(ob, inc[nome]['frame'], W, H)
            tex = os.path.join(TEX, nome + '_inc.png')
        dai(ob, betulla(ob, tex))
    elif nome in ('mascherina', 'cartellino_pad'):
        W, H = inc[nome]['dim']
        uv_riferimento(ob, inc[nome]['frame'], W, H)
        dai(ob, acrilico('acrilico ' + nome, os.path.join(TEX, nome + '_inc.png')))

petg = plastica('PETG nero', (0.012, 0.012, 0.013), 0.32, strati=True)
tpu = plastica('TPU nero', (0.01, 0.01, 0.01), 0.75)
for nome, ob in pezzi.items():
    if nome.startswith(('culla_flip', 'visiera', 'cornice_pad', 'fermo_hub', 'squadretta')):
        dai(ob, petg)
    elif nome.startswith('piedino'):
        dai(ob, tpu)

dai(pezzi['MPK_mini_IV'], plastica('MK4', (0.60, 0.60, 0.58), 0.42))
dai(pezzi['MPK_tasti'], plastica('tasti bianchi', (0.80, 0.80, 0.78), 0.3, coat=0.3))
dai(pezzi['MPK_tasti_neri'], plastica('tasti neri', (0.012, 0.012, 0.012), 0.28, coat=0.3))
gomma = plastica('gomma dei pulsanti', (0.02, 0.02, 0.022), 0.6)
pad_acqua = emissivo('pad accordi', (0.25, 0.95, 0.80), 2.5, 0.7, (0.12, 0.13, 0.13))
pad_bianco = emissivo('pad estensioni', (0.85, 0.92, 0.95), 1.6, 0.7, (0.12, 0.13, 0.13))
display = emissivo('display della MK4', (0.55, 0.75, 1.0), 2.0, 0.1)
for o in separa(pezzi['MPK_pad']):
    dx, dy = o.dimensions.x / MM, o.dimensions.y / MM
    if dx > 22 and dy > 22:
        cy = sum((o.matrix_world @ v.co).y for v in o.data.vertices) / len(o.data.vertices) / MM
        dai(o, pad_acqua if cy > -76 else pad_bianco)
    elif dx > 20 and dy < 14:
        dai(o, display)
    else:
        dai(o, gomma)
dai(pezzi['MPK_manopole'], plastica('manopole MK4', (0.10, 0.10, 0.105), 0.5))
alluminio = metallo('alluminio', (0.86, 0.87, 0.89), 0.2, 0.7)
fumé = plastica('acrilico fumé del pad', (0.015, 0.016, 0.018), 0.05, coat=0.5)
for o in separa(pezzi['Macro_pad']):
    dai(o, fumé if o.dimensions.x / MM > 100 else alluminio)
dai(pezzi['Interruttori_del_pad'], plastica('interruttori', (0.03, 0.03, 0.035), 0.4))
dai(pezzi['Tasti_trasparenti'], trasparente('tasti trasparenti'))
dai(pezzi['Hub_USB'], plastica('hub', (0.02, 0.02, 0.022), 0.4))

# la Flip bianca, con la faccia dei tasti dalla foto sulla metà di sotto
flip = pezzi['Miyoo_Flip']
(x0, yc), (fw, fd) = S['flip_faccia']
me = flip.data
uv = me.uv_layers.new(name='uv')
for li, lp in enumerate(me.loops):
    co = me.vertices[lp.vertex_index].co / MM
    uv.data[li].uv = ((co.x - x0) / fw, 1.0 - (yc - co.y) / fd)
m, nt, b = nuovo('Flip')
t = immagine(nt, os.path.join(TEX, 'flip_faccia.png'))
gn = nodo(nt, 'ShaderNodeNewGeometry')
sz = nodo(nt, 'ShaderNodeSeparateXYZ')
lega(nt, gn.outputs['Normal'], sz.inputs['Vector'])
su = nodo(nt, 'ShaderNodeMath', operation='GREATER_THAN')
lega(nt, sz.outputs['Z'], su.inputs[0])
su.inputs[1].default_value = 0.95
lega(nt, mix(nt, su.outputs[0], (0.72, 0.72, 0.70), t.outputs['Color']), b.inputs['Base Color'])
b.inputs['Roughness'].default_value = 0.35
dai(flip, m)

sch = pezzi['Schermo_della_Flip']
f = S['schermo']
O, U, V = Vector(f[0]), Vector(f[1]), Vector(f[2])
me = sch.data
uv = me.uv_layers.new(name='uv')
for li, lp in enumerate(me.loops):
    co = me.vertices[lp.vertex_index].co / MM - O
    uv.data[li].uv = ((co.dot(U) - 6.0) / 72.0, (co.dot(V) - 8.0) / 66.35)
m, nt, b = nuovo('schermo')
t = immagine(nt, os.path.join(TEX, 'schermo.png'))
b.inputs['Base Color'].default_value = (0.0, 0.0, 0.0, 1)
b.inputs['Roughness'].default_value = 0.04
lega(nt, t.outputs['Color'], b.inputs['Emission Color'])
b.inputs['Emission Strength'].default_value = 1.6
dai(sch, m)

# etichette di carta dentro i tasti trasparenti
ew, eh = (v - 0.2 for v in S['etichetta'])
z = (S['tasto_top'] - 1.4) * MM
for k, (x, y) in enumerate(S['tasti']):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x * MM, y * MM, z))
    p = bpy.context.active_object
    p.name = f'etichetta {k + 1}'
    p.scale = (ew * MM, eh * MM, 1)
    m, nt, b = nuovo(p.name)
    t = immagine(nt, os.path.join(TEX, f'etichetta_{k:02d}.png'), uv='UVMap')
    lega(nt, t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.8
    dai(p, m)

# spigoli arrotondati e ombreggiatura morbida
for ob in [o for o in scene.objects if o.type == 'MESH' and not o.name.startswith(('etichetta', 'Schermo'))]:
    bv = ob.modifiers.new('spigoli', 'BEVEL')
    bv.width = 0.00035
    bv.segments = 2
    bv.limit_method = 'ANGLE'
    bv.angle_limit = math.radians(40)
    bv.harden_normals = True
    try:
        attiva(ob)
        bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
    except Exception:
        pass

# ---------------------------------------------------------------------------------------------
# studio: piano, luce, mondo

bpy.ops.mesh.primitive_plane_add(size=8, location=(0.3, -0.1, 0))
piano = bpy.context.active_object
dai(piano, plastica('piano', (0.30, 0.285, 0.265), 0.55))
FONDO = (0.33, 0.315, 0.295)

w = bpy.data.worlds.new('studio')
scene.world = w
w.use_nodes = True
nt = w.node_tree
bg = nt.nodes['Background']
env = nodo(nt, 'ShaderNodeTexEnvironment')
env.image = bpy.data.images.load(S['hdr'])
mp = nodo(nt, 'ShaderNodeMapping')
mp.inputs['Rotation'].default_value = (0, 0, math.radians(120))
tc = nodo(nt, 'ShaderNodeTexCoord')
lega(nt, tc.outputs['Generated'], mp.inputs['Vector'])
lega(nt, mp.outputs['Vector'], env.inputs['Vector'])
lega(nt, env.outputs['Color'], bg.inputs['Color'])
bg.inputs['Strength'].default_value = 0.18
cam_bg = nodo(nt, 'ShaderNodeBackground')
cam_bg.inputs['Color'].default_value = (*FONDO, 1)
lp = nodo(nt, 'ShaderNodeLightPath')
mx = nodo(nt, 'ShaderNodeMixShader')
lega(nt, lp.outputs['Is Camera Ray'], mx.inputs['Fac'])
lega(nt, bg.outputs['Background'], mx.inputs[1])
lega(nt, cam_bg.outputs['Background'], mx.inputs[2])
lega(nt, mx.outputs['Shader'], nt.nodes['World Output'].inputs['Surface'])

CENTRO = Vector((S['ingombro'][0] / 2 * MM, -S['ingombro'][1] / 2 * MM, 0.04))


def luce(nome, pos, forza, misura, colore=(1, 1, 1)):
    d = bpy.data.lights.new(nome, 'AREA')
    d.energy = forza
    d.size = misura
    d.color = colore
    o = bpy.data.objects.new(nome, d)
    scene.collection.objects.link(o)
    o.location = pos
    o.rotation_euler = (CENTRO - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
    return o


luce('chiave', (-0.35, -0.95, 1.05), 55, 1.1, (1.0, 0.96, 0.9))
luce('riempimento', (1.5, -0.55, 0.55), 14, 1.6, (0.9, 0.95, 1.0))
luce('contro', (0.55, 1.1, 0.75), 40, 0.9)

# ---------------------------------------------------------------------------------------------
# camere e rendering

scene.render.engine = 'CYCLES'
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for tipo in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = tipo
            prefs.get_devices()
            usati = [d for d in prefs.devices if d.type == tipo]
            if usati:
                for d in prefs.devices:
                    d.use = d.type == tipo
                scene.cycles.device = 'GPU'
                print('Cycles su', tipo, [d.name for d in usati])
                break
        except TypeError:
            continue
except Exception as e:
    print('GPU non disponibile:', e)
scene.cycles.samples = 48 if PROVA else 640
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 16
scene.cycles.transmission_bounces = 16
scene.render.resolution_x, scene.render.resolution_y = (1200, 675) if PROVA else (2400, 1350)
scene.render.film_transparent = False
try:
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass


def camera(nome, bersaglio, az, el, dist, lente, fuoco=None, f_stop=5.6):
    bersaglio = Vector(bersaglio)
    a, e = math.radians(az), math.radians(el)
    pos = bersaglio + dist * Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    d = bpy.data.cameras.new(nome)
    d.lens = lente
    d.sensor_width = 36
    if fuoco is not None:
        d.dof.use_dof = True
        d.dof.focus_distance = (Vector(fuoco) - pos).length
        d.dof.aperture_fstop = f_stop
    o = bpy.data.objects.new(nome, d)
    scene.collection.objects.link(o)
    o.location = pos
    o.rotation_euler = (bersaglio - pos).to_track_quat('-Z', 'Y').to_euler()
    return o


tasto = S['tasti'][7]
VISTE = [
    ('eroe', (CENTRO.x + 0.01, CENTRO.y + 0.01, 0.045), 24, 27, 1.32, 60, (CENTRO.x, CENTRO.y, 0.05), 8.0),
    ('torre', (0.47, -0.135, 0.06), 32, 30, 0.62, 85, (tasto[0] * MM, tasto[1] * MM, 0.037), 4.0),
    ('mascherina', (0.20, -0.095, 0.045), -12, 50, 0.62, 70, (0.20, -0.09, 0.05), 6.3),
]
for nome, bers, az, el, dist, lente, fuoco, fs in VISTE:
    cam = camera(nome, bers, az, el, dist, lente, fuoco, fs)
    scene.camera = cam
    scene.render.filepath = os.path.join(S['uscita'], f'render_{nome}.png')
    bpy.ops.render.render(write_still=True)
    print('scritto', scene.render.filepath)
