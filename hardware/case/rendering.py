"""rendering.py — rendering fotorealistico della console con Blender (Cycles).

Uso: python -I hardware/case/rendering.py [--prova | --bozza | --blend] [--viste eroe,pad,…]   (dopo genera.py e assieme.py)

Prepara le texture in build/render/ (incisioni di mascherina, piano della Flip e fianchi dagli SVG, le
etichette dei tasti del pad, la faccia della Flip raddrizzata dalla foto, lo schermo con la
plancia), scrive scena.json con i riferimenti dei pezzi e lancia Blender in background con
blender_scena.py. I PNG escono in build/render/, i JPG per il repo in out/render/.
--prova: risoluzione e campioni bassi, per controllare inquadrature e materiali. --viste: solo
quelle (i nomi sono nelle chiamate a scatta() di blender_scena.py). --bozza: viste veloci con Workbench
(build/render/bozza_*.png), per le forme; --blend: salva build/render/stame.blend e lo apre in Blender.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.normpath(os.path.join(QUI, '..', '..'))
sys.path.insert(0, QUI)
import misure as M                  # noqa: E402

OUT = os.path.join(QUI, 'out')
BUILD = os.path.join(RADICE, 'build', 'render')
TEX = os.path.join(BUILD, 'tex')
FOTO = os.path.join(RADICE, 'private', 'foto')
VC = r'C:\Program Files\VectorCraft\vectorcraft-cli.exe'
BLENDER = r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
PT_MM = 72 / 25.4                   # VectorCraft: scala 1 = un punto per millimetro... in punti


def svg_png(svg, png, px_mm):
    subprocess.run([VC, 'convert', svg, png, '--scale', f'{px_mm / PT_MM:.3f}'], check=True, capture_output=True)
    return np.asarray(Image.open(png).convert('RGBA')).astype(np.int16)


def incisione(nome, px_mm=12.0):
    """maschera dell'incisione (bianco = inciso) di un pezzo del laser, alla misura del suo SVG"""
    a = svg_png(os.path.join(OUT, nome + '.svg'), os.path.join(TEX, nome + '_svg.png'), px_mm)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    inc = (al > 80) & (r < 120) & (g < 120) & (b < 120)
    Image.fromarray((inc * 255).astype(np.uint8)).save(os.path.join(TEX, nome + '_inc.png'))
    vb = open(os.path.join(OUT, nome + '.svg'), encoding='utf-8').read().split('viewBox="')[1].split('"')[0].split()
    return float(vb[2]), float(vb[3])


def etichette(px_mm=24.0):
    """le 15 etichette della prima serie chiara di etichette_pad.svg, una immagine per tasto"""
    import etichette as E
    a = svg_png(os.path.join(OUT, 'etichette_pad.svg'), os.path.join(TEX, 'etichette_svg.png'), px_mm)
    im = Image.fromarray(a.astype(np.uint8)).convert('RGB')
    w, h = E.CELLA
    x0 = E.A4[0] / 2 - 5 * w - 10
    y0 = 68.0
    for k in range(15):
        r, c = divmod(k, 5)
        box = [round(v * px_mm) for v in (x0 + c * w, y0 + r * h, x0 + (c + 1) * w, y0 + (r + 1) * h)]
        im.crop(box).save(os.path.join(TEX, f'etichetta_{k:02d}.png'))


def faccia_flip():
    """la metà con i tasti dalla foto flip_aperta.jpg, raddrizzata: 84 x 80,35 mm a 10 px/mm; senza la
    foto (sta fuori da git, su HOMEPC) la faccia si disegna"""
    if not os.path.exists(os.path.join(FOTO, 'flip_aperta.jpg')):
        faccia_disegnata()
        return
    im = Image.open(os.path.join(FOTO, 'flip_aperta.jpg')).convert('RGB')
    k = im.width / 1500.0
    # angoli della faccia (cerniera a sinistra, a destra; davanti a destra, a sinistra), in pixel
    quad = [(343, 982), (943, 982), (948, 1556), (318, 1556)]
    quad = [(x * k, y * k) for x, y in quad]
    W, H = 840, 804
    coeffs = _prospettiva([(0, 0), (W, 0), (W, H), (0, H)], quad)
    im.transform((W, H), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC).save(
        os.path.join(TEX, 'flip_faccia.png'))


