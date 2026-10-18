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
    'Macro pad (dalle foto del 18/10): corpo 11,5 mm, USB-C sul retro a 80 mm dal bordo dei tasti e 9 dal fondo, prima di stampare la culla',
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


MINUTERIA_STAMPA = [
    'viti M3 × 10 svasate e dadi M3: 4 per la culla della Flip, sotto la Flip',
    'viti M3 × 10 e dadi M3: 2 per la visiera, 6 per le squadrette nella base',
    'viti autofilettanti per plastica 3 × 12 (o M3 con inserti a caldo): 6 per le squadrette nei fianchi, 2 per il fermo dell\'hub',
    'colla cianoacrilica in gel o epossidica bicomponente, per i tasselli e le linguette',
    'feltro adesivo da 1 mm in strisce sugli appoggi del piano; 6 piedini in gomma da 12 mm sotto la base',
    'carta adesiva (o vinile da stampa) A4 per le etichette; taglierino e righello',
    'hub USB 2.0 senza Power Delivery; cavi USB-C a 90° per la MK4 e per il pad; cavi corti',
]


def _pagina_in(cartella, nome, corpo, n, tot, piede):
    p = os.path.join(cartella, nome + '.svg')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">\n')
        f.write(f'<rect width="{W}" height="{H}" fill="#F6F4EE"/>\n{corpo}\n')
        f.write(testo(14, H - 8, [f'{piede} · {n}/{tot}'], 3.2, 400, '#777'))
        f.write('\n</svg>\n')
    return p


def _elenco(x, y, righe, larghezza, size=3.4, passo=4.9, punto='· '):
    out = []
    for r in righe:
        for i, rr in enumerate(a_capo(punto + r, larghezza)):
            out.append(testo(x + (0 if i == 0 else 2.2), y, [rr], size))
            y += passo
    return out, y


