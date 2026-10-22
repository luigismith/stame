"""hardware.py — i disegni dei comandi hardware per il manuale e il prontuario: la postazione, la MPK
mini IV, il macro pad e la Flip, in SVG in docs/manuale/img/ (Luigi, 19/10/2026: «nel manuale ci sono
solo gli screenshot, invece devono esserci anche le immagini relative ai comandi hardware»; «anche il
prontuario DEVE essere illustrato»).

Uso: python -I docs/disegni/sorgenti/hardware.py

Le misure vengono da hardware/case/misure.py (i controlli della MK4 rimisurati il 17/10, il pad dalle
foto del 18/10); la Flip è schematica. I nomi dei comandi sono quelli del manuale (§7, §8, §9.2) e del
prontuario: se cambia la mappa si cambia qui e si rigenera. I colori sono quelli del tema Giorno
(docs/identita/README.md): acqua = suono e accordi, ambra = tempo e batteria, viola = loop, verde =
navigazione, liste e stati di Stame, ocra = Hold, Scene e PUSH, rosso = Panic, grigio = quello che
Stame ignora.
"""
import os
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.normpath(os.path.join(QUI, '..', '..', '..', 'hardware', 'case'))
sys.path.insert(0, CASE)
import misure as M                  # noqa: E402
from genera import COPRITASTI       # noqa: E402  (le etichette dei tasti del pad, le stesse del case)

OUT = os.path.normpath(os.path.join(QUI, '..', '..', 'manuale', 'img'))
FONT = "Inter, 'Segoe UI', Helvetica, Arial, sans-serif"
CARTA, INK, DIM, GHOST = '#F7F6F1', '#141B18', '#424C47', '#879180'
CORPO, PANNELLO, CHIARO = '#2E3330', '#3B403D', '#E8EBE4'
FAM = {                              # famiglia: (tratto e testo, fondo)
    'suono': ('#005A51', '#CFE4E0'),
    'tempo': ('#853A00', '#F2DCCB'),
    'loop':  ('#4A2894', '#DFD5F1'),
    'nav':   ('#285C00', '#D8E5CA'),
    'stato': ('#634A00', '#EEE3C4'),
    'warn':  ('#9E160C', '#F3D3CF'),
    'off':   ('#879180', '#E9EBE4'),
}


# ---------------------------------------------------------------- primitive

def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def tx(x, y, s, size=3.4, col=INK, anchor='middle', weight='400', italic=False, lh=1.18):
    """testo di una o più righe (\\n), centrato in verticale su y"""
    righe = s.split('\n')
    st = ' font-style="italic"' if italic else ''
    o = []
    for i, r in enumerate(righe):
        dy = (i - (len(righe) - 1) / 2) * size * lh
        o.append(f'<text x="{x:.2f}" y="{y + dy:.2f}" font-size="{size}" fill="{col}" text-anchor="{anchor}" '
                 f'font-weight="{weight}" dominant-baseline="central"{st}>{esc(r)}</text>')
    return ''.join(o)


def rc(x, y, w, h, fam=None, rx=1.5, sw=0.5, fill=None, stroke=None):
    f = fill or (FAM[fam][1] if fam else 'none')
    s = stroke or (FAM[fam][0] if fam else 'none')
    return (f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{rx}" fill="{f}" '
            f'stroke="{s}" stroke-width="{sw}"/>')


def ci(cx, cy, r, fam=None, sw=0.6, fill=None, stroke=None):
    f = fill or (FAM[fam][1] if fam else 'none')
    s = stroke or (FAM[fam][0] if fam else 'none')
    return f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{f}" stroke="{s}" stroke-width="{sw}"/>'


def ln(x1, y1, x2, y2, col=GHOST, sw=0.35):
    return f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{col}" stroke-width="{sw}"/>'


def legenda(x, y, voci, size=3.0):
    """chip colorati in fila: voci = [(famiglia, testo)]"""
    o = []
    for fam, testo in voci:
        o.append(rc(x, y - size * 0.6, size * 1.2, size * 1.2, fam, rx=0.6, sw=0.4))
        o.append(tx(x + size * 1.8, y, testo, size, col=DIM, anchor='start'))
        x += size * 1.8 + len(testo) * size * 0.52 + size * 2.4
    return ''.join(o)


