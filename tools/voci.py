"""voci.py — i set di voci umane del banco di campioni (specifica 20, SND-378).

Nessuna libreria CC0 ha cori o voci campionati nota per nota, quindi le voci di Stame si sintetizzano
qui, fuori dal nucleo, e finiscono nel banco come gli altri set (tools/campioni.py le importa). Sono
nostre: nessun campione di terzi.

La sintesi è additiva a formanti. Ogni cantante è una serie di armoniche pesate da cinque formanti in
parallelo (frequenza, banda e ampiezza dalle tabelle classiche della sintesi del canto per basso, tenore,
contralto e soprano; `tilt` > 1 scurisce, `alti_db` regola il terzo, quarto e quinto formante), più il
fiato: rumore con gli stessi formanti, modulato dal ciclo glottale.
L'inviluppo si calcola sulla frequenza istantanea di ogni armonica, così il vibrato fa passare le armoniche
dentro e fuori dai formanti come in una voce vera. Ogni cantante ha la sua intonazione, il suo vibrato
(ritardato nel solista), un tremolio lento d'intonazione, di volume e di formanti, e la sua lunghezza di
tratto vocale; nel coro gli attacchi sono sfalsati di qualche decina di millisecondi.

Il loop è perfetto per costruzione: dopo l'attacco ogni modulazione è periodica sul loop di N campioni
(vibrato, tremolii e rumore con un numero intero di cicli in N) e la frequenza di ogni cantante è scalata
perché in N faccia un numero intero di periodi; il campione N + A è identico al campione A. N si sceglie
intorno a 2,4 s perché la nota della zona cada su un numero intero di cicli.

    python -I tools/voci.py <cartella>     un WAV d'ascolto per set (ogni zona in loop per 2 s)
"""
import math
import os
import sys
import zlib

import numpy as np

FS = 32000
LOOP_S = 2.4                         # durata del loop, circa
F_MAX = 7500.0                       # armoniche fino a qui

# formanti (Hz) e bande (Hz), cinque per vocale, dalle tabelle classiche della sintesi del canto
_T = {
    ('bass', 'a'): ((600, 1040, 2250, 2450, 2750), (60, 70, 110, 120, 130), (0, -7, -9, -9, -20)),
    ('bass', 'e'): ((400, 1620, 2400, 2800, 3100), (40, 80, 100, 120, 120), (0, -12, -9, -12, -18)),
    ('bass', 'i'): ((250, 1750, 2600, 3050, 3340), (60, 90, 100, 120, 120), (0, -30, -16, -22, -28)),
    ('bass', 'o'): ((400, 750, 2400, 2600, 2900), (40, 80, 100, 120, 120), (0, -11, -21, -20, -40)),
    ('bass', 'u'): ((350, 600, 2400, 2675, 2950), (40, 80, 100, 120, 120), (0, -20, -32, -28, -36)),
    ('tenor', 'a'): ((650, 1080, 2650, 2900, 3250), (80, 90, 120, 130, 140), (0, -6, -7, -8, -22)),
    ('tenor', 'e'): ((400, 1700, 2600, 3200, 3580), (70, 80, 100, 120, 120), (0, -14, -12, -14, -20)),
    ('tenor', 'i'): ((290, 1870, 2800, 3250, 3540), (40, 90, 100, 120, 120), (0, -15, -18, -20, -30)),
    ('tenor', 'o'): ((400, 800, 2600, 2800, 3000), (40, 80, 100, 120, 120), (0, -10, -12, -12, -26)),
    ('tenor', 'u'): ((350, 600, 2700, 2900, 3300), (40, 60, 100, 120, 120), (0, -20, -17, -14, -26)),
    ('alto', 'a'): ((800, 1150, 2800, 3500, 4950), (80, 90, 120, 130, 140), (0, -4, -20, -36, -60)),
    ('alto', 'e'): ((400, 1600, 2700, 3300, 4950), (60, 80, 120, 150, 200), (0, -24, -30, -35, -60)),
    ('alto', 'i'): ((350, 1700, 2700, 3700, 4950), (50, 100, 120, 150, 200), (0, -20, -30, -36, -60)),
    ('alto', 'o'): ((450, 800, 2830, 3500, 4950), (70, 80, 100, 130, 135), (0, -9, -16, -28, -55)),
    ('alto', 'u'): ((325, 700, 2530, 3500, 4950), (50, 60, 170, 180, 200), (0, -12, -30, -40, -64)),
    ('soprano', 'a'): ((800, 1150, 2900, 3900, 4950), (80, 90, 120, 130, 140), (0, -6, -32, -20, -50)),
    ('soprano', 'e'): ((350, 2000, 2800, 3600, 4950), (60, 100, 120, 150, 200), (0, -20, -15, -40, -56)),
    ('soprano', 'i'): ((270, 2140, 2950, 3900, 4950), (60, 90, 100, 120, 120), (0, -12, -26, -26, -44)),
    ('soprano', 'o'): ((450, 800, 2830, 3800, 4950), (70, 80, 100, 130, 135), (0, -11, -22, -22, -50)),
    ('soprano', 'u'): ((325, 700, 2700, 3800, 4950), (50, 60, 170, 180, 200), (0, -16, -35, -40, -60)),
}
# la bocca chiusa (/m/): il mormorio nasale, un polo forte in basso, poco sopra, e lo zero della bocca chiusa
_M = {'male': ((270, 1050, 2150, 2750, 3400), (60, 160, 220, 260, 300), (0, -22, -28, -30, -36)),
      'female': ((310, 1200, 2450, 3100, 3900), (70, 180, 240, 280, 320), (0, -22, -28, -30, -36))}
