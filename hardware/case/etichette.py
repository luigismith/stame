"""etichette.py — le etichette di carta per i tasti trasparenti del macro pad (CASE-043).

Uso: python -I hardware/case/etichette.py      scrive out/etichette_pad.svg e out/etichette_pad.pdf

I tasti trasparenti a due strati (Luigi, 17/10/2026) hanno sotto il coperchio un vano da 11 × 9 mm:
ogni etichetta si taglia a 10,8 × 8,8. Sopra il nome nella mappa del pad (40 MIDI-120, MIDI-133),
con i punti della Matrice come sulla plancia e sul case.
T13 LOCK, T14 VIEW e T15 PAGE sono gli stati di Stame: etichette in negativo, come nel prontuario.
Un foglio A4 al 100 %: quattro serie chiare e quattro scure (il tema Notte), un righello di prova.
"""
import os
import subprocess
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import genera as G                  # noqa: E402
import misure as M                  # noqa: E402

OUT = os.path.join(QUI, 'out')
VC = r'C:\Program Files\VectorCraft\vectorcraft-cli.exe'

A4 = (210.0, 297.0)
CELLA = (M.ETICHETTA[0] - 0.2, M.ETICHETTA[1] - 0.2)
PASSO_NOME = 0.30                    # «SCENE» e «PANIC», le parole più larghe: 8,7 mm, lontane dal bordo
STATI = {4, 9, 14}                   # T13, T14, T15

# inchiostri: chiaro (carta bianca) e scuro (Notte: vetro verde scuro, fosfori)
TEMI = {
    'chiaro': dict(fondo='#FFFFFF', nome='#151A19', nota='#B86E0A', stato_fondo='#151A19', stato_nome='#F2EFE6'),
    'scuro': dict(fondo='#0B1F1C', nome='#9FF0DC', nota='#F0A43C', stato_fondo='#F2EFE6', stato_nome='#0B1F1C'),
}


def punti(out, x, base, passo, testo, colore, allinea='centro'):
    w = G.matrice_w(testo, passo)
    if allinea == 'centro':
        x -= w / 2
    elif allinea == 'destra':
        x -= w
    r = passo * 0.42
    for px, py in G.matrice_punti(testo, passo):
        out.append(f'<circle cx="{x + px:.3f}" cy="{base + py:.3f}" r="{r:.3f}" fill="{colore}"/>')


def etichetta(out, x0, y0, k, tema):
    righe = G.COPRITASTI[k]
    t = TEMI[tema]
    stato = k in STATI
    fondo = t['stato_fondo'] if stato else t['fondo']
    ink = t['stato_nome'] if stato else t['nome']
    w, h = CELLA
    out.append(f'<rect x="{x0:.3f}" y="{y0:.3f}" width="{w:.3f}" height="{h:.3f}" fill="{fondo}"/>')
    alto_nome = 7 * PASSO_NOME
    gap = 1.2 * PASSO_NOME * 2
    blocco = len(righe) * alto_nome + (len(righe) - 1) * gap
    base = y0 + (h - blocco) / 2 + alto_nome
    for testo in righe:
        punti(out, x0 + w / 2, base, PASSO_NOME, testo, ink)
        base += alto_nome + gap


def serie(out, x0, y0, tema):
    w, h = CELLA
    for k in range(15):
        r, c = divmod(k, 5)
        etichetta(out, x0 + c * w, y0 + r * h, k, tema)
    # linee di taglio, condivise fra le etichette vicine
    for c in range(6):
        out.append(f'<line x1="{x0 + c * w:.3f}" y1="{y0 - 2:.3f}" x2="{x0 + c * w:.3f}" y2="{y0 + 3 * h + 2:.3f}" '
                   f'stroke="#9A9A9A" stroke-width="0.08"/>')
    for r in range(4):
        out.append(f'<line x1="{x0 - 2:.3f}" y1="{y0 + r * h:.3f}" x2="{x0 + 5 * w + 2:.3f}" y2="{y0 + r * h:.3f}" '
                   f'stroke="#9A9A9A" stroke-width="0.08"/>')


def foglio():
    out = []
    W, H = A4
    out.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>')
    punti(out, 18, 24, 0.7, 'STAME', '#151A19', 'sinistra')
    punti(out, 18, 33, 0.4, 'ETICHETTE DEL MACRO PAD', '#151A19', 'sinistra')
    righe = ['STAMPARE AL 100 % SENZA ADATTARE ALLA PAGINA',
             f'TAGLIARE LUNGO LE LINEE GRIGIE  {CELLA[0]:.1f} X {CELLA[1]:.1f} MM  (VANO 11 X 9)',
             'COME SUL PAD  T1-T5 IN ALTO  T11-T15 IN BASSO']
    for i, r in enumerate(righe):
        punti(out, 18, 42 + i * 4.2, 0.26, r, '#4A504E', 'sinistra')
    sw, sh = 5 * CELLA[0], 3 * CELLA[1]
    xs = (W / 2 - sw - 10, W / 2 + 10)
    for i in range(8):
        tema = 'chiaro' if i < 4 else 'scuro'
        r, c = divmod(i, 2)
        serie(out, xs[c], 68 + r * (sh + 14), tema)
    # righello di prova: 100 mm
    y = 68 + 4 * (sh + 14) + 6
    out.append(f'<line x1="18" y1="{y}" x2="118" y2="{y}" stroke="#151A19" stroke-width="0.25"/>')
    for k in range(11):
        out.append(f'<line x1="{18 + 10 * k}" y1="{y - 2}" x2="{18 + 10 * k}" y2="{y + 2}" stroke="#151A19" stroke-width="0.25"/>')
    punti(out, 124, y + 1.2, 0.3, '100 MM  MISURARE DOPO LA STAMPA', '#4A504E', 'sinistra')
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    svg = os.path.join(OUT, 'etichette_pad.svg')
    W, H = A4
    with open(svg, 'w', encoding='utf-8', newline='\n') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<!-- Stame, etichette dei tasti trasparenti del macro pad: A4, 1:1, millimetri. -->\n')
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">\n')
        f.write('<title>Stame — etichette del macro pad</title>\n')
        f.write('\n'.join(foglio()))
        f.write('\n</svg>\n')
    pdf = os.path.join(OUT, 'etichette_pad.pdf')
    if os.path.exists(VC):
        subprocess.run([VC, 'convert', svg, pdf], check=True, capture_output=True)
    print(svg)
    print(pdf)


if __name__ == '__main__':
    main()
