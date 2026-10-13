# Costruisce docs/disegni/stame-plancia-e-controlli.html (poi stampato in PDF con Chrome headless).
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from controlli import mpk_svg, flip_svg, focus_ring_svg, C
from pad_case import pad_svg, twin_svg, tk_timeline_svg, case_top_svg, case_side_svg, wiring_svg
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
             ('push', 'PUSH (riserva senza pad)'), ('warn', 'Panic'), ('perf', 'esecuzione'), ('off', 'non usato da Stame')]
    return '<div class="legend">' + ''.join(
        f'<span><span class="sw" style="background:{C[k][1]};border-color:{C[k][0]}"></span>{t}</span>' for k, t in items) + '</div>'

def page(body, n, total):
    return (f'<section class="page">{body}<div class="foot"><span>Stame · plancia e controlli · bozza 2, con il macro pad · 13/10/2026</span>'
            f'<span>{n} / {total}</span></div></section>')

def k(t):
    return '<kbd>' + t.replace('<', '&lt;').replace('>', '&gt;') + '</kbd>'

PAGES = []

def seq(*steps):
    out = []
    for i, s in enumerate(steps):
        if i:
            out.append('<span class="arrow">→</span>')
        out.append(s)
    return '<div class="seq">' + ''.join(out) + '</div>'

def ricetta(titolo, *righe):
    return f'<div class="box" style="margin-bottom:2mm"><b>{titolo}</b><ul style="margin-top:0.5mm">' + ''.join(f'<li>{r}</li>' for r in righe) + '</ul></div>'

# 1 — copertina
PAGES.append(f"""
<div style="display:flex;gap:10mm;height:100%">
 <div style="flex:1.05">
  <div class="muted" style="font-weight:700;letter-spacing:1pt;font-size:8pt">CLONE FEDELE DELL'ORCHID · VERSIONE MIYOO FLIP</div>
  <h1>Stame</h1>
  <p class="sub big">Come appare sulla Miyoo Flip e come si suona con la Akai MPK mini Plus e il macro pad BRIMFORD.
  Con una bozza del case che tiene tutto insieme. Da leggere con la specifica in <code>docs/specifica/</code>.</p>
  <h3>Quattro idee guida</h3>
  <ol>
   <li><b>Il comportamento è quello dell'Orchid; lo schermo no.</b> La plancia 640×480 mostra tutto quello che serve,
   o è utile vedere, mentre si suona.</li>
   <li><b>I pad della MPK sono gli 8 tasti accordo dell'Orchid</b>, nella stessa disposizione, e restano sempre così.</li>
   <li><b>Manopole della MPK e tasti del pad sono due griglie gemelle.</b> Stessa posizione = stesso encoder:
   la manopola ruota, il tasto preme, tasto tenuto + manopola = premere e ruotare. Come un encoder dell'Orchid,
   diviso in due.</li>
   <li><b>Tutto in un case</b>: MPK davanti, pad a destra dove sull'Orchid stanno le manopole del voicing,
   Flip dietro come schermo.</li>
  </ol>
  <h3>Cosa c'è in queste pagine</h3>
  <table>
   <tr><td>2–3</td><td>La plancia sulla Flip</td></tr>
   <tr><td>4</td><td>MPK mini Plus: si suona</td></tr>
   <tr><td>5</td><td>Macro pad: i pulsanti dell'Orchid e le manopole del voicing</td></tr>
   <tr><td>6</td><td>Tasti della Flip</td></tr>
   <tr><td>7</td><td>I quattro gesti degli encoder</td></tr>
   <tr><td>8</td><td>Ogni controllo dell'Orchid, gesto per gesto</td></tr>
   <tr><td>9</td><td>Ricette</td></tr>
   <tr><td>10–11</td><td>Il case: disposizione, sezione, cablaggio, parti</td></tr>
   <tr><td>12</td><td>Preparazione e punti da verificare</td></tr>
  </table>
 </div>
 <div style="flex:1;display:flex;flex-direction:column;gap:3mm;justify-content:center">
  {plancia_svg('principale', width='100%')}
  {case_top_svg(width='100%')}
 </div>
</div>
""")

