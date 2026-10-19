"""sito_manuale.py — manuale e prontuario come pagine del sito (docs/manuale.html, docs/prontuario.html).

Uso: python -I tools/sito_manuale.py      (dopo ogni modifica di docs/manuale/*.md o delle sue immagini)

Le fonti restano i due Markdown di docs/manuale: questo script li porta nello stile del sito
(stame.css, temi Giorno e Notte) con un convertitore piccolo, per il Markdown che usano: titoli,
paragrafi, elenchi anche annidati, tabelle, immagini, grassetto, corsivo, codice e link. Le immagini
diventano figure con la didascalia presa dal testo alternativo. Le schermate di stame-render sono PNG
senza compressione (900 KB l'una): per il sito si ricomprimono senza perdite in docs/sito/img/manuale.
"""
import html
import os
import posixpath
import re
import unicodedata

from PIL import Image

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
DOCS = os.path.join(RADICE, 'docs')
FONTE = os.path.join(DOCS, 'manuale')
IMG_SITO = os.path.join(DOCS, 'sito', 'img', 'manuale')
REPO = 'https://github.com/luigismith/stame/blob/main/'
GITHUB = REPO + 'docs/manuale/'

# pagina, fonte, titolo breve, descrizione per i motori di ricerca
PAGINE = [
    ('manuale.html', 'manuale.md', 'Manuale',
     "Il manuale d'uso di Stame: la postazione, gli accordi, ogni controllo con i suoi gesti, il looper, "
     "i Beat, il macro pad, la drum machine dal vivo, le pagine e il menu della Flip."),
    ('prontuario.html', 'prontuario.md', 'Prontuario',
     'Il prontuario di Stame: tutti i comandi di MPK mini IV, macro pad e Miyoo Flip in una pagina da stampare.'),
]

MARCHIO = ('<svg viewBox="0 0 100 100" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="3.5" '
           'stroke-linecap="round"><path d="M30 98 L70 98"/><path d="M50 98 C47 62 22 52 16 36"/>'
           '<path d="M50 98 C50 75 50 50 50 30"/><path d="M50 98 C53 62 78 52 84 36"/></g><g fill="currentColor">'
           '<ellipse cx="16" cy="26" rx="10.5" ry="17" transform="rotate(-26 16 26)"/>'
           '<ellipse cx="50" cy="20" rx="10.5" ry="17"/>'
           '<ellipse cx="84" cy="26" rx="10.5" ry="17" transform="rotate(26 84 26)"/></g></svg>')


# ---------------------------------------------------------------------------------------------
# immagini

def immagine(src):
    """percorso nel sito e misure (larghezza, altezza) di un'immagine del manuale, data come in Markdown"""
    nome = os.path.basename(src)
    path = os.path.join(FONTE, src)
    if nome.endswith('.png'):
        os.makedirs(IMG_SITO, exist_ok=True)
        im = Image.open(path).convert('RGB')
        im.save(os.path.join(IMG_SITO, nome), optimize=True)
        return f'sito/img/manuale/{nome}', im.size
    testo = open(path, encoding='utf-8').read(4000)          # SVG: le misure dal viewBox
    m = re.search(r'viewBox="[\d.\-]+ [\d.\-]+ ([\d.]+) ([\d.]+)"', testo)
    wh = (round(float(m.group(1)) * 4), round(float(m.group(2)) * 4)) if m else None
    return 'manuale/' + src.replace('\\', '/'), wh


def figura(src, alt, largo=None):
    url, wh = immagine(src)
    misure = f' width="{wh[0]}" height="{wh[1]}"' if wh else ''
    stile = f' style="max-width:{largo}"' if largo else ''
    classe = ' class="disegno"' if url.endswith('.svg') else ''
    return (f'<figure{classe}><img src="{url}" alt="{html.escape(alt)}"{misure}{stile} loading="lazy">'
            f'<figcaption>{inline(alt)}</figcaption></figure>')


# ---------------------------------------------------------------------------------------------
# Markdown, il sottoinsieme dei due file

def inline(t):
    out = []
    for p in re.split(r'(`[^`]+`)', t):
        if len(p) >= 2 and p[0] == '`' and p[-1] == '`':
            out.append('<code>' + html.escape(p[1:-1], quote=False) + '</code>')
            continue
        s = html.escape(p, quote=False)
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'(?<![\w*])\*(?![\s*])(.+?)(?<![\s*])\*(?![\w*])', r'<em>\1</em>', s)
        s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', lambda m: f'<a href="{collegamento(m.group(2))}">{m.group(1)}</a>', s)
        out.append(s)
    return ''.join(out)


