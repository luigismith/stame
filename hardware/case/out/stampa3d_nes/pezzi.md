# Stame — la console stampata a più colori, nei colori del NES

Generato da `hardware/case/multicolore.py` per un piatto di 240 × 240 mm (Anycubic Kobra S1 con l'ACE Pro, o un'altra stampante a più filamenti). Le stesse 3 vasche di `../stampa3d/` (con `--piatto 240`), stampate in piedi con il fondo sul piatto, e gli stessi pezzi che si tolgono; le scritte le fa la stampa, in un altro filamento: incassate a filo nella faccia in vista di mascherina e piano della Flip, che sta sul piatto, e nella faccia di fuori dei fianchi. Le istruzioni da stampare, con le anteprime, sono in `istruzioni_multicolore.pdf`.

| File | Ingombro (mm) | Grammi | Filamenti | Note |
|---|---|---|---|---|
| `vasca_sx.3mf` (o `vasca_sx_fascia.stl` + `vasca_sx_corpo.stl` + `vasca_sx_scritte.stl`) | 200 × 240 × 45,0 | 244 | fascia 1 grigio traslucido, corpo 2 crema, scritte 3 rosso | fianco sinistro con marchio e nome, retro, pedana della MK4; in piedi, il fondo sul piatto; la fascia, fino a 8 mm, in un altro filamento; marchio e nome nel fianco, che è verticale: il filamento cambia in 127 strati |
| `vasca_centro.3mf` (o `vasca_centro_fascia.stl` + `vasca_centro_corpo.stl`) | 200 × 240 × 45,0 | 218 | fascia 1 grigio traslucido, corpo 2 crema | retro con la finestra del pedale, pedana della MK4, costola; in piedi, il fondo sul piatto; la fascia, fino a 8 mm, in un altro filamento |
| `vasca_dx.3mf` (o `vasca_dx_fascia.stl` + `vasca_dx_corpo.stl` + `vasca_dx_scritte.stl`) | 208 × 240 × 45,0 | 353 | fascia 1 grigio traslucido, corpo 2 crema, scritte 3 rosso | retro con la finestra dell'audio e quella dell'hub, fermo dell'hub, colonnina, culla del pad, parete davanti, fianco destro con marchio e nome; in piedi, il fondo sul piatto; la fascia, fino a 8 mm, in un altro filamento; marchio e nome nel fianco, che è verticale: il filamento cambia in 127 strati |
| `mascherina_1.3mf` (o `mascherina_1_corpo.stl` + `mascherina_1_scritte.stl`) | 194 × 126 × 2,0 | 40 | corpo 1 grigio traslucido, scritte 3 rosso | la metà sinistra della mascherina; scritte incassate nella faccia in vista, che sta sul piatto |
| `mascherina_2.3mf` (o `mascherina_2_corpo.stl` + `mascherina_2_scritte.stl`) | 166 × 126 × 2,0 | 38 | corpo 1 grigio traslucido, scritte 3 rosso | la metà destra della mascherina; scritte incassate nella faccia in vista, che sta sul piatto |
| `piano_flip.3mf` (o `piano_flip_corpo.stl` + `piano_flip_scritte.stl`) | 200 × 140 × 2,0 | 61 | corpo 1 grigio traslucido, scritte 3 rosso | scritte incassate nella faccia in vista, che sta sul piatto |
| `culla_flip.stl` | 89 × 83 × 7,0 | 19 | 1 grigio traslucido | vassoio sul piano della Flip, 4 viti M3 svasate |
| `visiera.stl` | 118 × 42 × 95,6 | 44 | 1 grigio traslucido | si avvita al piano dietro la culla; si stampa sul tettuccio, con i supporti solo sotto i piedi |
| `prova_giunta.stl` | 75 × 60 × 45,0 | 28 | 2 crema | la giunta sotto la MK4 in piccolo, le due metà insieme: da stampare prima |

Filamento: circa 1,0 kg in tutto, quasi tutto del colore del corpo. Viti delle giunte: 4 viti M3 × 6 a testa cilindrica (brugola) con i dadi.

## In Anycubic Slicer Next

1. Apri il `.3mf` del pezzo: arriva un oggetto con le sue parti, «corpo» e «scritte», e nelle vasche «fascia». Se lo slicer lo apre come più oggetti, o se preferisci gli STL: importa insieme gli STL del pezzo (`_corpo.stl`, `_scritte.stl`, `_fascia.stl`) e, alla domanda, caricali come un oggetto solo con più parti.
2. Tre filamenti, i PETG Anycubic di Luigi: 1 grigio traslucido, 2 crema, 3 rosso. Mascherina e piano della Flip: corpo 1 e scritte 3. Vasche: la fascia 1, cioè i primi 8 mm (40 strati, sotto le scritte dei fianchi), il corpo 2 e le scritte 3. Nel `.3mf` è già così; con gli STL si assegna a mano. La culla della Flip e la visiera col 1, la prova di giunta col 2.
3. Non girare i pezzi: le vasche stanno in piedi con il fondo sul piatto, mascherina e piano con la faccia in vista sul piatto. Il piatto liscio la fa lucida, quello testurizzato le dà la sua grana.
4. Strati da 0,2 e primo strato da 0,2: nei piani le scritte sono profonde 0,6 mm, cioè i primi tre strati. Nelle vasche il fianco è verticale e le scritte sono profonde 0,6 mm nella faccia di fuori: il filamento cambia in ogni strato fra il basso del marchio e la cima del nome, circa 127 strati per vasca. Torre di spurgo sì; spurgo nel riempimento se lo slicer lo offre. Se i cambi sono troppi, le vasche di `../stampa3d/` hanno il marchio in rilievo, di un colore.
5. Il resto come la console stampata a un colore: 3 perimetri, 4 strati pieni, riempimento al 20 %, senza supporti (solo la visiera, che si stampa sul tettuccio, li vuole sotto i piedi). Il primo strato deve essere perfetto: piatto pulito, livellamento fatto. Prima delle vasche, `prova_giunta.stl`.

## Le scritte

Le incisioni del laser sono troppo fini per un ugello da 0,4: qui le scritte sono ridisegnate con Matrice, il carattere 5×7 di Stame, a quadretti da 0,45 mm (lettere alte 3,15 mm) o da 0,40 dove non c'è posto. Logo e punti del nome restano quelli del laser. Sulla mascherina fra le due file di pad ci sono 2,8 mm: i tipi d'accordo e i piatti del banco B vanno sotto i pad, con l'estensione e il tamburo della stessa colonna, alto/basso come i pad: «DIM/6» è DIM sul pad di sopra e 6 su quello di sotto, «B:CHH/KICK» il charleston sopra e la cassa sotto. Le anteprime `anteprima_*.png` mostrano ogni faccia come la si guarda.

- **mascherina**: 30 scritte a 0,40 mm e 0,45 mm.
- **piano_flip**: 10 scritte a 0,45 mm.
- **fianco_sx**: 1 scritta a 0,45 mm.
- **fianco_dx**: 1 scritta a 0,45 mm.

Le giunte delle vasche e il montaggio sono come nella console a un colore: `../stampa3d/pezzi.md`.
