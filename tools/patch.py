"""patch.py — le patch di Stame per la vetrina (specifica 20, SND-454 e §2.7).

Ogni suono è descritto per nome di parametro (colonna "Nome" di §2.2) a partire dalla patch INIT
del suo modello. Lo script scrive:
  - assets/patch/sound/ e assets/patch/bass/: un .inc di Pistil per suono e l'indice bank.idx (SND-131);
  - src/platform/vetrina/patch_vetrina.c: le stesse patch come tabelle per la vetrina.
Sono patch di Stame, progettate sul carattere del nome: nessun preset dell'Orchid.

    python -I tools/patch.py
"""
import os
import re

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)


def leggi_patch_c():
    s = open(os.path.join(RADICE, 'src', 'dsp', 'patch.c'), encoding='utf-8').read()
    nomi = re.findall(r'"([A-Z0-9]+)"', s[s.index('snd_par_name'):s.index('/* default della tabella')])
    blocco = s[s.index('static const uint8_t DEF'):]
    blocco = blocco[blocco.index('{') + 1:blocco.index('};')]
    blocco = re.sub(r'/\*.*?\*/', '', blocco, flags=re.S)
    dfl = [int(v) for v in re.findall(r'\d+', blocco)]
    assert len(nomi) == 135 and len(dfl) == 135, (len(nomi), len(dfl))
    return nomi, dfl


NOMI, DEF = leggi_patch_c()
IDX = {n: i for i, n in enumerate(NOMI)}
VA, RP, FM = 0, 1, 2
SAW, PULSE, TRI = 1, 2, 3
# sorgenti e destinazioni della matrice (§8.3)
KEY, VEL, RND = 0, 1, 3
LFO = {1: 4, 2: 5, 3: 6, 4: 7}
ENV = {1: 8, 2: 9, 3: 10, 4: 11}
WHEEL, BEND = 12, 13
D_PITCH, D_CUTOFF, D_Q, D_VOLUME, D_PAN, D_MOD7, D_MOD8 = 1, 15, 16, 17, 18, 31, 32
def D_OSC(n): return 2 + 3 * (n - 1)
def D_PW(n): return 3 + 3 * (n - 1)
def D_GAIN(n): return 4 + 3 * (n - 1)
CHORUS, ENSEMBLE, PHASER, FLANGER, DRIVE, TREMOLO, DELAY = 1, 2, 3, 4, 5, 6, 7


def patch(model, matrice=(), **kw):
    p = list(DEF)
    p[IDX['MODEL']] = model
    if model == RP:
        p[IDX['RPHEIGHT']] = 64
        p[IDX['RPDISTANCE']] = 64
        p[IDX['RPVOL']] = 64
    for nome, v in kw.items():
        p[IDX[nome]] = int(v)
    for n, (s, d, a) in enumerate(matrice, 1):
        p[IDX['M%dS' % n]], p[IDX['M%dD' % n]], p[IDX['M%dA' % n]] = s, d, a
    for i, v in enumerate(p):
        assert 0 <= v <= 127, (NOMI[i], v)
    return p


def fx(slot, tipo, *par):
    d = {'FX%dTYPE' % slot: tipo}
    for k, v in enumerate(par, 1):
        d['FX%dP%d' % (slot, k)] = v
    return d


