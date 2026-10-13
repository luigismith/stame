# 90 — Questioni aperte

> Indice di tutto quello che resta da verificare o decidere, al 13/10/2026. I dettagli e i test stanno nelle sezioni: qui ci sono solo l'elenco, la priorità e il rimando. Quando una questione si chiude, si aggiorna la sezione e la si toglie da qui.

## 1. Decisioni di Luigi

### 1.1 Già prese (13/10/2026)
| Decisione | Dove |
|---|---|
| Specifica completa prima del codice; repo in `D:\dev\stame`, privato su GitHub `luigismith/stame` | `00` |
| Sulla Flip lo schermo **non** clona l'OLED: plancia nativa 640×480 con tutto ciò che serve in tempo reale | `30` §4, PLT-062 |
| Pad del banco A = gli 8 tasti accordo dell'Orchid, stessa disposizione; pad del banco B = pulsanti funzione | MIDI-078 |
| Pressione delle manopole con un tasto dedicato della Flip: **X** (oltre a B8) | MIDI-084 |
| Tasti della Flip: schema a fuoco sempre attivo; modo tascabile opzionale, da MENU | MIDI-092…094 |
| STOP della MPK come scorciatoia del looper (pressione = stop o pausa, tenuto 1 s = Clear) | MIDI-078, D-2 |
| Uscita solo da MENU → Quit Stame | MIDI-095, PLT-057 |
| Preset di fabbrica privati caricati da `Saves/stame/privato/`, mai nel repo | PLT-069 |

### 1.2 Da prendere
| # | Questione | Proposta | Dove |
|---|---|---|---|
| 1 | Ultimo accordo in grigio dopo la persistenza («Ghost Chord») | Acceso per default, come opzione | `30` §9.3 |
| 2 | Lingua dei testi a schermo: inglese come l'Orchid, ma le categorie dei Sound in `20` sono in italiano | Tutto in inglese; tradurre le categorie in `20` | `30` §9.3, `20` |
| 3 | Tastiera della plancia fissa a 8 ottave | Sì: i registri restano sempre allo stesso posto | `30` §9.3 |
| 4 | Ingresso dal DIN IN attivo per default (rischio di anello MIDI) | Attivo, con rilevamento dell'eco | D-4 |
| 5 | Clock verso la porta 1 della MPK attivo per default | Sì | D-5 |
| 6 | ID SysEx `7D` con famiglia "ST" finché è un prototipo | Sì | D-6 |
| 7 | Nomi delle note: Do centrale = C4 in tutte le sezioni | Sì | D-7 |
| 8 | Disposizione del tavolo: Flip a sinistra della MPK, X sotto la mano sinistra | Da provare con le mani | PDF dei controlli |

## 2. Allineamenti tra sezioni ancora aperti
| Questione | Sezioni | Nota |
|---|---|---|
| Persistenza del nome dell'accordo: 1000 ms in `30`, 500 ms in ACC-056 | `10`, `30` | Un solo default; decide il test T-24 sull'Orchid |
| Rotazione con l'encoder tenuto (stato `HELD`): ignorata in MIDI-103, mandata alla lista aperta nella vecchia `30` | `30`, `40` | Da verificare sull'Orchid (per esempio Save Sound tenuto + rotazione) |
| Chi specifica la sintesi del kit di batteria e i Drum FX | `10`, `20` | QA-SND-30 |
| Batteria: avviso al 15% in `50`, avvisi dell'Orchid al 10% e al 5% in `30` | `30`, `50` | Coerenti, ma da tenere allineati |

## 3. Verifiche

### 3.1 Su un Orchid vero
Servono per la fedeltà; finché mancano vale il default [V] indicato nella sezione.

| Gruppo | Quante | Dove | Le più importanti |
|---|---|---|---|
| Accordi, voicing, Play Style, looper | 33 test (T-01…T-33) | `10` §14 | mappa del dial (W = v+24), Dim + m7, tempi di Strum/Slop/Harp, contenuto dei 13 pattern e dei 12 Beat |
| Suono | 32 questioni (QA-SND-01…32) | `20` | curve fisiche (inviluppi, LFO, cutoff, volumi), algoritmi FM 4 e 7, riverbero in serie o a mandata, parametri dei 12 bassi |
| Interfaccia (fase 2, OLED) | V-UI-01… | `30` §9.1 | tempi degli overlay, schermate senza immagini |
| MIDI | 15 (VO-…) | `40` | velocity con Velocity Sense Off, range dei BPM, CC di stato, FA/FC del looper |

### 3.2 Sulla MPK mini Plus di Luigi
30 verifiche (VM-1…VM-30) in `40`; i comandi sono nel §18 della guida alla Plus. Niente SysEx sui programmi senza backup e senza l'ok di Luigi.

Prima di scrivere il profilo `mpk_stame` servono almeno:
- VM-2: DIN come interfaccia; VM-8: Relative e accelerazione delle manopole; VM-9 e VM-29: joystick;
- VM-13: LED del trasporto; VM-22: Trpt e PadAT globali o del programma;
- **VM-30**: pad tenuto mentre si preme BANK (quale Note Off arriva) e colori dei pad per banco.

### 3.3 Sulla Miyoo Flip
| Gruppo | Dove | Le più importanti |
|---|---|---|
| Piattaforma (T-PLT-01…16) | `50` §15, §18 | parametri reali del PCM e underrun a 256 frame; latenza tasto → suono; `SCHED_FIFO`; PCM libero dopo PyUI; sospensione e coperchio; come spruce chiude le app |
| Plancia (VF-UI-01…04) | `30` §9.2 | leggibilità a un braccio di distanza; colori sul pannello; glifi di Spleen; tempo di disegno ≤ 4 ms |
| Tasti | `30`, `40` | posizione di MENU, SELECT e START; comodità di X + manopola e di A tenuto + croce; levetta a 12 settori del modo tascabile |

## 4. Dati che mancano del tutto
Senza un Orchid vero o una sua registrazione non si possono ricavare:
- le sequenze dei **13 pattern** e il contenuto dei **Beat** (`10` ha contenuti provvisori);
- i **parametri dei 12 bassi** (`20` usa patch scritte da Stame);
- i **tempi esatti** di Strum, Slop e Harp;
- il **font dell'OLED**, solo per la fase 2 (`30` §9.5).
