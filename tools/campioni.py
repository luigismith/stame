"""campioni.py — il banco di campioni di Stame, stame.smp (specifica 20, §7b, SND-370…379; SND-537).

Scarica i campioni CC0 scelti da due fonti, li prepara e li scrive nel formato del banco:
  - VCSL (Versilian Community Sample Library, CC0): https://github.com/sgossner/VCSL
  - Sonic Pi (campioni CC0 da freesound, per le batterie): https://github.com/sonic-pi-net/sonic-pi
I file scaricati restano in private/samples/ (fuori da git). Escono:
  - build/campioni/stame.smp            il banco (mono, 16 bit, 32 kHz; va nel pacchetto della Flip)
  - build/campioni/indice.json          i set e le zone, per controllo
  - src/platform/vetrina/campioni_idx.h gli indici dei set, per le patch (tools/patch.py)
  - assets/campioni/FONTI.md            ogni file usato, con la fonte e la licenza

    python -I tools/campioni.py            tutto
    python -I tools/campioni.py --kit      solo i kit di batteria (prova veloce)
    python -I tools/campioni.py --indice   solo l'indice e le fonti, senza scaricare

Per ogni zona: mono, togli la continua, ricampiona, taglia il silenzio in testa, normalizza al picco
a −1 dBFS, e poi: one-shot → taglia la coda sotto −66 dBFS (o al massimo di durata) con dissolvenza;
loop → trova fra 0,4 e 1,5 s dalla fine il punto che somiglia di più e incolla una dissolvenza di
30 ms prima della giunzione, così il nucleo salta senza calcoli.
"""
import json
import os
import re
import struct
import sys
import urllib.parse
import urllib.request

import numpy as np
import soundfile as sf

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
CACHE = os.path.join(RADICE, 'private', 'samples')
OUT = os.path.join(RADICE, 'build', 'campioni')
FS = 32000
VCSL = 'https://raw.githubusercontent.com/sgossner/VCSL/master/'
SONIC = 'https://raw.githubusercontent.com/sonic-pi-net/sonic-pi/dev/etc/samples/'
PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

# strumenti dell'ordine di drums.h
(KICK, RIM, SNARE, CLAP, CHAT, TOMLO, OHAT, TOMHI, MARACAS, CONGA, COWBELL, CYMBAL) = range(12)

