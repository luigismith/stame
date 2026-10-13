# Costruisce docs/disegni/stame-plancia-e-controlli.html (poi stampato in PDF con Chrome headless).
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from controlli import mpk_svg, flip_svg, focus_ring_svg, push_timeline_svg, C
from plancia import plancia_svg, PLANCIA_PAGINE

CSS = """
@page { size: A4 landscape; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #fff; color: #1a1a1a;
  font-family: Inter, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 9.2pt; line-height: 1.38; }
.page { width: 297mm; height: 210mm; padding: 11mm 13mm 9mm; position: relative; page-break-after: always; overflow: hidden; }
.page:last-child { page-break-after: auto; }
h1 { font-size: 30pt; margin: 0 0 2mm; letter-spacing: -0.5pt; }
h2 { font-size: 15pt; margin: 0 0 1mm; letter-spacing: -0.2pt; }
h3 { font-size: 10.5pt; margin: 3mm 0 1mm; }
.sub { color: #555; margin: 0 0 4mm; font-size: 9.5pt; }
.foot { position: absolute; bottom: 5mm; left: 13mm; right: 13mm; font-size: 7.5pt; color: #888;
  display: flex; justify-content: space-between; border-top: 0.3mm solid #ddd; padding-top: 1.5mm; }
table { border-collapse: collapse; width: 100%; font-size: 8.2pt; }
th, td { border-bottom: 0.25mm solid #e2e2e2; padding: 1.1mm 1.6mm; text-align: left; vertical-align: top; }
th { background: #f4f4f4; font-weight: 700; }
.cols { display: flex; gap: 7mm; }
.cols > div { flex: 1; min-width: 0; }
.chip { display: inline-block; padding: 0 1.6mm; border-radius: 1.2mm; font-weight: 700; font-size: 7.8pt;
  border: 0.3mm solid; white-space: nowrap; }
.legend { display: flex; flex-wrap: wrap; gap: 2mm 4mm; margin: 2mm 0; font-size: 8pt; }
.legend span.sw { display: inline-block; width: 3.4mm; height: 3.4mm; border-radius: 0.8mm; vertical-align: -0.6mm; margin-right: 1mm; border: 0.3mm solid; }
.box { border: 0.3mm solid #ddd; border-radius: 2mm; padding: 2.5mm 3.5mm; background: #fafafa; }
.warn { border-left: 1.2mm solid #D24343; background: #fdf1f1; padding: 2mm 3.5mm; border-radius: 1mm; }
.note { border-left: 1.2mm solid #2F6FD6; background: #f0f5fe; padding: 2mm 3.5mm; border-radius: 1mm; }
ol, ul { margin: 1mm 0; padding-left: 5mm; }
li { margin: 0.6mm 0; }
kbd { font-family: inherit; font-weight: 700; font-size: 7.8pt; border: 0.3mm solid #bbb; border-bottom-width: 0.6mm;
  border-radius: 1mm; padding: 0 1.2mm; background: #fff; white-space: nowrap; }
.seq { display: flex; align-items: center; gap: 1.5mm; flex-wrap: wrap; margin: 0.8mm 0; }
.seq .arrow { color: #999; }
.big { font-size: 10pt; }
.muted { color: #777; }
"""

def chip(kind, label):
    s, f = C[kind]
    return f'<span class="chip" style="background:{f};border-color:{s}">{label}</span>'

def legend():
    items = [('tipo', 'tipi di accordo'), ('ext', 'estensioni'), ('rot', 'rotazione di un encoder'),
             ('fun', 'pulsante di un encoder'), ('loop', 'looper'), ('nav', 'fuoco e navigazione'),
             ('push', 'PUSH (pressione delle manopole)'), ('perf', 'esecuzione'), ('off', 'non usato da Stame')]
    return '<div class="legend">' + ''.join(
        f'<span><span class="sw" style="background:{C[k][1]};border-color:{C[k][0]}"></span>{t}</span>' for k, t in items) + '</div>'

