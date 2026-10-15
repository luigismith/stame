"""misure.py — tutte le misure del case di Stame, in millimetri (docs/specifica/60-case.md).

Fonti: [M] manuale o scheda, [D] dedotto da foto o calcolo, [V] da verificare con il calibro prima
di tagliare. Quasi tutte le posizioni dei controlli della MPK sono [D] (guida alla Plus §14.15.2):
prima di tagliare la mascherina va stampata la dima 1:1 su carta e provata sulla MPK.

Sistema di riferimento del case: x verso destra dal bordo esterno del fianco sinistro, y dal retro
verso il musicista, z dal tavolo verso l'alto.
"""
import math

# ---- macchine ----
LASER_BED = (390.0, 390.0)        # AtomStack S10, area utile con margine [D]
PRINT_BED = (240.0, 240.0)        # Kobra S1, 250 con 5 mm di margine per lato (CASE-003)

# ---- materiali ----
PLY = 4.0                         # compensato di betulla per pannelli e fianchi [D]
BASE_T = 6.0                      # compensato della base
ACR = 3.0                         # acrilico nero (si taglia con il laser a diodo) o compensato tinto nero
GIOCO = 0.2                       # gioco per incastri e fori di passaggio
FIANCO_STRATI = 4                 # fianchi: 4 strati da PLY incollati = 16 mm

# ---- apparecchi ----
MPK = dict(w=451.1, d=180.0, h_back=37.5, h_front=28.5, h_knobs=52.0)   # [M] 451,1×180×52; profilo [D]
FLIP = dict(w=84.0, d=80.35, h=24.5, half=12.25)                           # chiusa [O]; metà [D]
PAD = dict(w=115.0, d=100.0, h=35.0)                                       # macro pad BRIMFORD [V]
HUB = dict(w=85.0, d=32.0, h=15.0)                                         # hub USB 2.0 [V]

# Controlli della MPK: centro (x dal bordo sinistro, y dal bordo posteriore) [D, guida §14.15.2]
# tipo: k manopola, p pad, b pulsante, w ruota, j joystick, d display, e encoder di menu
MPK_CTRL = {
    'PITCH': (27.0, 52.0, 'w'), 'MOD': (57.0, 52.0, 'w'), 'JOY': (88.0, 19.0, 'j'),
    'ARP': (81.0, 43.0, 'b'), 'TAP': (98.0, 43.0, 'b'), 'NREP': (81.0, 56.0, 'b'), 'FULL': (98.0, 56.0, 'b'),
    'OCT-': (81.0, 69.0, 'b'), 'OCT+': (98.0, 69.0, 'b'),
    'PAD5': (132.0, 26.0, 'p'), 'PAD6': (167.0, 26.0, 'p'), 'PAD7': (201.0, 26.0, 'p'), 'PAD8': (236.0, 26.0, 'p'),
    'PAD1': (132.0, 61.0, 'p'), 'PAD2': (167.0, 61.0, 'p'), 'PAD3': (201.0, 61.0, 'p'), 'PAD4': (236.0, 61.0, 'p'),
    'DISP': (277.0, 19.0, 'd'), 'ENC': (310.0, 19.0, 'e'),
    'K1': (340.0, 19.0, 'k'), 'K2': (371.0, 19.0, 'k'), 'K3': (400.0, 19.0, 'k'), 'K4': (430.0, 19.0, 'k'),
    'K5': (340.0, 47.0, 'k'), 'K6': (371.0, 47.0, 'k'), 'K7': (400.0, 47.0, 'k'), 'K8': (430.0, 47.0, 'k'),
    'BANK': (271.0, 49.0, 'b'), 'SCALES': (289.0, 49.0, 'b'), 'CHORDS': (307.0, 49.0, 'b'),
    'SHIFT': (271.0, 70.5, 'b'), 'HOME': (289.0, 70.5, 'b'), 'PROG': (307.0, 70.5, 'b'),
    'REW': (341.0, 70.0, 'b'), 'FWD': (359.0, 70.0, 'b'), 'STOP': (376.0, 70.0, 'b'),
    'PLAY': (394.0, 70.0, 'b'), 'REC': (412.0, 70.0, 'b'), 'SEQ': (430.0, 70.0, 'b'),
}
MPK_KEYBED_Y = 93.0               # inizio dei tasti [D]

