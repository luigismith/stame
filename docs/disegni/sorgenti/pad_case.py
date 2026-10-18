# Disegni del macro pad BRIMFORD, delle griglie gemelle, del gesto Tn + Kn e del case.
# Misure in mm. MPK mini Plus dalla guida §14.15.2; Flip 84 x 80,35 x 24,5 mm; pad stimato [V].
import math
from controlli import C, rect, text, esc

C.setdefault('warn', ('#B71C1C', '#FFE0E0'))

PAD_W, PAD_D = 115, 100          # ingombro stimato del pad [V]
PAD_KEYS = [  # (n, nome, tipo)
    (1, 'Sound', 'fun'), (2, 'Perform', 'fun'), (3, 'FX', 'fun'), (4, 'Key', 'fun'),
    (5, 'Bass', 'fun'), (6, 'Loop', 'loop'), (7, 'BPM', 'fun'), (8, 'Volume', 'fun'),
    (9, 'Options', 'nav'), (10, 'Back', 'nav'), (11, 'Menu', 'perf'), (12, 'Panic\n1 s', 'warn'),
]

def knob(x, y, r, label, kind, sub=None, size=3.2):
    s, f = C[kind]
    o = [f'<circle cx="{x}" cy="{y}" r="{r}" fill="{f}" stroke="{s}" stroke-width="0.8"/>',
         f'<circle cx="{x}" cy="{y - r + 2.2}" r="0.9" fill="{s}"/>',
         text(x, y, label, size, weight='700')]
    if sub:
        o.append(text(x, y + r + 3.4, sub, 2.5, color='#333'))
    return ''.join(o)

def pad_svg(width='100%', labels=True):
    o = [f'<svg viewBox="-6 -6 {PAD_W + 12} {PAD_D + 14}" width="{width}" xmlns="http://www.w3.org/2000/svg" font-family="Inter, Helvetica, Arial, sans-serif">']
    o.append(f'<rect x="0" y="0" width="{PAD_W}" height="{PAD_D}" rx="6" fill="#2b2b2b"/>')
    o.append(knob(24, 18, 12.5, 'M', 'rot', None, 6))
    o.append(knob(64, 17, 8, 'm1', 'fun', None, 4))
    o.append(knob(92, 17, 8, 'm2', 'nav', None, 4))
    if labels:
        o.append(text(24, 34.4, 'Chord Voicing', 2.5, color='#fff'))
        o.append(text(64, 29, 'Bass Voicing', 2.4, color='#fff'))
        o.append(text(92, 29, 'liste', 2.4, color='#fff'))
    x0, y0, p, k = 19.5, 39, 19.5, 17.5
    for n, nm, kind in PAD_KEYS:
        r, c = divmod(n - 1, 4)
        x, y = x0 + c * p, y0 + r * p
        o.append(rect(x, y, k, k, kind, rx=2, sw=0.7))
        if labels:
            o.append(text(x + k / 2, y + k / 2 - 1.8, nm, 3.1 if len(nm) < 7 else 2.6, weight='700'))
            o.append(text(x + k / 2, y + k - 2.6, f'T{n}', 2.3, color='#555'))
    o.append(text(PAD_W / 2, PAD_D + 5, 'disposizione delle manopole e misure da verificare sul pad', 2.5, color='#777', italic=True))
    o.append('</svg>')
    return ''.join(o)