for body in PLANCIA_PAGINE:
    PAGES.append(body)

# 4 — MPK
PAGES.append(f"""
<h2>MPK mini Plus — si suona</h2>
<p class="sub">Banco A sempre attivo. La mano sinistra sta sui pad come sui tasti accordo dell'Orchid, la destra sulla tastiera e sulle manopole.</p>
{mpk_svg('A')}
{legend()}
<div class="cols" style="margin-top:1mm">
 <div>
  <h3>Accordi</h3>
  <ul>
   <li><b>Fila alta</b>: Dim · Min · Maj · Sus. <b>Fila bassa</b>: 6 · m7 · M7 · 9. Come i tasti a sinistra dell'Orchid.</li>
   <li>Tipo (ed estensione) con la sinistra, un tasto con la destra. Più tipi insieme = Secret Chords, se attivi.</li>
  </ul>
 </div>
 <div>
  <h3>Manopole: la rotazione degli encoder</h3>
  <ul>
   <li><b>K1 Sound · K2 Perform · K3 FX · K4 Key / K5 Bass · K6 Loop · K7 BPM · K8 Volume</b>: la stessa griglia dei tasti T1–T8 del pad.</li>
   <li>Chord Voicing e Bass Voicing sono passati alle manopole del pad (pagina 5).</li>
  </ul>
 </div>
 <div>
  <h3>Trasporto e joystick</h3>
  <ul>
   <li>{k('REC')} Loop · {k('PLAY')} BPM (beat) · {k('STOP')} stop o pausa del loop, tenuto 1 s = Clear.</li>
   <li>{k('<<')} {k('>>')} e joystick ▲▼ ruotano il fuoco; joystick ▶ conferma, ◀ indietro.</li>
   <li><b>Banco B</b>: resta come riserva quando il pad non c'è (B1 Key … B8 PUSH, come nella bozza 1).</li>
  </ul>
 </div>
</div>
""")

# 5 — macro pad
PAGES.append(f"""
<h2>Macro pad — i pulsanti dell'Orchid e le manopole del voicing</h2>
<p class="sub">BRIMFORD CusKeyboard0227: 12 tasti 4×3 e 3 manopole premibili, collegato con il cavo USB-C. Per Stame è una tastiera USB: lo legge da evdev, in esclusiva.</p>
<div class="cols">
 <div style="flex:0.8">{pad_svg('100%')}</div>
 <div style="flex:1.2">
  <h3 style="margin-top:0">Le due griglie gemelle</h3>
  {twin_svg('100%')}
  <table style="margin-top:2mm">
   <tr><th>Comando</th><th>Funzione</th></tr>
   <tr><td>{chip('fun','T1–T8')}</td><td>pulsanti di Sound, Perform, FX, Key / Bass, Loop, BPM, Volume: tocco = premere, 1 s = tenere</td></tr>
   <tr><td>{chip('nav','T9 Options')} {chip('nav','T10 Back')}</td><td>apre Options · indietro (chiude la lista o l'overlay)</td></tr>
   <tr><td>{chip('perf','T11 Menu')} {chip('warn','T12 Panic')}</td><td>menu della piattaforma (Quit, Learn Pad…) · Panic, solo tenuto 1 s</td></tr>
   <tr><td>{chip('rot','M')}</td><td><b>Chord Voicing</b>: ±1 semitono per scatto; premuta = Split ↔ Octave</td></tr>
   <tr><td>{chip('fun','m1')}</td><td><b>Bass Voicing</b>: ottava del basso; tenuta = il modificatore delle combinazioni</td></tr>
   <tr><td>{chip('nav','m2')}</td><td><b>liste</b>: scorre la lista aperta o ruota il controllo con il fuoco; premuta = conferma</td></tr>
  </table>
 </div>
</div>
<div class="cols" style="margin-top:2mm">
 <div class="note"><b>Perché il pad a destra.</b> Sull'Orchid le manopole del voicing stanno a destra, accanto alla tastiera: qui la manopola grande
 sta sotto la mano che suona i tasti. La sinistra resta sui pad degli accordi. Per «tasto + manopola» si usano due mani: la destra sul tasto,
 la sinistra sulla manopola della MPK.</div>
 <div class="box"><b>Codici da programmare</b> (una volta, dal PC): T1–T12 = F13–F24; M = KP7 / KP8 / KP9 (antiorario / premuta / orario);
 m1 = KP4 / KP5 / KP6; m2 = KP1 / KP2 / KP3. Se il software non li accetta: MENU → <b>Learn Pad</b>. RGB spento, per consumare meno.</div>
</div>
""")

