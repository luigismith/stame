# Disegno SVG della plancia 640x480 della Flip, secondo docs/specifica/30-interfaccia.md §4 (UI-140..UI-160).
# Coordinate in pixel dello schermo. Font: monospazio al posto di Spleen (stesse classi S/M/L/XL).

T = {  # tema Giorno, il default (UI-128): gli stessi colori di src/ui_flip/tema.c
    'bg': '#CED4C2', 'panel': '#D9DECE', 'line': '#A2AA95', 'bar': '#B5BDA7', 'text': '#141B18',
    'dim': '#424C47', 'ghost': '#879180', 'treble': '#005A51', 'bass': '#853A00', 'loop': '#4A2894',
    'focus': '#285C00', 'active': '#634A00', 'warn': '#9E160C', 'kb_white': '#E3E7D8', 'kb_black': '#252D29',
    'in_key': '#424C47',
}
MONO = "Consolas, 'DejaVu Sans Mono', 'Courier New', monospace"
FS = {'XS': 10.5, 'S': 14.2, 'M': 21, 'L': 28.5}

def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def tx(x, y, s, cls='S', col='text', anchor='start', weight='400', size=None):
    """y = riga superiore del box della classe (come nella specifica)."""
    fs = size or FS[cls]
    box = {'XS': 12, 'S': 16, 'M': 24, 'L': 32}.get(cls, fs)
    base = y + box * 0.78
    c = T.get(col, col)
    return (f'<text x="{x}" y="{base:.1f}" font-family="{MONO}" font-size="{fs}" fill="{c}" '
            f'text-anchor="{anchor}" font-weight="{weight}" xml:space="preserve">{esc(s)}</text>')

def rc(x, y, w, h, col, stroke=None, sw=1):
    c = T.get(col, col)
    st = f' stroke="{T.get(stroke, stroke)}" stroke-width="{sw}"' if stroke else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}"{st}/>'

def frame(x, y, w, h, col, sw=2):
    c = T.get(col, col)
    return f'<rect x="{x + sw / 2}" y="{y + sw / 2}" width="{w - sw}" height="{h - sw}" fill="none" stroke="{c}" stroke-width="{sw}"/>'

# ---------------------------------------------------------------- zone

def z1(st):
    o = [rc(0, 0, 640, 24, 'bg')]
    if st.get('mpk', True):
        o.append(tx(4, 4, 'MPK STAME', 'S', 'focus', weight='700'))
        o.append(tx(84, 4, st.get('bank', 'A'), 'S', 'dim'))
    else:
        o.append(tx(4, 4, 'NO MPK', 'S', 'warn', weight='700'))
    o.append(tx(108, 4, 'IN', 'S', 'dim'))
    o.append(f'<circle cx="134" cy="12" r="4" fill="{T["focus"] if st.get("mpk", True) else T["line"]}"/>')
    o.append(tx(146, 4, 'OUT', 'S', 'dim'))
    o.append(f'<circle cx="180" cy="12" r="4" fill="{T["line"]}"/>')
    o.append(tx(208, 4, st.get('vox', 'VOX 07/16'), 'S', 'text'))
    o.append(tx(292, 4, 'CPU 23%', 'S', 'text'))
    o.append(rc(360, 7, 88, 4, 'bar') + rc(360, 7, 66, 4, 'text') + rc(360, 13, 88, 4, 'bar') + rc(360, 13, 62, 4, 'text'))
    o.append(rc(430, 7, 2, 4, 'active') + rc(426, 13, 2, 4, 'active'))
    o.append(tx(452, 4, 'clip', 'S', 'dim'))
    if st.get('pad', True):
        o.append(tx(492, 4, 'PAD', 'S', 'focus', weight='700'))
    if st.get('pocket'):
        o.append(tx(520, 4, 'POCKET', 'S', 'active', weight='700'))
    o.append(tx(576, 4, '87%', 'S', 'text'))
    o.append(rc(606, 6, 26, 12, 'bg', 'dim', 1) + rc(632, 9, 2, 6, 'dim') + rc(608, 8, 19, 8, 'text'))
    return ''.join(o)