def twin_svg(width='100%'):
    names = ['Sound', 'Perform', 'FX', 'Key', 'Bass', 'Loop', 'BPM', 'Volume']
    o = [f'<svg viewBox="0 0 230 78" width="{width}" xmlns="http://www.w3.org/2000/svg" font-family="Inter, Helvetica, Arial, sans-serif">']
    o.append(text(48, 5, 'manopole della MPK', 4, weight='700'))
    o.append(text(182, 5, 'tasti del pad', 4, weight='700'))
    for i, nm in enumerate(names):
        r, c = divmod(i, 4)
        kx, ky = 12 + c * 24, 22 + r * 26
        px, py = 146 + c * 24, 22 + r * 26
        o.append(f'<line x1="{kx + 10}" y1="{ky}" x2="{px - 10}" y2="{py}" stroke="#c9c9c9" stroke-width="0.5" stroke-dasharray="1.5 1.5"/>')
    for i, nm in enumerate(names):
        r, c = divmod(i, 4)
        kx, ky = 12 + c * 24, 22 + r * 26
        px, py = 146 + c * 24, 22 + r * 26
        kind = 'loop' if nm == 'Loop' else 'rot'
        o.append(f'<circle cx="{kx}" cy="{ky}" r="9.5" fill="{C[kind][1]}" stroke="{C[kind][0]}" stroke-width="0.7"/>')
        o.append(text(kx, ky - 1.5, nm, 2.9 if len(nm) < 7 else 2.5, weight='700'))
        o.append(text(kx, ky + 4, f'K{i + 1}', 2.4, color='#555'))
        kind2 = 'loop' if nm == 'Loop' else 'fun'
        o.append(rect(px - 9.5, py - 9.5, 19, 19, kind2, rx=2, sw=0.7))
        o.append(text(px, py - 1.5, nm, 2.9 if len(nm) < 7 else 2.5, weight='700'))
        o.append(text(px, py + 4.5, f'T{i + 1}', 2.4, color='#555'))
    o.append(text(115, 71, 'stessa posizione = stesso encoder dell\'originale:  manopola = ruotare,  tasto = premere,  tasto tenuto + manopola = premere e ruotare', 2.9, weight='600'))
    o.append('</svg>')
    return ''.join(o)

def tk_timeline_svg(width='100%'):
    o = [f'<svg viewBox="0 -2 300 70" width="{width}" xmlns="http://www.w3.org/2000/svg" font-family="Inter, Helvetica, Arial, sans-serif">']
    for y, nm in ((14, 'Tn'), (28, 'Kn'), (44, 'evento')):
        o.append(text(1, y, nm, 4.2, anchor='start', weight='700'))
    ex = [
        (24, 'premere (T4)', (4, 20), [], [(20, 'PRESS')], 'Key mode on/off'),
        (114, 'tenere 1 s (T1)', (4, 80), [], [(54, 'HOLD')], 'Save / Save As / Delete'),
        (204, 'premere e ruotare (T4 + K4)', (4, 82), [(26, '+1'), (42, '+1'), (58, '−1')], [(26, 'TURN'), (42, 'TURN'), (58, 'TURN')], 'transpose'),
    ]
    for x0, title, (a, b), ticks, evs, eff in ex:
        o.append(text(x0 + 43, 3, title, 4.2, weight='700'))
        for yy in (14, 28, 44):
            o.append(f'<line x1="{x0}" y1="{yy}" x2="{x0 + 86}" y2="{yy}" stroke="#ccc" stroke-width="0.4"/>')
        o.append(f'<rect x="{x0 + a}" y="10" width="{b - a}" height="8" rx="1.5" fill="{C["fun"][1]}" stroke="{C["fun"][0]}" stroke-width="0.5"/>')
        o.append(text(x0 + (a + b) / 2, 14, 'tenuto' if b - a > 30 else 'tocco', 3.3, color=C['fun'][0], weight='600'))
        for t, lab in ticks:
            o.append(f'<circle cx="{x0 + t}" cy="28" r="2.2" fill="{C["rot"][0]}"/>')
            o.append(text(x0 + t, 34.5, lab, 3.2, color=C['rot'][0]))
        if not ticks:
            o.append(text(x0 + 43, 28, '—', 3.2, color='#aaa'))
        for t, lab in evs:
            o.append(rect(x0 + t - 7, 40, 14, 8, 'fun', rx=1.2, sw=0.4))
            o.append(text(x0 + t, 44, lab, 2.9, weight='700'))
        o.append(text(x0 + 43, 56, '→ ' + eff, 3.9, weight='600', color='#333'))
    o.append(text(150, 65, 'Ogni scatto di Kn conta. Senza tasto tenuto, la manopola ruota e basta.', 3.0, color='#777', italic=True))
    o.append('</svg>')
    return ''.join(o)

