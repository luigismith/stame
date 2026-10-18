# Case di Stame — la console

Bozza 5, 18/10/2026. Specifica: `docs/specifica/60-case.md`. Identità: `docs/identita/README.md`.

![La console](out/montaggio/console.png)

Un telaio di betulla tiene insieme la MPK mini IV, il macro pad BRIMFORD e la Miyoo Flip, nella composizione scelta da Luigi: MK4 a sinistra; a destra il pad davanti, in linea con i tasti, e la Flip aperta dietro. Nessun apparecchio viene modificato (CASE-001): si posano e si tolgono in un minuto.

Cosa cambia nella bozza 5 (Luigi, 18/10/2026: «deve essere tutto coperto e omogeneo. non mi piace tanto la divisione che hai creato tra mpk e pad, e per il pad vorrei una culla simile a quella che hai fatto per il flip»):
- **Un piano solo.** Fianchi, retro, costola e parete davanti arrivano tutti a 46 mm. Dentro c'è un piano di acrilico nero in due pezzi, alla stessa quota: la mascherina a sinistra e il piano della Flip a destra. Hub e cavi stanno sotto, coperti; non ci sono più la torre, la mensola e il divisorio.
- **La mascherina appoggia sulla MK4** e ha un foro per ogni controllo, anche per quelli che Stame non usa (Luigi: «falla che si poggia bene con i fori anche per i controlli non utilizzati»). Sui controlli di Stame ci sono le sue legende; su quelli della MK4 stessa (OCT, ARP, LATCH, NOTE REPEAT, TAP, BANK, DAW) il loro nome, piccolo. Dietro copre la zona dei cavi fino al retro, con la targa di Stame.
- **La culla del pad** è come quella della Flip: il pad ci sta con la piastra 2 mm sopra il piano e il bordo sale 5 mm oltre la piastra. Dentro segue il contorno vero del pad, misurato il 18/10/2026 sulle foto di Luigi: il lobo davanti dal lato delle manopole, gli angoli, la USB-C sul retro. Sta in piedi sulla base, poggia il pad su sei costole e regge con un dente il bordo del piano della Flip. Davanti ha la tacca per la manopola grande, dietro la finestra per la spina del pad.
- **Gli appoggi.** Lo strato più interno di fianchi, retro e costola è più basso dove sopra c'è il piano: con una striscia di feltro da 1 mm, il piano ci appoggia alla quota della MK4.
- **Il cartellino non c'è più**: i tasti del pad hanno le etichette sotto il coperchio, e le manopole del pad hanno la loro legenda sul piano, fra le due culle.

## Come si genera tutto

```
python -I hardware/case/genera.py      pezzi (SVG laser, STL), fogli di taglio (SVG, DXF), dima, tavola
python -I hardware/case/assieme.py     modello 3D (OBJ), dati per SketchUp, tavole del montaggio (PNG)
python -I hardware/case/stampa3d.py    la console tutta stampata, per chi non ha il laser (out/stampa3d/)
python -I hardware/case/manuale.py     PDF: progetti di taglio, istruzioni di montaggio, istruzioni della versione stampata
python -I hardware/case/sketchup.py    codice per costruire il modello in SketchUp (out/sketchup/)
python -I hardware/case/etichette.py   etichette dei tasti trasparenti del pad (A4, SVG e PDF)
python -I hardware/case/rendering.py   rendering con Blender 5.2, Cycles su GPU (out/render/)
```

Attenzione: il 18/10/2026, su HOMEPC, `rendering.py` in qualità piena ha mandato il PC in schermata blu due volte (0xEF). I rendering in `out/render/` sono di quella mattina; prima di rilanciarlo va capita la causa.

Tutte le misure stanno in `misure.py`, ognuna con la sua fonte: [M] manuale, [O] osservato, [D] dedotto, [V] da verificare. Cambiata una misura, si rigenera tutto. `genera.py` controlla che i pezzi stiano nei piani delle macchine, che i pezzi stampati siano gusci chiusi e che le scritte incise non escano a specchio.

Il riferimento del case (x a destra, y verso il musicista, z in su) è sinistrorso. Gli STL e i modelli 3D escono specchiati su y, cioè nel verso fisico giusto: senza lo specchio la culla avrebbe gli intagli dal lato sbagliato.