# ---- gli strumenti a tastiera: (nome del set, cartella VCSL, regex del file, passo in semitoni, loop,
# secondi, ottava del nome). VCSL chiama «C4» il Do5 (Do centrale = «C3», convenzione Yamaha): +12
# semitoni rispetto al nome; il TX81Z usa i nomi MIDI veri (0). Il gruppo <n> è la nota nel nome;
# senza gruppo la nota si misura dal campione. In ogni caso l'intonazione si verifica (stima_f0). ----
STRUMENTI = [
    ('piano_kawai', 'Chordophones/Zithers/Grand Piano, Kawai/Sustains',
     r'GPiano_sus_(?P<n>[A-G]#?-?\d)_v3_rr1_Player\.wav', 4, False, 6.0, 12),
    ('piano_upright', 'Chordophones/Zithers/Upright Piano, Yamaha/Sustains',
     r'Upright1_Sus_(?P<n>[A-G]#?-?\d)_vl2_rr1\.wav', 5, False, 5.0, 12),
    ('fm_piano', 'Electrophones/TX81Z/FM Piano', r'FMPiano_(?P<n>[A-G]#?\d)_vl2\.wav', 4, False, 3.5, 0),
    ('vibes', 'Idiophones/Struck Idiophones/Vibraphone/Soft Mallets',
     r'Vibes_soft_(?P<n>[A-G]#?\d)_v2_rr\d_Main\.wav', 1, False, 4.0, 12),
    ('marimba', 'Idiophones/Struck Idiophones/Marimba', r'Marimba_hit_Outrigger_(?P<n>[A-G]#?\d)_med_01\.wav', 1, False, 2.5, 12),
    ('glock', 'Idiophones/Struck Idiophones/Glockenspiel', r'glock_medium_(?P<n>[A-G]#?\d)_01\.wav', 1, False, 3.0, 12),
    ('chimes', 'Idiophones/Struck Idiophones/Tubular Bells 1', r'chimes_(?P<n>[A-G]#?\d)_f+_rr\d\.wav', 1, False, 5.0, 12),
    ('harp', 'Chordophones/Composite Chordophones/Concert Harp', r'KSHarp_(?P<n>[A-G]#?\d)_mf\d\.wav', 4, False, 4.0, 0),
    ('kalimba', 'Idiophones/Plucked Idiophones/Kalimba, Tanzania',
     r'MBira3_pluck_Main_(?P<n>[A-G]#?\d)_k\d+(?:alt)?_50_100_rr2\.wav', 3, False, 3.0, 12),
    ('harpsichord', 'Chordophones/Zithers/Harpsichord, French/Sustains',
     r'Harpsi2_Normal_(?P<n>[A-G]#?\d)_rr1_Main\.wav', 4, False, 3.0, 12),
    ('organ', 'Aerophones/Edge-blown Aerophones/Pipe Organ/Quiet', r'NT5_Man3Quiet_(?P<n>[A-G]#?\d)_rr1\.wav', 6, True, 3.0, 12),
    ('recorder', 'Aerophones/Edge-blown Aerophones/Baroque Alto Recorder/Sustain',
     r'AltRecorder_Sus_(?P<n>[A-G]#?\d)_rr1_Main\.wav', 1, True, 3.0, 12),
    ('sax', 'Aerophones/Reed Aerophones/Tenor Saxophone/Non-Vibrato',
     r'BrettTenor_NV_Main_(?P<n>[A-G]#?\d)_vl2_rr1\.wav', 4, True, 3.0, 12),
    # la seconda ondata, 15/10/2026 sera («tantissimi altri suoni»)
    ('tx_piano', 'Electrophones/TX81Z/Piano 1', r'Piano 1_(?P<n>[A-G]#?\d)_vl2\.wav', 4, False, 3.0, 12),
    ('clavisynth', 'Electrophones/TX81Z/Clavisynth', r'Clavisynth_(?P<n>[A-G]#?\d)_vl2\.wav', 4, False, 2.5, 24),
    ('upright_knight', 'Chordophones/Zithers/Upright Piano, Knight/Sustains',
     r'Player_vl2_rr1_(?P<n>[A-G]#?-?\d)\.wav', 5, False, 4.0, 12),
    ('harpsi_italian', 'Chordophones/Zithers/Harpsichord, Italian/Sustains/stop1',
     r'Harpsichord_stop1_(?P<n>[A-G]#?\d)_1\.wav', 4, False, 2.5, 12),
    ('harpsi_lute', 'Chordophones/Zithers/Harpsichord, English/Sustains/Lute',
     r'ZuckermannKitHarpsi_Lute_Sus_(?P<n>[A-G]#?\d)_rr1\.wav', 4, False, 2.0, 12),
    ('organ_loud', 'Aerophones/Edge-blown Aerophones/Pipe Organ/Loud', r'Rode_Man3Open_(?P<n>[A-G]#?\d)\.wav', 6, True, 2.5, 0),
    ('organ_ren', "Aerophones/Edge-blown Aerophones/Renaissance Organ/8'",
     r"RenOrgan_8foot_Room_(?P<n>[A-G]#?\d)_rr1\.wav", 6, True, 2.5, 12),
    ('organ_full', 'Aerophones/Edge-blown Aerophones/Renaissance Organ/Full',
     r'RenOrgan_Full_Room_(?P<n>[A-G]#?\d)_rr1\.wav', 6, True, 2.5, 12),
    ('recorder_sop', 'Aerophones/Edge-blown Aerophones/Baroque Soprano Recorder/Sustain',
     r'SopRecorder_Sus_(?P<n>[A-G]#?\d)_rr1_Main\.wav', 1, True, 2.5, 12),
    ('recorder_ten', 'Aerophones/Edge-blown Aerophones/Baroque Tenor Recorder/SusVib',
     r'TenRecorder_SusVib_(?P<n>[A-G]#?\d)_rr1_Main\.wav', 1, True, 2.5, 12),
    ('recorder_bass', 'Aerophones/Edge-blown Aerophones/Baroque Bass Recorder/Sustain',
     r'BassRecorder_Sus_(?P<n>[A-G]#?\d)_rr1_Main\.wav', 1, True, 2.5, 12),
    ('ocarina', 'Aerophones/Edge-blown Aerophones/Ocarina, Typical/Sustains/Sus', r'StdOcarina_Sus_(?P<n>[A-G]#?\d)\.wav', 1, True, 2.5, 12),
    ('harmonica', 'Aerophones/Free Aerophones/Harmonica-Hohner-Special20-C/Sustains/Normal',
     r'Hohner-Special20_Normal_(?P<n>[A-G]#?\d)\.wav', 1, True, 2.5, 12),
    ('harmonica_chrom', 'Aerophones/Free Aerophones/Harmonica-Hohner-Super64/Sustains/Normal',
     r'Hohner-Super64_Normal _(?P<n>[A-G]#?\d)\.wav', 1, True, 2.5, 12),
    ('saxello', 'Aerophones/Reed Aerophones/Saxello/Non-Vibrato',
     r'BrettSaxello_SusNV_MainSpirit_(?P<n>[A-G]#?\d)_vl2_rr2\.wav', 1, True, 2.5, 12),
    ('didgeridoo', 'Aerophones/Lip Aerophones/Didgeridoo', r'Didgeridoo1_Sus\d_Main\.wav', 1, True, 3.0, 12),
    ('strumstick', 'Chordophones/Composite Chordophones/Strumstick/Finger',
     r'Strumstick_Finger_Str\d_Main_(?P<n>[A-G]#?\d)_vl2_rr\d\.wav', 2, False, 2.5, 12),
    ('dan_tranh', 'Chordophones/Zithers/Dan Tranh/Normal', r'(?P<n>[A-G]#?\d)_mf_1\.wav', 2, False, 3.0, 12),
    ('psaltery_bow', 'Chordophones/Zithers/Psaltery, Bowed and Plucked/LongBow',
     r'BowedPsaltery_(?P<n>[A-G]#?\d)_Main_LongBow_rr\d\.wav', 1, True, 2.5, 12),
    ('psaltery_pluck', 'Chordophones/Zithers/Psaltery, Bowed and Plucked/Pluck',
     r'BowedPsaltery_(?P<n>[A-G]#?\d)_Main_Pluck_rr\d\.wav', 1, False, 2.5, 12),
    ('mbira', 'Idiophones/Plucked Idiophones/Mbira Mavembe (Gandanga), Zimbabwe, Low G',
     r'Mbira5_Normal_MainSpirit_(?P<n>[A-G]#?\d)_k\d+_vl2_rr1\.wav', 2, False, 2.5, 12),
    ('nyunga', 'Idiophones/Plucked Idiophones/Nyunga Nyunga, Mozambique, Low F',
     r'Mbira2_Normal_MainSpirit_(?P<n>[A-G]#?\d)_k\d+_vl3_rr2\.wav', 2, False, 2.5, 12),
    ('kalimba_kenya', 'Idiophones/Plucked Idiophones/Kalimba, Kenya',
     r'Mbira6_Normal_MainSpirit_(?P<n>[A-G]#?\d)_k\d+_vl3_rr2\.wav', 2, False, 2.5, 12),
    ('hand_chimes', 'Idiophones/Struck Idiophones/Hand Chimes', r'sus_(?P<n>[A-G]#?\d)_r01_main\.wav', 2, False, 4.0, 12),
    ('tub_glock', 'Idiophones/Struck Idiophones/Tubular Glockenspiel', r'(?P<n>[A-G]#?\d)_medium1\.wav', 1, False, 3.0, 72),
    ('vibes_bowed', 'Idiophones/Struck Idiophones/Vibraphone/Bowed', r'Vibes_bowed_(?P<n>[A-G]#?\d)_rr1_Main\.wav', 1, True, 3.0, 12),
    ('balafon', 'Idiophones/Struck Idiophones/Balafon/Soft Mallet', r'EthnicXylo_softM_(?P<n>[A-G]#?\d)_vl2_rr\d_Mid\.wav', 1, False, 2.0, 12),
    ('xylophone', 'Idiophones/Struck Idiophones/Xylophone/Medium Mallets', r'Xylo_Medium_(?P<n>[A-G]#?\d)_ff_01_far\.wav', 1, False, 2.0, 12),
    ('wine_glasses', 'Idiophones/Friction Idiophones/Wine Glasses/Sustains/Slow', r'glass\d_(?P<n>[A-G]#?\d)_Slow_\d_Main\.wav', 1, True, 3.0, 12),
]

