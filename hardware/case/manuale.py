"""manuale.py — i documenti del case: progetti di taglio e istruzioni di montaggio, in PDF.

Uso: python -I hardware/case/manuale.py      (dopo genera.py e assieme.py)

Usa la suite ArtCraft: VectorCraft converte le pagine SVG in PDF vettoriali, PdfCraft le unisce e
mette il titolo. Escono out/taglio/progetti_di_taglio.pdf (i fogli 1:1, da mandare al laser o da
stampare per controllo, e la dima) e out/istruzioni_montaggio.pdf (copertina con i pezzi e la
minuteria, un passo per pagina, le misure da verificare).
"""
import base64
import os
import subprocess
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import genera as G                   # noqa: E402
import assieme as A                  # noqa: E402
import misure as M                   # noqa: E402

VC = r'C:\Program Files\VectorCraft\vectorcraft-cli.exe'
PC = r'C:\Program Files\PdfCraft\pdfcraft-cli.exe'
OUT = G.OUT
PAG = os.path.join(OUT, 'montaggio', 'pagine')
W, H = 297.0, 210.0                                         # A4 orizzontale, mm
FONT = "Bahnschrift, 'Segoe UI', Arial, sans-serif"


def esegui(*args):
    r = subprocess.run(list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f'{os.path.basename(args[0])}: {r.stderr or r.stdout}')


def svg_pdf(svg, pdf):
    esegui(VC, 'convert', svg, pdf)


def unisci(pdfs, out, titolo):
    tmp = out + '.tmp.pdf'
    esegui(PC, 'combine', *pdfs, '--out', tmp)
    esegui(PC, 'edit', tmp, '--out', out, '--title', titolo, '--author', 'Stame')
    os.remove(tmp)


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def testo(x, y, righe, size=4.2, peso=400, colore='#222', interlinea=1.45):
    out = []
    for i, r in enumerate(righe):
        out.append(f'<text x="{x}" y="{y + i * size * interlinea:.2f}" font-family="{FONT}" font-size="{size}" '
                   f'font-weight="{peso}" fill="{colore}">{esc(r)}</text>')
    return '\n'.join(out)


def a_capo(s, n):
    righe, riga = [], ''
    for p in s.split():
        if len(riga) + len(p) + 1 > n:
            righe.append(riga)
            riga = p
        else:
            riga = (riga + ' ' + p).strip()
    righe.append(riga)
    return righe


def immagine(png, x, y, w, h):
    dati = base64.b64encode(open(png, 'rb').read()).decode()
    return f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{dati}"/>'


def pagina(nome, corpo, n, tot):
    p = os.path.join(PAG, nome + '.svg')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">\n')
        f.write(f'<rect width="{W}" height="{H}" fill="#F6F4EE"/>\n{corpo}\n')
        f.write(testo(14, H - 8, [f'Stame · la console, bozza 5 · {n}/{tot}'], 3.2, 400, '#777'))
        f.write('\n</svg>\n')
    return p


def ritaglia(png):
    """la tavola senza il titolo disegnato nell'immagine (le pagine hanno il loro)"""
    from PIL import Image
    im = Image.open(png)
    out = os.path.join(PAG, os.path.basename(png))
    im.crop((0, 150, im.width, im.height)).save(out)
    return out


def elenco_pezzi():
    righe = []
    for mat, nome in G.MATERIALI.items():
        pezzi = [(p['nome'], p['quanti']) for p in G.LASER if p['materiale'] == mat]
        righe.append(f'{nome}: ' + ', '.join(f'{n} ×{q}' if q > 1 else n for n, q in pezzi))
    stampati = ', '.join(f'{s["nome"]} ×{s["quanti"]}' if s['quanti'] > 1 else s['nome'] for s in G.STAMPATI)
    righe.append(f'stampa 3D (PETG): {stampati}')
    return righe


MINUTERIA = [
    'viti M3 × 10 svasate e dadi M3: 4 per la culla della Flip, sotto la Flip',
    'viti M3 × 10 e dadi M3: 2 per la visiera, 6 per le squadrette nella base',
    'viti da legno 3 × 12: 6 per le squadrette nei fianchi, 2 per il fermo dell\'hub',
    'colla vinilica (legno); feltro adesivo da 1 mm in strisce sugli appoggi del piano',
    '6 piedini in gomma da 12 mm sotto la base',
    'hub USB 2.0 senza Power Delivery; cavi USB-C a 90° per la MK4 e per il pad; cavi corti',
]

