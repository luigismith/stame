# Stame — la console tutta stampata

Generato da `hardware/case/stampa3d.py` (piatto 210 × 210 mm). Ogni pezzo sta sul piatto così com'è nel file: nel verso giusto, con la faccia in vista in alto; quelli lunghi sono già ruotati in diagonale.

| File | Quanti | Ingombro (mm) | Colore | Note |
|---|---|---|---|---|
| `base_1.stl` | 1 | 189 × 128 × 6,0 | telaio: PLA o PETG color legno o sabbia | lastra da 6 mm; i tasselli si incollano a coda di rondine |
| `base_2.stl` | 1 | 189 × 128 × 6,0 | telaio: PLA o PETG color legno o sabbia | lastra da 6 mm; i tasselli si incollano a coda di rondine |
| `base_3.stl` | 1 | 182 × 128 × 6,0 | telaio: PLA o PETG color legno o sabbia | lastra da 6 mm; i tasselli si incollano a coda di rondine |
| `base_4.stl` | 1 | 189 × 123 × 6,0 | telaio: PLA o PETG color legno o sabbia | lastra da 6 mm; i tasselli si incollano a coda di rondine |
| `base_5.stl` | 1 | 189 × 123 × 6,0 | telaio: PLA o PETG color legno o sabbia | lastra da 6 mm; i tasselli si incollano a coda di rondine |
| `base_6.stl` | 1 | 182 × 130 × 6,0 | telaio: PLA o PETG color legno o sabbia | lastra da 6 mm; i tasselli si incollano a coda di rondine |
| `fianco_sx.stl` | 1 | 202 × 202 × 16,6 | telaio: PLA o PETG color legno o sabbia | quattro strati in uno; faccia esterna in alto, marchio e nome in rilievo; ruotato di 45° per stare sul piatto |
| `fianco_dx.stl` | 1 | 202 × 202 × 16,6 | telaio: PLA o PETG color legno o sabbia | quattro strati in uno; faccia esterna in alto, marchio e nome in rilievo; ruotato di 45° per stare sul piatto |
| `retro_sx_1.stl` | 1 | 154 × 46 × 8,0 | telaio: PLA o PETG color legno o sabbia | retro e strato d'appoggio in un pezzo |
| `retro_sx_2.stl` | 1 | 147 × 46 × 8,0 | telaio: PLA o PETG color legno o sabbia | retro e strato d'appoggio in un pezzo |
| `retro_dx.stl` | 1 | 206 × 206 × 8,0 | telaio: PLA o PETG color legno o sabbia | retro e strato d'appoggio in un pezzo; ruotato di 45° per stare sul piatto |
| `costola.stl` | 1 | 186 × 185 × 8,0 | telaio: PLA o PETG color legno o sabbia | i due strati della costola in un pezzo; ruotato di 42° per stare sul piatto |
| `fronte.stl` | 1 | 186 × 46 × 4,0 | telaio: PLA o PETG color legno o sabbia | parete davanti, la faccia esterna in alto |
| `mascherina_1.stl` | 1 | 201 × 134 × 3,0 | piani: nero | lastra da 3 mm; le scritte su carta adesiva, nelle tasche |
| `mascherina_2.stl` | 1 | 166 × 134 × 3,0 | piani: nero | lastra da 3 mm; le scritte su carta adesiva, nelle tasche |
| `piano_flip.stl` | 1 | 194 × 153 × 3,0 | piani: nero | lastra da 3 mm; le scritte su carta adesiva, nelle tasche |
| `culla_flip.stl` | 1 | 89 × 83 × 7,0 | nero | vassoio sul piano della Flip, 4 viti M3 svasate |
| `visiera.stl` | 1 | 126 × 70 × 103,6 | nero | si avvita al piano dietro la culla; stampare sul tettuccio, con supporti |
| `culla_pad.stl` | 1 | 185 × 86 × 47,0 | nero | sta sulla base fra costola, fianco e parete davanti; si stampa in piedi |
| `fermo_hub.stl` | 1 | 118 × 39 × 9,0 | nero | tiene l'hub sotto il piano, 2 viti nella base |
| `squadretta_m3.stl` | 6 | 20 × 12 × 12,0 | nero | base e fianchi, viti M3 |

Filamento: circa 1,3 kg in tutto (stima con 3 perimetri, 4 strati pieni sopra e sotto, riempimento al 20 %).

## Impostazioni

- PETG o PLA, ugello 0,4, strati da 0,2. Telaio (base, fianchi, retro, costola, parete davanti) in un colore legno o sabbia; mascherina, piano della Flip e culle in nero.
- 3 perimetri, 4 strati pieni sopra e sotto, riempimento giroide al 20 %. Senza supporti, tranne la visiera.
- Fianchi: il marchio e il nome escono di 0,6 mm dalla faccia esterna. Per averli in un altro colore, cambio di filamento (M600) alla quota 16,0 mm, cioè all'inizio del rilievo.
- Mascherina e piano della Flip: 47 tasche profonde 0,4 mm per le etichette (`etichette_mascherina.svg`, da stampare al 100 % su carta adesiva; `etichette_mappa.svg` dice dove va ogni numero).
- Tasselli: code di rondine con 0,15 mm di gioco per lato. Si incollano su un piano dritto con colla cianoacrilica o epossidica bicomponente; `tasselli.svg` mostra come stanno insieme.