# 6 — Flip
PAGES.append(f"""
<h2>Tasti della Flip</h2>
<p class="sub">Nel case la Flip fa soprattutto da schermo. I suoi tasti restano raggiungibili: servono per muoversi nei menu, e da soli fanno tutto anche senza MPK e pad.</p>
<div class="cols">
 <div style="flex:1.25">
  <h3>Schema a fuoco: sempre attivo</h3>
  <div style="text-align:center">{flip_svg('fuoco', width='74%')}</div>
 </div>
 <div style="flex:0.75">
  <h3>Il fuoco</h3>
  <div style="text-align:center">{focus_ring_svg('Loop', width='62%')}</div>
  <p style="margin:1mm 0 0">Un solo fuoco, condiviso da Flip, MPK e pad. Lo spostano {k('L1')}/{k('R1')} e la pressione di un encoder da qualunque comando.
  Con una lista aperta il fuoco è sulla lista.</p>
 </div>
</div>
<div class="cols" style="margin-top:1mm">
 <div>
  <table>
   <tr><th>Tasto</th><th>Funzione</th></tr>
   <tr><td>{k('L1')} {k('R1')}</td><td>sposta il fuoco sugli 11 controlli</td></tr>
   <tr><td>croce</td><td>ruota il controllo con il fuoco o scorre la lista</td></tr>
   <tr><td>{k('A')} / {k('B')}</td><td>premi (tenuto = tenere, tenuto + croce = premere e ruotare) / indietro</td></tr>
  </table>
 </div>
 <div>
  <table>
   <tr><th>Tasto</th><th>Funzione</th></tr>
   <tr><td>{k('X')}</td><td>PUSH: <b>riserva</b> per premere le manopole della MPK quando il pad non c'è</td></tr>
   <tr><td>{k('Y')}</td><td>Bass Voicing premuto (come m1 tenuta)</td></tr>
   <tr><td>{k('SELECT')} {k('START')} {k('MENU')}</td><td>Options · BPM · menu della piattaforma (unica uscita: Quit Stame)</td></tr>
  </table>
 </div>
 <div style="flex:0.95">
  <h3 style="margin-top:0">Modo tascabile (da MENU)</h3>
  <div style="text-align:center">{flip_svg('tascabile', width='72%')}</div>
 </div>
</div>
""")

