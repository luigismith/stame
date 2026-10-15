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
import sys

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
VA, RP, FM, SMP = 0, 1, 2, 3
# il campionatore (20 §7b, SND-371) legge i byte RP con altri nomi
ALIAS = {'SMPSET': 'RPHEIGHT', 'SMPLOOP': 'RPDISTANCE', 'SMPSTART': 'RPKT', 'SMPTUNE': 'RPDECAY'}


def leggi_set_idx():
    """gli indici dei set del banco, da campioni_idx.h (generato da tools/campioni.py)"""
    p = os.path.join(RADICE, 'src', 'platform', 'vetrina', 'campioni_idx.h')
    if not os.path.exists(p):
        return {}
    return {m[1]: int(m[2]) for m in re.finditer(r'SMP_SET_([A-Z0-9_]+) = (\d+)', open(p, encoding='utf-8').read())}


SET_IDX = leggi_set_idx()


def set_idx(nome):
    if nome.upper() not in SET_IDX:
        sys.exit(f'set {nome} non nel banco: prima python -I tools/campioni.py')
    return SET_IDX[nome.upper()]
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
    if model == SMP:                                  # INIT del campionatore (SND-371)
        p[IDX['RPHEIGHT']] = 0
        p[IDX['RPDISTANCE']] = 0
        p[IDX['RPKT']] = 0
        p[IDX['RPDECAY']] = 64
        p[IDX['FTYPE']] = 0
        p[IDX['E2R']] = 50
    for nome, v in kw.items():
        p[IDX[ALIAS.get(nome, nome)]] = int(v)
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

# ---- gli strumenti campionati (20 §7b): dal 15/10/2026, banco di tools/campioni.py ----
if SET_IDX:
    SUONI += [
        ('Grand Piano', patch(SMP, [], SMPSET=set_idx('piano_kawai'), GVELO=100, FTYPE=1, CUTOFF=78, FVELO=55,
            E2A=0, E2D=64, E2S=127, E2R=42, GAIN=82, REVSEND=28, REVSIZE=95)),
        ('Upright Piano', patch(SMP, [], SMPSET=set_idx('piano_upright'), GVELO=100, FTYPE=1, CUTOFF=74, FVELO=55,
            E2A=0, E2D=64, E2S=127, E2R=40, GAIN=82, REVSEND=22)),
        ('FM Piano', patch(SMP, [], SMPSET=set_idx('fm_piano'), GVELO=90, E2A=0, E2D=64, E2S=127, E2R=45,
            GAIN=80, REVSEND=30, **fx(1, CHORUS, 24, 40, 100))),
        ('Vibraphone', patch(SMP, [], SMPSET=set_idx('vibes'), GVELO=90, E2A=0, E2D=64, E2S=127, E2R=60,
            GAIN=80, REVSEND=45, REVSIZE=105, **fx(1, TREMOLO, 40, 45, 0))),
        ('Marimba', patch(SMP, [], SMPSET=set_idx('marimba'), GVELO=95, E2A=0, E2D=64, E2S=127, E2R=35,
            GAIN=82, REVSEND=35)),
        ('Glockenspiel', patch(SMP, [], SMPSET=set_idx('glock'), GVELO=80, E2A=0, E2D=64, E2S=127, E2R=70,
            GAIN=72, REVSEND=55, REVSIZE=110)),
        ('Tubular Bells', patch(SMP, [], SMPSET=set_idx('chimes'), GVELO=85, E2A=0, E2D=64, E2S=127, E2R=90,
            GAIN=74, REVSEND=60, REVSIZE=118)),
        ('Concert Harp', patch(SMP, [], SMPSET=set_idx('harp'), GVELO=90, E2A=0, E2D=64, E2S=127, E2R=55,
            GAIN=80, REVSEND=42, REVSIZE=100)),
        ('Kalimba', patch(SMP, [], SMPSET=set_idx('kalimba'), GVELO=90, E2A=0, E2D=64, E2S=127, E2R=40,
            GAIN=80, REVSEND=30, **fx(2, DELAY, 1, 30, 35, 70, 110, 20))),
        ('Harpsichord', patch(SMP, [], SMPSET=set_idx('harpsichord'), GVELO=30, E2A=0, E2D=64, E2S=127, E2R=30,
            GAIN=76, REVSEND=35, REVSIZE=100)),
        ('Pipe Organ', patch(SMP, [], SMPSET=set_idx('organ'), GVELO=20, E2A=10, E2D=64, E2S=127, E2R=38,
            GAIN=74, REVSEND=65, REVSIZE=120, REVLP=90)),
        ('Alto Recorder', patch(SMP, [(LFO[1], D_PITCH, 68)], SMPSET=set_idx('recorder'), GVELO=60,
            L1SHAPE=0, L1RATE=70, L1MODE=0, E2A=12, E2D=64, E2S=127, E2R=30, GAIN=76, REVSEND=45)),
        ('Tenor Sax', patch(SMP, [], SMPSET=set_idx('sax'), GVELO=80, FTYPE=1, CUTOFF=92, FVELO=35,
            E2A=8, E2D=64, E2S=127, E2R=32, GAIN=78, REVSEND=38)),
    ]

