"""misure.py — tutte le misure del case di Stame, in millimetri (docs/specifica/60-case.md, bozza 5).

Fonti: [M] manuale o scheda, [O] osservato, [D] dedotto da foto o calcolo, [V] da verificare con il
calibro prima di tagliare. Le posizioni dei controlli della MK4 e le misure del macro pad sono [D],
ricavate dalle foto di Luigi del 15/10/2026 (private/foto/, fuori da git) in rapporto alla larghezza
nota della MK4: prima di tagliare la mascherina va stampata la dima 1:1 su carta e provata sulla MK4.

Il 17/10/2026 i controlli della MK4 sono stati rimisurati su mk4_vista_alto.jpg: la scala torna sui
due assi (347,5 mm di larghezza, 192 di profondità, ±1 %), con la correzione della prospettiva
(la fronte è più vicina all'obiettivo); centri dei pulsanti dal colore, delle manopole dal cerchio
degli anelli rossi, di pad e ruote dai bordi. Incertezza stimata ±1 mm. Le porte della Flip vengono
da due foto che concordano entro 0,5 mm. Il pad è stato misurato il 17/10/2026 con i tasti 1u come
metro (±2 %); la sua altezza è [V].

Composizione (decisa da Luigi il 15/10/2026): MPK mini IV a sinistra; a destra il macro pad in linea
con i tasti e, dietro, la Flip aperta. Bozza 5 (18/10/2026): un telaio solo con la cima alla stessa
quota, la mascherina che appoggia sulla MK4, il pad in una culla come quella della Flip, hub e cavi
sotto il piano.

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
# macro pad BRIMFORD: 15 tasti in 3 file da 5 e 3 manopole a destra [O]. Misure dalla foto
# pad_brimford_luigi.jpg (17/10/2026), con i copritasti 1u come metro (base 18 mm): 7,39 px/mm, e il
# pulsante AUTOMATION della MK4 nella stessa foto (17,7 mm) dà 7,40 [D, ±2 %]. L'altezza è [V].
PAD = dict(w=178.0, d=72.0, h=32.0, pitch_x=21.0, pitch_y=22.3, k0=(17.2, 13.3))
# manopole del pad: centro (x, y dal bordo posteriore) e raggio [D, foto]; m1 è la piccola vicina ai
# tasti, m2 quella sul bordo, M la grande in basso (specifica 40 §8.10)
PAD_KNOB = {'m1': (131.4, 16.0, 9.5), 'm2': (164.3, 16.4, 9.5), 'M': (150.0, 59.7, 15.0)}   # M sporge 2 mm davanti
PAD_USB_X = 148.0                 # presa USB-C sul bordo posteriore del pad, verso le manopole [D]
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

# Fori della mascherina per tipo di controllo (larghezza, altezza, raggio degli angoli). La
# mascherina appoggia sul pannello della MK4: i fori girano attorno a cappucci e cornici, e i pulsanti
# restano 1-2 mm sotto la sua faccia [V: altezza dei pulsanti].
FORO = {
    'k': (21.0, 21.0, 10.5),      # manopole: cappuccio da 11 mm, anello rosso del pannello da 15-17 [D]
    'e': (21.0, 21.0, 10.5),      # encoder: anello da 20 mm [D]
    'p': (25.5, 25.5, 3.0),       # pad: 22,5 mm, 25 con la cornice; passo 28,5, restano 3 mm fra i fori [D]
    'w': (14.0, 46.0, 4.0),       # ruote: cornice del pannello 13,8 × 45,5 [D]
    'd': (25.0, 12.5, 1.5),       # display: vetro 22,6 × 11,7 [D]; 2 mm dal foro dell'encoder
    'b': (17.8, 12.0, 2.0),       # pulsanti 17,7 × 11,5, passo 20-21: restano 2,2-3 mm fra i fori [D]
}
# I fori della mascherina sono per tutti i controlli della MK4 (Luigi, 18/10/2026: «falla che si
# poggia bene con i fori anche per i controlli non utilizzati»): la mascherina appoggia sul pannello.
SCOPERTI = set(MK4_CTRL)

# ---- disposizione del case (bozza 5, 18/10/2026) ----
# Luigi: «deve essere tutto coperto e omogeneo. non mi piace tanto la divisione che hai creato tra mpk e
# pad, e per il pad vorrei una culla simile a quella che hai fatto per il flip». Un telaio di betulla
# (fianchi, retro, fronte, costola) con la cima tutta alla stessa quota; dentro, un piano solo di
# acrilico nero: a sinistra la mascherina, che appoggia sulla MK4 e copre anche la zona dei cavi; a
# destra il piano della Flip. Il pad sta in una culla stampata davanti alla Flip, con il bordo come
# quello della culla della Flip. Hub e cavi stanno sotto il piano.
FIANCO = FIANCO_STRATI * PLY      # 16
FELTRO = 1.0                      # strisce di feltro adesivo sugli appoggi del piano
Z_MK4 = BASE_T + MK4['h']         # 43: il pannello della MK4, dove appoggia la mascherina
Z_PIANO0 = Z_MK4                  # 43: faccia di sotto del piano (mascherina e piano della Flip)
Z_PIANO = Z_PIANO0 + ACR          # 46: la cima della console: piano, fianchi, retro, fronte, costola
Z_APPOGGIO = Z_PIANO0 - FELTRO    # 42: gli strati d'appoggio sotto il bordo del piano, con il feltro
RETRO_Y = PLY                     # il retro: uno strato fino alla cima e uno d'appoggio davanti
APPOGGIO_Y = RETRO_Y + PLY        # 8: da qui comincia la zona dei cavi, sotto la mascherina
MK4_X0 = FIANCO + 2.0             # 2 mm di gioco ai lati della MK4
MK4_Y0 = 44.0                     # 36 mm di zona dei cavi dietro la MK4 (USB a 90°)
BASE_Y1 = MK4_Y0 + MK4['d'] + 8.0 # 244: 8 mm davanti ai tasti
MASCHERINA_Y1 = MK4_Y0 + 94.0     # 138: il bordo davanti della mascherina, 4 mm prima dei tasti
COSTOLA_X0 = MK4_X0 + MK4['w'] + 2.0   # 367,5: la costola fra la MK4 e la culla del pad, due strati
COSTOLA_X1 = COSTOLA_X0 + 2 * PLY      # 375,5
GIUNTA_PIANO = COSTOLA_X0 + PLY        # 371,5: mascherina e piano della Flip si incontrano qui
CULLA_PAD_PARETE = 2.7
CULLA_PAD_GIOCO = 0.5
DESTRA_X0 = COSTOLA_X1
DESTRA_X1 = DESTRA_X0 + PAD['w'] + 2 * (CULLA_PAD_PARETE + CULLA_PAD_GIOCO) + 0.6   # 560,5
LARGHEZZA = DESTRA_X1 + FIANCO    # 576,5
FRONTE_Y = BASE_Y1 - PLY          # 240: parete davanti della parte destra
# culla del pad: tutta la larghezza fra costola e fianco, fino alla parete davanti; dietro porta il
# bordo davanti del piano della Flip su un dente (CULLA_DENTE) e lascia passare la spina del pad
CULLA_PAD_Y1 = FRONTE_Y - 0.3
CULLA_PAD_Y0 = CULLA_PAD_Y1 - PAD['d'] - 2 * (CULLA_PAD_PARETE + CULLA_PAD_GIOCO)
CULLA_DENTE = 4.0
PIANO_Y1 = CULLA_PAD_Y0 - 0.3                  # il piano della Flip arriva alla culla del pad
PAD_X0 = DESTRA_X0 + 0.3 + CULLA_PAD_PARETE + CULLA_PAD_GIOCO
PAD_Y1 = CULLA_PAD_Y1 - CULLA_PAD_PARETE - CULLA_PAD_GIOCO
PAD_Y0 = PAD_Y1 - PAD['d']
# altezze del pad [V]: il corpo (dal fondo alla faccia della piastra di acrilico) e i tasti sopra.
# Come la Flip, il pad sta 2 mm sopra il piano, e il bordo della culla sale 5 mm oltre la piastra
PAD_CORPO = 16.0                  # [V]: da misurare prima di stampare la culla
PAD_Z1 = Z_PIANO + 2.0            # 48: la faccia della piastra del pad
PAD_Z0 = PAD_Z1 - PAD_CORPO       # 32: il pad poggia sulle costole della culla
PAD_USB_Z = 7.0                   # [V]: centro della presa USB-C sopra il fondo del pad; con la spina a 90°
                                  # verso il basso, se la spina tocca il piano si apre una tacca nel suo bordo
CULLA_BORDO = 5.0                 # bordi delle due culle sopra il fondo (Flip) o sopra la piastra (pad)
CULLA_FONDO = 2.0
CULLA_PARETE = 2.0
FLIP_X = (DESTRA_X0 + DESTRA_X1) / 2   # 468: centro della Flip e del pad
FLIP_Y0 = MK4_Y0 + 10.6           # 54,6: bordo posteriore della metà con i tasti (cerniera)
FLIP_Z0 = Z_PIANO + CULLA_FONDO   # 48: la metà con i tasti appoggia sul fondo della culla
SCHERMO_DEG = 65.0                # schermo a 65° dall'orizzontale: apertura della cerniera 115° [V]
GIUNTA = 310.0                    # giunta delle due metà di base e retro
LINGUETTA = 14.0                  # larghezza delle linguette; le asole hanno GIOCO in più per lato
FIANCO_R = 8.0                    # raggio degli spigoli in cima ai fianchi
# hub USB nel suo fermo, sotto il piano della Flip, dietro la culla del pad
HUB_X0 = FLIP_X - (HUB['w'] + 0.8) / 2
HUB_Y0 = CULLA_PAD_Y0 - CULLA_DENTE - 14.0 - HUB['d']
# tasti del macro pad (CASE-043, Luigi 17/10/2026): tasti trasparenti a due strati per Cherry MX,
# 17 × 17 alla base; sotto il coperchio un'etichetta di carta da 11 × 9 [M, scheda del venditore];
# il coperchio sta circa 4 mm sopra la piastra, la cima a 15 mm [D]
TASTO_PAD = dict(w=17.0, d=17.0, h=11.0, top_w=12.5, z=4.0)
ETICHETTA = (11.0, 9.0)
