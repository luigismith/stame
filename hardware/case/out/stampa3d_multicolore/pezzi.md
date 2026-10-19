# Stame — la console stampata a più colori

Generato da `hardware/case/multicolore.py` per un piatto di 240 × 240 mm (Anycubic Kobra S1 con l'ACE Pro, o un'altra stampante a più filamenti). Gli stessi pezzi di `../stampa3d/`; mascherina, piano della Flip e fianchi hanno le scritte stampate: incassate a filo nella faccia in vista, che sta sul piatto. Le istruzioni da stampare, con le anteprime dei pezzi, sono in `istruzioni_multicolore.pdf`.

| File | Ingombro (mm) | Colore | Note |
|---|---|---|---|
| `mascherina_1.3mf` (o `mascherina_1_corpo.stl` + `mascherina_1_scritte.stl`) | 201 × 134 × 3,0 | piani: nero | scritte incassate nella faccia in vista, che sta sul piatto |
| `mascherina_2.3mf` (o `mascherina_2_corpo.stl` + `mascherina_2_scritte.stl`) | 166 × 134 × 3,0 | piani: nero | scritte incassate nella faccia in vista, che sta sul piatto |
| `piano_flip.3mf` (o `piano_flip_corpo.stl` + `piano_flip_scritte.stl`) | 200 × 152 × 3,0 | piani: nero | scritte incassate nella faccia in vista, che sta sul piatto |
| `fianco_sx.3mf` (o `fianco_sx_corpo.stl` + `fianco_sx_scritte.stl`) | 202 × 202 × 16,0 | telaio: PLA o PETG color legno o sabbia | scritte incassate nella faccia in vista, che sta sul piatto; ruotato di 45° per stare sul piatto |
| `fianco_dx.3mf` (o `fianco_dx_corpo.stl` + `fianco_dx_scritte.stl`) | 202 × 202 × 16,0 | telaio: PLA o PETG color legno o sabbia | scritte incassate nella faccia in vista, che sta sul piatto; ruotato di 45° per stare sul piatto |
| `base_1.stl` | 191 × 129 × 6,0 | telaio: PLA o PETG color legno o sabbia | lastra da 6 mm; i tasselli si incollano a coda di rondine |
| `base_2.stl` | 192 × 129 × 6,0 | telaio: PLA o PETG color legno o sabbia | lastra da 6 mm; i tasselli si incollano a coda di rondine |
| `base_3.stl` | 182 × 129 × 6,0 | telaio: PLA o PETG color legno o sabbia | lastra da 6 mm; i tasselli si incollano a coda di rondine |
| `base_4.stl` | 191 × 122 × 6,0 | telaio: PLA o PETG color legno o sabbia | lastra da 6 mm; i tasselli si incollano a coda di rondine |
| `base_5.stl` | 192 × 122 × 6,0 | telaio: PLA o PETG color legno o sabbia | lastra da 6 mm; i tasselli si incollano a coda di rondine |
| `base_6.stl` | 182 × 122 × 6,0 | telaio: PLA o PETG color legno o sabbia | lastra da 6 mm; i tasselli si incollano a coda di rondine |
| `retro_sx.stl` | 236 × 236 × 8,0 | telaio: PLA o PETG color legno o sabbia | retro e strato d'appoggio in un pezzo; ruotato di 45° per stare sul piatto |
| `retro_dx.stl` | 210 × 210 × 8,0 | telaio: PLA o PETG color legno o sabbia | retro e strato d'appoggio in un pezzo; ruotato di 45° per stare sul piatto |
| `costola.stl` | 236 × 46 × 8,0 | telaio: PLA o PETG color legno o sabbia | i due strati della costola in un pezzo |
| `fronte.stl` | 192 × 46 × 4,0 | telaio: PLA o PETG color legno o sabbia | parete davanti, la faccia esterna in alto |
| `culla_flip.stl` × 1 | 89 × 83 × 7,0 | nero | vassoio sul piano della Flip, 4 viti M3 svasate |
| `visiera.stl` × 1 | 126 × 70 × 103,6 | nero | si avvita al piano dietro la culla; stampare sul tettuccio, con supporti |
| `culla_pad.stl` × 1 | 191 × 87 × 47,0 | nero | sta sulla base fra costola, fianco e parete davanti; si stampa in piedi |
| `fermo_hub.stl` × 1 | 175 × 65 × 10,5 | nero | tiene l'hub sotto il piano, 2 viti nella base |
| `squadretta_m3.stl` × 6 | 20 × 12 × 12,0 | nero | base e fianchi, viti M3 |

Filamento: circa 1,3 kg in tutto, quasi tutto del colore del corpo.

## In Anycubic Slicer Next

1. Apri il `.3mf` del pezzo: arriva un oggetto con due parti, «corpo» e «scritte». Se lo slicer lo apre come due oggetti, o se preferisci gli STL: importa insieme `_corpo.stl` e `_scritte.stl` e, alla domanda, caricali come un oggetto solo con più parti.
2. Due filamenti in tutto: 1 nero, 2 sabbia (o il colore scelto per il telaio). Mascherina e piano della Flip: corpo 1 e scritte 2, come l'incisione del laser sull'acrilico nero. Fianchi: corpo 2 e scritte 1, come la bruciatura sul legno. Nel `.3mf` è già così; con gli STL si assegna a mano. Gli altri pezzi del telaio vanno col 2, culle e visiera col 1.
3. Non girare il pezzo: la faccia in vista è già sul piatto. Il piatto liscio la fa lucida, quello testurizzato le dà la sua grana.
4. Strati da 0,2 e primo strato da 0,2: le scritte sono profonde 0,6 mm, cioè tre strati, quindi i cambi di filamento sono solo lì. Torre di spurgo sì; spurgo nel riempimento se lo slicer lo offre.
5. Il resto come la console stampata: 3 perimetri, 4 strati pieni, riempimento al 20 %, senza supporti tranne la visiera. Il primo strato deve essere perfetto: piatto pulito, livellamento fatto.

## Le scritte

Le incisioni del laser sono troppo fini per un ugello da 0,4: qui le scritte sono ridisegnate con Matrice, il carattere 5×7 di Stame, a quadretti da 0,45 mm (lettere alte 3,15 mm) o da 0,40 dove non c'è posto. Logo e punti del nome restano quelli del laser. Sulla mascherina fra le due file di pad ci sono 2,8 mm: i tipi d'accordo e i piatti del banco B vanno sotto i pad, con l'estensione e il tamburo della stessa colonna, alto/basso come i pad: «DIM/6» è DIM sul pad di sopra e 6 su quello di sotto, «B:CHH/KICK» il charleston sopra e la cassa sotto. Le anteprime `anteprima_*.png` mostrano ogni faccia come la si guarda.

- **mascherina**: 30 scritte a 0,40 mm e 0,45 mm.
- **piano_flip**: 10 scritte a 0,45 mm.
- **fianco_sx**: 1 scritte a 0,45 mm.
- **fianco_dx**: 1 scritte a 0,45 mm.