# 7 — gesti
PAGES.append(f"""
<h2>I quattro gesti degli encoder</h2>
<p class="sub">Ogni encoder dell'Orchid si <b>ruota</b>, si <b>preme</b>, si <b>tiene premuto</b> (1 s; Loop anche 2 s) e si <b>preme e ruota</b>.
Con il pad i quattro gesti diventano naturali: manopola della MPK + tasto del pad nella stessa posizione.</p>
<div class="cols">
 <div>
  <h3>Con MPK e pad</h3>
  <table>
   <tr><th style="width:26%">Gesto</th><th>Come si fa</th><th style="width:32%">Esempio</th></tr>
   <tr><td><b>Ruotare</b></td><td>{seq('gira Kn')}</td><td>K4: cambia tonalità</td></tr>
   <tr><td><b>Premere</b></td><td>{seq('tocca Tn')}</td><td>T4: Key mode on/off</td></tr>
   <tr><td><b>Tenere</b></td><td>{seq('tieni Tn 1 s')}</td><td>T1: Save / Save As / Delete</td></tr>
   <tr><td><b>Premere e ruotare</b></td><td>{seq('tieni Tn', 'gira Kn')}</td><td>T4 + K4: transpose</td></tr>
  </table>
  <h3>Nel tempo</h3>
  {tk_timeline_svg()}
  <h3>Le manopole del pad</h3>
  <p style="margin:0">M e m1 sono encoder veri: si girano e si premono, come i due dial dell'Orchid. m2 è la manopola delle liste:
  gira = scorre, premuta = conferma.</p>
 </div>
 <div>
  <h3>Combinazioni con Bass Voicing tenuto</h3>
  <p style="margin:0">Sull'Orchid si tiene premuto il Bass Voicing e si preme un altro pulsante. Qui: <b>m1 tenuta</b> (o {k('Y')}) +</p>
  <ul>
   <li>T6 Loop (o {k('REC')}) = <b>uscita hard dal loop</b></li>
   <li>T7 BPM (o {k('PLAY')}) = <b>batteria da suonare</b> sulla tastiera</li>
   <li>T5 Bass = basso on/off</li>
  </ul>
  <h3>Senza pad</h3>
  <p style="margin:0">Tutto torna come nella bozza 1: {k('X')} della Flip o B8 tenuto + manopola = manopola premuta; banco B per i pulsanti;
  fuoco + {k('A')} sulla Flip. Chord Voicing e Bass Voicing si ruotano allora dalla Flip (fuoco) o con il banco B.</p>
  <h3>Liste e menu</h3>
  <p style="margin:0">Una lista aperta prende il fuoco: si scorre con <b>m2</b> (o {k('<<')} {k('>>')}, joystick, croce),
  si conferma premendo m2 (o joystick ▶, {k('A')}), si torna indietro con <b>T10</b> (o joystick ◀, {k('B')}).</p>
 </div>
</div>
""")

# 8 — tabella
ROWS = [
  ('Sound', 'K1', 'suono per numero', 'T1', 'lista per nome', 'T1 1 s', 'Save / Save As / Delete', '—'),
  ('Perform', 'K2', 'modo e parametro', 'T2', 'lista dei modi', 'T2 1 s', 'Lock', '—'),
  ('FX', 'K3', 'effetto principale', 'T3', 'lista degli effetti', 'T3 1 s', 'Lock', '—'),
  ('Key', 'K4', 'tonalità', 'T4', 'Key mode on/off', 'T4 1 s', 'scelta rapida', 'T4 + K4 = transpose'),
  ('Bass', 'K5', 'suono di basso', 'T5', 'basso on/off', 'T5 1 s', 'lista dei modi', '—'),
  ('Loop', 'K6', 'Waiting Room, menu', 'T6 · REC', 'entra, Rec, Stop', 'T6 / REC 2 s', 'uscita morbida', '—'),
  ('BPM', 'K7', 'tempo', 'T7 · PLAY', 'beat o metronomo', 'T7 / PLAY 1 s', 'tempo in chiave → Beats', 'T7 + K7 = volume beat'),
  ('Volume', 'K8', 'volume 0–99', 'T8', 'batteria', '—', '—', 'T8 + K8 = volume basso'),
  ('Options', 'm2', 'scorre', 'T9 · SELECT', 'apre, entra', '—', '—', '—'),
  ('Chord Voicing', 'M', '±1 semitono', 'premi M', 'Split ↔ Octave', '—', '—', '—'),
  ('Bass Voicing', 'm1', 'ottava del basso', 'premi m1 · Y', 'modificatore', 'm1 tenuta', '+ T6 / T7 / T5', '—'),
]
rows = ''.join(f'<tr><td><b>{a}</b></td><td>{b}</td><td class="muted">{c}</td><td>{d}</td><td class="muted">{e}</td><td>{f}</td><td class="muted">{g}</td><td>{h}</td></tr>'
               for a, b, c, d, e, f, g, h in ROWS)
