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


if __name__ == '__main__':
    tavole()
    mascherina()