ZERO_M = (850.0, 140.0)

# registri: la nota (MIDI) dove canta meglio ogni tipo di voce, per interpolare i formanti fra le zone
REG = {'bass': 43, 'tenor': 54, 'alto': 62, 'soprano': 71}
CORO = ('bass', 'tenor', 'alto', 'soprano')
DONNA = ('alto', 'soprano')
UOMO = ('bass', 'tenor')


def _vocale(tipo, vocale):
    """(log F, log B, dB) di una vocale semplice ('a') o di una miscela ('ou' = metà o, metà u)"""
    if tipo in ('male', 'female'):
        F, B, A = _M[tipo]
        return np.log(np.array(F, float)), np.log(np.array(B, float)), np.array(A, float)
    F, B, A = np.zeros(5), np.zeros(5), np.zeros(5)
    for v in vocale:
        f, b, a = _T[(tipo, v)]
        F += np.log(np.array(f, float)) / len(vocale)
        B += np.log(np.array(b, float)) / len(vocale)
        A += np.array(a, float) / len(vocale)
    return F, B, A


def formanti(nota, tipi, vocale):
    """formanti, bande e ampiezze (dB) per una nota: interpolati fra i due tipi di voce del registro
    (frequenze e bande in logaritmo, ampiezze in dB)"""
    if vocale == 'm':
        F, B, A = _vocale('female' if tipi[-1] in ('alto', 'soprano') else 'male', '')
        return np.exp(F), np.exp(B), A
    regs = [(REG[t], t) for t in tipi]
    if nota <= regs[0][0]:
        F, B, A = _vocale(regs[0][1], vocale)
    elif nota >= regs[-1][0]:
        F, B, A = _vocale(regs[-1][1], vocale)
    else:
        for (n0, t0), (n1, t1) in zip(regs, regs[1:]):
            if n0 <= nota <= n1:
                w = (nota - n0) / (n1 - n0)
                x0, x1 = _vocale(t0, vocale), _vocale(t1, vocale)
                F, B, A = (u * (1 - w) + v * w for u, v in zip(x0, x1))
                break
    return np.exp(F), np.exp(B), A