def svg(w, h, corpo):
    """in millimetri; width e height in px (× 2,6) danno all'immagine una misura propria nelle pagine"""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.1f} {h:.1f}" width="{w * 2.6:.0f}" '
            f'height="{h * 2.6:.0f}" font-family="{FONT}">\n'
            f'<rect x="0" y="0" width="{w:.1f}" height="{h:.1f}" fill="{CARTA}"/>\n' + '\n'.join(corpo) + '\n</svg>\n')


# ---------------------------------------------------------------- MPK mini IV (manuale §8)

PAD_A = {'PAD5': 'Dim', 'PAD6': 'Min', 'PAD7': 'Maj', 'PAD8': 'Sus', 'PAD1': '6', 'PAD2': 'm7', 'PAD3': 'M7', 'PAD4': '9'}
PAD_B = {'PAD1': 'cassa', 'PAD2': 'rullante', 'PAD3': 'rimshot', 'PAD4': 'battimani',
         'PAD5': 'charleston\nchiuso', 'PAD6': 'charleston\naperto', 'PAD7': 'tom basso', 'PAD8': 'piatto'}
KNOB = {'K1': ('Sound', 'suono'), 'K2': ('Perform', 'suono'), 'K3': ('FX', 'suono'), 'K4': ('Key', 'suono'),
        'K5': ('Bass', 'suono'), 'K6': ('Loop', 'loop'), 'K7': ('BPM', 'tempo'), 'K8': ('Volume', 'suono')}
TRASPORTO = {'UNDO': ('UNDO', 'Undo', 'loop'), 'LOOP': ('LOOP', 'Pausa', 'loop'), 'PLAY': ('STOP/PLAY', 'Beat', 'tempo'),
             'REC': ('REC', 'Loop REC', 'loop'), 'DUB': ('⊕', 'Overdub', 'loop')}
PULSANTI = {'MINUS': ('−', 'Back', 'nav'), 'PLUS': ('+', 'Menu', 'nav'), 'SHIFT': ('SHIFT', 'PUSH', 'stato'),
            'BANK': ('BANK', 'A · B', 'nav'), 'DAW': ('DAW', '', 'off'), 'OCT-': ('OCT−', '', 'off'),
            'OCT+': ('OCT+', '', 'off'), 'ARP': ('ARP', '', 'off'), 'LATCH': ('LATCH', '', 'off'),
            'NREP': ('N.REP', '', 'off'), 'TAP': ('TAP', '', 'off')}
NOTE = ['Do', 'Re', 'Mi', 'Fa', 'Sol', 'La', 'Si']