# ---- i kit: strumento → (fonte, file, velocity minima del layer); V = VCSL, S = Sonic Pi ----
V = 'V'
S = 'S'
KIT = {
    'kit_studio': [
        (KICK, V, 'Membranophones/Struck Membranophones/Bass Drum 1/BDrumNew_hit_v5_rr1_Sum.wav', 0),
        (RIM, V, 'Membranophones/Struck Membranophones/Snare Drum, Modern 2/Snare3M_Xstick_v2_rr1_Mid.wav', 0),
        (SNARE, V, 'Membranophones/Struck Membranophones/Snare Drum, Modern 1/Snare2_HitSN_v6_rr1_Mid.wav', 0),
        (SNARE, V, 'Membranophones/Struck Membranophones/Snare Drum, Modern 1/Snare2_HitSN_v9_rr1_Mid.wav', 100),
        (CLAP, V, 'Idiophones/Struck Idiophones/Claps/Clap_rr1.wav', 0),
        (CHAT, V, 'Idiophones/Struck Idiophones/Hi-Hat Cymbal/HiHat_HitC_v3_rr1_Mid.wav', 0),
        (OHAT, V, 'Idiophones/Struck Idiophones/Hi-Hat Cymbal/HiHat_HitO_rr1_Mid.wav', 0),
        (TOMLO, V, 'Membranophones/Struck Membranophones/Tom 2/Stick/TomL_HitS_v3_rr1_Mid.wav', 0),
        (TOMHI, V, 'Membranophones/Struck Membranophones/Tom 1/Stick/TomH_HitS_v3_rr1_Mid.wav', 0),
        (MARACAS, V, 'Idiophones/Struck Idiophones/Shaker, Small/Mid_ShakerHighFaster_Down_rr1.wav', 0),
        (CONGA, V, 'Membranophones/Struck Membranophones/Conga/Conga_HitN_v2_rr1_Sum.wav', 0),
        (COWBELL, V, 'Idiophones/Struck Idiophones/Cowbells/Cowbell1_Hit_v3_rr1_Mid.wav', 0),
        (CYMBAL, V, 'Idiophones/Struck Idiophones/Suspended Cymbal 1/susCymb1_hit_f1.wav', 0),
    ],
    'kit_jazz': [
        (KICK, S, 'bd_jazz.flac', 0),
        (RIM, V, 'Membranophones/Struck Membranophones/Snare Drum, Modern 2/Snare3M_Xstick_v2_rr2_Mid.wav', 0),
        (SNARE, S, 'drum_snare_soft.flac', 0),
        (SNARE, S, 'drum_snare_hard.flac', 100),
        (CLAP, S, 'perc_snap2.flac', 0),
        (CHAT, S, 'drum_cymbal_closed.flac', 0),
        (OHAT, S, 'drum_cymbal_open.flac', 0),
        (TOMLO, S, 'drum_tom_lo_soft.flac', 0),
        (TOMHI, S, 'drum_tom_hi_soft.flac', 0),
        (MARACAS, V, 'Idiophones/Struck Idiophones/Cabasa/Cabasa1_Rub_v1_rr1_Mid.wav', 0),
        (CONGA, V, 'Membranophones/Struck Membranophones/Conga/Quinto_HitN_v2_rr1_Sum.wav', 0),
        (COWBELL, S, 'drum_cowbell.flac', 0),
        (CYMBAL, S, 'drum_cymbal_soft.flac', 0),
    ],
    'kit_808': [
        (KICK, S, 'bd_808.flac', 0),
        (RIM, S, 'elec_wood.flac', 0),
        (SNARE, S, 'sn_dub.flac', 0),
        (CLAP, S, 'perc_snap.flac', 0),
        (CHAT, S, 'drum_cymbal_closed.flac', 0),
        (OHAT, S, 'drum_cymbal_open.flac', 0),
        (TOMLO, S, 'drum_tom_lo_hard.flac', 0),
        (TOMHI, S, 'drum_tom_hi_hard.flac', 0),
        (MARACAS, S, 'elec_tick.flac', 0),
        (CONGA, S, 'elec_bong.flac', 0),
        (COWBELL, S, 'drum_cowbell.flac', 0),
        (CYMBAL, S, 'elec_cymbal.flac', 0),
    ],
}
KIT_SECONDI = {CYMBAL: 3.0, OHAT: 2.0}
DEFAULT_KIT_S = 1.5


