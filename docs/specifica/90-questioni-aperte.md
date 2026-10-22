# 90 — Questioni aperte

> Indice di tutto quello che resta da verificare o decidere, al 14/10/2026. I dettagli e i test stanno nelle sezioni: qui ci sono solo l'elenco, la priorità e il rimando. Quando una questione si chiude, si aggiorna la sezione e la si toglie da qui.

## 1. Decisioni di Luigi

### 1.1 Già prese (13/10/2026)
| Decisione | Dove |
|---|---|
| Specifica completa prima del codice; repo in `D:\dev\stame`, privato su GitHub `luigismith/stame` | `00` |
| Sulla Flip lo schermo **non** clona l'OLED: plancia nativa 640×480 con tutto ciò che serve in tempo reale | `30` §4, PLT-062 |
| Pad del banco A = gli 8 tasti accordo dell'originale, stessa disposizione; pad del banco B = pulsanti funzione | MIDI-078 |
| Pressione delle manopole con un tasto dedicato della Flip: **X** (oltre a B8) | MIDI-084 |
| Tasti della Flip: schema a fuoco sempre attivo; modo tascabile opzionale, da MENU | MIDI-092…094 |
| STOP della MPK come scorciatoia del looper (pressione = stop o pausa, tenuto 1 s = Clear) | MIDI-078, D-2 |
| Uscita solo da MENU → Quit Stame | MIDI-095, PLT-057 |
| Preset di fabbrica privati caricati da `Saves/stame/privato/`, mai nel repo | PLT-069 |
| **Macro pad BRIMFORD** (12 tasti, 3 manopole, solo via cavo) e **nuova mappa dei controlli**, chiesta da Luigi («rimappa i controlli alla luce di questo nuovo device»): K1–K8 e T1–T8 griglie gemelle (K1 Sound, K2 Perform, K3 FX, K4 Key / K5 Bass, K6 Loop, K7 BPM, K8 Volume); M = Chord Voicing, m1 = Bass Voicing, m2 = liste; T9 Options, T10 Back, T11 Menu, T12 Panic tenuto 1 s | MIDI-078, MIDI-120…129, D-8; `30` UI-131, UI-152, UI-155 |
| Con il macro pad, il banco B della MPK e il PUSH (B8 o X) restano come **riserva** | MIDI-078, MIDI-084 |
| Bozza del **case** che tiene insieme MPK, macro pad e Flip | `60-case.md` |

### 1.2 Da prendere
| # | Questione | Proposta | Dove |
|---|---|---|---|
| 1 | Ultimo accordo in grigio dopo la persistenza («Ghost Chord») | Acceso per default, come opzione | `30` §9.3 |
| 2 | Lingua dei testi a schermo: inglese come l'originale, ma le categorie dei Sound in `20` sono in italiano | Tutto in inglese; tradurre le categorie in `20` | `30` §9.3, `20` |
| 3 | ~~Tastiera della plancia fissa a 8 ottave~~ | **Decisa il 13/10/2026**: 4 ottave che seguono le finestre, tasti più grandi (UI-150) | `30` §9.3 |
| 4 | Ingresso dal DIN IN attivo per default (rischio di anello MIDI) | Attivo, con rilevamento dell'eco | D-4 |
| 5 | Clock verso la porta 1 della MPK attivo per default | Sì | D-5 |
| 6 | ID SysEx `7D` con famiglia "ST" finché è un prototipo | Sì | D-6 |
| 7 | Nomi delle note: Do centrale = C4 in tutte le sezioni | Sì | D-7 |
| 8 | Disposizione del tavolo: la bozza del case mette la MPK davanti, il macro pad a destra e la Flip dietro; X resta la riserva del PUSH | Da provare con le mani, insieme al case | `60-case.md`, PDF dei controlli |
| 9 | Comodità della nuova mappa con il macro pad: Tn + Kn a due mani, m1 tenuta come modificatore, T12 tenuto per il Panic | Da provare con le mani dopo VP-3 e VP-5 | D-8, MIDI-121 |
| 10 | ~~Contenuto del blob `STM1` (PLT-065) rispetto a `impostazioni.txt` e `stato.txt` (PLT-066)~~ | **Decisa il 14/10/2026**: lo stesso testo chiave=valore dei due file, così un solo lettore serve a tutti e due (PLT-065) | `50` §9 |