def mk4():
    W, D = M.MK4['w'], M.MK4['d']
    X0, Y0 = 6.0, 8.0
    o = [rc(X0, Y0, W, D, rx=5, sw=0.6, fill=CORPO, stroke='#1E2220'),
         rc(X0 + 2, Y0 + 2, W - 4, M.MK4_KEYBED_Y - 6, rx=3, fill=PANNELLO, stroke='none'),
         tx(X0 + 40, Y0 + 7, 'MPK mini IV · preset DAW', 3.6, col=CHIARO, weight='600')]

    def at(n):
        x, y, _ = M.MK4_CTRL[n]
        return X0 + x, Y0 + y

    # ruote
    for n, lab in (('PITCH', 'bend'), ('MOD', 'modulazione')):
        x, y = at(n)
        w, h = M.FORO['w'][:2]
        o.append(rc(x - w / 2, y - h / 2, w, h, 'suono', rx=3, sw=0.6))
        o.append(rc(x - 2, y - h / 2 + 3, 4, h - 6, rx=2, fill=FAM['suono'][0], stroke='none'))
        o.append(tx(x, y + h / 2 + 4.0, lab, 2.9, col=CHIARO))
    # pad: il banco A in grande (accordi), il banco B in piccolo (batteria)
    s = M.FORO['p'][0]
    for n in range(1, 9):
        k = f'PAD{n}'
        x, y = at(k)
        o.append(rc(x - s / 2, y - s / 2, s, s, 'suono', rx=2.5, sw=0.7))
        o.append(tx(x, y - 4.0, PAD_A[k], 7.0, col=FAM['suono'][0], weight='700'))
        o.append(tx(x, y + 6.2, PAD_B[k], 2.9, col=FAM['tempo'][0], lh=1.1))
        o.append(tx(x - s / 2 + 2.0, y - s / 2 + 2.4, str(n), 2.3, col=GHOST, anchor='start'))
    o.append(tx(X0 + 130.6, Y0 + 63.8, 'banco A (in grande): accordi, tipi sopra ed estensioni sotto · banco B (in piccolo): batteria',
                2.6, col=CHIARO))
    # pulsanti
    bw, bh = M.FORO['b'][:2]
    for n, (lab, fn, fam) in PULSANTI.items():
        x, y = at(n)
        o.append(rc(x - bw / 2, y - bh / 2, bw, bh, fam, rx=1.5, sw=0.6))
        if fn:
            o.append(tx(x, y - 2.3, lab, 2.6, col=DIM, weight='600'))
            o.append(tx(x, y + 2.4, fn, 3.0 if len(fn) < 6 else 2.7, col=FAM[fam][0], weight='700'))
        else:
            o.append(tx(x, y, lab, 2.6, col=GHOST))
    # display ed encoder di navigazione
    x, y = at('DISP')
    dw, dh = M.FORO['d'][:2]
    o.append(rc(x - dw / 2, y - dh / 2, dw, dh, rx=1, fill='#101412', stroke='#555555'))
    x, y = at('NAV')
    r = M.FORO['e'][0] / 2
    o.append(ci(x, y, r, 'nav', sw=0.8))
    o.append(tx(x, y, 'NAV', 3.6, col=FAM['nav'][0], weight='700'))
    o.append(tx(x, y + r + 4.2, 'gira: liste e fuoco · premi: conferma', 2.4, col=CHIARO))
    # manopole K1…K8
    r = M.FORO['k'][0] / 2
    for n, (lab, fam) in KNOB.items():
        x, y = at(n)
        o.append(ci(x, y, r, fam, sw=0.8))
        o.append(tx(x, y, lab, 4.0 if len(lab) < 7 else 3.5, col=FAM[fam][0], weight='700'))
        o.append(tx(x, y + r + 3.2, n, 2.5, col=CHIARO))
    # trasporto
    for n, (lab, fn, fam) in TRASPORTO.items():
        x, y = at(n)
        o.append(rc(x - bw / 2, y - bh / 2, bw, bh, fam, rx=1.5, sw=0.6))
        o.append(tx(x, y - 2.3, lab, 2.3 if len(lab) > 4 else 2.6, col=DIM, weight='600'))
        o.append(tx(x, y + 2.4, fn, 2.7 if len(fn) > 6 else 3.0, col=FAM[fam][0], weight='700'))
    o.append(tx(X0 + 294, Y0 + 88.8, 'SHIFT + UNDO = Clear · SHIFT + STOP/PLAY = Panic · SHIFT tenuto + K toccata = «premi»',
                2.4, col=CHIARO))
    # tastiera: 15 tasti bianchi e 10 neri, due ottave, fra le due guance; conta solo il nome della nota
    g = M.MK4['guancia']
    kx, ky = X0 + g + 1, Y0 + M.MK4_KEYBED_Y
    kw, kh = (W - 2 * g - 2) / 15, D - M.MK4_KEYBED_Y - 4.5
    for x in (X0 + 1, X0 + W - g):
        o.append(rc(x, ky, g - 1, D - M.MK4_KEYBED_Y - 1, rx=1.5, fill=PANNELLO, stroke='none'))
    for i in range(15):
        o.append(rc(kx + i * kw, ky, kw - 0.5, kh, rx=1.2, fill='#F4F5EF', stroke='#9AA091', sw=0.4))
        o.append(tx(kx + i * kw + kw / 2, ky + kh - 5, NOTE[i % 7], 3.6, col=DIM))
    neri = [1, 1, 0, 1, 1, 1, 0]
    for i in range(14):
        if neri[i % 7]:
            o.append(rc(kx + (i + 1) * kw - 5.5, ky, 11, kh * 0.6, rx=1, fill='#252D29', stroke='none'))
    o.append(rc(kx + 30, ky + kh * 0.63, 15 * kw - 60, 11, rx=2, fill=FAM['suono'][1], stroke=FAM['suono'][0], sw=0.5))
    o.append(tx(X0 + W / 2, ky + kh * 0.63 + 5.5,
                'qualunque tasto: la fondamentale dell\'accordo · conta il nome della nota, non l\'ottava',
                4.0, col=FAM['suono'][0], weight='600'))
    o.append(legenda(X0, Y0 + D + 8, [('suono', 'suono e accordi'), ('tempo', 'tempo e batteria'), ('loop', 'loop'),
                                       ('nav', 'navigazione e liste'), ('stato', 'PUSH: SHIFT tenuto'),
                                       ('off', 'interni della MPK: Stame li ignora')], 3.0))
    return svg(W + 12, Y0 + D + 16, o)