`manuale.py` usa la suite ArtCraft: VectorCraft converte le pagine SVG in PDF vettoriali, PdfCraft le unisce. Il modello SketchUp si costruisce con lo strumento SketchUp (nel cloud), eseguendo nell'ordine i file `out/sketchup/parte_N.py` (da 0 in su) e `scene.py`, poi salvandolo. Ha un livello e una scena per ogni passo del montaggio.

`rendering.py` prepara le texture in `build/render/` (incisioni dagli SVG, etichette, la faccia della Flip raddrizzata dalla foto, la plancia sullo schermo) e lancia `blender_scena.py` in Blender: betulla con i bordi bruciati dal laser, acrilico nero satinato con le incisioni, PETG con gli strati, alluminio, tasti trasparenti con l'etichetta dentro. La luce da studio è `studio_small_09_2k.hdr` di Poly Haven (CC0), da scaricare in `build/render/`. `--prova` fa una passata veloce. `tools/sito_case.py` porta render, tavole e fogli nel sito (`docs/case.html`).

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
| `render/*.jpg` | i rendering: la console, il pad con la Flip, la mascherina |
| `etichette_pad.pdf`, `.svg` | le etichette dei tasti del pad, A4 al 100 % |
| `dima_mascherina.svg`, `tavola_insieme.svg` | dima da stampare su carta, tavola dall'alto e di fianco |
| `stampa3d/` | la console tutta stampata: vedi sotto |

## Senza laser: la console tutta stampata

![La console tutta stampata](out/stampa3d/console_stampata.png)

Per chi non ha il laser c'è la stessa console fatta solo con una stampante 3D (`docs/specifica/60-case.md` §7b). `stampa3d.py` prende i pezzi del laser da `genera.py` e li trasforma:
- **gli strati incollati diventano un pezzo solo:** ogni fianco, ogni metà del retro con il suo strato d'appoggio, la costola; la base è una lastra sola;
- **quello che non sta sul piatto si divide in tasselli** con le code di rondine, da incollare: la base in sei, la mascherina in due, la metà sinistra del retro in due. I pezzi lunghi che entrano in diagonale escono già ruotati;
- **le scritte:** sui fianchi il marchio e il nome sono in rilievo, e con un cambio di filamento vengono di un altro colore. Sulla mascherina e sul piano della Flip le scritte del laser sono troppo fini per un ugello da 0,4: ogni gruppo ha una tasca profonda 0,4 mm, e le etichette si stampano su carta adesiva.

Il piatto di riferimento è 210 × 210 mm, cioè le stampanti da 220 in su; `--piatto N` rigenera tutto per un piatto diverso. In tutto servono circa 1,3 kg di PETG o PLA: il telaio color legno o sabbia, i piani e le culle neri.

| File in `out/stampa3d/` | Cos'è |
|---|---|
| `istruzioni_stampa3d.pdf` | i pezzi e le impostazioni, i tasselli, le scritte, le differenze dal montaggio della console laser |
| `pezzi.md` | l'elenco dei pezzi con le misure, le note e la stima del filamento |
| `*.stl` | i pezzi, nel verso giusto, con la faccia in vista in alto |
| `etichette_mascherina.pdf`, `.svg` | le etichette 1:1 da stampare al 100 % su carta adesiva, con la mappa delle tasche |
| `tasselli.svg` | come si uniscono i tasselli, con i numeri dei file |
| `console_stampata.png`, `console_stampata_retro.png` | la console montata, davanti e dietro |

## Prima di tagliare

1. **Misurare** le voci [V] di `misure.py`. I controlli della MK4 e le porte della Flip sono stati rimisurati sulle foto il 17/10/2026 (±1 mm); restano:
   - altezza del pannello della MK4 (37 mm, `MK4['h']`): la mascherina ci appoggia, e il piano della Flip va alla stessa quota;
   - altezza dei pulsanti piccoli della MK4: con la mascherina appoggiata stanno 1-2 mm sotto la sua faccia;
   - altezza del corpo del pad (`PAD_CORPO`, 11,5 mm dalle foto del 18/10/2026) e quota della sua presa USB-C (`PAD_USB_Z`, 9 mm; la presa è sul retro, a 80 mm dal bordo dei tasti): decidono le costole e la finestra della culla del pad;
   - angolo di apertura della Flip (serve almeno 115°);
   - misure dell'hub (`HUB`).

   Senza calibro basta una foto da sopra, con il pezzo appoggiato su un foglio A4 tutto in vista: i quattro angoli del foglio danno la scala e la prospettiva, e la misura viene entro mezzo millimetro.