def risposta(f, F, B, A, scala, zero=None):
    """modulo dei cinque formanti in parallelo alla frequenza f (vettore): ogni risonatore vale 1 sul suo
    picco, scalato dalla sua ampiezza; `scala` è il vettore della lunghezza del tratto vocale nel tempo
    (moltiplica tutti i formanti). Sotto il primo formante resta il suo pavimento (B/F), che porta la
    fondamentale; sopra il quinto cala di 12 dB per ottava."""
    g = np.zeros_like(f)
    f2 = f * f
    for Fk, Bk, Ak in zip(F, B, A):
        Fs = Fk * scala
        g += 10 ** (Ak / 20) * Fs * Bk / np.sqrt((Fs * Fs - f2) ** 2 + (Bk * f) ** 2)
    if zero is not None:                         # la tacca: uno zero e un polo largo alla stessa frequenza
        Fz, Bz = zero[0] * scala, zero[1]
        g *= np.sqrt(((Fz * Fz - f2) ** 2 + (Bz * f) ** 2) / ((Fz * Fz - f2) ** 2 + (1.5 * Fz * f) ** 2))
    return g / np.sqrt(1.0 + (f / 6500.0) ** 8)


def periodico(rng, N, T, componenti, rms):
    """modulazione lenta periodica su N campioni, valutata sui primi T campioni: somma di sinusoidi con
    1…componenti cicli in N (≈ 0,4…3 Hz), ampiezza 1/j, scalata al valore efficace `rms`"""
    n = np.arange(T) % N
    x = np.zeros(T)
    for j in range(1, componenti + 1):
        x += np.sin(2 * np.pi * j * n / N + rng.uniform(0, 2 * np.pi)) / j
    s = np.sqrt(np.mean(x[:N] ** 2)) if T >= N else 1.0
    return x * (rms / max(s, 1e-12))


def scegli_N(f0):
    """il loop: intorno a LOOP_S, con la nota della zona più vicina a un numero intero di cicli"""
    lo, hi = int(LOOP_S * 0.9 * FS), int(LOOP_S * 1.1 * FS)
    Ns = np.arange(lo, hi)
    c = f0 * Ns / FS
    return int(Ns[np.argmin(np.abs(c - np.round(c)))])


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def cantante(rng, f0, k, N, A, T, F, B, Adb, p, zero):
    """un cantante: T campioni, periodico di N dopo A. k = numero di cicli nel loop."""
    n = np.arange(T)
    t = n / FS
    nm = n % N
    # intonazione: vibrato con un numero intero di cicli in N, più il tremolio lento
    vr = rng.uniform(*p['vib_rate'])
    vr = max(1, round(vr * N / FS)) * FS / N
    vd = rng.uniform(*p['vib_cents'])
    cents = vd * np.sin(2 * np.pi * vr * nm / FS + rng.uniform(0, 2 * np.pi))
    cents += periodico(rng, N, T, 7, p['jitter_cents'])
    # l'attacco: il vibrato entra dopo, la nota arriva da sotto
    ritardo = rng.uniform(0.0, p['smear'])
    att = p['attack'] * rng.uniform(0.8, 1.2)
    rampa = smoothstep((t - ritardo - p['vib_delay']) / max(A / FS - ritardo - p['vib_delay'], 1e-3))
    cents_att = cents * rampa + p['scoop'] * np.exp(-np.maximum(t - ritardo, 0) / 0.07) * (n < A)
    # la frequenza nel loop fa esattamente k cicli in N
    fper = 2.0 ** (cents[:N] / 1200.0)
    fb = k * FS / np.sum(fper)
    f = fb * fper[nm]
    f[:A] = fb * 2.0 ** (cents_att[:A] / 1200.0)
    fase = 2 * np.pi * np.concatenate([[0.0], np.cumsum(f[:-1])]) / FS
    # tratto vocale: la lunghezza del cantante e il suo lento muoversi
    scala = rng.uniform(*p['tratto']) * (1.0 + periodico(rng, N, T, 5, p['formant_drift']))
    F = F.copy()
    F[0] = max(F[0], 1.12 * f0)                       # i soprani alzano il primo formante sopra la nota
    F[1] = max(F[1], 1.35 * F[0])
    voce = np.zeros(T)
    H = int(F_MAX / f0)
    tilt = p['tilt']
    for h in range(1, H + 1):
        fh = h * f
        a = risposta(fh, F, B, Adb, scala, zero) * h ** (1.0 - tilt)
        if a.max() < 1e-5:
            continue
        voce += a * np.sin(h * fase + rng.uniform(0, 2 * np.pi))
    # il fiato: rumore periodico su N con i formanti (più larghi), modulato dal ciclo glottale
    if p['fiato'] > 0:
        frq = np.fft.rfftfreq(N, 1.0 / FS)
        frq[0] = 1.0
        mag = risposta(frq, F, B * p['fiato_banda'], Adb, np.ones_like(frq) * np.mean(scala), zero)
        mag *= np.minimum(1.0, (frq / 400.0) ** 2)    # niente rombo sotto la voce
        spec = mag * np.exp(1j * rng.uniform(0, 2 * np.pi, len(frq)))
        spec[0] = 0
        rumore = np.fft.irfft(spec, N)
        rumore /= np.sqrt(np.mean(rumore ** 2)) + 1e-12
        glott = 0.35 + 0.65 * (0.5 + 0.5 * np.cos(fase)) ** 2
        rv = np.sqrt(np.mean(voce[A:A + N] ** 2)) if T >= A + N else np.sqrt(np.mean(voce ** 2))
        voce += p['fiato'] * rv * rumore[nm] * glott
    # volume: il tremolio lento e l'attacco
    vol = 10 ** (periodico(rng, N, T, 4, p['amp_db']) / 20.0)
    vol *= np.where(n < A, smoothstep((t - ritardo) / att), 1.0)
    return voce * vol * rng.uniform(0.8, 1.0)


