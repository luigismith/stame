"""manuale.py — i documenti del case: progetti di taglio e istruzioni di montaggio, in PDF.

Uso: python -I hardware/case/manuale.py      (dopo genera.py e assieme.py)
     python -I hardware/case/manuale.py --stampa3d       solo le due console stampate, a vasche
     python -I hardware/case/manuale.py --multicolore    solo quella a più colori

Usa la suite ArtCraft: VectorCraft converte le pagine SVG in PDF vettoriali, PdfCraft le unisce e
mette il titolo. Dove VectorCraft non c'è (il PC di lavoro) le pagine le stampa Edge senza finestra, alla
loro misura e in vettoriale, con un profilo temporaneo (quello di chi usa Edge resta fuori). Escono out/taglio/progetti_di_taglio.pdf (i fogli 1:1, da mandare al laser o da
stampare per controllo, e la dima) e out/istruzioni_montaggio.pdf (copertina con i pezzi e la
minuteria, un passo per pagina, le misure da verificare); per le console stampate a vasche
out/stampa3d/istruzioni_stampa3d.pdf con etichette_mascherina.pdf, e out/stampa3d_multicolore/istruzioni_multicolore.pdf.
"""
import base64
import os
import re
import subprocess
import sys
import tempfile

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import genera as G                   # noqa: E402
import assieme as A                  # noqa: E402
import misure as M                   # noqa: E402

VC = r'C:\Program Files\VectorCraft\vectorcraft-cli.exe'
PC = r'C:\Program Files\PdfCraft\pdfcraft-cli.exe'
EDGE = (r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe')
OUT = G.OUT
PAG = os.path.join(OUT, 'montaggio', 'pagine')
W, H = 297.0, 210.0                                         # A4 orizzontale, mm
FONT = "Bahnschrift, 'Segoe UI', Arial, sans-serif"


def esegui(*args):
    r = subprocess.run(list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f'{os.path.basename(args[0])}: {r.stderr or r.stdout}')


def svg_pdf(svg, pdf):
    if os.path.exists(VC):
        esegui(VC, 'convert', svg, pdf)
    else:
        edge_pdf(svg, pdf)


def edge_pdf(svg, pdf):
    """la pagina SVG in PDF con Edge senza finestra: una pagina alla misura del disegno (width e height in mm),
    margini zero, l'SVG dentro l'HTML così testi e tratti restano vettoriali"""
    edge = next((e for e in EDGE if os.path.exists(e)), None)
    if not edge:
        raise SystemExit('per i PDF serve VectorCraft o Microsoft Edge')
    testo_svg = open(svg, encoding='utf-8').read()
    w = float(re.search(r'width="([0-9.]+)mm"', testo_svg).group(1))
    h = float(re.search(r'height="([0-9.]+)mm"', testo_svg).group(1))
    corpo = re.sub(r'^<\?xml[^>]*>\s*', '', testo_svg)
    html = os.path.abspath(pdf[:-4] + '.html')
    with open(html, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f'<!doctype html><html><head><meta charset="utf-8"><style>@page {{ size: {w}mm {h}mm; margin: 0 }}'
                f'html, body {{ margin: 0; padding: 0 }} svg {{ display: block }}</style></head><body>{corpo}</body></html>')
    with tempfile.TemporaryDirectory() as profilo:
        subprocess.run([edge, '--headless', '--disable-gpu', f'--user-data-dir={profilo}', '--no-pdf-header-footer',
                        '--virtual-time-budget=3000', f'--print-to-pdf={os.path.abspath(pdf)}', 'file:///' + html.replace(os.sep, '/')],
                       capture_output=True, timeout=180)
    os.remove(html)
    if not os.path.exists(pdf):
        raise SystemExit(f'Edge non ha scritto {pdf}')


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
    'viti da legno 3 × 12: 6 per le squadrette nei fianchi, 2 per il fermo dell\'hub, 1 per la colonnina',
    'colla vinilica (legno); feltro adesivo da 1 mm in strisce sugli appoggi del piano',
    '6 piedini in gomma da 12 mm sotto la base',
    'hub USB-C NOVOO 9 in 1 (100 × 44 × 12,5): il fermo e la finestra del retro sono fatti sulle sue porte; cavi USB-C a 90° '
    'per la MK4 e per il pad; cavi corti',
]