# ---------------------------------------------------------------- macro pad (manuale §7)

TASTO_FAM = ['stato', 'tempo', 'tempo', 'tempo', 'nav',
             'stato', 'stato', 'stato', 'stato', 'nav',
             'nav', 'loop', 'tempo', 'warn', 'nav']
NEGATIVI = {4, 9, 14}                # T13, T14, T15: gli stati di Stame, in negativo come le etichette


def pad():
    W, D = M.PAD['w'], M.PAD['d']
    X0, Y0 = 6.0, 15.0
    mx, my, mr = M.PAD_KNOB['M']
    lobo = M.PAD_LOBO['lungo']
    o = [rc(X0 + W - lobo, Y0 + D - 3, lobo, 3 + M.PAD_LOBO['sporge'], rx=M.PAD_R, fill='#E3E6DF', stroke='#8E968A', sw=0.6),
         rc(X0, Y0, W, D, rx=M.PAD_R, sw=0.6, fill='#E3E6DF', stroke='#8E968A'),
         rc(X0 + W - lobo + 0.4, Y0 + D - 1.2, lobo - M.PAD_R, 1.8, fill='#E3E6DF', stroke='none')]
    lato = 18.0
    for k in range(15):
        r, c = divmod(k, 5)
        x = X0 + M.PAD['k0'][0] + c * M.PAD['pitch_x']
        y = Y0 + M.PAD['k0'][1] + r * M.PAD['pitch_y']
        fam = TASTO_FAM[k]
        if k in NEGATIVI:
            o.append(rc(x - lato / 2, y - lato / 2, lato, lato, rx=2, fill=INK, stroke=INK, sw=0.6))
            col, colnum = CARTA, '#B9C0B3'
        else:
            o.append(rc(x - lato / 2, y - lato / 2, lato, lato, fam, rx=2, sw=0.7))
            col, colnum = FAM[fam][0], GHOST
        righe = COPRITASTI[k]
        t = 13 + r if c == 4 else r * 4 + c + 1          # la quinta colonna è T13, T14, T15 (MIDI-120)
        o.append(tx(x, y + 1.0, '\n'.join(righe), 3.4 if len(righe) == 1 else 3.0, col=col, weight='700', lh=1.1))
        o.append(tx(x - lato / 2 + 1.5, y - lato / 2 + 2.2, f'T{t}', 2.2, col=colnum, anchor='start'))
    # manopole
    for n, (x, y, r) in M.PAD_KNOB.items():
        o.append(ci(X0 + x, Y0 + y, r, 'suono', sw=0.8))
        o.append(ci(X0 + x, Y0 + y, r - 2.2, stroke=FAM['suono'][0], sw=0.3, fill='none'))
        o.append(tx(X0 + x, Y0 + y, n, 5.0 if n == 'M' else 3.8, col=FAM['suono'][0], weight='700'))
    x1, y1, r1 = M.PAD_KNOB['m1']
    x2, y2, r2 = M.PAD_KNOB['m2']
    o.append(tx(X0 + x1, Y0 - 7.5, 'Bass Voicing\npremi: Mod', 2.8, col=FAM['suono'][0], lh=1.15))
    o.append(tx(X0 + x2, Y0 - 7.5, 'volume del Beat\npremi e gira: basso', 2.8, col=FAM['suono'][0], lh=1.15))
    o.append(ln(X0 + x1, Y0 - 3.6, X0 + x1, Y0 + y1 - r1))
    o.append(ln(X0 + x2, Y0 - 3.6, X0 + x2, Y0 + y2 - r2))
    o.append(tx(X0 + mx, Y0 + my - mr - 6.5, 'Chord Voicing\npremi: Split/Octave', 2.8, col=FAM['suono'][0], lh=1.15))
    o.append(ln(X0 + mx, Y0 + my - mr - 2.6, X0 + mx, Y0 + my - mr))
    # note sotto il pad
    yb = Y0 + D + M.PAD_LOBO['sporge'] + 7
    note = ['DROP (T13, tenuto): Beat, batteria del loop e basso tacciono; al rilascio rientrano sul battito. Accordi, metronomo e colpi dal vivo suonano.',
            'DRUMS (T11) acceso, modo crea: M densità · m1 stile · m2 variazione; premute: play e stop, la parte di M, idea nuova. Ripremi T11: il loop resta.',
            'AMBIENT (T14): Stame suona quasi da solo. M note sparse · m1 atmosfera · m2 movimento; premute: pausa, Mod, idea nuova. Un tuo accordo lo zittisce.',
            'Scene: tocco = richiama, tenuto 1 s = salva. Panic (T12) scatta dopo 1 s, tenuto 3 s = Reset. T15: la pagina dei comandi. Geek Out: Options › View.']
    for i, n in enumerate(note):
        o.append(tx(X0, yb + i * 4.2, n, 2.45, col=DIM, anchor='start'))
    yl = yb + len(note) * 4.2 + 2.5
    o.append(legenda(X0, yl, [('suono', 'suono e voicing'), ('tempo', 'tempo e batteria'), ('loop', 'loop'),
                              ('nav', 'navigazione, viste e stati'), ('stato', 'Hold e scene'), ('warn', 'Panic')], 2.8))
    return svg(W + 12, yl + 7, o)