# ---- i set: nome, note delle zone, tipi di voce del registro, vocale, cantanti, parametri ----
BASE = dict(vib_rate=(4.8, 5.8), vib_cents=(8, 20), vib_delay=0.0, jitter_cents=4.0, smear=0.06, attack=0.16,
            scoop=0.0, tratto=(0.96, 1.04), formant_drift=0.012, tilt=1.0, fiato=0.08, fiato_banda=1.6,
            amp_db=0.7, detune=12.0, alti_db=-7.0)
VOCI = [
    # il coro misto sulla «a»: bassi in fondo, soprani in cima
    ('choir_aah', range(36, 85, 4), CORO, 'a', 8, dict()),
    # il coro sulla «u» scura, più morbido
    ('choir_ooh', range(36, 85, 4), CORO, 'ou', 8, dict(tilt=1.25, vib_cents=(6, 15), fiato=0.06, attack=0.22)),
    # a bocca chiusa
    ('choir_hum', range(36, 85, 4), CORO, 'm', 6, dict(tilt=1.2, vib_cents=(4, 10), fiato=0.03, attack=0.2,
                                                         detune=8.0)),
    # il coro di fiato: poca voce e molto respiro, formanti larghi
    ('choir_breath', range(36, 85, 6), CORO, 'ao', 6, dict(tilt=1.1, vib_cents=(3, 8), fiato=2.5, fiato_banda=2.2,
                                                            attack=0.3, smear=0.1, detune=8.0)),
    # le voci bianche: dritte, chiare, sulla «u»; tratto vocale corto
    ('choir_kids', range(57, 85, 4), ('soprano',), 'uo', 6, dict(vib_cents=(1.5, 5), detune=7.0, tilt=1.1,
                                                                   tratto=(1.10, 1.18), fiato=0.10)),
    # la voce di donna, solista, sulla «a»: vibrato che entra dopo, la nota che arriva da sotto
    ('voice_female', range(55, 85, 3), DONNA, 'a', 1, dict(vib_rate=(5.4, 5.6), vib_cents=(32, 34), vib_delay=0.15,
                                                            jitter_cents=3.0, scoop=-45.0, attack=0.12, smear=0.0,
                                                            tilt=0.9, fiato=0.12, tratto=(1.0, 1.0), detune=0.0)),
    # la voce d'uomo, solista, sulla «o» aperta
    ('voice_male', range(40, 68, 3), UOMO, 'oa', 1, dict(vib_rate=(5.1, 5.3), vib_cents=(26, 28), vib_delay=0.15,
                                                         jitter_cents=3.0, scoop=-40.0, attack=0.12, smear=0.0,
                                                         tilt=0.95, fiato=0.10, tratto=(1.0, 1.0), detune=0.0,
                                                         alti_db=-9.0)),
]