def page(body, n, total):
    return (f'<section class="page">{body}<div class="foot"><span>Stame · plancia e controlli · bozza 1 · 13/10/2026</span>'
            f'<span>{n} / {total}</span></div></section>')

def k(t):
    return '<kbd>' + t.replace('<', '&lt;').replace('>', '&gt;') + '</kbd>'

PAGES = []

# 1 — copertina
PAGES.append(f"""
<div style="display:flex;gap:10mm;height:100%">
 <div style="flex:1.05">
  <div class="muted" style="font-weight:700;letter-spacing:1pt;font-size:8pt">CLONE FEDELE DELL'ORCHID · VERSIONE MIYOO FLIP</div>
  <h1>Stame</h1>
  <p class="sub big">Come appare sulla Miyoo Flip e come si suona con la Akai MPK mini Plus.<br>
  Disegni e ragionamento sui controlli, da leggere insieme alla specifica in <code>docs/specifica/</code>.</p>
  <h3>Tre idee guida</h3>
  <ol>
   <li><b>Il comportamento è quello dell'Orchid; lo schermo no.</b> Sulla Flip non si copia l'OLED 128×128: la plancia
   da 640×480 mostra tutto quello che serve, o è utile vedere, mentre si suona (decisione di Luigi del 13/10).</li>
   <li><b>I pad sono gli 8 tasti accordo dell'Orchid</b>, nella stessa disposizione: sopra Dim, Min, Maj, Sus;
   sotto 6, m7, M7, 9. È il modo normale della MPK (banco A).</li>
   <li><b>Ogni funzione ha almeno una strada senza cambiare banco.</b> Il banco B è comodo, ma è una «pagina»:
   con il banco B attivo i pad non fanno più gli accordi.</li>
  </ol>
  <h3>Cosa c'è in queste pagine</h3>
  <table>
   <tr><td>2–3</td><td>La plancia sulla Flip: schermata principale e stati con una lista o un menu aperto</td></tr>
   <tr><td>4</td><td>MPK mini Plus, banco A: il modo per suonare</td></tr>
   <tr><td>5</td><td>MPK mini Plus, banco B e trasporto: i pulsanti dell'Orchid</td></tr>
   <tr><td>6</td><td>Tasti della Flip: lo schema a fuoco e il modo tascabile</td></tr>
   <tr><td>7</td><td>I quattro gesti degli encoder: come si fanno senza manopole premibili</td></tr>
   <tr><td>8</td><td>Ogni controllo dell'Orchid, gesto per gesto: dove sta sulla MPK e sulla Flip</td></tr>
   <tr><td>9</td><td>Ricette: le operazioni di tutti i giorni</td></tr>
   <tr><td>10</td><td>Preparazione della MPK e punti da verificare</td></tr>
  </table>
 </div>
 <div style="flex:1;display:flex;flex-direction:column;gap:4mm;justify-content:center">
  {plancia_svg('principale', width='100%')}
  <div class="muted" style="font-size:8pt;text-align:center">La plancia principale (pagina 2), a grandezza ridotta.</div>
  <div class="note"><b>Come si dispone il tavolo.</b> Flip a sinistra della MPK, un po' arretrata e con lo schermo inclinato.
  La mano sinistra suona i pad e raggiunge il tasto <b>X</b> della Flip (PUSH); la destra suona la tastiera e gira le manopole,
  che sulla MPK stanno a destra. È un suggerimento, da provare con le mani.</div>
 </div>
</div>
""")

# 2–3 — plancia (dal modulo plancia.py)
for body in PLANCIA_PAGINE:
    PAGES.append(body)