def chord_name(x, y, root, acc, qual, sup, slash=None, col='text'):
    c = T[col]
    o = []
    o.append(f'<text x="{x}" y="{y + 80}" font-family="{MONO}" font-size="104" font-weight="700" fill="{c}">{esc(root)}</text>')
    x2 = x + 58
    if acc:
        o.append(f'<text x="{x2 - 3}" y="{y + 44}" font-family="{MONO}" font-size="54" font-weight="700" fill="{c}">{esc(acc)}</text>')
        x2 += 32
    if qual:
        o.append(f'<text x="{x2}" y="{y + 80}" font-family="{MONO}" font-size="58" font-weight="700" fill="{c}">{esc(qual)}</text>')
        x2 += 34 * len(qual)
    if sup:
        o.append(f'<text x="{x2 + 2}" y="{y + 30}" font-family="{MONO}" font-size="30" font-weight="700" fill="{c}">{esc(sup)}</text>')
        x2 += 18 * len(sup) + 6
    if slash:
        o.append(f'<text x="{x2}" y="{y + 80}" font-family="{MONO}" font-size="58" font-weight="700" fill="{c}">/{esc(slash)}</text>')
    return ''.join(o)

def z2(st):
    o = [rc(0, 24, 400, 160, 'bg')]
    o.append(tx(4, 26, st.get('key', 'F♯ Minor'), 'L', 'text', weight='700'))
    if st.get('trans'):
        o.append(tx(395, 26, st['trans'], 'L', 'active', anchor='end', weight='700'))
    o.append(chord_name(6, 62, *st.get('chord', ('C', '♯', 'm', '7', None)), col=st.get('chord_col', 'text')))
    notes = st.get('notes', ('C♯2', ['C♯3', 'E3', 'G♯3', 'B3']))
    o.append(tx(4, 158, notes[0], 'M', 'bass', weight='700'))
    o.append(tx(4 + 11.6 * (len(notes[0]) + 1), 158, ':', 'M', 'dim'))
    o.append(tx(4 + 11.6 * (len(notes[0]) + 3), 158, '  '.join(notes[1]), 'M', 'treble', weight='700'))
    o.append(tx(395, 162, st.get('ps', 'SIMPLE'), 'S', 'dim', anchor='end'))
    return ''.join(o)

def z3(st):
    o = [rc(400, 24, 240, 160, 'bg')]
    o.append(tx(408, 26, '120', 'L', 'text', weight='700'))
    o.append(tx(464, 40, 'BPM', 'S', 'dim'))
    o.append(tx(631, 26, '4/4', 'L', 'text', anchor='end', weight='700'))
    o.append(tx(408, 60, 'BEAT 03 Funk', 'S', 'text'))
    o.append(tx(631, 60, 'BAR 12', 'S', 'text', anchor='end'))
    cur = st.get('beat', 1)
    for i in range(4):
        x = 408 + i * 57
        if i == cur:
            o.append(rc(x, 80, 53, 26, 'focus' if i == 0 else 'text'))
        else:
            o.append(rc(x + 0.5, 80.5, 52, 25, 'bg', 'line', 1))
    lp = st.get('loop', 'play')
    if lp == 'play':
        o.append(tx(408, 110, '▶ PLAY', 'M', 'loop', weight='700'))
        col_prog, prog = 'loop', 1.45
        menu, sel = ['OVERDUB', 'PAUSE', 'CLEAR'], 0
    else:
        o.append(tx(408, 110, '● REC', 'M', 'warn', weight='700'))
        col_prog, prog = 'warn', 2.6
        menu, sel = ['STOP', 'PLAY', 'CLEAR'], 0
    o.append(tx(556, 114, 'L2', 'S', 'dim'))
    o.append(tx(631, 110, '2/4' if lp == 'play' else '3/4', 'M', 'text', anchor='end', weight='700'))
    seg_w = (224 - 2 * 3) / 4
    for i in range(4):
        x = 408 + i * (seg_w + 2)
        o.append(rc(round(x), 138, round(seg_w), 14, 'bar'))
        fill = max(0.0, min(1.0, prog - i))
        if fill > 0:
            o.append(rc(round(x), 138, round(seg_w * fill), 14, col_prog))
    hx = 408 + prog * (seg_w + 2)
    o.append(rc(round(hx), 136, 2, 18, 'text'))
    for i, m in enumerate(menu):
        x = 408 + i * 76
        if i == sel:
            o.append(rc(x, 156, 72, 24, 'focus' if st.get('loop_focus') else 'bar'))
            o.append(tx(x + 36, 160, m, 'S', 'bg' if st.get('loop_focus') else 'text', anchor='middle', weight='700'))
        else:
            o.append(rc(x + 0.5, 156.5, 71, 23, 'bg', 'line', 1))
            o.append(tx(x + 36, 160, m, 'S', 'dim', anchor='middle'))
    if lp == 'rec':
        o.append(frame(400, 24, 240, 160, 'warn', 2))
    return ''.join(o)