PAGES.append(f"""
<h2>Ogni controllo dell'Orchid, gesto per gesto</h2>
<p class="sub">K = manopola della MPK · T = tasto del pad · M, m1, m2 = manopole del pad. Dalla sola Flip si arriva sempre a tutto con fuoco + croce / A.</p>
<table>
 <tr><th>Controllo</th><th>Ruotare</th><th>→ effetto</th><th>Premere</th><th>→ effetto</th><th>Tenere</th><th>→ effetto</th><th>Premere e ruotare</th></tr>
 {rows}
</table>
<div class="cols" style="margin-top:3mm">
 <div class="box"><b>Una regola sola da ricordare.</b> Gli 8 encoder di uso comune hanno manopola e tasto nella stessa posizione
 delle due griglie 4×2. I due dial del voicing e la manopola delle liste stanno sul pad, premibili.</div>
 <div class="box"><b>Doppioni utili.</b> REC = T6 e PLAY = T7 sono a portata della mano destra sulla MPK; SELECT = T9 e Y = m1 sulla Flip.
 Panic: T12 tenuto 1 s, X/B8 + STOP, oppure MENU → Panic.</div>
</div>
""")

# 9 — ricette
PAGES.append(f"""
<h2>Ricette</h2>
<p class="sub">Le operazioni più comuni, con la strada più corta.</p>
<div class="cols">
 <div>
  {ricetta('Suonare un accordo', 'Tieni il tipo (e l\'estensione) sui pad, premi un tasto.',
           'Note più in alto o più in basso: gira <b>M</b>. Split ↔ Octave: premi M.',
           'Key mode accesa: un tasto senza pad dà l\'accordo diatonico.')}
  {ricetta('Cambiare suono', 'Gira <b>K1</b>: un suono per scatto.', 'Per nome: <b>T1</b> → gira m2 → premi m2.')}
  {ricetta('Salvare il suono', '<b>T1</b> tenuto 1 s → Save / Save As / Delete → m2 → premi m2.')}
  {ricetta('Tonalità', 'Gira <b>K4</b>; T4 accende o spegne la Key mode.', 'Transpose: <b>T4 tenuto + gira K4</b>.',
           'Scelta rapida: T4 tenuto 1 s, poi un tasto (con Min tenuto per la minore).')}
 </div>
 <div>
  {ricetta('Strum, Arp, Harp…', 'Gira <b>K2</b>: modo e parametro; tutto a sinistra = Off.', 'Lista: T2. Lock: T2 tenuto 1 s.')}
  {ricetta('Effetti', 'Gira <b>K3</b>: l\'effetto principale. Lista: T3. Lock: T3 tenuto.')}
  {ricetta('Basso', 'On/off: <b>T5</b>. Modo: T5 tenuto 1 s. Suono: gira <b>K5</b>. Ottava: gira <b>m1</b>.')}
  {ricetta('Beat e tempo', '<b>PLAY</b> (o T7) avvia e ferma il beat. <b>K7</b> cambia il tempo.',
           'Scegliere il beat: PLAY tenuto 1 s → tempo in chiave → Beats.', 'Volume del beat: T7 tenuto + gira K7.')}
 </div>
 <div>
  {ricetta('Looper', '<b>REC</b> (o T6) apre la Waiting Room; <b>K6</b> sceglie le battute.', 'REC di nuovo: registra dopo una battuta di count-in.',
           'In riproduzione REC esegue la voce scelta con K6 (Overdub, Play, Clear).',
           '<b>STOP</b>: chiude registrazione o overdub, pausa; tenuto 1 s = Clear.',
           'Uscita morbida: REC tenuto 2 s. Uscita hard: m1 tenuta + T6.')}
  {ricetta('Options', '<b>T9</b> → gira m2 → premi m2 per entrare → T10 per tornare.')}
  {ricetta('Emergenza', '<b>T12 tenuto 1 s</b> = Panic.')}
  {ricetta('Uscire', 'T11 (Menu) → Quit Stame.')}
 </div>
</div>
""")