# 4 — MPK banco A
PAGES.append(f"""
<h2>MPK mini Plus — banco A: si suona</h2>
<p class="sub">È lo stato normale: tasto BANK sul banco A. La mano sinistra sta sui pad come sui tasti accordo dell'Orchid, la destra sulla tastiera.</p>
{mpk_svg('A')}
{legend()}
<div class="cols" style="margin-top:1mm">
 <div>
  <h3>Accordi</h3>
  <ul>
   <li><b>Fila alta</b>: i 4 tipi, Dim · Min · Maj · Sus. <b>Fila bassa</b>: le 4 estensioni, 6 · m7 · M7 · 9. Stessa disposizione
   dei tasti a sinistra dell'Orchid.</li>
   <li>Si tengono tipo ed estensione con la sinistra e si preme un tasto con la destra. Come sull'Orchid, cambiare tipo
   con il tasto già premuto vale dal tasto successivo.</li>
   <li>Combinazioni di più tipi = Secret Chords (se attivi in Options).</li>
  </ul>
 </div>
 <div>
  <h3>Manopole: sempre attive, in tutti e due i banchi</h3>
  <ul>
   <li>K1–K8 ruotano gli 8 encoder più usati: Chord Voicing, Bass Voicing, Sound, Perform / FX, Key, BPM, Volume.</li>
   <li>Sono encoder infiniti in modo <b>Relative</b>: nessun salto di valore, e lo schermo mostra sempre il valore vero.</li>
   <li>Per <b>premerle</b> si tiene <b>X</b> sulla Flip (o B8 nel banco B) e si tocca la manopola: pagina 7.</li>
  </ul>
 </div>
 <div>
  <h3>Trasporto e joystick: sempre attivi</h3>
  <ul>
   <li>{k('REC')} pulsante Loop · {k('STOP')} stop o pausa del loop, tenuto 1 s = Clear · {k('PLAY')} pulsante BPM (beat o metronomo).</li>
   <li>{k('<<')} {k('>>')} e joystick ▲▼ ruotano l'encoder con il <b>fuoco</b> (Bass, Loop, Options e le liste aperte); joystick ▶ conferma, ◀ indietro.</li>
   <li>Ruote e pedale: bend, modulazione e sustain del Sound.</li>
  </ul>
 </div>
</div>
""")

# 5 — MPK banco B
PAGES.append(f"""
<h2>MPK mini Plus — banco B: i pulsanti dell'Orchid</h2>
<p class="sub">Si apre premendo BANK. I pad diventano i pulsanti degli encoder che non hanno una manopola o che si premono spesso. Si torna al banco A con BANK.</p>
{mpk_svg('B')}
<div class="cols" style="margin-top:2mm">
 <div>
  <h3>Cosa fa ogni pad</h3>
  <table>
   <tr><th>Pad</th><th>Premere</th><th>Tenere</th></tr>
   <tr><td>{chip('fun','B1 Key')}</td><td>Key mode on/off</td><td>scelta rapida della tonalità (+ Min = minore)</td></tr>
   <tr><td>{chip('fun','B2 Bass')}</td><td>basso on/off</td><td>1 s: lista dei modi del basso</td></tr>
   <tr><td>{chip('fun','B3 Perform')}</td><td>lista dei modi</td><td>Lock</td></tr>
   <tr><td>{chip('fun','B4 Chord Voicing')}</td><td>Split ↔ Octave</td><td>—</td></tr>
   <tr><td>{chip('loop','B5 Loop')}</td><td>come REC</td><td>2 s: uscita morbida / Save Loop</td></tr>
   <tr><td>{chip('fun','B6 BPM')}</td><td>come PLAY: beat o metronomo</td><td>1 s: tempo in chiave → Beats</td></tr>
   <tr><td>{chip('nav','B7 Options')}</td><td>apre Options</td><td>—</td></tr>
   <tr><td>{chip('push','B8 PUSH')}</td><td colspan="2">come X sulla Flip: tenuto + manopola = manopola premuta</td></tr>
  </table>
 </div>
 <div>
  <h3>Perché il banco B è una «pagina» e non un secondo pannello</h3>
  <div class="warn">La MPK ha <b>8 pad fisici</b>. BANK cambia solo le note che mandano (36–43 nel banco A, 44–51 nel B).
  Con il banco B attivo <b>i pad non fanno più gli accordi</b>, e Stame non sa che banco è attivo finché non arriva una nota
  da un pad. Il LED del tasto BANK cambia colore.</div>
  <h3>Conseguenze per il progetto</h3>
  <ul>
   <li>Tutto quello che si fa dal banco B si può fare <b>anche</b> senza cambiare banco: dal trasporto, dalle manopole con X,
   o dalla Flip con il fuoco (tabella a pagina 8).</li>
   <li>Le funzioni da usare <b>mentre si suona</b> (looper, beat, pressione delle manopole) stanno su comandi
   sempre disponibili: REC, STOP, PLAY e il tasto X della Flip.</li>
   <li>La plancia mostra in che banco <b>sembra</b> essere la MPK (dall'ultima nota dei pad) e la legenda dei pad di quel banco.</li>
   <li>Pad tenuto mentre si cambia banco: che Note Off arriva? Da verificare (pagina 10). Intanto Stame rilascia
   gli accordi tenuti appena vede una nota dell'altro banco.</li>
  </ul>
 </div>
</div>
""")

