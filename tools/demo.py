# demo.py — il brano della demo della vetrina: «Acacia», brano originale di Stame.
#
# Scrive src/platform/vetrina/demo_song.c (passi di demo.h) a partire dalla partitura qui sotto e
# controlla che ogni nota singola cada nella finestra del voicing di quel momento (ACC-080).
# Uso: python -I tools/demo.py   (dalla radice del repo)
#
# Il brano si suona come lo suonerebbe una persona sulla plancia: accordi con un dito, Perform,
# basso, Beat, looper con count-in e overdub, cambi di suono, Lock, transpose, voicing e ritardando.
# Registri separati, perché un note-off spegne tutte le voci con quella nota (dsp_note_off):
#   basso 36…47 · loop 48…59 (voicing 24) · riff 60…71 (voicing 36, Split) · strofa 72…83 (voicing 48)
#   · ritornello 78…89 (voicing 54).
import pathlib, re, sys

PPQ, BAR = 96, 384
ORIGIN = 192                     # due battiti di silenzio con il titolo, poi la battuta 1

# ordine dei tipi e delle estensioni di core/acc.h
DIM, MIN, MAJ, SUS = 1, 2, 4, 8
E6, E7MIN, E7MAJ, E9 = 1, 2, 4, 8
TYPE_PCS = {DIM: (0, 3, 6), MIN: (0, 3, 7), MAJ: (0, 4, 7), SUS: (0, 5, 7)}
EXT_PC = {E6: 9, E7MIN: 10, E7MAJ: 11, E9: 2}
QUAL = {
    '': (MAJ, 0), 'm': (MIN, 0), 'sus': (SUS, 0), 'dim': (DIM, 0),
    'maj7': (MAJ, E7MAJ), 'm7': (MIN, E7MIN), '7': (MAJ, E7MIN), '6': (MAJ, E6), 'm6': (MIN, E6),
    'add9': (MAJ, E9), 'madd9': (MIN, E9), 'maj9': (MAJ, E7MAJ | E9), 'm9': (MIN, E7MIN | E9),
    '9': (MAJ, E7MIN | E9), '69': (MAJ, E6 | E9), '7sus': (SUS, E7MIN), 'sus9': (SUS, E9),
}
LETTER = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# suoni, bassi e Beat della vetrina (ordine di SOUNDS[], BASSES[] e BEATS[] in vetrina.c)
GLASS_POLLEN, FERN_PLUCK, DEW_MALLET, SUN_ROOM = 0, 4, 8, 11
WOOD_BASS = 5
FUNK, LOUNGE, HALFTIME = 0, 3, 5
SINGLE_SPLIT, SINGLE_FULL = 0, 1


def midi(name):
    m = re.fullmatch(r'([A-G])([#b]?)(-?\d)', name)
    return 12 * (int(m[3]) + 1) + LETTER[m[1]] + {'#': 1, 'b': -1, '': 0}[m[2]]


def chord(sym):
    m = re.fullmatch(r'([A-G][#b]?)(.*)', sym)
    root = midi(m[1] + '4') % 12
    types, exts = QUAL[m[2]]
    return root, types, exts


def place(pc, w):
    return w + (pc - w) % 12