# la seconda ondata di campioni (15/10/2026 sera), se il banco li ha
if SET_IDX and 'TX_PIANO' in SET_IDX:
    SUONI += [
        ('TX Piano', patch(SMP, [], SMPSET=set_idx('tx_piano'), GVELO=90, E2A=0, E2D=64, E2S=127, E2R=42,
            GAIN=80, REVSEND=32, **fx(1, CHORUS, 20, 30, 90))),
        ('Clavisynth', patch(SMP, [], SMPSET=set_idx('clavisynth'), GVELO=95, FTYPE=1, CUTOFF=96, FVELO=40,
            E2A=0, E2D=64, E2S=127, E2R=28, GAIN=80, REVSEND=18, **fx(1, PHASER, 35, 30, 50, 40))),
        ('Knight Upright', patch(SMP, [], SMPSET=set_idx('upright_knight'), GVELO=100, FTYPE=1, CUTOFF=76, FVELO=55,
            E2A=0, E2D=64, E2S=127, E2R=40, GAIN=82, REVSEND=24)),
        ('Italian Cembalo', patch(SMP, [], SMPSET=set_idx('harpsi_italian'), GVELO=25, E2A=0, E2D=64, E2S=127, E2R=28,
            GAIN=76, REVSEND=38, REVSIZE=100)),
        ('Lute Stop', patch(SMP, [], SMPSET=set_idx('harpsi_lute'), GVELO=30, E2A=0, E2D=64, E2S=127, E2R=26,
            GAIN=78, REVSEND=30)),
        ('Grand Organ', patch(SMP, [], SMPSET=set_idx('organ_loud'), GVELO=15, E2A=8, E2D=64, E2S=127, E2R=40,
            GAIN=72, REVSEND=70, REVSIZE=124, REVLP=85)),
        ('Flute Organ', patch(SMP, [], SMPSET=set_idx('organ_ren'), GVELO=15, E2A=12, E2D=64, E2S=127, E2R=38,
            GAIN=74, REVSEND=60, REVSIZE=118)),
        ('Full Organ', patch(SMP, [], SMPSET=set_idx('organ_full'), GVELO=15, E2A=10, E2D=64, E2S=127, E2R=36,
            GAIN=70, REVSEND=62, REVSIZE=120)),
        ('Sop. Recorder', patch(SMP, [(LFO[1], D_PITCH, 67)], SMPSET=set_idx('recorder_sop'), GVELO=60,
            L1SHAPE=0, L1RATE=72, L1MODE=0, E2A=10, E2D=64, E2S=127, E2R=28, GAIN=72, REVSEND=45)),
        ('Tenor Recorder', patch(SMP, [], SMPSET=set_idx('recorder_ten'), GVELO=60, E2A=12, E2D=64, E2S=127, E2R=30,
            GAIN=76, REVSEND=45)),
        ('Bass Recorder', patch(SMP, [], SMPSET=set_idx('recorder_bass'), GVELO=60, E2A=14, E2D=64, E2S=127, E2R=32,
            GAIN=78, REVSEND=42)),
        ('Ocarina', patch(SMP, [(LFO[1], D_PITCH, 66)], SMPSET=set_idx('ocarina'), GVELO=60,
            L1SHAPE=0, L1RATE=70, L1MODE=0, E2A=10, E2D=64, E2S=127, E2R=30, GAIN=76, REVSEND=50, REVSIZE=108)),
        ('Harmonica', patch(SMP, [], SMPSET=set_idx('harmonica'), GVELO=70, FTYPE=1, CUTOFF=100, FVELO=25,
            E2A=6, E2D=64, E2S=127, E2R=26, GAIN=76, REVSEND=30)),
        ('Chromatic Harp', patch(SMP, [], SMPSET=set_idx('harmonica_chrom'), GVELO=70, E2A=8, E2D=64, E2S=127, E2R=28,
            GAIN=76, REVSEND=32)),
        ('Saxello', patch(SMP, [], SMPSET=set_idx('saxello'), GVELO=80, FTYPE=1, CUTOFF=94, FVELO=35,
            E2A=8, E2D=64, E2S=127, E2R=30, GAIN=78, REVSEND=36)),
        ('Didgeridoo', patch(SMP, [], SMPSET=set_idx('didgeridoo'), GLIDEMODE=2, GVELO=40, E2A=20, E2D=64, E2S=127, E2R=45,
            GAIN=80, REVSEND=35, REVSIZE=110)),
        ('Strumstick', patch(SMP, [], SMPSET=set_idx('strumstick'), GVELO=90, E2A=0, E2D=64, E2S=127, E2R=34,
            GAIN=80, REVSEND=26)),
        ('Dan Tranh', patch(SMP, [], SMPSET=set_idx('dan_tranh'), GVELO=90, E2A=0, E2D=64, E2S=127, E2R=45,
            GAIN=80, REVSEND=44, REVSIZE=104, **fx(2, DELAY, 1, 28, 30, 65, 100, 10))),
        ('Bowed Psaltery', patch(SMP, [], SMPSET=set_idx('psaltery_bow'), GVELO=50, E2A=22, E2D=64, E2S=127, E2R=50,
            GAIN=74, REVSEND=58, REVSIZE=116)),
        ('Pluck Psaltery', patch(SMP, [], SMPSET=set_idx('psaltery_pluck'), GVELO=90, E2A=0, E2D=64, E2S=127, E2R=40,
            GAIN=80, REVSEND=40)),
        ('Mbira', patch(SMP, [], SMPSET=set_idx('mbira'), GVELO=90, E2A=0, E2D=64, E2S=127, E2R=38,
            GAIN=80, REVSEND=30, **fx(2, DELAY, 1, 30, 32, 70, 100, 15))),
        ('Nyunga Nyunga', patch(SMP, [], SMPSET=set_idx('nyunga'), GVELO=90, E2A=0, E2D=64, E2S=127, E2R=36,
            GAIN=80, REVSEND=30)),
        ('Kenya Kalimba', patch(SMP, [], SMPSET=set_idx('kalimba_kenya'), GVELO=90, E2A=0, E2D=64, E2S=127, E2R=36,
            GAIN=80, REVSEND=34)),
        ('Hand Chimes', patch(SMP, [], SMPSET=set_idx('hand_chimes'), GVELO=85, E2A=0, E2D=64, E2S=127, E2R=80,
            GAIN=72, REVSEND=60, REVSIZE=120)),
        ('Tube Glock', patch(SMP, [], SMPSET=set_idx('tub_glock'), GVELO=85, E2A=0, E2D=64, E2S=127, E2R=70,
            GAIN=72, REVSEND=55, REVSIZE=112)),
        ('Bowed Vibes', patch(SMP, [], SMPSET=set_idx('vibes_bowed'), GVELO=40, E2A=30, E2D=64, E2S=127, E2R=60,
            GAIN=74, REVSEND=62, REVSIZE=120, **fx(1, CHORUS, 18, 50, 100))),
        ('Balafon', patch(SMP, [], SMPSET=set_idx('balafon'), GVELO=95, E2A=0, E2D=64, E2S=127, E2R=30,
            GAIN=82, REVSEND=30)),
        ('Xylophone', patch(SMP, [], SMPSET=set_idx('xylophone'), GVELO=95, E2A=0, E2D=64, E2S=127, E2R=28,
            GAIN=80, REVSEND=34)),
        ('Wine Glasses', patch(SMP, [], SMPSET=set_idx('wine_glasses'), GVELO=30, E2A=40, E2D=64, E2S=127, E2R=70,
            GAIN=74, REVSEND=70, REVSIZE=126, **fx(1, CHORUS, 15, 60, 100))),
    ]