# 6 — Flip
PAGES.append(f"""
<h2>Tasti della Flip</h2>
<p class="sub">La Flip sta accanto alla MPK. I suoi tasti servono a muoversi nell'interfaccia e a premere le manopole della MPK. Senza MPK si può anche suonare, con il modo tascabile.</p>
<div class="cols">
 <div style="flex:1.25">
  <h3>Schema a fuoco: sempre attivo</h3>
  <div style="text-align:center">{flip_svg('fuoco', width='74%')}</div>
 </div>
 <div style="flex:0.75">
  <h3>Il fuoco</h3>
  <div style="text-align:center">{focus_ring_svg('Loop', width='62%')}</div>
  <p style="margin:1mm 0 0">C'è <b>un solo fuoco</b>, condiviso da Flip e MPK. Lo spostano {k('L1')}/{k('R1')} e la pressione di un
  encoder da qualunque comando: premendo REC, il fuoco va su Loop, e {k('<<')} {k('>>')}, joystick e croce ruotano Loop.
  Se è aperta una lista, il fuoco è sulla lista.</p>
 </div>
</div>
<div class="cols" style="margin-top:1mm">
 <div>
  <table>
   <tr><th>Tasto</th><th>Funzione</th></tr>
   <tr><td>{k('L1')} {k('R1')}</td><td>sposta il fuoco sugli 11 controlli (giro ciclico)</td></tr>
   <tr><td>croce</td><td>ruota l'encoder con il fuoco, o scorre la lista aperta (ripete se tenuta)</td></tr>
   <tr><td>{k('A')}</td><td>preme l'encoder con il fuoco: tocco = premere, tenuto = tenere, tenuto + croce = premere e ruotare</td></tr>
   <tr><td>{k('B')}</td><td>indietro: chiude la lista o l'overlay</td></tr>
  </table>
 </div>
 <div>
  <table>
   <tr><th>Tasto</th><th>Funzione</th></tr>
   <tr><td>{k('X')}</td><td><b>PUSH</b>: tenuto, la manopola della MPK toccata viene premuta</td></tr>
   <tr><td>{k('Y')}</td><td>Bass Voicing premuto: il modificatore (Y + Loop = uscita hard dal loop)</td></tr>
   <tr><td>{k('SELECT')} {k('START')}</td><td>pulsante di Options · pulsante di BPM</td></tr>
   <tr><td>{k('MENU')}</td><td>menu della piattaforma: Panic, Pocket Mode, MPK Status, tema, <b>Quit Stame</b> (unica uscita)</td></tr>
  </table>
 </div>
 <div style="flex:0.95">
  <h3 style="margin-top:0">Modo tascabile (da MENU)</h3>
  <div style="text-align:center">{flip_svg('tascabile', width='72%')}</div>
  <p class="muted" style="margin:0;font-size:7.8pt">Levetta sinistra = nota (12 settori), A = suona, dorsali = tipi, croce = estensioni.
  Spento per default, si spegne da solo quando si collega la MPK.</p>
 </div>
</div>
""")

