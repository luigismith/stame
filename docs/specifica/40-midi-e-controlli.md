# 40 — MIDI e controlli

Questa sezione descrive come Stame **parla MIDI** e come **riceve i comandi** di chi suona:
- il MIDI in uscita e in ingresso dell'originale, replicato in modo fedele (canali, note, CC di stato, clock, trasporto, ingresso);
- i vincoli su identità, SysEx e nomi delle porte;
- la **Akai MPK mini Plus** come superficie di controllo, con il programma "STAME";
- il **macro pad BRIMFORD** (15 tasti e 3 manopole), che dà agli encoder dell'originale i pulsanti che la MPK non ha (profilo `pad_brimford`, §8.10);
- i tasti fisici della **Miyoo Flip**, sia insieme alla MPK sia senza;
- lo **strato di input logico**, che separa i controller dal nucleo;
- hot-plug, disconnessione, note appese e panic.

Il comportamento musicale (accordi, Play Style, looper, beat) sta in `10-accordi-e-performance.md`. Qui si definisce solo **cosa entra e cosa esce** e in che forma.

**Etichette** (da `CONVENZIONI.md`)
- `[M]` manuale o documentazione ufficiale: per l'originale il manuale v4.1, il supporto del costruttore e le note di firmware; per la MPK la User Guide v1.2 e la knowledge base Akai.
- `[O]` osservato: per l'originale le catture MIDI e l'analisi statica del firmware 3.92 pubblicate da un utente (RSMR); per la MPK le catture di terzi (algo-synth #420), il codice dell'estensione Bitwig e le prove fatte sulla Flip.
- `[D]` dedotto o ricostruito: scelta di progetto o inferenza.
- `[V]` da verificare: è il valore di default scelto per ora. Il test è indicato come **VO-n** (da fare sull'originale) o **VM-n** (da fare sulla MPK di Luigi collegata alla Flip; VM-n è il test n del §18 della guida alla Plus) o **VP-n** (da fare sul macro pad BRIMFORD collegato alla Flip). Elenco completo in [Questioni aperte](#questioni-aperte).

---

## 1. Confini

| Dentro questa sezione | Fuori (sezione) |
|---|---|
| Formato e ordine dei messaggi MIDI, canali, clock, trasporto, SysEx, nomi | Quale accordo o quale nota suonare (`10`) |
| Mappa dei controlli MPK e Flip verso le funzioni dell'originale | Disegno di overlay, menu e messaggi a schermo (`30`) |
| Eventi logici del pannello e riconoscimento dei gesti | Thread, ALSA rawmidi, evdev, budget di latenza (`50`) |
| Hot-plug, panic, note appese | Mappa dei 135 parametri usata dagli NRPN (`20`) |

---

## 2. Architettura: dai byte agli eventi del nucleo

```
 platform/flip                         core (C11 puro, portabile)
 ┌───────────────────────┐   byte    ┌──────────────┐  midi_msg_t  ┌──────────────────────┐
 │ rawmidi MPK porta 1   │──────────▶│ midi_parse   │─────────────▶│ profilo controller   │
 │ rawmidi MPK porta 2   │──┐        └──────────────┘              │ (mpk_stame,          │
 │ evdev /dev/input/...  │  │                                      │  mpk_fabbrica,       │
 │  → codici PAD_*       │──┼──────────── pad_event_t ────────────▶│  flip_tasti, …)      │
 └───────────────────────┘  │                                      └──────────┬───────────┘
            ▲               │  midi_msg_t (porta 2 = DIN IN)                  │ pnl_event_t
            │               └─────────────────────────────┐                   ▼
            │                                             │        ┌──────────────────────┐
            │                                             └───────▶│ midi_in (semantica   │
            │                                                      │ dell'originale)      │
            │                                                      ├──────────────────────┤
            │   midi_out_msg_t (con timestamp in campioni)         │ gesti → nucleo       │
            └──────────────────────────────────────────────────────│ (accordi, looper, UI)│
                                                                   │ midi_out + registro  │
                                                                   └──────────────────────┘
```

- **MIDI-001** — L'input DEVE essere diviso in quattro strati [D]:
  1. `platform/flip` legge byte grezzi (rawmidi) e eventi evdev, e li traduce in byte MIDI o in codici portabili `PAD_*`;
  2. `core/midi_parse` trasforma i byte in messaggi MIDI completi (`midi_msg_t`);
  3. un **profilo controller** trasforma i messaggi del controller in **eventi del pannello** (`pnl_event_t`, §10.1);
  4. il **riconoscitore dei gesti** del nucleo trasforma gli eventi del pannello nei gesti dell'originale (premere, ruotare, tenere, premere e ruotare: §10.3).
- **MIDI-002** — Il nucleo musicale (accordi, performance, looper, interfaccia) NON DEVE vedere byte MIDI né codici evdev dei controller: riceve solo `pnl_event_t`. L'unica eccezione è l'ingresso MIDI musicale (§5), che passa da `core/midi_in` con la semantica dell'originale [D].
- **MIDI-003** — Parser, profili e riconoscitore dei gesti DEVONO essere C11 puro, senza SDL, ALSA, evdev né `malloc`: tabelle `const` e stato statico. Così lo stesso profilo MPK gira sulla Flip e sull'hardware dedicato [D].
- **MIDI-004** — Tra il thread di input e il nucleo DEVE esserci una coda SPSC lock-free a dimensione fissa (default 256 eventi [D]). Se la coda è piena:
  - più `PNL_ENC_TURN` consecutivi dello stesso encoder DEVONO essere fusi sommando gli scatti;
  - gli eventi di pressione e rilascio (`*_DOWN`, `*_UP`) NON DEVONO mai essere scartati: se non c'è spazio, il produttore aspetta [D].
- **MIDI-005** — Il parser DEVE [O, codice della guida alla Plus §17.4]:
  - gestire il running status in ingresso;
  - accettare i messaggi real time (≥ `F8`) in qualunque punto, anche dentro un SysEx, senza interromperlo;
  - raccogliere i SysEx in un buffer statico di 4096 byte; oltre, il messaggio viene troncato e marcato come non valido;
  - chiudere un SysEx con `F7` o con qualunque status byte non real time;
  - ignorare i byte di dati orfani (senza status valido);
  - trattare un Note On con velocity 0 come Note Off.
- **MIDI-006** — Ogni `midi_msg_t` e ogni `pnl_event_t` DEVE portare il tempo d'arrivo in microsecondi (orologio monotono), per misurare latenza e gesti a tempo [D].

---

## 3. MIDI in uscita (replica dell'originale)

### 3.1 Flussi e canali

- **MIDI-010** — Stame DEVE produrre tre flussi MIDI, come l'originale [M]:

| Flusso | Contenuto | Canale di default |
|---|---|---|
| **Performance** | Quello che suona davvero: arpeggi, strum, pattern, note singole, melodie fatte con il voicing | 1 [M] |
| **Bass** | Le note del basso | 2 [M] |
| **Chord** | L'accordo in blocco, **qualunque sia la performance** | **Off** [M, dal firmware 3.90] |

- **MIDI-011** — Ogni flusso DEVE poter andare su un canale da 1 a 16 oppure su **Off**, da Options > Audio and MIDI > MIDI Channels [M]. Le scelte DEVONO restare salvate allo spegnimento [D]. Due flussi POSSONO condividere un canale (§3.2, registro).
- **MIDI-012** — Tutte le destinazioni fisiche (§3.6) DEVONO ricevere gli stessi dati: sull'originale DIN e USB portano gli stessi messaggi [M].

### 3.2 Note On e Note Off

- **MIDI-013** — Formato [O]:
  - Note On `9n kk vv` con `vv` da 1 a 127;
  - Note Off **sempre** `8n kk 00`: Stame NON DEVE mai trasmettere un Note On con velocity 0 al posto del Note Off;
  - Stame NON DEVE usare il running status in uscita: ogni messaggio porta il suo status byte [D, le catture dell'originale mostrano sempre lo status].
- **MIDI-014** — Ordine dei messaggi nello stesso istante:
  - Note On: **Chord → Bass → Performance**. L'ordine Chord prima di Performance è osservato [O]; la posizione del Bass è scelta [V VO-8];
  - Note Off: **Performance → Bass → Chord**. Performance prima di Chord è osservato [O]; il Bass [V VO-8].
- **MIDI-015** — Quando una nota o un accordo ne sostituisce un altro, i Note Off delle note vecchie DEVONO precedere i Note On delle nuove, flusso per flusso [O].
- **MIDI-016** — **Registro delle note.** Stame DEVE tenere, per ogni destinazione, un contatore per coppia (canale, nota) [D]:
  - a ogni attacco trasmette il Note On e incrementa il contatore;
  - al rilascio decrementa; trasmette il Note Off **solo** quando il contatore torna a zero;
  - un Note Off con contatore già a zero NON DEVE essere trasmesso.

  Così due flussi sullo stesso canale non producono note spezzate, e non esce mai un Note Off doppio. Con il firmware 3.92 l'originale manda un secondo Note Off sul ch3 alla pressione successiva [O]; le note del 3.90 lo danno per corretto [M]. Stame segue l'intenzione dichiarata e **non** copia il difetto.
- **MIDI-017** — Stame PUÒ offrire un'opzione di debug "Doppio Note Off 3.92", spenta per default, che riproduce il difetto sul flusso Chord per i confronti con l'originale (Appendice A).
- **MIDI-018** — Dalla tastiera le note singole sono **monofoniche** [M]: sul flusso Performance esce al massimo una nota singola alla volta. La logica (quale tasto vince) sta in `10`.
- **MIDI-019** — Il numero di nota trasmesso DEVE essere l'altezza effettivamente suonata dal motore, compreso l'effetto di voicing, Split/Octave e transpose. Dal 3.90 le ottave mostrate a schermo coincidono con quelle MIDI [M]; la convenzione scelta per Stame è Do centrale = nota 60 = "C4" [V VO-13].

### 3.3 Velocity

- **MIDI-020** — La velocity dei Note On DEVE venire dalla forza sul tasto (sulla MPK: la velocity del tasto, §8.5) [M]. Con Options > Instrument > Velocity Sense = Off DEVE essere un valore fisso: **100** [V VO-1]. I pattern scalano la loro velocity con quella del tasto e rispettano Sense Off [M]; il calcolo sta in `10`.

### 3.4 CC di stato

- **MIDI-021** — Stame DEVE trasmettere i CC di stato dell'originale [O]:

| CC | Quando esce | Valore |
|---|---|---|
| 103 | Cambio della quantità della Perform | Indice del sottotipo nel modo corrente: Off = 0, primo sottotipo = 1, … (es. Strum01 = 1, Strum02 = 2) |
| 104 | Scelta di un modo di Perform | Sempre 127: non dice quale modo |
| 107 | Scelta della Key | Indice 0–41: le 21 tonalità maggiori, poi le stesse 21 minori (22 = Do♯ minore). L'elenco ordinato sta in `10`. Uno scatto non è un semitono |
| 108 | Key mode accesa o spenta | 127 accesa, 0 spenta |
| 112 | Ogni scatto dell'encoder BPM; anche tra `FC` e `FA` quando si sceglie un beat (§4.2) | BPM intero. Sopra 127: **127** [V VO-2] |
| 113 | Ogni scatto dell'encoder Volume (master) | Relativo: 1 = +1, 127 = −1 |

  - Canale: quello del flusso **Performance**; con Performance su Off i CC di stato NON DEVONO uscire [V VO-3]. Nelle catture escono sul ch1, che è il default della Performance [O].
  - Un CC di stato esce solo per un'azione sul pannello, mai per un cambio arrivato da MIDI in ingresso o da un preset richiamato [D].
- **MIDI-022** — L'analisi statica del firmware indica anche CC 115 e 116 (voicing di accordo e basso) e CC 118 (FX Lock), mai catturati [O]. Finché non si conoscono valori e momenti, Stame NON DEVE trasmetterli [V VO-5].

### 3.5 Messaggi mai trasmessi

- **MIDI-023** — Come l'originale, Stame NON DEVE trasmettere [O]: Program Change, Pitch Bend, Aftertouch di canale e polifonico, CC 1, 7, 64 e qualunque CC musicale, Continue (`FB`), Song Position Pointer, MTC, Active Sensing, System Reset, Channel Mode (CC 120–127, salvo il panic del §7). In particolare pitch wheel, mod wheel e pedale della MPK agiscono sul suono interno ma **non** vengono inoltrati (l'inoltro è un'opzione dell'Appendice A).
- **MIDI-024** — Il looper registra eventi, non audio [M]. In riproduzione i suoi eventi DEVONO uscire sui tre flussi esattamente come se fossero suonati dal vivo [V VO-9; nel 3.92 il loop manda almeno le note del basso, O]. I beat di batteria e il metronomo NON DEVONO produrre MIDI [V VO-10].

### 3.6 Destinazioni fisiche sulla Flip

Sulla Flip la porta USB-C OTG fa da **host** per la MPK, quindi Stame non può presentarsi a un computer come dispositivo USB-MIDI [D]. L'equivalente dell'uscita DIN dell'originale è il **DIN OUT della MPK**, raggiunto attraverso la sua porta 2.

- **MIDI-025** — Destinazioni:

| Destinazione | Cosa riceve | Default |
|---|---|---|
| **DIN** = MPK porta 2 → DIN OUT | I tre flussi, i CC di stato, clock e trasporto, le risposte SysEx | Sempre attiva quando la MPK è collegata [M per il ruolo di interfaccia, UG p.7; V VM-2] |
| **MPK porta 1** (controllo) | Clock e trasporto (§4.4), LED del trasporto (§8.7), copia del basso per la CV (§8.7) | Clock: attivo [D]; CV: spenta |
| Altre (interfaccia USB-MIDI su hub, RTP-MIDI, gadget USB) | — | Solo Appendice A |

- **MIDI-026** — Sulla porta 1 NON DEVONO uscire i tre flussi: le Note On sul ch1 con note 115–119 accendono i LED del trasporto e una nota sul canale della CV muoverebbe la CV [O]/[D].
- **MIDI-027** — Il DIN viaggia a 31 250 bit/s: circa 1 ms per un messaggio da 3 byte [D]. Lo scrittore MIDI DEVE:
  - scrivere ogni messaggio intero con una sola `write()`, senza spezzarlo tra thread;
  - dare la precedenza a `F8`, `FA`, `FC` rispetto ai messaggi in coda, inserendoli al primo confine di messaggio;
  - non accumulare più di 64 messaggi in coda per destinazione; oltre, scartare i CC di stato più vecchi, mai i Note Off [D].

---

## 4. Clock e trasporto

### 4.1 Principi

- **MIDI-030** — Stame DEVE trasmettere il **MIDI clock** (`F8`) a **24 PPQN**, **solo mentre il trasporto è in moto** [O]. Come l'originale dal 3.60, il clock esce e basta: in ingresso il clock NON DEVE avere effetto (il clock in è un'opzione dell'Appendice A) [M].
- **MIDI-031** — La MPK non manda clock MIDI, nemmeno con Seq Play [O]: **Stame è sempre il master**.
- **MIDI-032** — Gli istanti dei tick DEVONO essere calcolati dal contatore dei campioni audio, sulla stessa griglia di beat, looper e performance. Requisiti [D]:
  - nessuna deriva cumulativa rispetto all'audio;
  - jitter di `F8` sul filo (USB verso la MPK) non superiore a 1 ms;
  - il nucleo produce eventi con timestamp in campioni; lo strato di piattaforma li scrive all'istante giusto (dettagli in `50`). NON DEVE uscire un gruppo di tick tutti insieme a ogni blocco audio.
- **MIDI-033** — Dopo un `FA` il primo `F8` DEVE coincidere con l'inizio della battuta del trasporto interno; i successivi seguono ogni 1/24 di quarto [D].

### 4.2 Stato del trasporto ed eventi

Il trasporto ha due stati: **FERMO** (nessun `F8`) e **IN MOTO** (`F8` continui). All'accensione è FERMO [D].

- **MIDI-034** — Transizioni e messaggi:

| Azione | Messaggi in uscita | Stato dopo | Etichetta |
|---|---|---|---|
| Premere BPM (accende o spegne beat o metronomo) | `FC` `FA`, in entrambi i casi | IN MOTO | [O] |
| Scegliere un beat nel menu Beats | `FC`, CC 112 = BPM, `FA` | IN MOTO | [O] |
| Beat in mute (pressione di BPM dal 3.60) | Nessun messaggio in più: `F8` continua | IN MOTO | [M]/[O] |
| Spegnere il metronomo senza beat né loop | `FC` `FA` (riga 1); `F8` continua | IN MOTO | [V VO-6] |
| Inizio del count-in del loop (sincronia BPM) | `FA` | IN MOTO | [V VO-7] |
| Inizio della registrazione in Free (prima nota) | `FA` | IN MOTO | [V VO-7] |
| Navigare nel menu Loop (Waiting Room, scelta della sincronia) | Nessuno | invariato | [V VO-7]: nelle catture ci sono `FA` e `FC` non attribuiti a una voce precisa |
| Pausa del loop | `FC`, poi i Note Off delle note in corso | FERMO | [O] |
| Ripresa del loop dalla pausa | `FA` (mai `FB`) | IN MOTO | [V VO-7] |
| Uscita dal loop, morbida o hard, con beat e metronomo spenti | `FC` | FERMO | [V VO-7] |
| Uscita dal loop con beat o metronomo attivo | Nessuno | IN MOTO | [V VO-7] |
| Ruotare BPM | CC 112 = nuovo BPM | invariato | [O] |

- **MIDI-035** — Stame NON DEVE trasmettere `FB`, Song Position Pointer né MTC [O, mai visti].

### 4.3 Range del tempo

- **MIDI-036** — Il BPM va da 60 a 200 [O; range ufficiale non documentato, V VO-2]. Il clock segue ogni cambio di BPM dal tick successivo, senza `FC`/`FA` [D].

### 4.4 Destinazioni del clock

- **MIDI-037** — Clock e trasporto DEVONO uscire sul DIN (porta 2), come l'uscita DIN dell'originale [D: il manuale dice che DIN e USB portano gli stessi dati; V VO-11].
- **MIDI-038** — Clock e trasporto DOVREBBERO uscire anche sulla **porta 1** della MPK (opzione "Clock alla MPK", attiva per default) [D]. Con il clock della Plus su **External**, arpeggiatore, sequencer e **Clock Out analogico** seguono Stame [M UG p.7; V VM-5, VM-6].

---

## 5. MIDI in ingresso (replica dell'originale)

L'originale riceve MIDI solo via USB [M]. Sulla Flip l'equivalente è il **DIN IN della MPK**, che arriva sulla porta 2 [M UG p.7].

- **MIDI-040** — La porta 2 della MPK (DIN IN) DEVE essere trattata come l'ingresso MIDI dell'originale, con la semantica di questo paragrafo. È attiva per default [D: rischio di anello se il DIN OUT torna nel DIN IN attraverso un thru esterno, decisione D-4 nelle Questioni aperte].
- **MIDI-041** — Note [M]:
  - note sul **ch1**: suonano il motore Sound in modo **polifonico**, **senza** motore degli accordi né Perform;
  - note sul **ch2**: suonano il motore Bass;
  - velocity 0 = Note Off;
  - note su qualunque altro canale, ch10 compreso: nessun effetto [O].
  - I canali di ingresso restano fissi a 1 e 2 e non seguono il menu MIDI Channels [V VO-4].
  - Le voci vengono dal pool comune di 16 voci [O]; il furto di voce sta in `20`.
- **MIDI-042** — Controller riconosciuti [O, analisi statica]:

| Messaggio | Effetto |
|---|---|
| CC 1 | Modulazione del motore del canale (ch1 Sound, ch2 Bass) |
| CC 64 | Sustain: qualunque valore diverso da 0 = acceso |
| Pitch Bend | Bend del motore del canale; ampiezza dal parametro BENDRANGE, 0–12 semitoni, default 2 |
| NRPN: CC 99 (MSB) + CC 98 (LSB) + CC 6 (valore) | Parametro di indice (MSB·128 + LSB): ch1 Sound e ch2 Bass, indici 0–134; ch3 drum, indici 0–52. Mappa degli indici in `20` |
| CC 120 | All Sound Off: silenzio immediato del motore del canale |
| CC 121 | Reset All Controllers: bend al centro, modulazione 0, sustain spento |
| CC 123 | All Notes Off: rilascio di tutte le note del motore del canale |

  - Esempio di prova [O]: `B0 63 00` · `B0 62 44` · `B0 06 64` porta il CUTOFF (indice 68) del Sound a 100.
- **MIDI-043** — DEVONO essere ignorati [O]: Program Change, Aftertouch, CC 7, CC 100–119 (compresi i CC di stato che Stame stessa trasmette), CC 122, CC 124–127, Master Volume universale, clock, Start, Stop, Continue, MMC, SPP.
- **MIDI-044** — Le estensioni dell'ingresso (CC di stato come comandi, Program Change per il Sound, CC 7, "ingresso accordi", clock in) NON DEVONO essere attive per default: sono opzioni dell'Appendice A [D, principio di fedeltà].

---

## 6. Identità, SysEx e nomi

- **MIDI-050** — Stame NON DEVE usare l'ID SysEx del produttore **`00 22 0C`** (quello dell'originale) [M tabella midi.org; O], né in uscita né come intestazione riconosciuta: i SysEx in ingresso con quell'ID DEVONO essere ignorati senza risposta.
- **MIDI-051** — Nessun nome esposto da Stame (porta ALSA, client del sequencer, sessione RTP-MIDI, nome Bluetooth, stringhe USB, nome di file di preset scambiati con altri) PUÒ cominciare con il **nome dell'originale**, confrontando in minuscolo dopo aver tolto gli spazi iniziali. L'updater ufficiale prende le porte proprio con quel prefisso [M, JavaScript della pagina firmware]. Il nome da usare è **"Stame"** [D].
- **MIDI-052** — A un Identity Request (`F0 7E <7F o il proprio device ID> 06 01 F7`) ricevuto dall'ingresso MIDI (§5), Stame DEVE rispondere sul DIN con [D]:

```
F0 7E 7F 06 02  7D  53 54  01 00  <maj> <min> <patch> 00  F7
               id    fam.   memb.  versione (binaria, 7 bit per byte)
```

  - `7D` = ID per uso non commerciale, da usare nei prototipi [M midi.org]; un prodotto vero richiede un ID MMA proprio;
  - famiglia `53 54` ("ST"); membro `01 00` = versione per la Flip;
  - device ID della risposta `7F`, come l'originale [O].
- **MIDI-053** — Stame PUÒ implementare un SysEx proprio con la stessa struttura di quello dell'originale [D]:
  - trama `F0 7D 53 54 <cmd> <payload…> <cs> F7`;
  - checksum `cs = (−Σ byte da 7D all'ultimo byte di payload) & 0x7F`;
  - risposta `F0 7D 53 54 7E <cmd> <val> F7`, senza checksum.

  Comandi proposti: scelta di Sound e di Bass, voicing di accordo e di basso, scrittura di un parametro (motore, indice, valore), interrogazioni, dump completo e ripristino. Nessun comando può cancellare o scrivere la memoria permanente senza una conferma a schermo.
- **MIDI-054** — Stame NON DEVE cercare la compatibilità con l'editor dell'originale né con l'updater ufficiale (trame "Tlp" `F0 54 6C 70 …`), che DEVONO essere ignorate [D].

---

## 7. Note appese, cambi di canale e panic

- **MIDI-060** — Se si cambia il canale di un flusso, o lo si mette su Off, mentre ci sono note accese, Stame DEVE mandare subito i Note Off di quelle note **sul canale vecchio** e azzerare le voci relative nel registro [D].
- **MIDI-061** — Nessun cambio di selettore (Sound, Perform, Key, Play Style, modalità del basso, basso on/off, voicing) può lasciare una nota senza Note Off. Il registro (MIDI-016) è la fonte di verità: ogni nota che il nucleo smette di suonare DEVE passare da un rilascio esplicito. Sull'originale, con il firmware 3.84, cambiare i selettori mentre si suona lascia note appese [O]: è un difetto e Stame NON DEVE copiarlo.
- **MIDI-062** — **Panic.** Comandi: PUSH + Stop sulla MPK (§8.5), T12 del macro pad tenuto 1 s (§8.10), voce "Panic" del menu di sistema (tasto MENU della Flip, §9), ricollegamento della MPK (§11). Effetto [D]:
  1. per ogni destinazione e ogni (canale, nota) con contatore > 0: Note Off `8n kk 00`; poi registro azzerato;
  2. CC 123 (All Notes Off) e CC 120 (All Sound Off) sui canali dei tre flussi e su quello della CV, se attivi;
  3. motori interni: tutte le voci in rilascio rapido (tempo in `20`), sustain spento, bend al centro.

  L'originale non trasmette mai CC 120 o 123 [O]: il panic è una deviazione voluta, solo su comando o al ricollegamento, mai nel funzionamento normale.
- **MIDI-063** — All'uscita dall'app Stame DEVE: mandare i Note Off di tutte le note nel registro; mandare `FC` se il trasporto è in moto; spegnere i LED del trasporto della MPK; chiudere le porte [D].

---

## 8. MPK mini Plus come superficie di controllo

### 8.1 Identificazione e porte

| Voce | Valore | Etichetta |
|---|---|---|
| USB | VID:PID **09E8:0054**, class compliant, Full Speed | [O] |
| Interfacce | HID (ignorata), Audio Control, MIDIStreaming con 2 cable | [O] |
| Porta 1 (cable 0) | Controller: tasti, pad, manopole, ruote, joystick, trasporto, pedale. Riceve clock, LED del trasporto, SysEx. Risponde all'Identity | [O] |
| Porta 2 (cable 1) | Il DIN usato come interfaccia: IN = quello che arriva dal DIN IN, OUT = DIN OUT. Non risponde ai SysEx e non genera nulla di suo | [M UG p.7; O] |
| Linux | Una scheda, `/dev/snd/midiC<N>D0` con sottodispositivi 0 (porta 1) e 1 (porta 2); `/proc/asound/card<N>/usbid` = `09e8:0054`; porte "MPK mini Plus MIDI 1" e "… MIDI 2" | [D; V VM-25] |
| Identity | `F0 7E 7F 06 02 47 54 00 19 00 <fw 3 byte> …` (`47` Akai, `54` prodotto, `19 00` membro); firmware 1.13 = `01 01 03` | [O] |

- **MIDI-070** — Stame DEVE riconoscere la MPK dal file `usbid` (`09e8:0054`) e NON DEVE memorizzare il numero di scheda: va ricercato a ogni collegamento [D; V VM-26].
- **MIDI-071** — Apertura delle porte [O, guida §13.10 e §17.4]:
  - porta 1 = sottodispositivo 0, porta 2 = sottodispositivo 1, scelti con `SNDRV_CTL_IOCTL_RAWMIDI_PREFER_SUBDEVICE` sul control della scheda, tenuto aperto durante l'`open()`;
  - `open()` con `O_RDWR | O_NONBLOCK`: senza `O_NONBLOCK` una porta occupata blocca;
  - dopo l'apertura, `SNDRV_RAWMIDI_IOCTL_INFO` DEVE confermare il sottodispositivo; se non coincide, la porta va chiusa e trattata come occupata (`EBUSY`);
  - con `EBUSY` Stame DEVE mostrare "MPK occupata da un'altra app" e riprovare ogni secondo (§11).
- **MIDI-072** — I messaggi della porta 1 vanno **solo** al profilo controller; quelli della porta 2 **solo** all'ingresso MIDI (§5) [D].
- **MIDI-073** — Al collegamento Stame DEVE mandare l'Identity Request `F0 7E 7F 06 01 F7` sulla porta 1, attendere al massimo 1 s, controllare il prefisso `47 54 00 19` e registrare il firmware. Senza risposta continua comunque, segnalandolo nel log [D].
- **MIDI-074** — I messaggi real time e i SysEx diversi dall'Identity Reply che arrivano dalla porta 1 DEVONO essere ignorati [D].
- **MIDI-075** — Messaggi della porta 1 su canali diversi da 1 (tasti e controlli) e 10 (pad) DEVONO essere ignorati: per esempio il sequencer interno della MPK, che nel programma STAME manda sul ch3 e sul ch11 [D].

### 8.2 Collegamento e alimentazione (sintesi)

- La MPK va sulla porta USB-C **di sopra** della Flip (OTG automatico), con un cavo USB-C → USB-B. La porta OTG NON DEVE mai essere forzata in modalità host [O]. Dettagli in `50`.
- La MPK prende i 5 V dall'USB e dichiara 100 mA; il consumo reale con pad, OLED e CV è ignoto [O; V VM-1]. Se la Flip non regge, serve un hub USB 2.0 semplice alimentato (le dock con Power Delivery non funzionano) [O].
- Con un host USB la MPK fa del DIN un'interfaccia: **quello che si suona sulla MPK non esce dal DIN OUT** finché l'host non lo rimanda sulla porta 2 [M UG p.7; V VM-2]. Per questo è Stame a pilotare il DIN (§3.6).
- Dall'host si accendono solo i **LED del trasporto**: LED dei pad e display non hanno un protocollo noto [O; V VM-12]. Lo stato di Stame si legge sullo schermo della Flip.

### 8.3 Il programma "STAME"

- **MIDI-076** — Stame DEVE essere suonata con un programma dedicato della MPK, chiamato **"STAME"**, preparato una volta con il Program Editor su PC e salvato nello **slot 8** [D]:

| Voce | Valore | Perché |
|---|---|---|
| Nome del programma | `STAME` | Compare sul display della MPK [M UG p.19] |
| Canale tastiera e controlli | **1** | Manopole e joystick stanno per forza sul canale dei tasti [M]: Stame li distingue dal numero di CC |
| Canale pad | **10** | Come di fabbrica; separa i pad dalla tastiera |
| Pad | Modo **Note**, Toggle **Off**; banco A note 36–43, banco B note 44–51 | Velocity disponibile; con il Toggle lo stato del pad si disallineerebbe da quello di Stame |
| Colori dei pad | Banco A: fila alta (tipi) e fila bassa (estensioni) di due colori diversi; banco B (riserva senza macro pad, §8.5): un terzo colore, B8 (PUSH) di un quarto | Distinguere a colpo d'occhio tipi, estensioni e funzioni. Indici della palette 0–31 da scegliere sull'unità [V VM-12] |
| Aftertouch dei pad (PadAT) | **Off** | L'originale non ha pressione; meno traffico. Forse è un'impostazione globale [V VM-22] |
| Manopole K1–K8 | **Relative**, CC **70–77**, Lo 0, Hi 127; nomi "Sound", "Perform", "FX", "Key", "Bass", "Loop", "BPM", "Volume" (mappa del 13/10/2026, §8.5) | Encoder veri: lo stato resta in Stame e non ci sono salti. Se l'OLED mostri i nomi [V VM-16] |
| Joystick | **2CC**: X → XCC1 13, XCC2 12; Y → YCC1 3, YCC2 2 | Quattro direzioni distinte. Quale CC sia il verso positivo [V VM-9] |
| Trasporto (Trpt) | **On/Off** | Serve il rilascio (127 alla pressione, 0 al rilascio) per i gesti "tenuto". Forse globale [V VM-22] |
| Arp, Chords, Scales, Note Repeat, Full Level | **Off** | Altrimenti la MPK trasforma le note prima che arrivino a Stame |
| Ottava, Transpose | **0**, **0** | — |
| Sequencer interno | Vuoto; Key Seq sul ch3, Pad Seq sul ch11 | Le sue note, se usato, restano fuori dai canali di Stame |
| CV | Src **MIDI 16**, Order **Last**, Gate **Legato**, Bend 2 | La CV segue solo la copia del basso sul ch16 (§8.7). Con Src = MIDI 1 anche le Note On dei LED muoverebbero la CV [D] |
| Clock (Sync) | **External** | Stame è il master (§4.4) |

- **MIDI-077** — Stame NON DEVE leggere né scrivere programmi della MPK via SysEx (comandi `0x64` scrittura, `0x66` lettura) se non sono soddisfatte **tutte** queste condizioni [D, decisione di Luigi]:
  1. backup di tutti gli 8 programmi fatto con l'editor (Get Program + salvataggio dei file `.mpkminiplus`);
  2. formato confermato dai test VM-10, VM-21 e VM-24;
  3. ok esplicito di Luigi;
  4. opzione "Carica STAME via SysEx" accesa a mano (è spenta per default e non compare nel menu finché i punti 1–3 non sono fatti).

  Il comando `0x64` sovrascrive il programma in RAM, sequenze comprese [O]. Lo stesso vale per il Program Change verso la MPK [V VM-11]. L'Identity Request è ammesso: non modifica nulla.

### 8.4 Cosa manda la MPK

Con il programma STAME, sulla porta 1 [O per il programma di fabbrica; D per STAME, che cambia solo modi e numeri di CC]:

| Controllo | Messaggio |
|---|---|
| 37 tasti | ch1 `90 kk vv` / `80 kk 00`; l'ottava della MPK cambia `kk` |
| Pitch wheel | ch1 `E0 lsb msb`, 14 bit, centro `00 40` |
| Mod wheel | ch1 CC 1 (resta dove la si lascia) |
| Pedale | ch1 CC 64, valori e polarità [V VM-15] |
| Manopole K1–K8 | ch1 CC 70–77, complemento a due a 7 bit: `01` = +1, `7F` = −1; accelerazione probabilmente assente [O/D; V VM-8] |
| Joystick | ch1 CC 13/12 (X), 3/2 (Y), 0 a riposo, fino a 127 a fondo corsa [V VM-9, VM-29] |
| Pad banco A | ch10 note 36–43 (pad 1–4 fila bassa = 36–39, pad 5–8 fila alta = 40–43) [O; M per la numerazione] |
| Pad banco B | ch10 note 44–51 (B1–B4 fila bassa = 44–47, B5–B8 fila alta = 48–51) |
| Trasporto | ch1 CC 115 «, 116 », 117 Stop, 118 Play, 119 Rec: 127 alla pressione, 0 al rilascio |
| Arp, Chords, Scales, Note Repeat, Full Level, Shift, Home, Bank, Prog Select, OCT, Seq Play, Tap, encoder di menu | **Nulla**: l'host non li vede [O] |

### 8.5 Mappa controllo MPK → funzione dell'originale

- **MIDI-078** — Il profilo `mpk_stame` DEVE applicare questa mappa [D, sulla base della proposta della guida alla Plus §17.6; **decisa da Luigi il 13/10/2026**; manopole **rimappate il 13/10/2026** per il macro pad, §8.10]:
  - i pad del **banco A** fanno gli **8 tasti accordo a sinistra dell'originale**, nella stessa disposizione: fila alta Dim, Min, Maj, Sus; fila bassa 6, m7, M7, 9. È la regola di Luigi: «se l'originale ha 8 pulsanti a sinistra i pad di mpk devono funzionare come quegli otto pulsanti»;
  - le manopole **K1–K8** ruotano gli otto encoder che il macro pad affianca con i tasti T1–T8, nella stessa posizione: fila alta **K1 Sound, K2 Perform, K3 FX, K4 Key**; fila bassa **K5 Bass, K6 Loop, K7 BPM, K8 Volume**. Chord Voicing e Bass Voicing non hanno più una manopola sulla MPK: stanno sulle manopole M e m1 del macro pad (§8.10) e, senza macro pad, si raggiungono con il fuoco (§9.1);
  - i pad del **banco B** restano i **pulsanti funzione** (Key, Bass, Perform, Chord Voicing, Loop, BPM, Options e PUSH), ma dal 13/10/2026 sono una **riserva** per quando il macro pad non c'è: con il macro pad collegato i pulsanti degli encoder sono T1–T9, M e m1;
  - la **pressione delle manopole**: con la MK4 è **SHIFT + K** (MIDI-130), dal 16/10/2026 l'unica strada (**deciso da Luigi**: «vedo comandi replicati sui vari device... questa cosa non mi piace», ogni comando in una casa sola); con la Plus resta B8 (PUSH) **oppure il tasto X della Flip** (§8.6, decisione del 13/10/2026). I tasti T1–T8 del macro pad non premono più gli encoder: fanno le aggiunte di MIDI-133.

| Controllo MPK | Messaggio | Evento del pannello (§10.1) | Funzione dell'originale |
|---|---|---|---|
| **37 tasti** | ch1 note `kk`, velocity `vv` | `PNL_KEY_DOWN/UP(kk % 12, vv)` | I 12 tasti della tastiera |
| **Pad A5** (fila alta) | ch10 nota 40 | `PNL_CHORD_DOWN/UP(CHB_DIM)` | Tasto accordo **Dim** |
| **Pad A6** | 41 | `CHB_MIN` | **Min** |
| **Pad A7** | 42 | `CHB_MAJ` | **Maj** |
| **Pad A8** | 43 | `CHB_SUS` | **Sus** |
| **Pad A1** (fila bassa) | 36 | `CHB_6` | Estensione **6** |
| **Pad A2** | 37 | `CHB_MIN7` | Estensione **m7** |
| **Pad A3** | 38 | `CHB_MAJ7` | Estensione **M7** |
| **Pad A4** | 39 | `CHB_9` | Estensione **9** |
| **K1** | CC 70 relativo | `PNL_ENC_TURN(ENC_SOUND, n)` | Encoder Sound (uno scatto = un suono) |
| **K2** | CC 71 | `ENC_PERFORM` | Encoder Perform |
| **K3** | CC 72 | `ENC_FX` | Encoder FX |
| **K4** | CC 73 | `ENC_KEY` | Encoder Key |
| **K5** | CC 74 | `ENC_BASS` | Encoder Bass (scelta del basso) |
| **K6** | CC 75 | `ENC_LOOP` | Encoder Loop (menu del looper) |
| **K7** | CC 76 | `ENC_BPM` | Encoder BPM |
| **K8** | CC 77 | `ENC_VOLUME` | Encoder Volume |
| **Pad B8 o X della Flip tenuto + Kn** (riserva) | ch10 nota 51 (o `PAD_X`) + CC 70–77 | `PNL_ENC_DOWN/UP` dell'encoder di Kn (§8.6) | Premere, tenere, premere e ruotare l'encoder di Kn |
| **Pad B1** (riserva) | 44 | `PNL_ENC_DOWN/UP(ENC_KEY)` | Pulsante di Key: premere = Key mode on/off; tenere = quick select |
| **Pad B2** (riserva) | 45 | `ENC_BASS` | Pulsante di Bass: premere = basso on/off; tenere 1 s = modalità |
| **Pad B3** (riserva) | 46 | `ENC_PERFORM` | Pulsante di Perform: premere = lista dei modi; tenere = Lock |
| **Pad B4** (riserva) | 47 | `ENC_CHORD_VOICING` | Pulsante del Chord Voicing: Split ↔ Octave |
| **Pad B5** (riserva) | 48 | `ENC_LOOP` | Pulsante di Loop |
| **Pad B6** (riserva) | 49 | `ENC_BPM` | Pulsante di BPM: beat o metronomo; tenere = tempo in chiave → Beats |
| **Pad B7** (riserva) | 50 | `ENC_OPTIONS` | Pulsante di Options |
| **Rec** | CC 119 | `PNL_ENC_DOWN/UP(ENC_LOOP)` | Loop (doppione di B5, sempre a portata) |
| **Play** | CC 118 | `PNL_ENC_DOWN/UP(ENC_BPM)` | BPM: beat o metronomo (doppione di B6) |
| **Stop** | CC 117 | pressione: `MACRO_LOOP_STOP`; tenuto ≥ 1 s: `MACRO_LOOP_CLEAR` | Scorciatoie per le voci del menu Loop: Stop della registrazione o dell'overdub, Pause in riproduzione; Clear |
| **PUSH (B8) + Stop** | 51 + CC 117 | `MACRO_PANIC` | Panic (§7) |
| **«** / **»** | CC 115 / 116 | `PNL_ENC_TURN(ENC_FOCUS, −1/+1)` | Ruota l'encoder che ha il fuoco (§10.4): liste, Options e, senza macro pad, Chord Voicing e Bass Voicing |
| **Joystick su / giù** | CC 3 / CC 2 sopra soglia | `PNL_ENC_TURN(ENC_FOCUS, +1/−1)`, con ripetizione | Come « » |
| **Joystick destra** | CC 13 sopra soglia | `PNL_ENC_DOWN` + `PNL_ENC_UP(ENC_FOCUS)` | Conferma (pressione dell'encoder con il fuoco) |
| **Joystick sinistra** | CC 12 sopra soglia | `PNL_BACK` | Chiude l'overlay o risale di un livello nel menu |
| **Pitch wheel** | `E0` | `PNL_BEND` | Bend del Sound, come un Pitch Bend in ingresso sul ch1 (MIDI-042) |
| **Mod wheel** | CC 1 | `PNL_MOD` | Modulazione del Sound, come CC 1 in ingresso sul ch1 |
| **Pedale** | CC 64 | `PNL_SUSTAIN` | Sustain del Sound, come CC 64 in ingresso sul ch1 (il latch è un'opzione dell'Appendice A) |
| SHIFT, Arp, Chords, Scales, Bank, OCT, Home, Prog Select, Seq Play, Tap, encoder di menu | nulla | — | Non usabili: lavorano solo dentro la MPK |

Combinazioni dell'originale con il **Bass Voicing tenuto** [M]. Il modificatore è la pressione della manopola **m1** del macro pad (§8.10) oppure il tasto **Y** della Flip (§9.1). La MPK da sola non ha più una manopola di Bass Voicing, quindi non lo si tiene con PUSH + manopola. Tenendo il modificatore si preme:
- T6, Rec o B5 → **uscita hard dal loop**;
- T7, Play o B6 → **batteria da suonare** ("On drums") [O];
- T5 o B2 → basso on/off.

Rispetto alla proposta della guida (§17.6) cambiano due cose:
- **B3** diventa il pulsante completo di Perform (premere = lista, tenere = Lock) invece del solo Lock;
- dal 13/10/2026 le manopole seguono la griglia gemella del macro pad (K1 Sound … K8 Volume), e Chord Voicing e Bass Voicing passano alle manopole M e m1 del macro pad.

- **MIDI-079** — Tastiera [D]:
  - la fondamentale è `kk % 12` (0 = Do); l'ottava fisica e l'ottava della MPK NON DEVONO influire, perché l'originale ha un'ottava sola e il registro lo decidono voicing e Split/Octave [M];
  - per ogni classe di nota il profilo DEVE contare i tasti fisici premuti: `PNL_KEY_DOWN` al primo, `PNL_KEY_UP` quando si rilascia l'ultimo. Un secondo tasto della stessa classe non produce eventi;
  - la velocity passa invariata [V VO-1, curva da confrontare con l'originale].
- **MIDI-080** — Pad del banco A: la velocity dei pad NON DEVE avere effetto, perché i tasti accordo dell'originale sono pulsanti in gomma senza velocity [M]; la dinamica dell'accordo viene dal tasto. L'aftertouch dei pad (`A9`, `D9`) DEVE essere ignorato [D].
- **MIDI-081** — Manopole [O/D]:
  - delta = `v < 64 ? v : v − 128` (complemento a due a 7 bit);
  - uno scatto ogni `step` unità accumulate: `step` = 2 per K1–K6 (Sound, Perform, FX, Key, Bass, Loop), 1 per K7 (BPM) e K8 (Volume) [V VM-8];
  - se la MPK manda passi più grandi di 1 (accelerazione), il delta si somma così com'è.
- **MIDI-082** — Joystick: soglia di attivazione 100 e di riarmo 60 per ciascuno dei 4 CC [O, valore usato da uno script di terzi; V VM-29]. Su e giù ripetono: primo passo all'attivazione, poi uno ogni 200 ms dopo 400 ms [D].
- **MIDI-083** — Trasporto: finché dal collegamento non è arrivato almeno un valore 0 su CC 115–119, il profilo DEVE considerare la MPK in Trpt = On (nessun rilascio) e:
  - per Rec e Play, emettere `PNL_ENC_DOWN` e subito `PNL_ENC_UP`;
  - per Stop, emettere solo `MACRO_LOOP_STOP` (niente Clear).

  Dal primo 0 in poi vale la mappa completa [D].

- **MIDI-089** — **Banco dei pad.** La MPK ha **8 pad fisici**: BANK A/B cambia solo le note mandate, e l'host non vede il tasto BANK [O]. Quindi [D, 13/10/2026]:
  - il profilo DEVE stimare il banco attivo dall'ultima nota di pad ricevuta (36–43 = A, 44–51 = B) e passarlo a `ui_model_t` come **stima**: «banco A», «banco B» o «sconosciuto» all'avvio. La plancia mostra la legenda dei pad di quel banco;
  - quando arriva una nota del banco B mentre tasti accordo del banco A risultano premuti, il profilo DEVE emettere i loro `PNL_CHORD_UP` sintetici prima dell'evento del banco B. Così un cambio di banco con un pad tenuto non lascia un accordo appeso. Vale anche al contrario per i pulsanti del banco B (`PNL_ENC_UP`, PUSH rilasciato);
  - un Note Off di pad senza il Note On corrispondente DEVE essere ignorato senza errori;
  - cosa manda la MPK se si preme BANK con un pad tenuto (il Note Off ha la nota del banco vecchio o del nuovo?) va verificato [V VM-30]: se manda la nota del banco vecchio, la seconda regola diventa una semplice rete di sicurezza. Finché VM-30 non risponde, stima e rilasci contano anche i Note Off, così è coperto il caso peggiore (Note Off con la nota del banco nuovo). Se la MPK manda la nota del banco vecchio, vanno ristretti ai Note On: altrimenti il rilascio di un pad tenuto da prima del cambio rilascia anche un pulsante tenuto nel banco nuovo [D, 14/10/2026];
  - ogni funzione del banco B DEVE avere anche una strada che non richiede di cambiare banco: macro pad (§8.10), trasporto, PUSH (B8 o X della Flip) + manopola, oppure fuoco e tasti della Flip. Le funzioni da usare mentre si suona (looper, beat, pressione delle manopole) DEVONO stare su comandi sempre disponibili: i tasti del macro pad e, senza macro pad, REC, STOP, PLAY e X.

### 8.6 Gesti degli encoder sulla MPK: il pad PUSH

Le manopole della MPK non si premono. Con la **MK4** il PUSH è il suo tasto **SHIFT** (MIDI-130), proposto da Luigi il 15/10/2026 («basti un solo tasto tipo shift») e dal 16/10/2026 **l'unica strada**: B8 e X non contano sulla MK4 e il macro pad non ha più i pulsanti degli encoder (MIDI-133). Con la **Plus** il PUSH resta il pad **B8** o il **tasto X della Flip** (decisione di Luigi del 13/10/2026: «per simulare la pressione delle manopole, dedica un tasto sulla flip»): fa da "pressione" per l'encoder della manopola toccata subito dopo; B8 e X sono intercambiabili e la stessa macchina a stati li tratta come un solo comando PUSH, premuto se lo è almeno uno dei due.

- **MIDI-084** — Macchina a stati del PUSH [D, ricostruita dalla guida §17.6]. Qui "PUSH giù / su" vuol dire B8 Note On / Note Off oppure X premuto / rilasciato:

```
stati: IDLE, ARMED, TARGET(k)            k = manopola 0..7, enc[k] = encoder dell'originale
PUSH giù:              IDLE      -> ARMED
scatto della manopola k (n scatti):
    ARMED              -> emetti PNL_ENC_DOWN(enc[k]); scarta gli n scatti;
                          t_sel = adesso; stato TARGET(k)
    TARGET(k), stessa k, adesso - t_sel < 150 ms -> scarta (tremolio della selezione)
    TARGET(k), stessa k -> emetti PNL_ENC_TURN(enc[k], n)   // il riconoscitore: "premi e ruota"
    altrimenti         -> emetti PNL_ENC_TURN(enc[j], n)    // rotazione normale
PUSH su (rilasciati sia B8 sia X):
    TARGET(k)          -> emetti PNL_ENC_UP(enc[k])
    tutti              -> IDLE
Stop (CC 117 = 127) in ARMED o TARGET -> emetti MACRO_PANIC (e niente MACRO_LOOP_STOP)
```

  Il riconoscitore (§10.3) trasforma `DOWN`/`UP`/`TURN` in premere, tenere, premere e ruotare. Esempi:
  - B8 + piccolo tocco a K4, rilascio di B8 → **premere Key** (Key mode on/off);
  - B8 + tocco a K4 + rotazione di K4 → **premere e ruotare Key** (transpose);
  - B8 + tocco a K1, B8 tenuto 1 s → **tenere Sound** (Save / Save As / Delete);
  - B8 + tocco a K8 → **premere Volume** (livello della batteria, qui quella della Flip).

  Con la MK4 gli stessi gesti sono SHIFT + K4 toccata, SHIFT + K4 girata, SHIFT + K1 toccata e tenuta 1 s, SHIFT + K8 toccata.

### 8.7 Uscite verso la MPK

- **MIDI-085** — LED del trasporto, sulla porta 1, con Note On sul ch1 e la nota uguale al numero del CC (`90 73…77 7F` acceso, `… 00` spento) [O; V VM-13]:

| LED | Acceso quando | Etichetta |
|---|---|---|
| Rec (119) | Loop in registrazione o in overdub; durante il count-in lampeggia a ogni quarto | [D] |
| Play (118) | Beat che suona (non in mute) o metronomo acceso | [D] |
| Stop (117) | Loop in pausa | [D] |
| « » (115, 116) | Mai | [D] |

  - Un messaggio solo a ogni cambio di stato, mai a ripetizione [D].
  - Tutti spenti al collegamento e all'uscita (MIDI-063).
- **MIDI-086** — **Basso su CV** (opzione, spenta per default): una copia del flusso Bass sul **ch16**, inviata alla porta 1, così la CV della MPK (Src = MIDI 16) pilota un synth analogico monofonico. Da quale ingresso la CV legga il canale non si sa: porta 1 per default [V VM-4]. Nota a 0 V e scala da misurare [V VM-7].
- **MIDI-087** — Stame NON DEVE mandare alla MPK messaggi diversi da: Identity Request, LED del trasporto, clock e trasporto (§4.4), copia del basso per la CV, flussi verso la porta 2. Ogni altro messaggio (LED dei pad, Program Change, SysEx di programma) è vietato finché i test VM-10, VM-11 e VM-12 non dicono cosa fa (e per i SysEx vale MIDI-077) [D].

### 8.8 Profilo di riserva: programma di fabbrica

Se sulla MPK è attivo un altro programma (per esempio il PGM1 "MPC" di fabbrica), Stame deve restare suonabile.

- **MIDI-088** — Il profilo DEVE riconoscere da solo il programma, mentre si suona [D]:
  - una manopola che manda valori tra 16 e 112 su CC 70–77 è in **Absolute**: per quella manopola il delta diventa `v − v_precedente` (il primo valore dopo il collegamento serve solo da riferimento);
  - un messaggio su CC 13 o CC 3 indica il joystick in 2CC di STAME;
  - nel programma di fabbrica il joystick manda CC 12 e CC 2 con 127 in **entrambi** i versi [O]: la direzione non si distingue, quindi il joystick NON DEVE produrre eventi finché non si è visto CC 13 o CC 3;
  - i pad di fabbrica hanno le stesse note (36–51, ch10) [O]: la mappa dei pad resta valida; l'aftertouch polifonico di fabbrica viene ignorato (MIDI-080);
  - il trasporto di fabbrica non manda il rilascio [O]: vale MIDI-083.
- **MIDI-119** — Quando il profilo passa a "fabbrica", Stame DOVREBBE mostrare una volta l'avviso "Programma STAME non attivo: funzioni ridotte" (testo e resa in `30`) [D].

### 8.9 Sequenza di avvio con la MPK

```
1. trova la scheda con usbid 09e8:0054                         (MIDI-070)
2. apri porta 1 (sub 0) e porta 2 (sub 1)                       (MIDI-071)
3. Identity Request sulla porta 1, attesa ≤ 1 s                 (MIDI-073)
4. LED del trasporto spenti: 90 73 00 … 90 77 00                (MIDI-085)
5. se c'erano note pendenti sul DIN: panic sulla porta 2        (MIDI-114)
6. se il trasporto è in moto: FA sulle destinazioni del clock   (MIDI-115)
7. emetti PNL_SRC_CONNECTED(SRC_MPK); profilo mpk_stame         (MIDI-088)
```

### 8.9b MPK mini IV (MK4): i messaggi catturati

Il 15/10/2026 Luigi ha scelto la **MPK mini IV** (MK4, versione bianca e grigia) al posto della Plus, per avere un kit più compatto: l'originale ha un'ottava sola e i 37 tasti della Plus non servivano. La mappa e il profilo `mpk_mk4` sono da scrivere; qui ci sono i fatti, catturati sul PC con `tools/midi_ascolta.py` (winmm, tutte le porte) con la MK4 nel preset **DAW**. È un preset di fabbrica in sola lettura, quindi resta sempre uguale e non va programmato [O]:

| Controllo | Porta | Messaggio | Note |
|---|---|---|---|
| 25 tasti | MIDI (1) | Note On/Off canale 1, velocity | il più basso è il Do3 (48) all'ottava 0 |
| Pad, banco A | MIDI e DAW (doppio) | Note canale 10: fila in basso 36–39 (pad 1–4), fila in alto 40–43 (pad 5–8) | aftertouch polifonico `A9` dopo la pressione; le note sono quelle della Plus |
| Pad, banco B | MIDI e DAW | note 44–51 | |
| BANK A/B | DAW | CC 12 127 e 0 | più un SysEx sulla porta Plugin `F0 47 00 5D 3A 00 01 <banco> F7` |
| Manopole K1–K8 | DAW | **CC 24–31 canale 1, relative** in complemento a 2: 1, 2, 3 in senso orario, 127, 126, 125 in senso antiorario, con accelerazione | **senza scatti**: un flusso continuo, decine di messaggi per giro |
| SHIFT | DAW | **CC 17**: 127 alla pressione, 0 al rilascio | con SHIFT tenuto le manopole mandano gli stessi CC |
| Manopola di navigazione | DAW | giro **CC 14** relativo (1, 127), **pressione CC 13** 127 e 0 | a scatti |
| UNDO, LOOP, STOP/PLAY, REC, ⊕ | DAW | CC **73, 74, 76, 77, 78**, solo 127 alla pressione | niente rilascio, anche tenendo premuto; SHIFT + UNDO = CC 17 + CC 73 |
| − e + | DAW | CC **80** e **81**, 127 e 0 | |
| OCT− e OCT+ | Plugin | SysEx `F0 47 00 5D 3B 00 01 <ottava> F7` | cambiano l'ottava interna dei tasti; a Stame non serve (MIDI tasto % 12) |
| Pitch, mod | MIDI | Pitch Bend 14 bit (centro 8192), CC 1 0–127 | |

Le quattro porte su Windows si chiamano «MPK mini IV MIDI Port», «DAW Port», «Plugin Port» e «Software Control». Sulla Flip le porte vanno lette tutte (PLT-039).

- **MIDI-130** — **Profilo `mpk_mk4`** [D, decisa con Luigi il 15/10/2026; `src/core/input/mpk_mk4.c`]. La piattaforma riconosce la MK4 dal nome della scheda («MPK mini IV»), apre le porte 1 e 2 e lo dice allo strato di input con `inp_set_mpk_model` prima di `inp_connected`. La porta 2 della MK4 non è l'ingresso MIDI di §5: porta i controlli. Mappa:

| Controllo MK4 | Funzione in Stame |
|---|---|
| 25 tasti | i 12 tasti dell'originale (nota % 12), come la Plus (MIDI-079) |
| Pad, banco A | fila in alto Dim, Min, Maj, Sus; fila in basso 6, m7, M7, 9: stesse note della Plus |
| Pad, banco B | **otto pad di batteria** con la velocity (MIDI-135, deciso da Luigi il 16/10/2026): fila bassa cassa, rullante, rimshot, battimani; fila alta charleston chiuso, charleston aperto, tom basso, piatto. Una nota del banco B rilascia prima i tasti accordo del banco A, come un cambio di banco (MIDI-089) |
| K1–K8 | gli 8 encoder (Sound, Perform, FX, Key, Bass, Loop, BPM, Volume). Uno scatto ogni 12 unità per Sound, Key, Bass e Loop, 8 per Perform e FX, 3 per BPM, 2 per Volume [V: da tarare a mano] |
| **SHIFT** | **PUSH** (MIDI-084): tenuto + manopola toccata e lasciata = premi; + manopola girata = premi e ruota; + tocco e 1 s = tieni. Il tremolio della selezione dura 300 ms, perché le manopole non hanno scatti. Dal 16/10/2026 è **l'unico PUSH**: B8 e X della Flip non contano |
| Manopola di navigazione | girata: liste e fuoco (orario = voce successiva); premuta: conferma; premuta e girata: premi e ruota dell'encoder con il fuoco. Con − e + è la **casa della navigazione** (16/10/2026): m2 del pad e croce, A e B della Flip non la rifanno |
| REC | Loop: registra, poi sovraincide (un tocco: il trasporto manda solo la pressione) |
| STOP/PLAY | BPM: avvia o ferma il beat (il solo doppione voluto di SHIFT + K7 toccata: un tasto PLAY per la batteria); **SHIFT + STOP/PLAY = Panic**, scorciatoia accanto a T12 tenuto |
| LOOP | `MACRO_LOOP_STOP`: pausa del loop |
| UNDO | `MACRO_LOOP_UNDO`; **SHIFT + UNDO = Clear** |
| ⊕ | `MACRO_LOOP_OVERDUB`: entra ed esce dall'overdub |
| − e + | Back e menu della piattaforma |
| Pitch, mod, sustain | come la Plus (bend, modulazione e sustain del Sound) |
| BANK A/B, OCT− e OCT+ | interni della MK4; Stame li ignora |

  Attenzione: SHIFT insieme a un pad cambia i modi interni della MK4 (Chords, Scales, modo dei pad). Il preset da usare è **DAW**.

### 8.10 Macro pad BRIMFORD (profilo `pad_brimford`)

Gli encoder dell'originale si premono, le manopole della MPK no. Luigi ha aggiunto un **macro pad** che il 13/10/2026 dava agli encoder i loro pulsanti (K1–K8 e T1–T8 come **due griglie gemelle 4×2**). Il **16/10/2026** Luigi ha chiesto di togliere i comandi replicati fra gli apparecchi («studia l'ergonomia migliore per i comandi utilizzando quelli che sono più ergonomicamente funzionali, se restano tasti o manopole libere... assegnamogli nuove feature») e ha deciso: la pressione degli encoder sta tutta su SHIFT + K della MK4, liste, conferma, Back e Menu sulla manopola di navigazione, − e + della MK4, il Lock resta, le riserve tacciono quando c'è l'apparecchio che sostituiscono. Il pad tiene Options, Panic, Lock, View, Page e i due voicing, e i tasti liberi fanno quello che l'originale non ha (MIDI-133). Il **17/10/2026** i tasti della Flip hanno smesso di tacere (MIDI-137, al posto delle riserve inerti di MIDI-134). Il 18/10/2026 Luigi ha tolto le mappe per la sola MK4 e per il solo pad: lo strumento è MK4, pad e Flip insieme, e ogni apparecchio fa sempre la sua mappa.

| Voce | Valore | Etichetta |
|---|---|---|
| Modello | **BRIMFORD CusKeyboard0227** (Amazon B0BWY7N8FF), pad generico cinese della famiglia «sikaicase», chip CH57x | [O per il modello; D per famiglia e chip] |
| Comandi | **15 tasti meccanici** in 3 file da 5 e **3 manopole a scatti**: una grande (**M**) e due piccole (**m1**, **m2**). Ogni manopola ha tre azioni (antioraria, oraria, pressione), programmabili come tasti. Luigi tiene il pad con le manopole a destra: le due piccole in alto, la grande in basso | [O, 15/10/2026: 15 tasti, non 12 come scritto il 13/10] |
| Collegamento | USB-C; anche 2.4G e Bluetooth, che Stame **non** usa: solo cavo | [O; D] |
| Programmazione | software sikaicase (solo Windows) oppure lo strumento open source `ch57x-keyboard-tool` con una configurazione YAML. La configurazione resta a bordo | [O] |
| Classe USB | dispositivo USB **composito**, revisione 1.00, senza nome di prodotto. Interfaccia 0: HID del produttore (pagina `0xFF00`), usata dal software di programmazione. Interfaccia 1: HID con due collezioni tastiera, una mouse e una per i tasti multimediali (pagina `0x0C`). Niente MIDI. Sulla Flip si legge da evdev, probabilmente su più nodi `/dev/input/event*` | [O su Windows, 15/10/2026; nodi evdev V VP-1] |
| VID:PID | **`1189:8840`** (il `1189:8890` del 13/10 era dedotto e sbagliato) | [O, 15/10/2026] |
| Strati | la configurazione a bordo ha **3 strati** da 24 azioni: 15 tasti più 3 azioni per manopola | [O, 15/10/2026] |
| LED | dall'host si comanda solo l'**illuminazione di tutto il pad, per strato**, con lo stesso comando del software di programmazione sull'interfaccia 0 (pacchetti di 64 byte: `03 fe b0 <strato 1–3> 08 00 00 00 00 00 01 00 <codice>`, poi `03 fd fe ff`; `codice = colore << 4 \| modo`, modi 0 spento, 1 fisso in un colore, 5 fisso bianco, 2 e 3 lampo al tocco, 4 tasto acceso finché premuto; colori 1 rosso, 2 arancio, 3 giallo, 4 verde, 5 ciano, 6 blu, 7 viola). **Niente LED per singolo tasto, niente lampeggio comandato**: Stame non può accendere il tasto di Hold o far lampeggiare DRUMS a tempo (chiesto da Luigi il 19/10/2026). È una scrittura di configurazione: se finisce nella flash del pad si consuma (VP-8). Il 19/10/2026 Luigi ha scelto di non provare: Stame **non scrive sul pad** | [O dal sorgente di `ch57x-keyboard-tool`, k884x.rs, verificato dai suoi autori con catture USB; V VP-8] |

**Verifiche del 15/10/2026** sul PC di Luigi, con `tools/pad_ascolta.py` (Raw Input di Windows, solo gli eventi del pad) [O]:
- ogni tasto e ogni pressione di manopola manda **«giù» alla pressione e «su» al rilascio** (90–230 ms nelle prove): VP-3 è chiusa, i gesti «tenere» e «premere e ruotare» funzionano e i ripieghi di MIDI-125 non servono;
- ogni **scatto** di manopola manda un tocco (giù e su a 3–7 ms): uno scatto = un evento. In 9 scatti lenti nessuno perso; la prova veloce di VP-4 resta da fare;
- con il pad tenuto con le manopole a destra, i tasti hanno gli indici 1–15 in ordine di lettura (fila in alto da sinistra a destra, poi in mezzo, poi in basso). Le manopole hanno gli indici 16–24: piccola vicina ai tasti 16 oraria, 17 pressione, 18 antioraria; l'altra piccola 19 oraria, 20 pressione, 21 antioraria; la grande 22 antioraria, 23 pressione, 24 oraria. Le due piccole hanno il verso invertito rispetto alla grande: nella configurazione va controllato manopola per manopola;
- il software di programmazione legge la configurazione dall'interfaccia 0 con report `03`: una riga per azione, `03 fa <indice> <strato> <tipo> … <quante> <modificatore> <tasto>…`, tipo 1 = tastiera (codici d'uso HID, es. `04` = A, `1e` = 1), tipo 2 = tasti multimediali (`e9` volume su, `ea` giù, `e2` muto);
- configurazione trovata: strato 1 con **Win+L** sul tasto 1 (blocca Windows), «K, Ctrl+C» e «L, Ctrl+V» sui tasti 11 e 12, volume sulla grande; strati 2 e 3 con A…O sui tasti e le cifre 1…9 sulle manopole. Luigi usa lo strato 3; all'accensione il pad riparte dallo strato 1, quindi Stame legge anche quello (MIDI-122).

```
  Macro pad BRIMFORD, tenuto con le manopole a destra (mappa del 16/10/2026)
  T1 Hold     T2 Tap      T3 Metro   T4 Fill    T13 Drop    m1   m2
  T5 Scene 1  T6 Scene 2  T7 Scene 3 T8 Scene 4 T14 View
  T9 Options  T10 Save Lp T11 Drums  T12 Panic  T15 Page       M
```

| Fila del pad | col. 1 | col. 2 | col. 3 | col. 4 | col. 5 | Manopole |
|---|---|---|---|---|---|---|
| in alto | T1 Hold | T2 Tap tempo | T3 Metronomo | T4 Fill (tenuto) | **T13 Drop** (tenuto) | m1 Bass Voicing (piccola vicina ai tasti), m2 volume del Beat (piccola sul bordo; premuta e girata, volume del basso) |
| in mezzo | T5 Scene 1 | T6 Scene 2 | T7 Scene 3 | T8 Scene 4 | **T14 View** | |
| in basso | T9 Options | T10 Save Loop | T11 Drums | T12 Panic | **T15 Page** | M Chord Voicing (la grande) |

La quinta colonna è quella **decisa da Luigi il 15/10/2026**, degli stati di Stame: **T13 Drop** (MIDI-140; fino al 19/10/2026 era il Lock delle manopole, MIDI-131), **T14 View** e **T15 Page** (MIDI-132). Le prime quattro, fino al 15/10 gemelle delle manopole della MPK, dal 16/10/2026 sono le funzioni di MIDI-133.

- **MIDI-120** — Il profilo `pad_brimford` DEVE applicare questa mappa [D, **13/10/2026**, rifatta il **16/10/2026**] sempre, con o senza tastiera (il pad strumento di MIDI-136 è stato tolto il 18/10/2026). I codici sono quelli programmati sul macro pad (MIDI-122) o imparati con Learn Pad (MIDI-123); al profilo arrivano già tradotti nei codici portabili `MPAD_*` (MIDI-124):

| Comando | Codice (strato 3 di fabbrica) | Evento del pannello (§10.1) | Funzione |
|---|---|---|---|
| **T1** | A | `PNL_MACRO(MACRO_HOLD_TOGGLE)` alla pressione | **Hold** dell'accordo (MIDI-133) |
| **T2** | B | `PNL_MACRO(MACRO_TAP_TEMPO)` alla pressione | **Tap tempo** |
| **T3** | C | `PNL_MACRO(MACRO_METRO_TOGGLE)` alla pressione | **Metronomo** on/off, indipendente dal Beat |
| **T4** | D | `PNL_MACRO(MACRO_FILL, 1)` alla pressione, `(…, 0)` al rilascio | **Fill** del Beat finché è tenuto |
| **T5–T8** | F, G, H, I | tocco: `PNL_MACRO(MACRO_SCENE, n)` al rilascio; tenuto 1 s: `PNL_MACRO(MACRO_SCENE_SAVE, n)` una volta, e il rilascio non richiama | **Scene 1–4**: richiama o salva |
| **T9** | K | `PNL_ENC_DOWN/UP(ENC_OPTIONS)` | Pulsante di Options (l'unico pulsante di encoder rimasto: Options non ha una K) |
| **T10** | L | `PNL_MACRO(MACRO_LOOP_EXIT)` alla pressione | **Save Loop**: l'uscita morbida di ACC-222 (`LOOP_C_EXIT`) |
| **T11** | M | `PNL_MACRO(MACRO_DRUMS_TOGGLE)` alla pressione | **Batteria a tastiera** on/off (ACC-211) |
| **T12** | N | `PNL_MACRO(MACRO_PANIC)` **solo dopo 1 s tenuto**, `MACRO_RESET` a 3 s (MIDI-126) | Panic (§7), Reset |
| **T13** | E | `PNL_MACRO(MACRO_DROP, 1)` alla pressione, `0` al rilascio | **Drop** finché è tenuto (MIDI-140) [D, **scelto da Luigi il 19/10/2026**] |
| **T14** | J | `PNL_MACRO(MACRO_VIEW_TOGGLE)` alla pressione | **View**: Geek Out e ritorno alla vista di prima (MIDI-132) |
| **T15** | O | `PNL_MACRO(MACRO_CONTROLS_PAGE)` alla pressione | **Page**: apre la pagina dei comandi della Flip e la tiene aperta; un altro tocco o Back la chiude (MIDI-132) |
| **M** antioraria / oraria | 9 / 7 (strato 1: volume giù / su) | `PNL_ENC_TURN(ENC_CHORD_VOICING, −1/+1)`, uno scatto per evento | Chord Voicing Dial |
| **M** pressione | 8 (strato 1: muto) | `PNL_ENC_DOWN/UP(ENC_CHORD_VOICING)` | Pulsante del Chord Voicing: Split ↔ Octave |
| **m1** antioraria / oraria | 1 / 3 | `PNL_ENC_TURN(ENC_BASS_VOICING, −1/+1)` | Bass Voicing Dial: registro (ottava) del basso |
| **m1** pressione | 2 | `PNL_ENC_DOWN/UP(ENC_BASS_VOICING)` | Bass Voicing premuto: il **modificatore** delle combinazioni |
| **m2** antioraria / oraria | 4 / 6 | `PNL_MACRO(MACRO_BEAT_VOL, ∓1)`; con m2 premuta `MACRO_BASS_VOL` | Volume del Beat; premuta e girata, volume del basso (MIDI-133). Con il Lock acceso `PNL_ENC_TURN(ENC_KEY)` |
| **m2** pressione | 5 | niente; premuta e lasciata senza girarla `MACRO_KNOB_CLICK` (MIDI-139) | — |

  Combinazioni con il Bass Voicing tenuto [M], come in §8.5: **m1 tenuta + Loop** (REC della MK4, o B5 della Plus) = uscita hard dal loop; **m1 tenuta + BPM** = batteria da suonare ("On drums") [O], che dal 16/10/2026 ha anche T11; **m1 tenuta + Bass** = basso on/off.

- **MIDI-121** — **Gesti con il macro pad** [D, 13/10/2026, ridotti il 16/10/2026]. Il riconoscitore (MIDI-103) lavora sullo stato unito delle sorgenti (MIDI-102):
  - T9 è un pulsante di encoder: **premere** = tocco, **tenere** = 1 s; porta il fuoco su Options (MIDI-104), che si ruota con la manopola di navigazione della MK4;
  - M e m1 premute e ruotate danno il premere e ruotare del proprio encoder;
  - T4 e T5–T8 hanno il tenuto nel profilo (`on_tick`), non nel riconoscitore: Fill finché è tenuto, scena salvata a 1 s;
  - i tasti T1–T8 non premono più gli encoder: il premere e ruotare degli encoder è SHIFT + K della MK4 (MIDI-130).

- **MIDI-122** — **Codici** [O, 15/10/2026]: il software del pad **non offre F13…F24** (VP-2 chiusa), ma non serve programmarlo. Stame legge i codici della configurazione di fabbrica, che sono già tutti diversi fra loro, e il pad è suo in esclusiva (MIDI-124):
  - **strati 2 e 3**: i tasti mandano **A…O** in ordine di lettura (fila in alto A–E, in mezzo F–J, in basso K–O). Le prime quattro colonne sono T1–T12 fila per fila, la quinta (**E, J, O**) è **T13–T15**: la lettera non è il numero del tasto (`mpad_tasto` in `pad_codes.h`). Fino al 15/10/2026 sera la piattaforma leggeva la lettera i-esima come T(i+1), e il tasto della mappa «Menu» accendeva il Lock. m1 = **1** antioraria, **2** pressione, **3** oraria; m2 = **4**, **5**, **6**; M = **9** antioraria, **8** pressione, **7** oraria. Nella colonna «Codice» della tabella di MIDI-120 c'è la lettera di ciascun tasto;
  - **strato 1**, quello con cui il pad si accende: uguale, salvo il tasto 1 (**Win+L**, letto come T1), i tasti 11 e 12, i primi due della fila in basso (**«K, Ctrl+C»** e **«L, Ctrl+V»**: contano K e L, le combinazioni con Ctrl si ignorano, quindi T9 Options e T10 Back sono solo tocchi e Options non si tiene) e la manopola grande (**volume giù, muto, volume su** dalla collezione multimediale). I tasti che arrivano con Ctrl, Alt o Shift tenuti si ignorano;
  - conviene usare lo strato 3, o rendere lo strato 1 uguale al 3 con il software del pad. **Il 17/10/2026 Luigi ha reso lo strato 1 uguale al 3** [O]: all'accensione il pad manda già A…O e le cifre, e T1, T9 e T10 sono tasti veri (con lo strato di fabbrica erano tocchi brevi, e nel pad strumento Do, Sol♯ e La non si potevano tenere). Il registro della Flip ha confermato i due versi di M e m1 (codici evdev 8 e 10, 4 e 2: i tasti 7 e 9, 3 e 1).

  La proposta del 13/10, superata, prevedeva di programmare il pad con F13…F24 e il tastierino:
  - **T1–T12 = F13–F24** (evdev `KEY_F13` = 183 … `KEY_F24` = 194). Le tastiere normali non hanno questi tasti;
  - manopole sul **tastierino numerico**, disposte come il tastierino stesso (riga alta = M, centrale = m1, bassa = m2; sinistra = antioraria, centro = pressione, destra = oraria):

| Manopola | Antioraria | Pressione | Oraria |
|---|---|---|---|
| M | KP7 (`KEY_KP7` = 71) | KP8 (72) | KP9 (73) |
| m1 | KP4 (75) | KP5 (76) | KP6 (77) |
| m2 | KP1 (79) | KP2 (80) | KP3 (81) |

  - evdev riporta i codici `KEY_KP*` così come sono, a prescindere da Bloc Num: Stame NON DEVE dipendere dallo stato dei LED della tastiera;
  - l'illuminazione RGB, se c'è, va spenta nella stessa configurazione [V VP-7];
  - schema indicativo per `ch57x-keyboard-tool` (i nomi esatti delle chiavi e dei tasti vanno controllati con lo strumento, VP-2):

```yaml
# stame-pad.yaml: profilo pad_brimford, 13/10/2026
orientation: normal
rows: 3
columns: 4
knobs: 3
layers:
  - buttons:
      - ["f13", "f14", "f15", "f16"]   # T1 Sound   T2 Perform  T3 FX    T4 Key
      - ["f17", "f18", "f19", "f20"]   # T5 Bass    T6 Loop     T7 BPM   T8 Volume
      - ["f21", "f22", "f23", "f24"]   # T9 Options T10 Back    T11 Menu T12 Panic
    knobs:
      - { ccw: "kp7", press: "kp8", cw: "kp9" }   # M  Chord Voicing
      - { ccw: "kp4", press: "kp5", cw: "kp6" }   # m1 Bass Voicing
      - { ccw: "kp1", press: "kp2", cw: "kp3" }   # m2 liste e fuoco
```

  L'ordine delle manopole nella configurazione dipende da come sono montate sul macro pad [V VP-5].

- **MIDI-123** — **Learn Pad** [D, 13/10/2026]. Se il software non ammette i codici di MIDI-122, o il macro pad arriva con un'altra configurazione, Stame DEVE offrire MENU → «Learn Pad» (`30` UI-129, UI-175):
  - chiede di premere **in ordine** ogni tasto e ogni azione: T1…T15, poi per M, m1 e m2 antioraria, pressione e oraria (24 passi);
  - per ogni passo registra il primo `EV_KEY` con valore 1 che non sia un modificatore, insieme ai modificatori tenuti in quel momento (Ctrl, Shift, Alt, Meta): così funziona anche un macro pad programmato con combinazioni;
  - un codice già assegnato a un passo precedente DEVE essere rifiutato con la richiesta di ripetere; B della Flip torna al passo precedente; MENU annulla senza salvare;
  - alla fine salva la mappa in **`Saves/stame/pad.map`** (testo, una riga per azione: `T1 183`, `M_CCW 71`, `M_PUSH 29+72` con i modificatori prima del `+`) e la applica subito;
  - con `pad.map` presente vale la mappa salvata, altrimenti i codici di MIDI-122. Un codice che non è in nessuna mappa DEVE essere ignorato; dopo 5 codici sconosciuti di fila Stame mostra l'avviso «Pad not mapped: MENU > Learn Pad» (`30` UI-156);
  - durante Learn Pad gli eventi del macro pad NON DEVONO arrivare al profilo.

- **MIDI-124** — **Riconoscimento ed esclusività** [D; V VP-1]:
  - Stame DEVE riconoscere il macro pad dal **VID:PID** `1189:8840` (`EVIOCGID`, `src/platform/flip/macropad.c`) [O, 15/10/2026];
  - NON DEVE confonderlo con il gamepad della Flip («MIYOO Player1», `50` PLT-053) né con l'interfaccia HID della MPK (`09e8:0054`, ignorata, §8.1);
  - se il macro pad espone più nodi evdev (tastiera, tasti multimediali, mouse), Stame DEVE aprirli tutti, cioè tutti i nodi con lo stesso dispositivo USB padre in sysfs;
  - ogni nodo va aperto in esclusiva con **`EVIOCGRAB`**: così spruce, PyUI e la console non vedono i tasti. Se `EVIOCGRAB` fallisce, il nodo va chiuso, lo stato diventa «PAD» in `warn` (`30` UI-126) e si riprova ogni secondo. La chiusura del file all'uscita rilascia il grab;
  - lo strato di piattaforma imposta `EVIOCSCLOCKID` su `CLOCK_MONOTONIC`, così il tempo degli eventi è lo stesso di `t_us`;
  - traduce i codici con la mappa (MIDI-122 o `pad.map`) negli identificatori portabili `MPAD_T1`…`MPAD_T12`, `MPAD_M_CCW`, `MPAD_M_PUSH`, `MPAD_M_CW`, `MPAD_M1_*`, `MPAD_M2_*` e li passa a `on_pad` del profilo `pad_brimford` (MIDI-101). I nomi `KEY_*` sono vietati, come i `BTN_*` (MIDI-090).

- **MIDI-125** — **Lettura degli eventi** [D; V VP-3, VP-4]:
  - `EV_KEY` con valore 1 = giù, 0 = su; il valore 2 (ripetizione automatica del kernel) DEVE essere ignorato;
  - **rotazioni**: ogni scatto arriva come una pressione con rilascio. Conta solo il `KEY_DOWN`: un `KEY_DOWN` = uno scatto, `PNL_ENC_TURN` con `b` = ±1; il rilascio si ignora. Scatti veloci non devono andare persi [V VP-4]: se il macro pad li accorpa o li scarta, non c'è modo di recuperarli e va annotato in VP-4;
  - **pressioni** (tasti e manopole): servono «giù» alla pressione e «su» al rilascio, altrimenti tenere, premere e ruotare, il modificatore m1 e T12 non funzionano [V VP-3]. Se VP-3 mostra che una pressione arriva come un tocco istantaneo (giù e su insieme qualunque sia la durata), il profilo DEVE passare a un ripiego per quel comando: m1 diventa un interruttore (primo tocco = Bass Voicing premuto, secondo = rilasciato, rilascio automatico dopo 10 s), T12 vale un doppio tocco entro 400 ms; per T1–T9, M e m2 resta solo il premere.

- **MIDI-126** — **T12 Panic e Reset** [D, 13/10/2026; Reset del 15/10/2026, chiesto da Luigi: «c'è il tasto panic per resettare tutto?»]: il profilo DEVE emettere `PNL_MACRO(MACRO_PANIC)` **una volta**, quando T12 resta premuto per 1 s (controllo in `on_tick`); un rilascio prima di 1 s non produce nulla. È tenuto apposta, per non premerlo per sbaglio. Se T12 resta premuto fino a **3 s**, il profilo emette anche `PNL_MACRO(MACRO_RESET)`, una volta: oltre alle note spente, il looper si cancella, il Beat si spegne, transpose torna a 0, il Perform si spegne con il suo Lock, le liste e la pagina dei comandi si chiudono, la vista torna Chord. Sulla MK4 SHIFT + STOP/PLAY resta il solo Panic (il trasporto non manda il rilascio).

- **MIDI-127** — **Hot-plug** [D]: come per la MPK (§11):
  - senza macro pad, lo strato di piattaforma DEVE cercarlo ogni secondo senza bloccare audio e interfaccia;
  - la disconnessione si rileva da `POLLERR`, `POLLHUP` o da `read()` che fallisce con `ENODEV`;
  - allora il profilo emette con `on_lost` i rilasci sintetici di tutto ciò che risultava premuto (T1–T9, pressioni di M, m1 e m2), annulla l'attesa di T12 ed emette `PNL_SRC_LOST(SRC_MACROPAD)`. Al collegamento: `PNL_SRC_CONNECTED(SRC_MACROPAD)`;
  - una disconnessione NON DEVE fermare il suono interno né il trasporto (come MIDI-113);
  - un dispositivo HID collegato all'avvio sposta il numero del gamepad della Flip: per questo il gamepad si cerca per nome (MIDI-090, `50` PLT-053).

- **MIDI-128** — **Collegamento e alimentazione** [O per hub e dock; D per il resto]:
  - il macro pad va su un **hub USB 2.0 semplice, senza Power Delivery**, sulla porta USB-C **di sopra** della Flip (OTG), insieme alla MPK (`50` PLT-091);
  - le docking station con Power Delivery non funzionano con la Flip, e `otg_mode` NON DEVE mai essere forzato (§8.2);
  - il macro pad va usato **solo via cavo**: se ha un selettore di modo, sta su USB. Con la batteria interna in carica dall'hub il consumo cresce [V VP-6]; l'RGB va spento [V VP-7].

- **MIDI-129** — **Convivenza con MPK e Flip** [D, 13/10/2026]:
  - il profilo `pad_brimford` è attivo insieme a `mpk_stame` (o `mpk_fabbrica`) e a `flip_tasti`, anche nel modo tascabile; non cambia la mappa degli altri profili;
  - con la MK4 il banco B è libero e il PUSH è solo SHIFT; con la Plus banco B, B8 e X restano le riserve (16/10/2026);
  - funziona anche senza MPK: in quel caso le note arrivano solo dal modo tascabile (§9.2);
  - quando il macro pad è collegato, le legende delle celle e la legenda viva mostrano i suoi nomi (`30` UI-152, UI-155) e la barra di stato mostra «PAD» (`30` UI-126).

- **MIDI-131** — **Lock delle manopole** [D, deciso da Luigi il 15/10/2026: «un tasto che funzioni tipo Caps Lock per i knob»; **tolto il 19/10/2026**]. Dal 15 al 19/10/2026 T13 era un interruttore a scatto: acceso, M, m1 e m2 erano gli encoder Sound, Perform e Key, perché le manopole della MK4 non hanno scatti e quelle del pad sì. Il 19/10/2026 Luigi: «a che serve se sulla mpk ho già sound, perform, key?»; la navigazione della MK4 ha scatti e pressione per le liste e SHIFT + K dà tutti i gesti premuti, quindi il Lock era un doppione. T13 è il Drop (MIDI-140).

- **MIDI-132** — **View e Page** [D, **decisi da Luigi il 15/10/2026**]. Due tasti per guardare la Flip senza allungare la mano fino ai suoi tasti:
  - **T14 View** emette `PNL_MACRO(MACRO_VIEW_TOGGLE)` alla pressione: la UI passa a **Geek Out** e, al tocco successivo, torna alla vista in uso prima (`30` UI-051: Options → View resta la strada dell'originale per le sei viste);
  - **T15 Page** emette `PNL_MACRO(MACRO_CONTROLS_PAGE)` alla pressione: la UI apre la **pagina dei comandi** (`30` UI-142a) e la tiene aperta finché non arriva un altro `MACRO_CONTROLS_PAGE` o un `PNL_BACK`; i 5 s dei tasti della Flip non la chiudono;
  - tutti e due agiscono solo alla pressione: tenerli non ripete nulla. Non cambiano suono, trasporto né looper.

- **MIDI-133** — **Le aggiunte sui tasti liberi del macro pad** [D, **decise da Luigi il 16/10/2026** con le domande a scelta multipla: «Hold, Tap tempo, Metronomo, Save Loop», «Scene 1–4 su T5–T8», «Fill del Beat su T4», «m2 = Beat volume, premuta e girata = Bass volume»]. Sono tutte cose che l'originale non ha (principio del 15/10/2026: le aggiunte si implementano e, se sono uno stato, si vedono sulla plancia, `30` UI-126):
  - **T1 Hold**: a scatto. Acceso, il rilascio dei tasti e dei tasti accordo non arriva al motore degli accordi: l'accordo resta a suonare finché non si preme un tasto nuovo (allora escono prima i rilasci trattenuti) o finché il Hold non si spegne. In testata «HOLD». La batteria a tastiera e il Reset lo spengono;
  - **T2 Tap tempo**: ogni tocco è un battito; dal secondo in poi il BPM è la media degli ultimi quattro intervalli (60…200), con l'overlay di BPM; due secondi senza tocchi e si riparte da capo;
  - **T3 Metronomo**: on/off, **indipendente dal Beat** (`mot_metronome`): clicca sui battiti della metrica in uso, mette in moto il trasporto come il Beat (ACC-204) e non lo riavvia se è già in moto; con il Beat scelto la metrica è 4/4 (ACC-209). In testata «METRO». La voce metronomo della lista di BPM resta quella dell'originale;
  - **T4 Fill**: finché è tenuto il Beat suona la sua **battuta di riempimento** (`beat_fill_hits`, una per ciascuno dei 15 Beat, nello stesso kit), al rilascio torna il pattern. In testata «FILL». Il profilo manda il rilascio sintetico se il pad si stacca;
  - **T5–T8 Scene 1–4**: un tocco richiama suono, basso, Perform (modo e amount), intensità dell'effetto, tonalità con la Key mode e basso acceso; tenuto 1 s salva lo stato corrente. Una scena vuota lo dice («Scene 3 empty: hold 1 s to save»). Le scene stanno in `Saves/stame/scene.txt` (chiave=valore, PLT-066: `s1.sound`, `s1.perf`…), lette all'avvio e riscritte a ogni salvataggio dal thread principale;
  - **T10 Save Loop**: l'uscita morbida di ACC-222 (`LOOP_C_EXIT`): il loop si ferma e resta in RAM; il Loop successivo (REC) lo riprende da t = 0 invece di registrarne uno nuovo; Clear da fermo lo svuota;
  - **T11 Drums**: `DRUMS_TOGGLE` di ACC-211, la batteria a tastiera, che con il PUSH su SHIFT non ha più una combinazione comoda (Mod + BPM resta);
  - **m2**: girata regola il **volume del Beat**, premuta e girata il **volume del basso**, uno scatto per punto, con i loro overlay; premuta da sola non fa niente.

- **MIDI-134** — **Riserve inerti** [D, 16/10/2026; **superata il 17/10/2026** da MIDI-137]. Dal 16 al 17/10/2026 i tasti della Flip che rifacevano il comando di un altro apparecchio tacevano quando quell'apparecchio c'era (croce, A, B e START con la MK4; Y, SELECT, L1 e R1 con il pad). Sulla Flip Luigi è rimasto chiuso nel menu: MENU lo apriva, ma la croce taceva. Il 17/10/2026: «i tasti della flip devono funzionare per la gestione», poi «tutti».

- **MIDI-135** — **La drum machine dal vivo** [D, **decisa da Luigi il 16/10/2026**: «la drum machine deve avere la stessa "filosofia" dell'originale... premo tasti, muovo manopole e creo loop di batteria in tempo reale», niente sequencer a passi; scelte con le domande a scelta multipla: pad del banco B, kit/Roll/Accent, Swing, FX sulla batteria]. Si suona e si registra nel looper come gli accordi (ACC-211); sotto **DRUMS** (T11) gli stessi encoder cambiano mestiere, come con il Lock, e le celle della pagina dei comandi lo scrivono (`30` UI-152):
  - **pad del banco B della MK4**: otto colpi con la velocity, sempre, anche senza DRUMS (`PNL_MACRO(MACRO_DRUM_HIT, strumento << 8 | velocity)`, velocity 0 al rilascio); fila bassa cassa, rullante, rimshot, battimani, fila alta charleston chiuso e aperto, tom basso, piatto, nell'ordine degli strumenti di `drums.h` (ACC-212);
  - **K1 = Kit** (cella «KIT»): 0 = il kit del Beat scelto, poi Studio, Jazz, 808, Techno, Chip e, dal 19/10/2026, i 35 kit della libreria sintetizzata, 6…40 (`mot_kit`, `20` SND-541; la lista è MIDI-141); vale per i tasti, i pad e il Beat;
  - **K2 = Roll** (cella «ROLL»): un tasto o un pad **tenuto** si ripete sulla griglia del loop (o del trasporto) con la suddivisione scelta: Off, 1/4, 1/8, 1/8T, 1/16, 1/16T, 1/32 (`mot_roll`, in tick: 96, 48, 32, 24, 16, 12). Il colpo della mano suona subito; la ripetizione salta il punto di griglia che cade a meno di mezza suddivisione dal colpo; ogni ripetizione entra nel loop al suo tick esatto. È lo Strum della batteria;
  - **K5 = Accent** (cella «ACCENT», 0…10, default 10): quanto conta la velocity: `v = 100 + (velocity − 100) × Accent / 10`, quindi 0 = colpi tutti uguali a 100, 10 = la dinamica com'è. Vale per tasti e pad;
  - **K3 = Drive** (cella «DRIVE», 0…10, default 0): la saturazione del bus della batteria; **premuta e girata = Filtro** (cella «FILTER» mentre si gira premuta; −10…+10: a sinistra passa-basso fino a 150 Hz, a destra passa-alto fino a 3 kHz, 0 spento). Nella cella il valore che non si sta girando va nel dettaglio («Filter LP 4», «Drive 06»). È l'FX del bus di `20` SND-538, fatto il 19/10/2026: i clic del metronomo non ci passano;
  - **K4 = Swing** (cella «SWING»): Off, 52 % … 75 %, cioè 0…12 tick di ritardo dei sedicesimi dispari (`10` ACC-216, fatto il 19/10/2026). Vale per il Beat, il loop inventato, i colpi di batteria del loop e il Roll;
  - gli overlay sono `OV_KIT`, `OV_ROLL`, `OV_ACCENT`, `OV_SWING`, `OV_DRIVE`, `OV_FILTER` (`30` UI-025);
  - fuori da DRUMS gli encoder tornano quelli dell'originale; kit, Roll, Accent, Swing e FX restano come sono. Swing e FX cambiano il Beat anche fuori da DRUMS, quindi sono uno stato in vista: la testata scrive «SWING» e «DRUM FX» finché ci sono (`30` UI-126). La demo suona com'è scritta: all'avvio azzera kit, swing e FX, alla fine rimette quelli di prima;
  - dal 18/10/2026, sotto DRUMS, le tre manopole del pad creano il loop di batteria: MIDI-139.

- **MIDI-136** — **Il pad senza tastiera era lo strumento** [D, 17/10/2026; **tolta il 18/10/2026**]. Dal 17 al 18/10/2026, senza MPK collegata, il pad cambiava mappa: T1–T12 erano le dodici fondamentali, M teneva il tipo d'accordo e m1 l'estensione. Il 18/10/2026 Luigi: «ci ho ripensato. elimina tutto quello che riguarda il funzionamento solo mpk o solo pad». Il pad fa sempre la mappa di MIDI-120.

- **MIDI-137** — **La Flip sempre viva** [D, **deciso da Luigi il 17/10/2026**: «i tasti della flip devono funzionare per la gestione», poi «tutti»; **il 18/10/2026** tolte le mappe per la sola MK4 e per il solo pad: «elimina tutto quello che riguarda il funzionamento solo mpk o solo pad»]. Sostituisce MIDI-134. Lo strato di input sa quale tastiera è collegata (`input.c`, `cfg_sync`, a ogni collegamento e scollegamento) e lo dice al profilo della Flip:
  - i tasti della Flip **non tacciono mai**: lo schema a fuoco di MIDI-092 vale in ogni configurazione, anche dove lo stesso comando c'è su un altro apparecchio. MENU resta la via d'uscita;
  - **X** è **Hold** (`PNL_MACRO(MACRO_HOLD_TOGGLE)`, come T1 del pad); con la **Plus** collegata resta il suo PUSH (§8.6);
  - **START** è il pulsante di **BPM**; con la **MK4** collegata, che ha STOP/PLAY per il Beat, è il **Fill** finché è tenuto (`PNL_MACRO(MACRO_FILL, 1/0)`, come T4). Il ruolo si fissa alla pressione: il rilascio va lì anche se intanto cambia la configurazione;
  - MK4, pad e Flip fanno sempre la loro mappa (MIDI-120, MIDI-130, MIDI-133, MIDI-135), anche se manca un apparecchio: non ci sono mappe per la sola MK4 o il solo pad;
  - **solo Flip**: lo schema a fuoco di MIDI-092 (il modo tascabile di MIDI-093 è previsto);
  - le legende della pagina dei comandi seguono la configurazione (`30` UI-152);
  - la MK4 non può prendere le funzioni del pad su **SHIFT + pad** né su **SHIFT + LOOP**: sono comandi della tastiera stessa (SHIFT + Pad 5 accende il suo modo accordi, SHIFT + LOOP apre il suo menu globale; guida della MK4 nel vault);
  - levette e grilletti della Flip: MIDI-138.

- **MIDI-138** — **Levette e grilletti della Flip** [D, **17/10/2026**, Luigi: «gli analogici dalla flip? non ti piacevano?»]. Fino a questa data levette, L2, R2, L3 e R3 erano liberi, tenuti per il modo tascabile. Le levette sono a molla e analogiche: la destra dà una manopola ai due voicing anche quando il pad non c'è. La mappa vale sempre, come il resto dei tasti della Flip (MIDI-137); il modo tascabile, quando ci sarà, la sostituisce (MIDI-094):

| Comando | Evento del pannello (§10.1) | Funzione |
|---|---|---|
| **Levetta sinistra**, orizzontale | `PNL_BEND(−8191…8191)`, esce quando cambia di almeno 64 o torna a 0 | **Pitch bend**, a molla come il joystick delle MPK |
| **Levetta sinistra**, verticale | `PNL_MOD(0…127)`, in su o in giù | **Modulazione**, torna a 0 quando la levetta torna al centro |
| **Levetta destra**, su/giù | `PNL_ENC_TURN(ENC_CHORD_VOICING, ±1)` | **Chord Voicing**: su = più in alto |
| **Levetta destra**, destra/sinistra | `PNL_ENC_TURN(ENC_BASS_VOICING, ±1)` | **Bass Voicing**: destra = su di un'ottava |
| **R3** | `PNL_ENC_DOWN/UP(ENC_CHORD_VOICING)` | Chord Voicing premuto: Split ↔ Octave |
| **L3** | `PNL_ENC_DOWN/UP(ENC_BASS_VOICING)` | Bass Voicing premuto: Mod, come Y |
| **L2** | `PNL_MACRO(MACRO_TAP_TEMPO)` alla pressione | **Tap tempo**, come T2 del pad |
| **R2** | `PNL_MACRO(MACRO_FILL, 1/0)` | **Fill** finché è tenuto, come T4 del pad |

  Regole:
  - la piattaforma legge gli assi con i limiti di `EVIOCGABS` e li manda già scalati: levette in −32767…32767 con 0 al centro, grilletti in 0…255 (PLT-055). Sulla Flip sono `ABS_X`/`ABS_Y` (sinistra), `ABS_RX`/`ABS_RY` (destra), `ABS_Z`/`ABS_RZ` (L2, R2), già in quelle scale [O, evtest del 17/10/2026];
  - bend e modulazione hanno la **zona morta del 20%** di PLT-055, poi tutta la corsa; un tremolio sotto i 64 punti di bend non esce;
  - i passi della levetta destra scattano **oltre il 50%** della corsa, si ripetono a 400 ms e poi ogni **150 ms**, ogni **50 ms oltre il 90%** (come MIDI-093), e si lasciano **sotto il 40%**;
  - L2 e R2 sono premuti **sopra 160** e lasciati **sotto 96** (PLT-055);
  - l'asse Y delle levette cresce verso il basso (convenzione di Linux) [V: su = Chord Voicing più in alto, da provare sulla Flip];
  - con la MK4 bend e modulazione arrivano anche dalle ruote: vale l'ultima mossa;
  - se la Flip si perde, bend e modulazione tornano a 0 e il Fill di R2 si chiude.

- **MIDI-139** — **La batteria che si inventa** [D, **chiesta da Luigi il 18/10/2026**: «la filosofia deve essere quella di utilizzare i 3 encoder del pad per "inventare" in tempo reale i loop di batteria», poi «un tasto per entrare in modalità crea e poi manopole e pressioni sulle manopole. ripremo il tasto per chiudere l'editing»]. Il tasto è **T11 DRUMS** (o Mod + BPM): acceso, oltre alla batteria a tastiera di MIDI-135, le tre manopole del pad creano il loop di batteria di `10` ACC-215; spento, l'editing si chiude, le manopole tornano ai voicing e il loop resta com'è e continua a suonare finché non si sceglie un Beat del menu.

| Manopola | Girata | Premuta |
|---|---|---|
| **M** | **Densità** 0…10 della parte scelta, o di tutto: 0 tace, 1 è lo scheletro dello stile, 10 suona tutto | **Play / Stop** del loop (come la pressione di BPM) |
| **m1** | **Stile** (Groove): Techno, Rock, Funk, Break, Halftime, Dub, Bossa, Electro, Acid, Industrial e, dal 19/10/2026, House, Garage, Jungle, DnB, Dubstep, Trap, Synthwave, Synthpop, Lo-Fi, Trip Hop, Chiptune, Glitch, EBM, Afrobeat, Tabla, Salsa, Reggaeton, Jazz, Arena, Preset (`10` ACC-215, MIDI-141) | **Parte** che M regola: tutto, cassa, rullante, charleston, aperto, percussioni |
| **m2** | **Variazione** 0…99: 0 è lo stile com'è, ogni scatto un'idea nuova, tornando indietro si ritrova quella di prima | **Idea nuova**: una variazione a caso, ripetibile (`MACRO_KNOB_CLICK`) |

  Regole:
  - il primo tocco di una manopola sostituisce il Beat che suonava con il loop inventato, nello stile più vicino (Funk → Funk, Disco → Techno, Boom Bap → Break…); il primo scatto di m1 non cambia stile. Se il Beat era fermo resta fermo: parte con M premuta o con BPM;
  - la densità di una parte è quella di tutto più uno scarto; portata a 0 la parte resta muta anche se si alza la densità di tutto, finché non la si rialza;
  - m2 premuta e girata è il volume del Beat; m1 tenuta resta il modificatore Mod (Mod + BPM, Mod + Loop) e in quel caso il suo rilascio non cambia parte;
  - i cambi valgono dal sedicesimo dopo: il loop non riparte, la battuta e il loop del looper restano allineati; il Fill di T4 e la scelta del kit (K1) valgono anche per il loop inventato;
  - lo stesso vale per il fuoco della Flip sotto DRUMS: la levetta destra e R3 (Chord Voicing) sono M, L3 e Y (Bass Voicing) sono m1;
  - sulla plancia la zona dell'accordo mostra la griglia del loop (`30` UI-176) e le celle CH.VOICING e BS.VOICING diventano DENSITY e GROOVE; sul case la legenda delle manopole sotto DRUMS è DENSITY, GROOVE, VARIATION (`60` CASE-045).

- **MIDI-140** — **Drop** [D, **scelto da Luigi il 19/10/2026** fra quattro proposte (Drop, scelta rapida della tonalità, Perform on/off, mute del loop), al posto del Lock di MIDI-131]. **T13 tenuto**: il Beat (tabella o loop inventato), i colpi di batteria del loop e il basso tacciono subito; al rilascio rientrano a tempo, sul battito dopo (`10` ACC-217). È il break della techno e del dub, e fa il paio con il Fill di T4. Regole:
  - il profilo emette `PNL_MACRO(MACRO_DROP, 1)` alla pressione e `MACRO_DROP, 0` al rilascio, come il Fill; se il pad si stacca con T13 tenuto, il rilascio sintetico arriva prima di `PNL_SRC_LOST` (MIDI-127);
  - suonano sempre: gli accordi e le loro performance, il metronomo e il count-in, i colpi suonati dal vivo (tasti sotto DRUMS, pad del banco B, Roll), che entrano nel loop se registra;
  - Beat e loop vanno avanti in silenzio: al rientro sono al loro posto. Le voci del basso continuano, quindi una nota tenuta ricompare al rientro (`20` SND-539);
  - la testata scrive «DROP» finché T13 è tenuto (`30` UI-126); sul case l'etichetta di T13 è DROP, in negativo come gli altri stati (`60` CASE-043). T13 sta nella quinta colonna, quella degli stati di Stame.

- **MIDI-141** — **La libreria dei kit e degli stili** [D, **chiesta da Luigi il 19/10/2026**: «voglio anche una libreria enorme di batterie»]. Quaranta kit (`20` SND-541), sessanta Beat (`10` ACC-218) e trenta stili della batteria che si inventa (`10` ACC-215), scelti con i comandi che c'erano, senza tasti nuovi:
  - **K1 girata** sotto DRUMS scorre i 41 valori del kit (0 = quello del Beat, poi 1…40); la banda scrive numero, nome e stile («Kit 06 808 Boom», «Synth, analog»);
  - **K1 premuta** (SHIFT + K1 della MK4; A della Flip sulla cella KIT) sotto DRUMS apre la **lista dei kit** (`30` UI-177) al posto di quella dei suoni: la manopola di navigazione (o K1) scorre, premuta sceglie; il kit vale subito, anche per il Beat che suona, e la lista resta aperta per provarne un altro. Fuori da DRUMS SHIFT + K1 resta la lista dei suoni;
  - **m1 girata** sotto DRUMS scorre i trenta stili (MIDI-139); **BPM tenuto** apre la lista dei Beat, che ora scrive accanto a ogni Beat il suo kit;
  - il kit scelto è uno stato già in vista (la cella KIT, la banda); resta quando DRUMS si spegne, come prima. La demo azzera il kit all'inizio e lo rimette alla fine (MIDI-135).

---

## 9. Tasti fisici della Flip

- **MIDI-090** — Stame DEVE leggere i tasti direttamente da evdev, dal dispositivo «MIYOO Player1» cercato per nome (di solito `/dev/input/event5`, ma un dispositivo HID collegato all'avvio, come il macro pad, lo sposta: `50` PLT-053), e NON DEVE usare insieme il gamepad di SDL, che legge lo stesso dispositivo con un'altra mappatura e lascia tasti "già premuti" [O]. Lo strato di piattaforma traduce i codici in un enum portabile con prefisso `PAD_*`. I nomi `BTN_*` sono vietati, perché collidono con le macro di `linux/input.h` [O].

| Tasto | Codice evdev [O] |
|---|---|
| A, B, X, Y | 305, 304, 308, 307 |
| L1, R1 | 310, 311 |
| L2, R2 | assi `ABS_Z`, `ABS_RZ` (0–255) |
| SELECT, START, MENU | 314, 315, 316 |
| L3, R3 | 317, 318 |
| Croce | `ABS_HAT0X`, `ABS_HAT0Y` |
| Levette | assi ABS 0/1 (sinistra) e 3/4 (destra), limiti letti con `EVIOCGABS` |

- **MIDI-091** — L2 e R2 contano come premuti sopra 160 e rilasciati sotto 96, come PLT-055 [D; allineato il 17/10/2026]. Le levette hanno la zona morta del 20% di PLT-055 per bend e modulazione; i comandi a passi (i voicing di MIDI-138, il modo tascabile) scattano oltre il 50% della corsa e si lasciano sotto il 40% [D].

### 9.1 Schema a fuoco (sempre attivo)

- **MIDI-092** — Profilo `flip_tasti`: i tasti della Flip DEVONO seguire lo **schema a fuoco** di `30-interfaccia.md` UI-132, sia con la MPK collegata sia senza [D; **deciso da Luigi il 13/10/2026**]. Il pannello ha un **fuoco** su uno degli 11 controlli rotanti, evidenziato a video:

| Tasto Flip | Evento | Funzione |
|---|---|---|
| L1 / R1 | `PNL_FOCUS_STEP(−1/+1)` | Sposta il fuoco, in giro ciclico: Sound, Perform, FX, Key, Bass, Loop, BPM, Volume, Options, Chord Voicing, Bass Voicing |
| Croce su / giù | `PNL_ENC_TURN(ENC_FOCUS, +1/−1)`, ripetizione come MIDI-082 | Ruota l'encoder con il fuoco, oppure scorre la lista aperta |
| Croce destra / sinistra | `PNL_ENC_TURN(ENC_FOCUS, +1/−1)`, con ripetizione | Come su / giù |
| A | `PNL_ENC_DOWN/UP(ENC_FOCUS)` | Pressione dell'encoder con il fuoco: conferma; tenere = tenere; A tenuto + croce = premere e ruotare |
| B | `PNL_BACK` | Indietro |
| **X** | `PNL_MACRO(MACRO_HOLD_TOGGLE)`; con la Plus il **PUSH** (§8.6) | **Hold** dell'accordo (MIDI-137, come T1 del pad). Con la Plus collegata è il suo PUSH: tenuto, la manopola della Plus toccata o girata viene "premuta" (premere, tenere, premere e ruotare) |
| Y | `PNL_ENC_DOWN/UP(ENC_BASS_VOICING)` | Bass Voicing premuto, come m1 del macro pad: il modificatore delle combinazioni (Y + A con il fuoco su Loop = uscita hard dal loop) |
| SELECT | `PNL_ENC_DOWN/UP(ENC_OPTIONS)` | Pulsante di Options |
| START | `PNL_ENC_DOWN/UP(ENC_BPM)`; con la MK4 `PNL_MACRO(MACRO_FILL, 1/0)` | Pulsante di BPM (beat o metronomo); con la MK4, che ha STOP/PLAY, il **Fill** finché è tenuto (MIDI-137) |
| MENU | `PNL_MACRO(MACRO_SYSTEM_MENU)` | Menu della piattaforma (`30` UI-129): Panic, Pocket Mode, Quit Stame… |
| Levetta sinistra | `PNL_BEND` (orizzontale), `PNL_MOD` (verticale) | Pitch bend e modulazione, a molla (MIDI-138) |
| Levetta destra | `PNL_ENC_TURN(ENC_CHORD_VOICING)` su/giù, `PNL_ENC_TURN(ENC_BASS_VOICING)` destra/sinistra | I due voicing, a passi con ripetizione (MIDI-138) |
| L3, R3 | `PNL_ENC_DOWN/UP(ENC_BASS_VOICING)`, `PNL_ENC_DOWN/UP(ENC_CHORD_VOICING)` | Mod, Split/Octave |
| L2, R2 | `PNL_MACRO(MACRO_TAP_TEMPO)`, `PNL_MACRO(MACRO_FILL, 1/0)` | Tap tempo, Fill finché è tenuto |

**Sempre vivi (17/10/2026).** I tasti della Flip non tacciono mai, con qualunque apparecchio collegato: sono la console di gestione (MIDI-137, al posto delle riserve inerti di MIDI-134). X e START cambiano ruolo secondo la tastiera collegata, come dice la tabella.

- **MIDI-095** — **Uscita dall'app:** l'unica strada DEVE essere MENU → «Quit Stame», oltre a `SIGTERM` (`50` PLT-086). Non c'è una combinazione di tasti riservata: SELECT e START servono già a Options e BPM [D].

### 9.2 Modo tascabile (opzionale)

Serve per suonare Stame anche senza la MPK, in viaggio. È più povero dell'originale: niente velocity, una sola fondamentale alla volta, scelta con la levetta. Però copre tutte le funzioni.

- **MIDI-093** — Stame DOVREBBE offrire un **modo tascabile**, una variante del profilo `flip_tasti` che sostituisce lo schema di §9.1 [D]:

| Comando | Evento | Funzione |
|---|---|---|
| Levetta sinistra | sceglie la classe di nota: 12 settori da 30°, Do in alto, in senso orario per semitoni; isteresi di 5° ai bordi | Nessun evento da sola |
| A | `PNL_KEY_DOWN(settore, 100)` alla pressione, `PNL_KEY_UP` al rilascio; se il settore cambia con A premuto: `KEY_UP` del vecchio e `KEY_DOWN` del nuovo | Tasto della tastiera (velocity fissa 100 [D]) |
| L2, L1, R1, R2 | `PNL_CHORD_DOWN/UP`: Dim, Min, Maj, Sus | Tasti tipo, nello stesso ordine da sinistra a destra dell'originale |
| Croce sinistra, giù, destra, su | `PNL_CHORD_DOWN/UP`: 6, m7, M7, 9 | Estensioni |
| Levetta destra, asse X | `PNL_ENC_TURN(ENC_CHORD_VOICING, ±1)`: un passo oltre il 50% della corsa, ripetuto ogni 150 ms; ogni 50 ms oltre il 90% | Chord Voicing |
| Levetta destra, asse Y | `PNL_ENC_TURN(ENC_FOCUS, ±1)`, stessa ripetizione | Ruota l'encoder con il fuoco |
| R3 | `PNL_ENC_DOWN/UP(ENC_FOCUS)` | Premere, tenere, premere e ruotare l'encoder con il fuoco |
| X / Y | `PNL_FOCUS_STEP(−1/+1)` | Sposta il fuoco, nello stesso giro di §9.1 |
| B | `PNL_BACK` | Indietro |
| L3 | `PNL_ENC_DOWN/UP(ENC_BASS_VOICING)` | Bass Voicing premuto (modificatore) |
| SELECT, START | Options, BPM | Come in §9.1 |
| MENU | `MACRO_SYSTEM_MENU` | Come in §9.1 |

- **MIDI-094** — Il modo tascabile DEVE essere **spento per default** e si accende solo dal menu della piattaforma (MENU → «Pocket Mode», `30` UI-129) [D; **deciso da Luigi il 13/10/2026**]. Se la MPK si collega mentre il modo è acceso, Stame torna allo schema di §9.1, ma solo quando nessun tasto, pad o pulsante è premuto; altrimenti il cambio aspetta il rilascio. La scelta NON DEVE essere ricordata fra un avvio e l'altro: Stame riparte sempre con lo schema a fuoco.

---

## 10. Strato di input logico

### 10.1 Eventi del pannello: il contratto con il nucleo

- **MIDI-100** — Il nucleo DEVE ricevere solo questi eventi, definiti in un header senza dipendenze [D]:

```c
/* core/input/panel.h — C11, nessuna dipendenza */
#include <stdint.h>

typedef enum {                      /* i controlli rotanti dell'originale */
    ENC_SOUND, ENC_PERFORM, ENC_FX, ENC_KEY, ENC_BASS, ENC_LOOP,
    ENC_BPM, ENC_VOLUME, ENC_OPTIONS, ENC_CHORD_VOICING, ENC_BASS_VOICING,
    ENC_COUNT,
    ENC_FOCUS = 0x40                /* pseudo-encoder: lo risolve il nucleo (MIDI-104) */
} enc_id_t;

typedef enum {                      /* gli 8 tasti accordo */
    CHB_DIM, CHB_MIN, CHB_MAJ, CHB_SUS, CHB_6, CHB_MIN7, CHB_MAJ7, CHB_9, CHB_COUNT
} chord_btn_t;

typedef enum {
    MACRO_LOOP_STOP, MACRO_LOOP_CLEAR, MACRO_PANIC, MACRO_SYSTEM_MENU, MACRO_LOOP_UNDO, MACRO_LOOP_OVERDUB,
    MACRO_DROP,                     /* b = 1 tenuto, 0 rilasciato (MIDI-140) */
    MACRO_VIEW_TOGGLE,              /* Geek Out <-> la vista di prima (MIDI-132) */
    MACRO_CONTROLS_PAGE             /* apre o chiude la pagina dei comandi della Flip (MIDI-132) */
} macro_t;

typedef enum {
    PNL_KEY_DOWN, PNL_KEY_UP,       /* a = classe 0..11 (0 = Do), b = velocity 1..127 */
    PNL_CHORD_DOWN, PNL_CHORD_UP,   /* a = chord_btn_t */
    PNL_ENC_TURN,                   /* a = enc_id_t, b = scatti con segno, b != 0 */
    PNL_ENC_DOWN, PNL_ENC_UP,       /* a = enc_id_t */
    PNL_BACK,                       /* chiude overlay o risale nel menu */
    PNL_FOCUS_STEP,                 /* b = ±1 */
    PNL_BEND,                       /* b = -8192..8191 */
    PNL_MOD,                        /* b = 0..127 */
    PNL_SUSTAIN,                    /* b = 0 o 1 */
    PNL_MACRO,                      /* a = macro_t */
    PNL_SRC_CONNECTED, PNL_SRC_LOST /* a = src_t */
} pnl_type_t;

#define PNL_F_VERTICAL 0x80         /* in a, solo per PNL_ENC_TURN(ENC_FOCUS): scatto da un comando verticale (MIDI-105) */

typedef enum { SRC_MPK, SRC_FLIP, SRC_MACROPAD, SRC_COUNT } src_t;   /* SRC_MACROPAD: §8.10 */

typedef struct {
    uint8_t  type;                  /* pnl_type_t */
    uint8_t  src;                   /* src_t */
    uint8_t  a;
    int16_t  b;
    uint32_t t_us;                  /* tempo d'arrivo, orologio monotono */
} pnl_event_t;
```

- **MIDI-101** — Un profilo controller DEVE avere questa interfaccia, e aggiungere un controller DEVE voler dire solo aggiungere un profilo, senza toccare il nucleo [D]:

```c
/* core/input/profile.h */
#define PNL_B_SYNTH 1   /* b di un PNL_ENC_UP sintetico (MIDI-103); i rilasci veri hanno b = 0 */

typedef struct {
    const char *name;
    void (*reset)(void *st);
    /* messaggio MIDI completo -> 0..max eventi; ritorna quanti */
    int  (*on_midi)(void *st, uint8_t port, const uint8_t *m, uint16_t n,
                    uint32_t t_us, pnl_event_t *out, int max);
    /* tasto della console (PAD_*), del macro pad (MPAD_*, §8.10) o asse -> eventi */
    int  (*on_pad)(void *st, uint16_t pad_code, int32_t value,
                   uint32_t t_us, pnl_event_t *out, int max);
    /* chiamata ogni 10 ms: ripetizioni, soglie a tempo */
    int  (*on_tick)(void *st, uint32_t t_us, pnl_event_t *out, int max);
    /* sorgente persa: rilasci sintetici di tutto ciò che è premuto */
    int  (*on_lost)(void *st, uint32_t t_us, pnl_event_t *out, int max);
} ctl_profile_t;
```

- **MIDI-102** — Più sorgenti possono essere attive insieme (MPK, macro pad e tasti della Flip). Il nucleo DEVE tenere lo stato di pressione **per sorgente**: un controllo risulta premuto se lo è in almeno una sorgente; `PNL_ENC_UP` o `PNL_CHORD_UP` di una sorgente non rilascia il controllo tenuto da un'altra [D]. Aggiungere una sorgente vuol dire aggiungere un valore a `src_t` e un profilo: la logica del nucleo non cambia.

### 10.2 Profili previsti

| Profilo | Sorgente | Uso |
|---|---|---|
| `mpk_stame` | MPK porta 1 | Programma STAME (§8.5); passa da solo a `mpk_fabbrica` (§8.8) |
| `mpk_fabbrica` | MPK porta 1 | Programma di fabbrica o sconosciuto, funzioni ridotte |
| `flip_tasti` | evdev | Schema a fuoco (§9.1) o modo tascabile, se acceso dal menu (§9.2) |
| `pad_brimford` | evdev, macro pad BRIMFORD in esclusiva | Pulsanti degli encoder T1–T9, Back, Menu, Panic; manopole Chord Voicing, Bass Voicing e liste (§8.10) |

Un profilo generico per qualunque tastiera MIDI, con apprendimento dei controlli, è nell'Appendice A.

### 10.3 Riconoscimento dei gesti

Gli encoder dell'originale hanno quattro gesti [M]: **premere** (commuta), **ruotare** (valore), **tenere premuto** (menu o lock), **premere e ruotare** (funzione secondaria).

- **MIDI-103** — Il riconoscitore DEVE produrre, per ciascun encoder, questi gesti [D]:

```
per ogni encoder e:  stato IDLE | DOWN | HELD,  t_down, ruotato
PNL_ENC_DOWN(e): stato = DOWN; t_down = adesso; ruotato = falso
PNL_ENC_TURN(e, n):
    stato IDLE           -> G_TURN(e, n)
    stato DOWN           -> ruotato = vero; G_PRESS_TURN(e, n)
    stato HELD           -> ignora                          [D]
ogni 10 ms:
    DOWN, !ruotato, adesso - t_down >= T_HOLD(e)       -> G_HOLD(e); stato = HELD
    HELD, e == ENC_LOOP, adesso - t_down >= T_HOLD2     -> G_HOLD_LONG(e) (una volta)
PNL_ENC_UP(e):
    DOWN, !ruotato, b != PNL_B_SYNTH -> G_PRESS(e)
    sempre                           -> G_RELEASE(e); stato = IDLE
```

  Un rilascio che l'utente non ha fatto (sorgente persa, cambio di banco dei pad: MIDI-089, MIDI-112, MIDI-127; X tenuto quando si stacca la Flip) arriva come `PNL_ENC_UP` con `b = PNL_B_SYNTH`. Chiude il gesto con `G_RELEASE` ma senza `G_PRESS`, così non esegue la funzione del tocco, per esempio Rec del looper o Key mode on/off [D, 14/10/2026].

| Costante | Valore | Etichetta |
|---|---|---|
| `T_HOLD` per Bass e BPM | 1 s | [M] |
| `T_HOLD` per Key, Perform, FX, Sound, Loop, Volume, Options, Bass Voicing | 1 s | [V VO-12] |
| `T_HOLD2` per Loop (uscita morbida dopo 2 s) | 2 s | [M] |

  Il nucleo legge anche se un encoder è tenuto (`DOWN` o `HELD`) per le combinazioni: per esempio `G_PRESS(ENC_LOOP)` con `ENC_BASS_VOICING` tenuto = uscita hard dal loop [M]. Il significato di ogni gesto sta in `10` e `30`.

  Il riconoscitore riceve lo **stato unito** di MIDI-102: `PNL_ENC_DOWN(e)` quando `e` passa da libero a premuto in almeno una sorgente, `PNL_ENC_UP(e)` quando lo rilasciano tutte; `PNL_ENC_TURN(e)` arriva da qualunque sorgente. Così T4 tenuto sul macro pad + K4 girata sulla MPK dà `G_PRESS_TURN(ENC_KEY)` (MIDI-121) [D, 13/10/2026].

### 10.4 Il fuoco

- **MIDI-104** — `ENC_FOCUS` DEVE essere risolto dal nucleo, in questo ordine [D]:
  1. l'encoder che ha aperto la lista o il menu visibile (Options, menu Loop, lista dei suoni, dei modi, degli effetti, dei beat), finché non si chiude;
  2. altrimenti il **fuoco del pannello**: un solo valore, condiviso da tutte le sorgenti, che parte da Sound. Lo cambiano `PNL_FOCUS_STEP` e la pressione di un encoder da qualunque sorgente (`PNL_ENC_DOWN(e)` con `e` ≠ `ENC_FOCUS` porta il fuoco su `e`). Così m2 del macro pad, « », il joystick della MPK e la croce della Flip ruotano Options, o qualunque encoder, subito dopo averne premuto il pulsante.

  Lo schermo DEVE mostrare quale encoder ha il fuoco (resa in `30`).

  Decisione di Luigi del 16/10/2026 `[D]`: l'**overlay** di valore (la banda che per 3,4 s mostra il controllo appena girato, `30` UI-154) NON prende la manopola del fuoco. Girare K1 e poi m2 regola l'encoder con il fuoco, non Sound; per regolare con m2 ciò che si è appena girato si preme prima il suo pulsante (punto 2). Fino al 15/10 l'overlay era padrone della manopola finché non spariva, e dalla revisione di quel giorno la pressione di un altro encoder glielo toglieva: la regola è ora una sola, senza la finestra di 3,4 s.

- **MIDI-105** — **Verso dei comandi verticali** [D, 13/10/2026]. Croce ▲▼ della Flip e joystick ▲▼ della MPK emettono `PNL_ENC_TURN(ENC_FOCUS | PNL_F_VERTICAL, ±1)` con su = +1. Il nucleo DEVE:
  - con una lista o un menu aperto, invertire il segno: su = voce precedente, cioè più in alto sullo schermo (`30` UI-157);
  - senza lista, usare il segno così com'è: su = valore più alto.
  Le rotazioni vere (manopole della MPK e del macro pad, m2 compresa, « », croce ◀▶) non portano il flag e seguono sempre la regola orario = successiva (`30` UI-074).

### 10.5 Esempio: dal byte al gesto

```
MPK porta 1:  B0 46 01            (K1 relativo, +1)
midi_parse -> {port 0, B0 46 01}
mpk_stame  -> acc[K1] = 1 < step 2: nessun evento
MPK porta 1:  B0 46 01
mpk_stame  -> acc[K1] = 2 -> PNL_ENC_TURN(ENC_SOUND, +1)
gesti      -> G_TURN(ENC_SOUND, +1)
nucleo     -> suono successivo (10/20); overlay (30)
```

---

## 11. Hot-plug e disconnessione

- **MIDI-110** — Senza MPK collegata, lo strato di piattaforma DEVE cercarla ogni secondo (MIDI-070) senza bloccare audio e interfaccia [O, guida §17.4].
- **MIDI-111** — La disconnessione DEVE essere rilevata da `POLLERR`, `POLLHUP` o da `read()`/`write()` che falliscono con `ENODEV` o `EIO`. Allora: chiudere entrambe le porte e tornare alla ricerca [O].
- **MIDI-112** — Alla disconnessione il profilo DEVE emettere, con `on_lost`, i rilasci sintetici di tutto ciò che risultava premuto (tasti, tasti accordo, encoder, PUSH), poi `PNL_SUSTAIN(0)`, `PNL_BEND(0)` e `PNL_SRC_LOST`. La mod wheel resta all'ultimo valore, come la ruota fisica [D].
- **MIDI-113** — Una disconnessione NON DEVE fermare il suono interno né il trasporto: loop, beat e clock interno continuano; le note tenute si chiudono per effetto dei rilasci sintetici [D].
- **MIDI-114** — Senza MPK il DIN non esiste più e i Note Off delle note già mandate non possono partire. Stame DEVE tenere nel registro le note rimaste accese sulla destinazione DIN e, al ricollegamento, eseguire per prima cosa il panic sulla porta 2 (MIDI-062, punti 1 e 2) [D].
- **MIDI-115** — Al ricollegamento Stame DEVE rifare la sequenza di avvio (§8.9); se il trasporto è in moto, mandare `FA` sulle destinazioni del clock e riprendere i `F8` dal tick successivo [D].
- **MIDI-116** — Se dopo il ricollegamento la MPK ha un numero di scheda diverso, Stame DEVE ritrovarla comunque (MIDI-070) [V VM-26].

Il macro pad segue regole analoghe, in MIDI-127.

---

## 12. Verifiche da fare sulla MPK (sintesi)

L'elenco completo dei 29 test è nelle [Questioni aperte](#questioni-aperte); comandi e procedure nel §18 della guida alla Plus. Prima di tutto: porta OTG mai forzata in host; **nessun SysEx di programma senza backup e senza l'ok di Luigi** (MIDI-077).

| Priorità | Test | Cosa decide |
|---|---|---|
| 1 — senza questi non si parte | VM-25 driver e riconoscimento; VM-1 consumo; VM-2 DIN come interfaccia; VM-26 hot-plug | MIDI-025, MIDI-070, MIDI-110…116 |
| 2 — taratura della mappa | VM-8 Relative e accelerazione; VM-9 e VM-29 joystick; VM-13 LED del trasporto; VM-15 pedale; VM-22 Trpt e PadAT globali; VM-27 latenza e traffico | MIDI-081…085 |
| 3 — clock e CV | VM-5 clock in ingresso alla MPK; VM-6 Clock Out; VM-4 sorgente della CV; VM-7 tracking della CV | MIDI-038, MIDI-086 |
| 4 — comodità | VM-12 LED dei pad; VM-16 nomi delle manopole; VM-11 Program Change; VM-23 cambio di programma; VM-20 nota più bassa; VM-28 velocity dei pad | MIDI-087, MIDI-119 |
| 5 — solo con l'ok di Luigi | VM-10 lettura SysEx; VM-21 backup dei programmi; VM-24 traffico dell'editor | MIDI-077 |

Per il macro pad le verifiche sono VP-1…VP-8 (in [Questioni aperte](#questioni-aperte)). Prima di scrivere `pad_brimford` servono VP-1 (identità e nodi evdev), VP-2 (codici ammessi) e VP-3 («giù» e «su» delle pressioni).

---

## 13. Casi di prova

| ID | Situazione | Atteso |
|---|---|---|
| T-MIDI-01 | Chord su ch3, Performance su ch1; nota singola 52, velocity 49, poi rilascio | `92 34 31` `90 34 31`; al rilascio `80 34 00` `82 34 00`; alla nota successiva **nessun** `82 34 00` in più |
| T-MIDI-02 | Performance e Chord entrambi su ch1; accordo tenuto | Ogni nota: due Note On; un solo Note Off al rilascio |
| T-MIDI-03 | Velocity Sense Off | Ogni Note On con velocity 100 |
| T-MIDI-04 | Pressione di BPM con trasporto fermo | `FC` `FA`, poi `F8` ogni 60/(BPM·24) s; nessun `FB` |
| T-MIDI-05 | Pausa del loop con il basso in corso | `FC`, poi `81 kk 00`; nessun `F8` dopo |
| T-MIDI-06 | Rotazione di BPM da 87 a 88 | `B0 70 58` sul canale Performance |
| T-MIDI-07 | Performance su Off, scatto di Volume | Nessun CC 113 |
| T-MIDI-08 | Cambio del canale Bass da 2 a 5 con nota di basso accesa | `81 kk 00` prima di qualunque messaggio sul ch5 |
| T-MIDI-09 | Ingresso DIN: `9A 3C 64` (ch11) | Nessun suono |
| T-MIDI-10 | Ingresso DIN: `F0 7E 7F 06 01 F7` | Risposta `F0 7E 7F 06 02 7D 53 54 01 00 …`; mai `00 22 0C` |
| T-MIDI-11 | MPK: B8 giù, K4 +1, B8 su entro 1 s | `G_PRESS(ENC_KEY)`; nessun cambio di tonalità |
| T-MIDI-12 | MPK: due Do (48 e 60) premuti, rilascio di 48 | Un solo `PNL_KEY_DOWN(0)`; `PNL_KEY_UP(0)` solo al rilascio di 60 |
| T-MIDI-13 | MPK scollegata con accordo tenuto, poi ricollegata | Rilasci sintetici, suono interno chiuso; al ricollegamento Note Off sul DIN e CC 123 + 120 |
| T-MIDI-14 | K1 in Absolute (programma di fabbrica), valore da 40 a 44 | Profilo in fabbrica; 2 scatti di Sound con `step` = 2 |
| T-MIDI-15 | Nomi esposti | Nessuno comincia con il nome dell'originale (anche con le maiuscole o dopo spazi iniziali) |
| T-MIDI-16 | Macro pad: F16 giù, poi MPK K4 +2 (uno scatto), poi F16 su | `G_PRESS_TURN(ENC_KEY, +1)` (transpose); nessun `G_PRESS(ENC_KEY)` |
| T-MIDI-17 | Macro pad: F24 tenuto 0,5 s, poi tenuto 1,2 s | Primo: nessun evento; secondo: un solo `MACRO_PANIC`, a 1 s |
| T-MIDI-18 | Macro pad: KP5 giù, F18 giù e su, KP5 su | `G_PRESS(ENC_LOOP)` con `ENC_BASS_VOICING` tenuto: uscita hard dal loop |
| T-MIDI-19 | Lista dei suoni aperta; KP3 giù e su, poi KP1 giù e su | Voce successiva, poi precedente; nessun `PNL_F_VERTICAL` |
| T-MIDI-20 | Macro pad scollegato con F13 tenuto | `PNL_ENC_UP(ENC_SOUND)` sintetico, poi `PNL_SRC_LOST(SRC_MACROPAD)`; nessun `G_HOLD` dopo |
| T-MIDI-21 | Macro pad: F17 tenuto con ripetizione automatica (valori 1, 2, 2, 2, 0) | Un solo `PNL_ENC_DOWN(ENC_BASS)` e un solo `PNL_ENC_UP` |

---

## Appendice A — Migliorie opzionali (spente per default)

Per il principio di fedeltà queste opzioni esistono ma partono spente [D].

- **MIDI-200** — **Clock in**: opzione MIDI Clock = Out (default) / In. Con In il tempo segue gli `F8` del DIN IN (media su 24–48 tick); loop e beat seguono `FA`, `FB`, `FC` e SPP; lo spegnimento del clock in ripristina l'ultimo BPM interno.
- **MIDI-201** — **`FB` alla ripresa** dalla pausa del loop, mantenendo la posizione, al posto di `FA`.
- **MIDI-202** — **CC di stato come comandi** in ingresso (103, 107, 108, 112, 113): Key, BPM, Perform e volume dalla DAW. BPM sopra 127: CC 112 + CC 113 come MSB/LSB, oppure solo SysEx.
- **MIDI-203** — **Program Change** in ingresso per il Sound; **CC 7** per il volume master.
- **MIDI-204** — **Ingresso accordi**: le note di un canale scelto fanno da tastiera dell'originale (fondamentale + tasti accordo su note fisse), cosa che l'originale non fa.
- **MIDI-205** — **Inoltro** di pitch wheel e mod wheel della MPK sul canale Performance.
- **MIDI-206** — **Latch** con il pedale della MPK (l'originale non ha né latch né hold [O]).
- **MIDI-207** — **Zone della tastiera** della MPK: ottava più bassa = solo basso, resto = accordi.
- **MIDI-208** — **Altre uscite**: interfaccia USB-MIDI class compliant su hub; RTP-MIDI via Wi-Fi verso il computer; gadget USB `f_midi` se il kernel lo permette (senza MPK). Nome sempre "Stame".
- **MIDI-209** — **Doppio Note Off 3.92** sul flusso Chord, solo per i confronti (MIDI-017).
- **MIDI-210** — **Profilo generico** per qualunque tastiera MIDI, con apprendimento dei controlli.
- **MIDI-211** — **Caricamento di STAME via SysEx** all'avvio, solo alle condizioni di MIDI-077.

---

## Questioni aperte

### Da verificare sull'originale (VO)

| ID | Domanda | Default scelto | Requisiti |
|---|---|---|---|
| VO-1 | Velocity fissa con Velocity Sense Off; curva della velocity dai tasti (nelle catture 21–49) | 100; velocity della MPK invariata | MIDI-020, MIDI-079 |
| VO-2 | Range del BPM e come esce CC 112 sopra 127 | 60–200; CC 112 saturato a 127 | MIDI-021, MIDI-036 |
| VO-3 | I CC di stato seguono il canale Performance? Escono con Performance su Off? | Seguono; con Off non escono | MIDI-021 |
| VO-4 | I canali in ingresso seguono il menu MIDI Channels? | No: fissi 1 e 2 | MIDI-041 |
| VO-5 | CC 115, 116, 118: quando escono e con quali valori | Non trasmessi | MIDI-022 |
| VO-6 | Spegnendo il metronomo (senza beat né loop) il clock continua dopo `FC FA`? | Continua | MIDI-034 |
| VO-7 | `FA`/`FC` nel menu Loop: a quali azioni corrispondono; count-in; ripresa dalla pausa (`FA` o `FB`); uscita dal loop | Vedi tabella MIDI-034 | MIDI-034 |
| VO-8 | Accordi completi su ch1/ch2/ch3: ordine dei Note On e Off fra i flussi, ordine delle note nell'accordo, Note Off ai cambi d'accordo, doppio Note Off anche con gli accordi | Chord → Bass → Performance per gli On, inverso per gli Off | MIDI-014 |
| VO-9 | In riproduzione il loop manda tutti i flussi o solo il basso? | Tutti | MIDI-024 |
| VO-10 | La batteria ("On drums") e i beat mandano note MIDI? Su che canale? | No | MIDI-024 |
| VO-11 | Clock e trasporto escono identici sul DIN? | Sì | MIDI-037 |
| VO-12 | Tempi di "tenere premuto" per Key, Perform, FX, Sound, Loop, Volume, Options | 1 s | MIDI-103 |
| VO-13 | Numero MIDI della nota mostrata come "C3" o "C4" a schermo (convenzione dal 3.90) | Do centrale = 60 = C4 | MIDI-019 |
| VO-14 | La pressione di BPM riporta beat e clock all'inizio della battuta? | Sì (`FA` = inizio battuta) | MIDI-033 |
| VO-15 | "Premi e ruota" di Volume (volume del basso) e di BPM (volume del beat) mandano CC 113 o altro? | Nessun CC | MIDI-021 |

### Da verificare sulla MPK di Luigi (VM = test del §18 della guida alla Plus)

| ID | Test | Requisiti che ne dipendono |
|---|---|---|
| VM-1 | Assorbimento reale (pad, OLED, CV accesi) dalla porta OTG | §8.2 |
| VM-2 | Con la Flip come host il DIN fa da interfaccia? I tasti escono dal DIN OUT? (loopback DIN) | MIDI-025, MIDI-037 |
| VM-3 | Thru da DIN IN a DIN OUT in standalone | — (informativo) |
| VM-4 | Con CV Src = MIDI N, la CV legge dalla porta 1, dalla porta 2 o dal DIN IN? | MIDI-086 |
| VM-5 | Il clock dalla Flip guida arp, sequencer e Clock Out? Su quale porta? Serve lo Start? | MIDI-038 |
| VM-6 | Clock Out: livello, durata, PPQN reale; esce sempre o solo con arp o sequencer attivi? | MIDI-038 |
| VM-7 | Nota a 0 V, range e tracking della CV di pitch | MIDI-086 |
| VM-8 | Il Relative accelera? Valori girando piano e veloce | MIDI-081 |
| VM-9 | Joystick: quale CC è il verso positivo; centro in 1CC | MIDI-076, MIDI-078 |
| VM-10 | Lettura di un programma via SysEx (`0x66` → `0x67`?) — **solo con l'ok di Luigi e dopo il backup** | MIDI-077 |
| VM-11 | Program Change in ingresso: cambia programma? Lo ricorda all'accensione? Via DIN? | MIDI-077, MIDI-087 |
| VM-12 | LED dei pad pilotabili dall'host? | MIDI-076, MIDI-087 |
| VM-13 | LED del trasporto via Note On su Linux | MIDI-085 |
| VM-14 | Feedback delle manopole in Absolute (soft takeover?) | MIDI-088 |
| VM-15 | Pedale: CC 64 con 0/127? Polarità rilevata all'accensione? | MIDI-078 |
| VM-16 | L'OLED mostra il nome della manopola quando la si gira? | MIDI-076 |
| VM-17 | Quale controllo manda CC 114? | collisioni nella mappa |
| VM-18 | Start/Stop in ingresso avviano e fermano il sequencer interno? | MIDI-038 |
| VM-19 | Pad in modo CC: 127/0 o velocity? E in Toggle? | — (alternativa ai pad in Note) |
| VM-20 | Nota più bassa di fabbrica (probabilmente 48) | MIDI-207 |
| VM-21 | Contenuto degli altri 7 programmi di fabbrica (backup dall'editor) | MIDI-077 |
| VM-22 | Trpt e PadAT sono globali o del programma? | MIDI-076, MIDI-083 |
| VM-23 | Prog Select o il cambio di programma mandano qualcosa all'host? | MIDI-088 |
| VM-24 | Traffico SysEx dell'editor (Wireshark + USBPcap su Windows) | MIDI-077 |
| VM-25 | Il kernel della Flip ha `snd-usb-audio` e `snd-rawmidi`? Nomi delle porte | MIDI-070, MIDI-071 |
| VM-26 | Hot-plug: numero di scheda e nomi uguali dopo il ricollegamento? | MIDI-070, MIDI-116 |
| VM-27 | Latenza e jitter dal tasto alla `read()`; traffico con 4 manopole girate insieme (fino a ~240 msg/s ciascuna) | MIDI-004, budget in `50` |
| VM-28 | Pad: velocity reale, Full Level, Note Off durante l'aftertouch | MIDI-080 |
| VM-29 | Joystick: risoluzione, zona morta, valori a riposo | MIDI-082 |
| VM-30 | Pad tenuto mentre si preme BANK: il Note Off ha la nota del banco vecchio o del nuovo? I colori dei pad si possono dare per banco? | MIDI-089 |

### Da verificare sul macro pad BRIMFORD (VP)

| ID | Test | Default scelto | Requisiti |
|---|---|---|---|
| VP-1 | Identità: VID:PID, nome evdev, quanti nodi `/dev/input/event*` crea e quali codici dichiara ciascuno (`evtest`); se `EVIOCGRAB` riesce su tutti | **VID:PID `1189:8840`** [O 15/10/2026]; nodi evdev e `EVIOCGRAB` da provare sulla Flip | MIDI-124 |
| VP-2 | Il software sikaicase o `ch57x-keyboard-tool` ammettono F13–F24 e KP1–KP9? Nomi esatti nel file YAML; la configurazione resta dopo lo scollegamento? | Sì; altrimenti Learn Pad | MIDI-122, MIDI-123 |
| VP-3 | Pressione dei tasti e delle manopole: arrivano «giù» alla pressione e «su» al rilascio, o un tocco istantaneo? Ripetizione automatica? | **Chiusa il 15/10/2026: giù e su separati** [O]; ripetizione automatica solo quella del sistema | MIDI-121, MIDI-125, MIDI-126 |
| VP-4 | Rotazioni: un evento per scatto? Scatti veloci persi o accorpati (girare 20 scatti in fretta e contarli)? Le manopole hanno davvero gli scatti? | Un `KEY_DOWN` per scatto, nessuno perso | MIDI-125 |
| VP-5 | Posizione delle tre manopole rispetto ai tasti; quale è M, m1, m2; ordine delle manopole nella configurazione | Manopole a destra dei tasti, piccole in alto e grande in basso; indici 16–24 noti [O 15/10/2026]. Quale piccola è m1 e quale m2 resta da confermare sul pezzo; T13–T15 decisi il 15/10/2026 (Lock, View, Page: MIDI-131, MIDI-132) | MIDI-120, MIDI-122 |
| VP-6 | Assorbimento dalla porta OTG, con la batteria interna in carica e con l'RGB acceso e spento; MPK e macro pad insieme sull'hub senza PD | Regge con l'hub; altrimenti hub alimentato | MIDI-128 |
| VP-7 | L'RGB si può spegnere dalla configurazione e resta spento? | Spento | MIDI-122, MIDI-128 |
| VP-8 | Il comando dei LED (§8.10) dalla Flip: funziona sull'hidraw dell'interfaccia 0? Il colore resta dopo stacca e riattacca (cioè è scritto nella flash, che si consuma) o sta solo in RAM? Solo con Luigi presente e con il suo ok | Non provato: il 19/10/2026 Luigi ha detto di fermarsi; i LED del suo pad sono spenti | §8.10 |

### Decisioni di progetto da confermare con Luigi (D)

| ID | Decisione | Proposta |
|---|---|---|
| D-1 | Mappa dei pad del banco B e del PUSH (B8) | **Decisa il 13/10/2026**: pad = pulsanti funzione come in §8.5; il banco A fa gli 8 tasti accordo; PUSH anche sul tasto X della Flip. Con il macro pad (D-8) banco B e PUSH diventano una riserva |
| D-2 | Il tasto Stop della MPK come scorciatoia del looper (pressione = stop/pausa, tenuto 1 s = Clear) | **Deciso il 13/10/2026** (mappa scelta da Luigi) |
| D-3 | Tasti della Flip e modo tascabile | **Deciso il 13/10/2026**: schema a fuoco sempre attivo; modo tascabile opzionale, acceso dal menu (§9.1, §9.2). Resta da provare la disposizione del tascabile |
| D-4 | Ingresso dal DIN IN attivo per default, con il rischio di anello se un apparecchio esterno rimanda indietro i messaggi | Attivo; valutare un'opzione o un rilevamento dell'eco |
| D-5 | Clock verso la porta 1 della MPK attivo per default | Sì |
| D-6 | ID SysEx 7D con famiglia "ST" finché il progetto resta un prototipo | Sì |
| D-7 | Convenzione dei nomi delle note (Do centrale = C4) | Da allineare con `10` e `30` |
| D-8 | Macro pad BRIMFORD e nuova mappa dei controlli | **Decisa il 13/10/2026**: griglie gemelle K1–K8 / T1–T8 (K1 Sound … K8 Volume), M = Chord Voicing, m1 = Bass Voicing, m2 = liste; T9 Options, T10 Back, T11 Menu, T12 Panic tenuto (§8.10). Resta da provare con le mani, dopo VP-3 e VP-5 |

### Dati mancanti senza un test previsto
- Come la Plus capisce di essere collegata a un "computer" (enumerazione USB?) e quindi se la Flip conta come tale: lo dirà VM-2.
- Banda reale del DIN della MPK sotto carico (accordo di 5 note su tre flussi ≈ 11 messaggi ≈ 11 ms): da misurare con un loopback DIN insieme a VM-2.

---

## Dipendenze da altre sezioni

| Sezione | Cosa serve da lì | Cosa fornisce questa |
|---|---|---|
| `00-panoramica.md` | Architettura a strati (`core`, `dsp`, `gfx`, `platform/flip`), glossario | Lo strato di input logico e i moduli `midi_parse`, `midi_in`, `midi_out` |
| `10-accordi-e-performance.md` | Uso di `pnl_event_t` e dei gesti; logica mono della tastiera; Play Style; elenco ordinato delle 42 tonalità (CC 107); sottotipi della Perform (CC 103); macchina a stati del looper e del beat (trasporto, LED); significato di ogni gesto | Eventi del pannello, gesti, tempi di "tenere premuto", stato del trasporto MIDI |
| `20-suono.md` | Mappa dei 135 indici NRPN per Sound e Bass e dei 53 drum; BENDRANGE; risposta a CC 1, 64, 120, 121, 123; pool di 16 voci e furto di voce; rilascio rapido per il panic | Messaggi d'ingresso già decodificati |
| `30-interfaccia.md` | Resa di fuoco, overlay, avvisi (MPK occupata, programma non STAME, modo tascabile, macro pad senza mappa), menu Options > Audio and MIDI, menu di sistema (MENU) con Learn Pad, contrassegno «PAD», legende con i nomi del macro pad | Eventi `PNL_BACK`, `ENC_FOCUS`, `MACRO_SYSTEM_MENU`; stato del macro pad (MIDI-124, MIDI-127) |
| `50-piattaforma-flip.md` | Thread di input e di scrittura MIDI, apertura rawmidi, evdev (gamepad cercato per nome, PLT-053; macro pad in esclusiva con `EVIOCGRAB` e traduzione in `MPAD_*`), file `Saves/stame/pad.map`, conversione da campioni a tempo reale per clock e note, budget di latenza e jitter, porta OTG e hub senza PD (PLT-091) | Requisiti di temporizzazione (MIDI-032), code (MIDI-004), sequenza di avvio (§8.9), hot-plug (§11, MIDI-127), riconoscimento del macro pad (MIDI-124) |
| `90-questioni-aperte.md` | — | Le verifiche VO-1…15, VM-1…30, VP-1…8 e le decisioni D-1…8 |