VERIFICARE = [
    'MK4: dima su carta (controlli dalle foto, ±1 mm); altezza del pannello (37 mm) e dei pulsanti piccoli',
    "Macro pad: misurato col metro il 19/10 (185 × 75, corpo 16,2, USB-C fra m1 e m2 a 8,3 dal fondo); resta l'altezza dell'interruttore sul retro",
    'Flip: angolo massimo dello schermo (serve 115°: schermo a 65°); porte e tasti presi dalle foto',
    'Hub NOVOO: che si accenda con la Flip con l\'ingresso PD vuoto (CASE-021); la finestra del retro sulle sue porte, col calibro',
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
                                        'altezza 132 mm con lo schermo aperto, 141 con la visiera.', 80), 3.6, 400, '#444'))
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


def minuteria_stampa(viti, etichette=True):
    """la minuteria della console stampata, con le viti delle giunte che servono per quel piatto"""
    import stampa3d as S
    out = ['viti M3 × 10 svasate e dadi M3: 4 per la culla della Flip, sotto la Flip',
           'viti M3 × 10 e dadi M3: 2 per i piedi della visiera, i dadi sotto il piano',
           f'{S.testo_viti(viti)}: le giunte delle vasche, ognuna nella sua sede',
           'feltro adesivo da 1 mm in strisce sugli appoggi del piano; 6 piedini in gomma da 12 mm, due sotto ogni colonna di vasche',
           'niente colla: le vasche si smontano (una goccia di cianoacrilica nelle code, se si vuole la console in un pezzo)']
    if etichette:
        out.append('carta adesiva (o vinile da stampa) A4 per le etichette; taglierino e righello')
    out.append('hub USB-C NOVOO 9 in 1 (100 × 44 × 12,5): il fermo e la finestra del retro sono fatti sulle sue porte; cavi '
               'USB-C a 90° per la MK4 e per il pad; cavi corti')
    return out


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


def _giunte(n_vasche, viti):
    """come si uniscono le vasche: le stesse parole nei due PDF"""
    import stampa3d as S
    return [
        f'Le {n_vasche} vasche si calano una accanto all\'altra sul tavolo, in qualunque ordine: le code di rondine del fondo '
        'entrano dall\'alto nelle loro sedi, e le pareti che attraversano la giunta si sormontano a mezzo spessore.',
        'Perché così: stampate in piedi, code e sedi sono prismi dritti, senza sbalzi né supporti, e allineano le vasche da '
        'sole. Le code però non tengono in altezza: per questo in ogni sormonto ci sono due viti M3, la testa nella sua sede '
        'nella faccia di fuori, il dado nella sua sede in quella di dentro. Niente colla, e la console si smonta.',
        'Le giunte stanno dove non tagliano sedi né appoggi: a metà sotto la MK4, che ci appoggia sopra; fra la costola e la '
        'culla del pad, che resta intera; con sei vasche anche davanti alla colonnina, dietro la culla.',
        f'Viti: {S.testo_viti(viti)}. Si stringono dopo aver calato le vasche, prima di mettere hub, piano e MK4.',
        f'Prima delle vasche, prova_giunta.stl (circa 30 g): le due metà devono calarsi a mano, con '
        f'{virgola(M.GIOCO_STAMPA, 2)} mm di gioco per lato nelle sedi delle code. Se la coda è dura, carta abrasiva '
        'fine sui suoi fianchi; se balla, una goccia di colla.']


def _montaggio():
    return [
        'Le vasche, come a pagina 2; poi le viti delle giunte. Piedini in gomma sotto.',
        'L\'hub nel fermo, con il lato dell\'alimentazione nella finestra del retro; i cavi come nella console laser '
        '(istruzioni_montaggio.pdf, passo 4): '
        'quello della MK4 dietro e sotto il ponte della costola. Feltro sugli appoggi: retro, fianchi, costola, colonnina, '
        'dente della culla del pad.',
        'Il pad nella sua culla, con il cavo a 90° nella finestra di dietro.',
        'La culla della Flip e la visiera avvitate al piano (4 viti svasate e 2 viti M3, i dadi sotto), il piano sugli appoggi.',
        'La MK4 sulla pedana; le due metà della mascherina sopra, ogni controllo nel suo foro.',
        'La Flip nella culla, i cavi nelle fessure; i tasti trasparenti del pad con le etichette (etichette_pad.pdf).']


