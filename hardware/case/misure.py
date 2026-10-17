"""misure.py — tutte le misure del case di Stame, in millimetri (docs/specifica/60-case.md, bozza 3).

Fonti: [M] manuale o scheda, [O] osservato, [D] dedotto da foto o calcolo, [V] da verificare con il
calibro prima di tagliare. Le posizioni dei controlli della MK4 e le misure del macro pad sono [D],
ricavate dalle foto di Luigi del 15/10/2026 (private/foto/, fuori da git) in rapporto alla larghezza
nota della MK4: prima di tagliare la mascherina va stampata la dima 1:1 su carta e provata sulla MK4.

Il 17/10/2026 i controlli della MK4 sono stati rimisurati su mk4_vista_alto.jpg: la scala torna sui
due assi (347,5 mm di larghezza, 192 di profondità, ±1 %), con la correzione della prospettiva
(la fronte è più vicina all'obiettivo); centri dei pulsanti dal colore, delle manopole dal cerchio
degli anelli rossi, di pad e ruote dai bordi. Incertezza stimata ±1 mm. Le porte della Flip vengono
da due foto che concordano entro 0,5 mm. Le misure del pad no: due foto danno passi diversi del 10 %.

Composizione (decisa da Luigi il 15/10/2026): MPK mini IV a sinistra; a destra la «torre»: davanti il
macro pad in linea con i tasti, dietro la Flip aperta su una mensola, con l'hub nel vano sotto.

Sistema di riferimento del case: x verso destra dal bordo esterno del fianco sinistro, y dal retro
verso il musicista, z dal tavolo verso l'alto.
"""
import math

# ---- macchine ----
LASER_BED = (390.0, 390.0)        # AtomStack S10, area utile con margine [D]
PRINT_BED = (240.0, 240.0)        # Kobra S1, 250 con 5 mm di margine per lato (CASE-003)

# ---- materiali ----
PLY = 4.0                         # compensato di betulla per pannelli e fianchi [D]
BASE_T = 6.0                      # compensato della base e del piano della mensola
ACR = 3.0                         # acrilico nero (si taglia con il laser a diodo) o compensato tinto nero
GIOCO = 0.2                       # gioco per incastri e fori di passaggio
FIANCO_STRATI = 4                 # fianchi: 4 strati da PLY incollati = 16 mm

# ---- apparecchi ----
# MPK mini IV: 347,5 × 192 × 45,7 con le manopole (rivenditori), corpo 37 (Akai) [M, guida MK4 §1];
# i tasti cominciano a 98 mm dal bordo posteriore e sono alti circa 30 mm dal tavolo [D, foto]
MK4 = dict(w=347.5, d=192.0, h=37.0, h_knobs=45.7, keybed_y=98.0, key_top=30.0)
# Miyoo Flip chiusa 84 × 80,35 × 24,5 [O schede]; metà con i tasti 12,25 [D]; apertura della
# cerniera [V]: qui serve almeno 115°
FLIP = dict(w=84.0, d=80.35, h=24.5, half=12.25)
# porte sul bordo davanti della metà con i tasti, centro rispetto al centro della Flip [D, due foto]
FLIP_JACK_DX = -6.0
FLIP_USBC_DX = 6.3
# tasti sul fianco destro, vicino alla cerniera: fra 6 e 16 mm dal bordo posteriore [D, foto]
FLIP_TASTI_LATO = (6.0, 16.0)
# macro pad BRIMFORD: 15 tasti in 3 file da 5 e 3 manopole a destra [O]; misure dalle foto [D, V]
PAD = dict(w=158.0, d=70.0, h=32.0, pitch_x=18.2, pitch_y=19.5, k0=(12.0, 11.0))
# manopole del pad: centro (x, y dal bordo posteriore) e raggio [D, foto]; m1 è la piccola vicina ai
# tasti, m2 quella sul bordo, M la grande in basso (specifica 40 §8.10)
PAD_KNOB = {'m1': (117.5, 13.0, 10.0), 'm2': (150.0, 13.0, 10.0), 'M': (135.0, 53.0, 15.0)}
PAD_USB_X = 150.0                 # presa USB-C sul bordo posteriore del pad, verso le manopole [D, V]
HUB = dict(w=85.0, d=32.0, h=15.0)   # hub USB 2.0 [V]

