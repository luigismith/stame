"""pad.py — la configurazione del macro pad BRIMFORD (1189:8840) dal PC, con il protocollo del programma
del produttore (specifica 40, §8.10, MIDI-122 e VP-8).

Uso: python -I tools/pad.py info                         identifica il pad (03 fb fb fb), non cambia niente
     python -I tools/pad.py backup                       legge i tre strati (03 fa 0f 03 L) in private/pad/
     python -I tools/pad.py copia DA A [--manda]         copia su A le righe dello strato DA che sono diverse
     python -I tools/pad.py led STRATO COLORE MODO [--fine] [--manda]
     python -I tools/pad.py spegni STRATO [--manda]      LED spento e fine strato, come «LED Mode0» + Save

COLORE 1–7 (rosso, arancio, giallo, verde, ciano, blu, viola), MODO 0–5 (0 spento, 1 fisso). Senza
--manda stampa cosa farebbe e non scrive niente. --fine aggiunge la fine strato (03 fd fe ff), il
«salva» del programma del produttore. Ogni scrittura va nella flash del pad (VP-8, provato il
19/10/2026), anche il LED senza la fine strato: niente cicli.

Il pad si scrive solo con Luigi presente e con il suo ok. `copia` riscrive solo le righe lette dal pad
(come «Save settings» del programma del produttore) e poi le rilegge; lo strumento non sa costruire i
comandi pericolosi (modalità aggiornamento, cambio di modello). Serve il pacchetto hidapi (pip install
hidapi, accanto a numpy: `python -I` non vede i pacchetti installati con --user).
"""
import datetime
import os
import sys
import time

import hid

for flusso in (sys.stdout, sys.stderr):
    flusso.reconfigure(encoding='utf-8')

VID = (0x1189, 0x514C)
PID = (0x8840,)
RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLORI = ['', 'rosso', 'arancio', 'giallo', 'verde', 'ciano', 'blu', 'viola']


def apri():
    vie = [d for d in hid.enumerate() if d['vendor_id'] in VID and d['product_id'] in PID and d['interface_number'] == 0]
    if not vie:
        sys.exit('pad non trovato (1189:8840, interfaccia 0): è collegato al PC?')
    dev = hid.device()
    dev.open_path(vie[0]['path'])
    return dev


def pacchetto(*byte):
    return bytes([0x03, *byte] + [0] * (64 - len(byte)))


def manda(dev, p):
    print('  ->', p[:16].hex(' '))
    if dev.write(p) != len(p):
        sys.exit('scrittura non riuscita')


def risposte(dev, attesa_ms=60):
    out = []
    while True:
        r = dev.read(64, attesa_ms)
        if not r:
            return out
        out.append(bytes(r))


def identifica(dev):
    risposte(dev, 20)                     # svuota la coda
    manda(dev, pacchetto(0xFB, 0xFB, 0xFB))
    rr = risposte(dev, 100)
    if not rr:
        sys.exit('il pad non risponde a 03 fb fb fb: mi fermo')
    r = rr[0]
    print('  <-', r[:8].hex(' '))
    tasti, manopole, famiglia = r[2], r[3], r[4]
    print(f'tasti {tasti}, manopole {manopole}, famiglia 0x{famiglia:02x}')
    if (tasti, manopole) != (15, 3) or famiglia == 0x0A:
        sys.exit('non è il pad atteso (15 tasti, 3 manopole, famiglia classica): mi fermo')


def leggi_strato(dev, strato):
    """le 24 righe di uno strato (15 tasti, 3 manopole × 3 azioni), per indice 1–24"""
    manda(dev, pacchetto(0xFA, 0x0F, 0x03, strato))
    rr = risposte(dev, 150)
    righe = {r[2]: r for r in rr if r[1] == 0xFA and r[3] == strato}
    if sorted(righe) != list(range(1, 25)):
        sys.exit(f'strato {strato}: attese 24 righe, lette {len(rr)}: mi fermo')
    return righe