# 7 — gesti
def seq(*steps):
    out = []
    for i, s in enumerate(steps):
        if i:
            out.append('<span class="arrow">→</span>')
        out.append(s)
    return '<div class="seq">' + ''.join(out) + '</div>'

PAGES.append(f"""
<h2>I quattro gesti degli encoder</h2>
<p class="sub">Ogni encoder dell'Orchid si <b>ruota</b>, si <b>preme</b>, si <b>tiene premuto</b> (1 s; Loop anche 2 s) e si <b>preme e ruota</b>.
Le manopole della MPK non si premono: la pressione la dà il PUSH.</p>
<div class="cols">
 <div>
  <h3>Con la MPK: PUSH = {k('X')} della Flip (o pad B8)</h3>
  <table>
   <tr><th style="width:24%">Gesto</th><th>Come si fa</th><th style="width:30%">Esempio</th></tr>
   <tr><td><b>Ruotare</b></td><td>{seq('gira Kn')}</td><td>K6: cambia tonalità</td></tr>
   <tr><td><b>Premere</b></td><td>{seq(k('X')+' giù', 'tocca Kn', k('X')+' su')}</td><td>X + tocco K6: Key mode on/off</td></tr>
   <tr><td><b>Tenere</b></td><td>{seq(k('X')+' giù', 'tocca Kn', 'aspetta 1 s')}</td><td>X + K3 tenuto: Save / Save As / Delete</td></tr>
   <tr><td><b>Premere e ruotare</b></td><td>{seq(k('X')+' giù', 'tocca Kn', 'gira Kn')}</td><td>X + gira K6: transpose</td></tr>
  </table>
  <div class="note" style="margin-top:2mm">Il primo scatto dopo X <b>sceglie</b> la manopola e non cambia il valore; per 150 ms si ignorano
  i tremolii. Poi ogni scatto della stessa manopola è «premere e ruotare». Girare un'altra manopola con X tenuto
  la ruota normalmente.</div>
  <h3>Nel tempo</h3>
  {push_timeline_svg()}
  <h3>Scorciatoia: pulsante tenuto + la sua manopola</h3>
  <p style="margin:0">Se un encoder ha già un pulsante (PLAY per BPM, B1 per Key…), tenerlo e girare la sua manopola è
  «premere e ruotare»: {k('PLAY')} tenuto + K7 = volume del beat; B1 tenuto + K6 = transpose.</p>
 </div>
 <div>
  <h3>Con la sola Flip: fuoco + {k('A')}</h3>
  <table>
   <tr><th style="width:24%">Gesto</th><th>Come si fa</th></tr>
   <tr><td><b>Ruotare</b></td><td>{seq(k('L1')+'/'+k('R1')+' sul controllo', 'croce')}</td></tr>
   <tr><td><b>Premere</b></td><td>{seq('fuoco sul controllo', 'tocco '+k('A'))}</td></tr>
   <tr><td><b>Tenere</b></td><td>{seq('fuoco sul controllo', k('A')+' tenuto 1 s')}</td></tr>
   <tr><td><b>Premere e ruotare</b></td><td>{seq('fuoco sul controllo', k('A')+' tenuto', 'croce')}</td></tr>
  </table>
  <h3>Combinazioni con Bass Voicing tenuto</h3>
  <p style="margin:0">Sull'Orchid si tiene premuto il Bass Voicing e si preme un altro pulsante. Qui il Bass Voicing premuto è {k('Y')}:</p>
  <ul>
   <li>{k('Y')} + {k('REC')} (o + Loop) = <b>uscita hard dal loop</b></li>
   <li>{k('Y')} + {k('PLAY')} (o + BPM) = <b>batteria da suonare</b> sulla tastiera</li>
   <li>{k('Y')} + B2 (Bass) = basso on/off</li>
  </ul>
  <h3>Liste e menu</h3>
  <p style="margin:0">Una lista aperta prende il fuoco: si scorre con {k('<<')} {k('>>')}, joystick ▲▼ o croce; si conferma con joystick ▶ o {k('A')};
  si torna indietro con joystick ◀ o {k('B')}. Lo scorrimento che continua tenendo premuto parte dopo 400 ms, poi un passo ogni 120 ms.</p>
 </div>
</div>
""")