# Controlli della MK4: centro (x dal bordo sinistro, y dal bordo posteriore) [D, foto, rimisurati il
# 17/10/2026]; tipo: k manopola, p pad, b pulsante, w ruota, d display, e encoder di navigazione
MK4_CTRL = {
    'PITCH': (22.9, 37.1, 'w'), 'MOD': (53.7, 37.1, 'w'),
    'OCT-': (24.4, 75.5, 'b'), 'OCT+': (50.3, 75.5, 'b'),
    'PAD5': (87.9, 18.0, 'p'), 'PAD6': (116.6, 18.0, 'p'), 'PAD7': (145.2, 18.0, 'p'), 'PAD8': (173.3, 18.0, 'p'),
    'PAD1': (87.9, 46.3, 'p'), 'PAD2': (116.6, 46.3, 'p'), 'PAD3': (145.2, 46.3, 'p'), 'PAD4': (173.3, 46.3, 'p'),
    'ARP': (88.5, 75.2, 'b'), 'LATCH': (109.6, 75.1, 'b'), 'NREP': (130.4, 75.1, 'b'),
    'TAP': (151.1, 75.0, 'b'), 'BANK': (171.9, 75.4, 'b'),
    'DISP': (214.1, 16.0, 'd'), 'NAV': (214.5, 34.9, 'e'),
    'MINUS': (203.8, 60.0, 'b'), 'PLUS': (224.4, 60.0, 'b'),
    'SHIFT': (203.5, 75.1, 'b'), 'DAW': (224.3, 75.1, 'b'),
    'K1': (252.4, 18.3, 'k'), 'K2': (280.4, 18.3, 'k'), 'K3': (307.9, 18.3, 'k'), 'K4': (335.6, 18.3, 'k'),
    'K5': (252.2, 50.0, 'k'), 'K6': (280.6, 50.0, 'k'), 'K7': (308.2, 50.0, 'k'), 'K8': (336.0, 50.0, 'k'),
    'UNDO': (252.9, 74.4, 'b'), 'LOOP': (273.8, 74.4, 'b'), 'PLAY': (294.1, 74.4, 'b'),
    'REC': (314.2, 74.4, 'b'), 'DUB': (334.2, 74.4, 'b'),
}
MK4_KEYBED_Y = MK4['keybed_y']
MK4_CONN_X = (255.0, 335.0)       # USB-C (a x 278 nella foto), MIDI OUT e SUSTAIN sul retro [D, V]

# Fori della mascherina per tipo di controllo (larghezza, altezza, raggio degli angoli). I tasti
# stanno sotto la mascherina (sollevata dai piedini): i fori non devono girare attorno ai cappucci,
# solo lasciarli raggiungere dal dito.
FORO = {
    'k': (21.0, 21.0, 10.5),      # manopole: cappuccio da 11 mm, anello rosso del pannello da 15-17 [D]
    'e': (21.0, 21.0, 10.5),      # encoder: anello da 20 mm [D]
    'p': (25.5, 25.5, 3.0),       # pad: 22,5 mm, 25 con la cornice; passo 28,5, restano 3 mm fra i fori [D]
    'w': (14.0, 46.0, 4.0),       # ruote: cornice del pannello 13,8 × 45,5 [D]
    'd': (25.0, 12.5, 1.5),       # display: vetro 22,6 × 11,7 [D]; 2 mm dal foro dell'encoder
    'b': (17.8, 12.0, 2.0),       # pulsanti 17,7 × 11,5, passo 20-21: restano 2,2-3 mm fra i fori [D]
}
# Controlli che restano scoperti; gli altri (OCT, ARP, LATCH, NOTE REPEAT, TAP, BANK, PLUGIN/DAW)
# stanno sotto la mascherina, sollevata dai piedini. PLUGIN/DAW serve una volta per scegliere il
# preset DAW: si solleva la mascherina.
SCOPERTI = {'PITCH', 'MOD', 'PAD1', 'PAD2', 'PAD3', 'PAD4', 'PAD5', 'PAD6', 'PAD7', 'PAD8',
            'DISP', 'NAV', 'MINUS', 'PLUS', 'SHIFT', 'K1', 'K2', 'K3', 'K4', 'K5', 'K6', 'K7', 'K8',
            'UNDO', 'LOOP', 'PLAY', 'REC', 'DUB'}

MASCHERINA = dict(
    y0=1.0, y1=94.0,              # copre il pannello comandi fino ai tasti (bordo della MK4 [V])
    x0=3.0, x1=349.0,             # un pezzo solo (346 mm stanno nel laser); a destra sporge di 1,5 mm
                                  # sulla fessura verso il divisorio, così attorno a K4 e K8 restano 3 mm
    piede_h=4.0,                  # piedini: la mascherina sta 4 mm sopra i pulsanti [V]
    piede_d=6.0,
)
# piedini incollati SOTTO la mascherina (x, y nel riferimento della MK4), dove la MK4 è piana e
# lontano da fori e controlli [V: controllare con la dima]
PIEDINI = [(9.0, 9.0), (9.0, 88.0), (68.0, 9.0), (68.0, 88.0), (130.0, 88.0),
           (194.0, 9.0), (194.0, 88.0), (236.0, 9.0), (236.0, 88.0), (339.0, 34.0), (339.0, 88.0)]

