# Case di Stame — la console

Bozza 4, 17/10/2026. Specifica: `docs/specifica/60-case.md`. Identità: `docs/identita/README.md`.

![La console](out/montaggio/console.png)

Un telaio di betulla tiene insieme la MPK mini IV, il macro pad BRIMFORD e la Miyoo Flip, nella composizione scelta da Luigi: MK4 a sinistra; a destra la **torre**, con il pad davanti in linea con i tasti e la Flip aperta dietro, su una mensola che nasconde l'hub. Nessun apparecchio viene modificato (CASE-001): si posano e si tolgono in un minuto.

Cosa cambia nella bozza 4:
- **Incastri a linguetta.** Retro, divisorio e pareti della torre entrano con linguette nelle asole della base e del piano, e si incollano. Il piano poggia sulle pareti, che stanno sotto di lui; prima le pareti arrivavano alla stessa quota del piano e le viti cadevano fuori dalle pareti.
- **Culla bassa.** È un vassoio sul piano, alto 5 mm, avvitato con 4 viti. È aperto dietro, così le spalle della Flip (L1, R1, L2 Tap, R2 Fill) restano libere: dal 17/10/2026 sono comandi sempre vivi.
- **Visiera.** Ha due fianchi che seguono lo schermo a 65°, un tettuccio e due piedi avvitati al piano.
- **Squadrette.** I fori nella base sono a 6 mm dal fianco e quelli nel fianco 6 mm sopra la base, come vuole la squadretta.
- **Legende.** Usano la mappa del 17/10/2026: banco B della MK4 = batteria; sul cartellino e sui copritasti le funzioni del pad con la tastiera e, in piccolo, la nota del pad strumento.
- **Copritasti.** Sono 15, con le scritte a punti Matrice in rilievo.
- **3D e documenti.** Modello 3D, modello SketchUp, fogli di taglio, tavole e istruzioni di montaggio nascono dalla stessa geometria dei pezzi.

## Come si genera tutto

```
python -I hardware/case/genera.py      pezzi (SVG laser, STL), fogli di taglio (SVG, DXF), dima, tavola
python -I hardware/case/assieme.py     modello 3D (OBJ), dati per SketchUp, tavole del montaggio (PNG)
python -I hardware/case/manuale.py     PDF: progetti di taglio e istruzioni di montaggio
python -I hardware/case/sketchup.py    codice per costruire il modello in SketchUp (out/sketchup/)
```

Tutte le misure stanno in `misure.py`, ognuna con la sua fonte: [M] manuale, [O] osservato, [D] dedotto, [V] da verificare. Cambiata una misura, si rigenera tutto. `genera.py` controlla che i pezzi stiano nei piani delle macchine e che i pezzi stampati siano gusci chiusi.

Il riferimento del case (x a destra, y verso il musicista, z in su) è sinistrorso. Gli STL e i modelli 3D escono specchiati su y, cioè nel verso fisico giusto: senza lo specchio la culla avrebbe gli intagli dal lato sbagliato.

`manuale.py` usa la suite ArtCraft: VectorCraft converte le pagine SVG in PDF vettoriali, PdfCraft le unisce. Il modello SketchUp si costruisce con lo strumento SketchUp (nel cloud), eseguendo nell'ordine `out/sketchup/parte_0.py`, `parte_1.py`, `parte_2.py`. Ha un livello e una scena per ogni passo del montaggio.

## Cosa esce in `out/`

| File | Cos'è |
|---|---|
| `istruzioni_montaggio.pdf` | copertina con pezzi e minuteria, un passo per pagina, misure da verificare |
| `taglio/progetti_di_taglio.pdf` | i fogli 1:1 per materiale e la dima |
| `taglio/taglio_*.svg`, `.dxf` | i fogli per LightBurn: rosso taglio, nero incisione, blu segno (nel DXF: livelli TAGLIO, INCISIONE, SEGNO) |
| `*.svg` | i singoli pezzi del laser, 1:1 in millimetri |
| `*.stl` | i pezzi da stampare, nel verso giusto, appoggiati sul piatto |
| `stame_console.skp` | il modello SketchUp, con le scene dei passi |
| `stame_console.obj`, `.mtl` | lo stesso modello per altri programmi, in millimetri |
| `montaggio/*.png` | le tavole dei passi e due viste della console |
| `dima_mascherina.svg`, `tavola_insieme.svg` | dima da stampare su carta, tavola dall'alto e di fianco |

## Prima di tagliare