# ---------------------------------------------------------------- case

CASE_W, CASE_D = 610, 300
MPK = (8, 112, 451, 180)          # x, y (dall'alto = retro), w, h in vista dall'alto
PADBAY = (469, 182, 133, 110)
COMP = (469, 8, 133, 166)
SPINE = (8, 8, 453, 96)
CRADLE = (150, 14, 100, 86)

def _dim(x1, y1, x2, y2, label, off=0, vertical=False, size=6):
    o = [f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#555" stroke-width="0.6" marker-start="url(#ar)" marker-end="url(#ar)"/>']
    if vertical:
        o.append(f'<text x="{x1 - 3 + off}" y="{(y1 + y2) / 2}" font-size="{size}" text-anchor="middle" fill="#333" transform="rotate(-90 {x1 - 3 + off} {(y1 + y2) / 2})">{esc(label)}</text>')
    else:
        o.append(f'<text x="{(x1 + x2) / 2}" y="{y1 - 2.5 + off}" font-size="{size}" text-anchor="middle" fill="#333">{esc(label)}</text>')
    return ''.join(o)

DEFS = ('<defs><marker id="ar" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">'
        '<path d="M0,2 L10,5 L0,8 z" fill="#555"/></marker>'
        '<pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        '<line x1="0" y1="0" x2="0" y2="6" stroke="#bbb" stroke-width="1.2"/></pattern></defs>')

def case_top_svg(width='100%'):
    o = [f'<svg viewBox="-40 -22 {CASE_W + 64} {CASE_D + 58}" width="{width}" xmlns="http://www.w3.org/2000/svg" font-family="Inter, Helvetica, Arial, sans-serif">', DEFS]
    o.append(f'<rect x="0" y="0" width="{CASE_W}" height="{CASE_D}" rx="10" fill="#efe9dc" stroke="#8a7f6a" stroke-width="1.4"/>')
    # dorso posteriore e canale cavi
    x, y, w, h = SPINE
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#ddd5c3" stroke="#a89c84" stroke-width="0.8"/>')
    o.append(f'<rect x="{x}" y="{y + h - 26}" width="{w}" height="26" fill="url(#hatch)" stroke="#a89c84" stroke-width="0.5"/>')
    o.append(text(80, y + h - 13, 'canale dei cavi (coperchio)', 6, color='#6b6150'))
    o.append(text(90, 40, 'dorso posteriore', 7, weight='700', color='#6b6150'))
    o.append(text(90, 52, 'in 3 pezzi stampati', 5.5, color='#6b6150'))
    # culla della Flip
    x, y, w, h = CRADLE
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#fff" stroke="#2F6FD6" stroke-width="1.2"/>')
    o.append(f'<rect x="{x + 8}" y="{y + 3}" width="84" height="80" rx="6" fill="#e9e6df" stroke="#999" stroke-width="0.6"/>')
    o.append(text(x + w / 2, y + 30, 'Miyoo Flip', 8, weight='700'))
    o.append(text(x + w / 2, y + 42, 'aperta, schermo verso di te', 5.5))
    o.append(text(x + w / 2, y + 52, 'culla inclinata 15°', 5.5))
    o.append(f'<rect x="{x + 30}" y="{y - 4}" width="12" height="6" fill="#2F6FD6"/>')
    o.append(text(x + 36, y - 9, 'USB-C OTG (posizione schematica)', 4.8, color='#2F6FD6', weight='700'))
    # MPK
    x, y, w, h = MPK
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#3a3a3a" stroke="#222" stroke-width="1"/>')
    for px in (132, 167, 201, 236):
        for py in (26, 61):
            kind = 'tipo' if py == 26 else 'ext'
            o.append(f'<rect x="{x + px - 14}" y="{y + py - 14}" width="28" height="28" rx="2.5" fill="{C[kind][1]}" stroke="{C[kind][0]}" stroke-width="0.8"/>')
    for kx in (340, 371, 400, 430):
        for ky in (19, 47):
            o.append(f'<circle cx="{x + kx}" cy="{y + ky}" r="9.5" fill="{C["rot"][1]}" stroke="{C["rot"][0]}" stroke-width="0.7"/>')
    o.append(f'<circle cx="{x + 88}" cy="{y + 19}" r="9" fill="#d33"/>')
    o.append(f'<rect x="{x + 20}" y="{y + 30}" width="14" height="44" rx="3" fill="#ddd"/><rect x="{x + 50}" y="{y + 30}" width="14" height="44" rx="3" fill="#ddd"/>')
    o.append(f'<rect x="{x + 13}" y="{y + 93}" width="425" height="84" fill="#f7f7f7" stroke="#999" stroke-width="0.4"/>')
    o.append(text(x + w / 2, y + 135, 'Akai MPK mini Plus  451 × 180 × 52', 9, weight='700', color='#555'))
    for cx, lab in ((280, 'MIDI'), (357, 'CV'), (394, 'pedale'), (428, 'USB-B')):
        o.append(f'<rect x="{x + cx - 5}" y="{y - 4}" width="10" height="5" fill="#D24343"/>')
    o.append(text(x + 357, y - 9, 'connettori MPK sul retro', 4.8, color='#D24343', weight='700'))
    # vano del pad
    x, y, w, h = PADBAY
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#fff" stroke="#17936B" stroke-width="1.2"/>')
    o.append(f'<g transform="translate({x + 9},{y + 5})"><rect x="0" y="0" width="{PAD_W}" height="{PAD_D}" rx="6" fill="#2b2b2b"/>'
             f'<circle cx="24" cy="21" r="14" fill="{C["rot"][1]}"/><circle cx="64" cy="21" r="8.5" fill="{C["fun"][1]}"/><circle cx="92" cy="21" r="8.5" fill="{C["nav"][1]}"/>'
             + ''.join(f'<rect x="{18.5 + c * 20}" y="{43 + r * 20}" width="18" height="18" rx="2" fill="#ccc"/>' for r in range(3) for c in range(4)) + '</g>')
    o.append(text(x + w / 2, y - 6, 'macro pad (rialzato 10 mm)', 5.5, weight='700', color='#17936B'))
    # vano hub e powerbank
    x, y, w, h = COMP
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#ddd5c3" stroke="#a89c84" stroke-width="0.8"/>')
    o.append(f'<rect x="{x + 10}" y="{y + 12}" width="85" height="32" rx="3" fill="#fff" stroke="#555" stroke-width="0.6"/>')
    o.append(text(x + 52, y + 28, 'hub USB 2.0', 6, weight='700'))
    o.append(f'<rect x="{x + 10}" y="{y + 56}" width="110" height="68" rx="5" fill="#fff" stroke="#555" stroke-width="0.6" stroke-dasharray="3 2"/>')
    o.append(text(x + 65, y + 84, 'powerbank', 6, weight='700'))
    o.append(text(x + 65, y + 94, '(facoltativo)', 5, color='#666'))
    o.append(text(x + w / 2, y + 145, 'vano con coperchio', 5.5, color='#6b6150'))
    # quote
    o.append(_dim(0, -8, CASE_W, -8, f'{CASE_W} mm'))
    o.append(_dim(-14, 0, -14, CASE_D, f'{CASE_D} mm', vertical=True, off=-4))
    o.append(_dim(MPK[0], CASE_D + 12, MPK[0] + MPK[2], CASE_D + 12, '453 (vano MPK)', off=12))
    o.append(_dim(PADBAY[0], CASE_D + 12, PADBAY[0] + PADBAY[2], CASE_D + 12, '133', off=12))
    o.append(text(CASE_W / 2, CASE_D + 30, 'vista dall\'alto, in scala · il musicista sta in basso', 6, color='#777', italic=True))
    o.append('</svg>')
    return ''.join(o)

def case_side_svg(width='100%'):
    # sezione laterale vista da destra, profondità in orizzontale (fronte a sinistra), altezza in verticale
    H = 175
    def P(d, h):
        return f'{d:.1f},{H - h:.1f}'
    o = [f'<svg viewBox="-14 -4 352 {H + 22}" width="{width}" xmlns="http://www.w3.org/2000/svg" font-family="Inter, Helvetica, Arial, sans-serif">', DEFS]
    o.append(f'<polygon points="{P(0,0)} {P(300,0)} {P(300,6)} {P(0,6)}" fill="#c8b48e" stroke="#8a7f6a" stroke-width="0.6"/>')
    o.append(text(150, H - 3, 'base: compensato 6 mm', 4.5, color='#6b6150'))
    # bordo anteriore
    o.append(f'<polygon points="{P(0,6)} {P(6,6)} {P(6,22)} {P(0,22)}" fill="#ddd5c3" stroke="#a89c84" stroke-width="0.6"/>')
    # MPK (profilo approssimato): fronte 8, retro 188
    mpk = [(8, 6), (8, 26), (95, 30), (100, 38), (188, 40), (188, 6)]
    o.append('<polygon points="' + ' '.join(P(d, h) for d, h in mpk) + '" fill="#3a3a3a" stroke="#222" stroke-width="0.6"/>')
    for d in (141, 169):
        o.append(f'<rect x="{d - 9.5}" y="{H - 52}" width="19" height="12" rx="3" fill="{C["rot"][1]}" stroke="{C["rot"][0]}" stroke-width="0.5"/>')
    o.append(f'<rect x="{169 - 4}" y="{H - 62}" width="8" height="22" rx="3" fill="#d33"/>')
    o.append(text(60, H - 34, 'MPK mini Plus', 5, weight='700', color='#fff'))
    o.append(text(155, H - 56, 'manopole', 4.2, color='#17936B'))
    # canale cavi e dorso
    o.append(f'<polygon points="{P(188,6)} {P(206,6)} {P(206,30)} {P(188,30)}" fill="url(#hatch)" stroke="#a89c84" stroke-width="0.6"/>')
    o.append(text(197, H - 34, 'cavi', 4, color='#6b6150'))
    o.append(f'<polygon points="{P(206,6)} {P(300,6)} {P(300,62)} {P(206,52)}" fill="#ddd5c3" stroke="#a89c84" stroke-width="0.6"/>')
    o.append(text(258, H - 22, 'dorso', 4.6, color='#6b6150'))
    # Flip: metà inferiore inclinata 15° (retro più alto), cerniera sul retro, schermo aperto
    t = math.radians(15)
    d0, h0 = 210, 56                      # spigolo anteriore della metà inferiore
    L, T = 80.35, 12.25
    rear = (d0 + L * math.cos(t), h0 + L * math.sin(t))
    base = [(d0, h0), rear, (rear[0] - T * math.sin(t), rear[1] + T * math.cos(t)), (d0 - T * math.sin(t), h0 + T * math.cos(t))]
    o.append('<polygon points="' + ' '.join(P(d, h) for d, h in base) + '" fill="#e9e6df" stroke="#777" stroke-width="0.6"/>')
    hinge = base[2]
    ang = math.radians(180 - 125 + 15)    # schermo a 70° dall'orizzontale, inclinato all'indietro
    top = (hinge[0] + L * math.cos(ang), hinge[1] + L * math.sin(ang))
    o.append(f'<line x1="{hinge[0]:.1f}" y1="{H - hinge[1]:.1f}" x2="{top[0]:.1f}" y2="{H - top[1]:.1f}" stroke="#555" stroke-width="10" stroke-linecap="round"/>')
    o.append(f'<line x1="{hinge[0] - 4:.1f}" y1="{H - hinge[1] - 3:.1f}" x2="{top[0] - 4:.1f}" y2="{H - top[1] + 3:.1f}" stroke="#38C8F0" stroke-width="3"/>')
    o.append(text(top[0] - 44, H - top[1] + 4, 'schermo Flip', 4.6, weight='700', color='#2F6FD6'))
    o.append(text(top[0] - 44, H - top[1] + 10, '≈ 70° dall\'orizzontale', 4, color='#2F6FD6'))
    o.append(text(top[0] - 44, H - top[1] + 16, 'sporge ≈ 10 mm dal retro', 4, color='#2F6FD6'))
    # culla
    o.append(f'<polygon points="{P(206,52)} {P(300,62)} {P(300,72)} {P(208,57)}" fill="#fff" stroke="#2F6FD6" stroke-width="0.6"/>')
    o.append(text(250, H - 48, 'culla 15°', 4, color='#2F6FD6'))
    # linea dello sguardo
    mid = ((hinge[0] + top[0]) / 2, (hinge[1] + top[1]) / 2)
    o.append(f'<line x1="-6" y1="{H - 150}" x2="{mid[0] - 6:.1f}" y2="{H - mid[1]:.1f}" stroke="#999" stroke-width="0.6" stroke-dasharray="3 2" marker-end="url(#ar)"/>')
    o.append(text(10, H - 156, 'sguardo dal musicista (≈ 50–70 cm)', 4.2, color='#777', anchor='start'))
    # quote
    o.append(_dim(0, H + 10, 300, H + 10, '300 mm', off=9, size=5))
    o.append(_dim(-6, H, -6, H - 58, '≈ 58', vertical=True, size=4.5))
    o.append(_dim(330, H, 330, H - top[1], f'≈ {top[1]:.0f}', vertical=True, off=-4, size=4.5))
    o.append('</svg>')
    return ''.join(o)

def wiring_svg(width='100%'):
    o = [f'<svg viewBox="0 0 260 104" width="{width}" xmlns="http://www.w3.org/2000/svg" font-family="Inter, Helvetica, Arial, sans-serif">', DEFS]
    def box(x, y, w, h, title, sub, col='#555', dash=False):
        d = ' stroke-dasharray="3 2"' if dash else ''
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="#fff" stroke="{col}" stroke-width="0.9"{d}/>'
                + text(x + w / 2, y + h / 2 - 3, title, 4.4, weight='700') + text(x + w / 2, y + h / 2 + 4, sub, 3.2, color='#555'))
    def wire(x1, y1, x2, y2, lab='', col='#333', dash=False):
        d = ' stroke-dasharray="3 2"' if dash else ''
        o = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="1"{d} marker-end="url(#ar)"/>'
        if lab:
            o += text((x1 + x2) / 2, (y1 + y2) / 2 - 3, lab, 3.1, color='#555')
        return o
    o.append(box(6, 38, 50, 26, 'Miyoo Flip', 'Stame', '#2F6FD6'))
    o.append(box(96, 38, 46, 26, 'hub USB 2.0', 'semplice, senza PD'))
    o.append(box(190, 8, 62, 22, 'MPK mini Plus', 'USB-B'))
    o.append(box(190, 40, 62, 22, 'macro pad', 'USB-C, RGB spento'))
    o.append(box(190, 74, 62, 22, 'powerbank', 'solo per l\'hub', '#777', True))
    o.append(wire(56, 51, 96, 51, 'USB-C sopra (OTG)'))
    o.append(wire(142, 46, 190, 19))
    o.append(wire(142, 51, 190, 51))
    o.append(wire(190, 85, 142, 60, 'hub alimentato?', '#777', True))
    o.append(box(6, 76, 50, 20, 'cuffie / ampli', 'jack della Flip'))
    o.append(wire(31, 64, 31, 76))
    o.append(text(31, 10, 'USB-C sotto: ricarica', 3.4, weight='700', color='#B71C1C'))
    o.append(text(31, 16, 'solo a console spenta', 3.2, color='#B71C1C'))
    o.append(f'<line x1="31" y1="20" x2="31" y2="38" stroke="#B71C1C" stroke-width="0.8" stroke-dasharray="2 2"/>')
    o.append(text(221, 101, 'pedale → jack SUSTAIN della MPK', 3.2, color='#555'))
    o.append('</svg>')
    return ''.join(o)

if __name__ == '__main__':
    import sys
    open(sys.argv[1], 'w', encoding='utf-8').write('<html><body style="margin:0;background:#fff;width:1100px">'
        + pad_svg('40%') + twin_svg('90%') + tk_timeline_svg('90%') + case_top_svg('100%') + case_side_svg('80%') + wiring_svg('80%') + '</body></html>')