def midi(name):
    m = re.fullmatch(r'([A-G])(#?)(-?\d)', name)
    return 12 * (int(m[3]) + 1) + PC[m[1]] + (1 if m[2] else 0)


def url_of(fonte, path):
    return (VCSL if fonte == V else SONIC) + urllib.parse.quote(path)


def scarica(fonte, path):
    dest = os.path.join(CACHE, 'vcsl' if fonte == V else 'sonicpi', *path.split('/'))
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    url = url_of(fonte, path)
    print('  scarico', path)
    for tentativo in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r, open(dest + '.part', 'wb') as f:
                while True:
                    b = r.read(1 << 16)
                    if not b:
                        break
                    f.write(b)
            os.replace(dest + '.part', dest)
            return dest
        except Exception as e:                      # noqa: BLE001 — si riprova
            print('    errore', e)
    sys.exit(f'non scaricabile: {url}')


def leggi(path):
    x, fs = sf.read(path, dtype='float64', always_2d=True)
    return x.mean(axis=1), fs


def ricampiona(x, fs_in):
    if fs_in == FS:
        return x
    n_out = int(round(len(x) * FS / fs_in))
    X = np.fft.rfft(x)
    k = n_out // 2 + 1
    Y = X[:k] if k <= len(X) else np.concatenate([X, np.zeros(k - len(X))])
    return np.fft.irfft(Y, n_out) * (n_out / len(x))


def inviluppo(x, finestra):
    a = np.abs(x)
    n = len(a) // finestra * finestra
    return a[:n].reshape(-1, finestra).max(axis=1)