# ---- nuovi suoni di sintesi (15/10/2026 sera): venti timbri di Stame nei tre modelli ----
SUONI += [
    ('Moonflower', patch(VA, [(LFO[1], D_CUTOFF, 84), (LFO[2], D_PAN, 90)],
        O1SHAPE=SAW, O1DETUNE=60, O2SHAPE=SAW, O2DETUNE=68, O2GAIN=60, O3SHAPE=PULSE, O3SEMI=52, O3PW=40, O3GAIN=30,
        CUTOFF=58, RESONANCE=22, FENV=22, FKT=50, E1A=75, E1D=80, E1S=70, E1R=85, E2A=85, E2D=80, E2S=118, E2R=95,
        L1SHAPE=0, L1RATE=22, L1MODE=1, L2SHAPE=0, L2RATE=12, L2MODE=1, GAIN=58, REVSEND=80, REVSIZE=124, REVLP=90,
        **fx(1, ENSEMBLE, 40, 70, 60, 45))),
    ('Thistle Lead', patch(VA, [(WHEEL, D_MOD7, 80), (0, 0, 64), (0, 0, 64), (0, 0, 64), (0, 0, 64), (0, 0, 64),
        (LFO[1], D_PITCH, 64)], GLIDEMODE=3, GLIDE=22,
        O1SHAPE=SAW, O2SHAPE=SAW, O2DETUNE=71, O2GAIN=55, O3SHAPE=PULSE, O3SEMI=52, O3PW=30, O3GAIN=35,
        CUTOFF=66, RESONANCE=42, FENV=46, FVELO=30, E1A=0, E1D=55, E1S=35, E1R=30, E2A=0, E2D=64, E2S=110, E2R=30,
        L1SHAPE=0, L1RATE=80, L1MODE=1, GAIN=58, REVSEND=35, **fx(2, DELAY, 1, 20, 28, 70, 60, 10))),
    ('Lichen Organ', patch(FM, [(ENV[3], D_GAIN(2), 70)], FMALG=7,
        O1PW=112, O1GAIN=0, O2SEMI=76, O2PW=90, O2GAIN=0, O3SEMI=83, O3PW=64, O3GAIN=0, O4SEMI=95, O4PW=48, O4GAIN=0,
        E2A=3, E2D=64, E2S=127, E2R=14, E3A=0, E3D=24, E3S=64, E3R=10, CUTOFF=100, GAIN=56, REVSEND=34,
        **fx(1, TREMOLO, 60, 50, 40))),
    ('Nectar EP', patch(RP, [], RPICKUP=0, RPHEIGHT=66, RPDISTANCE=38, RPDECAY=96, RPRELEASE=34, RPTONE=62,
        RPVELCURVE=90, RPCLANK=30, RPCLANCURVE=60, RPTREMOLO=30, RPTREMRATE=60, RPVOL=82, RPHAMMER=26, RPKEYOFF=18,
        RPTSTEREO=90, REVSEND=38, **fx(1, PHASER, 28, 25, 45, 35))),
    ('Ivy Pluck', patch(VA, [], O1SHAPE=PULSE, O1PW=28, O2SHAPE=TRI, O2SEMI=76, O2GAIN=34,
        CUTOFF=50, RESONANCE=34, FENV=66, FVELO=38, FKT=60, E1A=0, E1D=24, E1S=0, E1R=22,
        E2A=0, E2D=38, E2S=0, E2R=28, GAIN=66, REVSEND=34, **fx(2, DELAY, 1, 30, 36, 72, 110, 20))),
    ('Bramble Brass', patch(VA, [], O1SHAPE=SAW, O2SHAPE=SAW, O2DETUNE=70, O2GAIN=60, O3SHAPE=SAW, O3SEMI=52, O3DETUNE=62, O3GAIN=40,
        CUTOFF=48, RESONANCE=14, FENV=54, FVELO=44, E1A=22, E1D=48, E1S=50, E1R=36,
        E2A=14, E2D=50, E2S=108, E2R=36, GAIN=58, REVSEND=38, **fx(1, DRIVE, 20, 30))),
    ('Cocoon Pad', patch(VA, [(LFO[1], D_PW(1), 88), (LFO[2], D_CUTOFF, 80)],
        O1SHAPE=PULSE, O1PW=50, O2SHAPE=PULSE, O2PW=36, O2DETUNE=70, O2GAIN=50, NOISE=4, PINK=1,
        CUTOFF=52, RESONANCE=26, FENV=20, E1A=80, E1D=90, E1S=60, E1R=90, E2A=90, E2D=80, E2S=116, E2R=100,
        L1SHAPE=0, L1RATE=28, L1MODE=1, L2SHAPE=1, L2RATE=16, L2MODE=1, GAIN=58, REVSEND=78, REVSIZE=122,
        **fx(1, CHORUS, 30, 55, 120))),
    ('Spore Bells', patch(FM, [(ENV[3], D_GAIN(2), 120), (ENV[4], D_GAIN(4), 100)], FMALG=2,
        O1PW=127, O1GAIN=0, O2SEMI=94, O2PW=40, O2GAIN=70, O3SEMI=78, O3PW=25, O3GAIN=50, O4SEMI=108, O4PW=20, O4GAIN=60,
        E2A=0, E2D=80, E2S=0, E2R=60, E3A=0, E3D=30, E3S=0, E3R=25, E4A=0, E4D=12, E4S=0, E4R=10,
        GAIN=68, REVSEND=62, REVSIZE=118, **fx(2, DELAY, 1, 35, 40, 70, 100, 15))),
    ('Rootstock', patch(VA, [(LFO[1], D_CUTOFF, 76)], O1SHAPE=SAW, O2SHAPE=SAW, O2SEMI=52, O2GAIN=70, O3SHAPE=PULSE, O3SEMI=52, O3PW=45, O3GAIN=40,
        CUTOFF=40, RESONANCE=48, FENV=40, FKT=30, E1A=0, E1D=60, E1S=20, E1R=40, E2A=0, E2D=64, E2S=120, E2R=40,
        L1SHAPE=1, L1RATE=18, L1MODE=1, GAIN=60, REVSEND=20, **fx(1, DRIVE, 32, 40))),
    ('Birch Keys', patch(RP, [], RPICKUP=1, RPHEIGHT=58, RPDISTANCE=26, RPDECAY=104, RPRELEASE=42, RPTONE=48,
        RPVELCURVE=80, RPCLANK=12, RPHAMMER=12, RPKEYOFF=14, RPVOL=84, REVSEND=44, REVSIZE=106,
        **fx(1, ENSEMBLE, 20, 60, 40, 25))),
    ('Pollen Choir', patch(FM, [(LFO[1], D_PITCH, 70), (LFO[2], D_GAIN(3), 76)], FMALG=4,
        O1PW=127, O1GAIN=0, O2SEMI=76, O2PW=60, O2GAIN=0, O3SEMI=71, O3PW=50, O3GAIN=0, O4SEMI=64, O4PW=20, O4GAIN=0,
        L1SHAPE=0, L1RATE=74, L1MODE=1, L2SHAPE=0, L2RATE=20, L2MODE=1, CUTOFF=78, RESONANCE=8,
        E2A=70, E2D=64, E2S=122, E2R=80, GAIN=56, REVSEND=76, REVSIZE=120, **fx(1, ENSEMBLE, 34, 80, 50, 35))),
    ('Reed Marsh', patch(RP, [], RPICKUP=3, RPHEIGHT=92, RPDISTANCE=84, RPDECAY=76, RPRELEASE=28,
        RPTONE=80, RPVELCURVE=100, RPCLANK=36, RPCLANCURVE=70, RPHAMMER=34, RPKEYOFF=26, RPVOL=74, REVSEND=26,
        **fx(1, DRIVE, 36, 45), **fx(2, DELAY, 0, 24, 30, 60, 50, 0))),
    ('Clover Strings', patch(VA, [(LFO[1], D_PITCH, 69)],
        O1SHAPE=SAW, O1DETUNE=58, O2SHAPE=SAW, O2DETUNE=70, O2GAIN=64, O3SHAPE=SAW, O3SEMI=52, O3DETUNE=66, O3GAIN=44,
        CUTOFF=68, RESONANCE=6, FKT=40, FENV=18, E1A=55, E1D=80, E1S=85, E1R=70,
        E2A=52, E2D=70, E2S=118, E2R=70, L1SHAPE=1, L1RATE=72, L1MODE=1, GAIN=58, REVSEND=62, REVSIZE=112,
        **fx(1, ENSEMBLE, 30, 85, 55, 35), **fx(2, DELAY, 0, 22, 35, 60, 60, 0))),
    ('Frost Pad', patch(FM, [(LFO[1], D_GAIN(2), 74)], FMALG=5,
        O1PW=120, O1GAIN=0, O2SEMI=83, O2PW=30, O2GAIN=0, O3SEMI=76, O3PW=55, O3GAIN=0, O4SEMI=88, O4PW=35, O4GAIN=0,
        L1SHAPE=0, L1RATE=18, L1MODE=1, CUTOFF=92, E2A=78, E2D=64, E2S=127, E2R=95, GAIN=54, REVSEND=84, REVSIZE=127, REVLP=70,
        **fx(1, CHORUS, 22, 70, 127))),
    ('Cactus Pluck', patch(FM, [(ENV[3], D_GAIN(2), 118)], FMALG=1,
        O1PW=127, O1GAIN=0, O2SEMI=64, O2PW=40, O2GAIN=85, O3PW=0, O4PW=0,
        E2A=0, E2D=46, E2S=0, E2R=30, E3A=0, E3D=16, E3S=0, E3R=12, GAIN=70, REVSEND=30,
        **fx(2, DELAY, 1, 26, 34, 72, 100, 25))),
    ('Heliotrope', patch(VA, [(LFO[1], D_PITCH, 66)], GLIDEMODE=2, GLIDE=18,
        O1SHAPE=SAW, O2SHAPE=PULSE, O2PW=40, O2DETUNE=66, O2GAIN=50, CUTOFF=74, RESONANCE=24, FENV=36,
        E1A=0, E1D=52, E1S=45, E1R=32, E2A=0, E2D=64, E2S=112, E2R=34, L1SHAPE=0, L1RATE=76, L1MODE=1,
        GAIN=60, REVSEND=42, **fx(1, PHASER, 30, 30, 55, 40))),
    ('Underbrush', patch(FM, [(LFO[1], D_GAIN(2), 84), (LFO[2], D_PAN, 90), (LFO[3], D_PITCH, 65)], FMALG=0,
        O1PW=127, O1GAIN=0, O2SEMI=52, O2PW=55, O2GAIN=0, O3SEMI=69, O3PW=28, O3GAIN=0, O4PW=30, O4GAIN=0, O4FB=60,
        L1SHAPE=1, L1RATE=16, L1MODE=1, L2SHAPE=0, L2RATE=12, L2MODE=1, L3SHAPE=0, L3RATE=24, L3MODE=1,
        CUTOFF=72, RESONANCE=30, E2A=90, E2D=64, E2S=127, E2R=100, GAIN=56, REVSEND=84, REVSIZE=126,
        **fx(2, DELAY, 0, 30, 60, 60, 90, 0))),
    ('Dandelion', patch(FM, [(ENV[3], D_GAIN(2), 100)], FMALG=7,
        O1PW=100, O1GAIN=0, O2SEMI=88, O2PW=70, O2GAIN=30, O3SEMI=100, O3PW=40, O3GAIN=30, O4SEMI=107, O4PW=25, O4GAIN=30,
        E2A=0, E2D=90, E2S=0, E2R=70, E3A=0, E3D=40, E3S=0, E3R=30, GAIN=64, REVSEND=66, REVSIZE=120,
        **fx(1, CHORUS, 26, 40, 110))),
    ('Sundew', patch(VA, [(LFO[1], D_PITCH, 72), (LFO[2], D_CUTOFF, 74)],
        O1SHAPE=TRI, O2SHAPE=PULSE, O2PW=58, O2DETUNE=63, O2GAIN=40, NOISE=14, PINK=1,
        L1SHAPE=0, L1RATE=34, L1MODE=1, L2SHAPE=1, L2RATE=20, L2MODE=1, CUTOFF=60, RESONANCE=18,
        E2A=4, E2D=60, E2S=100, E2R=55, GAIN=62, REVSEND=40, REVLP=60, **fx(1, DRIVE, 40, 36))),
    ('Lotus Flute', patch(VA, [(LFO[1], D_PITCH, 67), (LFO[2], D_VOLUME, 72)],
        O1SHAPE=TRI, O2SHAPE=TRI, O2SEMI=76, O2GAIN=24, NOISE=12, CUTOFF=70, RESONANCE=10,
        L1SHAPE=0, L1RATE=74, L1MODE=0, L2SHAPE=0, L2RATE=70, L2MODE=0, E2A=28, E2D=64, E2S=118, E2R=40,
        GAIN=64, REVSEND=56, REVSIZE=110)),
    ('Pine Organ', patch(FM, [], FMALG=7,
        O1PW=118, O1GAIN=0, O2SEMI=76, O2PW=100, O2GAIN=0, O3SEMI=83, O3PW=80, O3GAIN=0, O4SEMI=88, O4PW=70, O4GAIN=0,
        E2A=1, E2D=64, E2S=127, E2R=10, CUTOFF=104, GAIN=54, REVSEND=44, REVSIZE=112, **fx(1, ENSEMBLE, 26, 50, 60, 30))),
]

