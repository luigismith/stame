"""sito_case.py — immagini del case per il sito (docs/sito/img/case_*).

Uso: python -I tools/sito_case.py      (dopo hardware/case/genera.py e assieme.py)

Le tavole di hardware/case/out/montaggio hanno il titolo in italiano dentro l'immagine: per il sito,
che è in due lingue, si ritagliano senza titolo. La mascherina viene da mascherina.svg, resa con
VectorCraft e ricolorata: acrilico nero, incisioni chiare.
"""
import os
import subprocess
import tempfile

import numpy as np
from PIL import Image
from scipy import ndimage

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
CASE = os.path.join(RADICE, 'hardware', 'case', 'out')
DEST = os.path.join(RADICE, 'docs', 'sito', 'img')
VC = r'C:\Program Files\VectorCraft\vectorcraft-cli.exe'

# tavola, ritaglio (x0, y0, x1, y1) senza il titolo, nome nel sito
TAVOLE = [
    ('console.png', (90, 200, 1410, 920), 'case_console.png'),
    ('console_retro.png', (90, 130, 1410, 850), 'case_retro.png'),
    ('passo_7.png', (90, 200, 1410, 920), 'case_passo_7.png'),
]


def tavole():
    for nome, box, dest in TAVOLE:
        im = Image.open(os.path.join(CASE, 'montaggio', nome)).convert('RGB').crop(box)
        im = im.quantize(colors=96, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        im.save(os.path.join(DEST, dest), optimize=True)
        print(dest, im.size)


def mascherina():
    with tempfile.TemporaryDirectory() as tmp:
        png = os.path.join(tmp, 'm.png')
        subprocess.run([VC, 'convert', os.path.join(CASE, 'mascherina.svg'), png, '--scale', '4'],
                       check=True, capture_output=True)
        a = np.asarray(Image.open(png).convert('RGBA')).astype(float)
    # sfondo trasparente = acrilico, rosso = taglio, nero = incisione
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    taglio = (al > 60) & (r > 150) & (g < 120) & (b < 120)
    incisione = (al > 60) & (r < 110) & (g < 110) & (b < 110)
    out = np.zeros(a.shape[:2] + (3,))
    out[...] = (28, 28, 31)
    out[incisione] = (226, 220, 204)
    out[taglio] = (90, 88, 84)
    im = Image.fromarray(out.astype(np.uint8))
    # fuori dal contorno e nei fori la pagina resta trasparente: la lastra è la regione più grande
    # fra quelle chiuse dai tagli (le scritte incise ne fanno parte)
    lab, n = ndimage.label(~ndimage.binary_dilation(taglio))
    aree = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    bordo = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    lastra = max((k for k in range(1, n + 1) if k not in bordo), key=lambda k: aree[k - 1])
    piena = ndimage.binary_dilation(lab == lastra, iterations=2)
    im.putalpha(Image.fromarray((piena * 255).astype(np.uint8)))
    im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
    im.save(os.path.join(DEST, 'case_mascherina.png'), optimize=True)
    print('case_mascherina.png', im.size)


CARTELLA = os.path.join(DEST, 'case')
FONDI = {'betulla4': (226, 196, 152), 'betulla6': (214, 182, 135), 'acrilico': (34, 34, 38)}


def pagina():
    """le immagini della pagina del case (docs/case.html): render, passi, fogli, etichette"""
    os.makedirs(CARTELLA, exist_ok=True)
    rd = os.path.join(CASE, 'render')
    for n in sorted(os.listdir(rd)):
        im = Image.open(os.path.join(rd, n)).convert('RGB')
        im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
        im.save(os.path.join(CARTELLA, 'render_' + n), quality=86, optimize=True, progressive=True)
        print('case/render_' + n, im.size)
    for k in range(1, 10):
        im = Image.open(os.path.join(CASE, 'montaggio', f'passo_{k}.png')).convert('RGB').crop((90, 200, 1410, 920))
        im = im.resize((990, 540), Image.LANCZOS)
        im = im.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        im.save(os.path.join(CARTELLA, f'passo_{k}.png'), optimize=True)
    print('case/passo_1..9.png')
    td = os.path.join(CASE, 'taglio')
    with tempfile.TemporaryDirectory() as tmp:
        for n in sorted(os.listdir(td)):
            if not (n.startswith('taglio_') and n.endswith('.svg')):
                continue
            png = os.path.join(tmp, 'f.png')
            subprocess.run([VC, 'convert', os.path.join(td, n), png, '--scale', '0.9'], check=True, capture_output=True)
            a = np.asarray(Image.open(png).convert('RGBA')).astype(float)
            mat = n[len('taglio_'):].rsplit('_', 1)[0]
            fondo = np.array(FONDI[mat], float)
            chiaro = mat != 'acrilico'
            col = np.empty(a.shape[:2] + (3,))
            col[...] = fondo
            al = a[..., 3:4] / 255
            rosso = (a[..., 0] > 150) & (a[..., 1] < 120)
            segno = (a[..., 2] > 150) & (a[..., 0] < 120)
            linea = np.where(rosso[..., None], (120, 30, 20) if chiaro else (220, 90, 70),
                             np.where(segno[..., None], (60, 90, 200), (90, 50, 25) if chiaro else (230, 226, 214)))
            col = col * (1 - al) + linea * al
            Image.fromarray(col.astype(np.uint8)).save(os.path.join(CARTELLA, n[:-4] + '.png'), optimize=True)
            print('case/' + n[:-4] + '.png')
        png = os.path.join(tmp, 'e.png')
        subprocess.run([VC, 'convert', os.path.join(CASE, 'etichette_pad.svg'), png, '--scale', '3'], check=True, capture_output=True)
        im = Image.open(png).convert('RGBA')
        s = im.width / 210.0
        bianco = Image.new('RGBA', im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bianco, im).convert('RGB').crop((int(14 * s), int(60 * s), int(196 * s), int(232 * s)))
        im.save(os.path.join(CARTELLA, 'etichette.png'), optimize=True)
        print('case/etichette.png', im.size)


def stampata():
    """la console tutta stampata (hardware/case/stampa3d.py): il disegno, i tasselli, le etichette"""
    s3 = os.path.join(CASE, 'stampa3d')
    im = Image.open(os.path.join(s3, 'console_stampata.png')).convert('RGB').crop((90, 200, 1410, 920))
    im = im.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    im.save(os.path.join(CARTELLA, 'stampata.png'), optimize=True)
    print('case/stampata.png', im.size)
    with tempfile.TemporaryDirectory() as tmp:
        for nome, scala in (('tasselli', 3), ('etichette_mascherina', 5)):
            png = os.path.join(tmp, nome + '.png')
            subprocess.run([VC, 'convert', os.path.join(s3, nome + '.svg'), png, '--scale', str(scala)], check=True, capture_output=True)
            im = Image.open(png).convert('RGB')
            a = 255 - np.asarray(im.convert('L'))
            ys, xs = np.nonzero(a > 8)
            m = 8 * scala
            im = im.crop((max(xs.min() - m, 0), max(ys.min() - m, 0), min(xs.max() + m, im.width), min(ys.max() + m, im.height)))
            if nome == 'etichette_mascherina':          # la prima serie, senza quella di ricambio
                im = im.crop((0, 0, im.width, int(im.height * 0.52)))
            im = im.quantize(colors=96, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
            im.save(os.path.join(CARTELLA, nome + '.png'), optimize=True)
            print(f'case/{nome}.png', im.size)


if __name__ == '__main__':
    tavole()
    mascherina()
    pagina()
    stampata()
