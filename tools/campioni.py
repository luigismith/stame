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

# ---- gli strumenti a tastiera: (nome del set, cartella VCSL, regex del file, passo in semitoni, loop, secondi) ----
STRUMENTI = [
    ('piano_kawai', 'Chordophones/Zithers/Grand Piano, Kawai/Sustains',
     r'GPiano_sus_(?P<n>[A-G]#?-?\d)_v3_rr1_Player\.wav', 4, False, 6.0),
    ('piano_upright', 'Chordophones/Zithers/Upright Piano, Yamaha/Sustains',
     r'Upright1_Sus_(?P<n>[A-G]#?-?\d)_vl2_rr1\.wav', 5, False, 5.0),
    ('fm_piano', 'Electrophones/TX81Z/FM Piano', r'FMPiano_(?P<n>[A-G]#?\d)_vl2\.wav', 4, False, 3.5),
    ('vibes', 'Idiophones/Struck Idiophones/Vibraphone/Soft Mallets',
     r'Vibes_soft_(?P<n>[A-G]#?\d)_v2_rr\d_Main\.wav', 1, False, 4.0),
    ('marimba', 'Idiophones/Struck Idiophones/Marimba', r'Marimba_hit_Outrigger_(?P<n>[A-G]#?\d)_med_01\.wav', 1, False, 2.5),
    ('glock', 'Idiophones/Struck Idiophones/Glockenspiel', r'glock_medium_(?P<n>[A-G]#?\d)_01\.wav', 1, False, 3.0),
    ('chimes', 'Idiophones/Struck Idiophones/Tubular Bells 1', r'chimes_(?P<n>[A-G]#?\d)_f+_rr\d\.wav', 1, False, 5.0),
    ('harp', 'Chordophones/Composite Chordophones/Concert Harp', r'KSHarp_(?P<n>[A-G]#?\d)_mf\d\.wav', 4, False, 4.0),
    ('kalimba', 'Idiophones/Plucked Idiophones/Kalimba, Tanzania',
     r'MBira3_pluck_Main_(?P<n>[A-G]#?\d)_k\d+(?:alt)?_50_100_rr2\.wav', 3, False, 3.0),
    ('harpsichord', 'Chordophones/Zithers/Harpsichord, French/Sustains',
     r'Harpsi2_Normal_(?P<n>[A-G]#?\d)_rr1_Main\.wav', 4, False, 3.0),
    ('organ', 'Aerophones/Edge-blown Aerophones/Pipe Organ/Quiet', r'NT5_Man3Quiet_(?P<n>[A-G]#?\d)_rr1\.wav', 6, True, 3.0),
    ('recorder', 'Aerophones/Edge-blown Aerophones/Baroque Alto Recorder/Sustain',
     r'AltRecorder_Sus_(?P<n>[A-G]#?\d)_rr1_Main\.wav', 1, True, 3.0),
    ('sax', 'Aerophones/Reed Aerophones/Tenor Saxophone/Non-Vibrato',
     r'BrettTenor_NV_Main_(?P<n>[A-G]#?\d)_vl2_rr1\.wav', 4, True, 3.0),
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


def zone_strumento(nome, cartella, rx, passo, loop, max_s, fonti):
    """sceglie i file della cartella VCSL a passo di semitoni e prepara una zona per ciascuno"""
    albero = json.load(open(os.path.join(OUT, 'vcsl_tree.json'), encoding='utf-8'))
    disp = []
    for e in albero['tree']:
        if e['type'] != 'blob' or not e['path'].startswith(cartella + '/'):
            continue
        m = re.fullmatch(rx, e['path'].split('/')[-1])
        if m:
            disp.append((midi(m['n']), e['path']))
    disp.sort()
    if not disp:
        sys.exit(f'{nome}: nessun file in {cartella} con {rx}')
    scelti, ultimo = [], -999
    for n, p in disp:
        if n >= ultimo + passo:
            scelti.append((n, p))
            ultimo = n
    zone = []
    for k, (n, p) in enumerate(scelti):
        print(f'{nome}: nota {n} {p.split("/")[-1]}')
        x, fs = leggi(scarica(V, p))
        y, ls, le = prepara(x, fs, loop, max_s)
        lo = 0 if k == 0 else (scelti[k - 1][0] + n) // 2 + 1
        hi = 127 if k == len(scelti) - 1 else (n + scelti[k + 1][0]) // 2
        zone.append(dict(root=n, lo=lo, hi=hi, vel_lo=0, data=y, ls=ls, le=le))
        fonti.append((nome, url_of(V, p), 'VCSL, CC0'))
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
        for nome, cartella, rx, passo, loop, max_s in STRUMENTI:
            if solo_indice:
                sets.append((nome, 1 if loop else 0, [None] * 0))
                continue
            albero_vcsl()
            sets.append((nome, 1 if loop else 0, zone_strumento(nome, cartella, rx, passo, loop, max_s, fonti)))
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
    print(f'{path}: {len(sets)} set, {sum(len(z) for _, _, z in sets)} zone, {n * 2 / 1e6:.1f} MB, {n / FS:.0f} s di audio')


if __name__ == '__main__':
    main(sys.argv[1:])