# ---- terza ondata (15/10/2026 notte), Luigi: «ancora più suoni, magari più cupi e più tecno». Stab da
# techno e da dub techno, una linea acid, hoover, supersaw a quattro dente di sega (l'unisono non c'è,
# SND-270), pad e drone scuri, campane inarmoniche, sync, organo house, pulsazioni per gli arpeggi ----
SUONI += [
    ('Nightshade', patch(VA, [(LFO[1], D_CUTOFF, 82), (LFO[2], D_PAN, 88)],
        O1SHAPE=SAW, O1DETUNE=60, O2SHAPE=SAW, O2DETUNE=69, O2GAIN=58, O3SHAPE=SAW, O3SEMI=52, O3DETUNE=62, O3GAIN=44,
        CUTOFF=40, RESONANCE=20, FENV=16, FKT=40, E1A=85, E1D=90, E1S=70, E1R=90, E2A=88, E2D=80, E2S=118, E2R=100,
        L1SHAPE=1, L1RATE=14, L1MODE=1, L2SHAPE=0, L2RATE=10, L2MODE=1, GAIN=60, REVSEND=84, REVSIZE=124, REVLP=72,
        **fx(1, ENSEMBLE, 36, 70, 60, 40))),
    ('Belladonna', patch(FM, [(LFO[1], D_GAIN(2), 76), (LFO[2], D_PAN, 86)], FMALG=5,
        O1PW=118, O1GAIN=0, O2SEMI=64, O2DETUNE=67, O2PW=34, O2GAIN=0, O3SEMI=52, O3PW=50, O3GAIN=0, O4SEMI=83, O4PW=16,
        O4GAIN=0, L1SHAPE=0, L1RATE=14, L1MODE=1, L2SHAPE=0, L2RATE=9, L2MODE=1, CUTOFF=66, RESONANCE=12,
        E2A=82, E2D=64, E2S=127, E2R=100, GAIN=56, REVSEND=86, REVSIZE=127, REVLP=58, **fx(1, CHORUS, 24, 70, 127))),
    ('Mandrake Stab', patch(VA, [], O1SHAPE=SAW, O2SHAPE=PULSE, O2PW=40, O2DETUNE=68, O2GAIN=56,
        CUTOFF=36, RESONANCE=56, FENV=72, FVELO=42, FKT=40, E1A=0, E1D=30, E1S=0, E1R=24, E2A=0, E2D=46, E2S=0, E2R=30,
        GAIN=66, REVSEND=42, REVSIZE=110, **fx(2, DELAY, 1, 30, 46, 60, 96, 30))),
    ('Dub Moss', patch(VA, [], O1SHAPE=SAW, O2SHAPE=SAW, O2DETUNE=66, O2GAIN=50,
        CUTOFF=32, RESONANCE=30, FENV=52, FKT=36, E1A=0, E1D=46, E1S=10, E1R=40, E2A=0, E2D=56, E2S=0, E2R=46,
        GAIN=66, REVSEND=70, REVSIZE=122, REVLP=66, **fx(1, CHORUS, 16, 40, 90), **fx(2, DELAY, 0, 42, 72, 44, 110, 40))),
    ('Acid Nettle', patch(VA, [], GLIDEMODE=3, GLIDE=14, O1SHAPE=SAW,
        CUTOFF=34, RESONANCE=102, FENV=74, FVELO=52, FKT=30, E1A=0, E1D=32, E1S=0, E1R=20,
        E2A=0, E2D=64, E2S=110, E2R=18, GAIN=62, REVSEND=12, **fx(1, DRIVE, 42, 46), **fx(2, DELAY, 2, 18, 26, 70, 60, 20))),
    ('Hogweed Hoover', patch(VA, [(ENV[3], D_PITCH, 54), (LFO[1], D_PW(1), 92)], GLIDEMODE=1, GLIDE=20,
        O1SHAPE=PULSE, O1PW=30, O2SHAPE=SAW, O2DETUNE=72, O2GAIN=60, O3SHAPE=SAW, O3SEMI=52, O3DETUNE=56, O3GAIN=50,
        CUTOFF=72, RESONANCE=10, E3A=0, E3D=26, E3S=0, E3R=20, L1SHAPE=1, L1RATE=30, L1MODE=1,
        E2A=2, E2D=64, E2S=115, E2R=40, GAIN=58, REVSEND=40, **fx(1, ENSEMBLE, 42, 82, 70, 50))),
    ('Cypress Saw', patch(VA, [], O1SHAPE=SAW, O1DETUNE=57, O2SHAPE=SAW, O2DETUNE=71, O2GAIN=60,
        O3SHAPE=SAW, O3SEMI=76, O3DETUNE=62, O3GAIN=30, O4SHAPE=SAW, O4DETUNE=67, O4GAIN=44,
        CUTOFF=72, RESONANCE=8, FENV=20, E1A=0, E1D=64, E1S=80, E1R=50, E2A=4, E2D=64, E2S=115, E2R=50,
        GAIN=54, REVSEND=56, REVSIZE=116, **fx(1, ENSEMBLE, 40, 85, 60, 40))),
    ('Mycelium', patch(FM, [(ENV[3], D_GAIN(2), 120)], FMALG=1,
        O1PW=127, O1GAIN=0, O2SEMI=76, O2PW=50, O2GAIN=85, O3PW=0, O4PW=0,
        E2A=0, E2D=30, E2S=0, E2R=24, E3A=0, E3D=12, E3S=0, E3R=10, CUTOFF=90, GAIN=70, REVSEND=26,
        **fx(2, DELAY, 2, 26, 42, 60, 110, 30))),
    ('Puffball Pulse', patch(VA, [(LFO[1], D_PW(1), 84)], O1SHAPE=PULSE, O1PW=22,
        CUTOFF=48, RESONANCE=40, FENV=56, FVELO=30, E1A=0, E1D=26, E1S=0, E1R=20, E2A=0, E2D=36, E2S=0, E2R=24,
        L1SHAPE=1, L1RATE=20, L1MODE=1, GAIN=66, REVSEND=24, **fx(2, DELAY, 2, 30, 46, 60, 100, 20))),
    ('Charred Keys', patch(RP, [], RPICKUP=2, RPHEIGHT=74, RPDISTANCE=52, RPDECAY=100, RPRELEASE=34, RPTONE=30,
        RPVELCURVE=95, RPCLANK=10, RPHAMMER=20, RPKEYOFF=18, RPTREMOLO=24, RPTREMRATE=50, RPVOL=86, REVSEND=50,
        REVSIZE=110, **fx(1, DRIVE, 24, 28), **fx(2, DELAY, 0, 24, 40, 50, 80, 20))),
    ('Charcoal Organ', patch(FM, [(ENV[3], D_GAIN(2), 80)], FMALG=7,
        O1PW=116, O1GAIN=0, O2SEMI=76, O2PW=96, O2GAIN=0, O3SEMI=83, O3PW=60, O3GAIN=0, O4SEMI=100, O4PW=40, O4GAIN=0,
        E2A=0, E2D=40, E2S=80, E2R=12, E3A=0, E3D=16, E3S=40, E3R=10, CUTOFF=92, GAIN=56, REVSEND=34,
        **fx(1, CHORUS, 22, 40, 110))),
    ('Tar Drone', patch(FM, [(LFO[1], D_GAIN(2), 84), (LFO[2], D_PAN, 92), (LFO[3], D_CUTOFF, 72)], FMALG=0,
        O1PW=127, O1GAIN=0, O2SEMI=52, O2PW=58, O2GAIN=0, O3SEMI=59, O3PW=30, O3GAIN=0, O4PW=34, O4GAIN=0, O4FB=84,
        L1SHAPE=1, L1RATE=12, L1MODE=1, L2SHAPE=0, L2RATE=8, L2MODE=1, L3SHAPE=0, L3RATE=6, L3MODE=1,
        CUTOFF=52, RESONANCE=34, E2A=94, E2D=64, E2S=127, E2R=104, GAIN=56, REVSEND=88, REVSIZE=127, REVLP=56,
        **fx(2, DELAY, 0, 30, 66, 44, 90, 0))),
    ('Wolfsbane Lead', patch(VA, [(WHEEL, D_MOD7, 78), (0, 0, 64), (0, 0, 64), (0, 0, 64), (0, 0, 64), (0, 0, 64),
        (LFO[1], D_PITCH, 64)], GLIDEMODE=2, GLIDE=10,
        O1SHAPE=PULSE, O1PW=64, O2SHAPE=SAW, O2SEMI=52, O2GAIN=50,
        CUTOFF=50, RESONANCE=46, FENV=40, FVELO=30, E1A=0, E1D=50, E1S=30, E1R=30, E2A=0, E2D=64, E2S=115, E2R=30,
        L1SHAPE=0, L1RATE=78, L1MODE=1, GAIN=60, REVSEND=30, **fx(1, DRIVE, 36, 40), **fx(2, DELAY, 1, 22, 34, 55, 70, 20))),
    ('Datura Bells', patch(FM, [(ENV[3], D_GAIN(2), 118), (ENV[4], D_GAIN(4), 104)], FMALG=2,
        O1PW=127, O1GAIN=0, O2SEMI=70, O2DETUNE=60, O2PW=42, O2GAIN=60, O3SEMI=52, O3PW=40, O3GAIN=40,
        O4SEMI=81, O4PW=22, O4GAIN=50,
        E2A=0, E2D=96, E2S=0, E2R=80, E3A=0, E3D=40, E3S=0, E3R=30, E4A=0, E4D=16, E4S=0, E4R=12,
        CUTOFF=74, GAIN=66, REVSEND=72, REVSIZE=124, REVLP=70, **fx(2, DELAY, 0, 26, 44, 50, 110, 10))),
    ('Bog Rumble', patch(VA, [(LFO[1], D_CUTOFF, 74)], O1SHAPE=TRI, O1SEMI=52, O2SHAPE=SAW, O2SEMI=40, O2DETUNE=62,
        O2GAIN=40, NOISE=26, PINK=1, CUTOFF=28, RESONANCE=40, L1SHAPE=6, L1RATE=40, L1MODE=1,
        E2A=46, E2D=64, E2S=127, E2R=80, GAIN=64, REVSEND=74, REVSIZE=126, REVLP=48, **fx(1, DRIVE, 30, 20))),
    ('Blackthorn Sync', patch(VA, [(ENV[3], D_OSC(4), 100)], GLIDEMODE=2, GLIDE=8,
        O1SHAPE=0, O1GAIN=0, O3SHAPE=SAW, O3GAIN=0, O4SHAPE=SAW, O4SEMI=76, O4SYNC=1, O4GAIN=64,
        CUTOFF=82, RESONANCE=20, E3A=0, E3D=40, E3S=24, E3R=30, E2A=0, E2D=64, E2S=112, E2R=30,
        GAIN=60, REVSEND=28, **fx(2, DELAY, 1, 20, 30, 60, 60, 10))),
    ('Ironwood Perc', patch(FM, [(ENV[3], D_GAIN(2), 120)], FMALG=1,
        O1PW=127, O1GAIN=0, O2SEMI=79, O2DETUNE=62, O2PW=60, O2GAIN=80, O3PW=0, O4PW=0,
        E2A=0, E2D=26, E2S=0, E2R=20, E3A=0, E3D=14, E3S=0, E3R=10, CUTOFF=96, GAIN=70, REVSEND=34,
        **fx(2, DELAY, 2, 28, 40, 64, 120, 26))),
    ('Burdock Chords', patch(VA, [], O1SHAPE=SAW, O2SHAPE=SAW, O2DETUNE=68, O2GAIN=60, O3SHAPE=PULSE, O3SEMI=52, O3PW=40,
        O3GAIN=30, CUTOFF=44, RESONANCE=26, FENV=46, FVELO=34, E1A=0, E1D=56, E1S=24, E1R=40,
        E2A=2, E2D=60, E2S=90, E2R=46, GAIN=62, REVSEND=50, REVSIZE=112,
        **fx(1, ENSEMBLE, 30, 60, 50, 30), **fx(2, DELAY, 1, 24, 40, 55, 100, 20))),
]