def collegamento(url):
    """i link fra i due documenti restano nel sito; gli altri file del repo vanno su GitHub"""
    if re.match(r'[a-z]+:', url) or url.startswith('#'):
        return url
    base, _, ancora = url.partition('#')
    if base in ('manuale.md', 'prontuario.md'):
        return base.replace('.md', '.html') + ('#' + ancora if ancora else '')
    return REPO + posixpath.normpath('docs/manuale/' + base) + ('#' + ancora if ancora else '')


def slug(t):
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')


RE_VOCE = re.compile(r'^( *)([-*]|\d+\.) +(.*)$')
RE_IMG = re.compile(r'^!\[([^\]]*)\]\(([^)\s]+)\)$')


def rientro(riga):
    return len(riga) - len(riga.lstrip(' '))


def elenco(righe, i):
    """l'elenco che comincia a righe[i], con quelli annidati; torna (html, indice dopo l'elenco)"""
    m = RE_VOCE.match(righe[i])
    livello, ordinato = len(m.group(1)), m.group(2)[0].isdigit()
    voci = []
    while i < len(righe):
        m = RE_VOCE.match(righe[i])
        if not m or len(m.group(1)) != livello or m.group(2)[0].isdigit() != ordinato:
            break
        testo, figli = m.group(3), []
        i += 1
        while i < len(righe) and righe[i].strip() and rientro(righe[i]) > livello:
            if RE_VOCE.match(righe[i]):
                h, i = elenco(righe, i)
                figli.append(h)
            else:
                testo += ' ' + righe[i].strip()
                i += 1
        voci.append(f'<li>{inline(testo)}{"".join(figli)}</li>')
        # una riga vuota fra due voci dello stesso elenco non lo chiude
        if i + 1 < len(righe) and not righe[i].strip():
            m = RE_VOCE.match(righe[i + 1])
            if m and len(m.group(1)) == livello and m.group(2)[0].isdigit() == ordinato:
                i += 1
    tag = 'ol' if ordinato else 'ul'
    return f'<{tag}>' + ''.join(voci) + f'</{tag}>', i


def celle(riga):
    return [c.strip() for c in riga.strip().strip('|').split('|')]


def tabella(righe, i):
    testa = celle(righe[i])
    i += 2                                                       # la riga dopo è |---|---|
    corpo = []
    while i < len(righe) and righe[i].startswith('|'):
        corpo.append(celle(righe[i]))
        i += 1
    h = '<div class="scorri"><table class="tabella"><thead><tr>'
    h += ''.join(f'<th>{inline(c)}</th>' for c in testa) + '</tr></thead><tbody>'
    for r in corpo:
        h += '<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>'
    return h + '</tbody></table></div>', i


def converti(md):
    """(titolo, html del corpo, indice [(id, titolo)] delle sezioni ##)"""
    righe = md.replace('\r\n', '\n').split('\n')
    titolo, blocchi, indice = '', [], []
    i = 0
    while i < len(righe):
        r = righe[i]
        s = r.strip()
        if not s:
            i += 1
            continue
        m = re.match(r'^(#{1,4}) +(.*)$', r)
        if m:
            n, testo = len(m.group(1)), m.group(2).strip()
            if n == 1:
                titolo = testo
            else:
                ident = slug(testo)
                if n == 2:
                    indice.append((ident, testo))
                blocchi.append(f'<h{n} id="{ident}">{inline(testo)}</h{n}>')
            i += 1
        elif RE_IMG.match(s):
            m = RE_IMG.match(s)
            blocchi.append(figura(m.group(2), m.group(1)))
            i += 1
        elif s.startswith('<img'):
            attr = dict(re.findall(r'(\w+)="([^"]*)"', s))
            blocchi.append(figura(attr['src'], attr.get('alt', ''), attr.get('width')))
            i += 1
        elif s.startswith('|') and i + 1 < len(righe) and re.match(r'^\|[\s|:-]+\|$', righe[i + 1].strip()):
            h, i = tabella(righe, i)
            blocchi.append(h)
        elif RE_VOCE.match(r):
            h, i = elenco(righe, i)
            blocchi.append(h)
        else:                                                    # paragrafo: un a capo nel sorgente resta un a capo
            par = []
            while i < len(righe) and righe[i].strip() and not re.match(r'^(#|\||!\[|<img)', righe[i].strip()) \
                    and not RE_VOCE.match(righe[i]):
                par.append(inline(righe[i].strip()))
                i += 1
            blocchi.append('<p>' + '<br>\n'.join(par) + '</p>')
    return titolo, '\n'.join(blocchi), indice