class Song:
    def __init__(self):
        self.steps = []                  # (tick, ordine, azione, a, b, c, d, commento)
        self.v = 24                      # Chord Voicing (W = v + 24)
        self.single = SINGLE_FULL
        self.lock = False
        self.state_t = 0                 # ultimo cambio di voicing o di note singole
        self.loop = []                   # (tick, comando), per i controlli

    @staticmethod
    def at(bar, beat=1.0):
        return ORIGIN + (bar - 1) * BAR + round((beat - 1) * PPQ)

    # a parità di tick i passi restano nell'ordine in cui sono scritti (il rilascio prima del gesto dopo)
    def add(self, t, act, a=0, b=0, c=0, d=0, note=''):
        self.steps.append((t, len(self.steps), act, a, b, c, d, note))

    # la finestra delle note dipende dall'ultimo cambio: la partitura va scritta in ordine di tempo
    def state(self, t):
        if t < self.state_t:
            sys.exit(f'cambio di stato a {t} prima di {self.state_t}')
        self.state_t = t

    # ---- gesti con uno stato da seguire ----
    def voicing(self, t, v):
        self.state(t)
        self.add(t, 'D_VOICING', c=v, note=f'voicing {v}: finestra da {NAMES[(v + 24) % 12]}')
        self.v = v

    def opt(self, t, name, val):
        self.state(t)
        self.add(t, 'D_OPT', 'ACC_OPT_' + name, val)
        if name == 'VOICING':
            self.v = val
        if name == 'SINGLE_NOTES':
            self.single = val

    def single_toggle(self, t):
        self.state(t)
        self.single = SINGLE_SPLIT if self.single == SINGLE_FULL else SINGLE_FULL
        self.add(t, 'D_PRESS', 'ENC_CHORD_VOICING', note='note singole: ' + ('Split' if self.single == SINGLE_SPLIT else 'Full Octave'))

    def lock_toggle(self, t):
        self.lock = not self.lock
        self.add(t, 'D_HOLD', 'ENC_PERFORM', note='Lock del Perform ' + ('acceso' if self.lock else 'spento'))

    def loop_cmd(self, t, cmd, note):
        self.add(t, 'D_LOOP', 'LOOP_C_' + cmd, note=note)
        self.loop.append((t, cmd))

    # ---- accordi: "battito:Accordo:durata[@vel]" per battuta, battute separate da | ----
    def chords(self, bar0, text, vel=96, early=0):
        ev = []
        for i, bar in enumerate(text.split('|')):
            for tok in bar.split():
                body, _, v = tok.partition('@')
                beat, sym, dur = body.split(':')
                t = self.at(bar0 + i, float(beat))
                ev.append((t, t + round(float(dur) * PPQ) - early, sym, int(v) if v else vel))
        if ev[0][0] < self.state_t:
            sys.exit(f'accordi a {ev[0][0]} prima dell\'ultimo cambio di stato')
        for j, (t, end, sym, v) in enumerate(ev):
            root, types, exts = chord(sym)
            w = self.v + 24
            pcs = set(TYPE_PCS[types]) | {EXT_PC[e] for e in EXT_PC if exts & e}
            notes = sorted(place((root + p) % 12, w) for p in pcs)
            self.add(t, 'D_CHORD', hex(types), hex(exts), root, v,
                     f'{sym}: ' + ' '.join(NAMES[n % 12] + str(n // 12 - 1) for n in notes))
            nxt = ev[j + 1][0] if j + 1 < len(ev) else None
            if nxt is None or nxt > end:
                self.add(end, 'D_OFF')

    # ---- note singole: "battito:Nota:durata[@vel]" ----
    def melody(self, bar0, text, vel=100, gate=1.0):
        ev = []
        for i, bar in enumerate(text.split('|')):
            for tok in bar.split():
                body, _, v = tok.partition('@')
                beat, name, dur = body.split(':')
                t = self.at(bar0 + i, float(beat))
                ev.append((t, t + round(float(dur) * PPQ * gate), name, int(v) if v else vel))
        if ev[0][0] < self.state_t:
            sys.exit(f'note a {ev[0][0]} prima dell\'ultimo cambio di stato')
        w = self.v + 24
        lo = w if self.single == SINGLE_SPLIT else 12 * (w // 12)
        for j, (t, end, name, v) in enumerate(ev):
            n = midi(name)
            if not lo <= n <= lo + 11:
                sys.exit(f'{name} a {t} fuori dalla finestra {lo}…{lo + 11} (voicing {self.v})')
            self.add(t, 'D_CHORD', 0, 0, n % 12, v, name)
            nxt = ev[j + 1][0] if j + 1 < len(ev) else None
            if nxt is None or nxt > end:
                self.add(end, 'D_OFF')


# ======================================================================== il brano
S = Song()
at = Song.at

LOOP = '1:Gmaj7:2@{a} 3:Gmaj7:2@{b} | 1:Asus:2@{a} 3:A:2@{b} | 1:F#m7:2@{a} 3:F#m7:2@{b} | 1:Bm7:2@{a} 3:Bm:2@{b}'

VERSE = ('1:B5:1.5@104 2.5:A5:.5@88 3:F#5:1@98 4:E5:.5@86 4.5:F#5:.5@90 |'
         '1:E5:2@100 3:C#5:.5@90 3.5:D5:.5@84 4:E5:1@94 |'
         '1:A5:1.5@102 2.5:F#5:.5@86 3:E5:1@96 4:C#5:.5@86 4.5:D5:.5@90 |'
         '1:D5:2@98 3:C#5:.5@84 3.5:D5:1.5@92 |'
         '1:B5:1.5@106 2.5:A5:.5@90 3:F#5:1@100 4:E5:.5@88 4.5:F#5:.5@92 |'
         '1:E5:2@100 3:C#5:.5@90 3.5:E5:.5@92 4:A5:1@104 |'
         '1:B5:1.5@110 2.5:A5:.5@94 3:F#5:.5@96 3.5:E5:.5@90 4:C#5:1@94 |'
         '1:D5:3@96')

VERSE2 = ('1:B5:1@100 2:A5:.5@86 2.5:B5:.5@92 3:F#5:1@98 4:E5:.5@86 4.5:F#5:.5@90 |'
          '1:E5:1.5@98 2.5:D5:.5@86 3:C#5:1@94 4:E5:.5@88 4.5:A5:.5@96 |'
          '1:A5:1@100 2:B5:.5@92 2.5:A5:.5@88 3:E5:1@96 4:C#5:.5@86 4.5:D5:.5@90 |'
          '1:D5:1.5@96 2.5:F#5:.5@90 3:E5:.5@86 3.5:D5:1.5@92 |'
          '1:B5:1.5@106 2.5:A5:.5@90 3:F#5:1@98 4:G5:.5@90 4.5:A5:.5@96 |'
          '1:B5:1@108 2:A5:1@96 3:E5:1@94 4:A5:1@102 |'
          '1:B5:1.5@110 2.5:A5:.5@94 3:F#5:.5@96 3.5:E5:.5@90 4:C#5:1@94 |'
          '1:D5:2@96')

RIFF = ('1:B4:.75@100 1.75:A4:.75@84 2.5:F#4:.5@90 3:D4:.5@94 3.5:E4:.5@80 4:F#4:.5@88 4.5:A4:.5@82 |'
        '1:A4:.75@100 1.75:E4:.75@84 2.5:D4:.5@90 3:C#4:.5@94 3.5:E4:.5@80 4:A4:.5@88 4.5:B4:.5@82 |'
        '1:A4:.75@100 1.75:F#4:.75@84 2.5:E4:.5@90 3:C#4:.5@94 3.5:E4:.5@80 4:F#4:.5@88 4.5:A4:.5@82 |'
        '1:F#4:.75@100 1.75:D4:.75@84 2.5:C#4:.5@90 3:D4:.5@94 3.5:F#4:.5@80 4:B4:.5@88 4.5:A4:.5@82')

CHORUS = ('1:D6:1@108 2:C#6:.5@94 2.5:B5:1@100 3.5:A5:1.5@98 |'
          '1.5:B5:.5@90 2:A5:1@96 3:C#6:1.5@104 4.5:E6:.5@100 |'
          '1:E6:1.5@110 2.5:C#6:.5@94 3:A5:1@98 4:B5:.5@90 4.5:A5:.5@88 |'
          '1:F#5:1.5@96 2.5:A5:.5@92 3:B5:2@100 |'
          '1:D6:1@110 2:C#6:.5@96 2.5:B5:1@102 3.5:A5:1@98 4.5:B5:.5@94 |'
          '1:D6:1@104 2:E6:.5@100 2.5:D6:.5@94 3:C#6:1@104 4:E6:1@108 |'
          '1:E6:1.5@114 2.5:D6:.5@98 3:C#6:1@104 4:B5:.5@94 4.5:C#6:.5@98 |'
          '1:D6:2@108 3:C#6:.5@96 3.5:B5:1.5@100')

CHORUS2 = ('1:D6:1@110 2:C#6:.5@96 2.5:B5:1@102 3.5:A5:1.5@100 |'
           '1.5:B5:.5@92 2:A5:1@98 3:C#6:1.5@106 4.5:E6:.5@102 |'
           '1:E6:1.5@112 2.5:C#6:.5@96 3:A5:1@100 4:B5:.5@92 4.5:C#6:.5@96 |'
           '1:D6:1.5@104 2.5:C#6:.5@94 3:B5:2@100 |'
           '1:D6:1@112 2:E6:.5@104 2.5:D6:1@100 3.5:B5:1@96 4.5:D6:.5@100 |'
           '1:E6:2@114 3:C#6:1@104 4:E6:1@110 |'
           '1:E6:1.5@116 2.5:D6:.5@100 3:C#6:1@106 4:B5:.5@96 4.5:C#6:.5@100 |'
           '1:D6:2@110 3:C#6:.5@98 3.5:B5:1.5@104')

# ---- preparazione: titolo, opzioni, tempo e suono dell'alba ----
S.add(0, 'D_TITLE')
S.add(0, 'D_THEME', 'THEME_DARK')
S.add(0, 'D_VIEW', 'VIEW_CHORD')
S.opt(0, 'KEY_ON', 0)                       # note singole vere: Key mode spenta (ACC-080)
S.opt(0, 'BASS_ON', 0)
S.opt(0, 'SINGLE_NOTES', SINGLE_FULL)
S.opt(0, 'BASS_VOICING', 23)
S.opt(0, 'VOICING', 36)
S.add(0, 'D_FOCUS', 'ENC_BPM')
S.add(0, 'D_BPM', c=96, note='96 BPM')
S.add(48, 'D_FOCUS', 'ENC_SOUND')
S.add(48, 'D_SOUND', c=GLASS_POLLEN, note='Glass Pollen, Harp 3')
S.add(120, 'D_FOCUS', 'ENC_FX')
S.add(120, 'D_TURN', 'ENC_FX', 2, note='più riverbero')

# ---- 1–8 Alba: campane in Harp, senza basso né Beat; il voicing riaccende la cascata ----
S.chords(1, '1:Dmaj9:8@84')
S.voicing(at(2), 41)
S.chords(3, '1:Bm9:8@80')
S.voicing(at(4), 36)
S.chords(5, '1:Gmaj9:8@86')
S.voicing(at(6), 43)
S.chords(7, '1:Asus9:2@82 3:A:6@78')
# la lista dei Beat mentre le campane suonano: Lounge
S.add(at(8, 1), 'D_HOLD', 'ENC_BPM', note='lista dei Beat')
for k, b in enumerate((1.5, 2, 2.5)):
    S.add(at(8, b), 'D_TURN', 'ENC_BPM', 1)
S.add(at(8, 3), 'D_PRESS', 'ENC_BPM', note='04 Lounge')
S.add(at(8, 3.5), 'D_BACK')

# ---- 9 count-in: REC, e intanto Dew Mallet in Pattern 13, il basso Wood Bass, il voicing del loop ----
S.loop_cmd(at(9), 'PRESS', 'REC: una battuta di count-in, poi 4 da registrare')
S.add(at(9), 'D_FOCUS', 'ENC_SOUND')
S.add(at(9), 'D_SOUND', c=DEW_MALLET, note='Dew Mallet')
S.add(at(9), 'D_PERF', 'PERF_PATTERN', 13, note='Pattern 13: gruppi di tre sedicesimi')
S.add(at(9, 2), 'D_FOCUS', 'ENC_BASS')
S.add(at(9, 2), 'D_PRESS', 'ENC_BASS', note='basso acceso')
S.add(at(9, 2.5), 'D_BASS', c=WOOD_BASS, note='Wood Bass')
S.voicing(at(9, 3), 24)

# ---- 10–13 registrazione: il giro del loop, IV V iii vi, con il Beat ----
S.add(at(10), 'D_BEATON', 1, note='Beat: Lounge')
S.chords(10, LOOP.format(a=92, b=84), early=24)

# ---- 14–17 il loop suona da solo; poi il Perform si spegne e si blocca per la melodia ----
S.add(at(14), 'D_VIEW', 'VIEW_CHORD_KB')
S.add(at(17, 2), 'D_FOCUS', 'ENC_PERFORM')
S.add(at(17, 2), 'D_PERF', 'PERF_OFF', 0, note='Perform spento')
S.lock_toggle(at(17, 2.5))
S.add(at(17, 3), 'D_FOCUS', 'ENC_CHORD_VOICING')
S.single_toggle(at(17, 3))
S.voicing(at(17, 4), 48)
S.melody(17, '4.5:D5:.5@88')                # levare

# ---- 18–25 strofa ----
S.add(at(18), 'D_VIEW', 'VIEW_NOTES')
S.melody(18, VERSE)

# ---- 26–29 overdub: il riff della kalimba entra nel loop ----
S.voicing(at(25, 4), 36)
S.loop_cmd(at(26), 'OVERDUB', 'overdub')
S.add(at(26), 'D_VIEW', 'VIEW_CHORD')
S.melody(26, RIFF, gate=0.8)
S.loop_cmd(at(30), 'OVERDUB', 'fine dell\'overdub: due strati')

# ---- 30–33 loop e riff da soli ----
S.add(at(30), 'D_VIEW', 'VIEW_GEEK')
S.voicing(at(33, 3), 54)

# ---- 34–41 ritornello: Sun Room, il giorno ----
S.add(at(34), 'D_FOCUS', 'ENC_SOUND')
S.add(at(34), 'D_SOUND', c=SUN_ROOM, note='Sun Room: anche il loop cambia suono (ACC-221)')
S.add(at(34), 'D_THEME', 'THEME_LIGHT')
S.add(at(34), 'D_VIEW', 'VIEW_CHORD')
S.melody(34, CHORUS)

# ---- 42–49 seconda strofa ----
S.voicing(at(42), 48)
S.add(at(42), 'D_VIEW', 'VIEW_KEYBOARD')
S.melody(42, VERSE2)

# ---- 50–57 ponte, la pioggia: loop in pausa, Halftime, Fern Pluck in arpeggio ----
S.lock_toggle(at(49, 3))
S.add(at(49, 3), 'D_HOLD', 'ENC_BPM', note='lista dei Beat')
S.add(at(49, 3.5), 'D_TURN', 'ENC_BPM', 1)
S.add(at(49, 4), 'D_TURN', 'ENC_BPM', 1)
S.add(at(50), 'D_PRESS', 'ENC_BPM', note='06 Halftime')
S.add(at(50), 'D_BACK')
S.loop_cmd(at(50), 'STOP', 'pausa del loop')
S.add(at(50), 'D_FOCUS', 'ENC_SOUND')
S.add(at(50), 'D_SOUND', c=FERN_PLUCK, note='Fern Pluck: Arpeggiate 6, sedicesimi su e giù')
S.voicing(at(50), 36)
S.add(at(50), 'D_THEME', 'THEME_DARK')
S.add(at(50), 'D_VIEW', 'VIEW_REACT')
S.add(at(50, 1.5), 'D_FOCUS', 'ENC_FX')
S.add(at(50, 1.5), 'D_TURN', 'ENC_FX', 2)
S.add(at(57), 'D_BEATON', 0, note='ultima battuta senza batteria')
S.chords(50, '1:Em9:4@88 | 1:F#m7:4@86 | 1:Gmaj9:4@90 | 1:A7sus:4@92 | 1:Em9:4@92 | 1:F#m7:4@94 |'
             ' 1:Gm6:4@98 | 1:A7sus:2@100 3:A:2@104', early=24)

# ---- 58–65 finale: un tono sopra, il loop riprende, la kalimba torna ----
S.add(at(57, 4.75), 'D_FOCUS', 'ENC_SOUND')
S.add(at(57, 4.75), 'D_SOUND', c=DEW_MALLET)
S.add(at(57, 4.75), 'D_PERF', 'PERF_OFF', 0)
S.lock_toggle(at(57, 4.75))
S.voicing(at(57, 4.75), 48)
S.add(at(58), 'D_FOCUS', 'ENC_KEY')
S.add(at(58), 'D_PTURN', 'ENC_KEY', 2, note='transpose +2: anche il loop sale (ACC-221)')
S.add(at(58), 'D_BEAT', LOUNGE)
S.add(at(58), 'D_BEATON', 1)
S.loop_cmd(at(58), 'STOP', 'il loop riprende da capo, con il trasporto')
S.add(at(58), 'D_THEME', 'THEME_LIGHT')
S.add(at(58), 'D_VIEW', 'VIEW_CHORD')
S.melody(58, VERSE.rsplit('|', 1)[0] + '| 1:D5:2@96 3:E5:.5@92 3.5:F#5:.5@96 4:A5:1@104')

# ---- 66–73 ritornello finale: Sun Room e Funk ----
S.voicing(at(66), 54)
S.add(at(66), 'D_FOCUS', 'ENC_SOUND')
S.add(at(66), 'D_SOUND', c=SUN_ROOM)
S.add(at(66), 'D_BEAT', FUNK)
S.add(at(66), 'D_VIEW', 'VIEW_CHORD_KB')
S.melody(66, CHORUS)

# ---- 74–81 l'ultimo ritornello sulle campane ----
S.add(at(74), 'D_SOUND', c=GLASS_POLLEN, note='Glass Pollen: il Lock tiene il Perform spento')
S.add(at(74), 'D_VIEW', 'VIEW_NOTES')
S.melody(74, CHORUS2)

# ---- 82–89 sera: via il riff (Undo), via la batteria, ritardando, poi l'ultimo accordo in Harp ----
S.loop_cmd(at(82), 'UNDO', 'Undo: via il riff')
S.add(at(82), 'D_BEATON', 0)
S.add(at(82), 'D_THEME', 'THEME_DARK')
S.add(at(82), 'D_VIEW', 'VIEW_CHORD')
S.add(at(82), 'D_FOCUS', 'ENC_BPM')
TEMPI = {82: 88, 83: 80, 84: 72, 85: 66}
for bar, bpm in TEMPI.items():
    S.add(at(bar), 'D_BPM', c=bpm, note=f'ritardando: {bpm} BPM')
S.loop_cmd(at(86), 'CLEAR', 'Clear')
S.lock_toggle(at(86))
S.add(at(86), 'D_FOCUS', 'ENC_PERFORM')
S.add(at(86), 'D_PERF', 'PERF_HARP', 3, note='Harp 3')
S.voicing(at(86), 36)
S.add(at(86), 'D_TURN', 'ENC_FX', 2)
S.chords(86, '1:Dmaj9:8@92')               # con il transpose: Mi maggiore
S.voicing(at(86, 3), 41)
S.voicing(at(87), 46)
S.voicing(at(87, 3), 50)
S.add(at(88, 3), 'D_MENU', note='il menu, con «Play Demo Song»')
for k in range(6):
    S.add(at(88, 3.5 + k * 0.25), 'D_TURN', 'ENC_OPTIONS', 1)
S.add(at(89, 4), 'D_BACK')
S.add(at(90), 'D_END')

# ======================================================================== controlli e uscita
steps = sorted(S.steps, key=lambda s: (s[0], s[1]))
assert steps[-1][2] == 'D_END'

# il looper: overdub e Undo all'inizio di un giro di 4 battute (anche dopo la ripresa, che riparte da capo)
rec = next(t for t, c in S.loop if c == 'PRESS') + BAR
for t, c in S.loop:
    if c in ('OVERDUB', 'UNDO') and (t - rec) % (4 * BAR):
        sys.exit(f'{c} a {t} non cade all\'inizio di un giro')

# durata in ms con la mappa dei tempi (il BPM vale dal tick in cui cambia)
bpm, t0, ms = 120, 0, 0.0
for t, _, act, a, b, c, d, note in steps:
    if act == 'D_BPM':
        ms += (t - t0) * 60000.0 / (bpm * PPQ)
        bpm, t0 = c, t
ms += (steps[-1][0] - t0) * 60000.0 / (bpm * PPQ)

out = ['/* demo_song.c — «Acacia», il brano della demo (demo.h). Brano originale di Stame.',
       ' *',
       ' * Generato da tools/demo.py: non va modificato a mano. Re maggiore, poi Mi; 96 BPM con un',
       f' * ritardando finale; {len(steps)} passi, {int(ms) // 60000}:{int(ms) // 1000 % 60:02d}. Tick a 96 PPQN dall\'inizio del brano.',
       ' */',
       '#include "demo.h"',
       '#include "vetrina.h"',
       '',
       'const char vet_demo_song_title[] = "Demo song: Acacia";',
       '',
       'const dstep_t vet_demo_song[] = {']
for t, _, act, a, b, c, d, note in steps:
    line = f'    {{ {t:6d}, {act}, {a}, {b}, {c}, {d} }},'
    if note:
        line = f'{line:<62}/* {note} */'
    out.append(line.rstrip())
out += ['};', '',
        'const uint16_t vet_demo_song_n = (uint16_t)(sizeof vet_demo_song / sizeof vet_demo_song[0]);',
        f'const uint32_t vet_demo_song_ms = {int(round(ms))}u;', '']
dest = pathlib.Path('src/platform/vetrina/demo_song.c')
dest.write_bytes('\n'.join(out).encode('utf-8'))
notes = sum(1 for s in steps if s[2] == 'D_CHORD')
print(f'{dest}: {len(steps)} passi, {notes} accordi e note, {ms / 1000:.1f} s')
