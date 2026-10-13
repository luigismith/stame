# Genera i disegni SVG dei controlli (MPK mini Plus, Miyoo Flip) per il PDF di Stame.
# Coordinate della MPK in mm, dalla guida alla MPK mini Plus §14.15.2.

C = {
    'tipo':   ('#E07A1F', '#FCE3CC'),
    'ext':    ('#C99A00', '#FFF0B3'),
    'fun':    ('#2F6FD6', '#D9E6FB'),
    'rot':    ('#17936B', '#CDEFE2'),
    'nav':    ('#7A4FD0', '#E7DDFB'),
    'loop':   ('#D24343', '#F9D6D6'),
    'push':   ('#C2185B', '#F8D2E2'),
    'perf':   ('#555555', '#E4E4E4'),
    'off':    ('#B5B5B5', '#F2F2F2'),
}

def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def rect(x, y, w, h, kind, rx=1.5, sw=0.5):
    s, f = C[kind]
    return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{rx}" fill="{f}" stroke="{s}" stroke-width="{sw}"/>'

def text(x, y, t, size=3.2, anchor='middle', weight='400', color='#1a1a1a', italic=False):
    st = ' font-style="italic"' if italic else ''
    lines = t.split('\n')
    out = []
    for i, ln in enumerate(lines):
        dy = (i - (len(lines) - 1) / 2) * size * 1.15
        out.append(f'<text x="{x:.2f}" y="{y + dy:.2f}" font-size="{size}" text-anchor="{anchor}" '
                   f'font-weight="{weight}" fill="{color}" dominant-baseline="central"{st}>{esc(ln)}</text>')
    return ''.join(out)

def badge(x, y, n):
    return (f'<circle cx="{x}" cy="{y}" r="3.1" fill="#1a1a1a"/>'
            + text(x, y + 0.1, str(n), 3.4, weight='700', color='#fff'))

# ---------------------------------------------------------------- MPK mini Plus

PADS = {  # numero pad: (x, y)
    5: (132, 26), 6: (167, 26), 7: (201, 26), 8: (236, 26),
    1: (132, 61), 2: (167, 61), 3: (201, 61), 4: (236, 61),
}
PAD_A = {
    5: ('Dim', 'tipo'), 6: ('Min', 'tipo'), 7: ('Maj', 'tipo'), 8: ('Sus', 'tipo'),
    1: ('6', 'ext'), 2: ('m7', 'ext'), 3: ('M7', 'ext'), 4: ('9', 'ext'),
}
PAD_B = {
    1: ('Key', 'fun', 'B1'), 2: ('Bass', 'fun', 'B2'), 3: ('Perform', 'fun', 'B3'), 4: ('Chord\nVoicing', 'fun', 'B4'),
    5: ('Loop', 'loop', 'B5'), 6: ('BPM', 'fun', 'B6'), 7: ('Options', 'nav', 'B7'), 8: ('PUSH', 'push', 'B8'),
}
KNOBS = [  # (x, y, nome, Kn)
    (340, 19, 'Chord\nVoicing', 'K1'), (371, 19, 'Bass\nVoicing', 'K2'), (400, 19, 'Sound', 'K3'), (430, 19, 'Perform', 'K4'),
    (340, 47, 'FX', 'K5'), (371, 47, 'Key', 'K6'), (400, 47, 'BPM', 'K7'), (430, 47, 'Volume', 'K8'),
]
TRANSPORT = [  # (x, nome MPK, funzione, tipo)
    (341, '<<', 'fuoco −', 'nav'), (359, '>>', 'fuoco +', 'nav'), (376, 'STOP', 'stop loop\n1 s = Clear', 'loop'),
    (394, 'PLAY', 'BPM\n(beat)', 'fun'), (412, 'REC', 'Loop', 'loop'), (430, 'SEQ', '—', 'off'),
]
UNUSED = [  # (x, y, nome)
    (81, 43, 'ARP'), (98, 43, 'TAP'), (81, 56, 'N.REP'), (98, 56, 'FULL'), (81, 69, 'OCT−'), (98, 69, 'OCT+'),
    (289, 49, 'SCALES'), (307, 49, 'CHORDS'), (271, 70.5, 'SHIFT'), (289, 70.5, 'HOME'), (307, 70.5, 'PROG'),
]