1. **Misurare** le voci [V] di `misure.py`. I controlli della MK4 e le porte della Flip sono stati rimisurati sulle foto il 17/10/2026 (±1 mm); restano:
   - ingombro del macro pad, passo dei tasti, manopole, presa USB-C e stelo dei tasti (`PAD`, `PAD_KNOB`, `PAD_USB_X`, `COPRITASTO`): le foto non bastano, due foto danno passi diversi del 10%;
   - altezza dei pulsanti piccoli della MK4, perché la mascherina sta 4 mm sopra il pannello (`piede_h`);
   - angolo di apertura della Flip (serve almeno 115°);
   - misure dell'hub (`HUB`).

   Senza calibro basta una foto da sopra, con il pezzo appoggiato su un foglio A4 tutto in vista: i quattro angoli del foglio danno la scala e la prospettiva, e la misura viene entro mezzo millimetro.
2. **Stampare la dima** su carta al 100% e controllare il righello di 100 mm. Posarla sulla MK4: i fori devono cadere sui controlli, i cerchi blu dei piedini su zone piane.
3. **Fare una prova di taglio** su un ritaglio, per tarare potenza, velocità e il gioco delle linguette (0,2 mm per lato, `GIOCO`). Il laser a diodo taglia l'acrilico nero, non quello trasparente.

## Pezzi

### Laser

| Materiale | Fogli (390 × 390) | Pezzi |
|---|---|---|
| betulla 4 mm | 2 | listello del retro (2 metà), 2 fianchi esterni incisi, 6 strati interni, divisorio, 2 pareti della torre |
| betulla 6 mm | 2 | base (2 metà a coda di rondine), piano della mensola |
| acrilico nero 3 mm | 1 (basta 352 × 140) | mascherina della MK4, cartellino del pad |

### Stampa 3D (Kobra S1, PETG)

| File | Quanti | Note |
|---|---|---|
| `culla_flip.stl` | 1 | vassoio sul piano, 4 viti M3 svasate; un intaglio davanti per jack e USB-C, ai lati libero vicino alla cerniera per i tasti [D, foto] |
| `visiera.stl` | 1 | si avvita al piano dietro la culla; stampare sul tettuccio, con supporti |
| `cornice_pad.stl` | 1 | si incolla sulla base attorno al pad |
| `fermo_hub.stl` | 1 | tiene l'hub nel vano, 2 viti nella base |
| `squadretta_m3.stl` | 6 | fra base e fianchi |
| `piedino_mascherina.stl` | 11 | meglio in TPU; si incollano sotto la mascherina dove indica la dima |
| `copritasti.stl` | 1 (15 tasti) | PETG sabbia, dritti; filamento nero dall'altezza dei punti in su; supporto solo sotto lo stelo; stelo a croce tipo MX [V] |

Minuteria: 4 viti M3 × 10 svasate e 8 viti M3 × 10 con i dadi; 8 viti da legno 3 × 12; colla vinilica; biadesivo sottile per il cartellino; 6 piedini in gomma da 12 mm; hub USB 2.0 senza Power Delivery; un cavo USB-C a 90° per la MK4.

## Montaggio

Le istruzioni con le tavole sono in `out/istruzioni_montaggio.pdf`. In breve:

1. **La base:** le due metà a coda di rondine, con la colla.
2. **Retro e divisorio:** nelle tacche e nelle asole della base, con la colla.
3. **I fianchi:** quattro strati incollati per lato, poi avvitati alla base con le squadrette.
4. **Il vano dell'hub:** fermo e hub, le pareti della torre nelle asole, il cartellino sulla parete davanti.
5. **La mensola:** culla e visiera avvitate al piano, poi il piano sulle linguette delle pareti.
6. **Il macro pad:** cornice incollata sulla base, il pad dentro, il cavo nel vano.
7. **MK4 e mascherina:** la MK4 nel vano, i piedini sotto la mascherina, la mascherina sopra.
8. **La Flip e i cavi:** la Flip aperta nella culla; nell'hub OTG della Flip, USB della MK4 e del pad.
9. **I copritasti:** al posto dei tasti del pad.

## Misure principali

| | mm |
|---|---|
| ingombro | 569,5 × 244 |
| altezza dei fianchi | 54 dietro, 40 davanti |
| mensola della Flip | piano da 40 a 46; vano sotto alto 34 |
| altezza con lo schermo aperto | 133 lo schermo (a 65°), 150 la visiera |
| tasti del pad / tasti della MK4 | 38 / ≈ 36 dal tavolo |
