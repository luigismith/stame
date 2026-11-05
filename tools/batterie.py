"""batterie.py — i kit a campioni del banco (specifica 20, SND-537 e SND-544). Lo importa tools/campioni.py.

Ogni kit è un set del banco: per ognuno dei dodici strumenti di ACC-212 una lista di strati di velocity, e per
ogni strato i colpi alternati della stessa forza; ogni colpo è la somma pesata dei microfoni di una
registrazione (il microfono vicino e i panoramici, sommati in mono come in un mix). Fonti, tutte CC0:
  V  VCSL (Versilian Community Sample Library): percussioni d'orchestra e del mondo
  S  Sonic Pi (campioni di freesound): elettronica e tabla
  R  Karoryfer, Big Rusty Drums: una batteria vera, con le spazzole
  U  Karoryfer, Unruly Drums: un'altra batteria vera (senza tom)
  F  Michael Fischer, TR-808 (1994, tidalcycles/sounds-tr808-fischer): la 808 vera, registrata dall'uscita
     a cinque posizioni delle manopole; qui una posizione per strumento
  M  MckAudio/MckSamplePacks: le batterie elettroniche registrate dall'uscita (Roland TR-8 con i suoni di
     808, 909, 707, 606 e 727; Yamaha RX5; Alesis DR-5)
Gli strati si prendono a circa un terzo, due terzi e in cima alla dinamica della registrazione; la velocity
che li separa è in VEL. Il livello di ogni strumento lo pareggia campioni.py (LIVELLO_REL).
"""
V, S, R, U, F, M = 'V', 'S', 'R', 'U', 'F', 'M'
(KICK, RIM, SNARE, CLAP, CHAT, TOMLO, OHAT, TOMHI, MARACAS, CONGA, COWBELL, CYMBAL) = range(12)
VEL = {1: (0,), 2: (0, 88), 3: (0, 64, 104)}

# intensità di ogni strumento rispetto alla cassa (dB, massimo del valore efficace su 50 ms): come in un mix,
# il charleston e i metalli stanno sotto cassa e rullante
LIVELLO_REL = [0.0, -8.0, -1.0, -3.0, -11.0, -2.0, -9.0, -2.0, -13.0, -5.0, -9.0, -10.0]
# durata massima (s) prima della sfumata; il resto lo taglia la coda sotto −66 dB
SECONDI = {KICK: 1.6, CYMBAL: 2.5, OHAT: 1.5, TOMLO: 1.3, TOMHI: 1.1}     # la cassa lunga della 808
SECONDI_DEF = 0.9

BR = 'Samples/'


def multi(fonte, schema, mics, vls, rrs=(1, 2)):
    """strati da una libreria a più microfoni: `schema` con {mic}, {vl}, {rr}; mics = {microfono: peso}"""
    return [(v, [[(fonte, schema.format(mic=m, vl=vl, rr=rr), w) for m, w in mics.items()] for rr in rrs])
            for v, vl in zip(VEL[len(vls)], vls)]


def file(fonte, cartella, *strati):
    """strati da file singoli: ogni strato è un nome o una lista di nomi (i colpi alternati)"""
    out = []
    for v, s in zip(VEL[len(strati)], strati):
        nomi = [s] if isinstance(s, str) else s
        out.append((v, [[(fonte, (cartella + '/' if cartella else '') + n, 1.0)] for n in nomi]))
    return out


# microfoni
K_RUSTY = {'kick': 1.0, 'oh': 0.45}
SN_RUSTY = {'top': 1.0, 'btm': 0.3, 'oh': 0.5}
TOM_RUSTY = {'cl': 1.0, 'oh': 0.5}
MET_RUSTY = {'cl': 0.7, 'oh': 0.8}
K_UNRULY = {'in': 0.8, 'out': 0.6, 'oh': 0.35}
SN_UNRULY = {'top': 1.0, 'btm': 0.3, 'ohl': 0.35, 'ohr': 0.35}
HH_UNRULY = {'cl': 0.8, 'ohl': 0.4, 'ohr': 0.4}
CY_UNRULY = {'cl': 0.5, 'oh': 1.0}

# cartelle di VCSL
VS = 'Idiophones/Struck Idiophones/'
VM = 'Membranophones/Struck Membranophones/'
CLAPS = file(V, VS + 'Claps', ['Clap_rr1.wav', 'Clap_rr2.wav', 'Clap_rr3.wav', 'Clap_rr4.wav'])
SHAKER = file(V, VS + 'Shaker, Small', ['Mid_ShakerHighFaster_Down_rr1.wav', 'Mid_ShakerHighFaster_Down_rr2.wav'])
CONGA_N = file(V, VM + 'Conga', ['Conga_HitN_v2_rr1_Sum.wav', 'Conga_HitN_v2_rr2_Sum.wav'],
               ['Conga_HitN_v3_rr1_Sum.wav', 'Conga_HitN_v3_rr2_Sum.wav'])
COWBELL1 = file(V, VS + 'Cowbells', 'Cowbell1_Hit_v2_rr1_Mid.wav', 'Cowbell1_Hit_v3_rr1_Mid.wav',
                'Cowbell1_Hit_v4_rr1_Mid.wav')


def rusty_toms(art='center', prefisso=''):
    """i tom di Big Rusty: il 18" per il basso, il 14" per l'alto"""
    lo = {'center': (3, 5, 8), 'brush': (2, 4, 5)}[art]
    hi = {'center': (2, 4, 6), 'brush': (2, 4, 5)}[art]
    p = '' if art == 'center' else prefisso
    return (multi(R, BR + 'tom_18/' + art + '/{mic}/t18' + p + '_vl{vl}_rr{rr}.flac', TOM_RUSTY, lo),
            multi(R, BR + 'tom_14/' + art + '/{mic}/t14' + p + '_vl{vl}_rr{rr}.flac', TOM_RUSTY, hi))


TOM18, TOM14 = rusty_toms()
TOM18B, TOM14B = rusty_toms('brush', '_b')


def f8(nome):
    """un suono della 808 di Fischer: `nome` è sigla e manopole, come BD2550 (tono 25, decadimento 50)"""
    return file(F, nome[:2].lower() + '8', nome + '.WAV')


