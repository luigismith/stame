"""patch.py — le patch di Stame per la vetrina (specifica 20, SND-454 e §2.7).

Ogni suono è descritto per nome di parametro (colonna "Nome" di §2.2) a partire dalla patch INIT
del suo modello. Lo script scrive:
  - assets/patch/sound/ e assets/patch/bass/: un .inc per suono, nel formato dell'editor dell'originale, e l'indice bank.idx (SND-131);
  - src/platform/vetrina/patch_vetrina.c: le stesse patch come tabelle per la vetrina.
Sono patch di Stame, progettate sul carattere del nome: nessun preset dell'originale.

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

# ---- quarta ondata (18/10/2026), Luigi: «altri preset soprattutto di suoni ma anche di batterie, più cupi,
# più profondi, più grevi, più bassi, più acidi». Tre linee acid (dente di sega, quadra, con la sub), pad e
# drone con il riverbero chiuso, stab dub e industriali, un organo e un coro scuri, campane inarmoniche basse ----
SUONI += [
    ('Hemlock Acid', patch(VA, [], GLIDEMODE=3, GLIDE=16, O1SHAPE=SAW,
        CUTOFF=24, RESONANCE=114, FENV=86, FVELO=60, FKT=24, E1A=0, E1D=26, E1S=0, E1R=18,
        E2A=0, E2D=64, E2S=112, E2R=16, GAIN=60, REVSEND=10, **fx(1, DRIVE, 58, 52), **fx(2, DELAY, 2, 20, 34, 64, 70, 24))),
    ('Aconite Square', patch(VA, [], GLIDEMODE=3, GLIDE=12, O1SHAPE=PULSE, O1PW=64,
        CUTOFF=28, RESONANCE=108, FENV=78, FVELO=56, FKT=24, E1A=0, E1D=34, E1S=0, E1R=20,
        E2A=0, E2D=64, E2S=110, E2R=18, GAIN=60, REVSEND=14, **fx(1, DRIVE, 50, 44), **fx(2, DELAY, 1, 24, 40, 60, 90, 26))),
    ('Mandragora Acid', patch(VA, [], GLIDEMODE=3, GLIDE=18, O1SHAPE=SAW, O2SHAPE=PULSE, O2SEMI=52, O2PW=50, O2GAIN=40,
        CUTOFF=22, RESONANCE=100, FENV=70, FVELO=50, FKT=20, E1A=0, E1D=40, E1S=6, E1R=24,
        E2A=0, E2D=64, E2S=110, E2R=20, GAIN=60, REVSEND=12, **fx(1, DRIVE, 64, 40))),
    ('Yew Shadow', patch(VA, [(LFO[1], D_CUTOFF, 80), (LFO[2], D_PAN, 86)],
        O1SHAPE=SAW, O1DETUNE=58, O2SHAPE=SAW, O2DETUNE=70, O2GAIN=60, O3SHAPE=SAW, O3SEMI=52, O3DETUNE=62, O3GAIN=52,
        CUTOFF=26, RESONANCE=18, FENV=12, FKT=34, E1A=90, E1D=90, E1S=80, E1R=96, E2A=92, E2D=80, E2S=120, E2R=104,
        L1SHAPE=1, L1RATE=10, L1MODE=1, L2SHAPE=0, L2RATE=8, L2MODE=1, GAIN=62, REVSEND=86, REVSIZE=126, REVLP=44,
        **fx(1, ENSEMBLE, 38, 72, 60, 42))),
    ('Black Hellebore', patch(FM, [(LFO[1], D_GAIN(2), 86), (LFO[2], D_PAN, 92), (LFO[3], D_CUTOFF, 76)], FMALG=0,
        O1PW=127, O1GAIN=0, O2SEMI=52, O2PW=64, O2GAIN=0, O3SEMI=40, O3PW=36, O3GAIN=0, O4PW=40, O4GAIN=0, O4FB=96,
        L1SHAPE=1, L1RATE=9, L1MODE=1, L2SHAPE=0, L2RATE=6, L2MODE=1, L3SHAPE=0, L3RATE=5, L3MODE=1,
        CUTOFF=46, RESONANCE=30, E2A=96, E2D=64, E2S=127, E2R=108, GAIN=56, REVSEND=90, REVSIZE=127, REVLP=40,
        **fx(2, DELAY, 0, 34, 70, 40, 90, 0))),
    ('Deadnettle Dub', patch(VA, [], O1SHAPE=SAW, O2SHAPE=PULSE, O2PW=44, O2DETUNE=66, O2GAIN=50,
        CUTOFF=26, RESONANCE=34, FENV=46, FKT=34, E1A=0, E1D=40, E1S=6, E1R=36, E2A=0, E2D=50, E2S=0, E2R=40,
        GAIN=66, REVSEND=76, REVSIZE=124, REVLP=50, **fx(1, CHORUS, 14, 36, 80), **fx(2, DELAY, 0, 46, 84, 40, 110, 50))),
    ('Peat Choir', patch(FM, [(LFO[1], D_PITCH, 69), (LFO[2], D_GAIN(3), 78)], FMALG=4,
        O1PW=127, O1GAIN=0, O2SEMI=64, O2PW=56, O2GAIN=0, O3SEMI=52, O3PW=48, O3GAIN=0, O4SEMI=59, O4PW=18, O4GAIN=0,
        L1SHAPE=0, L1RATE=70, L1MODE=1, L2SHAPE=0, L2RATE=16, L2MODE=1, CUTOFF=60, RESONANCE=10,
        E2A=74, E2D=64, E2S=122, E2R=86, GAIN=58, REVSEND=80, REVSIZE=124, REVLP=52, **fx(1, ENSEMBLE, 30, 76, 50, 30))),
    ('Spleenwort Organ', patch(FM, [(ENV[3], D_GAIN(2), 74)], FMALG=7,
        O1PW=118, O1GAIN=0, O2SEMI=64, O2PW=92, O2GAIN=0, O3SEMI=52, O3PW=84, O3GAIN=0, O4SEMI=71, O4PW=40, O4GAIN=0,
        E2A=1, E2D=64, E2S=127, E2R=12, E3A=0, E3D=20, E3S=40, E3R=10, CUTOFF=70, GAIN=56, REVSEND=40, REVLP=60,
        **fx(1, DRIVE, 30, 26), **fx(2, DELAY, 0, 22, 30, 50, 60, 0))),
    ('Bitterroot Lead', patch(VA, [(WHEEL, D_MOD7, 78), (0, 0, 64), (0, 0, 64), (0, 0, 64), (0, 0, 64), (0, 0, 64),
        (LFO[1], D_PITCH, 64)], GLIDEMODE=2, GLIDE=16,
        O1SHAPE=SAW, O2SHAPE=SAW, O2SEMI=52, O2DETUNE=66, O2GAIN=60,
        CUTOFF=40, RESONANCE=50, FENV=44, FVELO=30, E1A=0, E1D=54, E1S=36, E1R=30, E2A=0, E2D=64, E2S=116, E2R=30,
        L1SHAPE=0, L1RATE=76, L1MODE=1, GAIN=60, REVSEND=26, **fx(1, DRIVE, 44, 36), **fx(2, DELAY, 1, 22, 36, 50, 70, 20))),
    ('Witchgrass Pulse', patch(VA, [(LFO[1], D_PW(1), 80)], O1SHAPE=PULSE, O1PW=18,
        CUTOFF=30, RESONANCE=52, FENV=58, FVELO=34, E1A=0, E1D=24, E1S=0, E1R=18, E2A=0, E2D=34, E2S=0, E2R=22,
        L1SHAPE=1, L1RATE=16, L1MODE=1, GAIN=66, REVSEND=30, REVLP=56, **fx(2, DELAY, 2, 30, 50, 56, 100, 24))),
    ('Mire Bells', patch(FM, [(ENV[3], D_GAIN(2), 116), (ENV[4], D_GAIN(4), 100)], FMALG=2,
        O1PW=127, O1GAIN=0, O2SEMI=71, O2DETUNE=58, O2PW=46, O2GAIN=60, O3SEMI=46, O3PW=38, O3GAIN=40,
        O4SEMI=83, O4PW=20, O4GAIN=50,
        E2A=0, E2D=100, E2S=0, E2R=86, E3A=0, E3D=44, E3S=0, E3R=34, E4A=0, E4D=18, E4S=0, E4R=14,
        CUTOFF=60, GAIN=66, REVSEND=76, REVSIZE=126, REVLP=46, **fx(2, DELAY, 0, 30, 50, 44, 110, 10))),
    ('Undertow', patch(VA, [(LFO[1], D_CUTOFF, 76)], O1SHAPE=TRI, O2SHAPE=SAW, O2SEMI=52, O2DETUNE=62, O2GAIN=56,
        O3SHAPE=SAW, O3SEMI=52, O3DETUNE=67, O3GAIN=40, CUTOFF=30, RESONANCE=24, FENV=10,
        E1A=84, E1D=90, E1S=90, E1R=96, E2A=86, E2D=80, E2S=122, E2R=104, L1SHAPE=0, L1RATE=8, L1MODE=1,
        GAIN=62, REVSEND=84, REVSIZE=127, REVLP=40, **fx(1, CHORUS, 18, 60, 110))),
    ('Tar Pit Keys', patch(RP, [], RPICKUP=2, RPHEIGHT=80, RPDISTANCE=60, RPDECAY=98, RPRELEASE=36, RPTONE=20,
        RPVELCURVE=95, RPCLANK=8, RPHAMMER=16, RPKEYOFF=14, RPTREMOLO=34, RPTREMRATE=36, RPVOL=88, REVSEND=54,
        REVSIZE=114, REVLP=50, **fx(1, DRIVE, 40, 24), **fx(2, DELAY, 0, 26, 44, 46, 80, 16))),
    ('Nightjar Brass', patch(VA, [], O1SHAPE=SAW, O2SHAPE=SAW, O2DETUNE=70, O2GAIN=60, O3SHAPE=SAW, O3SEMI=52, O3DETUNE=60,
        O3GAIN=50, CUTOFF=30, RESONANCE=16, FENV=50, FVELO=40, E1A=30, E1D=56, E1S=50, E1R=44,
        E2A=24, E2D=56, E2S=110, E2R=44, GAIN=60, REVSEND=50, REVLP=56, **fx(1, DRIVE, 20, 24))),
    ('Gravel Stab', patch(VA, [], O1SHAPE=SAW, O2SHAPE=SAW, O2SEMI=52, O2GAIN=50, NOISE=40,
        CUTOFF=34, RESONANCE=40, FENV=60, FVELO=40, E1A=0, E1D=28, E1S=0, E1R=22, E2A=0, E2D=40, E2S=0, E2R=26,
        GAIN=64, REVSEND=46, REVSIZE=104, REVLP=58, **fx(1, DRIVE, 70, 36), **fx(2, DELAY, 1, 28, 42, 50, 90, 24))),
    ('Ink Cap Drone', patch(VA, [(LFO[1], D_CUTOFF, 80), (LFO[2], D_PAN, 90)], O1SHAPE=TRI, O1SEMI=40, O2SHAPE=SAW,
        O2SEMI=52, O2DETUNE=60, O2GAIN=34, NOISE=30, PINK=1, CUTOFF=24, RESONANCE=60,
        L1SHAPE=6, L1RATE=20, L1MODE=1, L2SHAPE=0, L2RATE=7, L2MODE=1,
        E2A=90, E2D=64, E2S=127, E2R=104, GAIN=62, REVSEND=90, REVSIZE=127, REVLP=38)),
]

# ---- quinta ondata (18/10/2026 sera), Luigi: «con i preset arriviamo a 150, gli ultimi 25 devono essere
# SORPRENDENTI». Dodici suoni che mancavano (un piano che diventa pad, un carillon, un harmonium, uno steel
# drum, un clavinet, un e-bow, un sitar, una cascata d'arpa, una string machine, un pizzicato, un pianino
# giocattolo, una chitarra di nylon) e poi venticinque che fanno una cosa che non ti aspetti: un bordone
# fisso sotto ogni accordo, bicchieri stonati a caso, salti d'ottava, una sirena in sync, un contatore
# Geiger sul filtro, accordi di solo vento, il suono al contrario, un pad che risponde al tocco, un timbro
# che sboccia una volta sola, la tastiera a rovescio, lo zap, il fischietto a coulisse, le lucciole, l'eco
# che non finisce, la ruggine, il vinile deformato, il canto di gola, la pioggia, il robot, il fuoco fatuo,
# la dionea che scatta, il nastro che si ferma, il pad che parla, il megafono e il fiore cadavere ----
L_SINE, L_TRI, L_SQU, L_SAW, L_SAWN, L_RAND, L_SH = range(7)        # forme degli LFO (SND-411)
L_RESET, L_FREE, L_MONO, L_ONESHOT = range(4)                       # modi (SND-412)
D_ENV1T, D_ENV2T, D_NOISE = 23, 25, 33                              # altre destinazioni (§8.3)
BANDPASS = 2
SUONI += [
    # 114-125: i dodici che mancavano
    ('Hothouse Piano', patch(SMP, [], SMPSET=set_idx('piano_kawai'), GVELO=60, FTYPE=1, CUTOFF=70, FVELO=30,
        E2A=78, E2D=64, E2S=127, E2R=70, GAIN=76, REVSEND=70, REVSIZE=120, **fx(1, CHORUS, 22, 55, 110))),
    ('Seedling Box', patch(SMP, [], SMPSET=set_idx('glock'), GVELO=70, HIGHPASS=40, E2A=0, E2D=64, E2S=127, E2R=50,
        GAIN=72, REVSEND=50, REVSIZE=108, **fx(2, DELAY, 1, 36, 44, 80, 127, 30))),
    ('Harmonium Moss', patch(SMP, [], SMPSET=set_idx('harmonica'), GVELO=20, FTYPE=1, CUTOFF=84,
        E2A=40, E2D=64, E2S=127, E2R=44, GAIN=74, REVSEND=44, REVSIZE=104, **fx(1, TREMOLO, 84, 30, 20))),
    ('Steel Petal', patch(FM, [(ENV[3], D_GAIN(3), 118), (ENV[4], D_GAIN(4), 110)], FMALG=2,
        O1PW=127, O1GAIN=20, O2SEMI=76, O2PW=90, O2GAIN=20, O3SEMI=83, O3PW=60, O3GAIN=0, O4SEMI=95, O4PW=45, O4GAIN=0,
        E2A=0, E2D=80, E2S=20, E2R=50, E3A=0, E3D=30, E3S=0, E3R=20, E4A=0, E4D=18, E4S=0, E4R=12,
        GAIN=66, REVSEND=50, REVSIZE=110, **fx(1, CHORUS, 20, 25, 80))),
    ('Clav Vine', patch(VA, [], O1SHAPE=PULSE, O1PW=18, O2SHAPE=PULSE, O2PW=22, O2SEMI=76, O2GAIN=30, HIGHPASS=50,
        CUTOFF=60, RESONANCE=30, FENV=50, FVELO=50, FKT=70, E1A=0, E1D=26, E1S=0, E1R=20,
        E2A=0, E2D=64, E2S=90, E2R=10, GAIN=64, REVSEND=15, **fx(1, PHASER, 40, 40, 60, 50))),
    ('Ebow Fern', patch(VA, [(LFO[1], D_PITCH, 68)], O1SHAPE=SAW, O1GAIN=50, O2SHAPE=TRI, O2DETUNE=70, O2GAIN=50,
        O3SHAPE=SAW, O3SEMI=76, O3DETUNE=60, O3GAIN=20, CUTOFF=70, RESONANCE=14, FENV=20,
        E1A=80, E1D=80, E1S=80, E1R=70, E2A=84, E2D=64, E2S=127, E2R=66, L1SHAPE=L_SINE, L1RATE=72, L1MODE=L_RESET,
        GAIN=58, REVSEND=66, REVSIZE=116, **fx(1, PHASER, 24, 45, 50, 40), **fx(2, DELAY, 0, 30, 50, 70, 100, 0))),
    ('Sitar Tranh', patch(SMP, [], SMPSET=set_idx('dan_tranh'), GVELO=80, FTYPE=BANDPASS, CUTOFF=88, RESONANCE=48, FKT=40,
        E2A=0, E2D=64, E2S=127, E2R=50, GAIN=76, REVSEND=50, REVSIZE=110,
        **fx(1, DRIVE, 46, 30), **fx(2, DELAY, 2, 24, 42, 64, 110, 20))),
    ('Harp Rain', patch(SMP, [(RND, D_PAN, 110)], SMPSET=set_idx('harp'), SMPSTART=8, GVELO=90,
        E2A=0, E2D=64, E2S=127, E2R=60, GAIN=74, REVSEND=55, REVSIZE=116, **fx(2, DELAY, 2, 50, 100, 90, 127, 40))),
    ('Solina Sedge', patch(VA, [], O1SHAPE=SAW, O1DETUNE=61, O2SHAPE=SAW, O2DETUNE=67, O2GAIN=60,
        O3SHAPE=SAW, O3SEMI=52, O3DETUNE=64, O3GAIN=36, O4SHAPE=SAW, O4SEMI=76, O4GAIN=18, HIGHPASS=30,
        CUTOFF=78, RESONANCE=6, FKT=40, E1A=40, E1D=64, E1S=100, E1R=60, E2A=40, E2D=64, E2S=120, E2R=58,
        GAIN=54, REVSEND=56, REVSIZE=112, **fx(1, ENSEMBLE, 36, 100, 66, 50), **fx(2, PHASER, 20, 36, 40, 60))),
    ('Pizzicato Moss', patch(VA, [], O1SHAPE=TRI, O1GAIN=64, O2SHAPE=SAW, O2DETUNE=66, O2GAIN=40, NOISE=18,
        CUTOFF=52, RESONANCE=22, FENV=70, FVELO=50, FKT=70, E1A=0, E1D=14, E1S=0, E1R=12,
        E2A=0, E2D=30, E2S=0, E2R=22, GAIN=68, REVSEND=36, REVSIZE=104)),
    ('Toy Thicket', patch(RP, [], RPICKUP=1, RPHEIGHT=50, RPDISTANCE=20, RPDECAY=60, RPRELEASE=20, RPTONE=110,
        RPVELCURVE=80, RPCLANK=90, RPCLANCURVE=80, RPCKT=60, RPHAMMER=60, RPKEYOFF=40, RPVOL=84,
        REVSEND=40, REVSIZE=100, **fx(2, DELAY, 1, 20, 30, 80, 80, 30))),
    ('Nylon Bramble', patch(VA, [], O1SHAPE=TRI, O1GAIN=60, O2SHAPE=SAW, O2DETUNE=70, O2GAIN=30,
        CUTOFF=58, RESONANCE=18, FENV=58, FVELO=44, FKT=60, E1A=0, E1D=22, E1S=0, E1R=20,
        E2A=0, E2D=70, E2S=0, E2R=36, GAIN=66, REVSEND=40, REVSIZE=106,
        **fx(1, CHORUS, 18, 22, 60), **fx(2, DELAY, 1, 14, 20, 70, 80, 20))),
    # 126-150: i venticinque che sorprendono
    ('Tanpura Root', patch(VA, [(LFO[1], D_GAIN(4), 90)],                 # l'oscillatore 4 è fisso: un Do2 sotto ogni accordo
        O1SHAPE=SAW, O1GAIN=50, O2SHAPE=SAW, O2DETUNE=70, O2GAIN=44, O4SHAPE=SAW, O4KT=0, O4SEMI=40, O4GAIN=56,
        L1SHAPE=L_SINE, L1RATE=20, L1MODE=L_FREE, CUTOFF=58, RESONANCE=24, FENV=16, FKT=30,
        E1A=60, E1D=64, E1S=90, E1R=70, E2A=56, E2D=64, E2S=127, E2R=80, GAIN=58, REVSEND=70, REVSIZE=120, REVLP=80,
        **fx(1, DRIVE, 24, 28), **fx(2, DELAY, 0, 20, 40, 60, 90, 0))),
    ('Drunk Glasses', patch(SMP, [(RND, D_PITCH, 84), (RND, D_PAN, 110), (LFO[1], D_PITCH, 72)],   # ogni nota stonata a caso
        SMPSET=set_idx('wine_glasses'), GVELO=30, L1SHAPE=L_RAND, L1RATE=28, L1MODE=L_RESET,
        E2A=50, E2D=64, E2S=127, E2R=80, GAIN=72, REVSEND=80, REVSIZE=127, REVLP=90, **fx(1, CHORUS, 16, 50, 110))),
    ('Octave Hopper', patch(VA, [(LFO[1], D_PITCH, 109)],               # onda quadra sul pitch: ±6 = un'ottava di salto
        O1SHAPE=PULSE, O1PW=40, O2SHAPE=SAW, O2DETUNE=68, O2GAIN=40, L1SHAPE=L_SQU, L1RATE=76, L1MODE=L_MONO,
        CUTOFF=66, RESONANCE=20, FENV=30, FVELO=30, E1A=0, E1D=50, E1S=40, E1R=30, E2A=0, E2D=64, E2S=110, E2R=30,
        GAIN=60, REVSEND=36, **fx(2, DELAY, 2, 24, 36, 70, 110, 20))),
    ('Siren Thorn', patch(VA, [(LFO[1], D_OSC(4), 112)],                # sync: l'LFO spazza l'oscillatore sincronizzato
        O1SHAPE=0, O1GAIN=0, O3SHAPE=SAW, O3GAIN=0, O4SHAPE=SAW, O4SEMI=80, O4SYNC=1, O4GAIN=64,
        L1SHAPE=L_TRI, L1RATE=36, L1MODE=L_MONO, CUTOFF=90, RESONANCE=10, E2A=4, E2D=64, E2S=118, E2R=36,
        GAIN=58, REVSEND=36, REVSIZE=110, **fx(1, PHASER, 30, 30, 40, 60), **fx(2, DELAY, 1, 22, 34, 60, 80, 10))),
    ('Geiger Garden', patch(VA, [(LFO[1], D_CUTOFF, 112), (LFO[2], D_PAN, 100), (LFO[1], D_Q, 86)],   # S&H sul filtro
        O1SHAPE=SAW, O2SHAPE=PULSE, O2PW=30, O2SEMI=52, O2GAIN=50, L1SHAPE=L_SH, L1RATE=92, L1MODE=L_RESET,
        L2SHAPE=L_SH, L2RATE=80, L2MODE=L_RESET, CUTOFF=50, RESONANCE=80, FENV=20,
        E2A=4, E2D=64, E2S=118, E2R=40, GAIN=58, REVSEND=40, REVSIZE=108, **fx(2, DELAY, 2, 26, 40, 70, 120, 20))),
    ('Wind Chords', patch(VA, [(LFO[1], D_CUTOFF, 68)],                 # solo rumore: il passa-banda segue la nota
        O1GAIN=0, NOISE=127, PINK=0, FTYPE=BANDPASS, CUTOFF=47, RESONANCE=122, FKT=127,
        L1SHAPE=L_RAND, L1RATE=40, L1MODE=L_RESET, E2A=60, E2D=64, E2S=127, E2R=70,
        GAIN=90, REVSEND=70, REVSIZE=120)),
    ('Rewind Fern', patch(VA, [],                                       # sale piano e si spegne di colpo: suona al contrario
        O1SHAPE=SAW, O2SHAPE=SAW, O2DETUNE=70, O2GAIN=55, O3SHAPE=PULSE, O3SEMI=76, O3PW=40, O3GAIN=24,
        CUTOFF=40, RESONANCE=16, FENV=60, FKT=40, E1A=104, E1D=64, E1S=127, E1R=8,
        E2A=104, E2D=64, E2S=127, E2R=6, GAIN=60, REVSEND=50, REVSIZE=112, **fx(2, DELAY, 1, 40, 56, 80, 110, 20))),
    ('Mimosa', patch(VA, [(VEL, D_ENV2T, 0), (VEL, D_ENV1T, 0), (VEL, D_CUTOFF, 100)],   # tocco leggero: sboccia piano; forte: subito
        O1SHAPE=TRI, O1GAIN=60, O2SHAPE=SAW, O2DETUNE=68, O2GAIN=40, O3SHAPE=SAW, O3SEMI=76, O3DETUNE=60, O3GAIN=20,
        CUTOFF=64, RESONANCE=12, FENV=30, FVELO=40, GVELO=50, E1A=96, E1D=64, E1S=90, E1R=50,
        E2A=100, E2D=64, E2S=127, E2R=60, GAIN=60, REVSEND=56, REVSIZE=112, **fx(1, CHORUS, 22, 40, 100))),
    ('Bloom Cycle', patch(FM, [(LFO[2], D_GAIN(2), 118), (LFO[2], D_GAIN(3), 100)], FMALG=0,   # un LFO a colpo solo apre e chiude l'FM
        O1PW=127, O1GAIN=0, O2SEMI=64, O2PW=30, O2GAIN=0, O3SEMI=76, O3PW=40, O3GAIN=0, O4SEMI=83, O4PW=30, O4GAIN=0, O4FB=30,
        L2SHAPE=L_SINE, L2RATE=22, L2MODE=L_ONESHOT, CUTOFF=100, E2A=50, E2D=64, E2S=127, E2R=80,
        GAIN=58, REVSEND=72, REVSIZE=122, **fx(1, CHORUS, 20, 50, 120))),
    ('Upside Down', patch(VA, [(KEY, D_CUTOFF, 0), (KEY, D_PAN, 0), (KEY, D_Q, 0)],   # in alto scuro e a sinistra, in basso chiaro e a destra
        O1SHAPE=SAW, O2SHAPE=PULSE, O2PW=40, O2DETUNE=67, O2GAIN=50, O3SHAPE=SAW, O3SEMI=52, O3GAIN=30,
        CUTOFF=78, RESONANCE=20, FENV=20, FKT=0, E1A=0, E1D=60, E1S=60, E1R=40, E2A=2, E2D=64, E2S=115, E2R=40,
        GAIN=60, REVSEND=44, REVSIZE=108, **fx(1, ENSEMBLE, 30, 50, 50, 30))),
    ('Zap Nettle', patch(VA, [(ENV[3], D_PITCH, 127), (ENV[3], D_PITCH, 127)],   # due ottave di caduta a ogni colpo
        O1SHAPE=SAW, O2SHAPE=PULSE, O2PW=50, O2DETUNE=72, O2GAIN=40, E3A=0, E3D=22, E3S=0, E3R=10,
        CUTOFF=60, RESONANCE=40, FENV=60, FVELO=40, E1A=0, E1D=30, E1S=0, E1R=20, E2A=0, E2D=40, E2S=0, E2R=30,
        GAIN=62, REVSEND=40, REVSIZE=106, **fx(1, DRIVE, 30, 30), **fx(2, DELAY, 2, 30, 46, 70, 120, 30))),
    ('Slide Whistle', patch(VA, [(ENV[3], D_PITCH, 0), (LFO[1], D_PITCH, 76)], GLIDEMODE=3, GLIDE=44,   # ogni nota arriva da sotto
        O1SHAPE=TRI, O1GAIN=64, NOISE=6, E3A=0, E3D=36, E3S=0, E3R=20, L1SHAPE=L_SINE, L1RATE=74, L1MODE=L_RESET,
        CUTOFF=74, E2A=10, E2D=64, E2S=120, E2R=30, GAIN=64, REVSEND=46, REVSIZE=108, **fx(2, DELAY, 1, 20, 30, 70, 60, 0))),
    ('Firefly Pad', patch(VA, [(LFO[1], D_VOLUME, 20), (LFO[1], D_CUTOFF, 100)],   # il pad lampeggia, tutto l'accordo insieme
        O1SHAPE=SAW, O2SHAPE=SAW, O2DETUNE=70, O2GAIN=50, O3SHAPE=SAW, O3SEMI=76, O3DETUNE=60, O3GAIN=24,
        L1SHAPE=L_SQU, L1RATE=82, L1MODE=L_MONO, CUTOFF=60, RESONANCE=18, FENV=20, E1A=0, E1D=64, E1S=100, E1R=60,
        E2A=20, E2D=64, E2S=127, E2R=56, GAIN=60, REVSEND=60, REVSIZE=118,
        **fx(1, CHORUS, 24, 50, 110), **fx(2, DELAY, 2, 30, 40, 70, 127, 20))),
    ('Everlasting Moss', patch(VA, [],                                  # l'eco non finisce più
        O1SHAPE=SAW, O2SHAPE=SAW, O2DETUNE=67, O2GAIN=50, CUTOFF=44, RESONANCE=26, FENV=50, FKT=36,
        E1A=0, E1D=40, E1S=10, E1R=40, E2A=0, E2D=50, E2S=0, E2R=40, GAIN=62, REVSEND=70, REVSIZE=124, REVLP=60,
        **fx(1, CHORUS, 14, 36, 80), **fx(2, DELAY, 1, 60, 125, 54, 100, 40))),
    ('Rust Chords', patch(FM, [(ENV[3], D_GAIN(2), 110), (ENV[3], D_GAIN(3), 100), (LFO[1], D_PAN, 90)], FMALG=1,   # rapporti stonati: metallo
        O1PW=127, O1GAIN=0, O2SEMI=71, O2DETUNE=90, O2PW=72, O2GAIN=30, O3SEMI=58, O3DETUNE=40, O3PW=60, O3GAIN=30,
        O4SEMI=85, O4PW=40, O4GAIN=40, O4FB=60, E2A=0, E2D=90, E2S=30, E2R=70, E3A=0, E3D=60, E3S=20, E3R=40,
        L1SHAPE=L_SINE, L1RATE=30, L1MODE=L_RESET, CUTOFF=86, GAIN=62, REVSEND=62, REVSIZE=120, REVLP=70,
        **fx(2, DELAY, 0, 24, 40, 50, 100, 10))),
    ('Warped Vinyl', patch(VA, [(LFO[1], D_PITCH, 86), (LFO[2], D_CUTOFF, 90), (LFO[3], D_VOLUME, 84)],   # il disco deformato
        O1SHAPE=SAW, O2SHAPE=PULSE, O2PW=40, O2DETUNE=66, O2GAIN=44, O3SHAPE=TRI, O3SEMI=52, O3GAIN=30, NOISE=8, PINK=1,
        L1SHAPE=L_RAND, L1RATE=30, L1MODE=L_MONO, L2SHAPE=L_RAND, L2RATE=24, L2MODE=L_FREE, L3SHAPE=L_SINE, L3RATE=66, L3MODE=L_FREE,
        CUTOFF=66, RESONANCE=10, FENV=10, E1A=30, E2A=16, E2D=64, E2S=118, E2R=50, GAIN=60, REVSEND=40, REVLP=70,
        **fx(1, DRIVE, 26, 26), **fx(2, DELAY, 0, 18, 30, 40, 40, 0))),
    ('Throat Song', patch(SMP, [(LFO[1], D_PITCH, 80), (LFO[2], D_CUTOFF, 112), (LFO[4], D_VOLUME, 100)], GLIDEMODE=2, GLIDE=20,   # il didgeridoo che canta
        SMPSET=set_idx('didgeridoo'), L1SHAPE=L_SH, L1RATE=60, L1MODE=L_MONO, L2SHAPE=L_TRI, L2RATE=52, L2MODE=L_MONO,
        L4SHAPE=L_SINE, L4RATE=68, L4MODE=L_MONO,                      # il respiro ritmico sta sull'LFO 4, il drive dà voce
        FTYPE=BANDPASS, CUTOFF=58, RESONANCE=60, GVELO=40, E2A=20, E2D=64, E2S=127, E2R=40, GAIN=112, REVSEND=40, REVSIZE=112,
        **fx(1, DRIVE, 64, 110), **fx(2, DELAY, 2, 20, 30, 60, 90, 20))),
    ('Rain Marimba', patch(SMP, [(RND, D_PAN, 120), (RND, D_PITCH, 76), (RND, D_VOLUME, 90)],   # gocce sparse nello stereo
        SMPSET=set_idx('marimba'), GVELO=90, E2A=0, E2D=64, E2S=127, E2R=40, GAIN=78, REVSEND=50, REVSIZE=114,
        **fx(2, DELAY, 2, 40, 70, 90, 127, 30))),
    ('Robot Garden', patch(VA, [(LFO[1], D_PITCH, 96), (LFO[2], D_PW(1), 100), (LFO[1], D_CUTOFF, 100)],   # S&H sul pitch: parla
        O1SHAPE=PULSE, O1PW=64, O2SHAPE=PULSE, O2PW=64, O2SEMI=76, O2GAIN=30, L1SHAPE=L_SH, L1RATE=70, L1MODE=L_MONO,
        L2SHAPE=L_SH, L2RATE=84, L2MODE=L_FREE, CUTOFF=70, RESONANCE=36, E2A=0, E2D=64, E2S=115, E2R=20,
        GAIN=60, REVSEND=24, **fx(1, FLANGER, 40, 60, 70, 80), **fx(2, DELAY, 2, 26, 36, 60, 90, 20))),
    ('Wisp Choir', patch(FM, [(RND, D_PITCH, 78), (RND, D_PAN, 120), (LFO[1], D_PAN, 110), (LFO[2], D_PITCH, 70)], FMALG=4,   # fuoco fatuo
        O1PW=127, O1GAIN=0, O2SEMI=64, O2PW=50, O2GAIN=0, O3SEMI=76, O3PW=90, O3GAIN=0, O4SEMI=71, O4PW=30, O4GAIN=0, HIGHPASS=70,
        L1SHAPE=L_SINE, L1RATE=50, L1MODE=L_RESET, L2SHAPE=L_SINE, L2RATE=74, L2MODE=L_RESET, CUTOFF=92,
        E2A=96, E2D=64, E2S=127, E2R=104, GAIN=58, REVSEND=100, REVSIZE=127, REVLP=100,
        **fx(1, ENSEMBLE, 30, 80, 50, 40), **fx(2, DELAY, 0, 40, 70, 30, 127, 60))),
    ('Venus Flytrap', patch(VA, [(ENV[3], D_PITCH, 20), (VEL, D_ENV1T, 10), (VEL, D_Q, 110)],   # scatta e si chiude
        O1SHAPE=SAW, O2SHAPE=SAW, O2SEMI=52, O2DETUNE=68, O2GAIN=60, O3SHAPE=PULSE, O3PW=30, O3GAIN=30,
        CUTOFF=30, RESONANCE=70, FENV=90, FVELO=50, FKT=30, E1A=0, E1D=18, E1S=0, E1R=14, E3A=0, E3D=12, E3S=0, E3R=8,
        E2A=0, E2D=56, E2S=0, E2R=36, GAIN=62, REVSEND=36, REVSIZE=104, **fx(1, DRIVE, 40, 40), **fx(2, DELAY, 1, 22, 30, 60, 80, 20))),
    ('Tape Stop', patch(VA, [(LFO[1], D_PITCH, 109), (LFO[1], D_CUTOFF, 110), (LFO[1], D_VOLUME, 96)],   # ogni accordo rallenta e si ferma
        O1SHAPE=SAW, O1SEMI=58, O2SHAPE=SAW, O2SEMI=58, O2DETUNE=68, O2GAIN=50, O3SHAPE=PULSE, O3SEMI=70, O3PW=40, O3GAIN=20,
        L1SHAPE=L_SAWN, L1RATE=30, L1MODE=L_ONESHOT, CUTOFF=70, RESONANCE=14, E2A=2, E2D=64, E2S=127, E2R=40,
        GAIN=60, REVSEND=50, REVSIZE=112, **fx(1, CHORUS, 20, 36, 100))),
    ('Talking Reed', patch(VA, [(LFO[1], D_CUTOFF, 100), (LFO[2], D_Q, 90)],   # il passa-banda fa le vocali
        O1SHAPE=SAW, O2SHAPE=PULSE, O2PW=30, O2DETUNE=70, O2GAIN=50, FTYPE=BANDPASS, CUTOFF=66, RESONANCE=72, FKT=20,
        L1SHAPE=L_TRI, L1RATE=34, L1MODE=L_MONO, L2SHAPE=L_SINE, L2RATE=20, L2MODE=L_FREE,
        E2A=10, E2D=64, E2S=120, E2R=40, GAIN=64, REVSEND=40, REVSIZE=106, **fx(1, DRIVE, 30, 30), **fx(2, DELAY, 1, 20, 30, 60, 80, 20))),
    ('Megaphone Moss', patch(SMP, [], SMPSET=set_idx('harmonica_chrom'), HIGHPASS=80, FTYPE=BANDPASS, CUTOFF=86, RESONANCE=40,
        GVELO=60, E2A=4, E2D=64, E2S=127, E2R=20, GAIN=76, REVSEND=16, **fx(1, DRIVE, 90, 40), **fx(2, DELAY, 2, 14, 20, 40, 20, 60))),
    ('Corpse Flower', patch(FM, [(LFO[1], D_GAIN(2), 96), (LFO[2], D_PAN, 110), (LFO[3], D_PITCH, 70), (RND, D_PITCH, 74)], FMALG=0,   # enorme, lento, raro
        O1PW=127, O1GAIN=0, O2SEMI=52, O2PW=70, O2GAIN=0, O3SEMI=45, O3PW=50, O3GAIN=0, O4SEMI=40, O4PW=48, O4GAIN=0, O4FB=118,
        L1SHAPE=L_SINE, L1RATE=12, L1MODE=L_FREE, L2SHAPE=L_SINE, L2RATE=8, L2MODE=L_FREE, L3SHAPE=L_RAND, L3RATE=16, L3MODE=L_FREE,
        CUTOFF=44, RESONANCE=40, E2A=127, E2D=64, E2S=127, E2R=120, GAIN=56, REVSEND=100, REVSIZE=127, REVLP=36,
        **fx(1, DRIVE, 36, 24), **fx(2, DELAY, 0, 40, 90, 36, 100, 0))),
]

# famiglia di ogni suono, per la lista e il dettaglio della cella (UI-152)
FAMIGLIA = {
    'Hothouse Piano': 'pad', 'Seedling Box': 'bell', 'Harmonium Moss': 'reed', 'Steel Petal': 'mallet',
    'Clav Vine': 'keys', 'Ebow Fern': 'pad', 'Sitar Tranh': 'harp', 'Harp Rain': 'harp', 'Solina Sedge': 'strings',
    'Pizzicato Moss': 'pluck', 'Toy Thicket': 'keys', 'Nylon Bramble': 'pluck',
    'Tanpura Root': 'drone', 'Drunk Glasses': 'pad', 'Octave Hopper': 'lead', 'Siren Thorn': 'lead',
    'Geiger Garden': 'lo-fi', 'Wind Chords': 'pad', 'Rewind Fern': 'pad', 'Mimosa': 'pad', 'Bloom Cycle': 'pad',
    'Upside Down': 'pad', 'Zap Nettle': 'stab', 'Slide Whistle': 'lead', 'Firefly Pad': 'pad',
    'Everlasting Moss': 'stab', 'Rust Chords': 'bell', 'Warped Vinyl': 'lo-fi', 'Throat Song': 'drone',
    'Rain Marimba': 'mallet', 'Robot Garden': 'lead', 'Wisp Choir': 'voice', 'Venus Flytrap': 'stab',
    'Tape Stop': 'lo-fi', 'Talking Reed': 'voice', 'Megaphone Moss': 'reed', 'Corpse Flower': 'drone',
    'Hemlock Acid': 'acid', 'Aconite Square': 'acid', 'Mandragora Acid': 'acid', 'Yew Shadow': 'pad',
    'Black Hellebore': 'drone', 'Deadnettle Dub': 'stab', 'Peat Choir': 'voice', 'Spleenwort Organ': 'organ',
    'Bitterroot Lead': 'lead', 'Witchgrass Pulse': 'pluck', 'Mire Bells': 'bell', 'Undertow': 'pad',
    'Tar Pit Keys': 'keys', 'Nightjar Brass': 'brass', 'Gravel Stab': 'stab', 'Ink Cap Drone': 'drone',
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
    # 18/10/2026: più acidi e più profondi (due 303, una sub che scende fino in fondo, reese ringhioso, 808, FM)
    ('Hemlock 303', patch(VA, [], GLIDEMODE=3, GLIDE=14, O1SHAPE=SAW, CUTOFF=22, RESONANCE=116, FENV=84, FVELO=56,
        E1A=0, E1D=28, E1S=0, E1R=16, E2A=0, E2D=64, E2S=104, E2R=14, GAIN=62, **fx(1, DRIVE, 54, 50))),
    ('Square Acid', patch(VA, [], GLIDEMODE=3, GLIDE=12, O1SHAPE=PULSE, O1PW=64, CUTOFF=26, RESONANCE=110, FENV=76,
        FVELO=52, E1A=0, E1D=34, E1S=0, E1R=18, E2A=0, E2D=64, E2S=104, E2R=16, GAIN=62, **fx(1, DRIVE, 48, 44))),
    ('Abyss Sub', patch(VA, [], GLIDEMODE=2, O1SHAPE=TRI, O2SHAPE=TRI, O2SEMI=52, O2GAIN=40, CUTOFF=30,
        E2A=2, E2D=64, E2S=127, E2R=30, GAIN=78)),
    ('Growl Reese', patch(VA, [(LFO[1], D_OSC(2), 68), (LFO[2], D_CUTOFF, 74)], GLIDEMODE=2, O1SHAPE=SAW,
        O2SHAPE=SAW, O2DETUNE=76, O2GAIN=64, O3SHAPE=SAW, O3SEMI=52, O3DETUNE=56, O3GAIN=44, CUTOFF=34, RESONANCE=26,
        L1SHAPE=0, L1RATE=8, L1MODE=1, L2SHAPE=0, L2RATE=12, L2MODE=1, E2A=0, E2D=64, E2S=120, E2R=22,
        GAIN=62, **fx(1, DRIVE, 50, 30))),
    ('Detroit Sub', patch(VA, [(ENV[3], D_PITCH, 84)], GLIDEMODE=2, O1SHAPE=TRI, CUTOFF=52,
        E3A=0, E3D=20, E3S=0, E3R=12, E2A=0, E2D=90, E2S=50, E2R=44, GAIN=76, **fx(1, DRIVE, 40, 22))),
    ('Coal FM Bass', patch(FM, [(ENV[3], D_GAIN(2), 108)], GLIDEMODE=2, FMALG=1, O1PW=127, O1GAIN=0,
        O2SEMI=52, O2PW=60, O2GAIN=44, O3PW=0, O4PW=0, E2A=0, E2D=48, E2S=40, E2R=16,
        E3A=0, E3D=24, E3S=0, E3R=14, CUTOFF=50, GAIN=72, **fx(1, DRIVE, 30, 26))),
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
    # quarta ondata, misurata il 18/10/2026
    'Hemlock Acid': -2.1, 'Aconite Square': -1.9, 'Mandragora Acid': -2.8, 'Yew Shadow': -0.7,
    'Black Hellebore': -6.1, 'Deadnettle Dub': 0.4, 'Peat Choir': 1.3, 'Spleenwort Organ': -6.5,
    'Bitterroot Lead': -1.4, 'Witchgrass Pulse': 5.1, 'Mire Bells': -3.2, 'Undertow': -0.4, 'Tar Pit Keys': -6.7,
    'Nightjar Brass': -3.5, 'Gravel Stab': -4.3, 'Ink Cap Drone': -4.2,
    'Hemlock 303': -0.6, 'Square Acid': -1.9, 'Abyss Sub': 4.4, 'Growl Reese': 0.0, 'Detroit Sub': 2.8,
    'Coal FM Bass': 3.6,
    # quinta ondata, misurata il 18/10/2026 sera (Tanpura, Wind Chords e Tape Stop arrivavano a 0 dBFS: ora no)
    'Hothouse Piano': 11.2, 'Seedling Box': 7.0, 'Harmonium Moss': 5.4, 'Steel Petal': -0.3, 'Clav Vine': 4.1,
    'Ebow Fern': -1.2, 'Sitar Tranh': 8.9, 'Harp Rain': 4.2, 'Solina Sedge': 1.6, 'Pizzicato Moss': 2.0,
    'Toy Thicket': -3.4, 'Nylon Bramble': 1.7,
    'Tanpura Root': -13.6, 'Drunk Glasses': -0.5, 'Octave Hopper': -2.6, 'Siren Thorn': 2.4, 'Geiger Garden': -0.1,
    'Wind Chords': -7.0, 'Rewind Fern': -2.5, 'Mimosa': -0.7, 'Bloom Cycle': -2.9, 'Upside Down': -0.4,
    'Zap Nettle': -0.3, 'Slide Whistle': 4.3, 'Firefly Pad': -1.7, 'Everlasting Moss': 4.7, 'Rust Chords': 3.2,
    'Warped Vinyl': -5.3, 'Throat Song': -3.4, 'Rain Marimba': -2.7, 'Robot Garden': 0.0, 'Wisp Choir': -2.9,
    'Venus Flytrap': -3.3, 'Tape Stop': -11.2, 'Talking Reed': -1.7, 'Megaphone Moss': -1.1, 'Corpse Flower': -2.4,
}


# Perform di default di ogni suono (ACC-162; colonne perform_mode e perform_amount di bank.idx, SND-131).
# Modi di ACC-160: 0 Off, 1 Strum, 2 Strum 2 Oct, 3 Slop, 4 Arpeggiate, 5 Arp 2 Oct, 6 Pattern, 7 Harp.
# Scelte di Stame per i suoi suoni, non dati dell'originale. I bassi non hanno performance (ACC-142).
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
    'Hemlock Acid': (PATTERN, 4), 'Aconite Square': (ARP, 5), 'Mandragora Acid': (ARP2, 3),
    'Witchgrass Pulse': (ARP2, 5), 'Mire Bells': (STRUM, 2), 'Tar Pit Keys': (STRUM, 1), 'Gravel Stab': (STRUM, 1),
    'Seedling Box': (PATTERN, 10), 'Steel Petal': (STRUM, 1), 'Clav Vine': (PATTERN, 6), 'Sitar Tranh': (STRUM, 3),
    'Harp Rain': (HARP, 5), 'Solina Sedge': (STRUM2, 3), 'Pizzicato Moss': (STRUM, 3), 'Toy Thicket': (PATTERN, 3),
    'Nylon Bramble': (STRUM, 3), 'Zap Nettle': (ARP, 5), 'Rust Chords': (STRUM, 2), 'Rain Marimba': (PATTERN, 13),
    'Robot Garden': (ARP2, 5), 'Venus Flytrap': (STRUM, 1),
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