# ---- i 16 suoni della vetrina, nell'ordine di SOUNDS[] in vetrina.c ----
SUONI = [
    ('Glass Pollen', patch(FM, [(ENV[3], D_GAIN(2), 114)], FMALG=1,
        O1PW=127, O1GAIN=0, O2SEMI=85, O2DETUNE=108, O2PW=30, O2GAIN=80, O3PW=0, O4PW=0,
        E2A=0, E2D=85, E2S=0, E2R=55, E3A=0, E3D=45, E3S=0, E3R=40, GAIN=70, REVSEND=55,
        **fx(1, CHORUS, 30, 35, 100), **fx(2, DELAY, 1, 25, 30, 80, 90, 20))),
    ('Night Greenhouse', patch(VA, [(LFO[1], D_CUTOFF, 89)],
        O2SHAPE=SAW, O2DETUNE=72, O2GAIN=60, O3SHAPE=SAW, O3SEMI=52, O3DETUNE=58, O3GAIN=40,
        CUTOFF=62, RESONANCE=20, FENV=25, FKT=40, E1A=60, E1D=70, E1S=60, E1R=70,
        E2A=55, E2D=70, E2S=110, E2R=75, L1SHAPE=1, L1RATE=25, L1MODE=1, GAIN=60, REVSEND=70, REVSIZE=110,
        REVLP=100, **fx(1, ENSEMBLE, 35, 70, 60, 40))),
    ('Anther Keys', patch(RP, [], RPHEIGHT=72, RPDISTANCE=45, RPDECAY=92, RPRELEASE=36, RPTONE=70,
        RPVELCURVE=95, RPCLANK=28, RPCLANCURVE=40, RPTREMOLO=42, RPTREMRATE=68, RPVOL=80, RPHAMMER=22,
        RPKEYOFF=20, RPTSTEREO=110, REVSEND=35, **fx(1, CHORUS, 20, 0, 90))),
    ('Slow Stamen', patch(VA, [(LFO[2], D_PW(1), 94)],
        O1SHAPE=PULSE, O1PW=50, O2SHAPE=SAW, O2DETUNE=70, O2GAIN=55, NOISE=6,
        L2SHAPE=0, L2RATE=40, L2MODE=1, CUTOFF=56, RESONANCE=30, FENV=30, E1A=70, E1D=80, E1S=50, E1R=80,
        E2A=80, E2D=80, E2S=115, E2R=85, GAIN=62, REVSEND=75, REVSIZE=115, **fx(2, DELAY, 0, 20, 40, 60, 60, 0))),
    ('Fern Pluck', patch(VA, [], O2SHAPE=PULSE, O2PW=40, O2SEMI=76, O2GAIN=40,
        CUTOFF=45, RESONANCE=28, FENV=62, FVELO=30, FKT=64, E1A=0, E1D=28, E1S=0, E1R=25,
        E2A=0, E2D=42, E2S=0, E2R=30, GAIN=66, REVSEND=30, **fx(2, DELAY, 1, 32, 38, 70, 120, 25))),
    ('Copper Reed', patch(RP, [], RPICKUP=2, RPHEIGHT=88, RPDISTANCE=78, RPDECAY=80, RPRELEASE=30,
        RPTONE=74, RPVELCURVE=100, RPCLANK=22, RPHAMMER=30, RPKEYOFF=24, RPTREMOLO=55, RPTREMRATE=80,
        RPVOL=78, REVSEND=30, **fx(1, DRIVE, 22, 35))),
    ('Orbit Choir', patch(FM, [(LFO[1], D_PITCH, 72)], FMALG=6,
        O1PW=127, O1GAIN=0, O2SEMI=76, O2PW=70, O2GAIN=0, O3SEMI=83, O3PW=45, O3GAIN=0, O4PW=35, O4GAIN=0,
        L1SHAPE=0, L1RATE=76, L1MODE=1, CUTOFF=85, RESONANCE=10, E2A=62, E2D=64, E2S=120, E2R=70,
        GAIN=58, REVSEND=70, REVSIZE=112, **fx(1, ENSEMBLE, 30, 80, 50, 30))),
    ('Moss Strings', patch(VA, [(LFO[1], D_PITCH, 70)],
        O2SHAPE=SAW, O2DETUNE=70, O2GAIN=64, O3SHAPE=SAW, O3DETUNE=57, O3GAIN=50,
        CUTOFF=72, RESONANCE=8, FKT=50, FENV=15, E1A=50, E1D=80, E1S=90, E1R=70,
        E2A=60, E2D=70, E2S=118, E2R=72, L1SHAPE=1, L1RATE=74, L1MODE=1, GAIN=58, REVSEND=60,
        **fx(1, ENSEMBLE, 28, 85, 55, 35))),
    ('Dew Mallet', patch(FM, [(ENV[3], D_GAIN(2), 120), (ENV[4], D_GAIN(3), 110)], FMALG=1,
        O1PW=127, O1GAIN=0, O2SEMI=88, O2PW=20, O2GAIN=90, O3SEMI=104, O3PW=0, O3GAIN=60, O4PW=0,
        E2A=0, E2D=55, E2S=0, E2R=40, E3A=0, E3D=22, E3S=0, E3R=20, E4A=0, E4D=8, E4S=0, E4R=8,
        GAIN=72, REVSEND=40)),
    ('Tape Fern', patch(VA, [(LFO[1], D_PITCH, 70), (LFO[2], D_PITCH, 67)],
        O1SHAPE=TRI, O2SHAPE=SAW, O2DETUNE=66, O2GAIN=30, NOISE=10, PINK=1,
        L1SHAPE=0, L1RATE=30, L1MODE=1, L2SHAPE=0, L2RATE=74, L2MODE=1, CUTOFF=76, RESONANCE=15,
        E2A=2, E2D=60, E2S=100, E2R=50, GAIN=62, REVSEND=35, REVLP=70, **fx(1, DRIVE, 30, 30))),
    ('Seed Organ', patch(FM, [(ENV[3], D_GAIN(3), 100)], FMALG=7,
        O1PW=110, O1GAIN=0, O2SEMI=76, O2PW=95, O2GAIN=0, O3SEMI=83, O3PW=70, O3GAIN=0,
        O4SEMI=88, O4PW=60, O4GAIN=0, E2A=2, E2D=64, E2S=127, E2R=12, E3A=0, E3D=18, E3S=0, E3R=10,
        CUTOFF=110, GAIN=56, REVSEND=30, **fx(1, CHORUS, 110, 40, 127))),
    ('Sun Room', patch(RP, [], RPICKUP=1, RPHEIGHT=60, RPDISTANCE=30, RPDECAY=100, RPRELEASE=40,
        RPTONE=52, RPVELCURVE=85, RPCLANK=18, RPHAMMER=14, RPKEYOFF=16, RPVOL=84, REVSEND=45,
        **fx(1, CHORUS, 18, 45, 110))),
    ('Linnaeus Lead', patch(VA, [(WHEEL, D_MOD7, 76), (0, 0, 64), (0, 0, 64), (0, 0, 64), (0, 0, 64),
        (0, 0, 64), (LFO[1], D_PITCH, 64)], GLIDEMODE=3, GLIDE=28,
        O2SHAPE=PULSE, O2PW=64, O2SEMI=52, O2GAIN=45, CUTOFF=70, RESONANCE=35, FENV=40,
        E1A=5, E1D=50, E1S=40, E1R=30, E2A=3, E2D=64, E2S=110, E2R=35,
        L1SHAPE=0, L1RATE=78, L1MODE=1, GAIN=60, REVSEND=40, **fx(2, DELAY, 0, 22, 30, 70, 40, 10))),
    ('Petal Brass', patch(VA, [], O2SHAPE=SAW, O2DETUNE=69, O2GAIN=58,
        CUTOFF=52, RESONANCE=12, FENV=48, FVELO=40, E1A=18, E1D=45, E1S=55, E1R=40,
        E2A=12, E2D=50, E2S=108, E2R=38, GAIN=60, REVSEND=40, **fx(1, ENSEMBLE, 30, 30, 50, 20))),
    ('Root Drone', patch(FM, [(LFO[1], D_GAIN(2), 80), (LFO[2], D_PAN, 80)], FMALG=0,
        O1PW=127, O1GAIN=0, O2SEMI=52, O2PW=50, O2GAIN=0, O3SEMI=71, O3PW=30, O3GAIN=0,
        O4PW=25, O4GAIN=0, O4FB=50, L1SHAPE=1, L1RATE=20, L1MODE=1, L2SHAPE=0, L2RATE=15, L2MODE=1,
        CUTOFF=80, RESONANCE=25, E2A=75, E2D=64, E2S=127, E2R=90, GAIN=56, REVSEND=80, REVSIZE=120,
        **fx(2, DELAY, 0, 25, 55, 60, 80, 0))),
    ('Vetro Pad', patch(VA, [], O1SHAPE=PULSE, O1PW=30, O1GAIN=60, O2SHAPE=SAW, O2SEMI=76, O2DETUNE=67,
        O2GAIN=35, O3SHAPE=TRI, O3SEMI=88, O3GAIN=25, CUTOFF=90, RESONANCE=20, FKT=64,
        E2A=45, E2D=70, E2S=105, E2R=80, GAIN=56, REVSEND=70, REVSIZE=118,
        **fx(1, CHORUS, 25, 60, 127), **fx(2, DELAY, 0, 25, 45, 70, 127, 0))),
]