# 10 — case, disposizione
PAGES.append(f"""
<h2>Il case — tutto in un pezzo</h2>
<p class="sub">Bozza. Gli apparecchi entrano interi e si tolgono in un minuto: nessuna vite nella MPK, nessuna modifica alla Flip o al pad.</p>
<div class="cols">
 <div style="flex:1.55">{case_top_svg('100%')}</div>
 <div>
  <h3 style="margin-top:0">Scelte</h3>
  <ul>
   <li><b>MPK davanti</b>, in un vano con un bordo basso che la tiene ferma (spessori in TPU per il gioco).</li>
   <li><b>Pad a destra</b>, rialzato di circa 10 mm perché i tasti stiano all'altezza del piano della MPK. È dove sull'Orchid stanno le manopole del voicing.</li>
   <li><b>Flip dietro ai pad</b>, al centro-sinistra: lontana dai connettori della MPK (tutti nella metà destra del retro) e davanti agli occhi. I suoi tasti restano raggiungibili.</li>
   <li><b>Vano dietro al pad</b> per l'hub USB e, se serve, un powerbank. Coperchio con feritoie.</li>
   <li><b>Canale dei cavi</b> lungo il retro della MPK: USB-B, pedale, MIDI e CV escono senza pieghe strette.</li>
  </ul>
  <h3>Numeri</h3>
  <table>
   <tr><td>Ingombro</td><td>610 × 300 mm</td></tr>
   <tr><td>Altezza</td><td>≈ 58 mm al dorso; ≈ 160 mm in cima allo schermo</td></tr>
   <tr><td>Peso</td><td>≈ 2,8 kg con tutto dentro (stima)</td></tr>
  </table>
 </div>
</div>
<div class="cols" style="margin-top:3mm">
 <div class="box"><b>Alternative scartate.</b> <i>Tutto stampato</i>: 610 mm non stanno nel piano da 250 mm, servirebbero 6–8 pezzi incollati e la base
 verrebbe meno rigida. <i>Guscio unico che smonta la MPK</i>: è il lavoro della fase 2 (strumento dedicato), non di questa.
 <i>Pad a sinistra</i>: comodo per «tasto + manopola» con due mani, ma la manopola grande del voicing finirebbe lontano dalla mano che suona i tasti.</div>
 <div class="box"><b>Prossimi passi.</b> Misurare pad e Flip (porte, jack, altoparlante). Modello parametrico in OpenSCAD in <code>hardware/case/</code>,
 con le misure in un solo file. Prima stampa di prova: culla della Flip e piattaforma del pad, che sono le parti più incerte. Poi i moduli del dorso.</div>
</div>
""")

# 11 — case, costruzione
PARTS = [
  ('Base', 'compensato di betulla 6 mm (o MDF)', '610 × 300', 'taglio dritto, angoli raggiati, piedini in gomma'),
  ('Bordo del vano MPK', 'PETG stampato, 4 pezzi', '≤ 240 mm, alto 16', 'tiene la MPK senza viti; spessori in TPU'),
  ('Dorso posteriore', 'PETG, 3 moduli', '≈ 150 × 96 × 58', 'incastri a coda di rondine, inserti a caldo M3 nella base'),
  ('Coperchi del canale cavi', 'PETG, 3 pezzi', '≈ 150 × 24', 'a scatto, con uscite per USB-B, pedale, MIDI, CV'),
  ('Culla della Flip', 'PETG + appoggi in TPU', '100 × 90, inclinata 15°', 'aperture per USB-C, jack e altoparlante (posizioni da misurare)'),
  ('Piattaforma del pad', 'PETG', '133 × 110 × 10', 'bordo alto 8 mm, cava per il cavo USB-C'),
  ('Vano hub e coperchio', 'PETG', '133 × 166', 'feritoie; fermo per il powerbank'),
  ('Minuteria', 'viti M3 × 8, inserti a caldo', '≈ 24 + 24', '—'),
]
parts = ''.join(f'<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td class="muted">{d}</td></tr>' for a, b, c, d in PARTS)
PAGES.append(f"""
<h2>Il case — sezione, cablaggio e parti</h2>
<p class="sub">Ogni parte stampata sta nel piano della Kobra S1 (250 × 250 mm); la base, troppo grande, è un pannello di legno.</p>
<div class="cols">
 <div style="flex:1.2">
  <h3 style="margin-top:0">Sezione dalla destra, attraverso la Flip</h3>
  {case_side_svg('100%')}
 </div>
 <div>
  <h3 style="margin-top:0">Cablaggio</h3>
  {wiring_svg('100%')}
  <div class="warn" style="margin-top:2mm;font-size:8pt">Solo un <b>hub USB 2.0 semplice, senza PD</b>: le docking station non funzionano con la Flip.
  Mai forzare <code>otg_mode</code> in host. La ricarica della Flip dalla porta di sotto va fatta a console spenta.</div>
 </div>
</div>
<table style="margin-top:2mm">
 <tr><th>Parte</th><th>Materiale</th><th>Misure (mm)</th><th>Note</th></tr>
 {parts}
</table>
""")