def faccia_disegnata():
    """la faccia della Flip bianca disegnata (10 px/mm, cerniera in alto): croce, ABXY pastello, levette,
    SELECT e START, il tasto di accensione e la griglia dell'altoparlante, come nella foto del 15/10"""
    from PIL import ImageDraw, ImageFilter
    k = 10
    W, H = 840, 804
    im = Image.new('RGB', (W, H), (226, 226, 220))
    d = ImageDraw.Draw(im)

    def cerchio(c, r, fill, outline=None, w=0):
        x, y = c
        d.ellipse([(x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k], fill=fill, outline=outline, width=w)

    for c in ((21.0, 30.0), (63.0, 33.0)):                     # le due conche, appena più scure
        cerchio(c, 13.5, (214, 214, 208), (200, 200, 194), 6)
    for c, r in (((19.0, 62.0), 10.0), ((65.0, 62.0), 10.0)):  # levette, alla stessa altezza: anello, bordo, cappello
        cerchio(c, r, (206, 206, 200), (186, 186, 180), 8)
        cerchio(c, r - 2.6, (70, 72, 74))
        cerchio(c, r - 4.2, (222, 222, 218), (196, 196, 190), 6)
    x, y = 21.0, 30.0                                          # croce
    for a, b, c_, e in ((x - 10, y - 3.4, x + 10, y + 3.4), (x - 3.4, y - 10, x + 3.4, y + 10)):
        d.rounded_rectangle([a * k, b * k, c_ * k, e * k], radius=12, fill=(204, 204, 198), outline=(184, 184, 178), width=4)
    x, y = 63.0, 33.0                                          # Y verde, X azzurro, A rosa, B giallo
    for (dx, dy), col in (((-7.2, 0), (198, 226, 196)), ((0, -6.8), (180, 216, 236)),
                          ((7.2, 0), (240, 198, 206)), ((0, 6.8), (240, 228, 180))):
        cerchio((x + dx, y + dy), 4.3, col, (190, 190, 186), 4)
    cerchio((42.0, 15.0), 2.0, (214, 214, 208), (190, 190, 184), 4)        # accensione, al centro
    for c in ((36.5, 71.0), (47.5, 71.0)):                                  # SELECT, START, in asse
        cerchio(c, 2.7, (210, 210, 204), (186, 186, 180), 5)
    for i in range(4):                                                      # altoparlante
        for j in range(4):
            cerchio((37.5 + i * 3.0, 47.0 + j * 3.0), 0.55, (176, 176, 170))
    im.filter(ImageFilter.GaussianBlur(1.2)).save(os.path.join(TEX, 'flip_faccia.png'))


def _prospettiva(dst, src):
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def schermo():
    """la plancia nel vetro dello schermo (72 x 66,35 mm del modello): 4:3 al centro, cornice nera;
    una per tema (Giorno è il default, Notte per la scena di sera)"""
    W, H = 720, 664
    for tema, nome in (('giorno', 'schermo.png'), ('notte', 'schermo_notte.png')):
        out = Image.new('RGB', (W, H), (6, 8, 8))
        p = Image.open(os.path.join(RADICE, 'docs', 'sito', 'img', f'plancia_{tema}.png')).convert('RGB')
        p = p.resize((700, 525), Image.Resampling.LANCZOS)
        out.paste(p, ((W - 700) // 2, (H - 525) // 2))
        out.save(os.path.join(TEX, nome))


def riferimenti():
    d = json.load(open(os.path.join(OUT, 'stame_sketchup.json'), encoding='utf-8'))
    return {q['n']: [pr['f'] for pr in q['p']] for q in d}


def tasti_pad():
    """centri dei tasti del pad nel riferimento destrorso (y specchiata), in mm"""
    out = []
    for k in range(15):
        r, c = divmod(k, 5)
        x = M.PAD_X0 + M.PAD['k0'][0] + c * M.PAD['pitch_x']
        y = M.PAD_Y0 + M.PAD['k0'][1] + r * M.PAD['pitch_y']
        out.append([x, -y])
    return out


def main():
    prova = '--prova' in sys.argv
    viste = sys.argv[sys.argv.index('--viste') + 1].split(',') if '--viste' in sys.argv else []
    modo = 'bozza' if '--bozza' in sys.argv else 'blend' if '--blend' in sys.argv else 'cycles'
    os.makedirs(TEX, exist_ok=True)
    fr = riferimenti()
    inc = {}
    for nome in ('mascherina', 'piano_flip', 'fianco_sx_esterno', 'fianco_dx_esterno'):
        inc[nome] = dict(dim=incisione(nome), frame=fr[nome][0])
    etichette()
    faccia_flip()
    schermo()
    scena = dict(
        obj=os.path.join(OUT, 'stame_console.obj'), tex=TEX, uscita=BUILD, prova=prova, viste=viste, modo=modo,
        hdr=os.path.join(BUILD, 'studio.hdr'), incisioni=inc,
        flip=fr['Miyoo Flip'][0], flip_faccia=[[M.FLIP_X - M.FLIP['w'] / 2, -M.FLIP_Y0], [M.FLIP['w'], M.FLIP['d']]],
        schermo=fr['Schermo della Flip'][0], tasti=tasti_pad(),
        tasto_top=M.PAD_Z1 + M.TASTO_PAD['z'] + M.TASTO_PAD['h'], etichetta=list(M.ETICHETTA),
        ingombro=[M.LARGHEZZA, M.BASE_Y1],
    )
    with open(os.path.join(BUILD, 'scena.json'), 'w', encoding='utf-8') as f:
        json.dump(scena, f, indent=1)
    if not os.path.exists(scena['hdr']):
        print('manca', scena['hdr'], '(Poly Haven, studio_small_09_2k.hdr, CC0)')
        return
    r = subprocess.run([BLENDER, '-b', '--factory-startup', '-P', os.path.join(QUI, 'blender_scena.py'), '--',
                        os.path.join(BUILD, 'scena.json')])
    if r.returncode:
        sys.exit(r.returncode)
    if modo == 'blend':                 # Blender con la finestra, sulla scena salvata: la si gira con il mouse
        subprocess.Popen([BLENDER, os.path.join(BUILD, 'stame.blend')])
        return
    if modo == 'bozza':
        return
    os.makedirs(os.path.join(OUT, 'render'), exist_ok=True)
    for n in sorted(os.listdir(BUILD)):
        fatta = not viste or n[len('render_'):-4] in viste
        if n.startswith('render_') and n.endswith('.png') and not prova and fatta:
            Image.open(os.path.join(BUILD, n)).convert('RGB').save(
                os.path.join(OUT, 'render', n[len('render_'):-4] + '.jpg'), quality=92, optimize=True)
            print('out/render/' + n[len('render_'):-4] + '.jpg')


if __name__ == '__main__':
    main()