def mpk_svg(bank='A', width='100%'):
    o = [f'<svg viewBox="-4 -4 459 150" width="{width}" xmlns="http://www.w3.org/2000/svg" font-family="Inter, Helvetica, Arial, sans-serif">']
    o.append('<rect x="0" y="0" width="451" height="142" rx="6" fill="#2b2b2b"/>')
    o.append('<rect x="3" y="3" width="445" height="86" rx="4" fill="#3a3a3a"/>')
    # ruote
    for x, nm, kind in ((27, 'Pitch', 'perf'), (57, 'Mod', 'perf')):
        o.append(rect(x - 7, 52 - 21.75, 14, 43.5, kind, rx=3))
        o.append(text(x, 52, nm, 3.2, weight='600'))
    o.append(text(42, 80.5, 'bend · modulazione', 2.6, color='#ddd'))
    # joystick
    o.append(f'<circle cx="88" cy="19" r="11" fill="{C["nav"][1]}" stroke="{C["nav"][0]}" stroke-width="0.6"/>')
    o.append(f'<circle cx="88" cy="19" r="5" fill="#d33"/>')
    o.append(text(88, 4.5, '▲▼ ruota il fuoco', 2.5, color='#fff'))
    o.append(text(100.5, 19, '▶ ok', 2.4, anchor='start', color='#fff'))
    o.append(text(75.5, 19, 'indietro ◀', 2.4, anchor='end', color='#fff'))
    # pulsanti senza effetto su Stame
    for x, y, nm in UNUSED:
        o.append(rect(x - 6.85, y - 4.35, 13.7, 8.7, 'off', rx=1))
        o.append(text(x, y, nm, 2.3, color='#888'))
    # BANK A/B
    o.append(rect(271 - 6.85, 49 - 4.35, 13.7, 8.7, 'fun' if bank == 'B' else 'tipo', rx=1, sw=0.8))
    o.append(text(271, 49, 'BANK', 2.4, weight='700'))
    o.append(text(271, 57, 'A = accordi\nB = funzioni', 2.0, color='#fff'))
    # display ed encoder della MPK
    o.append('<rect x="258.5" y="11" width="37" height="16" rx="1" fill="#0b0b0b" stroke="#555" stroke-width="0.4"/>')
    o.append(text(277, 19, 'STAME', 3.4, weight='700', color='#9fd8ff'))
    o.append(f'<circle cx="310" cy="19" r="6" fill="{C["off"][1]}" stroke="{C["off"][0]}" stroke-width="0.5"/>')
    o.append(text(310, 30, 'enc. MPK', 2.2, color='#aaa'))
    # pad
    for n, (x, y) in PADS.items():
        if bank == 'A':
            nm, kind = PAD_A[n]
            o.append(rect(x - 14, y - 14, 28, 28, kind, rx=2.5, sw=0.8))
            o.append(text(x, y - 1.5, nm, 7 if len(nm) < 4 else 6, weight='700'))
            o.append(text(x, y + 9, f'pad {n}', 2.4, color='#666'))
        else:
            nm, kind, bn = PAD_B[n]
            o.append(rect(x - 14, y - 14, 28, 28, kind, rx=2.5, sw=0.8))
            o.append(text(x, y - 1, nm, 4.6 if '\n' not in nm and len(nm) < 6 else 3.8, weight='700'))
            o.append(text(x, y + 9.5, bn, 2.6, color='#555'))
    # manopole
    for x, y, nm, kn in KNOBS:
        o.append(f'<circle cx="{x}" cy="{y}" r="9.5" fill="{C["rot"][1]}" stroke="{C["rot"][0]}" stroke-width="0.7"/>')
        o.append(text(x, y - 0.3, nm, 2.7 if '\n' in nm else 3.0, weight='700'))
        o.append(text(x, y + 12.3, kn, 2.4, color='#ddd'))
    # trasporto
    for x, nm, fn, kind in TRANSPORT:
        o.append(rect(x - 6.85, 70 - 4.35, 13.7, 8.7, kind, rx=1, sw=0.7))
        o.append(text(x, 70, nm, 2.5, weight='700', color='#333' if kind != 'off' else '#888'))
        o.append(text(x, 81, fn, 2.2, color='#fff'))
    # tastiera (accorciata)
    x0, ww, ytop, h = 13.0, 425 / 22, 93, 46
    whites = []
    for i in range(22):
        o.append(f'<rect x="{x0 + i * ww:.2f}" y="{ytop}" width="{ww - 0.4:.2f}" height="{h}" fill="#f7f7f7" stroke="#999" stroke-width="0.3"/>')
    pattern = [1, 1, 0, 1, 1, 1, 0]  # nero dopo C, D, F, G, A
    for i in range(21):
        if pattern[i % 7]:
            bx = x0 + (i + 1) * ww - 5.5
            o.append(f'<rect x="{bx:.2f}" y="{ytop}" width="11" height="{h * 0.6:.2f}" fill="#222"/>')
    o.append(f'<rect x="{x0}" y="{ytop + h - 9}" width="425" height="9" fill="{C["perf"][1]}" fill-opacity="0.85"/>')
    o.append(text(225.5, ytop + h - 4.5, 'qualunque tasto = fondamentale (Do … Si) con velocity · l\'ottava non conta', 3.0, weight='600'))
    o.append('</svg>')
    return ''.join(o)