# Fori della mascherina per tipo di controllo (larghezza, altezza, raggio degli angoli) [V]
FORO = {
    'k': (21.0, 21.0, 10.5),      # manopole da 19 mm [D]: 1 mm di gioco, così resta posto per le scritte
    'e': (21.0, 21.0, 10.5),
    'p': (32.0, 32.0, 3.0),       # pad [V]
    'w': (18.0, 54.0, 4.0),       # ruote [V]
    'j': (17.0, 17.0, 8.5),       # joystick [V]
    'd': (30.0, 13.0, 1.5),       # display della MPK [V]
    'b': (12.0, 8.0, 2.0),        # pulsanti piccoli [V]
}
# Controlli che restano scoperti; gli altri pulsanti stanno sotto la mascherina, sollevata dai piedini
SCOPERTI = {'PITCH', 'MOD', 'JOY', 'PAD1', 'PAD2', 'PAD3', 'PAD4', 'PAD5', 'PAD6', 'PAD7', 'PAD8',
            'DISP', 'ENC', 'K1', 'K2', 'K3', 'K4', 'K5', 'K6', 'K7', 'K8', 'BANK', 'PROG', 'SHIFT',
            'REW', 'FWD', 'STOP', 'PLAY', 'REC'}

MASCHERINA = dict(
    y0=3.0, y1=89.0,              # copre il pannello comandi fino ai tasti (bordo della MPK [V])
    x0=3.0, x1=448.1,
    taglio=253.0,                 # giunta fra le due metà: fra i pad e BANK
    piede_h=4.0,                  # piedini: la mascherina sta 4 mm sopra i pulsanti piccoli [V]
    piede_d=6.0,
)
# piedini incollati SOTTO la mascherina (x, y nel riferimento della MPK), dove la MPK è piana e
# lontano da fori e controlli [V: controllare con la dima]
PIEDINI = [(8.0, 8.0), (8.0, 84.0), (105.0, 8.0), (105.0, 84.0), (184.0, 6.0), (249.0, 6.0),
           (184.0, 86.0), (249.0, 86.0),
           (258.0, 8.0), (258.0, 86.0), (325.0, 6.0), (325.0, 86.0), (446.0, 6.0), (446.0, 86.0)]

# ---- disposizione del case ----
FIANCO = FIANCO_STRATI * PLY      # 16 mm
MPK_X0 = FIANCO + 2.0             # 2 mm di gioco ai lati della MPK
MPK_Y0 = 100.0                    # la MPK comincia dietro il ponte
BASE_Y1 = MPK_Y0 + MPK['d'] + 8.0 # 288: 8 mm davanti ai tasti
PAD_X0 = MPK_X0 + MPK['w'] + 4.0  # vano del macro pad
POD_W = 128.0
LARGHEZZA = PAD_X0 + POD_W + 2.0 + FIANCO
PONTE_Y = (0.0, 98.0)             # il ponte sta dietro la MPK
PONTE_Z_FRONT = BASE_T + MPK['h_back'] + MASCHERINA['piede_h'] + ACR + 1.5   # appena sopra la mascherina
INCLINAZIONE = 15.0               # piano della Flip (CASE-010)
PONTE_Z_BACK = PONTE_Z_FRONT + (PONTE_Y[1] - PONTE_Y[0]) * math.tan(math.radians(INCLINAZIONE))
FLIP_X = 205.0                    # centro della Flip: dietro i pad, lontana dai connettori della MPK
MPK_CONN_X = (272.0, 420.0)       # connettori sul retro della MPK [D]

# rinforzi interni del ponte (posizioni x delle centine)
CENTINE_X = [160.0, 310.0, 460.0]