# famiglia di ogni suono, per la lista e il dettaglio della cella (UI-152)
FAMIGLIA = {
    'Glass Pollen': 'bell', 'Night Greenhouse': 'pad', 'Anther Keys': 'keys', 'Slow Stamen': 'pad',
    'Fern Pluck': 'pluck', 'Copper Reed': 'keys', 'Orbit Choir': 'voice', 'Moss Strings': 'strings',
    'Dew Mallet': 'mallet', 'Tape Fern': 'lo-fi', 'Seed Organ': 'organ', 'Sun Room': 'keys',
    'Linnaeus Lead': 'lead', 'Petal Brass': 'brass', 'Root Drone': 'drone', 'Vetro Pad': 'pad',
    'Grand Piano': 'piano', 'Upright Piano': 'piano', 'FM Piano': 'keys', 'Vibraphone': 'mallet',
    'Marimba': 'mallet', 'Glockenspiel': 'bell', 'Tubular Bells': 'bell', 'Concert Harp': 'harp',
    'Kalimba': 'pluck', 'Harpsichord': 'keys', 'Pipe Organ': 'organ', 'Alto Recorder': 'flute', 'Tenor Sax': 'reed',
    'TX Piano': 'keys', 'Clavisynth': 'keys', 'Knight Upright': 'piano', 'Italian Cembalo': 'keys', 'Lute Stop': 'keys',
    'Grand Organ': 'organ', 'Flute Organ': 'organ', 'Full Organ': 'organ', 'Sop. Recorder': 'flute',
    'Tenor Recorder': 'flute', 'Bass Recorder': 'flute', 'Ocarina': 'flute', 'Harmonica': 'reed', 'Chromatic Harp': 'reed',
    'Saxello': 'reed', 'Didgeridoo': 'drone', 'Strumstick': 'pluck', 'Dan Tranh': 'harp', 'Bowed Psaltery': 'strings',
    'Pluck Psaltery': 'harp', 'Mbira': 'pluck', 'Nyunga Nyunga': 'pluck', 'Kenya Kalimba': 'pluck', 'Hand Chimes': 'bell',
    'Tube Glock': 'bell', 'Bowed Vibes': 'pad', 'Balafon': 'mallet', 'Xylophone': 'mallet', 'Wine Glasses': 'pad',
    'Moonflower': 'pad', 'Thistle Lead': 'lead', 'Lichen Organ': 'organ', 'Nectar EP': 'keys', 'Ivy Pluck': 'pluck',
    'Bramble Brass': 'brass', 'Cocoon Pad': 'pad', 'Spore Bells': 'bell', 'Rootstock': 'lead', 'Birch Keys': 'keys',
    'Pollen Choir': 'voice', 'Reed Marsh': 'keys', 'Clover Strings': 'strings', 'Frost Pad': 'pad', 'Cactus Pluck': 'pluck',
    'Heliotrope': 'lead', 'Underbrush': 'drone', 'Dandelion': 'bell', 'Sundew': 'lo-fi', 'Lotus Flute': 'flute',
    'Pine Organ': 'organ',
    'Nightshade': 'pad', 'Belladonna': 'pad', 'Mandrake Stab': 'stab', 'Dub Moss': 'stab', 'Acid Nettle': 'acid',
    'Hogweed Hoover': 'lead', 'Cypress Saw': 'pad', 'Mycelium': 'pluck', 'Puffball Pulse': 'pluck',
    'Charred Keys': 'keys', 'Charcoal Organ': 'organ', 'Tar Drone': 'drone', 'Wolfsbane Lead': 'lead',
    'Datura Bells': 'bell', 'Bog Rumble': 'drone', 'Blackthorn Sync': 'lead', 'Ironwood Perc': 'stab',
    'Burdock Chords': 'stab',
}
# motore per la UI (ui_model.h: ENGINE_VA, ENGINE_FM, ENGINE_RP, ENGINE_SMP) dal modello della patch
ENGINE_UI = {VA: 'ENGINE_VA', FM: 'ENGINE_FM', RP: 'ENGINE_RP', SMP: 'ENGINE_SMP'}

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
    # 15/10/2026 sera
    ('Taproot', patch(VA, [], GLIDEMODE=2, GLIDE=14, O1SHAPE=SAW, O2SHAPE=SAW, O2DETUNE=68, O2GAIN=45, CUTOFF=52,
        RESONANCE=26, FENV=34, E1A=0, E1D=40, E1S=20, E2A=0, E2D=60, E2S=110, E2R=20, GAIN=68, **fx(1, DRIVE, 18, 30))),
    ('Peat Sub', patch(VA, [], GLIDEMODE=2, O1SHAPE=TRI, O2SHAPE=TRI, O2SEMI=52, O2GAIN=50, CUTOFF=40,
        E2A=1, E2D=64, E2S=127, E2R=24, GAIN=78)),
    ('Bark Bass', patch(VA, [], GLIDEMODE=2, O1SHAPE=PULSE, O1PW=36, O2SHAPE=SAW, O2SEMI=52, O2GAIN=40, CUTOFF=46,
        RESONANCE=36, FENV=52, FVELO=30, E1A=0, E1D=30, E1S=10, E2A=0, E2D=50, E2S=70, E2R=18, GAIN=68)),
    ('Pod Bass', patch(FM, [(ENV[3], D_GAIN(2), 110)], GLIDEMODE=2, FMALG=0, O1PW=127, O1GAIN=0, O2SEMI=52, O2PW=50, O2GAIN=30,
        O3SEMI=64, O3PW=20, O3GAIN=40, O4PW=0, E2A=0, E2D=58, E2S=60, E2R=20, E3A=0, E3D=26, E3S=0, E3R=16, CUTOFF=80, GAIN=72)),
    ('Thorn Bass', patch(VA, [(LFO[1], D_CUTOFF, 70)], GLIDEMODE=2, O1SHAPE=SAW, O2SHAPE=PULSE, O2PW=30, O2DETUNE=70, O2GAIN=55,
        CUTOFF=44, RESONANCE=44, FENV=30, L1SHAPE=1, L1RATE=14, L1MODE=1, E1A=0, E1D=50, E1S=40, E2A=0, E2D=64, E2S=115, E2R=22,
        GAIN=66, **fx(1, DRIVE, 28, 34))),
    ('Moss Sub', patch(RP, [], GLIDEMODE=2, RPICKUP=1, RPHEIGHT=70, RPDISTANCE=40, RPDECAY=90, RPRELEASE=24, RPTONE=40,
        RPVOL=92, GAIN=72, REVSEND=4)),
    # 15/10/2026 notte: bassi cupi e techno (reese, acid, sub alla 808 con la caduta di pitch, rumble, FM)
    ('Reese Root', patch(VA, [(LFO[1], D_OSC(2), 67)], GLIDEMODE=2, O1SHAPE=SAW, O2SHAPE=SAW, O2DETUNE=74, O2GAIN=64,
        O3SHAPE=SAW, O3SEMI=52, O3DETUNE=58, O3GAIN=40, CUTOFF=40, RESONANCE=18, L1SHAPE=0, L1RATE=10, L1MODE=1,
        E2A=0, E2D=64, E2S=120, E2R=22, GAIN=64, **fx(1, DRIVE, 26, 30))),
    ('Acid Sedge', patch(VA, [], GLIDEMODE=3, GLIDE=12, O1SHAPE=SAW, CUTOFF=30, RESONANCE=104, FENV=72, FVELO=52,
        E1A=0, E1D=30, E1S=0, E1R=16, E2A=0, E2D=64, E2S=100, E2R=15, GAIN=64, **fx(1, DRIVE, 46, 50))),
    ('Henbane Sub', patch(VA, [(ENV[3], D_PITCH, 80)], GLIDEMODE=2, O1SHAPE=TRI, CUTOFF=60,
        E3A=0, E3D=16, E3S=0, E3R=10, E2A=0, E2D=84, E2S=40, E2R=40, GAIN=76, **fx(1, DRIVE, 20, 25))),
    ('Fen Rumble', patch(VA, [(LFO[1], D_CUTOFF, 72)], GLIDEMODE=2, O1SHAPE=TRI, O2SHAPE=SAW, O2DETUNE=62, O2GAIN=30,
        NOISE=14, PINK=1, CUTOFF=32, RESONANCE=30, L1SHAPE=6, L1RATE=36, L1MODE=1,
        E2A=4, E2D=64, E2S=120, E2R=40, GAIN=70, REVSEND=10)),
    ('Spore Bass', patch(FM, [(ENV[3], D_GAIN(2), 112)], GLIDEMODE=2, FMALG=1, O1PW=127, O1GAIN=0,
        O2SEMI=64, O2PW=56, O2GAIN=50, O3PW=0, O4PW=0, E2A=0, E2D=40, E2S=20, E2R=15,
        E3A=0, E3D=18, E3S=0, E3R=12, CUTOFF=82, GAIN=72)),
    ('Ironroot', patch(FM, [(LFO[1], D_GAIN(2), 74)], GLIDEMODE=2, FMALG=0, O1PW=127, O1GAIN=0,
        O2SEMI=64, O2PW=48, O2GAIN=20, O3SEMI=52, O3PW=30, O3GAIN=0, O4PW=28, O4GAIN=0, O4FB=70,
        L1SHAPE=1, L1RATE=26, L1MODE=1, E2A=0, E2D=64, E2S=118, E2R=20, CUTOFF=70, RESONANCE=20, GAIN=70,
        **fx(1, DRIVE, 30, 35))),
]