# ---------------------------------------------------------------- Miyoo Flip (metà inferiore, schematica)

def btn_round(x, y, r, label, kind, sub=None, lsize=3.4):
    s, f = C[kind]
    o = [f'<circle cx="{x}" cy="{y}" r="{r}" fill="{f}" stroke="{s}" stroke-width="0.7"/>',
         text(x, y, label, lsize, weight='700')]
    if sub:
        o.append(text(x, y + r + 3.6, sub, 2.5, color='#333'))
    return ''.join(o)

def flip_svg(mode='fuoco', width='100%'):
    o = [f'<svg viewBox="-12 -30 184 134" width="{width}" xmlns="http://www.w3.org/2000/svg" font-family="Inter, Helvetica, Arial, sans-serif">']
    o.append('<rect x="0" y="0" width="160" height="86" rx="10" fill="#e9e6df" stroke="#999" stroke-width="0.6"/>')
    o.append('<rect x="8" y="-6" width="144" height="6" rx="2" fill="#cfcac0"/>')
    o.append(text(80, -3, 'cerniera · schermo sopra', 2.4, color='#666'))
    if mode == 'fuoco':
        sh = [(24, -22, 'L2', 'libero', 'off'), (24, -13, 'L1', 'fuoco −', 'nav'),
              (136, -22, 'R2', 'libero', 'off'), (136, -13, 'R1', 'fuoco +', 'nav')]
    else:
        sh = [(24, -22, 'L2', 'Dim', 'tipo'), (24, -13, 'L1', 'Min', 'tipo'),
              (136, -22, 'R2', 'Sus', 'tipo'), (136, -13, 'R1', 'Maj', 'tipo')]
    for x, y, nm, fn, kind in sh:
        o.append(rect(x - 13, y - 3.5, 26, 7, kind, rx=2))
        o.append(text(x, y, f'{nm}  {fn}', 2.5, weight='600'))
    # croce
    cx, cy = 30, 26
    if mode == 'fuoco':
        o.append(rect(cx - 5, cy - 16, 10, 32, 'nav', rx=1.5))
        o.append(rect(cx - 16, cy - 5, 32, 10, 'nav', rx=1.5))
        o.append(text(cx, cy - 11, '▲', 3), ); o.append(text(cx, cy + 11, '▼', 3))
        o.append(text(cx - 11, cy, '◀', 3)); o.append(text(cx + 11, cy, '▶', 3))
        o.append(text(cx, cy - 22, 'croce: ruota il fuoco\no scorre la lista', 2.5))
    else:
        for dx, dy, nm in ((0, -11, '9'), (0, 11, 'm7'), (-11, 0, '6'), (11, 0, 'M7')):
            o.append(rect(cx + dx - 5, cy + dy - 5, 10, 10, 'ext', rx=1.5))
            o.append(text(cx + dx, cy + dy, nm, 3, weight='700'))
        o.append(text(cx, cy - 22, 'croce: estensioni', 2.5))
    # levette
    if mode == 'fuoco':
        o.append(btn_round(40, 62, 8, 'L3', 'off', 'libera'))
        o.append(btn_round(120, 62, 8, 'R3', 'off', 'libera'))
    else:
        o.append(btn_round(40, 62, 8, 'nota', 'perf', 'levetta: 12 settori'))
        o.append(btn_round(120, 62, 8, 'CV', 'rot', 'X: voicing · Y: fuoco'))
    # ABXY (stile Nintendo: X sopra, A a destra, B sotto, Y a sinistra)
    ax, ay = 130, 26
    if mode == 'fuoco':
        abxy = [(0, -11, 'X', 'push', 'PUSH'), (11, 0, 'A', 'nav', 'premi'),
                (0, 11, 'B', 'nav', 'indietro'), (-11, 0, 'Y', 'fun', 'B.Voicing')]
    else:
        abxy = [(0, -11, 'X', 'nav', 'fuoco −'), (11, 0, 'A', 'perf', 'suona'),
                (0, 11, 'B', 'nav', 'indietro'), (-11, 0, 'Y', 'nav', 'fuoco +')]
    for dx, dy, nm, kind, fn in abxy:
        o.append(btn_round(ax + dx, ay + dy, 5, nm, kind))
    for dx, dy, nm, kind, fn in abxy:
        if dx > 0:
            o.append(text(ax + dx + 7, ay + dy, fn, 2.6, anchor='start', weight='600'))
        elif dx < 0:
            o.append(text(ax + dx - 7, ay + dy, fn, 2.6, anchor='end', weight='600'))
        elif dy < 0:
            o.append(text(ax, ay + dy - 8, fn, 2.6, weight='600'))
        else:
            o.append(text(ax, ay + dy + 8, fn, 2.6, weight='600'))
    # SELECT, START, MENU
    for x, nm, fn, kind in ((66, 'SELECT', 'Options', 'nav'), (94, 'START', 'BPM', 'fun'), (80, 'MENU', 'menu', 'perf')):
        y = 76 if nm != 'MENU' else 58
        o.append(rect(x - 8, y - 3, 16, 6, kind, rx=3))
        o.append(text(x, y, nm, 2.3, weight='700'))
        o.append(text(x, y - 6, fn, 2.5, weight='600'))
    o.append(text(80, 98, 'disposizione schematica: le posizioni di MENU, SELECT e START vanno controllate sulla console', 2.4, color='#777', italic=True))
    o.append('</svg>')
    return ''.join(o)