# ---- disposizione del case (bozza 3) ----
FIANCO = FIANCO_STRATI * PLY      # 16
RETRO_Y = 40.0                    # zona dei cavi dietro gli apparecchi (y 0..40), chiusa dal listello
MK4_X0 = FIANCO + 2.0             # 2 mm di gioco ai lati della MK4
MK4_Y0 = RETRO_Y + PLY            # 44: dietro c'è il listello del retro
BASE_Y1 = MK4_Y0 + MK4['d'] + 8.0 # 244: 8 mm davanti ai tasti
DIV_X = MK4_X0 + MK4['w'] + 2.0   # 367,5: divisorio fra MK4 e torre
TORRE_X0 = DIV_X + PLY + 2.0      # 373,5
TORRE_W = PAD['w'] + 20.0         # 178: 10 mm per lato attorno al pad
TORRE_X1 = TORRE_X0 + TORRE_W     # 551,5
LARGHEZZA = TORRE_X1 + 2.0 + FIANCO   # 569,5
MENSOLA_Y = (MK4_Y0, MK4_Y0 + 100.0)  # 44..144: vano della mensola fra la parete dietro e quella davanti
MENSOLA_Z = 46.0                  # cima del piano della mensola: sotto c'è il vano dell'hub
TORRE_FRONTE_Y = MENSOLA_Y[1]     # parete davanti della mensola (4 mm), con il cartellino sul davanti
# Bozza 4 (17/10/2026): le pareti della torre stanno SOTTO il piano (z da BASE_T a MENSOLA_Z - BASE_T)
# e si incastrano a linguetta nella base e nel piano; il piano sporge di 3 mm oltre le pareti, così
# le asole restano chiuse. Il listello del retro e il divisorio si incastrano nella base allo stesso modo.
PIANO_Y = (MENSOLA_Y[0] - 3.0, TORRE_FRONTE_Y + PLY + 3.0)   # 41..151
PIANO_Z0 = MENSOLA_Z - BASE_T     # 40: sotto il piano il vano è alto 34 mm
LINGUETTA = 14.0                  # larghezza delle linguette; le asole hanno GIOCO in più per lato
PAD_X0 = TORRE_X0 + 10.0
PAD_Y0 = TORRE_FRONTE_Y + PLY + (BASE_Y1 - 8.0 - TORRE_FRONTE_Y - PLY - PAD['d']) / 2   # 157: centrato
FLIP_X = TORRE_X0 + TORRE_W / 2   # 462,5: centro della Flip
# Culla (bozza 4): un vassoio basso appoggiato sul piano e fissato con 4 viti M3. Il 17/10/2026 i tasti
# della Flip sono diventati sempre vivi, spalle comprese (L1 R1 fuoco, L2 Tap, R2 Fill): la culla non
# deve coprirle, quindi è aperta dietro e i bordi sono alti solo CULLA_BORDO.
CULLA_FONDO = 2.0
CULLA_BORDO = 5.0
CULLA_PARETE = 2.0
FLIP_Y0 = MENSOLA_Y[0] + PLY + 6.6                # bordo posteriore della metà con i tasti (cerniera): 54,6
FLIP_Z0 = MENSOLA_Z + CULLA_FONDO                 # la metà con i tasti appoggia sul fondo della culla: 48
SCHERMO_DEG = 65.0                # schermo a 65° dall'orizzontale: apertura della cerniera 115° [V]
GIUNTA = 310.0                    # giunta delle due metà di base e retro
FIANCO_Z = dict(front=40.0, back=54.0, y_front=180.0, y_back=140.0)   # profilo dei fianchi

# cartellino del macro pad: acrilico sulla parete davanti della mensola
CARTELLINO = dict(w=TORRE_W - 4.0, h=PIANO_Z0 - BASE_T - 1.0)   # 33: sotto il bordo del piano
# hub USB nel suo fermo, sotto la culla
HUB_X0 = FLIP_X - (HUB['w'] + 0.8) / 2
HUB_Y0 = MENSOLA_Y[0] + PLY + 30.0
# copritasti del macro pad (CASE-043): stelo a croce tipo MX [V: verificare sul pad, che ha tasti
# meccanici]; il cappuccio è più piccolo del passo di 1,6 mm
COPRITASTO = dict(w=PAD['pitch_x'] - 1.6, d=PAD['pitch_y'] - 2.9, h=7.5, top=1.6, stelo_d=5.5, croce=(4.1, 1.35), stelo_h=4.0)