def prepara(x, fs_in, loop, max_s):
    """mono già fatto: ricampiona, taglia la testa, normalizza; poi coda o loop. Restituisce
    (int16, loop_start, loop_end)."""
    x = x - x.mean()
    x = ricampiona(x, fs_in)
    pk = np.abs(x).max()
    if pk <= 0:
        sys.exit('campione muto')
    x = x / pk
    # testa: il primo campione sopra −45 dBFS, meno 2 ms
    sopra = np.nonzero(np.abs(x) > 10 ** (-45 / 20))[0]
    i0 = max(0, sopra[0] - int(0.002 * FS)) if len(sopra) else 0
    x = x[i0:]
    if loop:
        x = x[:int(max_s * FS) + int(1.5 * FS)]
        x, ls, le = metti_loop(x, max_s)
    else:
        env = inviluppo(x, 256)
        vivo = np.nonzero(env > 10 ** (-66 / 20))[0]
        fine = min(len(x), (vivo[-1] + 2) * 256 if len(vivo) else len(x), int(max_s * FS))
        x = x[:fine]
        fade = min(len(x) // 4, int(0.03 * FS))
        if fade > 0:
            x[-fade:] *= np.linspace(1.0, 0.0, fade)
        ls = le = 0
    x = x / max(np.abs(x).max(), 1e-9) * 0.891            # −1 dBFS
    y = np.clip(np.round(x * 32767.0), -32768, 32767).astype('<i2')
    return y, ls, le


def metti_loop(x, max_s):
    """loop lungo fra 0,4 e 1,5 s che finisce entro max_s: cerca la giunzione che somiglia di più,
    incolla la dissolvenza e taglia dopo la fine del loop (più 2 campioni per l'interpolazione)."""
    N = len(x)
    e = min(N - int(0.05 * FS), int(max_s * FS))
    W = int(0.04 * FS)                                     # finestra di confronto: 40 ms
    tmin, tmax = int(0.4 * FS), int(1.5 * FS)
    if e - tmax - W < 0:
        tmax = e - W - 1
    if tmax <= tmin:
        sys.exit(f'campione troppo corto per il loop: {N / FS:.2f} s')
    ref = x[e - W:e]
    dec = 4
    xd, refd = x[::dec], ref[::dec]
    # correlazione normalizzata delle finestre che finiscono in s, per s nel campo ammesso
    cands = np.arange(e - tmax, e - tmin, dec)
    best, best_s = -2.0, None
    norm_ref = np.linalg.norm(refd) + 1e-9
    for s in cands:
        seg = xd[(s - W) // dec:s // dec]
        if len(seg) != len(refd):
            continue
        c = float(np.dot(seg, refd) / ((np.linalg.norm(seg) + 1e-9) * norm_ref))
        if c > best:
            best, best_s = c, s
    # raffina a passo 1 intorno al migliore, poi allinea la fase allo zero crossing in salita di e
    lo, hi = max(W, best_s - 2 * dec), min(e - tmin, best_s + 2 * dec)
    best = -2.0
    for s in range(lo, hi + 1):
        seg = x[s - W:s]
        c = float(np.dot(seg, ref) / ((np.linalg.norm(seg) + 1e-9) * (np.linalg.norm(ref) + 1e-9)))
        if c > best:
            best, best_s = c, s
    s = best_s
    C = int(0.03 * FS)                                     # dissolvenza di 30 ms prima della giunzione
    w = np.linspace(0.0, 1.0, C)
    y = x.copy()
    y[e - C:e] = x[e - C:e] * (1.0 - w) + x[s - C:s] * w
    y = np.concatenate([y[:e], y[s:s + 2]])
    return y, s, e


def finestra_analisi(x):
    """0,35 s di segnale da 30 ms dopo l'attacco (dove un percussivo ha ancora energia), con Hann"""
    i0 = min(int(0.03 * FS), max(0, len(x) - int(0.35 * FS)))
    seg = x[i0:i0 + int(0.35 * FS)]
    if len(seg) < int(0.1 * FS):
        return None
    return seg * np.hanning(len(seg))


def picchi_spettro(x):
    """i picchi dello spettro fra 40 Hz e 8 kHz: lista di (Hz, dB) in ordine di frequenza, con i dB
    riferiti al picco più alto (0 dB)"""
    seg = finestra_analisi(x)
    if seg is None:
        return []
    n = 1 << int(np.ceil(np.log2(len(seg) * 4)))
    mag = 20.0 * np.log10(np.abs(np.fft.rfft(seg, n)) + 1e-9)
    df = FS / n
    lo, hi = int(40 / df), int(8000 / df)
    m = mag[lo:hi]
    top = m.max()
    idx = np.nonzero((m[1:-1] > m[:-2]) & (m[1:-1] >= m[2:]) & (m[1:-1] > top - 50))[0] + 1
    grezzi = [((lo + i) * df, m[i] - top) for i in idx]
    picchi = []                                            # un picco ogni 10 Hz: il più alto del gruppo
    for f, d in grezzi:
        if picchi and f - picchi[-1][0] < 10.0:
            if d > picchi[-1][1]:
                picchi[-1] = (f, d)
        else:
            picchi.append((f, d))
    return picchi


def stima_ac(x):
    """nota MIDI (float) dal primo picco alto dell'autocorrelazione fra 25 Hz e 5 kHz, o None.
    Regge bene la fondamentale mancante, sbaglia d'ottava sui suoni molto acuti o inarmonici."""
    seg = finestra_analisi(x)
    if seg is None:
        return None
    n = 1 << int(np.ceil(np.log2(len(seg) * 2)))
    X = np.fft.rfft(seg, n)
    ac = np.fft.irfft(np.abs(X) ** 2)[:len(seg)]
    ac /= ac[0] + 1e-12
    lo, hi = int(FS / 5000), int(FS / 25)
    k = lo + int(np.argmax(ac[lo:hi]))
    cands = [i for i in range(lo + 1, hi - 1) if ac[i] > ac[i - 1] and ac[i] >= ac[i + 1] and ac[i] > 0.6 * ac[k]]
    k = cands[0] if cands else k
    if ac[k] < 0.3:
        return None
    den = ac[k - 1] - 2 * ac[k] + ac[k + 1]
    d = 0.5 * (ac[k - 1] - ac[k + 1]) / den if abs(den) > 1e-12 else 0.0   # vertice della parabola
    return 69.0 + 12.0 * np.log2(FS / (k + d) / 440.0)


def stima_f0(y):
    """nota MIDI (float) della fondamentale di un campione int16 e la sua attendibilità (0…1).
    Setaccio armonico: i candidati sono i picchi forti dello spettro, i loro sottomultipli fino a 1/4
    e la stima dell'autocorrelazione con le sue ottave; vince quello che spiega meglio i picchi come
    serie armonica: premio per ogni armonica presente (tutte con lo stesso peso), penale per quelle
    mancanti sotto la più alta trovata e per i picchi forti che restano fuori dalla serie. Così
    l'ottava sotto perde per le armoniche dispari mancanti e quella sopra per i picchi fuori serie.
    L'attendibilità cala se l'autocorrelazione non è d'accordo entro un semitono."""
    x = y.astype('float64') / 32768.0
    x = x - x.mean()
    P = picchi_spettro(x)
    if not P:
        return None, 0.0
    freqs = np.array([f for f, _ in P])
    mags = np.array([d for _, d in P])
    ac = stima_ac(x)
    cands = set()
    for f, d in P:
        if d < -25:
            continue
        for n in (1, 2, 3, 4):
            if 25.0 <= f / n <= 5000.0:
                cands.add(round(f / n, 1))
    if ac is not None:
        for k in (-1, 0, 1, 2):
            f = 440.0 * 2 ** ((ac - 69.0) / 12.0) * 2.0 ** k
            if 25.0 <= f <= 5000.0:
                cands.add(round(f, 1))
    punteggi = []
    for c in cands:
        presenti = {}
        for h in range(1, 17):
            fh = h * c
            if fh > 8000.0:
                break
            j = int(np.argmin(np.abs(freqs - fh)))
            if abs(freqs[j] - fh) <= max(0.03 * fh, 3.0):
                presenti[h] = j
        if not presenti:
            continue
        hmax = max(presenti)
        premi = [50.0 + mags[j] for j in presenti.values()]
        premio = sum(premi)
        mancanti = 0.5 * np.mean(premi) * sum(1 for h in range(1, hmax) if h not in presenti)
        r = freqs / c
        fuori = (np.abs(r - np.round(r)) > 0.03 * np.maximum(np.round(r), 1.0)) & (mags > -40.0) & (r <= 30.0)
        estranei = float(np.sum((mags[fuori] + 40.0) / 40.0 * 20.0))
        punteggi.append((premio - mancanti - estranei, c, presenti))
    if not punteggi:
        return None, 0.0
    punteggi.sort(reverse=True)
    best, c, presenti = punteggi[0]
    rivali = [s for s, cc, _ in punteggi[1:] if abs(cc - c) > 0.06 * c]      # oltre un semitono
    secondo = rivali[0] if rivali else -1e9
    conf = max(0.0, min(1.0, (best - secondo) / max(best, 1.0))) * max(0.0, min(1.0, best / 40.0))
    stime = [freqs[j] / h for h, j in presenti.items() if h <= 4]       # la frequenza precisa
    f0 = float(np.mean(stime)) if stime else c
    nota = 69.0 + 12.0 * np.log2(f0 / 440.0)
    if ac is None or abs(ac - nota) > 1.0:
        conf = min(conf, 0.3)
    return nota, float(conf)


AVVISI = []

# set dai parziali non armonici (campane, lamelle, barre): la misura si stampa ma non decide l'ottava
INARMONICI = {'chimes', 'hand_chimes', 'glock', 'tub_glock', 'kalimba', 'kalimba_kenya', 'mbira', 'nyunga',
              'vibes', 'vibes_bowed', 'marimba', 'xylophone', 'balafon'}

# file di VCSL la cui nota vera non è quella del nome (controllati con lo spettro): nome del file →
# nota MIDI. Vince sulla convenzione del set.
ECCEZIONI = {}


def root_zone(nome, scelti):
    """le note delle zone di un set. La convenzione d'ottava dei nomi (colonna oct di STRUMENTI) è
    una sola per set, e la misura la controlla: se almeno due terzi delle zone attendibili (e almeno
    tre) la contraddicono della stessa ottava, la convenzione si sposta, con un avviso. Le singole
    zone che non tornano finiscono negli avvisi ma restano sulla convenzione: un errore di misura su
    un file non deve spostare la sua zona. scelti: lista di (nota del nome o None, file, y)."""
    misure = [stima_f0(y) for _, _, y in scelti]
    voti = [int(round((m - n) / 12.0)) for (n, _, _), (m, conf) in zip(scelti, misure)
            if n is not None and m is not None and conf >= 0.5]
    conv = 0
    if voti:
        vincente = max(set(voti), key=voti.count)
        quanti = voti.count(vincente)
        riga = f'{nome}: ottava dei nomi misurata {12 * vincente:+d} semitoni ({quanti} zone su {len(voti)} attendibili)'
        if vincente and nome not in INARMONICI and quanti >= 3 and quanti * 3 >= len(voti) * 2:
            conv = 12 * vincente
            AVVISI.append(riga + ': convenzione del set corretta')
        elif vincente:
            AVVISI.append(riga + ': tengo la convenzione della tabella')
        print('  ' + riga)
    roots = []
    for (n, file, _), (m, conf) in zip(scelti, misure):
        if file in ECCEZIONI:
            roots.append(ECCEZIONI[file])
            continue
        if n is None:                                      # la nota viene solo dalla misura
            if m is None:
                sys.exit(f'{nome}: {file} senza nota nel nome e senza misura')
            if conf < 0.5:
                AVVISI.append(f'{nome}: {file}: senza nota nel nome, misurata {m:.1f} (attendibilità {conf:.2f})')
            roots.append(int(round(m)))
            continue
        root = n + conv
        if m is not None and conf >= 0.5 and abs(m - root) > 1.5:
            AVVISI.append(f'{nome}: {file}: nota {root}, misurata {m:.1f} (attendibilità {conf:.2f})')
        roots.append(root)
    return roots


def zone_strumento(nome, cartella, rx, passo, loop, max_s, oct_nome, fonti):
    """sceglie i file della cartella VCSL a passo di semitoni e prepara una zona per ciascuno"""
    albero = json.load(open(os.path.join(OUT, 'vcsl_tree.json'), encoding='utf-8'))
    disp = []
    for e in albero['tree']:
        if e['type'] != 'blob' or not e['path'].startswith(cartella + '/'):
            continue
        m = re.fullmatch(rx, e['path'].split('/')[-1])
        if m:
            n = midi(m['n']) + oct_nome if 'n' in m.groupdict() else None
            disp.append((n if n is not None else len(disp), e['path'], n))
    disp.sort()
    if not disp:
        sys.exit(f'{nome}: nessun file in {cartella} con {rx}')
    scelti, ultimo = [], -999
    for ordine, p, n in disp:
        if n is None or n >= ultimo + passo:
            scelti.append((n, p))
            ultimo = n if n is not None else ultimo
    pronti = []
    for n, p in scelti:
        x, fs = leggi(scarica(V, p))
        y, ls, le = prepara(x, fs, loop, max_s)
        pronti.append((n, p.split('/')[-1], y, ls, le))
        fonti.append((nome, url_of(V, p), 'VCSL, CC0'))
    zone = []
    for (n, file, y, ls, le), root in zip(pronti, root_zone(nome, [(n, f, y) for n, f, y, _, _ in pronti])):
        print(f'{nome}: nota {root} {file}')
        zone.append(dict(root=root, lo=0, hi=127, vel_lo=0, data=y, ls=ls, le=le))
    # zone in ordine di nota, senza doppioni, con i confini a metà fra due note
    zone.sort(key=lambda z: z['root'])
    zone = [z for i, z in enumerate(zone) if i == 0 or z['root'] != zone[i - 1]['root']]
    for k, z in enumerate(zone):
        z['lo'] = 0 if k == 0 else (zone[k - 1]['root'] + z['root']) // 2 + 1
        z['hi'] = 127 if k == len(zone) - 1 else (z['root'] + zone[k + 1]['root']) // 2
    return zone


def zone_kit(nome, voci, fonti):
    zone = []
    for inst, fonte, path, vel_lo in voci:
        x, fs = leggi(scarica(fonte, path))
        y, ls, le = prepara(x, fs, False, KIT_SECONDI.get(inst, DEFAULT_KIT_S))
        zone.append(dict(root=inst, lo=inst, hi=inst, vel_lo=vel_lo, data=y, ls=0, le=0))
        fonti.append((nome, url_of(fonte, path), 'VCSL, CC0' if fonte == V else 'Sonic Pi (freesound), CC0'))
    print(f'{nome}: {len(zone)} strumenti')
    return zone


def scrivi_banco(sets, path):
    """sets: lista di (nome, flags, zone); il formato è quello di §7b.2"""
    n_sets = len(sets)
    n_zones = sum(len(z) for _, _, z in sets)
    data_off = (20 + 32 * n_sets + 32 * n_zones + 3) & ~3
    dati, zone_rec, set_rec = [], [], []
    off = 0
    first = 0
    for nome, flags, zone in sets:
        set_rec.append(struct.pack('<24sHHHH', nome.encode('ascii'), first, len(zone), flags, 0))
        for z in zone:
            y = z['data']
            zone_rec.append(struct.pack('<IIIIIfBBBBI', off, len(y), z['ls'], z['le'], FS, 1.0,
                                        z['root'], z['lo'], z['hi'], z['vel_lo'], 0))      # 32 byte
            dati.append(y.tobytes())
            off += len(y)
        first += len(zone)
    testa = b'STMP' + struct.pack('<HHHHII', 1, n_sets, n_zones, 0, data_off, off)
    corpo = testa + b''.join(set_rec) + b''.join(zone_rec)
    corpo += b'\0' * (data_off - len(corpo))
    with open(path, 'wb') as f:
        f.write(corpo)
        for d in dati:
            f.write(d)
    return off


def scrivi_indice(sets):
    righe = ['/* campioni_idx.h — indici dei set del banco stame.smp (specifica 20, §7b). Generato da',
             ' * tools/campioni.py: non va modificato a mano. Le patch SMP mettono l\'indice in SMPSET. */',
             '#ifndef STAME_CAMPIONI_IDX_H', '#define STAME_CAMPIONI_IDX_H', '', 'enum {']
    for i, (nome, _, zone) in enumerate(sets):
        righe.append(f'    SMP_SET_{nome.upper()} = {i},'.ljust(36) + f'/* {len(zone)} zone */')
    righe += [f'    SMP_SET_COUNT = {len(sets)}', '};', '', '#endif', '']
    with open(os.path.join(RADICE, 'src', 'platform', 'vetrina', 'campioni_idx.h'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(righe))


def scrivi_fonti(fonti):
    righe = ['# Fonti dei campioni di Stame', '',
             'Il banco `stame.smp` (costruito da `tools/campioni.py`, non nel repo) usa solo campioni **CC0** '
             '(Creative Commons Zero: pubblico dominio), ricampionati a 32 kHz mono e tagliati.', '',
             '- **VCSL**, Versilian Community Sample Library, CC0 1.0: <https://github.com/sgossner/VCSL>',
             '- **Sonic Pi**, campioni di freesound.org donati in CC0: <https://github.com/sonic-pi-net/sonic-pi/tree/dev/etc/samples>',
             '', '| Set | File | Licenza |', '|---|---|---|']
    for nome, url, lic in fonti:
        righe.append(f'| {nome} | <{url}> | {lic} |')
    righe.append('')
    os.makedirs(os.path.join(RADICE, 'assets', 'campioni'), exist_ok=True)
    with open(os.path.join(RADICE, 'assets', 'campioni', 'FONTI.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(righe))


def albero_vcsl():
    dest = os.path.join(OUT, 'vcsl_tree.json')
    if not os.path.exists(dest):
        print('scarico l\'albero di VCSL')
        with urllib.request.urlopen('https://api.github.com/repos/sgossner/VCSL/git/trees/master?recursive=1', timeout=60) as r:
            open(dest, 'wb').write(r.read())


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(CACHE, exist_ok=True)
    solo_kit = '--kit' in argv
    solo_indice = '--indice' in argv
    sets, fonti = [], []
    if not solo_kit:
        for nome, cartella, rx, passo, loop, max_s, oct_nome in STRUMENTI:
            if solo_indice:
                sets.append((nome, 1 if loop else 0, [None] * 0))
                continue
            albero_vcsl()
            sets.append((nome, 1 if loop else 0, zone_strumento(nome, cartella, rx, passo, loop, max_s, oct_nome, fonti)))
    for nome, voci in KIT.items():
        sets.append((nome, 0, [] if solo_indice else zone_kit(nome, voci, fonti)))
    scrivi_indice(sets)
    if solo_indice:
        print('indice scritto')
        return
    path = os.path.join(OUT, 'stame.smp')
    n = scrivi_banco(sets, path)
    scrivi_fonti(fonti)
    indice = [dict(set=nome, flags=flags, zone=[dict(root=z['root'], lo=z['lo'], hi=z['hi'], vel_lo=z['vel_lo'],
                                                     len=int(len(z['data'])), loop=[int(z['ls']), int(z['le'])]) for z in zone])
              for nome, flags, zone in sets]
    json.dump(indice, open(os.path.join(OUT, 'indice.json'), 'w', encoding='utf-8'), indent=1)
    for a in AVVISI:
        print('avviso:', a)
    print(f'{path}: {len(sets)} set, {sum(len(z) for _, _, z in sets)} zone, {n * 2 / 1e6:.1f} MB, {n / FS:.0f} s di audio, {len(AVVISI)} avvisi')


if __name__ == '__main__':
    main(sys.argv[1:])
