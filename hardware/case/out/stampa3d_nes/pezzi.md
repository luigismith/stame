# Stame — la console stampata a più colori, nei colori del NES

Generato da `hardware/case/multicolore.py` per un piatto di 240 × 240 mm (Anycubic Kobra S1 con l'ACE Pro, o un'altra stampante a più filamenti). Le stesse 3 vasche di `../stampa3d/` (con `--piatto 240`), stampate in piedi con il fondo sul piatto, e gli stessi pezzi che si tolgono; le scritte le fa la stampa, in un altro filamento: incassate a filo nella faccia in vista di mascherina e piano della Flip, che sta sul piatto, e nella faccia di fuori dei fianchi. Le istruzioni da stampare, con le anteprime, sono in `istruzioni_multicolore.pdf`.

| File | Ingombro (mm) | Grammi | Filamenti | Note |
|---|---|---|---|---|
| `vasca_sx.stl` | 200 × 240 × 45,0 | 240 | 2 crema | fianco sinistro con marchio e nome, retro, pedana della MK4; in piedi, il fondo sul piatto |
| `vasca_centro.stl` | 200 × 240 × 45,0 | 218 | 2 crema | retro con la finestra del pedale, pedana della MK4, costola; in piedi, il fondo sul piatto |
| `vasca_dx.stl` | 208 × 240 × 45,0 | 348 | 2 crema | retro con la finestra dell'audio e quella dell'hub, fermo dell'hub, colonnina, culla del pad, parete davanti, fianco destro con marchio e nome; in piedi, il fondo sul piatto |
| `mascherina_1.3mf` (o `mascherina_1_corpo.stl` + `mascherina_1_scritte.stl`) | 194 × 126 × 2,0 | 40 | corpo 1 grigio traslucido, scritte 3 rosso | la metà sinistra della mascherina; scritte incassate nella faccia in vista, che sta sul piatto |
| `mascherina_2.3mf` (o `mascherina_2_corpo.stl` + `mascherina_2_scritte.stl`) | 166 × 126 × 2,0 | 38 | corpo 1 grigio traslucido, scritte 3 rosso | la metà destra della mascherina; scritte incassate nella faccia in vista, che sta sul piatto |
| `piano_flip.3mf` (o `piano_flip_corpo.stl` + `piano_flip_scritte.stl`) | 200 × 140 × 2,0 | 61 | corpo 1 grigio traslucido, scritte 3 rosso | scritte incassate nella faccia in vista, che sta sul piatto |
| `targa_sx.3mf` (o `targa_sx_corpo.stl` + `targa_sx_scritte.stl`) | 232 × 37 × 2,0 | 20 | corpo 1 grigio traslucido, scritte 3 rosso | il marchio e il nome del fianco sx: si incolla nella sede del fianco, profonda 2,0 mm; scritte incassate nella faccia in vista, che sta sul piatto |
| `targa_dx.3mf` (o `targa_dx_corpo.stl` + `targa_dx_scritte.stl`) | 232 × 37 × 2,0 | 20 | corpo 1 grigio traslucido, scritte 3 rosso | il marchio e il nome del fianco dx: si incolla nella sede del fianco, profonda 2,0 mm; scritte incassate nella faccia in vista, che sta sul piatto |
| `culla_flip.stl` | 89 × 83 × 7,0 | 19 | 1 grigio traslucido | vassoio sul piano della Flip, 4 viti M3 svasate |
| `visiera.stl` | 118 × 42 × 95,6 | 44 | 1 grigio traslucido | si avvita al piano dietro la culla; si stampa sul tettuccio, con i supporti solo sotto i piedi |
| `prova_giunta.stl` | 75 × 60 × 45,0 | 28 | 2 crema | la giunta sotto la MK4 in piccolo, le due metà insieme: da stampare prima |

Filamento: circa 1,1 kg in tutto, quasi tutto del colore del corpo. Viti delle giunte: 4 viti M3 × 6 a testa cilindrica (brugola) con i dadi.

## In Anycubic Slicer Next