# ---- i 6 bassi della vetrina, nell'ordine di BASSES[] ----
BASSI = [
    ('Round Root', patch(VA, [], GLIDEMODE=2, O1SHAPE=TRI, O2SHAPE=SAW, O2GAIN=30, CUTOFF=58, RESONANCE=10,
        FENV=20, E1A=0, E1D=35, E1S=30, E2A=1, E2D=50, E2S=100, E2R=18, GAIN=70, REVSEND=5)),
    ('Sub Floor', patch(VA, [], GLIDEMODE=2, O1SHAPE=TRI, CUTOFF=45, E2A=2, E2D=64, E2S=127, E2R=20, GAIN=76)),
    ('Pluck Bass', patch(VA, [], GLIDEMODE=2, O2SHAPE=PULSE, O2SEMI=52, O2PW=50, O2GAIN=35, CUTOFF=38,
        RESONANCE=30, FENV=60, E1A=0, E1D=26, E1S=5, E2A=0, E2D=45, E2S=50, E2R=15, GAIN=66)),
    ('Reed Bass', patch(RP, [], GLIDEMODE=2, RPICKUP=2, RPHEIGHT=80, RPDISTANCE=60, RPDECAY=85,
        RPRELEASE=25, RPTONE=60, RPVOL=90, GAIN=70)),
    ('Velvet Sub', patch(VA, [], GLIDEMODE=2, O1SHAPE=TRI, O2SHAPE=SAW, O2DETUNE=70, O2GAIN=22, CUTOFF=50,
        RESONANCE=22, E2A=6, E2D=64, E2S=120, E2R=30, GAIN=70, **fx(1, CHORUS, 20, 25, 90))),
    ('Wood Bass', patch(FM, [(ENV[3], D_GAIN(2), 115)], GLIDEMODE=2, FMALG=1, O1PW=127, O1GAIN=0,
        O2SEMI=64, O2PW=15, O2GAIN=40, O3PW=0, O4PW=0, E2A=0, E2D=52, E2S=25, E2R=22,
        E3A=0, E3D=20, E3S=0, E3R=15, CUTOFF=75, GAIN=72)),
]


