"""midi_ascolta.py — registra il MIDI di una tastiera su tutte le sue porte (Windows, winmm).

Serve alle catture prima di scrivere un profilo (specifica 40: «prima di scrivere la mappa, catturare
il traffico reale su tutte le porte»). Aspetta che compaia un ingresso il cui nome contiene il filtro,
apre tutte le porte che lo contengono e scrive ogni messaggio con l'istante e la porta.

    python -I tools/midi_ascolta.py [secondi] [file.jsonl] [filtro]      (filtro di default: MPK)
"""
import ctypes
import ctypes.wintypes as wt
import json
import sys
import time

DURATA = float(sys.argv[1]) if len(sys.argv) > 1 else 300.0
USCITA = sys.argv[2] if len(sys.argv) > 2 else None
FILTRO = (sys.argv[3] if len(sys.argv) > 3 else 'MPK').upper()

winmm = ctypes.WinDLL('winmm')
CALLBACK_FUNCTION = 0x30000
MIM_DATA, MIM_LONGDATA = 0x3C3, 0x3C4


class MIDIINCAPSW(ctypes.Structure):
    _fields_ = [('wMid', wt.WORD), ('wPid', wt.WORD), ('vDriverVersion', wt.UINT),
                ('szPname', wt.WCHAR * 32), ('dwSupport', wt.DWORD)]


class MIDIHDR(ctypes.Structure):
    pass


MIDIHDR._fields_ = [('lpData', ctypes.c_void_p), ('dwBufferLength', wt.DWORD), ('dwBytesRecorded', wt.DWORD),
                    ('dwUser', ctypes.c_size_t), ('dwFlags', wt.DWORD), ('lpNext', ctypes.c_void_p),
                    ('reserved', ctypes.c_size_t), ('dwOffset', wt.DWORD), ('dwReserved', ctypes.c_size_t * 8)]

MIDIINPROC = ctypes.WINFUNCTYPE(None, wt.HANDLE, wt.UINT, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t)
winmm.midiInOpen.argtypes = [ctypes.POINTER(wt.HANDLE), wt.UINT, ctypes.c_void_p, ctypes.c_size_t, wt.DWORD]
winmm.midiInGetDevCapsW.argtypes = [ctypes.c_size_t, ctypes.POINTER(MIDIINCAPSW), wt.UINT]
winmm.midiInStart.argtypes = [wt.HANDLE]
winmm.midiInStop.argtypes = [wt.HANDLE]
winmm.midiInClose.argtypes = [wt.HANDLE]
winmm.midiInReset.argtypes = [wt.HANDLE]
winmm.midiInPrepareHeader.argtypes = [wt.HANDLE, ctypes.POINTER(MIDIHDR), wt.UINT]
winmm.midiInAddBuffer.argtypes = [wt.HANDLE, ctypes.POINTER(MIDIHDR), wt.UINT]

t0 = time.monotonic()
righe = []
porte = {}            # handle -> nome
tenuti = []           # oggetti da tenere in vita (callback, buffer)


def nome_stato(st):
    t = st & 0xF0
    return {0x80: 'NoteOff', 0x90: 'NoteOn', 0xA0: 'PolyAT', 0xB0: 'CC', 0xC0: 'PC', 0xD0: 'ChanAT',
            0xE0: 'Bend'}.get(t, 'sys')


coda = []             # (istante, handle, msg, p1): il callback solo accoda, il resto lo fa il thread principale


@MIDIINPROC
def ricevi(h, msg, inst, p1, p2):
    # nel callback niente funzioni di winmm né stampa (la documentazione lo vieta): solo la coda
    if msg in (MIM_DATA, MIM_LONGDATA):
        coda.append((time.monotonic(), h, msg, p1))


def svuota():
    while coda:
        tm, h, msg, p1 = coda.pop(0)
        t = round(tm - t0, 3)
        porta = porte.get(h, '?')
        if msg == MIM_DATA:
            st, d1, d2 = p1 & 0xFF, (p1 >> 8) & 0xFF, (p1 >> 16) & 0xFF
            if st in (0xFE, 0xF8):
                continue                                  # active sensing e clock: non servono qui
            r = {'t': t, 'porta': porta, 'byte': '%02X %02X %02X' % (st, d1, d2)}
            righe.append(r)
            print('%8.3f  %-28s %s  %-7s ch%-2d %3d %3d' % (t, porta, r['byte'], nome_stato(st), (st & 15) + 1, d1, d2),
                  flush=True)
        else:
            hdr = ctypes.cast(p1, ctypes.POINTER(MIDIHDR))
            n = hdr.contents.dwBytesRecorded
            if n:
                r = {'t': t, 'porta': porta, 'byte': ctypes.string_at(hdr.contents.lpData, n).hex(' ').upper()}
                righe.append(r)
                print('%8.3f  %-28s SysEx %s' % (t, porta, r['byte'][:120]), flush=True)
            winmm.midiInAddBuffer(h, hdr, ctypes.sizeof(MIDIHDR))      # il buffer torna al driver


def elenco():
    out = []
    for i in range(winmm.midiInGetNumDevs()):
        caps = MIDIINCAPSW()
        if winmm.midiInGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
            out.append((i, caps.szPname))
    return out


def apri(i, nome):
    h = wt.HANDLE()
    if winmm.midiInOpen(ctypes.byref(h), i, ctypes.cast(ricevi, ctypes.c_void_p), 0, CALLBACK_FUNCTION) != 0:
        print('non apro %s' % nome)
        return
    porte[h.value] = nome
    for _ in range(4):                               # buffer per i SysEx
        buf = ctypes.create_string_buffer(1024)
        hdr = MIDIHDR()
        hdr.lpData = ctypes.cast(buf, ctypes.c_void_p)
        hdr.dwBufferLength = 1024
        winmm.midiInPrepareHeader(h, ctypes.byref(hdr), ctypes.sizeof(hdr))
        winmm.midiInAddBuffer(h, ctypes.byref(hdr), ctypes.sizeof(hdr))
        tenuti.append((buf, hdr))
    winmm.midiInStart(h)
    tenuti.append(h)
    print('aperta: %s' % nome, flush=True)


def main():
    global t0
    print('ingressi MIDI ora: %s' % ', '.join(n for _, n in elenco()) or '(nessuno)', flush=True)
    print('aspetto un ingresso che contenga «%s»…' % FILTRO, flush=True)
    while True:
        trovati = [(i, n) for i, n in elenco() if FILTRO in n.upper()]
        if trovati:
            break
        time.sleep(1.0)
    time.sleep(1.0)                                   # tutte le porte del dispositivo
    trovati = [(i, n) for i, n in elenco() if FILTRO in n.upper()]
    for i, n in trovati:
        apri(i, n)
    t0 = time.monotonic()
    print('in ascolto per %.0f s' % DURATA, flush=True)
    while time.monotonic() - t0 < DURATA:
        svuota()
        time.sleep(0.01)
    svuota()
    for h in list(porte):
        winmm.midiInStop(h)
        winmm.midiInReset(h)
        winmm.midiInClose(h)
    if USCITA:
        with open(USCITA, 'w', encoding='utf-8') as f:
            for r in righe:
                f.write(json.dumps(r) + '\n')
    print('fine: %d messaggi' % len(righe), flush=True)


if __name__ == '__main__':
    main()