1. Apri il `.3mf` del pezzo: arriva un oggetto con le sue parti, «corpo» e «scritte». Se lo slicer lo apre come più oggetti, o se preferisci gli STL: importa insieme gli STL del pezzo (`_corpo.stl`, `_scritte.stl`) e, alla domanda, caricali come un oggetto solo con più parti.
2. Tre filamenti, i PETG Anycubic di Luigi: 1 grigio traslucido, 2 crema, 3 rosso. Mascherina, piano della Flip e le due targhe dei fianchi: corpo 1 e scritte 3. Le vasche sono di un filamento solo, il 2: il marchio e il nome dei fianchi stanno sulle targhe, che si incollano nella loro sede, profonda 2,0 mm. Nel `.3mf` è già così; con gli STL si assegna a mano. La culla della Flip e la visiera col 1, la prova di giunta col 2.
3. Non girare i pezzi: le vasche stanno in piedi con il fondo sul piatto, mascherina e piano con la faccia in vista sul piatto. Il piatto liscio la fa lucida, quello testurizzato le dà la sua grana.
4. Strati da 0,2 e primo strato da 0,2: nei piani le scritte sono profonde 0,6 mm, cioè i primi tre strati, e il filamento cambia solo lì: le targhe sono come i piani, e le vasche non cambiano mai. Torre di spurgo sì, sui piatti dei pezzi piatti; i pezzi grandi come il piatto vanno da soli, senza cambi.
5. Il resto come la console stampata a un colore: 3 perimetri, 4 strati pieni, riempimento al 20 %, senza supporti (solo la visiera, che si stampa sul tettuccio, li vuole sotto i piedi). Il primo strato deve essere perfetto: piatto pulito, livellamento fatto. Prima delle vasche, `prova_giunta.stl`.

## Il lavoro già pronto

`stame_kobra_s1.3mf` è un progetto di Anycubic Slicer Next per la Kobra S1 (`progetto.py`): tutti i pezzi tranne la prova di giunta, su sei piatti, un piatto per colore principale, con le parti e i filamenti già assegnati, 3 perimetri, 4 strati pieni, giroide al 20 % e i supporti solo sotto i piedi della visiera. Le vasche, crema, hanno un piatto ciascuna e nessun cambio, quindi niente torre; i pezzi grigi con le scritte rosse cambiano filamento solo nei primi tre strati, e sui loro piatti la torre ha il suo posto. Si apre (File › Apri progetto), si affetta un piatto alla volta e, mandandolo alla stampante, si abbinano i tre filamenti agli slot dell'ACE Pro. I piatti: 1 vasca sinistra, crema; 2 vasca di centro, crema; 3 vasca destra, crema; 4 mascherina sinistra, grigio e rosso; 5 mascherina destra e visiera, grigio e rosso; 6 piano della Flip e culla, grigio e rosso; 7 targhe dei fianchi, grigio e rosso.

## Le targhe

Il marchio e il nome dei fianchi stanno su due targhe grigie con le scritte rosse (`targa_sx`, `targa_dx`), stampate come la mascherina, con la faccia in vista sul piatto. Ogni fianco ha la sua sede, profonda 2,0 mm, 0,15 mm più larga della targa per lato: una goccia di cianoacrilica o un biadesivo sottile, e la targa sta a filo del fianco.

## Le scritte

Le incisioni del laser sono troppo fini per un ugello da 0,4: qui le scritte sono ridisegnate con Matrice, il carattere 5×7 di Stame, a quadretti da 0,45 mm (lettere alte 3,15 mm) o da 0,40 dove non c'è posto. Logo e punti del nome restano quelli del laser. Sulla mascherina fra le due file di pad ci sono 2,8 mm: i tipi d'accordo e i piatti del banco B vanno sotto i pad, con l'estensione e il tamburo della stessa colonna, alto/basso come i pad: «DIM/6» è DIM sul pad di sopra e 6 su quello di sotto, «B:CHH/KICK» il charleston sopra e la cassa sotto. Le anteprime `anteprima_*.png` mostrano ogni faccia come la si guarda.

- **mascherina**: 30 scritte a 0,40 mm e 0,45 mm.
- **piano_flip**: 14 scritte a 0,45 mm.
- **fianco_sx**: 1 scritta a 0,45 mm.
- **fianco_dx**: 1 scritta a 0,45 mm.

Le giunte delle vasche e il montaggio sono come nella console a un colore: `../stampa3d/pezzi.md`.