# Livelli pareggiati il 15/10/2026 con `stame-render --suoni`: finestra più forte da 100 ms mentre la nota
# è tenuta, accordo di 5 note a −17 dBFS, basso (una nota, volume del basso 70) a −24 dBFS.
# Correzione in dB, applicata a GAIN: GAIN' = GAIN · 10^(dB/40), perché g_vol = (GAIN/64)².
LIVELLO_DB = {
    'Glass Pollen': -0.3, 'Night Greenhouse': -1.9, 'Anther Keys': -0.2, 'Slow Stamen': -7.7,
    'Fern Pluck': 2.0, 'Copper Reed': -8.0, 'Orbit Choir': -2.4, 'Moss Strings': 1.4, 'Dew Mallet': -0.7,
    'Tape Fern': -0.5, 'Seed Organ': 0.8, 'Sun Room': -0.5, 'Linnaeus Lead': 1.8, 'Petal Brass': 1.0,
    'Root Drone': -4.7, 'Vetro Pad': -1.8,
    'Round Root': 7.3, 'Sub Floor': 5.0, 'Pluck Bass': 6.1, 'Reed Bass': -3.3, 'Velvet Sub': 6.5, 'Wood Bass': 5.8,
}


# Perform di default di ogni suono (ACC-162; colonne perform_mode e perform_amount di bank.idx, SND-131).
# Modi di ACC-160: 0 Off, 1 Strum, 2 Strum 2 Oct, 3 Slop, 4 Arpeggiate, 5 Arp 2 Oct, 6 Pattern, 7 Harp.
# Scelte di Stame per i suoi suoni, non dati dell'Orchid. I bassi non hanno performance (ACC-142).
OFF, STRUM, STRUM2, SLOP, ARP, ARP2, PATTERN, HARP = range(8)
PERFORM = {
    'Glass Pollen': (HARP, 3), 'Anther Keys': (STRUM, 2), 'Fern Pluck': (ARP, 6), 'Copper Reed': (STRUM, 3),
    'Moss Strings': (STRUM2, 4), 'Dew Mallet': (PATTERN, 5), 'Tape Fern': (SLOP, 4), 'Sun Room': (PATTERN, 2),
    'Linnaeus Lead': (ARP2, 4), 'Petal Brass': (STRUM, 1),
}


