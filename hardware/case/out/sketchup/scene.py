ro = model.get_rendering_options()
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

xmin, ymin, zmin = 0.0, -9.61, 0.0
xmax, ymax, zmax = 22.97, 0.0, 5.89
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
nomi = ['1 La base', '2 Retro, costola e parete davanti', '3 I fianchi', "4 L'hub e i cavi", '5 La culla del pad', '6 Il piano della Flip', '7 MK4 e mascherina', '8 La Flip e i cavi', '9 Le etichette']
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