def mk(path):
    """un suono di MckSamplePacks: `path` dopo la cartella della macchina, come TR8/BD/004_909_Bass_Drum_1"""
    return file(M, '', path + '.wav')


# le macchine della TR-8 per sigla: cassa, rullante, charleston e piatti, tom, percussioni
T_BD, T_SD, T_HH, T_TOM, T_PC = 'TR8/BD/', 'TR8/SD/', 'TR8/HATS/', 'TR8/TOMS/', 'TR8/PERC/'
X_BD, X_SD, X_HH, X_TOM, X_PC = 'RX5/BD/', 'RX5/SD/', 'RX5/HATS/', 'RX5/TOMS/', 'RX5/PERC/'
D_BD, D_SD, D_HH, D_TOM, D_PC = 'DR5/BD/', 'DR5/SD/', 'DR5/HATS/', 'DR5/TOMS/', 'DR5/PERC/'

KIT = {
    # Studio (i Beat di sempre): Big Rusty con le bacchette
    'kit_studio': {
        KICK: multi(R, BR + 'kick_24/kick/{mic}/k_vl{vl}_rr{rr}.flac', K_RUSTY, (3, 6, 10), (1, 2, 3)),
        RIM: multi(R, BR + 'snare_14/sidestick/{mic}/sn_ss_vl{vl}_rr{rr}.flac', {'top': 1.0, 'oh': 0.4}, (2, 4)),
        SNARE: multi(R, BR + 'snare_14/center/{mic}/sn_center_vl{vl}_rr{rr}.flac', SN_RUSTY, (3, 6, 10), (1, 2, 3)),
        CLAP: CLAPS,
        CHAT: multi(R, BR + 'hihat_14/tc/{mic}/ht_tc_vl{vl}_rr{rr}.flac', MET_RUSTY, (3, 5, 8), (1, 2, 3)),
        TOMLO: TOM18,
        OHAT: multi(R, BR + 'hihat_14/open/{mic}/ht_open_vl{vl}_rr{rr}.flac', MET_RUSTY, (3, 6)),
        TOMHI: TOM14,
        MARACAS: SHAKER,
        CONGA: CONGA_N,
        COWBELL: COWBELL1,
        CYMBAL: multi(R, BR + 'crash_17/cr/{mic}/cr_vl{vl}_rr{rr}.flac', {'cl': 0.5, 'oh': 1.0}, (3, 5)),
    },
    # Jazz: Unruly, la cassa aperta e il ride al posto del piatto, lo schiocco delle dita come battimani
    'kit_jazz': {
        KICK: multi(U, BR + 'k20/{mic}/rr{rr}/kick_clean_vl{vl}_rr{rr}.flac', K_UNRULY, (2, 4, 6)),
        RIM: multi(U, BR + 's13/{mic}/rr{rr}/s13_sstick_vl{vl}_rr{rr}.flac', SN_UNRULY, (2, 4, 6)),
        SNARE: multi(U, BR + 's13/{mic}/rr{rr}/s13_center_vl{vl}_rr{rr}.flac', SN_UNRULY, (2, 5, 8), (1, 2, 3)),
        CLAP: file(S, '', 'perc_snap2.flac'),
        CHAT: multi(U, BR + 'h14/{mic}/rr{rr}/hh_closed_tip_vl{vl}_rr{rr}.flac', HH_UNRULY, (2, 4, 6), (1, 2, 3)),
        TOMLO: TOM18,
        OHAT: multi(U, BR + 'h14/{mic}/rr{rr}/hh_loose_tip_vl{vl}_rr{rr}.flac', HH_UNRULY, (3, 5)),
        TOMHI: TOM14,
        MARACAS: file(V, VS + 'Cabasa', ['Cabasa1_Hit_rr1_Mid.wav', 'Cabasa1_Hit_rr2_Mid.wav']),
        CONGA: file(V, VM + 'Conga', ['Quinto_HitN_v2_rr1_Sum.wav', 'Quinto_HitN_v2_rr2_Sum.wav'],
                    ['Quinto_HitN_v3_rr1_Sum.wav', 'Quinto_HitN_v3_rr2_Sum.wav']),
        COWBELL: file(V, VS + 'Cowbells', 'Cowbell2_Normal_v2_rr1_Mid.wav', 'Cowbell2_Normal_v3_rr1_Mid.wav'),
        CYMBAL: multi(U, BR + 'r20/{mic}/rr{rr}/ride_bow_vl{vl}_rr{rr}.flac', CY_UNRULY, (3, 6, 8)),
    },
    # Acoustic Room (libreria): Unruly pulita, i tom di Big Rusty
    'kit_room': {
        KICK: multi(U, BR + 'k20/{mic}/rr{rr}/kick_clean_vl{vl}_rr{rr}.flac', K_UNRULY, (3, 5, 8), (1, 2, 3)),
        RIM: multi(U, BR + 's14/{mic}/rr{rr}/s14_sstick_vl{vl}_rr{rr}.flac', SN_UNRULY, (3, 6)),
        SNARE: multi(U, BR + 's14/{mic}/rr{rr}/s14_center_vl{vl}_rr{rr}.flac', SN_UNRULY, (3, 5, 8), (1, 2, 3)),
        CLAP: CLAPS,
        CHAT: multi(U, BR + 'h14/{mic}/rr{rr}/hh_tight_tip_vl{vl}_rr{rr}.flac', HH_UNRULY, (2, 4, 6), (1, 2, 3)),
        TOMLO: TOM18,
        OHAT: multi(U, BR + 'h14/{mic}/rr{rr}/hh_open_tip_vl{vl}_rr{rr}.flac', HH_UNRULY, (3, 5, 7)),
        TOMHI: TOM14,
        MARACAS: file(V, VS + 'Shaker, Large', ['LShaker_Hit_rr1_Mid.wav', 'LShaker_Hit_rr2_Mid.wav']),
        CONGA: CONGA_N,
        COWBELL: file(V, VS + 'Cowbells', 'Cowbell2_Normal_v2_rr1_Mid.wav', 'Cowbell2_Normal_v3_rr1_Mid.wav'),
        CYMBAL: multi(U, BR + 'c16/{mic}/rr{rr}/cr_edge_vl{vl}_rr{rr}.flac', CY_UNRULY, (3, 5)),
    },
    # Stadium Rock (libreria): la cassa sporca, il rullante sul cerchio, il tamburello al posto delle maracas
    'kit_rock': {
        KICK: multi(U, BR + 'k20/{mic}/rr{rr}/kick_dirty_vl{vl}_rr{rr}.flac', K_UNRULY, (3, 6, 8), (1, 2, 3)),
        RIM: multi(U, BR + 's13/{mic}/rr{rr}/s13_sstick_vl{vl}_rr{rr}.flac', SN_UNRULY, (3, 6)),
        SNARE: multi(U, BR + 's13/{mic}/rr{rr}/s13_rimshot_vl{vl}_rr{rr}.flac', SN_UNRULY, (2, 4, 6), (1, 2, 3)),
        CLAP: CLAPS,
        CHAT: multi(U, BR + 'h14/{mic}/rr{rr}/hh_closed_shank_vl{vl}_rr{rr}.flac', HH_UNRULY, (2, 4, 6), (1, 2, 3)),
        TOMLO: multi(R, BR + 'tom_22/center/{mic}/t22_vl{vl}_rr{rr}.flac', TOM_RUSTY, (3, 5, 7)),
        OHAT: multi(U, BR + 'h14/{mic}/rr{rr}/hh_open_shank_vl{vl}_rr{rr}.flac', HH_UNRULY, (2, 4)),
        TOMHI: multi(R, BR + 'tom_15/center/{mic}/t15_vl{vl}_rr{rr}.flac', TOM_RUSTY, (3, 5, 7)),
        MARACAS: file(V, VS + 'Tambourine 1', 'Tamb1_Hit_v1_rr1_Mid.wav', 'Tamb1_Hit_v2_rr1_Mid.wav'),
        CONGA: TOM18,
        COWBELL: COWBELL1,
        CYMBAL: multi(R, BR + 'crash_sizzle_17/cr/{mic}/crs_vl{vl}_rr{rr}.flac', {'cl': 0.5, 'oh': 1.0}, (3, 6)),
    },
    # Brushes (libreria): Big Rusty con le spazzole, il ride spazzolato
    'kit_brushes': {
        KICK: multi(R, BR + 'kick_24/kick/{mic}/k_vl{vl}_rr{rr}.flac', K_RUSTY, (2, 4, 6)),
        RIM: multi(R, BR + 'snare_14/sidestick/{mic}/sn_ss_vl{vl}_rr{rr}.flac', {'top': 1.0, 'oh': 0.4}, (1, 3)),
        SNARE: multi(R, BR + 'snare_14/brush/{mic}/sn_b_vl{vl}_rr{rr}.flac', SN_RUSTY, (3, 6, 8), (1, 2, 3)),
        CLAP: file(V, VS + 'Claps', ['SoloClap_vl2.wav', 'SoloClap_vl3.wav']),
        CHAT: multi(R, BR + 'hihat_14/cl_brush/{mic}/ht_cl_b_vl{vl}_rr{rr}.flac', MET_RUSTY, (2, 4, 5), (1, 2, 3)),
        TOMLO: TOM18B,
        OHAT: multi(R, BR + 'hihat_14/open_brush/{mic}/ht_open_b_vl{vl}_rr{rr}.flac', MET_RUSTY, (2, 4)),
        TOMHI: TOM14B,
        MARACAS: SHAKER,
        CONGA: file(V, VM + 'Frame Drum', ['HDrumS_Hit_v2_rr1_Sum.wav', 'HDrumS_Hit_v2_rr2_Sum.wav']),
        COWBELL: file(V, VS + 'Cowbells', 'Cowbell1_Muted_v2_rr1_Mid.wav', 'Cowbell1_Muted_v3_rr1_Mid.wav'),
        CYMBAL: multi(R, BR + 'ride_22/brush/{mic}/rd_b_vl{vl}_rr{rr}.flac', {'cl': 0.5, 'oh': 1.0}, (2, 4)),
    },
    # Cajon Box (libreria): il cajón di VCSL (basso, schiocco, e un colpo di mezzo), più le mani
    'kit_cajon': {
        KICK: file(V, VS + 'Cajon', ['Cajon_hit1_mp_rr1.wav', 'Cajon_hit1_mp_rr2.wav'],
                   ['Cajon_hit1_f_rr1.wav', 'Cajon_hit1_f_rr2.wav'], ['Cajon_hit1_fff_rr1.wav', 'Cajon_hit1_fff_rr2.wav']),
        RIM: file(V, VS + 'Cajon', ['Cajon_hit2_pp_rr1.wav', 'Cajon_hit2_pp_rr2.wav'], ['Cajon_hit2_mp_rr1.wav', 'Cajon_hit2_mp_rr2.wav']),
        SNARE: file(V, VS + 'Cajon', ['Cajon_hit3_p_rr1.wav', 'Cajon_hit3_p_rr2.wav'],
                    ['Cajon_hit3_mp_rr1.wav', 'Cajon_hit3_mp_rr2.wav'], ['Cajon_hit3_f_rr1.wav', 'Cajon_hit3_f_rr2.wav']),
        CLAP: CLAPS,
        CHAT: SHAKER,
        TOMLO: file(V, VS + 'Cajon', ['Cajon_hit2_f_rr1.wav', 'Cajon_hit2_f_rr2.wav']),
        OHAT: file(V, VS + 'Tambourine 1', ['Tamb1_Shake_rr1_Mid.wav', 'Tamb1_Shake_rr2_Mid.wav']),
        TOMHI: file(V, VM + 'Frame Drum', ['HDrumS_Hit_v3_rr1_Sum.wav', 'HDrumS_Hit_v3_rr2_Sum.wav']),
        MARACAS: file(V, VS + 'Shaker, Large', ['LShaker_Hit_rr1_Mid.wav', 'LShaker_Hit_rr2_Mid.wav']),
        CONGA: CONGA_N,
        COWBELL: file(V, VS + 'Agogo Bells', 'Agogo_High_v1_rr1_Mid.wav', 'Agogo_High_v2_rr1_Mid.wav', 'Agogo_High_v3_rr1_Mid.wav'),
        CYMBAL: multi(R, BR + 'crash_sizzle_17/brush/{mic}/crs_b_vl{vl}_rr{rr}.flac', {'cl': 0.5, 'oh': 1.0}, (2, 4)),
    },
    # Darbuka Sand (libreria): i cinque colpi della darbuka di VCSL, il tamburello come riq
    'kit_darbuka': {
        KICK: file(V, VM + 'Darbuka', ['Darbuka_1_hit_vl1_rr1.wav', 'Darbuka_1_hit_vl1_rr2.wav'],
                   ['Darbuka_1_hit_vl2_rr1.wav', 'Darbuka_1_hit_vl2_rr2.wav']),
        RIM: file(V, VM + 'Darbuka', ['Darbuka_4_hit_vl1_rr1.wav', 'Darbuka_4_hit_vl1_rr2.wav'],
                  ['Darbuka_4_hit_vl2_rr1.wav', 'Darbuka_4_hit_vl2_rr2.wav']),
        SNARE: file(V, VM + 'Darbuka', ['Darbuka_2_hit_vl1_rr1.wav', 'Darbuka_2_hit_vl1_rr2.wav'],
                    ['Darbuka_2_hit_vl2_rr1.wav', 'Darbuka_2_hit_vl2_rr2.wav']),
        CLAP: CLAPS,
        CHAT: file(V, VS + 'Tambourine 2', 'Tamb2_Hit_v1_rr1_Mid.wav', 'Tamb2_Hit_v2_rr2_Mid.wav'),
        TOMLO: file(V, VM + 'Frame Drum', ['HDrumL_Hit_v2_rr1_Sum.wav', 'HDrumL_Hit_v2_rr2_Sum.wav'],
                    ['HDrumL_Hit_v3_rr1_Sum.wav', 'HDrumL_Hit_v3_rr2_Sum.wav']),
        OHAT: file(V, VS + 'Tambourine 2', ['Tamb2_Shake_rr3_Mid.wav', 'Tamb2_Shake_rr4_Mid.wav']),
        TOMHI: file(V, VM + 'Darbuka', ['Darbuka_3_hit_vl1_rr1.wav', 'Darbuka_3_hit_vl1_rr2.wav'],
                    ['Darbuka_3_hit_vl2_rr1.wav', 'Darbuka_3_hit_vl2_rr2.wav']),
        MARACAS: SHAKER,
        CONGA: file(V, VM + 'Darbuka', ['Darbuka_5_hit_vl1_rr1.wav', 'Darbuka_5_hit_vl1_rr2.wav'],
                    ['Darbuka_5_hit_vl2_rr1.wav', 'Darbuka_5_hit_vl2_rr2.wav']),
        COWBELL: file(V, VS + 'Finger Cymbals', 'Fing_Cymb.wav'),
        CYMBAL: file(V, VS + 'Tambourine 2', 'Tamb2_Roll_v1_rr1_Mid.wav', 'Tamb2_Roll_v2_rr1_Mid.wav'),
    },
    # Latin Perc (libreria): tumba, conga e quinto, bongó, clave, güiro, campanaccio e agogô
    'kit_latin': {
        KICK: file(V, VM + 'Conga', ['Tumba_HitN_v2_rr1_Sum.wav', 'Tumba_HitN_v2_rr2_Sum.wav'],
                   ['Tumba_HitN_v3_rr1_Sum.wav', 'Tumba_HitN_v3_rr2_Sum.wav'], ['Tumba_HitN_v4_rr1_Sum.wav', 'Tumba_HitN_v4_rr2_Sum.wav']),
        RIM: file(V, VS + 'Claves', ['Claves1_Hit_v1_rr1_Mid.wav', 'Claves2_Hit_v1_rr1_Mid.wav'],
                  ['Claves1_Hit_v2_rr1_Mid.wav', 'Claves2_Hit_v2_rr1_Mid.wav'], ['Claves1_Hit_v3_rr1_Mid.wav', 'Claves2_Hit_v3_rr1_Mid.wav']),
        SNARE: file(V, VM + 'Conga', ['Quinto_HitFM1_v1_rr1_Sum.wav', 'Quinto_HitFM1_v1_rr2_Sum.wav'],
                    ['Quinto_HitFM1_v2_rr1_Sum.wav', 'Quinto_HitFM1_v2_rr2_Sum.wav']),
        CLAP: file(V, VS + 'Guiro', ['Guiro_Hit_rr1_Mid.wav', 'Guiro_Hit_rr2_Mid.wav']),
        CHAT: SHAKER,
        TOMLO: CONGA_N,
        OHAT: file(V, VS + 'Guiro', 'Guiro_Fast_rr1_Mid.wav'),
        TOMHI: file(V, VM + 'Bongos', ['BongoL_Hit1_v2_rr1_Mid.wav', 'BongoL_Hit1_v2_rr2_Mid.wav'],
                    ['BongoL_Hit1_v3_rr1_Mid.wav', 'BongoL_Hit1_v3_rr2_Mid.wav']),
        MARACAS: file(V, VS + 'Shaker, Small', ['Mid_ShakerDouble_Down_rr1.wav', 'Mid_ShakerDouble_Down_rr2.wav']),
        CONGA: file(V, VM + 'Bongos', ['BongoH_Hit1_v2_rr1_Mid.wav', 'BongoH_Hit1_v2_rr2_Mid.wav'],
                    ['BongoH_Hit1_v3_rr1_Mid.wav', 'BongoH_Hit1_v3_rr2_Mid.wav']),
        COWBELL: file(V, VS + 'Cowbells', 'Cowbell1_Normal_v2_rr1_Mid.wav', 'Cowbell1_Normal_v3_rr1_Mid.wav'),
        CYMBAL: file(V, VS + 'Agogo Bells', 'Agogo_Low_v1_rr1_Mid.wav', 'Agogo_Low_v2_rr1_Mid.wav'),
    },
    # Afro Hand (libreria): tamburo a cornice, tamburo a fessura, conghe, campane e sonagli
    'kit_afro': {
        KICK: file(V, VM + 'Frame Drum', ['HDrumL_Hit_v2_rr1_Sum.wav', 'HDrumL_Hit_v2_rr2_Sum.wav'],
                   ['HDrumL_Hit_v3_rr1_Sum.wav', 'HDrumL_Hit_v3_rr2_Sum.wav']),
        RIM: file(V, VS + 'Slit Drum', 'LogDrumHi_MedM_v1_rr1_Sum.wav', 'LogDrumHi_MedM_v2_rr1_Sum.wav',
                  'LogDrumHi_MedM_v3_rr1_Sum.wav'),
        SNARE: file(V, VM + 'Conga', ['Quinto_HitFM1_v1_rr1_Sum.wav', 'Quinto_HitFM1_v1_rr2_Sum.wav'],
                    ['Quinto_HitFM1_v2_rr1_Sum.wav', 'Quinto_HitFM1_v2_rr2_Sum.wav']),
        CLAP: CLAPS,
        CHAT: SHAKER,
        TOMLO: file(V, VS + 'Slit Drum', 'LogDrumLo_MedM_v1_rr1_Sum.wav', 'LogDrumLo_MedM_v2_rr1_Sum.wav',
                    'LogDrumLo_MedM_v3_rr1_Sum.wav'),
        OHAT: file(V, VS + 'Shaker, Large', ['LShaker_Shake1U_rr1_Mid.wav', 'LShaker_Shake1D_rr2_Mid.wav']),
        TOMHI: file(V, VM + 'Bongos', ['BongoH_Hit1_v2_rr1_Mid.wav', 'BongoH_Hit1_v2_rr2_Mid.wav'],
                    ['BongoH_Hit1_v3_rr1_Mid.wav', 'BongoH_Hit1_v3_rr2_Mid.wav']),
        MARACAS: file(V, VS + 'Cabasa', ['Cabasa1_Hit_rr1_Mid.wav', 'Cabasa1_Hit_rr2_Mid.wav']),
        CONGA: CONGA_N,
        COWBELL: file(V, VS + 'Agogo Bells', 'Agogo_High_v1_rr1_Mid.wav', 'Agogo_High_v2_rr1_Mid.wav', 'Agogo_High_v3_rr1_Mid.wav'),
        CYMBAL: file(V, VS + 'Sleigh Bells', ['Sleighbells_Hit_rr1_Mid.wav', 'Sleighbells_Hit_rr2_Mid.wav']),
    },
    # Tabla Mist (libreria): i bol della tabla di Sonic Pi; bayan (ghe, ke) in basso, dayan (na, tin, te) in alto
    'kit_tabla': {
        KICK: file(S, '', ['tabla_ghe1.flac', 'tabla_ghe2.flac', 'tabla_ghe3.flac', 'tabla_ghe4.flac']),
        RIM: file(S, '', ['tabla_ke1.flac', 'tabla_ke2.flac', 'tabla_ke3.flac']),
        SNARE: file(S, '', ['tabla_na.flac', 'tabla_na_s.flac']),
        CLAP: file(S, '', ['tabla_tas1.flac', 'tabla_tas2.flac', 'tabla_tas3.flac']),
        CHAT: file(S, '', ['tabla_te1.flac', 'tabla_te2.flac']),
        TOMLO: file(S, '', ['tabla_ghe5.flac', 'tabla_ghe6.flac', 'tabla_ghe7.flac', 'tabla_ghe8.flac']),
        OHAT: file(S, '', ['tabla_tun1.flac', 'tabla_tun2.flac', 'tabla_tun3.flac']),
        TOMHI: file(S, '', 'tabla_re.flac'),
        MARACAS: file(S, '', 'tabla_te_m.flac'),
        CONGA: file(S, '', 'tabla_dhec.flac'),
        COWBELL: file(S, '', 'tabla_te_ne.flac'),
        CYMBAL: file(S, '', 'tabla_na_o.flac'),
    },
    # Taiko (libreria): la grancassa da concerto come ōdaiko, il tamburo tenore come shime, la piastra dei freni
    # come atarigane
    'kit_taiko': {
        KICK: file(V, VM + 'Bass Drum 1', ['BDrumNew_hit_v3_rr1_Sum.wav', 'BDrumNew_hit_v3_rr2_Sum.wav'],
                   ['BDrumNew_hit_v5_rr1_Sum.wav', 'BDrumNew_hit_v5_rr2_Sum.wav'], ['BDrumNew_hit_v7_rr1_Sum.wav', 'BDrumNew_hit_v7_rr2_Sum.wav']),
        RIM: file(V, VS + 'Woodblock', ['wood_click_f_rr1.wav', 'wood_click_f_rr2.wav']),
        SNARE: file(V, VM + 'Legacy Toms/tenor_higher', ['tenorH_mf_rr1.wav', 'tenorH_mf_rr2.wav'],
                    ['tenorH_ff_rr1.wav', 'tenorH_ff_rr2.wav', 'tenorH_ff_rr3.wav'], ['tenorH_fff_rr1.wav', 'tenorH_fff_rr2.wav']),
        CLAP: CLAPS,
        CHAT: file(V, VS + 'Woodblock', ['wood_click_pp_rr1.wav', 'wood_click_pp_rr2.wav', 'wood_click_pp_rr3.wav']),
        TOMLO: file(V, VM + 'Bass Drum 2', ['bassdrum_hit_mf1.wav', 'bassdrum_hit_mf2.wav'], 'bassdrum_hit_ff.wav'),
        OHAT: file(V, VS + 'Brake Drum', 'BrakeDrum1_Susp_v1_rr1_Mid.wav', 'BrakeDrum1_Susp_v3_rr1_Mid.wav'),
        TOMHI: file(V, VM + 'Legacy Toms/tenor_lower', ['tenor_mf_rr1.wav', 'tenor_mf_rr2.wav'],
                    ['tenor_ff_rr1.wav', 'tenor_ff_rr2.wav'], ['tenor_fff_rr1.wav', 'tenor_fff_rr2.wav']),
        MARACAS: file(V, VS + 'Shaker, Large', ['LShaker_Hit_rr1_Mid.wav', 'LShaker_Hit_rr2_Mid.wav']),
        CONGA: file(V, VM + 'Frame Drum', ['HDrumL_Hit_v3_rr1_Sum.wav', 'HDrumL_Hit_v3_rr2_Sum.wav']),
        COWBELL: file(V, VS + 'Brake Drum', 'BrakeDrum1_Hammer_v1_rr1_Mid.wav', 'BrakeDrum1_Hammer_v2_rr1_Mid.wav',
                      'BrakeDrum1_Hammer_v3_rr1_Mid.wav'),
        CYMBAL: file(V, VS + 'Gong 1', 'gong_mf.wav', 'gong_f.wav'),
    },
    # 808 (i Beat di sempre): la 808 vera di Fischer, il suono di mezzo delle manopole
    'kit_808': {
        KICK: f8('BD2550'), RIM: f8('RS'), SNARE: f8('SD2550'), CLAP: f8('CP'), CHAT: f8('CH'), TOMLO: f8('LT25'),
        OHAT: f8('OH25'), TOMHI: f8('HT25'), MARACAS: f8('MA'), CONGA: f8('MC25'), COWBELL: f8('CB'),
        CYMBAL: f8('CY5050'),
    },
    # Techno (i Beat di sempre): la 909 della TR-8, con il ride al posto del piatto
    'kit_techno': {
        KICK: mk(T_BD + '005_909_Bass_Drum_2'), RIM: mk(T_PC + '009_909_Rim_Shot'),
        SNARE: mk(T_SD + '006_909_Snare_Drum_2'), CLAP: mk(T_PC + '019_909_Hand_Clap'),
        CHAT: mk(T_HH + '010_909_Closed_HiHat_Short'), TOMLO: mk(T_TOM + '013_909_Low_Tom_Short'),
        OHAT: mk(T_HH + '009_909_Open_HiHat_Short'), TOMHI: mk(T_TOM + '015_909_High_Tom_Short'),
        MARACAS: mk(T_PC + '026_808_Maracas'), CONGA: mk(T_PC + '002_727_Open_High_Conga'),
        COWBELL: mk(T_PC + '033_808_Cowbell'), CYMBAL: mk(T_HH + '026_909_Ride_Cymbal'),
    },
    # 808 Boom (libreria): la 808 di Fischer con la cassa lunga e chiara, i tom e le conghe alti
    'kit_808boom': {
        KICK: f8('BD5075'), RIM: f8('RS'), SNARE: f8('SD5075'), CLAP: f8('CP'), CHAT: f8('CH'), TOMLO: f8('LT50'),
        OHAT: f8('OH50'), TOMHI: f8('HT50'), MARACAS: f8('MA'), CONGA: f8('HC50'), COWBELL: f8('CB'),
        CYMBAL: f8('CY7575'),
    },
    # 808 Trap (libreria): la cassa più lunga e scura, il rullante secco, il charleston aperto corto
    'kit_808trap': {
        KICK: f8('BD0075'), RIM: f8('RS'), SNARE: f8('SD7510'), CLAP: f8('CP'), CHAT: f8('CH'), TOMLO: f8('LT00'),
        OHAT: f8('OH10'), TOMHI: f8('HT10'), MARACAS: f8('MA'), CONGA: f8('LC25'), COWBELL: f8('CB'),
        CYMBAL: f8('CY2525'),
    },
    # 909 House (libreria): la 909 della TR-8 com'è
    'kit_909': {
        KICK: mk(T_BD + '004_909_Bass_Drum_1'), RIM: mk(T_PC + '009_909_Rim_Shot'),
        SNARE: mk(T_SD + '005_909_Snare_Drum_1'), CLAP: mk(T_PC + '019_909_Hand_Clap'),
        CHAT: mk(T_HH + '008_909_Closed_HiHat'), TOMLO: mk(T_TOM + '010_909_Low_Tom'),
        OHAT: mk(T_HH + '007_909_Open_HiHat'), TOMHI: mk(T_TOM + '012_909_High_Tom'),
        MARACAS: mk(T_PC + '026_808_Maracas'), CONGA: mk(T_PC + '002_727_Open_High_Conga'),
        COWBELL: mk(T_PC + '033_808_Cowbell'), CYMBAL: mk(T_HH + '020_909_Crash_Cymbal'),
    },
    # 909 Rave (libreria): la 909 con l'attacco spinto, il battimani lungo, i tom lunghi
    'kit_909rave': {
        KICK: mk(T_BD + '012_909_AttackBD_1'), RIM: mk(T_PC + '009_909_Rim_Shot'),
        SNARE: mk(T_SD + '011_909_AttackSD_1'), CLAP: mk(T_PC + '020_909_Hand_Clap_Long'),
        CHAT: mk(T_HH + '008_909_Closed_HiHat'), TOMLO: mk(T_TOM + '016_909_Low_Tom_Long'),
        OHAT: mk(T_HH + '007_909_Open_HiHat'), TOMHI: mk(T_TOM + '018_909_High_Tom_Long'),
        MARACAS: mk(T_PC + '028_727_Cabasa'), CONGA: mk(T_PC + '002_727_Open_High_Conga'),
        COWBELL: mk(T_PC + '033_808_Cowbell'), CYMBAL: mk(T_HH + '021_909_Crash_Cymbal_Short'),
    },
    # 606 Tick (libreria): la 606 della TR-8; le claves della 808 per il bordo, il battimani della 707
    'kit_606': {
        KICK: mk(T_BD + '015_606_Bass_Drum_1'), RIM: mk(T_PC + '010_808_Claves_1'),
        SNARE: mk(T_SD + '013_606_Snare_Drum_1'), CLAP: mk(T_PC + '021_707_Hand_Clap'),
        CHAT: mk(T_HH + '014_606_Closed_HiHat'), TOMLO: mk(T_TOM + '035_606_Low_Tom'),
        OHAT: mk(T_HH + '013_606_Open_HiHat'), TOMHI: mk(T_TOM + '036_606_High_Tom'),
        MARACAS: mk(T_PC + '026_808_Maracas'), CONGA: mk(T_PC + '007_727_High_Bongo'),
        COWBELL: mk(T_PC + '033_808_Cowbell'), CYMBAL: mk(T_HH + '024_606_Cymbal'),
    },
    # Robot Pop (libreria): la 707 della TR-8, il tamburello al posto delle maracas
    'kit_707': {
        KICK: mk(T_BD + '009_707_Bass_Drum_1'), RIM: mk(T_PC + '012_707_Rim_Shot'),
        SNARE: mk(T_SD + '008_707_Snare_Dum_1'), CLAP: mk(T_PC + '021_707_Hand_Clap'),
        CHAT: mk(T_HH + '012_707_Closed_HiHat'), TOMLO: mk(T_TOM + '025_707_Low_Tom'),
        OHAT: mk(T_HH + '011_707_Open_HiHat'), TOMHI: mk(T_TOM + '027_707_High_Tom'),
        MARACAS: mk(T_PC + '036_707_Tambourine'), CONGA: mk(T_PC + '002_727_Open_High_Conga'),
        COWBELL: mk(T_PC + '015_727_Agogo_Mid'), CYMBAL: mk(T_HH + '022_707_Crash_Cymbal'),
    },
    # Linn Pop (libreria): la Yamaha RX5, campioni digitali degli anni ottanta
    'kit_rx5': {
        KICK: mk(X_BD + '001_Bass_Drum_1'), RIM: mk(X_SD + '004_Rim_Shot_1'), SNARE: mk(X_SD + '001_Snare_Drum_1'),
        CLAP: mk(X_PC + '001_Claps'), CHAT: mk(X_HH + '001_HiHat_Closed'), TOMLO: mk(X_TOM + '003_Tom_3'),
        OHAT: mk(X_HH + '002_HiHat_Open'), TOMHI: mk(X_TOM + '001_Tom_1'), MARACAS: mk(X_PC + '004_Shaker'),
        CONGA: mk(X_PC + '006_Conga_High_Open'), COWBELL: mk(X_PC + '003_Cowbell'),
        CYMBAL: mk(X_HH + '005_Crash_Cymbal'),
    },
    # Gated 80s (libreria): cassa e rullante col gate della DR-5, i tom pesanti della RX5
    'kit_80s': {
        KICK: mk(D_BD + '013_Gate_Kick_1'), RIM: mk(X_SD + '005_Rim_Shot_2'), SNARE: mk(D_SD + '031_Room_Gated_Snare'),
        CLAP: mk(X_PC + '001_Claps'), CHAT: mk(X_HH + '001_HiHat_Closed'), TOMLO: mk(X_TOM + '013_Heavy_Tom_3'),
        OHAT: mk(X_HH + '002_HiHat_Open'), TOMHI: mk(X_TOM + '011_Heavy_Tom_1'), MARACAS: mk(X_PC + '002_Tambourine'),
        CONGA: mk(X_PC + '007_Conga_Low'), COWBELL: mk(X_PC + '003_Cowbell'), CYMBAL: mk(X_HH + '006_China_Cymbal'),
    },
    # Minimal Click (libreria): suoni corti e asciutti, la cassa stretta e il rullante piccolo della DR-5
    'kit_minimal': {
        KICK: mk(D_BD + '032_Tight_Kick'), RIM: mk(T_PC + '013_707_Rim_Shot_Short'), SNARE: mk(D_SD + '039_Tiny_Snare'),
        CLAP: mk(T_PC + '024_808_Finger_Snap'), CHAT: mk(T_HH + '010_909_Closed_HiHat_Short'),
        TOMLO: mk(T_TOM + '004_808_Low_Tom_Short'), OHAT: mk(T_HH + '009_909_Open_HiHat_Short'),
        TOMHI: mk(T_TOM + '006_808_High_Tom_Short'), MARACAS: mk(T_PC + '026_808_Maracas'),
        CONGA: mk(T_TOM + '023_808_Mid_Conga_Short'), COWBELL: mk(T_PC + '033_808_Cowbell'),
        CYMBAL: mk(T_HH + '027_909_Ride_Cymbal_Short'),
    },
    # Dub Yard (libreria): la DR-5 col rullante reggae e i tom d'ambiente
    'kit_dub': {
        KICK: mk(D_BD + '007_Deep_Kick'), RIM: mk(D_SD + '041_Ambient_Side_Stick'), SNARE: mk(D_SD + '028_Reggae_Snare_1'),
        CLAP: mk(T_PC + '017_808_Hand_Clap'), CHAT: mk(D_HH + '006_Pop_Closed_Hi-hat'), TOMLO: mk(D_TOM + '004_Ambient_Tom_4'),
        OHAT: mk(D_HH + '007_Pop_Open_Hi-hat'), TOMHI: mk(D_TOM + '002_Ambient_Tom_2'), MARACAS: mk(D_PC + '020_Shaker'),
        CONGA: mk(D_PC + '012_Conga_High_Open'), COWBELL: mk(D_PC + '001_Cowbell'), CYMBAL: mk(D_HH + '017_Splash_Cymbal'),
    },
    # 2-Step (libreria): cassa e rullante house della DR-5, metalli e battimani della 909
    'kit_2step': {
        KICK: mk(D_BD + '017_House_Kick_1'), RIM: mk(T_PC + '008_808_Rim_Shot'), SNARE: mk(D_SD + '014_House_Snare'),
        CLAP: mk(T_PC + '019_909_Hand_Clap'), CHAT: mk(T_HH + '008_909_Closed_HiHat'), TOMLO: mk(T_TOM + '001_808_Low_Tom'),
        OHAT: mk(T_HH + '007_909_Open_HiHat'), TOMHI: mk(T_TOM + '003_808_High_Tom'), MARACAS: mk(D_PC + '020_Shaker'),
        CONGA: mk(T_TOM + '021_808_High_Conga'), COWBELL: mk(T_PC + '033_808_Cowbell'),
        CYMBAL: mk(T_HH + '026_909_Ride_Cymbal'),
    },
    # Jungle (libreria): una batteria acustica asciutta della DR-5, il rullante piccolo e brillante dei break
    'kit_jungle': {
        KICK: mk(D_BD + '009_Dry_Kick'), RIM: mk(D_SD + '041_Ambient_Side_Stick'), SNARE: mk(D_SD + '022_Piccolo_Snare'),
        CLAP: mk(D_PC + '035_TR-808_Clap'), CHAT: mk(D_HH + '001_Acoustic_Closed_Hi-hat'), TOMLO: mk(D_TOM + '024_Rock_Tom_4'),
        OHAT: mk(D_HH + '002_Acoustic_Open_Hi-hat'), TOMHI: mk(D_TOM + '022_Rock_Tom_2'), MARACAS: mk(D_PC + '002_Tambourine'),
        CONGA: mk(D_PC + '008_Bongo_High'), COWBELL: mk(D_PC + '001_Cowbell'), CYMBAL: mk(D_HH + '016_Rock_Ride_Cymbal'),
    },
    # Lo-Fi Dust (libreria): la cassa ovattata e il rullante «radio» della DR-5, i tom spazzolati
    'kit_lofi': {
        KICK: mk(D_BD + '022_Muffle_Kick'), RIM: mk(D_SD + '041_Ambient_Side_Stick'), SNARE: mk(D_SD + '023_Radio_Snare'),
        CLAP: mk(T_PC + '024_808_Finger_Snap'), CHAT: mk(D_HH + '006_Pop_Closed_Hi-hat'), TOMLO: mk(D_TOM + '012_Brush_Tom_4'),
        OHAT: mk(D_HH + '007_Pop_Open_Hi-hat'), TOMHI: mk(D_TOM + '010_Brush_Tom_2'), MARACAS: mk(D_PC + '021_Cabasa'),
        CONGA: mk(D_PC + '009_Bongo_Low'), COWBELL: mk(D_PC + '007_Wood_Block'), CYMBAL: mk(D_HH + '014_Ride_Cymbal'),
    },
    # Tape Crate (libreria): la batteria jazz della RX5, come un campionatore degli anni ottanta
    'kit_tape': {
        KICK: mk(X_BD + '004_Jazz_Bass_Drum_1'), RIM: mk(X_SD + '005_Rim_Shot_2'), SNARE: mk(X_SD + '006_Jazz_Snare_Drum_1'),
        CLAP: mk(X_PC + '001_Claps'), CHAT: mk(X_HH + '008_Jazz_HiHat_Closed'), TOMLO: mk(X_TOM + '007_Jazz_Tom_3'),
        OHAT: mk(X_HH + '007_Jazz_HiHat_Open'), TOMHI: mk(X_TOM + '005_Jazz_Tom_1'), MARACAS: mk(X_PC + '004_Shaker'),
        CONGA: mk(X_PC + '007_Conga_Low'), COWBELL: mk(X_PC + '018_Jazz_Cowbell'), CYMBAL: mk(X_HH + '010_Flat_Ride_Cymbal'),
    },
    # Trance Arena (libreria): la 909 con l'attacco, il battimani lungo e il charleston aperto pieno
    'kit_trance': {
        KICK: mk(T_BD + '013_909_AttackBD_2'), RIM: mk(T_PC + '009_909_Rim_Shot'),
        SNARE: mk(T_SD + '007_909_Snare_Drum_3'), CLAP: mk(T_PC + '020_909_Hand_Clap_Long'),
        CHAT: mk(T_HH + '010_909_Closed_HiHat_Short'), TOMLO: mk(T_TOM + '016_909_Low_Tom_Long'),
        OHAT: mk(T_HH + '007_909_Open_HiHat'), TOMHI: mk(T_TOM + '017_909_Mid_Tom_Long'),
        MARACAS: mk(T_PC + '028_727_Cabasa'), CONGA: mk(T_PC + '002_727_Open_High_Conga'),
        COWBELL: mk(T_PC + '035_727_Star_Chime'), CYMBAL: mk(T_HH + '020_909_Crash_Cymbal'),
    },
    # Psy Forest (libreria): la cassa d'attacco più corta della 909, metalli corti, i bonghi della 727
    'kit_psy': {
        KICK: mk(T_BD + '014_909_AttackBD_3'), RIM: mk(T_PC + '013_707_Rim_Shot_Short'),
        SNARE: mk(T_SD + '012_909_AttackSD_2'), CLAP: mk(T_PC + '022_808_Noise_Clap'),
        CHAT: mk(T_HH + '016_606_Closed_HiHat_Long'), TOMLO: mk(T_TOM + '031_808_NoiseTom_Low'),
        OHAT: mk(T_HH + '009_909_Open_HiHat_Short'), TOMHI: mk(T_TOM + '033_808_NoiseTom_High'),
        MARACAS: mk(T_PC + '026_808_Maracas'), CONGA: mk(T_PC + '007_727_High_Bongo'),
        COWBELL: mk(T_PC + '031_727_Quijada'), CYMBAL: mk(T_HH + '027_909_Ride_Cymbal_Short'),
    },
    # Goa Temple (libreria): 909 e 808, le conghe e l'agogô della 727, la campana a stella come piatto
    'kit_goa': {
        KICK: mk(T_BD + '006_909_Bass_Drum_3'), RIM: mk(T_PC + '011_808_Claves_2'),
        SNARE: mk(T_SD + '003_808_Snare_Drum_3'), CLAP: mk(T_PC + '018_808_Hand_Clap_Long'),
        CHAT: mk(T_HH + '014_606_Closed_HiHat'), TOMLO: mk(T_TOM + '019_808_Low_Conga'),
        OHAT: mk(T_HH + '015_606_Open_HiHat_Long'), TOMHI: mk(T_TOM + '021_808_High_Conga'),
        MARACAS: mk(T_PC + '027_808_Maracas_Long'), CONGA: mk(T_PC + '003_727_Mute_High_Conga'),
        COWBELL: mk(T_PC + '016_727_Agogo_High'), CYMBAL: mk(T_PC + '035_727_Star_Chime'),
    },
}
# l'ordine dei set nel banco: i quattro di sempre per primi, come prima
ORDINE = ['kit_studio', 'kit_jazz', 'kit_808', 'kit_techno', 'kit_room', 'kit_rock', 'kit_brushes', 'kit_cajon',
          'kit_darbuka', 'kit_latin', 'kit_afro', 'kit_tabla', 'kit_taiko', 'kit_808boom', 'kit_808trap', 'kit_909',
          'kit_909rave', 'kit_606', 'kit_707', 'kit_rx5', 'kit_80s', 'kit_minimal', 'kit_dub', 'kit_2step',
          'kit_jungle', 'kit_lofi', 'kit_tape', 'kit_trance', 'kit_psy', 'kit_goa']
assert sorted(ORDINE) == sorted(KIT) and all(len(k) == 12 for k in KIT.values())