# ---------------------------------------------------------------- anello del fuoco

FOCUS_ORDER = ['Sound', 'Perform', 'FX', 'Key', 'Bass', 'Loop', 'BPM', 'Volume', 'Options', 'Chord\nVoicing', 'Bass\nVoicing']

def focus_ring_svg(active='Loop', width='100%'):
    import math
    o = [f'<svg viewBox="-62 -58 124 116" width="{width}" xmlns="http://www.w3.org/2000/svg" font-family="Inter, Helvetica, Arial, sans-serif">']
    o.append('<circle cx="0" cy="0" r="40" fill="none" stroke="#bbb" stroke-width="0.6" stroke-dasharray="2 2"/>')
    n = len(FOCUS_ORDER)
    for i, nm in enumerate(FOCUS_ORDER):
        a = -math.pi / 2 + 2 * math.pi * i / n
        x, y = 40 * math.cos(a), 40 * math.sin(a)
        on = nm.replace('\n', ' ') == active
        s, f = C['nav']
        o.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="10" fill="{s if on else "#fff"}" stroke="{s}" stroke-width="{1.4 if on else 0.6}"/>')
        o.append(text(x, y, nm, 2.7 if '\n' in nm else 3, weight='700', color='#fff' if on else '#222'))
    o.append(text(0, -6, 'fuoco', 4.5, weight='700', color=C['nav'][0]))
    o.append(text(0, 2, 'L1 ◀  ▶ R1', 3.2, weight='600'))
    o.append(text(0, 8.5, 'o premi un encoder', 2.6, color='#555'))
    o.append('</svg>')
    return ''.join(o)