# 8 — tabella delle strade
ROWS = [
  ('Chord Voicing', 'K1', 'voicing ±1 semitono', 'X + tocco K1 · B4', 'Split ↔ Octave', '—', '—'),
  ('Bass Voicing', 'K2', 'ottava del basso', 'X + tocco K2 · Y', 'modificatore', 'Y tenuto', '—'),
  ('Sound', 'K3', 'suono per numero', 'X + tocco K3', 'lista per nome', 'X + K3 1 s', 'Save / Save As / Delete'),
  ('Perform', 'K4', 'modo e parametro', 'X + tocco K4 · B3', 'lista dei modi', 'X + K4 1 s · B3 tenuto', 'Lock'),
  ('FX', 'K5', 'effetto principale', 'X + tocco K5', 'lista degli effetti', 'X + K5 1 s', 'Lock'),
  ('Key', 'K6', 'tonalità', 'X + tocco K6 · B1', 'Key mode on/off', 'X + K6 1 s · B1 tenuto', 'scelta rapida; X + gira K6 = transpose'),
  ('Bass', '&lt;&lt; &gt;&gt; / joy (fuoco)', 'suono di basso', 'B2 · fuoco + A', 'basso on/off', 'B2 1 s · A 1 s', 'lista dei modi'),
  ('Loop', '&lt;&lt; &gt;&gt; / joy (fuoco)', 'Waiting Room, battute', 'REC · B5', 'entra, Rec, Stop', 'REC 2 s', 'uscita morbida / Save Loop'),
  ('BPM', 'K7', 'tempo', 'PLAY · B6 · START', 'beat o metronomo', 'PLAY 1 s', 'tempo in chiave → Beats; PLAY + K7 = volume beat'),
  ('Volume', 'K8', 'volume 0–99', 'X + tocco K8', 'batteria', '—', 'X + gira K8 = volume basso'),
  ('Options', '&lt;&lt; &gt;&gt; / joy (fuoco)', 'scorre', 'SELECT · B7', 'apre, entra, conferma', '—', '—'),
]
rows = ''.join(f'<tr><td><b>{a}</b></td><td>{b}</td><td class="muted">{c}</td><td>{d}</td><td class="muted">{e}</td><td>{f}</td><td class="muted">{g}</td></tr>'
               for a, b, c, d, e, f, g in ROWS)
PAGES.append(f"""
<h2>Ogni controllo dell'Orchid, gesto per gesto</h2>
<p class="sub">Dove si trova ogni gesto sulla MPK e sulla Flip. Dalla sola Flip si arriva sempre a tutto con <b>fuoco + croce / A</b>, quindi qui la Flip compare solo quando ha un tasto dedicato.</p>
<table>
 <tr><th>Controllo</th><th>Ruotare</th><th>→ effetto</th><th>Premere</th><th>→ effetto</th><th>Tenere</th><th>→ effetto</th></tr>
 {rows}
</table>
<div class="cols" style="margin-top:3mm">
 <div class="box"><b>Lettura.</b> «X + tocco K3» = tieni X della Flip, tocca la manopola K3, rilascia X. «B4» = pad 4 del banco B.
 «fuoco + A» = porta il fuoco sul controllo con L1/R1 e premi A sulla Flip. Per «premere e ruotare» vale la regola di pagina 7.</div>
 <div class="box"><b>Controlli senza manopola.</b> Bass, Loop e Options non hanno una manopola sulla MPK: si premono dal trasporto o dal banco B,
 e si ruotano con {k('<<')} {k('>>')} o con il joystick dopo averli premuti, perché la pressione porta lì il fuoco.</div>
</div>
""")