VERIFICARE = [
    'MK4: dima su carta (controlli dalle foto, ±1 mm); altezza del pannello (37 mm) e dei pulsanti piccoli',
    'Macro pad: altezza del corpo (16 mm stimati) e quota della presa USB-C, prima di stampare la culla',
    'Flip: angolo massimo dello schermo (serve 115°: schermo a 65°); porte e tasti presi dalle foto',
    'Hub: misure reali (fermo dell\'hub) e consumo di MK4 + pad dalla batteria della Flip',
    'Prova di taglio su un ritaglio: potenza, velocità e gioco delle linguette (0,2 mm per lato)',
]


def istruzioni():
    os.makedirs(PAG, exist_ok=True)
    for n in os.listdir(PAG):
        os.remove(os.path.join(PAG, n))
    tavole = os.path.join(OUT, 'montaggio')
    passi = list(A.PASSI.items())
    tot = len(passi) + 2
    pagine = []
    # copertina
    corpo = [testo(14, 22, ['Stame — la console'], 11, 700, '#141B18'),
             testo(14, 31, ['Istruzioni di montaggio · bozza 5, 18/10/2026 · MPK mini IV, macro pad, Miyoo Flip'], 4.4, 400, '#555'),
             immagine(ritaglia(os.path.join(tavole, 'console.png')), 120, 36, 170, 110),
             testo(14, 46, ['I pezzi'], 5.2, 700)]
    y = 54
    for r in elenco_pezzi():
        for rr in a_capo(r, 52):
            corpo.append(testo(14, y, [rr], 3.4))
            y += 4.9
        y += 1.5
    corpo.append(testo(14, y + 4, ['Minuteria'], 5.2, 700))
    y += 12
    for r in MINUTERIA:
        for rr in a_capo('· ' + r, 52):
            corpo.append(testo(14, y, [rr], 3.4))
            y += 4.9
    corpo.append(testo(120, 160, a_capo('Prima di tagliare: la dima della mascherina su carta al 100% e le misure '
                                        'dell\'ultima pagina. Ingombro ' f'{M.LARGHEZZA:.0f} × {M.BASE_Y1:.0f} mm; '
                                        'altezza 133 mm con lo schermo aperto, 150 con la visiera.', 80), 3.6, 400, '#444'))
    pagine.append(pagina('00_copertina', '\n'.join(corpo), 1, tot))
    # un passo per pagina
    for i, (k, (tit, txt)) in enumerate(passi, 2):
        corpo = [testo(14, 22, [f'{k}. {tit}'], 10, 700, '#141B18'),
                 testo(14, 32, a_capo(txt, 130), 4.4, 400, '#333'),
                 immagine(ritaglia(os.path.join(tavole, f'passo_{k}.png')), 14, 44, W - 28, H - 58),
                 testo(W - 80, 22, ['in ambra: i pezzi di questo passo'], 3.4, 400, '#B86A00')]
        pagine.append(pagina(f'{k:02d}_passo', '\n'.join(corpo), i, tot))
    # misure da verificare
    corpo = [testo(14, 22, ['Da verificare prima di tagliare'], 10, 700, '#141B18')]
    y = 36
    for r in VERIFICARE:
        corpo.append(testo(14, y, ['· ' + r], 4.4))
        y += 8
    corpo.append(testo(14, y + 6, a_capo('Tutte le misure stanno in hardware/case/misure.py, ognuna con la sua fonte. '
                                         'Cambiata una misura: python -I hardware/case/genera.py, poi assieme.py e '
                                         'manuale.py rifanno pezzi, modello e documenti.', 120), 4.0, 400, '#555'))
    corpo.append(immagine(ritaglia(os.path.join(tavole, 'console_retro.png')), 150, 90, 140, 100))
    pagine.append(pagina('99_verifiche', '\n'.join(corpo), tot, tot))
    pdfs = []
    for p in pagine:
        pdf = p[:-4] + '.pdf'
        svg_pdf(p, pdf)
        pdfs.append(pdf)
    out = os.path.join(OUT, 'istruzioni_montaggio.pdf')
    unisci(pdfs, out, 'Stame — istruzioni di montaggio della console')
    return out


def taglio():
    cart = os.path.join(OUT, 'taglio')
    svgs = sorted(n for n in os.listdir(cart) if n.startswith('taglio_') and n.endswith('.svg'))
    pdfs = []
    for n in svgs + ['../dima_mascherina.svg']:
        src = os.path.join(cart, n)
        pdf = os.path.join(cart, os.path.basename(n)[:-4] + '.pdf')
        svg_pdf(src, pdf)
        pdfs.append(pdf)
    out = os.path.join(cart, 'progetti_di_taglio.pdf')
    unisci(pdfs, out, 'Stame — progetti di taglio della console (1:1, mm)')
    for p in pdfs:
        if 'dima' not in p:
            os.remove(p)
    return out


def main():
    G.genera()
    print(taglio())
    print(istruzioni())


if __name__ == '__main__':
    main()