def push_timeline_svg(width='100%'):
    # tre esempi affiancati: premere, tenere, premere e ruotare; corsie X, K6 (o K3), evento generato
    o = [f'<svg viewBox="0 -2 300 72" width="{width}" xmlns="http://www.w3.org/2000/svg" font-family="Inter, Helvetica, Arial, sans-serif">']
    lanes = [(14, 'X'), (28, 'Kn'), (44, 'evento')]
    for y, nm in lanes:
        o.append(text(1, y, nm, 4.2, anchor='start', weight='700'))
    ex = [
        (22, 'premere', [(4, 38)], [(14, 'tick')], [(38, 'G_PRESS', 'push')], 'Key mode on/off'),
        (112, 'tenere 1 s', [(4, 78)], [(12, 'tick')], [(52, 'G_HOLD', 'push')], 'Save / Save As / Delete'),
        (202, 'premere e ruotare', [(4, 80)], [(12, 'tick'), (30, '+1'), (46, '+1'), (62, '−1')], [(30, 'TURN', 'push'), (46, 'TURN', 'push'), (62, 'TURN', 'push')], 'transpose'),
    ]
    for x0, title, xs, ticks, evs, eff in ex:
        o.append(text(x0 + 43, 3, title, 4.4, weight='700'))
        o.append(f'<line x1="{x0}" y1="14" x2="{x0 + 86}" y2="14" stroke="#ccc" stroke-width="0.4"/>')
        o.append(f'<line x1="{x0}" y1="28" x2="{x0 + 86}" y2="28" stroke="#ccc" stroke-width="0.4"/>')
        o.append(f'<line x1="{x0}" y1="44" x2="{x0 + 86}" y2="44" stroke="#ccc" stroke-width="0.4"/>')
        for a, b in xs:
            o.append(f'<rect x="{x0 + a}" y="10" width="{b - a}" height="8" rx="1.5" fill="{C["push"][1]}" stroke="{C["push"][0]}" stroke-width="0.5"/>')
            o.append(text(x0 + (a + b) / 2, 14, 'tenuto', 3.4, color=C['push'][0], weight='600'))
        for i, (t, lab) in enumerate(ticks):
            pass
        for i, (t, lab) in enumerate(ticks):
            col = '#999' if i == 0 else C['rot'][0]
            o.append(f'<circle cx="{x0 + t}" cy="28" r="2.2" fill="{col}"/>')
            o.append(text(x0 + t, 34.5, 'sceglie' if i == 0 else lab, 3.2, color=col))
        for t, lab, kind in evs:
            o.append(rect(x0 + t - 6.8, 40, 13.6, 8, kind, rx=1.2, sw=0.4))
            o.append(text(x0 + t, 44, lab.replace('G_', ''), 2.9, weight='700'))
        o.append(text(x0 + 43, 56, '→ ' + eff, 3.9, weight='600', color='#333'))
    o.append(text(150, 66, 'Kn = K6 negli esempi 1 e 3, K3 nel 2. Il primo scatto sceglie la manopola e non conta.', 3.0, color='#777', italic=True))
    o.append('</svg>')
    return ''.join(o)

if __name__ == '__main__':
    import sys
    open(sys.argv[1], 'w', encoding='utf-8').write(
        '<html><body style="margin:0;background:#fff">' + mpk_svg('A') + mpk_svg('B') +
        '<div style="display:flex">' + flip_svg('fuoco', '50%') + flip_svg('tascabile', '50%') + '</div>' +
        focus_ring_svg(width='40%') + '</body></html>')