# 12 — preparazione e verifiche
PAGES.append(f"""
<h2>Preparazione e punti da verificare</h2>
<div class="cols">
 <div>
  <h3>Una volta sola</h3>
  <ol>
   <li><b>MPK</b>: programma «STAME» (manopole Relative su CC 70–77, joystick Dual CC, pad 36–51 sul canale 10);
   <b>Global → Trpt = ON/OFF</b> (SHIFT + STOP), perché i gesti «tenere» su REC, STOP e PLAY funzionino.</li>
   <li><b>Pad</b>: dal PC, con il software sikaicase o con <code>ch57x-keyboard-tool</code>, codici F13–F24 per i tasti e KP1…KP9
   per le manopole (pagina 5); RGB spento. Se i codici non passano: MENU → Learn Pad sulla Flip.</li>
   <li><b>Collegamenti</b>: Flip (USB-C sopra) → hub → MPK e pad, tutti via cavo. Pedale nel jack SUSTAIN della MPK.</li>
   <li>Banco A attivo sulla MPK.</li>
  </ol>
  <h3>Da non usare con Stame aperta</h3>
  <p style="margin:0">ARP, CHORDS, SCALES, NOTE REPEAT e SEQ della MPK, e le funzioni senza fili del pad (2.4G, Bluetooth).</p>
 </div>
 <div>
  <h3>Da verificare</h3>
  <table>
   <tr><th>Punto</th><th>Perché conta</th></tr>
   <tr><td>Pad: VID:PID, codici ammessi dal software, misure, posizione delle manopole</td><td>Profilo <code>pad_brimford</code> e misure del vano</td></tr>
   <tr><td>Pad: la pressione delle manopole manda «giù» e «su»?</td><td>Tenere M o m1 (modificatore)</td></tr>
   <tr><td>Pad: scatti veloci delle manopole persi?</td><td>Precisione del voicing (1 scatto = 1 semitono)</td></tr>
   <tr><td>Hub USB 2.0 con la Flip: MPK e pad visti insieme? Quanto consumano?</td><td>Autonomia e alimentazione del case</td></tr>
   <tr><td>MPK: pad tenuto mentre si preme BANK; LED del trasporto</td><td>Solo per il banco B di riserva e per i LED</td></tr>
   <tr><td>Flip: posizione di porte, jack, altoparlante, MENU/SELECT/START</td><td>Aperture della culla</td></tr>
   <tr><td>Case: ingombro del cavo USB-B dietro la MPK</td><td>Profondità del canale (meglio un connettore a 90°)</td></tr>
  </table>
  <p class="muted" style="font-size:7.8pt;margin-top:2mm">Elenco completo in <code>docs/specifica/90-questioni-aperte.md</code>; il case in <code>docs/specifica/60-case.md</code>.</p>
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