def istruzioni_stampa3d():
    """out/stampa3d/istruzioni_stampa3d.pdf (i pezzi, le vasche e le giunte, le scritte e il montaggio) ed
    etichette_mascherina.pdf (le etichette 1:1 e dove vanno)"""
    import stampa3d as S
    righe, totale, _, viti = S.genera()
    cart = S.OUT3D
    pag = os.path.join(cart, 'pagine')
    os.makedirs(pag, exist_ok=True)
    for n in os.listdir(pag):
        os.remove(os.path.join(pag, n))
    piatto = M.PIATTO_COMUNE[0]
    n_vasche = sum(1 for r in righe if r['nome'].startswith('vasca_'))
    piede = 'Stame · la console tutta stampata, a vasche'
    tot = 3
    pagine = []
    # 1: i pezzi
    telaio = sum(r['grammi'] for r in righe if r['colore'] == 'telaio')
    corpo = [testo(14, 22, ['Stame — la console tutta stampata'], 11, 700, '#141B18'),
             testo(14, 31, [f'Per chi non ha il laser · a vasche, 19/10/2026 · piatto da {piatto:.0f} × {piatto:.0f} mm '
                            '(stampanti da 220 in su; con 240, stampa3d.py --piatto 240: tre vasche)'], 4.0, 400, '#555'),
             immagine(ritaglia_in(os.path.join(cart, 'console_stampata.png'), pag), 150, 36, 138, 90),
             testo(14, 44, ['I pezzi'], 5.2, 700)]
    y = 51
    for r in righe:
        dx, dy, dz = r['dim']
        q = f' ×{r["quanti"]}' if r['quanti'] > 1 else ''
        corpo.append(testo(14, y, [f'{r["nome"]}.stl{q}'], 3.2, 700))
        corpo.append(testo(64, y, [f'{dx:.0f} × {dy:.0f} × {dz:.0f} mm'], 3.2))
        corpo.append(testo(104, y, [f'{r["grammi"]:.0f} g'], 3.2))
        y += 4.6
    corpo.append(testo(14, y + 3, a_capo(f'Filamento: circa {virgola(totale / 1000)} kg, di cui {virgola(telaio / 1000)} kg per '
                                         'le vasche (color legno o sabbia) e il resto in nero.', 64), 3.4, 400, '#333'))
    el, y2 = _elenco(14, y + 16, ['Ogni vasca è un tratto di console già montato: fondo, pareti, appoggi del piano e sedi. Si '
                                  'stampa in piedi, con il fondo sul piatto; niente squadrette, linguette o strati da incollare.'],
                     64, 3.3, 4.6)
    corpo += el
    corpo.append(testo(150, 136, ['Impostazioni'], 5.2, 700))
    el, yy = _elenco(150, 143, [
        'PETG o PLA, ugello 0,4, strati da 0,2; 3 perimetri, 4 strati pieni sopra e sotto, riempimento giroide al 20 %.',
        'Ogni file esce nel verso giusto: le vasche in piedi, mascherina e piano con la faccia in vista in alto.',
        'Senza supporti: nelle vasche ci sono solo ponti corti (il passaggio dei cavi sotto la costola, le finestre della '
        'culla del pad). Solo la visiera, che si stampa sul tettuccio, vuole i supporti sotto i piedi.',
        'Le vasche sono alte 45 mm e larghe quasi quanto il piatto: piatto pulito, una tesa di 5 mm se gli angoli si alzano.'],
        70, 3.3, 4.6)
    corpo += el
    pagine.append(_pagina_in(pag, '01_pezzi', '\n'.join(corpo), 1, tot, piede))
    # 2: le vasche e le giunte
    corpo = [testo(14, 22, ['Le vasche e le giunte'], 10, 700, '#141B18'),
             immagine(os.path.join(cart, 'vasche.png'), 8, 28, 184, 110),
             immagine(os.path.join(cart, 'giunta.png'), 14, 140, 76, 55),
             testo(92, 152, a_capo('La prova di giunta: a sinistra il retro passa la giunta con le sedi delle teste, a '
                                   'destra le sedi dei dadi; sotto, la coda di rondine e la sua sede.', 52), 3.2, 400, '#555')]
    el, _ = _elenco(196, 32, _giunte(n_vasche, viti), 46, 3.3, 4.7)
    corpo += el
    pagine.append(_pagina_in(pag, '02_vasche', '\n'.join(corpo), 2, tot, piede))
    # 3: scritte e montaggio
    png = os.path.join(pag, 'mappa.png')
    svg_png(os.path.join(cart, 'etichette_mappa.svg'), png)
    corpo = [testo(14, 22, ['Scritte e montaggio'], 10, 700, '#141B18'),
             testo(14, 34, ['Le scritte'], 5.2, 700)]
    el, y = _elenco(14, 41, [
        f'Fianchi: il marchio e il nome escono di {virgola(M.RILIEVO)} mm dalla faccia di fuori, che stampata in piedi è '
        'verticale: vengono del colore della vasca. A più colori, con le scritte stampate: istruzioni_multicolore.pdf.',
        f'Mascherina e piano della Flip: le scritte del laser sono troppo fini per un ugello da 0,4 e si stampano su carta. '
        f'Ogni gruppo ha una tasca profonda {virgola(M.TASCA)} mm; etichette_mascherina.pdf al 100 % su carta adesiva opaca o '
        'vinile da stampa, ritagliate lungo il bordo grigio e posate con una pinzetta nella tasca con lo stesso numero.',
        'La mascherina è in due metà accostate, senza giunta: i fori sui comandi della MK4 tengono ogni metà al suo posto, e '
        'per arrivare ai cavi si sollevano una per volta.'], 70, 3.4, 4.9)
    corpo += el
    corpo.append(testo(14, y + 4, ['Il montaggio'], 5.2, 700))
    el, y = _elenco(14, y + 11, [f'{k}. {p}' for k, p in enumerate(_montaggio(), 1)], 70, 3.4, 4.9, '')
    corpo += el
    corpo.append(testo(150, 34, ['Minuteria'], 5.2, 700))
    el, ym = _elenco(150, 41, minuteria_stampa(viti), 66, 3.3, 4.6)
    corpo += el
    corpo.append(immagine(png, 150, ym + 2, 134, H - 18 - ym))
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