def istruzioni_stampa3d():
    """out/stampa3d/istruzioni_stampa3d.pdf (i pezzi, i tasselli, le scritte e il montaggio) ed
    etichette_mascherina.pdf (le etichette 1:1 e dove vanno)"""
    import stampa3d as S
    righe, totale, _ = S.genera()
    cart = S.OUT3D
    pag = os.path.join(cart, 'pagine')
    os.makedirs(pag, exist_ok=True)
    for n in os.listdir(pag):
        os.remove(os.path.join(pag, n))
    piatto = M.PIATTO_COMUNE[0]
    piede = 'Stame · la console tutta stampata, bozza 5'
    tot = 3
    pagine = []
    # 1: i pezzi
    telaio = sum(r['grammi'] for r in righe if r['colore'] == 'telaio')
    corpo = [testo(14, 22, ['Stame — la console tutta stampata'], 11, 700, '#141B18'),
             testo(14, 31, [f'Per chi non ha il laser · bozza 5, 18/10/2026 · piatto da {piatto:.0f} × {piatto:.0f} mm '
                            '(stampanti da 220 in su)'], 4.4, 400, '#555'),
             immagine(ritaglia_in(os.path.join(cart, 'console_stampata.png'), pag), 150, 34, 138, 90),
             testo(14, 44, ['I pezzi'], 5.2, 700)]
    y = 51
    for r in righe:
        dx, dy, dz = r['dim']
        q = f' ×{r["quanti"]}' if r['quanti'] > 1 else ''
        rot = f', ruotato di {r["angolo"]}°' if r['angolo'] else ''
        corpo.append(testo(14, y, [f'{r["nome"]}.stl{q}'], 3.2, 700))
        corpo.append(testo(52, y, [f'{dx:.0f} × {dy:.0f} × {dz:.0f} mm{rot}'], 3.2))
        y += 4.5
    corpo.append(testo(14, y + 3, a_capo(f'Filamento: circa {virgola(totale / 1000)} kg, di cui {virgola(telaio / 1000)} kg per '
                                         'il telaio (color legno o sabbia) e il resto in nero.', 62), 3.4, 400, '#333'))
    corpo.append(testo(150, 134, ['Impostazioni'], 5.2, 700))
    el, yy = _elenco(150, 141, [
        'PETG o PLA, ugello 0,4, strati da 0,2; 3 perimetri, 4 strati pieni sopra e sotto, riempimento giroide al 20 %.',
        'Ogni file esce nel verso giusto, con la faccia in vista in alto; i pezzi lunghi sono già ruotati in diagonale.',
        'Senza supporti, tranne la visiera (si stampa sul tettuccio).',
        'Prima un tassello di prova: le code di rondine devono entrare a mano, con 0,15 mm di gioco per lato.'], 70, 3.3, 4.6)
    corpo += el
    pagine.append(_pagina_in(pag, '01_pezzi', '\n'.join(corpo), 1, tot, piede))
    # 2: i tasselli
    png = os.path.join(pag, 'tasselli.png')
    svg_png(os.path.join(cart, 'tasselli.svg'), png)
    corpo = [testo(14, 22, ['I tasselli'], 10, 700, '#141B18'),
             testo(14, 31, a_capo('Quello che non sta sul piatto si stampa in tasselli a coda di rondine: la base in sei, '
                                  'la mascherina in due, una metà del retro in due. Il numero è quello del file.', 150), 4.0, 400, '#333'),
             immagine(png, 10, 42, 180, 150)]
    el, yy = _elenco(196, 46, [
        'Prova a secco: ogni coda entra nella sua sede a mano, al massimo con un colpo leggero. Se è dura, carta '
        'abrasiva fine sui fianchi della coda, non sulla sede.',
        'Colla cianoacrilica in gel o epossidica bicomponente nelle sedi; unire su un piano dritto (vetro o piano di '
        'lavoro), premere e tenere fermo con pesi o morsetti finché la colla tira.',
        'La base: prima le due file da tre, poi le due file insieme. Controllare con una riga che resti piana.',
        'La mascherina: le due metà con la faccia in vista in giù sul vetro, così la giunta resta a filo.',
        'Una passata di carta abrasiva sulla giunta della faccia in vista, se serve.'], 46, 3.4, 4.9)
    corpo += el
    pagine.append(_pagina_in(pag, '02_tasselli', '\n'.join(corpo), 2, tot, piede))
    # 3: scritte e montaggio
    png = os.path.join(pag, 'mappa.png')
    svg_png(os.path.join(cart, 'etichette_mappa.svg'), png)
    corpo = [testo(14, 22, ['Scritte e montaggio'], 10, 700, '#141B18'),
             testo(14, 34, ['Le scritte'], 5.2, 700)]
    el, y = _elenco(14, 41, [
        f'Fianchi: il marchio e il nome escono di {virgola(M.RILIEVO)} mm. Per averli in un altro colore, nello slicer un cambio '
        f'di filamento (pausa, M600) alla quota {virgola(M.FIANCO)} mm, dove comincia il rilievo.',
        f'Mascherina e piano della Flip: le scritte del laser sono troppo fini per un ugello da 0,4, quindi si stampano su '
        f'carta. Ogni gruppo ha una tasca profonda {virgola(M.TASCA)} mm; etichette_mascherina.pdf, al 100 %, su carta adesiva '
        'opaca o vinile da stampa (meglio con una pellicola trasparente sopra).',
        'Ritagliare con taglierino e righello lungo il bordo grigio; posare con una pinzetta nella tasca con lo stesso '
        'numero. Quattro scritte fra le file dei pad non hanno la tasca (manca il posto): si posano sulla faccia.'], 70, 3.4, 4.9)
    corpo += el
    corpo.append(testo(14, y + 5, ['Il montaggio'], 5.2, 700))
    el, y = _elenco(14, y + 12, [
        'Come in istruzioni_montaggio.pdf, passi 1-9, con queste differenze:',
        'passo 1: la base è già una lastra sola (i tasselli incollati);',
        'passo 2: ogni metà del retro e la costola sono un pezzo solo, senza strati da incollare; nelle tacche e nelle '
        'asole con la colla dei tasselli, o a secco se stanno strette;',
        'passo 3: i fianchi sono un pezzo solo; le squadrette si avvitano con le viti per plastica (o inserti a caldo);',
        'passi 4-9: uguali.'], 70, 3.4, 4.9)
    corpo += el
    corpo.append(testo(150, 34, ['Minuteria'], 5.2, 700))
    el, _ = _elenco(150, 41, MINUTERIA_STAMPA, 66, 3.3, 4.6)
    corpo += el
    corpo.append(immagine(png, 150, 104, 134, 94))
    pagine.append(_pagina_in(pag, '03_scritte', '\n'.join(corpo), 3, tot, piede))
    pdfs = []
    for p in pagine:
        pdf = p[:-4] + '.pdf'
        svg_pdf(p, pdf)
        pdfs.append(pdf)
    out = os.path.join(cart, 'istruzioni_stampa3d.pdf')
    unisci(pdfs, out, 'Stame — la console tutta stampata')
    # le etichette: la pagina da stampare al 100 % e la mappa
    eti = []
    for n in ('etichette_mascherina', 'etichette_mappa'):
        pdf = os.path.join(pag, n + '.pdf')
        svg_pdf(os.path.join(cart, n + '.svg'), pdf)
        eti.append(pdf)
    out_e = os.path.join(cart, 'etichette_mascherina.pdf')
    unisci(eti, out_e, 'Stame — etichette della mascherina (stampare al 100 %)')
    return out, out_e


def svg_png(svg, png, scala=4):
    """la pagina SVG in PNG, ritagliata sul disegno (fuori resta solo il bianco)"""
    from PIL import Image, ImageChops
    esegui(VC, 'convert', svg, png, '--scale', str(scala))
    im = Image.open(png).convert('RGB')
    box = ImageChops.difference(im, Image.new('RGB', im.size, (255, 255, 255))).getbbox()
    if box:
        m = 6 * scala
        im.crop((max(box[0] - m, 0), max(box[1] - m, 0), min(box[2] + m, im.width), min(box[3] + m, im.height))).save(png)
    return png


def virgola(x, d=1):
    return f'{x:.{d}f}'.replace('.', ',')


def ritaglia_in(png, cartella):
    """come ritaglia(), ma nella cartella data"""
    from PIL import Image
    im = Image.open(png)
    out = os.path.join(cartella, os.path.basename(png))
    im.crop((0, 150, im.width, im.height)).save(out)
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
    for p in istruzioni_stampa3d():
        print(p)


if __name__ == '__main__':
    main()
