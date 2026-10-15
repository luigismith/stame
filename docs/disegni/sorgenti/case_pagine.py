# Pagine 10–11 del PDF: il case, bozza 2 (14/10/2026). Immagini da docs/identita/img e hardware/case.
import base64
import os

from pad_case import wiring_svg

QUI = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.normpath(os.path.join(QUI, '..', '..', 'identita', 'img'))


def img(nome, width='100%', pixel=False):
    data = base64.b64encode(open(os.path.join(IMG, nome), 'rb').read()).decode('ascii')
    resa = 'image-rendering:pixelated;' if pixel else ''
    return f'<img src="data:image/png;base64,{data}" style="width:{width};display:block;{resa}" alt="{nome}">'


LASER = [
    ('Mascherina della MPK', 'acrilico nero 3 mm, inciso', '2 metà', 'legende a punti Matrice e a pixel; copre i pulsanti non usati'),
    ('Cartellino del macro pad', 'acrilico nero 3 mm, inciso', '1', 'mappa di T1–T12 e delle manopole; copre l\'hub'),
    ('Ponte: piano, fronte, retro', 'betulla 4 mm', '2 + 2 + 2', 'piano a 15° con tasca della Flip, marchio, legende, griglia'),
    ('Centine del ponte', 'betulla 4 mm', '3', 'reggono il piano'),
    ('Fianchi', 'betulla 4 mm, 4 strati', '2 esterni + 6 interni', 'esterni con marchio e nome; coprono le guance rosse'),
    ('Base', 'betulla 6 mm', '2 metà', 'coda di rondine'),
    ('Divisorio', 'betulla 4 mm', '1', 'fra MPK e macro pad'),
]
STAMPA = [
    ('Culla della Flip', 'PETG nero', '1', 'aperta dietro e ai lati per porte e volume [V]'),
    ('Visiera', 'PETG nero', '1', 'cappa attorno allo schermo, come un oscilloscopio'),
    ('Vassoio del macro pad', 'PETG', '1', 'porta i tasti all\'altezza della mascherina [V]'),
    ('Piedini della mascherina', 'TPU o PETG', '14', '4 mm: la mascherina non preme i pulsanti'),
    ('Squadrette M3, colonnine, fermo hub', 'PETG', '12 + 4 + 1', 'montaggio senza colla dove serve smontare'),
]


def righe(tab):
    return ''.join(f'<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td class="muted">{d}</td></tr>' for a, b, c, d in tab)


CASE_PAGINE = [f"""
<h2>Il case — la console (bozza 2)</h2>
<p class="sub">Un telaio di betulla con le scritte della plancia incise. Gli apparecchi entrano interi e si tolgono in un minuto. Pezzi generati da <code>hardware/case/genera.py</code>.</p>
<div class="cols">
 <div style="flex:1">{img('case_3d.png')}
  <div class="muted" style="font-size:7.6pt;margin-top:1mm">Modello SketchUp <code>hardware/case/out/stame_console.skp</code>, dalle stesse misure dei pezzi.</div></div>
 <div style="flex:1.1">
  <h3 style="margin-top:0">Scelte</h3>
  <ul>
   <li><b>Mascherina</b> di acrilico nero sulla MPK: ogni comando ha il nome della sua funzione in Stame, i pulsanti che Stame non usa spariscono sotto il marchio. Sta su piedini da 4 mm, così non preme nulla.</li>
   <li><b>Fianchi di betulla</b> a quattro strati: coprono le guance rosse della MPK. Il <b>divisorio</b> chiude il lato verso il macro pad.</li>
   <li><b>Ponte</b> dietro la MPK: piano a 15° con la tasca della Flip, il marchio, le funzioni dei tasti della Flip e una griglia d'aerazione. Sotto passano i cavi; la bocca sul fronte lascia liberi i connettori della MPK.</li>
   <li><b>Flip</b> in una culla stampata, schermo a 70° dentro una <b>visiera</b>: sembra il display della console.</li>
   <li><b>Macro pad</b> a destra su un vassoio; dietro, il <b>cartellino</b> con la sua legenda copre l'hub.</li>
  </ul>
  <h3>Numeri</h3>
  <table>
   <tr><td>Ingombro</td><td>619 × 288 mm</td></tr>
   <tr><td>Altezza</td><td>52 mm davanti al ponte, 78 dietro; 150 mm in cima allo schermo</td></tr>
   <tr><td>Peso</td><td>≈ 3 kg con tutto dentro (stima)</td></tr>
  </table>
 </div>
</div>
""", f"""
<h2>Il case — tavola d'insieme e mascherina</h2>
<p class="sub">Vista dall'alto e di fianco (da <code>hardware/case/out/tavola_insieme.svg</code>); sotto, la mascherina sinistra come esce dal generatore.</p>
<div style="display:flex;gap:5mm;align-items:flex-start">
 <div style="flex:0 0 118mm">{img('tavola_insieme.png')}</div>
 <div style="flex:1">
  <h3 style="margin-top:0">Come si legge</h3>
  <ul>
   <li><b>Rosso</b>: i pezzi tagliati (fianchi, ponte, mascherina, cartellino) e la Flip.</li>
   <li><b>Blu</b>: MPK, macro pad, fori della mascherina, visiera, sguardo del musicista.</li>
   <li>Di fianco: la MPK a cuneo, la mascherina 4 mm sopra il pannello, il ponte a 15°, lo schermo a 70° dentro la visiera. Lo schermo sporge 21 mm dietro la base.</li>
  </ul>
 </div>
</div>
<div style="margin-top:3mm">{img('mascherina_sx.png', '66%')}
 <div class="muted" style="font-size:7.6pt;margin-top:1mm">Mascherina sinistra: DIM MIN MAJ SUS sopra i pad, 6 m7 M7 9 sotto, a punti Matrice; in piccolo la funzione del banco B. Il marchio sta dove la MPK ha i pulsanti che Stame non usa.</div></div>
""", f"""
<h2>Il case — pezzi e cablaggio</h2>
<p class="sub">Laser AtomStack S10 (rosso taglio, nero incisione, blu segno) e stampante Kobra S1. Prima di tagliare: dima della mascherina su carta al 100%.</p>
<div class="cols">
 <div style="flex:1.4">
  <table>
   <tr><th>Laser</th><th>Materiale</th><th>Pezzi</th><th>Note</th></tr>
   {righe(LASER)}
   <tr><th>Stampa</th><th>Materiale</th><th>Pezzi</th><th>Note</th></tr>
   {righe(STAMPA)}
  </table>
 </div>
 <div>
  <h3 style="margin-top:0">Cablaggio</h3>
  {wiring_svg('100%')}
  <div class="warn" style="margin-top:2mm;font-size:8pt">Solo un <b>hub USB 2.0 semplice, senza PD</b>: le docking station non funzionano con la Flip.
  Mai forzare <code>otg_mode</code> in host. La ricarica della Flip dalla porta di sotto va fatta a console spenta.</div>
 </div>
</div>
"""]