# Livelli pareggiati il 15/10/2026 con `stame-render --suoni`: finestra più forte da 100 ms mentre la nota
# è tenuta, accordo di 5 note a −17 dBFS, basso (una nota, volume del basso 70) a −24 dBFS.
# Correzione in dB, applicata a GAIN: GAIN' = GAIN · 10^(dB/40), perché g_vol = (GAIN/64)².
LIVELLO_DB = {
    # 79 suoni e 12 bassi, misurati il 15/10/2026 sera con il banco della seconda versione
    'Glass Pollen': -0.3, 'Night Greenhouse': -2.0, 'Anther Keys': -0.2, 'Slow Stamen': -7.8,
    'Fern Pluck': 2.0, 'Copper Reed': -9.2, 'Orbit Choir': -2.6, 'Moss Strings': 1.3, 'Dew Mallet': -0.7,
    'Tape Fern': -0.5, 'Seed Organ': 0.7, 'Sun Room': -0.5, 'Linnaeus Lead': 1.7, 'Petal Brass': 0.9,
    'Root Drone': -4.8, 'Vetro Pad': -1.6, 'Grand Piano': 5.5, 'Upright Piano': 4.3, 'FM Piano': 5.0,
    'Vibraphone': 2.3, 'Marimba': 1.8, 'Glockenspiel': 7.2, 'Tubular Bells': 5.9, 'Concert Harp': 3.7,
    'Kalimba': 7.2, 'Harpsichord': 3.7, 'Pipe Organ': -8.3, 'Alto Recorder': 0.8, 'Tenor Sax': 2.9,
    'TX Piano': 2.3, 'Clavisynth': 6.1, 'Knight Upright': 4.4, 'Italian Cembalo': 5.1, 'Lute Stop': 6.5,
    'Grand Organ': 0.7, 'Flute Organ': -6.0, 'Full Organ': -2.4, 'Sop. Recorder': -1.2,
    'Tenor Recorder': 1.2, 'Bass Recorder': 1.5, 'Ocarina': -2.0, 'Harmonica': 5.6, 'Chromatic Harp': 4.7,
    'Saxello': 2.4, 'Didgeridoo': 15.5, 'Strumstick': 6.5, 'Dan Tranh': 5.9, 'Bowed Psaltery': 9.6,
    'Pluck Psaltery': 8.9, 'Mbira': 9.0, 'Nyunga Nyunga': 10.9, 'Kenya Kalimba': 8.8, 'Hand Chimes': 0.7,
    'Tube Glock': 7.3, 'Bowed Vibes': -0.5, 'Balafon': 10.5, 'Xylophone': 9.1, 'Wine Glasses': -1.5,    # i bicchieri: l'attacco lento inganna la misura
    # terza ondata, misurata il 15/10/2026 notte (e il Tube Glock dopo il cambio d'ottava del banco)
    'Nightshade': -2.5, 'Belladonna': -1.3, 'Mandrake Stab': -1.4, 'Dub Moss': 3.3, 'Acid Nettle': 1.2,
    'Hogweed Hoover': 2.4, 'Cypress Saw': 1.3, 'Mycelium': 3.8, 'Puffball Pulse': 3.9, 'Charred Keys': -5.9,
    'Charcoal Organ': 2.5, 'Tar Drone': -8.4, 'Wolfsbane Lead': -0.1, 'Datura Bells': -3.7, 'Bog Rumble': -2.7,
    'Blackthorn Sync': 10.1, 'Ironwood Perc': 4.4, 'Burdock Chords': 0.7,
    'Reese Root': 2.0, 'Acid Sedge': 1.3, 'Henbane Sub': 4.3, 'Fen Rumble': 3.5, 'Spore Bass': 5.7, 'Ironroot': 1.7,
    'Moonflower': -2.8, 'Thistle Lead': 4.7, 'Lichen Organ': 1.5, 'Nectar EP': 0.4, 'Ivy Pluck': 1.7,
    'Bramble Brass': -1.8, 'Cocoon Pad': -5.2, 'Spore Bells': -2.2, 'Rootstock': -3.7, 'Birch Keys': 0.3,
    'Pollen Choir': 0.1, 'Reed Marsh': -3.3, 'Clover Strings': -0.8, 'Frost Pad': 1.2, 'Cactus Pluck': 0.4,
    'Heliotrope': 3.8, 'Underbrush': -5.2, 'Dandelion': 2.1, 'Sundew': -3.1, 'Lotus Flute': -4.2,
    'Pine Organ': -2.7, 'Round Root': 7.3, 'Sub Floor': 5.1, 'Pluck Bass': 6.1, 'Reed Bass': -3.3,
    'Velvet Sub': 6.4, 'Wood Bass': 5.7, 'Taproot': 3.3, 'Peat Sub': 3.0, 'Bark Bass': 4.5, 'Pod Bass': 4.4,
    'Thorn Bass': 1.6, 'Moss Sub': 0.9,
}