def backup(dev):
    cart = os.path.join(RADICE, 'private', 'pad')
    os.makedirs(cart, exist_ok=True)
    quando = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    tutto = []
    for strato in (1, 2, 3):
        righe = leggi_strato(dev, strato)
        print(f'strato {strato}: 24 righe')
        tutto += [righe[k] for k in sorted(righe)]
    with open(os.path.join(cart, f'strati_{quando}.bin'), 'wb') as f:
        f.write(b''.join(tutto))
    with open(os.path.join(cart, f'strati_{quando}.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(''.join(r.hex(' ') + '\n' for r in tutto))
    print('scritto', os.path.join(cart, f'strati_{quando}.bin'))


def descrivi(r):
    """tipo, numero di tasti, modificatore e codici di una riga, per leggerla"""
    return f'tipo {r[4]} mod {r[11]:02x} tasti ' + ' '.join(f'{c:02x}' for c in r[12:12 + max(r[10], 1)])


def copia(dev, da, a, davvero):
    """riscrive su A le righe dello strato DA che sono diverse (03 fd + la riga letta, con lo strato
    cambiato), poi la fine strato, e rilegge A per controllare"""
    sorgente, dest = leggi_strato(dev, da), leggi_strato(dev, a)
    diverse = [k for k in range(1, 25) if sorgente[k][4:51] != dest[k][4:51]]
    if not diverse:
        print(f'lo strato {a} è già uguale allo strato {da}: niente da scrivere')
        return
    for k in diverse:
        print(f'  riga {k:2d}: {descrivi(dest[k])}  ->  {descrivi(sorgente[k])}')
    if not davvero:
        print(f'{len(diverse)} righe da scrivere sullo strato {a}; aggiungi --manda per scriverle sul pad')
        return
    for k in diverse:
        r = bytearray(sorgente[k][2:51])
        r[1] = a
        manda(dev, pacchetto(0xFD, *r))
    manda(dev, pacchetto(0xFD, 0xFE, 0xFF))
    time.sleep(0.2)
    risposte(dev, 50)
    dopo = leggi_strato(dev, a)
    if all(dopo[k][4:51] == sorgente[k][4:51] for k in range(1, 25)):
        print(f'fatto: lo strato {a} ora è uguale allo strato {da}')
    else:
        sys.exit(f'ATTENZIONE: lo strato {a} riletto non è uguale allo strato {da}; il backup è in private/pad/')


def riga_led(strato, codice):
    return pacchetto(0xFE, 0xB0, strato, 0x08, 0, 0, 0, 0, 0, 0x01, 0x00, codice)


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ('info', 'backup', 'copia', 'led', 'spegni'):
        sys.exit(__doc__)
    davvero = '--manda' in a
    if a[0] == 'copia':
        da, verso = int(a[1]), int(a[2])
        if not (1 <= da <= 3 and 1 <= verso <= 3 and da != verso):
            sys.exit('due strati diversi, 1–3')
        dev = apri()
        try:
            identifica(dev)
            if davvero:
                backup(dev)
            copia(dev, da, verso, davvero)
        finally:
            dev.close()
        return
    if a[0] == 'led':
        strato, colore, modo = int(a[1]), int(a[2]), int(a[3])
        if not (1 <= strato <= 3 and 1 <= colore <= 7 and 0 <= modo <= 5):
            sys.exit('strato 1–3, colore 1–7, modo 0–5')
        righe = [riga_led(strato, colore << 4 | modo)] + ([pacchetto(0xFD, 0xFE, 0xFF)] if '--fine' in a else [])
        print(f'strato {strato}: {COLORI[colore]}, modo {modo}' + (', con la fine strato' if '--fine' in a else ', senza la fine strato'))
    elif a[0] == 'spegni':
        strato = int(a[1])
        if not 1 <= strato <= 3:
            sys.exit('strato 1–3')
        righe = [riga_led(strato, 0x50), pacchetto(0xFD, 0xFE, 0xFF)]
        print(f'strato {strato}: LED spento, con la fine strato')
    else:
        righe = []
    if righe and not davvero:
        for p in righe:
            print('  (non mandato)', p[:16].hex(' '))
        print('aggiungi --manda per scriverli sul pad')
        return
    dev = apri()
    try:
        identifica(dev)
        if a[0] == 'backup':
            backup(dev)
        for p in righe:
            manda(dev, p)
            if p[1] == 0xFD:
                time.sleep(0.2)
        if righe:
            print('mandato; il pad ha risposto:', [r[:6].hex(' ') for r in risposte(dev, 100)])
    finally:
        dev.close()


if __name__ == '__main__':
    main()