def zona(nome, nota, tipi, vocale, quanti, par):
    """una zona: (int16, loop_start, loop_end); il loop è [A, A + N), con 2 campioni oltre la fine"""
    p = dict(BASE, **par)
    rng = np.random.default_rng(zlib.crc32(f'{nome}/{nota}'.encode()))
    f0 = 440.0 * 2 ** ((nota - 69) / 12)
    N = scegli_N(f0)
    A = int((p['smear'] + 1.25 * p['attack'] + p['vib_delay'] + 0.05) * FS)
    T = A + N + 2
    F, B, Adb = formanti(nota, tipi, vocale)
    Adb = Adb + np.array([0, 0, 1, 1, 1]) * p['alti_db']
    zero = ZERO_M if vocale == 'm' else None
    k0 = int(round(f0 * N / FS))
    # stonature simmetriche, a cicli interi nel loop: la media resta la nota
    det = []
    for i in range(quanti // 2):
        c = p['detune'] * (i + 1) / max(quanti // 2, 1) * rng.uniform(0.7, 1.0)
        det += [c, -c]
    det += [0.0] * (quanti - len(det))
    out = np.zeros(T)
    for c in det:
        k = k0 + int(round(k0 * (2 ** (c / 1200) - 1)))
        out += cantante(rng, f0, k, N, A, T, F, B, Adb, p, zero)
    out -= np.mean(out[A:A + N])
    out *= 0.891 / max(np.abs(out).max(), 1e-9)     # −1 dBFS, come gli altri set
    y = np.clip(np.round(out * 32767.0), -32768, 32767).astype('<i2')
    return y, A, A + N


def zone_set(nome, note, tipi, vocale, quanti, par):
    """le zone di un set nel formato di campioni.py, con i confini a metà fra due note"""
    note = list(note)
    zone = []
    for i, m in enumerate(note):
        y, ls, le = zona(nome, m, tipi, vocale, quanti, par)
        lo = 0 if i == 0 else (note[i - 1] + m) // 2 + 1
        hi = 127 if i == len(note) - 1 else (m + note[i + 1]) // 2
        zone.append(dict(root=m, lo=lo, hi=hi, vel_lo=0, data=y, ls=ls, le=le))
        print(f'{nome}: nota {m}, loop {(le - ls) / FS:.2f} s, attacco {ls / FS:.2f} s')
    return zone


def scrivi_wav(path, x):
    import soundfile as sf
    sf.write(path, x, FS, subtype='PCM_16')


def ascolto(cartella):
    """per ogni set: ogni zona suonata 2,5 s (attacco e loop), con 0,2 s di silenzio fra le zone"""
    os.makedirs(cartella, exist_ok=True)
    for nome, note, tipi, vocale, quanti, par in VOCI:
        pezzi = []
        for z in zone_set(nome, note, tipi, vocale, quanti, par):
            y = z['data'].astype(float) / 32768.0
            ls, le = z['ls'], z['le']
            dur = int(2.5 * FS)
            idx = np.arange(dur)
            idx = np.where(idx < le, idx, ls + (idx - ls) % (le - ls))
            seg = y[idx]
            seg[-int(0.15 * FS):] *= np.linspace(1, 0, int(0.15 * FS))
            pezzi += [seg, np.zeros(int(0.2 * FS))]
        scrivi_wav(os.path.join(cartella, nome + '.wav'), np.concatenate(pezzi))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    ascolto(sys.argv[1])