## 2. Allineamenti tra sezioni ancora aperti
| Questione | Sezioni | Nota |
|---|---|---|
| Persistenza del nome dell'accordo: 1000 ms in `30`, 500 ms in ACC-056 | `10`, `30` | Un solo default; decide il test T-24 sull'originale |
| Rotazione con l'encoder tenuto (stato `HELD`): ignorata in MIDI-103, mandata alla lista aperta nella vecchia `30` | `30`, `40` | Da verificare sull'originale (per esempio Save Sound tenuto + rotazione) |
| Chi specifica la sintesi del kit di batteria e i Drum FX | `10`, `20` | QA-SND-30 |
| Batteria: avviso al 15% in `50`, avvisi dell'originale al 10% e al 5% in `30` | `30`, `50` | Coerenti, ma da tenere allineati |
| L2 e R2: premuti sopra 128 e rilasciati sotto 64 in MIDI-091, sopra 160 e sotto 96 in PLT-055; zona morta delle levette 50% in MIDI-091, 20% in PLT-055 | `40`, `50` | Un solo valore; decide T-PLT-10. Servono solo al modo tascabile (fase F5) |
| Coda dell'ingresso: in MIDI-004 porta eventi del pannello, fonde le rotazioni e fa aspettare il produttore se è piena; in PLT-015/016 porta MIDI grezzo (`q_midi_in`) e scarta, senza mai aspettare | `40`, `50` | Il codice segue `50`: profili e riconoscitore girano nel thread audio (`inp_t`, 14/10/2026). MIDI-004 va riscritto |

## 3. Verifiche

### 3.1 Sull'originale
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

### 3.3 Sul macro pad BRIMFORD
8 verifiche (VP-1…VP-8) in `40`, Questioni aperte. Prima di scrivere il profilo `pad_brimford` servono almeno:
- **VP-1**: VID:PID, nome evdev, nodi creati, `EVIOCGRAB` su tutti;
- **VP-2**: il software sikaicase o `ch57x-keyboard-tool` ammettono F13–F24 e KP1–KP9 (se no, Learn Pad, MIDI-123);
- **VP-3**: tasti e pressioni delle manopole mandano «giù» e «su» separati (serve per tenere, per Tn + Kn e per m1 come modificatore).

Poi: VP-4 scatti persi o accorpati nelle rotazioni veloci; VP-5 posizione delle manopole e quale è M, m1, m2; VP-6 consumo sulla porta OTG insieme alla MPK, sull'hub senza PD; VP-7 RGB spento; VP-8 chiusa il 19/10/2026: il colore dei LED (solo globale per strato) finisce nella flash a ogni scrittura, quindi Stame non lo comanda; si sceglie una volta dal PC.

### 3.4 Sulla Miyoo Flip
| Gruppo | Dove | Le più importanti |
|---|---|---|
| Piattaforma (T-PLT-01…16) | `50` §15, §18 | parametri reali del PCM e underrun a 256 frame; latenza tasto → suono; `SCHED_FIFO`; PCM libero dopo PyUI; sospensione e coperchio; come spruce chiude le app |
| Plancia (VF-UI-01…04) | `30` §9.2 | leggibilità a un braccio di distanza; colori sul pannello; glifi di Spleen; tempo di disegno ≤ 4 ms |
| Tasti | `30`, `40` | posizione di MENU, SELECT e START; comodità di X + manopola e di A tenuto + croce; levetta a 12 settori del modo tascabile; numerazione evdev del gamepad con il macro pad collegato all'avvio (PLT-053, MIDI-090) |
| Suoni e batteria del 19/10/2026 | `20` SND-540…543, `10` ACC-218 | ascolto dei suoni 151–200 (livelli a −17 dBFS misurati sul PC) e dei 35 kit della libreria con i loro Beat: bilanciamento fra gli strumenti, quanto sporcano i kit con meno bit, il campanaccio e i metalli a sei quadre semplici; CPU del thread audio con dieci voci di metallo e il synth pieno (stima del 5 % di un core, SND-543) |
| Suoni e batteria del 22/10/2026 | `20` SND-541, `10` ACC-215, ACC-218, ACC-219 | ascolto dei suoni 201–232 e dei bassi 25–38 (livelli a −17 e −24 dBFS misurati sul PC con la nota tenuta 6 s), dei kit Psy Forest, Goa Temple e Trance Arena con i loro Beat e stili; il gate di Gated Lily è tarato su circa 138 BPM e non segue il tempo (SND-410: gli LFO non hanno sync) |
| AMBIENT e basso che rotola del 22/10/2026 | `10` ACC-219, ACC-260…264, `40` MIDI-142, MIDI-143, `60` CASE-045 | provati sul PC con la vetrina vera (WAV di 90 s con Ghost Orchid e Hadal Drone, e con Tundra Bell in Glass): da ascoltare sulla Flip le tavolozze delle sei atmosfere, quanto è fitta la densità 4 di fabbrica, la pausa di un quarto prima che il modulo riprenda dopo un accordo di chi suona, il basso Rolling a 145 BPM con Rolling Root; se aggiungere alla legenda incisa delle manopole la colonna BLOOMS, MOOD, MOTION (la bozza 5 è approvata) |

## 4. Dati che mancano del tutto
Senza l'originale o una sua registrazione non si possono ricavare:
- le sequenze dei **13 pattern** e il contenuto dei **Beat** (`10` ha contenuti provvisori);
- i **parametri dei 12 bassi** (`20` usa patch scritte da Stame);
- i **tempi esatti** di Strum, Slop e Harp;
- il **font dell'OLED**, solo per la fase 2 (`30` §9.5).