# ---------------------------------------------------------------- Flip (manuale §9.2), schematica

def flip():
    W, D = M.FLIP['w'], M.FLIP['d']
    X0, Y0 = 60.0, 20.0
    nav, suono, tempo, stato = FAM['nav'][0], FAM['suono'][0], FAM['tempo'][0], FAM['stato'][0]
    o = [rc(X0, Y0, W, D, rx=8, sw=0.6, fill='#E6E8E3', stroke='#8E968A'),
         rc(X0 + 27, Y0 - 2.5, W - 54, 3.5, rx=1.5, fill='#C9CFC0', stroke='none'),
         tx(X0 + W / 2, Y0 - 16.0, 'cerniera: di là c\'è lo schermo, verso chi suona', 2.5, col=DIM, italic=True)]
    # dorsali
    for x, nm, fn, fam, dy in ((X0 + 2, 'L2', 'Tap tempo', 'tempo', -10.5), (X0 + 2, 'L1', 'fuoco −', 'nav', -5.5),
                               (X0 + W - 24, 'R2', 'Fill (tenuto)', 'tempo', -10.5), (X0 + W - 24, 'R1', 'fuoco +', 'nav', -5.5)):
        o.append(rc(x, Y0 + dy, 22, 4.4, fam, rx=1.5, sw=0.5))
        o.append(tx(x + 11, Y0 + dy + 2.2, f'{nm}  {fn}', 2.5, col=FAM[fam][0], weight='600'))
    # croce
    cx, cy = X0 + 22, Y0 + 30
    o.append(rc(cx - 4.5, cy - 13, 9, 26, 'nav', rx=1.5))
    o.append(rc(cx - 13, cy - 4.5, 26, 9, 'nav', rx=1.5))
    o.append(rc(cx - 4.3, cy - 4.3, 8.6, 8.6, fill=FAM['nav'][1], stroke='none', rx=0))
    for dx, dy, ch in ((0, -8.5, '▲'), (0, 8.5, '▼'), (-8.5, 0, '◀'), (8.5, 0, '▶')):
        o.append(tx(cx + dx, cy + dy, ch, 3.0, col=nav))
    # A B X Y
    ax, ay = X0 + 62, Y0 + 30
    for dx, dy, nm, fam in ((0, -9, 'X', 'stato'), (9, 0, 'A', 'nav'), (0, 9, 'B', 'nav'), (-9, 0, 'Y', 'stato')):
        o.append(ci(ax + dx, ay + dy, 4.3, fam, sw=0.6))
        o.append(tx(ax + dx, ay + dy, nm, 3.6, col=FAM[fam][0], weight='700'))
    # levette con il clic
    for x, nm in ((X0 + 22, 'L'), (X0 + 62, 'R')):
        o.append(ci(x, Y0 + 58, 7.5, 'suono', sw=0.7))
        o.append(ci(x, Y0 + 58, 4.2, fill='#FFFFFF', stroke=suono, sw=0.4))
        o.append(tx(x, Y0 + 58, nm, 3.2, col=suono, weight='700'))
    # SELECT, START, MENU
    for x, y, nm, fam in ((X0 + 33, Y0 + 72, 'SELECT', 'nav'), (X0 + 51, Y0 + 72, 'START', 'tempo'), (X0 + 42, Y0 + 47, 'MENU', 'nav')):
        o.append(rc(x - 7.5, y - 2.6, 15, 5.2, fam, rx=2.6, sw=0.5))
        o.append(tx(x, y, nm, 2.4, col=FAM[fam][0], weight='700'))
    # didascalie con la linea al comando
    L, R = X0 - 4, X0 + W + 4

    def dida(x, y, testo, px, py, anchor, col=DIM):
        o.append(tx(x, y, testo, 2.8, col=col, anchor=anchor, lh=1.15))
        xa = x + (1.5 if anchor == 'end' else -1.5) if anchor != 'middle' else x
        ya = y if anchor != 'middle' else y - 2.2 - 1.6 * (testo.count('\n'))
        o.append(ln(xa, ya, px, py))

    dida(L, cy, 'croce: gira il controllo con il\nfuoco, o scorre la lista aperta', cx - 13, cy, 'end', nav)
    dida(L, Y0 + 58, 'levetta sinistra: ↔ pitch bend,\n↕ modulazione (torna al centro)\nclic L3: Mod', X0 + 22 - 7.5, Y0 + 58, 'end', suono)
    dida(R, ay - 9, 'X: Hold', ax + 4.3, ay - 9, 'start', stato)
    dida(R, ay + 1, 'A: premi · tenuto: tieni\nA tenuto + croce: premi e gira', ax + 9 + 4.3, ay, 'start', nav)
    dida(R, ay + 11, 'B: indietro', ax + 4.3, ay + 9, 'start', nav)
    o.append(tx(ax - 5.5, ay + 9.2, 'Y: Mod', 2.6, col=stato, weight='600', anchor='end'))
    dida(R, Y0 + 47, 'MENU: il menu della piattaforma\ntenuto 2 s: esce da Stame', X0 + 42 + 7.5, Y0 + 47, 'start', nav)
    dida(R, Y0 + 58, 'levetta destra: ↕ Chord Voicing,\n↔ Bass Voicing (tenuta: ripete)\nclic R3: Split/Octave', X0 + 62 + 7.5, Y0 + 58, 'start', suono)
    yb = Y0 + D + 6
    dida(X0 + 26, yb, 'SELECT: Options', X0 + 33, Y0 + 72 + 2.6, 'middle', nav)
    dida(X0 + 74, yb, 'START: Beat on/off · con la MK4: Fill tenuto', X0 + 51, Y0 + 72 + 2.6, 'middle', tempo)
    o.append(tx(X0 + W / 2, yb + 8, 'i tasti della Flip funzionano sempre, qualunque cosa sia collegata · disposizione schematica',
                2.4, col=GHOST, italic=True))
    return svg(2 * X0 + W, yb + 13, o)