# 9 — ricette
def ricetta(titolo, *righe):
    return f'<div class="box" style="margin-bottom:2.2mm"><b>{titolo}</b><ul style="margin-top:0.6mm">' + ''.join(f'<li>{r}</li>' for r in righe) + '</ul></div>'

PAGES.append(f"""
<h2>Ricette</h2>
<p class="sub">Le operazioni più comuni, con la strada più corta. Tra parentesi l'alternativa dalla Flip.</p>
<div class="cols">
 <div>
  {ricetta('Suonare un accordo', 'Banco A: tieni il tipo (e l\'estensione) con la sinistra, premi un tasto con la destra.',
           'Key mode accesa: un tasto senza pad dà l\'accordo diatonico della tonalità.',
           'Sposta le note più in alto o più in basso: gira <b>K1</b>. Split ↔ Octave: X + tocco K1.')}
  {ricetta('Cambiare suono', 'Gira <b>K3</b>: un suono per scatto, nell\'ordine dei numeri.',
           'Per nome: X + tocco K3 apre la lista → joystick ▲▼ → joystick ▶. (Fuoco su Sound, A, croce, A.)')}
  {ricetta('Salvare il suono modificato', 'X + K3 tenuto 1 s → Save / Save As / Delete → joystick ▶.')}
  {ricetta('Tonalità', 'Gira <b>K6</b> per scegliere; X + tocco K6 (o B1) accende o spegne la Key mode.',
           'Transpose: X tenuto + gira K6.', 'Scelta rapida: X + K6 tenuto 1 s, poi un tasto (con Min tenuto per la minore).')}
 </div>
 <div>
  {ricetta('Strum, Arp, Harp…', 'Gira <b>K4</b>: modo e parametro insieme; tutto a sinistra = Off.',
           'Lista dei modi: X + tocco K4. Lock: X + K4 tenuto.')}
  {ricetta('Basso', 'On/off: B2 nel banco B. (Fuoco su Bass, A.)', 'Modo: B2 tenuto 1 s. Suono: dopo B2, gira con &lt;&lt; &gt;&gt;.',
           'Ottava: gira <b>K2</b>.')}
  {ricetta('Beat e tempo', '<b>PLAY</b> avvia e ferma il beat (o il metronomo). <b>K7</b> cambia il tempo.',
           'Scegliere il beat: PLAY tenuto 1 s → tempo in chiave → Beats.', 'Volume del beat: PLAY tenuto + gira K7.')}
 </div>
 <div>
  {ricetta('Looper', '<b>REC</b> apre la Waiting Room; &lt;&lt; &gt;&gt; sceglie le battute (Free, 1, 2, 4, 8, 16).',
           '<b>REC</b> di nuovo: registra, con una battuta di count-in (in Free parte alla prima nota).',
           'In riproduzione REC esegue la voce evidenziata del menu del loop (Overdub, Play, Clear), che si sceglie con &lt;&lt; &gt;&gt;.',
           '<b>STOP</b>: chiude registrazione o overdub, in riproduzione mette in pausa; tenuto 1 s = Clear.',
           'Uscita morbida: REC tenuto 2 s. Uscita hard, che cancella il loop non salvato: Y + REC.')}
  {ricetta('Options', 'SELECT sulla Flip (o B7) → joystick ▲▼ → ▶ entra → ◀ indietro.')}
  {ricetta('Emergenza: note appese', '<b>X + STOP</b> = Panic. Oppure MENU → Panic.')}
  {ricetta('Uscire', 'MENU → Quit Stame. Salva lo stato e torna a spruceOS.')}
 </div>
</div>
""")