# ---------------------------------------------------------------------------------------------
# la pagina

def pagina(nome, fonte, breve, descrizione):
    titolo, corpo, indice = converti(open(os.path.join(FONTE, fonte), encoding='utf-8').read())
    altra = [p for p in PAGINE if p[0] != nome][0]
    h1 = titolo.split('—', 1)[-1].strip()
    h1 = h1[:1].upper() + h1[1:]
    nav = ''
    if len(indice) > 4:                                          # il manuale: l'indice delle sezioni
        voci = ''.join(f'<li><a href="#{i}">{inline(t)}</a></li>' for i, t in indice)
        nav = f'<nav class="indice" aria-label="Indice"><span class="etichetta">Indice</span><ol>{voci}</ol></nav>'
    stampa = ('<button type="button" class="bottone" onclick="window.print()">Stampa</button>'
              if nome == 'prontuario.html' else '')
    return f'''<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Stame · {breve.lower()}</title>
<meta name="description" content="{html.escape(descrizione)}">
<meta property="og:title" content="Stame · {breve.lower()}">
<meta property="og:description" content="{html.escape(descrizione)}">
<meta property="og:image" content="https://luigismith.github.io/stame/sito/img/plancia_giorno.png">
<meta property="og:type" content="article">
<meta name="theme-color" content="#CED4C2">
<link rel="icon" type="image/png" href="sito/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DotGothic16&family=IBM+Plex+Sans:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="sito/stame.css">
<script>
/* il tema scelto l'ultima volta, prima del primo disegno */
try {{ var t = localStorage.getItem('stame-tema'); if (t) document.documentElement.dataset.theme = t; }} catch (e) {{}}
</script>
</head>
<body class="documento-pagina">
<!-- generata da tools/sito_manuale.py a partire da docs/manuale/{fonte}: si modifica il Markdown, non questa pagina -->

<header class="barra">
  <div class="contenitore">
    <a class="marchio" href="index.it.html" aria-label="Stame, pagina iniziale">
      {MARCHIO}
      STAME
    </a>
    <nav aria-label="Pagine">
      <a href="{nome}" aria-current="page">{breve}</a><a href="{altra[0]}">{altra[2]}</a><a href="case.it.html">Case</a><a href="index.it.html">Home</a>
    </nav>
    <div class="lingua">
      <button type="button" id="tema" aria-label="Passa dal tema Giorno al tema Notte">Giorno / Notte</button>
    </div>
  </div>
</header>

<main id="inizio">
<section class="sezione">
  <div class="contenitore">
    <div class="testata">
      <span class="etichetta">Stame · {breve.lower()} · in italiano</span>
      <h1>{inline(h1)}</h1>
      <div class="bottoni"><a class="bottone" href="{altra[0]}">{altra[2]}</a><a class="bottone" href="{GITHUB}{fonte}">Il sorgente su GitHub</a>{stampa}</div>
    </div>
    {nav}
    <article class="documento">
{corpo}
    </article>
  </div>
</section>
</main>

<footer class="piede">
  <div class="contenitore">
    <div>Stame · <a href="https://github.com/luigismith/stame">github.com/luigismith/stame</a> · MIT</div>
    <div>Questa pagina viene da <a href="{GITHUB}{fonte}">docs/manuale/{fonte}</a>.</div>
  </div>
</footer>

<script>
(function () {{
  var b = document.getElementById('tema');
  if (!b) return;
  b.addEventListener('click', function () {{
    var r = document.documentElement;
    var cur = r.dataset.theme || 'giorno';
    var next = cur === 'notte' ? 'giorno' : 'notte';
    r.dataset.theme = next;
    try {{ localStorage.setItem('stame-tema', next); }} catch (e) {{}}
  }});
}})();
</script>
</body>
</html>
'''


def main():
    for nome, fonte, breve, descrizione in PAGINE:
        testo = pagina(nome, fonte, breve, descrizione)
        with open(os.path.join(DOCS, nome), 'w', encoding='utf-8', newline='\n') as f:
            f.write(testo)
        print(nome, len(testo), 'byte')
    print('immagini:', len(os.listdir(IMG_SITO)), 'in', os.path.relpath(IMG_SITO, RADICE))


if __name__ == '__main__':
    main()