# ---------------------------------------------------------------- la postazione (manuale §1), dall'alto

def postazione():
    W, D = M.MK4['w'], M.MK4['d']
    mx, my = 20.0, 76.0
    o = [rc(mx, my, W, D, rx=5, fill=CORPO, stroke='#1E2220', sw=0.8),
         rc(mx + M.MK4['guancia'] + 1, my + M.MK4_KEYBED_Y, W - 2 * M.MK4['guancia'] - 2, D - M.MK4_KEYBED_Y - 4.5, rx=2,
            fill='#F4F5EF', stroke='none'),
         tx(mx + W / 2, my + 44, 'MPK mini IV · preset DAW', 12, col=CHIARO, weight='700'),
         tx(mx + W / 2, my + 62, 'pad e manopole sopra, i tasti davanti', 7.5, col=CHIARO),
         tx(mx + W / 2, my + 146, 'tasti', 8, col=DIM)]
    # il pad, in linea con i tasti, con le manopole a destra
    px, pw, pd = mx + W + 36, M.PAD['w'], M.PAD['d']
    py = my + D - pd
    o.append(rc(px, py, pw, pd, rx=M.PAD_R, fill='#E3E6DF', stroke='#8E968A', sw=0.8))
    o.append(tx(px + pw / 2 - 20, py + pd / 2, 'macro pad', 10, col=INK, weight='700'))
    o.append(tx(px + pw - 22, py + 14, 'm1  m2', 7, col=DIM))
    o.append(tx(px + pw - 31, py + pd - 12, 'M', 8, col=DIM, weight='700'))
    # la Flip dietro il pad, aperta, con lo schermo verso chi suona
    fw, fd = M.FLIP['w'], M.FLIP['d']
    fx, fy = px + pw / 2 - fw / 2, py - 16 - fd
    o.append(rc(fx, fy - 34, fw, 32, rx=4, fill='#CED4C2', stroke='#8E968A', sw=0.8))
    o.append(tx(fx + fw / 2, fy - 18, 'schermo, inclinato', 7, col=DIM))
    o.append(rc(fx, fy, fw, fd, rx=6, fill='#E6E8E3', stroke='#8E968A', sw=0.8))
    o.append(tx(fx + fw / 2, fy + fd / 2, 'Flip, aperta', 9, col=INK, weight='700'))
    # hub e cavi: la MPK ha la USB-C sul retro, il pad pure, la Flip la porta di sopra
    hw, hd = M.HUB['w'], M.HUB['d']
    hx, hy = mx + W - 60, 8.0                        # dietro, fra la MPK e il pad: la zona dei cavi
    o.append(rc(hx, hy, hw, hd, rx=3, fill='#D9DECE', stroke='#8E968A', sw=0.8))
    o.append(tx(hx + hw / 2, hy + hd / 2, 'hub USB', 6.5, col=INK, weight='600'))
    gx = mx + W + 18                                 # il corridoio fra la MPK e il pad
    cavi = [f'M{hx + 12:.1f},{hy + hd:.1f} C{hx + 12:.1f},{my - 10:.1f} {mx + M.MK4_CONN_X[0] + 23:.1f},{my - 22:.1f} '
            f'{mx + M.MK4_CONN_X[0] + 23:.1f},{my:.1f}',
            f'M{hx + hw - 20:.1f},{hy + hd:.1f} C{gx:.1f},{hy + hd + 30:.1f} {gx:.1f},{py - 40:.1f} {gx:.1f},{py - 8:.1f} '
            f'S{px - 2:.1f},{py + 10:.1f} {px:.1f},{py + 10:.1f}',
            f'M{hx + hw:.1f},{hy + hd / 2:.1f} C{fx - 10:.1f},{hy + hd / 2:.1f} {fx + fw / 2:.1f},{fy - 60:.1f} '
            f'{fx + fw / 2:.1f},{fy - 34:.1f}']
    for d in cavi:
        o.append(f'<path d="{d}" fill="none" stroke="{DIM}" stroke-width="1.2"/>')
    o.append(tx(mx + 30, hy + 6, 'tre cavi in un hub, e un cavo solo alla porta USB-C di sopra della Flip', 6.5, col=DIM, anchor='start'))
    o.append(tx(mx + 30, hy + 18, '(mai forzare la porta in modalità host)', 6.0, col=DIM, anchor='start', italic=True))
    o.append(tx(mx + W / 2 + 90, my + D + 18, 'chi suona sta davanti ai tasti, con lo sguardo sullo schermo della Flip', 8, col=DIM, italic=True))
    return svg(px + pw + 20, my + D + 32, o)


# ---------------------------------------------------------------- uscita

DISEGNI = {'mk4': mk4, 'pad': pad, 'flip': flip, 'postazione': postazione}

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for nome, f in DISEGNI.items():
        p = os.path.join(OUT, nome + '.svg')
        open(p, 'w', encoding='utf-8', newline='\n').write(f())
        print(f'{p}: {os.path.getsize(p)} byte')