def livella(voci):
    for nome, p in voci:
        g = p[IDX['GAIN']] * 10.0 ** (LIVELLO_DB.get(nome, 0.0) / 40.0)
        p[IDX['GAIN']] = max(1, min(127, int(round(g))))


livella(SUONI)
livella(BASSI)


def inc(p):
    righe = ['0x%02X,\t//%d TREBLE_%s' % (v, i, NOMI[i]) for i, v in enumerate(p)]
    return '\r\n'.join(righe)


def nome_file(n, nome):
    return '%02d_%s.inc' % (n, re.sub(r'[^a-z0-9]+', '_', nome.lower()).strip('_'))


def scrivi_banco(cartella, voci):
    os.makedirs(cartella, exist_ok=True)
    idx = []
    for n, (nome, p) in enumerate(voci, 1):
        f = nome_file(n, nome)
        dati = inc(p).encode('ascii')
        assert len(dati) == 3414, (nome, len(dati))
        open(os.path.join(cartella, f), 'wb').write(dati)
        modo, amount = PERFORM.get(nome, (OFF, 0))
        idx.append('%02d\t%s\t%s\t%d\t%d' % (n, nome, f, modo, amount))
    open(os.path.join(cartella, 'bank.idx'), 'w', encoding='utf-8', newline='\n').write('\n'.join(idx) + '\n')


def tabella(nome_c, voci):
    r = ['const uint8_t %s[%d][DSP_NPAR] STAME_ROM = {' % (nome_c, len(voci))]
    for nome, p in voci:
        r.append('    /* %s */' % nome)
        r.append('    {')
        for i in range(0, 135, 15):
            r.append('        ' + ', '.join('%d' % v for v in p[i:i + 15]) + ',')
        r.append('    },')
    r.append('};')
    return r


def main():
    scrivi_banco(os.path.join(RADICE, 'assets', 'patch', 'sound'), SUONI)
    scrivi_banco(os.path.join(RADICE, 'assets', 'patch', 'bass'), BASSI)
    c = ['/* patch_vetrina.c — patch di Stame per i suoni e i bassi della vetrina.',
         ' * Generato da tools/patch.py: non modificare a mano. Le stesse patch sono in assets/patch/. */',
         '#include "vetrina.h"', '']
    c += tabella('vet_sound_patch', SUONI) + ['']
    c += tabella('vet_bass_patch', BASSI) + ['']
    c += ['/* Perform di default: modo di ACC-160 e amount (ACC-162) */',
          'const uint8_t vet_sound_perf[%d][2] STAME_ROM = {' % len(SUONI)]
    c += ['    { %d, %d },   /* %s */' % (PERFORM.get(nome, (OFF, 0)) + (nome,)) for nome, _ in SUONI]
    c += ['};', '']
    p = os.path.join(RADICE, 'src', 'platform', 'vetrina', 'patch_vetrina.c')
    open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(c))
    print('patch: %d suoni, %d bassi' % (len(SUONI), len(BASSI)))


if __name__ == '__main__':
    main()
