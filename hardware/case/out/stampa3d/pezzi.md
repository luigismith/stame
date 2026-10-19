# Stame — la console tutta stampata, a vasche

Generato da `hardware/case/stampa3d.py` (piatto 210 × 210 mm; `--piatto 240` per la Kobra S1 e le altre da 250: tre vasche intere). Il telaio è in vasche: ogni vasca è un tratto di console già montato, con fondo, pareti, appoggi del piano e sedi, e si stampa in piedi con il fondo sul piatto. Ogni file sta sul piatto così com'è, nel verso giusto.

| File | Quanti | Ingombro (mm) | Grammi | Colore | Note |
|---|---|---|---|---|---|
| `vasca_sx_dietro.stl` | 1 | 200 × 155 × 45,0 | 161 | telaio: PLA o PETG color legno o sabbia | fianco sinistro con marchio e nome, retro, pedana della MK4; in piedi, il fondo sul piatto |
| `vasca_centro_dietro.stl` | 1 | 200 × 155 × 45,0 | 143 | telaio: PLA o PETG color legno o sabbia | retro con la finestra del pedale, pedana della MK4, costola; in piedi, il fondo sul piatto |
| `vasca_dx_dietro.stl` | 1 | 209 × 155 × 45,0 | 184 | telaio: PLA o PETG color legno o sabbia | retro con le finestre di alimentazione e audio, fermo dell'hub, colonnina, fianco destro con marchio e nome; in piedi, il fondo sul piatto |
| `vasca_sx_davanti.stl` | 1 | 195 × 104 × 45,0 | 89 | telaio: PLA o PETG color legno o sabbia | fianco sinistro, pedana della MK4; in piedi, il fondo sul piatto |
| `vasca_centro_davanti.stl` | 1 | 188 × 104 × 45,0 | 80 | telaio: PLA o PETG color legno o sabbia | pedana della MK4, costola; in piedi, il fondo sul piatto |
| `vasca_dx_davanti.stl` | 1 | 208 × 104 × 45,0 | 192 | telaio: PLA o PETG color legno o sabbia | culla del pad, parete davanti, fianco destro; in piedi, il fondo sul piatto |
| `mascherina_1.stl` | 1 | 194 × 126 × 2,0 | 40 | piani: nero | lastra da 2,0 mm, la faccia in vista in alto; le scritte su carta adesiva, nelle tasche; la metà sinistra |
| `mascherina_2.stl` | 1 | 166 × 126 × 2,0 | 37 | piani: nero | lastra da 2,0 mm, la faccia in vista in alto; le scritte su carta adesiva, nelle tasche; la metà destra |
| `piano_flip.stl` | 1 | 200 × 140 × 2,0 | 61 | piani: nero | lastra da 2,0 mm, la faccia in vista in alto; le scritte su carta adesiva, nelle tasche |
| `culla_flip.stl` | 1 | 89 × 83 × 7,0 | 19 | nero | vassoio sul piano della Flip, 4 viti M3 svasate |
| `visiera.stl` | 1 | 118 × 42 × 95,6 | 44 | nero | si avvita al piano dietro la culla; si stampa sul tettuccio, con i supporti solo sotto i piedi |
| `prova_giunta.stl` | 1 | 75 × 60 × 45,0 | 28 | telaio: PLA o PETG color legno o sabbia | la giunta sotto la MK4 in piccolo, le due metà insieme: da stampare prima delle vasche |

Filamento: circa 1,1 kg in tutto (stima a fette, come lo slicer: 3 perimetri, 4 strati pieni sopra e sotto, riempimento al 20 %).

## Le giunte

Le 6 vasche si uniscono senza colla. Nel fondo ci sono code di rondine verticali (collo 8, testa 12, profondità 7 mm; nella sede 0,15 mm di gioco per lato): stampate in piedi sono prismi dritti, senza sbalzi, e si infilano calando una vasca accanto all'altra. Tengono le vasche allineate nel piano, non in altezza: per questo le pareti che attraversano la giunta (il retro e, con sei vasche, i fianchi e la costola) si sormontano a mezzo spessore per 12 mm e due viti M3 le stringono, con la testa nella sua sede nella faccia di fuori e il dado nella sua sede in quella di dentro. Le giunte stanno dove non tagliano sedi né appoggi: a metà sotto la MK4, che ci appoggia sopra; fra la costola e la culla del pad, che resta intera; con sei vasche, fra la colonnina e la culla.

Viti: 6 viti M3 × 6 a testa cilindrica (brugola), 4 viti M3 × 12 a testa cilindrica (brugola) con i dadi.

## Impostazioni

- PETG o PLA, ugello 0,4, strati da 0,2. Le vasche in un colore legno o sabbia; mascherina, piano della Flip, culla della Flip e visiera in nero.
- 3 perimetri, 4 strati pieni sopra e sotto, riempimento giroide al 20 %. Senza supporti: le vasche hanno solo ponti corti (il passaggio dei cavi sotto la costola, 28 mm; le finestre della culla del pad) e le sedi delle viti, orizzontali e piccole. Solo la visiera vuole i supporti, sotto i piedi: si stampa sul tettuccio, come esce.
- Le vasche sono alte 45 mm e larghe fino al piatto: piatto pulito, tesa (brim) di 5 mm se gli angoli si alzano.
- Fianchi: il marchio e il nome escono di 0,6 mm dalla faccia di fuori, che stampata in piedi è verticale: vengono del colore della vasca (a più colori: `../stampa3d_multicolore/`).
- Mascherina e piano della Flip: 39 tasche profonde 0,4 mm per le etichette (`etichette_mascherina.svg`, da stampare al 100 % su carta adesiva; `etichette_mappa.svg` dice dove va ogni numero). La mascherina è in due metà accostate, senza giunta: i fori sui comandi della MK4 tengono ogni metà al suo posto.
- Prima delle vasche, `prova_giunta.stl`: le due metà devono calarsi l'una nell'altra a mano, e le viti stringere con il dado nella sua sede. Se la coda è dura, carta abrasiva sui fianchi della coda.

## Montaggio

1. Le vasche: si calano una accanto all'altra, in qualunque ordine, sul tavolo; poi le viti delle giunte. Piedini in gomma sotto, due per colonna.
2. L'hub nel fermo, con le porte verso il davanti; i cavi come nella console laser (passo 4 di `istruzioni_montaggio.pdf`). Feltro sugli appoggi del piano (retro, fianchi, costola, colonnina, dente della culla).
3. Il pad nella sua culla, con il cavo a 90° nella finestra di dietro.
4. La culla della Flip e la visiera avvitate al piano (4 viti M3 svasate e 2 M3 × 10, dadi sotto); il piano sugli appoggi.
5. La MK4 sulla pedana, le due metà della mascherina sopra, ogni controllo nel suo foro.
6. Le etichette nelle tasche; la Flip nella culla; i tasti trasparenti del pad con le loro etichette.