# Perform di default di ogni suono (ACC-162; colonne perform_mode e perform_amount di bank.idx, SND-131).
# Modi di ACC-160: 0 Off, 1 Strum, 2 Strum 2 Oct, 3 Slop, 4 Arpeggiate, 5 Arp 2 Oct, 6 Pattern, 7 Harp.
# Scelte di Stame per i suoi suoni, non dati dell'Orchid. I bassi non hanno performance (ACC-142).
OFF, STRUM, STRUM2, SLOP, ARP, ARP2, PATTERN, HARP = range(8)
PERFORM = {
    'Glass Pollen': (HARP, 3), 'Anther Keys': (STRUM, 2), 'Fern Pluck': (ARP, 6), 'Copper Reed': (STRUM, 3),
    'Moss Strings': (STRUM2, 4), 'Dew Mallet': (PATTERN, 5), 'Tape Fern': (SLOP, 4), 'Sun Room': (PATTERN, 2),
    'Linnaeus Lead': (ARP2, 4), 'Petal Brass': (STRUM, 1),
    'Grand Piano': (STRUM, 2), 'FM Piano': (STRUM, 3), 'Vibraphone': (PATTERN, 3), 'Glockenspiel': (HARP, 3),
    'Concert Harp': (HARP, 4), 'Kalimba': (PATTERN, 13), 'Harpsichord': (STRUM, 2), 'Marimba': (ARP, 6),
    'TX Piano': (STRUM, 2), 'Clavisynth': (PATTERN, 5), 'Italian Cembalo': (STRUM, 3), 'Lute Stop': (ARP, 4),
    'Strumstick': (STRUM, 4), 'Dan Tranh': (HARP, 5), 'Pluck Psaltery': (ARP2, 3), 'Mbira': (PATTERN, 9),
    'Nyunga Nyunga': (PATTERN, 11), 'Kenya Kalimba': (ARP, 5), 'Hand Chimes': (HARP, 2), 'Tube Glock': (HARP, 3),
    'Balafon': (ARP, 6), 'Xylophone': (STRUM, 1), 'Thistle Lead': (ARP2, 4), 'Ivy Pluck': (ARP, 6),
    'Bramble Brass': (STRUM, 1), 'Spore Bells': (HARP, 4), 'Birch Keys': (STRUM, 2), 'Cactus Pluck': (PATTERN, 7),
    'Heliotrope': (ARP, 3), 'Dandelion': (HARP, 3), 'Sundew': (SLOP, 5), 'Nectar EP': (STRUM, 2),
    'Acid Nettle': (ARP, 4), 'Puffball Pulse': (ARP2, 5), 'Mycelium': (PATTERN, 9), 'Ironwood Perc': (PATTERN, 6),
    'Datura Bells': (STRUM, 2), 'Charred Keys': (STRUM, 1),
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
    c += ['/* nome, motore per la UI e famiglia di ogni suono (UI-152) */',
          'const vet_snd_info_t vet_sound_info[%d] STAME_ROM = {' % len(SUONI)]
    c += ['    { "%s", %s, "%s" },' % (nome, ENGINE_UI[p[IDX['MODEL']]], FAMIGLIA.get(nome, '')) for nome, p in SUONI]
    c += ['};', '', 'const char *const vet_bass_name[%d] STAME_ROM = {' % len(BASSI)]
    c += ['    "%s",' % nome for nome, _ in BASSI]
    c += ['};', '']
    p = os.path.join(RADICE, 'src', 'platform', 'vetrina', 'patch_vetrina.c')
    open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(c))
    h = ['/* patch_vetrina.h — quanti suoni e bassi ha la vetrina. Generato da tools/patch.py. */',
         '#ifndef STAME_PATCH_VETRINA_H', '#define STAME_PATCH_VETRINA_H',
         '#define VET_N_SOUNDS  %d' % len(SUONI), '#define VET_N_BASSES  %d' % len(BASSI),
         '#endif', '']
    open(os.path.join(RADICE, 'src', 'platform', 'vetrina', 'patch_vetrina.h'), 'w', encoding='utf-8', newline='\n').write('\n'.join(h))
    print('patch: %d suoni (%d campionati), %d bassi' % (len(SUONI), sum(1 for _, p in SUONI if p[IDX['MODEL']] == SMP), len(BASSI)))


if __name__ == '__main__':
    main()