WHITE_PC = [0, 2, 4, 5, 7, 9, 11]

def z4(st):
    """UI-150: 4 ottave da kb_lo, tasti bianchi di 21 px."""
    o = [rc(0, 184, 640, 104, 'bg')]
    treble = set(st.get('treble', [49, 52, 56, 59]))
    bass = set(st.get('bass', [37]))
    loopn = set(st.get('loopn', [45, 57, 64]))
    inkey = st.get('inkey', {6, 8, 9, 11, 1, 2, 4})
    W, WB = st.get('W', 49), st.get('WB', 37)
    kb_lo = 12 * (min(W, WB) // 12)
    pocket_pc = st.get('pocket_pc')
    keys = {}
    for i in range(28):
        octv, k = divmod(i, 7)
        midi = kb_lo + 12 * octv + WHITE_PC[k]
        keys[midi] = (12 + 22 * i, 21, 200, 271, True)
        if k not in (2, 6):
            keys[midi + 1] = (12 + 22 * i + 15, 13, 200, 243, False)
    def draw_key(m):
        x, w, t, b, white = keys[m]
        col = 'kb_white' if white else 'kb_black'
        out = []
        if m in treble and m in bass:
            out.append(rc(x, t, w / 2, b - t + 1, 'treble') + rc(x + w / 2, t, w / 2, b - t + 1, 'bass'))
        else:
            if m in treble: col = 'treble'
            if m in bass: col = 'bass'
            out.append(rc(x, t, w, b - t + 1, col))
        if m in loopn:
            out.append(rc(x, b - 9 if white else b - 7, w, 10 if white else 8, 'loop'))
        if (m % 12) in inkey:
            on = m in treble or m in bass
            if white:
                out.append(rc(x + 7.5, 252, 6, 6, 'bg' if on else 'in_key'))
            else:
                out.append(rc(x + 4, 228, 5, 5, 'bg' if on else 'in_key'))
        if pocket_pc is not None and (m % 12) == pocket_pc and W <= m <= W + 11:
            out.append(f'<rect x="{x + 1}" y="{t + 1}" width="{w - 2}" height="{b - t - 1}" fill="none" stroke="{T["focus"]}" stroke-width="2"/>')
        return ''.join(out)
    for m in sorted(keys):
        if keys[m][4]:
            o.append(draw_key(m))
    for m in sorted(keys):
        if not keys[m][4]:
            o.append(draw_key(m))
    def win(lo, y, col):
        x0 = keys[lo][0]
        hi = lo + 11
        x1 = keys[hi][0] + keys[hi][1]
        return rc(x0, y, x1 - x0, 2, col) + rc(x0, y - 2, 1, 6, col) + rc(x1 - 1, y - 2, 1, 6, col)
    o.append(win(W, 189, 'treble'))
    o.append(win(WB, 195, 'bass'))
    out_hi = [m for m in treble | bass | loopn if m > kb_lo + 47]
    if out_hi:
        o.append(f'<polygon points="630,228 637,236 630,243" fill="{T["loop"]}"/>')
    for octv in range(4):
        x = 12 + 22 * 7 * octv
        n = kb_lo // 12 - 1 + octv
        o.append(tx(x + 2, 272, f'C{n}', 'S', 'text' if n == 4 else 'dim'))
    return ''.join(o)

CELLS_ROW1 = [('SOUND', 208), ('PERFORM', 160), ('FX', 144), ('KEY', 128)]
CELLS_ROW2 = [('BASS', 144), ('LOOP', 80), ('BPM', 88), ('VOLUME', 80), ('OPTIONS', 72), ('CH.VOICING', 88), ('BS.VOICING', 88)]

def cell(x, y, w, title, val, det, leg, focus=False, led=False, lock=False, pressed=0.0, active=False,
         bar=None, val_col='text', title_override=None, det_col='text'):
    o = [rc(x, y, w, 72, 'bg'), f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{w - 1}" height="71" fill="none" stroke="{T["line"]}" stroke-width="1"/>']
    t = title_override or title
    if focus:
        o.append(rc(x + 2, y + 2, w - 4, 16, 'focus'))
        o.append(tx(x + 4, y + 2, t, 'S', 'bg', weight='700'))
    else:
        o.append(tx(x + 4, y + 2, t, 'S', 'active' if title_override else 'dim', weight='700'))
    if led:
        o.append(f'<circle cx="{x + w - 9}" cy="{y + 10}" r="3.5" fill="{T["bg"] if focus else T["text"]}"/>')
    if lock:
        o.append(rc(x + w - 46, y + 3, 40, 14, 'active') + tx(x + w - 26, y + 2, 'LOCK', 'S', 'bg', anchor='middle', weight='700'))
    if bar is not None:
        o.append(rc(x + 4, y + 20, round((w - 8) * bar), 22, 'bar'))
    if active:
        o.append(rc(x + 2, y + 18, w - 4, 24, 'active'))
        val_col = 'bg'
    o.append(tx(x + 4, y + 18, val, 'M', val_col, weight='700'))
    o.append(tx(x + 4, y + 43, det, 'S', det_col))
    o.append(tx(x + 4, y + 60, leg, 'XS', 'dim'))
    if focus:
        o.append(frame(x, y, w, 72, 'focus', 2))
    if pressed:
        o.append(rc(x + 2, y + 2, round((w - 4) * pressed), 3, 'text'))
    return ''.join(o)

def z5_cells(st):
    f = st.get('focus', 'FX')
    pr = st.get('pressed', {})
    tov = st.get('title_override', {})
    data1 = {
        'SOUND': ('03 Analog Flower', 'VA  pluck', 'K1 T1', 'text'),
        'PERFORM': ('Arpeggiate', '16  UP/DOWN', 'K2 T2', 'text'),
        'FX': ('Reverb 04', 'REV4 CHO3 DLY5', 'K3 T3', 'text'),
        'KEY': ('F♯ Minor', 'Trans +3', 'K4 T4', 'active'),
    }
    data2 = {
        'BASS': ('On  03', 'Fifth Organ Bass', 'K5 T5'),
        'LOOP': (st.get('loop_cell', 'Play'), st.get('loop_det', 'bar 2/4'), 'K6 T6 Rec'),
        'BPM': ('120', 'Beat 03', 'K7 T7 Play'),
        'VOLUME': ('72', 'Bass 70', 'K8 T8'),
        'OPTIONS': ('Chord', 'Simple', 'm2 T9 SEL'),
        'CH.VOICING': ('049', 'C♯3 Oct', 'M'),
        'BS.VOICING': ('37', 'C♯2', 'm1 Y'),
    }
    o = []
    x = 0
    for nm, w in CELLS_ROW1:
        v, d, l, dc = data1[nm]
        o.append(cell(x, 288, w, nm, v, d, l, focus=(nm == f), led=(nm == 'KEY'), lock=(nm == 'PERFORM'),
                      pressed=pr.get(nm, 0), title_override=tov.get(nm), det_col=dc))
        x += w
    x = 0
    for nm, w in CELLS_ROW2:
        v, d, l = data2[nm]
        bar = {'VOLUME': 0.72, 'CH.VOICING': 0.5, 'BS.VOICING': 0.45}.get(nm)
        o.append(cell(x, 360, w, nm, v, d, l, focus=(nm == f), led=(nm == 'BASS'), pressed=pr.get(nm, 0), bar=bar))
        x += w
    return ''.join(o)

def z5_list(st):
    o = [rc(0, 288, 640, 144, 'bg'), rc(0, 288, 640, 24, 'panel')]
    o.append(tx(8, 292, st['list_title'], 'S', 'text', weight='700'))
    o.append(tx(632, 292, st['list_pos'], 'S', 'dim', anchor='end'))
    for i, (num, lab, info, mark) in enumerate(st['list_rows']):
        y = 312 + 24 * i
        sel = (i == 2)
        if sel:
            o.append(rc(0, y, 634, 24, 'focus'))
        col = 'bg' if sel else 'text'
        if num:
            o.append(tx(16, y, num, 'M', col, weight='700' if sel else '400'))
        o.append(tx(64 if num else 16, y, lab, 'M', col, weight='700' if sel else '400'))
        if info:
            o.append(tx(448, y + 4, info, 'S', 'bg' if sel else 'dim'))
        if mark:
            o.append(tx(616, y, mark, 'M', col))
    o.append(rc(636, 312, 3, 120, 'bar') + rc(636, 318, 3, 14, 'dim'))
    return ''.join(o)

def legend_row(x, y, items):
    o = []
    cx = x
    for key, fn in items:
        if key:
            w = len(key) * FS['S'] * 0.55 + 4
            o.append(rc(round(cx), y, round(w), 16, 'dim') + tx(round(cx) + 2, y, key, 'S', 'bg', weight='700'))
            cx += w + 4
        o.append(tx(round(cx), y, fn, 'S', 'text'))
        cx += len(fn) * FS['S'] * 0.55 + 10
    return ''.join(o)

def z6(st):
    o = [rc(0, 432, 640, 48, 'bg')]
    mode = st.get('z6', 'gioco')
    if mode == 'gioco':
        o.append(legend_row(6, 436, [('L1 R1', 'focus'), ('✚', 'turn'), ('A', 'press'), ('B', 'back'), ('X', 'push'), ('Y', 'bs.voicing'), ('SEL', 'opt'), ('START', 'bpm')]))
        o.append(legend_row(6, 456, [('Rec', 'loop'), ('Stop', 'pause'), ('T', 'press'), ('T+K', 'press&turn'), ('M', 'voicing'), ('m1', 'bs.voic'), ('m2', 'list')]))
    elif mode == 'lista':
        o.append(legend_row(6, 436, [('✚ ▲▼', 'scroll'), ('A', 'select'), ('B', 'back'), ('MENU', 'menu')]))
        o.append(legend_row(6, 456, [('m2', 'scroll'), ('m2 press', 'select'), ('T10', 'back'), ('T11', 'menu'), ('« » joy ▲▼', 'scroll')]))
    elif mode == 'tk':
        o.append(tx(6, 436, 'T4 KEY held: turn K4 = Transpose   release = Key on/off', 'S', 'active', weight='700'))
        o.append(legend_row(6, 456, [('Rec', 'loop'), ('Stop', 'pause'), ('T', 'press'), ('T+K', 'press&turn'), ('M', 'voicing'), ('m1', 'bs.voic'), ('m2', 'list')]))
    elif mode == 'transpose':
        o.append(rc(0, 434, 640, 44, 'active'))
        o.append(tx(8, 442, 'Transpose', 'M', 'bg'))
        o.append(tx(150, 438, '+3', 'L', 'bg', weight='700'))
    elif mode == 'pocket':
        o.append(legend_row(6, 436, [('L-stick', 'note'), ('A', 'play'), ('L2 L1 R1 R2', 'Dim Min Maj Sus'), ('✚', '6 m7 M7 9')]))
        o.append(tx(6, 456, 'No MPK: Flip keys only.  MENU > Pocket Mode to play without MPK', 'S', 'dim', size=13.4))
    return ''.join(o)

def plancia(st, width='100%'):
    o = [f'<svg viewBox="0 0 640 480" width="{width}" xmlns="http://www.w3.org/2000/svg" style="display:block;border-radius:6px">',
         rc(0, 0, 640, 480, 'bg')]
    o.append(z1(st)); o.append(z2(st)); o.append(z3(st)); o.append(z4(st))
    o.append(z5_list(st) if st.get('list_title') else z5_cells(st))
    o.append(z6(st))
    for y in (24, 184, 288, 432):
        o.append(rc(0, y, 640, 1, 'line'))
    o.append(rc(400, 24, 1, 160, 'line'))
    o.append('</svg>')
    return ''.join(o)

STATI = {
    'principale': dict(focus='FX', trans='Trans +3'),
    'lista': dict(focus='SOUND', z6='lista', trans='Trans +3', list_title='SOUND', list_pos='3/76',
                  list_rows=[('01', 'Nectar EP', 'RP  piano elettrico', ''), ('02', 'Ghost', 'VA  pad', ''),
                             ('03', 'Analog Flower', 'VA  pluck', '✓'), ('04', 'Cherry Blossom', 'VA  pad', ''),
                             ('05', 'Eraserhead', 'FM  organo', '')]),
    'push_rec': dict(focus='KEY', z6='tk', trans='Trans +3', loop='rec', loop_cell='Rec', loop_det='bar 3/4',
                     pressed={'KEY': 0.6}, beat=2, loop_focus=True),
    'transpose': dict(focus='KEY', z6='transpose', trans='Trans +3', title_override={'KEY': 'TRANSPOSE'}, pressed={'KEY': 1.0}),
    'tascabile': dict(mpk=False, pad=False, pocket=True, z6='pocket', focus='CH.VOICING', pocket_pc=1, ps='SIMPLE  STICK C♯',
                      loopn=[], loop='play'),
}

def plancia_svg(stato, width='100%'):
    return plancia(STATI[stato], width)


def plancia_img(nome, width='100%'):
    """Fotogramma vero della plancia, scritto da stame-render --scene (tema Giorno, 18/10/2026) in img/."""
    import base64
    import os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img', nome + '.png')
    data = base64.b64encode(open(p, 'rb').read()).decode('ascii')
    return (f'<img src="data:image/png;base64,{data}" style="width:{width};image-rendering:pixelated;'
            f'display:block;border-radius:1.5mm" alt="plancia: {nome}">')

# ---------------------------------------------------------------- pagine del PDF

def _zone_note(n, title, body):
    return (f'<div style="display:flex;gap:2.5mm;margin-bottom:2mm"><div style="flex:0 0 7mm;height:7mm;border-radius:1.5mm;'
            f'background:#1a1a1a;color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center;font-size:8.5pt">{n}</div>'
            f'<div><b>{title}</b><br><span style="font-size:8.2pt">{body}</span></div></div>')

def _p2():
    notes = ''.join([
        _zone_note('Z1', 'Testata · 640×24', 'Vuota quando tutto va bene: solo la batteria. Si accende in rosso per NO MPK, clip, xrun o batteria scarica. In Geek Out torna la barra completa: MIDI, voci, CPU, livelli.'),
        _zone_note('Z2', 'Accordo · 416×216', 'Tonalità e transpose; il <b>nome dell\'accordo</b> a punti (Matrice, lettera alta 98 px), con i punti spenti visibili: l\'accordo in acqua, il basso dopo la barra in ambra, come i tasti accesi. Note, intervalli, Play Style e cartellino di Linneo stanno in Geek Out.'),
        _zone_note('Z3', 'Tempo e loop · 224×216', 'BPM a sette segmenti alti 50 px e un riquadro per movimento. Il looper compare solo quando lavora: stato, battuta, barra a celle, menu a tre voci; cornice rossa mentre registra.'),
        _zone_note('Z4', 'Tastiera · 640×144', '4 ottave che seguono le finestre: treble, basso e loop (striscia viola) sui tasti. I puntini sono i granelli di polline: le note della tonalità. Girando un voicing compaiono sopra i <b>filamenti</b> con le antere.'),
        _zone_note('Z5', 'Comandi · a richiesta', 'Con L1/R1, croce, A o X della Flip, al posto della tastiera: gli 11 controlli dell\'originale con fuoco, LED, LOCK e legenda. Si chiude da sola dopo 5 s o con B. Qui si aprono anche liste e menu.'),
        _zone_note('Z6', 'Banda · 640×96', 'Il <b>controllo appena toccato</b>, in grande, con un segno a sinistra nel colore delle evidenze: è l\'overlay dell\'originale. A riposo, il suono. Avvisi e richiesta della tonalità passano davanti. I nomi dei comandi sono incisi sulla mascherina, non qui.'),
    ])
    return f"""
<h2>La plancia sulla Flip</h2>
<p class="sub">Schermo 640×480, tema Giorno (un LCD riflettente, quello con cui Stame parte). <b>Plancia calma</b>: mentre si suona, quattro cose leggibili a un braccio; i comandi e il dettaglio a richiesta. Stato d'esempio: Re maggiore settima con il basso, looper in riproduzione con le note registrate (viola), MPK e macro pad collegati.</p>
<div style="display:flex;gap:7mm">
 <div style="flex:0 0 168mm">{plancia_img('principale')}
  <div class="muted" style="font-size:7.6pt;margin-top:1.2mm">Fotogramma vero del renderer della plancia (<code>stame-render --scene</code>, 18/10/2026), lo stesso codice che gira sulla Flip. Identità: <code>docs/identita/README.md</code>; requisiti: <code>30-interfaccia.md</code> §4.</div>
 </div>
 <div style="flex:1">{notes}</div>
</div>
"""

def _p3():
    def fig(stato, cap):
        return f'<div style="flex:1;min-width:0">{plancia_img(stato)}<div style="font-size:8pt;margin-top:1.2mm">{cap}</div></div>'
    return f"""
<h2>La plancia in altri stati</h2>
<p class="sub">La banda risponde a ciò che tocchi; liste, menu e pagina dei comandi prendono il posto della tastiera. Accordo e tempo non si muovono mai. Fotogrammi veri della vetrina.</p>
<div style="display:flex;gap:6mm;margin-bottom:3mm">
 {fig('tocco', '<b>Hai appena girato FX</b> (K3 della MPK). La banda mostra «REVERB 04» in grande per 3,4 s, con il segno a sinistra, poi torna al suono.')}
 {fig('comandi', '<b>Pagina dei comandi</b> (T15 del pad, o L1/R1 della Flip): le 11 celle al posto della tastiera, il fuoco in verde su Key; FX appena girato, acceso nella sua cella e in grande nella banda.')}
 {fig('lista', '<b>Lista dei suoni</b> (SHIFT + K1, oppure fuoco su Sound + A): la voce scelta in negativo, la spunta segna il suono attivo; si scorre con la manopola di navigazione.')}
</div>
<div style="display:flex;gap:6mm">
 {fig('rec', '<b>Registrazione del loop.</b> Cornice rossa sulla zona del tempo, barra a celle rossa, menu a tre voci.')}
 {fig('transpose', '<b>Funzione secondaria</b> (premi e gira Key: SHIFT + K4 girata): etichetta in negativo, «Trans +3» in alto; la tastiera e il nome dell’accordo seguono il transpose.')}
 {fig('notte', '<b>Tema Notte</b> (MENU › Theme › Dark): un VFD, vetro scuro e fosfori; stessi ruoli e stesse forme del tema Giorno.')}
</div>
"""

PLANCIA_PAGINE = [_p2(), _p3()]