2. **Stampare la dima** su carta al 100% e controllare il righello di 100 mm. Posarla sulla MK4: ogni foro deve lasciare libero il suo controllo, con la cornice attorno.
3. **Fare una prova di taglio** su un ritaglio, per tarare potenza, velocità e il gioco delle linguette (0,2 mm per lato, `GIOCO`). Il laser a diodo taglia l'acrilico nero, non quello trasparente.

## Pezzi

### Laser

| Materiale | Fogli (390 × 390) | Pezzi |
|---|---|---|
| betulla 4 mm | 2 | retro e strato d'appoggio (2 metà ciascuno), 2 fianchi esterni incisi, 4 strati di mezzo, 2 strati d'appoggio dei fianchi, 2 strati della costola, parete davanti |
| betulla 6 mm | 2 | base (2 metà a coda di rondine) |
| acrilico nero 3 mm, satinato | 1 (basta 369 × 307) | mascherina della MK4, piano della Flip |

### Stampa 3D (Kobra S1, PETG)

| File | Quanti | Note |
|---|---|---|
| `culla_flip.stl` | 1 | vassoio sul piano, 4 viti M3 svasate; un intaglio davanti per jack e USB-C, ai lati libero vicino alla cerniera per i tasti [D, foto] |
| `culla_pad.stl` | 1 | sta sulla base fra costola, fianco e parete davanti; si stampa in piedi, senza supporti |
| `visiera.stl` | 1 | si avvita al piano dietro la culla; stampare sul tettuccio, con supporti |
| `fermo_hub.stl` | 1 | tiene l'hub sotto il piano, 2 viti nella base |
| `squadretta_m3.stl` | 6 | fra base e fianchi |

Minuteria: 4 viti M3 × 10 svasate e 8 viti M3 × 10 con i dadi; 8 viti da legno 3 × 12; colla vinilica; feltro adesivo da 1 mm in strisce; 6 piedini in gomma da 12 mm; hub USB 2.0 senza Power Delivery; due cavi USB-C a 90°, per la MK4 e per il pad.

## Montaggio

Le istruzioni con le tavole sono in `out/istruzioni_montaggio.pdf`. In breve:

1. **La base:** le due metà a coda di rondine, con la colla.
2. **Retro, costola e parete davanti:** nelle tacche e nelle asole della base, con la colla; lo strato d'appoggio incollato davanti al retro, i due strati della costola fra loro.
3. **I fianchi:** quattro strati incollati per lato, quello d'appoggio dentro; poi avvitati alla base con le squadrette.
4. **L'hub e i cavi:** fermo e hub sulla base; il cavo della MK4 passa dietro, sotto la costola. Feltro sugli appoggi.
5. **La culla del pad:** sulla base, il pad dentro, il cavo nella finestra di dietro.
6. **Il piano della Flip:** culla e visiera avvitate al piano, il piano sugli appoggi e sul dente della culla del pad.
7. **MK4 e mascherina:** la MK4 al suo posto, la mascherina sopra.
8. **La Flip e i cavi:** la Flip aperta nella culla; OTG nella fessura dietro, jack e ricarica in quella davanti.
9. **Le etichette:** tasti trasparenti sul pad, sotto ogni coperchio la sua etichetta (`out/etichette_pad.pdf`, stampata al 100 %).

## Misure principali

| | mm |
|---|---|
| ingombro | 577,5 × 244 |
| cima della console (telaio e piano) | 46 |
| piastra del pad / bordo delle culle | 48 / 53 |
| altezza con lo schermo aperto | 133 lo schermo (a 65°), 150 la visiera |
| tasti del pad / tasti della MK4 | ≈ 63 / ≈ 36 dal tavolo |