# 10 — preparazione e verifiche
PAGES.append(f"""
<h2>Preparazione della MPK e punti da verificare</h2>
<div class="cols">
 <div>
  <h3>Una volta sola, prima di suonare</h3>
  <ol>
   <li><b>Programma «STAME»</b> sulla MPK, caricato dall'editor sul PC (proposta nella guida alla Plus §17.3):
   manopole in <b>Relative</b> su CC 70–77; joystick in <b>Dual CC</b> con un CC diverso per ogni verso (13/12 e 3/2);
   pad banco A note 36–43, banco B 44–51, canale 10; colori diversi per tipi, estensioni e pulsanti.</li>
   <li><b>Global → Trpt = ON/OFF</b> (SHIFT + STOP). È un'impostazione <b>globale</b>, non del programma:
   senza, i tasti di trasporto non mandano il rilascio e i gesti «tenere» su REC, STOP e PLAY non funzionano.</li>
   <li>Banco A attivo (LED del tasto BANK).</li>
   <li>Collegamento: hub USB-C <b>alimentato</b> tra Flip e MPK. Mai forzare la porta OTG della Flip in modo host.</li>
   <li>Pedale sustain nel jack della MPK.</li>
  </ol>
  <h3>Da non usare mentre Stame è aperta</h3>
  <p style="margin:0">ARP, CHORDS, SCALES, NOTE REPEAT e SEQ lavorano dentro la MPK e generano note per conto loro.
  Stame non li vede e non li può spegnere: le note in più si sommerebbero agli accordi di Stame. OCT −/+ si può
  usare, ma non serve: conta solo il nome della nota.</p>
 </div>
 <div>
  <h3>Da verificare con le mani e con la MPK di Luigi</h3>
  <table>
   <tr><th>Punto</th><th>Perché conta</th></tr>
   <tr><td>Pad tenuto mentre si preme BANK: che Note Off arriva?</td><td>Accordi appesi o rilasciati per sbaglio</td></tr>
   <tr><td>I colori dei pad si possono dare per banco?</td><td>Vedere a colpo d'occhio se si è in A o in B</td></tr>
   <tr><td>Accelerazione delle manopole in Relative</td><td>Precisione del Chord Voicing (1 scatto = 1 semitono)</td></tr>
   <tr><td>Joystick: zona morta e ritorno al centro</td><td>Scorrimento delle liste senza scatti in più</td></tr>
   <tr><td>LED di REC, PLAY, STOP pilotabili dall'host</td><td>Stato del looper e del beat sulla MPK</td></tr>
   <tr><td>Posizione di X sulla Flip appoggiata a sinistra</td><td>X + manopola deve essere un gesto comodo</td></tr>
   <tr><td>Posizione di MENU, SELECT, START sulla Flip</td><td>Il disegno a pagina 6 è schematico</td></tr>
   <tr><td>Pocket Mode: levetta a 12 settori</td><td>Precisione nello scegliere la nota senza guardare</td></tr>
  </table>
  <p class="muted" style="font-size:7.8pt;margin-top:2mm">L'elenco completo delle verifiche (Orchid, MPK, Flip) è in
  <code>docs/specifica/90-questioni-aperte.md</code>; i test della MPK sono nella guida alla Plus §18.</p>
 </div>
</div>
""")

def build(out):
    total = len(PAGES)
    html = ('<!doctype html><html lang="it"><head><meta charset="utf-8"><title>Stame — plancia e controlli</title>'
            f'<style>{CSS}</style></head><body>' + ''.join(page(b, i + 1, total) for i, b in enumerate(PAGES)) + '</body></html>')
    open(out, 'w', encoding='utf-8').write(html)

if __name__ == '__main__':
    build(sys.argv[1])