def istruzioni_multicolore():
    """out/stampa3d_multicolore/istruzioni_multicolore.pdf: i pezzi con i filamenti, lo slicer, le scritte, le
    vasche e il montaggio della console stampata a più colori (multicolore.py, 60-case.md §7c)"""
    import multicolore as MC
    righe, totale, report, viti = MC.genera()
    cart = MC.OUT
    pag = os.path.join(cart, 'pagine')
    os.makedirs(pag, exist_ok=True)
    for n in os.listdir(pag):
        os.remove(os.path.join(pag, n))
    piatto = M.PRINT_BED[0]
    n_vasche = sum(1 for r in righe if r['nome'].startswith('vasca_'))
    cambi = max((r.get('cambi', 0) for r in righe if r['nome'].startswith('vasca_')), default=0)
    piede = 'Stame · la console stampata a più colori, a vasche'
    tot = 3
    pagine = []
    filamento = {'piano': '1 nero, scritte 2', 'telaio': '2 sabbia, scritte 1'}
    da_solo = {'telaio': '2 sabbia', 'petg_sabbia': '2 sabbia'}

    def anteprima(nome):
        """l'anteprima senza la riga del titolo (la pagina ha il suo)"""
        from PIL import Image
        im = Image.open(os.path.join(cart, f'anteprima_{nome}.png'))
        out = os.path.join(pag, f'anteprima_{nome}.png')
        im.crop((0, 30, im.width, im.height)).save(out)
        return out
    # 1: i pezzi e i filamenti
    corpo = [testo(14, 22, ['Stame — la console stampata a più colori'], 11, 700, '#141B18'),
             testo(14, 31, [f'Per stampanti a più filamenti (Anycubic Kobra S1 con l\'ACE Pro) · a vasche, 19/10/2026 · '
                            f'piatto da {piatto:.0f} × {piatto:.0f} mm: {n_vasche} vasche intere davanti-dietro'], 4.2, 400, '#555'),
             testo(14, 44, ['I pezzi'], 5.2, 700)]
    y = 51
    for r in righe:
        dx, dy, dz = r['dim']
        due = '.3mf' in r['file']
        nome = f'{r["nome"]}.3mf' if due else f'{r["nome"]}.stl'
        fil = filamento[r['colore']] if due else da_solo.get(r['colore'], '1 nero')
        corpo.append(testo(14, y, [nome], 3.1, 700))
        corpo.append(testo(52, y, [f'{dx:.0f} × {dy:.0f} × {dz:.0f} mm'], 3.1))
        corpo.append(testo(88, y, [f'{r["grammi"]:.0f} g'], 3.1))
        corpo.append(testo(104, y, [fil], 3.1, 700 if due else 400, '#7A5A00' if due else '#333'))
        y += 4.4
    corpo.append(testo(14, y + 3, a_capo(f'Filamento: circa {virgola(totale / 1000)} kg in tutto. In grassetto i pezzi con le '
                                         'scritte: un file .3mf con due parti, e accanto gli stessi in due STL (_corpo, _scritte).',
                                         64), 3.3, 400, '#333'))
    corpo.append(immagine(anteprima('mascherina_1'), 150, 36, 136, 94))
    corpo.append(testo(150, 140, ['Due filamenti'], 5.2, 700))
    el, _ = _elenco(150, 147, [
        '1 nero e 2 sabbia (o il colore scelto per il telaio). Si scambiano il ruolo:',
        'mascherina e piano della Flip: corpo 1, scritte 2, come l\'incisione del laser sull\'acrilico nero;',
        'vasche: corpo 2, scritte 1 nei fianchi, come la bruciatura sul legno;',
        'la vasca di centro e la prova di giunta col 2; la culla della Flip e la visiera col 1.'], 66, 3.3, 4.6)
    corpo += el
    pagine.append(_pagina_in(pag, '01_pezzi', '\n'.join(corpo), 1, tot, piede))
    # 2: nello slicer
    corpo = [testo(14, 22, ['Nello slicer'], 10, 700, '#141B18'),
             testo(14, 31, ['Anycubic Slicer Next, o un altro slicer per più filamenti'], 4.4, 400, '#555')]
    el, y = _elenco(14, 42, [
        'Apri il .3mf del pezzo: arriva un oggetto con due parti, «corpo» e «scritte», con i filamenti già assegnati. '
        'Controllali nell\'elenco degli oggetti.',
        'Se lo slicer lo apre come due oggetti, o se preferisci gli STL: importa insieme _corpo.stl e _scritte.stl e, '
        'alla domanda, caricali come un oggetto solo con più parti; poi assegna i filamenti a mano (pagina 1).',
        'Non girare i pezzi: le vasche stanno in piedi con il fondo sul piatto, mascherina e piano con la faccia in vista sul '
        'piatto (liscia sul piatto liscio, con la sua grana su quello testurizzato). Non spostare le due parti.',
        f'Strati da 0,2, primo strato da 0,2. Nei piani le scritte sono profonde {virgola(MC.SCRITTA_H)} mm, i primi tre '
        f'strati. Nelle vasche il fianco è verticale: il filamento cambia in ogni strato fra il marchio e il nome, circa '
        f'{cambi} strati, quindi la vasca con il fianco dura di più e spurga di più.',
        'Torre di spurgo sì. Se lo slicer lo permette, spurgo nel riempimento. Se i cambi nelle vasche sono troppi, le '
        'vasche a un colore (../stampa3d, con --piatto 240) hanno il marchio in rilievo.',
        'Il primo strato deve essere perfetto: piatto pulito e sgrassato, livellamento fatto, velocità bassa. Le lettere '
        'hanno il tratto di una linea dell\'ugello (0,45 mm).',
        'Il resto come la console stampata a un colore: PETG o PLA, ugello 0,4, 3 perimetri, 4 strati pieni sopra e sotto, '
        'riempimento giroide al 20 %, senza supporti. Prima delle vasche, prova_giunta.stl.'], 74, 3.4, 4.9)
    corpo += el
    corpo.append(immagine(anteprima('mascherina_2'), 156, 38, 128, 86))
    corpo.append(immagine(anteprima('piano_flip'), 156, 128, 128, 66))
    pagine.append(_pagina_in(pag, '02_slicer', '\n'.join(corpo), 2, tot, piede))
    # 3: scritte, vasche e montaggio
    fuori = [f'{n}: {"; ".join(f)}' for n, (_, f, _) in report.items() if f]
    corpo = [testo(14, 22, ['Scritte, vasche e montaggio'], 10, 700, '#141B18'),
             testo(14, 34, ['Le scritte'], 5.2, 700)]
    el, y = _elenco(14, 41, [
        'Ridisegnate con Matrice, il carattere 5×7 di Stame, a quadretti da 0,45 mm: lettere alte 3,15 mm. Logo e punti del '
        'nome restano quelli del laser. Sulla mascherina i tipi d\'accordo e i piatti del banco B vanno sotto i pad, con '
        'l\'estensione e il tamburo della stessa colonna: «DIM/6», «B:CHH/KICK».'
        + (' Restano fuori, perché non ci stanno: ' + '; '.join(fuori) + '.' if fuori else '')], 70, 3.4, 4.9)
    corpo += el
    corpo.append(testo(14, y + 4, ['Le vasche'], 5.2, 700))
    el, y = _elenco(14, y + 11, _giunte(n_vasche, viti)[:2] + [_giunte(n_vasche, viti)[3]], 70, 3.4, 4.9)
    corpo += el
    corpo.append(testo(14, y + 4, ['Il montaggio'], 5.2, 700))
    el, y = _elenco(14, y + 11, ['Come nella console a un colore (istruzioni_stampa3d.pdf, pagine 2 e 3): le vasche calate '
                                 'una accanto all\'altra e avvitate, l\'hub, il pad, il piano con la culla, la MK4 e le due '
                                 'metà della mascherina, la Flip. Niente etichette di carta: le scritte sono nei pezzi.'],
                    70, 3.4, 4.9)
    corpo += el
    corpo.append(testo(150, 34, ['I fianchi, come si guardano da fuori'], 5.2, 700))
    corpo.append(immagine(anteprima('fianco_sx'), 150, 38, 136, 30))
    corpo.append(immagine(anteprima('fianco_dx'), 150, 70, 136, 30))
    corpo.append(testo(150, 110, ['Minuteria'], 5.2, 700))
    el, _ = _elenco(150, 117, minuteria_stampa(viti, etichette=False), 66, 3.3, 4.6)
    corpo += el
    pagine.append(_pagina_in(pag, '03_scritte', '\n'.join(corpo), 3, tot, piede))
    pdfs = []
    for p in pagine:
        pdf = p[:-4] + '.pdf'
        svg_pdf(p, pdf)
        pdfs.append(pdf)
    out = os.path.join(cart, 'istruzioni_multicolore.pdf')
    unisci(pdfs, out, 'Stame — la console stampata a più colori')
    return out


def svg_png(svg, png, scala=4):
    """la pagina SVG in PNG, ritagliata sul disegno (fuori resta solo il bianco)"""
    from PIL import Image, ImageChops
    if os.path.exists(VC):
        esegui(VC, 'convert', svg, png, '--scale', str(scala))
    else:                             # senza VectorCraft: Edge fa il PDF, PdfCraft lo rende in PNG
        pdf = png[:-4] + '.tmp.pdf'
        edge_pdf(svg, pdf)
        esegui(PC, 'render', pdf, '--page', '1', '--dpi', str(int(25.4 * scala)), '--out', png)
        os.remove(pdf)
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
    if '--multicolore' in sys.argv:                  # solo le istruzioni della console a più colori
        print(istruzioni_multicolore())
        return
    if '--stampa3d' in sys.argv:                     # solo le due console stampate, a un colore e a più colori
        for p in istruzioni_stampa3d():
            print(p)
        print(istruzioni_multicolore())
        return
    G.genera()
    print(taglio())
    print(istruzioni())
    for p in istruzioni_stampa3d():
        print(p)
    print(istruzioni_multicolore())


if __name__ == '__main__':
    main()
