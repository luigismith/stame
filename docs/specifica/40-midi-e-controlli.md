# 40 — MIDI e controlli

Questa sezione descrive come Stame **parla MIDI** e come **riceve i comandi** di chi suona:
- il MIDI in uscita e in ingresso dell'Orchid, replicato in modo fedele (canali, note, CC di stato, clock, trasporto, ingresso);
- i vincoli su identità, SysEx e nomi delle porte;
- la **Akai MPK mini Plus** come superficie di controllo, con il programma "STAME";
- i tasti fisici della **Miyoo Flip**, sia insieme alla MPK sia senza;
- lo **strato di input logico**, che separa i controller dal nucleo;
- hot-plug, disconnessione, note appese e panic.

Il comportamento musicale (accordi, Play Style, looper, beat) sta in `10-accordi-e-performance.md`. Qui si definisce solo **cosa entra e cosa esce** e in che forma.

**Etichette** (da `CONVENZIONI.md`)
- `[M]` manuale o documentazione ufficiale: per l'Orchid il manuale v4.1, il supporto Telepathic e le note di firmware; per la MPK la User Guide v1.2 e la knowledge base Akai.
- `[O]` osservato: per l'Orchid le catture MIDI e l'analisi statica del firmware 3.92 pubblicate da un utente (RSMR); per la MPK le catture di terzi (algo-synth #420), il codice dell'estensione Bitwig e le prove fatte sulla Flip.
- `[D]` dedotto o ricostruito: scelta di progetto o inferenza.
- `[V]` da verificare: è il valore di default scelto per ora. Il test è indicato come **VO-n** (da fare su un Orchid vero) o **VM-n** (da fare sulla MPK di Luigi collegata alla Flip; VM-n è il test n del §18 della guida alla Plus). Elenco completo in [Questioni aperte](#questioni-aperte).

---

## 1. Confini

| Dentro questa sezione | Fuori (sezione) |
|---|---|
| Formato e ordine dei messaggi MIDI, canali, clock, trasporto, SysEx, nomi | Quale accordo o quale nota suonare (`10`) |
| Mappa dei controlli MPK e Flip verso le funzioni dell'Orchid | Disegno di overlay, menu e messaggi a schermo (`30`) |
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
            │                                                      │ dell'ingresso Orchid)│
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
  4. il **riconoscitore dei gesti** del nucleo trasforma gli eventi del pannello nei gesti dell'Orchid (premere, ruotare, tenere, premere e ruotare: §10.3).
- **MIDI-002** — Il nucleo musicale (accordi, performance, looper, interfaccia) NON DEVE vedere byte MIDI né codici evdev dei controller: riceve solo `pnl_event_t`. L'unica eccezione è l'ingresso MIDI musicale (§5), che passa da `core/midi_in` con la semantica dell'Orchid [D].
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

## 3. MIDI in uscita (replica dell'Orchid)

### 3.1 Flussi e canali

- **MIDI-010** — Stame DEVE produrre tre flussi MIDI, come l'Orchid [M]:

| Flusso | Contenuto | Canale di default |
|---|---|---|
| **Performance** | Quello che suona davvero: arpeggi, strum, pattern, note singole, melodie fatte con il voicing | 1 [M] |
| **Bass** | Le note del basso | 2 [M] |
| **Chord** | L'accordo in blocco, **qualunque sia la performance** | **Off** [M, dal firmware 3.90] |

- **MIDI-011** — Ogni flusso DEVE poter andare su un canale da 1 a 16 oppure su **Off**, da Options > Audio and MIDI > MIDI Channels [M]. Le scelte DEVONO restare salvate allo spegnimento [D]. Due flussi POSSONO condividere un canale (§3.2, registro).
- **MIDI-012** — Tutte le destinazioni fisiche (§3.6) DEVONO ricevere gli stessi dati: sull'Orchid DIN e USB portano gli stessi messaggi [M].

### 3.2 Note On e Note Off

- **MIDI-013** — Formato [O]:
  - Note On `9n kk vv` con `vv` da 1 a 127;
  - Note Off **sempre** `8n kk 00`: Stame NON DEVE mai trasmettere un Note On con velocity 0 al posto del Note Off;
  - Stame NON DEVE usare il running status in uscita: ogni messaggio porta il suo status byte [D, le catture dell'Orchid mostrano sempre lo status].
- **MIDI-014** — Ordine dei messaggi nello stesso istante:
  - Note On: **Chord → Bass → Performance**. L'ordine Chord prima di Performance è osservato [O]; la posizione del Bass è scelta [V VO-8];
  - Note Off: **Performance → Bass → Chord**. Performance prima di Chord è osservato [O]; il Bass [V VO-8].
- **MIDI-015** — Quando una nota o un accordo ne sostituisce un altro, i Note Off delle note vecchie DEVONO precedere i Note On delle nuove, flusso per flusso [O].
- **MIDI-016** — **Registro delle note.** Stame DEVE tenere, per ogni destinazione, un contatore per coppia (canale, nota) [D]:
  - a ogni attacco trasmette il Note On e incrementa il contatore;
  - al rilascio decrementa; trasmette il Note Off **solo** quando il contatore torna a zero;
  - un Note Off con contatore già a zero NON DEVE essere trasmesso.

  Così due flussi sullo stesso canale non producono note spezzate, e non esce mai un Note Off doppio. L'Orchid 3.92 manda un secondo Note Off sul ch3 alla pressione successiva [O]; le note del 3.90 lo danno per corretto [M]. Stame segue l'intenzione dichiarata e **non** copia il difetto.
- **MIDI-017** — Stame PUÒ offrire un'opzione di debug "Doppio Note Off 3.92", spenta per default, che riproduce il difetto sul flusso Chord per i confronti con un Orchid vero (Appendice A).
- **MIDI-018** — Dalla tastiera le note singole sono **monofoniche** [M]: sul flusso Performance esce al massimo una nota singola alla volta. La logica (quale tasto vince) sta in `10`.
- **MIDI-019** — Il numero di nota trasmesso DEVE essere l'altezza effettivamente suonata dal motore, compreso l'effetto di voicing, Split/Octave e transpose. Dal 3.90 le ottave mostrate a schermo coincidono con quelle MIDI [M]; la convenzione scelta per Stame è Do centrale = nota 60 = "C4" [V VO-13].

### 3.3 Velocity

- **MIDI-020** — La velocity dei Note On DEVE venire dalla forza sul tasto (sulla MPK: la velocity del tasto, §8.5) [M]. Con Options > Instrument > Velocity Sense = Off DEVE essere un valore fisso: **100** [V VO-1]. I pattern scalano la loro velocity con quella del tasto e rispettano Sense Off [M]; il calcolo sta in `10`.

### 3.4 CC di stato

- **MIDI-021** — Stame DEVE trasmettere i CC di stato dell'Orchid [O]:

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

- **MIDI-023** — Come l'Orchid, Stame NON DEVE trasmettere [O]: Program Change, Pitch Bend, Aftertouch di canale e polifonico, CC 1, 7, 64 e qualunque CC musicale, Continue (`FB`), Song Position Pointer, MTC, Active Sensing, System Reset, Channel Mode (CC 120–127, salvo il panic del §7). In particolare pitch wheel, mod wheel e pedale della MPK agiscono sul suono interno ma **non** vengono inoltrati (l'inoltro è un'opzione dell'Appendice A).
- **MIDI-024** — Il looper registra eventi, non audio [M]. In riproduzione i suoi eventi DEVONO uscire sui tre flussi esattamente come se fossero suonati dal vivo [V VO-9; nel 3.92 il loop manda almeno le note del basso, O]. I beat di batteria e il metronomo NON DEVONO produrre MIDI [V VO-10].

### 3.6 Destinazioni fisiche sulla Flip

Sulla Flip la porta USB-C OTG fa da **host** per la MPK, quindi Stame non può presentarsi a un computer come dispositivo USB-MIDI [D]. L'equivalente dell'uscita DIN dell'Orchid è il **DIN OUT della MPK**, raggiunto attraverso la sua porta 2.

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

- **MIDI-030** — Stame DEVE trasmettere il **MIDI clock** (`F8`) a **24 PPQN**, **solo mentre il trasporto è in moto** [O]. Come l'Orchid dal 3.60, il clock esce e basta: in ingresso il clock NON DEVE avere effetto (il clock in è un'opzione dell'Appendice A) [M].
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

- **MIDI-037** — Clock e trasporto DEVONO uscire sul DIN (porta 2), come l'uscita DIN dell'Orchid [D: il manuale dice che DIN e USB portano gli stessi dati; V VO-11].
- **MIDI-038** — Clock e trasporto DOVREBBERO uscire anche sulla **porta 1** della MPK (opzione "Clock alla MPK", attiva per default) [D]. Con il clock della Plus su **External**, arpeggiatore, sequencer e **Clock Out analogico** seguono Stame [M UG p.7; V VM-5, VM-6].

---

## 5. MIDI in ingresso (replica dell'Orchid)

L'Orchid riceve MIDI solo via USB [M]. Sulla Flip l'equivalente è il **DIN IN della MPK**, che arriva sulla porta 2 [M UG p.7].

- **MIDI-040** — La porta 2 della MPK (DIN IN) DEVE essere trattata come l'ingresso MIDI dell'Orchid, con la semantica di questo paragrafo. È attiva per default [D: rischio di anello se il DIN OUT torna nel DIN IN attraverso un thru esterno, decisione D-4 nelle Questioni aperte].
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

- **MIDI-050** — Stame NON DEVE usare l'ID SysEx del produttore **`00 22 0C`** (Telepathic Instruments) [M tabella midi.org; O], né in uscita né come intestazione riconosciuta: i SysEx in ingresso con quell'ID DEVONO essere ignorati senza risposta.
- **MIDI-051** — Nessun nome esposto da Stame (porta ALSA, client del sequencer, sessione RTP-MIDI, nome Bluetooth, stringhe USB, nome di file di preset scambiati con altri) PUÒ cominciare con **"orchid"**, confrontando in minuscolo dopo aver tolto gli spazi iniziali. L'updater ufficiale prende le porte proprio con quel prefisso [M, JavaScript della pagina firmware]. Il nome da usare è **"Stame"** [D].
- **MIDI-052** — A un Identity Request (`F0 7E <7F o il proprio device ID> 06 01 F7`) ricevuto dall'ingresso MIDI (§5), Stame DEVE rispondere sul DIN con [D]:

```
F0 7E 7F 06 02  7D  53 54  01 00  <maj> <min> <patch> 00  F7
               id    fam.   memb.  versione (binaria, 7 bit per byte)
```

  - `7D` = ID per uso non commerciale, da usare nei prototipi [M midi.org]; un prodotto vero richiede un ID MMA proprio;
  - famiglia `53 54` ("ST"); membro `01 00` = versione per la Flip;
  - device ID della risposta `7F`, come l'Orchid [O].
- **MIDI-053** — Stame PUÒ implementare un SysEx proprio con la stessa struttura di quello dell'Orchid [D]:
  - trama `F0 7D 53 54 <cmd> <payload…> <cs> F7`;
  - checksum `cs = (−Σ byte da 7D all'ultimo byte di payload) & 0x7F`;
  - risposta `F0 7D 53 54 7E <cmd> <val> F7`, senza checksum.

  Comandi proposti: scelta di Sound e di Bass, voicing di accordo e di basso, scrittura di un parametro (motore, indice, valore), interrogazioni, dump completo e ripristino. Nessun comando può cancellare o scrivere la memoria permanente senza una conferma a schermo.
- **MIDI-054** — Stame NON DEVE cercare la compatibilità con Pistil né con l'updater ufficiale (trame "Tlp" `F0 54 6C 70 …`), che DEVONO essere ignorate [D].

---

## 7. Note appese, cambi di canale e panic

- **MIDI-060** — Se si cambia il canale di un flusso, o lo si mette su Off, mentre ci sono note accese, Stame DEVE mandare subito i Note Off di quelle note **sul canale vecchio** e azzerare le voci relative nel registro [D].
- **MIDI-061** — Nessun cambio di selettore (Sound, Perform, Key, Play Style, modalità del basso, basso on/off, voicing) può lasciare una nota senza Note Off. Il registro (MIDI-016) è la fonte di verità: ogni nota che il nucleo smette di suonare DEVE passare da un rilascio esplicito. Sull'Orchid 3.84 cambiare i selettori mentre si suona lascia note appese [O]: è un difetto e Stame NON DEVE copiarlo.
- **MIDI-062** — **Panic.** Comandi: PUSH + Stop sulla MPK (§8.5), voce "Panic" del menu di sistema (tasto MENU della Flip, §9), ricollegamento della MPK (§11). Effetto [D]:
  1. per ogni destinazione e ogni (canale, nota) con contatore > 0: Note Off `8n kk 00`; poi registro azzerato;
  2. CC 123 (All Notes Off) e CC 120 (All Sound Off) sui canali dei tre flussi e su quello della CV, se attivi;
  3. motori interni: tutte le voci in rilascio rapido (tempo in `20`), sustain spento, bend al centro.

  L'Orchid non trasmette mai CC 120 o 123 [O]: il panic è una deviazione voluta, solo su comando o al ricollegamento, mai nel funzionamento normale.
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
| Colori dei pad | Banco A: fila alta (tipi) e fila bassa (estensioni) di due colori diversi; banco B: un terzo colore, B8 (PUSH) di un quarto | Distinguere a colpo d'occhio tipi, estensioni e funzioni. Indici della palette 0–31 da scegliere sull'unità [V VM-12] |
| Aftertouch dei pad (PadAT) | **Off** | L'Orchid non ha pressione; meno traffico. Forse è un'impostazione globale [V VM-22] |
| Manopole K1–K8 | **Relative**, CC **70–77**, Lo 0, Hi 127; nomi "ChVoic", "BsVoic", "Sound", "Perform", "FX", "Key", "BPM", "Volume" | Encoder veri: lo stato resta in Stame e non ci sono salti. Se l'OLED mostri i nomi [V VM-16] |
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

### 8.5 Mappa controllo MPK → funzione dell'Orchid

- **MIDI-078** — Il profilo `mpk_stame` DEVE applicare questa mappa [D, sulla base della proposta della guida alla Plus §17.6; **decisa da Luigi il 13/10/2026**]:
  - i pad del **banco A** fanno gli **8 tasti accordo a sinistra dell'Orchid**, nella stessa disposizione: fila alta Dim, Min, Maj, Sus; fila bassa 6, m7, M7, 9. È la regola di Luigi: «se orchid ha 8 pulsanti a sinistra i pad di mpk devono funzionare come quegli otto pulsanti»;
  - i pad del **banco B** sono i **pulsanti funzione** (Key, Bass, Perform, Chord Voicing, Loop, BPM, Options e PUSH);
  - la **pressione delle manopole** si fa tenendo B8 (PUSH) **oppure il tasto X della Flip** (§8.6, decisione di Luigi del 13/10/2026).

| Controllo MPK | Messaggio | Evento del pannello (§10.1) | Funzione dell'Orchid |
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
| **K1** | CC 70 relativo | `PNL_ENC_TURN(ENC_CHORD_VOICING, n)` | Chord Voicing Dial |
| **K2** | CC 71 | `ENC_BASS_VOICING` | Bass Voicing Dial |
| **K3** | CC 72 | `ENC_SOUND` | Encoder Sound (uno scatto = un suono) |
| **K4** | CC 73 | `ENC_PERFORM` | Encoder Perform |
| **K5** | CC 74 | `ENC_FX` | Encoder FX |
| **K6** | CC 75 | `ENC_KEY` | Encoder Key |
| **K7** | CC 76 | `ENC_BPM` | Encoder BPM |
| **K8** | CC 77 | `ENC_VOLUME` | Encoder Volume |
| **Pad B8 o X della Flip tenuto + Kn** | ch10 nota 51 (o `PAD_X`) + CC 70–77 | `PNL_ENC_DOWN/UP` dell'encoder di Kn (§8.6) | Premere, tenere, premere e ruotare l'encoder di Kn |
| **Pad B1** | 44 | `PNL_ENC_DOWN/UP(ENC_KEY)` | Pulsante di Key: premere = Key mode on/off; tenere = quick select |
| **Pad B2** | 45 | `ENC_BASS` | Pulsante di Bass: premere = basso on/off; tenere 1 s = modalità |
| **Pad B3** | 46 | `ENC_PERFORM` | Pulsante di Perform: premere = lista dei modi; tenere = Lock |
| **Pad B4** | 47 | `ENC_CHORD_VOICING` | Pulsante del Chord Voicing: Split ↔ Octave |
| **Pad B5** | 48 | `ENC_LOOP` | Pulsante di Loop |
| **Pad B6** | 49 | `ENC_BPM` | Pulsante di BPM: beat o metronomo; tenere = tempo in chiave → Beats |
| **Pad B7** | 50 | `ENC_OPTIONS` | Pulsante di Options |
| **Rec** | CC 119 | `PNL_ENC_DOWN/UP(ENC_LOOP)` | Loop (doppione di B5, sempre a portata) |
| **Play** | CC 118 | `PNL_ENC_DOWN/UP(ENC_BPM)` | BPM: beat o metronomo (doppione di B6) |
| **Stop** | CC 117 | pressione: `MACRO_LOOP_STOP`; tenuto ≥ 1 s: `MACRO_LOOP_CLEAR` | Scorciatoie per le voci del menu Loop: Stop della registrazione o dell'overdub, Pause in riproduzione; Clear |
| **PUSH (B8) + Stop** | 51 + CC 117 | `MACRO_PANIC` | Panic (§7) |
| **«** / **»** | CC 115 / 116 | `PNL_ENC_TURN(ENC_FOCUS, −1/+1)` | Ruota l'encoder che ha il fuoco (§10.4): liste, Bass, Loop, Options |
| **Joystick su / giù** | CC 3 / CC 2 sopra soglia | `PNL_ENC_TURN(ENC_FOCUS, +1/−1)`, con ripetizione | Come « » |
| **Joystick destra** | CC 13 sopra soglia | `PNL_ENC_DOWN` + `PNL_ENC_UP(ENC_FOCUS)` | Conferma (pressione dell'encoder con il fuoco) |
| **Joystick sinistra** | CC 12 sopra soglia | `PNL_BACK` | Chiude l'overlay o risale di un livello nel menu |
| **Pitch wheel** | `E0` | `PNL_BEND` | Bend del Sound, come un Pitch Bend in ingresso sul ch1 (MIDI-042) |
| **Mod wheel** | CC 1 | `PNL_MOD` | Modulazione del Sound, come CC 1 in ingresso sul ch1 |
| **Pedale** | CC 64 | `PNL_SUSTAIN` | Sustain del Sound, come CC 64 in ingresso sul ch1 (il latch è un'opzione dell'Appendice A) |
| SHIFT, Arp, Chords, Scales, Bank, OCT, Home, Prog Select, Seq Play, Tap, encoder di menu | nulla | — | Non usabili: lavorano solo dentro la MPK |

Combinazioni dell'Orchid con il **Bass Voicing tenuto** [M]: si tiene B8, si tocca K2 (Bass Voicing premuto, §8.6) e si preme:
- B5 o Rec → **uscita hard dal loop**;
- B6 o Play → **batteria da suonare** ("On drums") [O];
- B2 → basso on/off.

Sulla Flip lo stesso modificatore è anche sul tasto Y (§9.1), più comodo.

Rispetto alla proposta della guida (§17.6) cambia una cosa: **B3** diventa il pulsante completo di Perform (premere = lista, tenere = Lock) invece del solo Lock.

- **MIDI-079** — Tastiera [D]:
  - la fondamentale è `kk % 12` (0 = Do); l'ottava fisica e l'ottava della MPK NON DEVONO influire, perché l'Orchid ha un'ottava sola e il registro lo decidono voicing e Split/Octave [M];
  - per ogni classe di nota il profilo DEVE contare i tasti fisici premuti: `PNL_KEY_DOWN` al primo, `PNL_KEY_UP` quando si rilascia l'ultimo. Un secondo tasto della stessa classe non produce eventi;
  - la velocity passa invariata [V VO-1, curva da confrontare con l'Orchid].
- **MIDI-080** — Pad del banco A: la velocity dei pad NON DEVE avere effetto, perché i tasti accordo dell'Orchid sono pulsanti in gomma senza velocity [M]; la dinamica dell'accordo viene dal tasto. L'aftertouch dei pad (`A9`, `D9`) DEVE essere ignorato [D].
- **MIDI-081** — Manopole [O/D]:
  - delta = `v < 64 ? v : v − 128` (complemento a due a 7 bit);
  - uno scatto ogni `step` unità accumulate: `step` = 2 per K1–K6, 1 per K7 (BPM) e K8 (Volume) [V VM-8];
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
  - cosa manda la MPK se si preme BANK con un pad tenuto (il Note Off ha la nota del banco vecchio o del nuovo?) va verificato [V VM-30]: se manda la nota del banco vecchio, la seconda regola diventa una semplice rete di sicurezza;
  - ogni funzione del banco B DEVE avere anche una strada che non richiede di cambiare banco: trasporto, PUSH (B8 o X della Flip) + manopola, oppure fuoco e tasti della Flip. Le funzioni da usare mentre si suona (looper, beat, pressione delle manopole) DEVONO stare su comandi sempre disponibili: REC, STOP, PLAY e X.

### 8.6 Gesti degli encoder sulla MPK: il pad PUSH

Le manopole della MPK non si premono. Il pad **B8** o il **tasto X della Flip** (decisione di Luigi: «per simulare la pressione delle manopole, dedica un tasto sulla flip») fa da "pressione" per l'encoder della manopola toccata subito dopo. B8 e X sono intercambiabili, e la stessa macchina a stati li tratta come un solo comando PUSH: è premuto se lo è almeno uno dei due.

- **MIDI-084** — Macchina a stati del PUSH [D, ricostruita dalla guida §17.6]. Qui "PUSH giù / su" vuol dire B8 Note On / Note Off oppure X premuto / rilasciato:

```
stati: IDLE, ARMED, TARGET(k)            k = manopola 0..7, enc[k] = encoder dell'Orchid
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
  - B8 + piccolo tocco a K6, rilascio di B8 → **premere Key** (Key mode on/off);
  - B8 + tocco a K6 + rotazione di K6 → **premere e ruotare Key** (transpose);
  - B8 + tocco a K3, B8 tenuto 1 s → **tenere Sound** (Save / Save As / Delete);
  - B8 + tocco a K8 → **premere Volume** (livello della batteria, qui quella della Flip).

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
- **MIDI-089** — Quando il profilo passa a "fabbrica", Stame DOVREBBE mostrare una volta l'avviso "Programma STAME non attivo: funzioni ridotte" (testo e resa in `30`) [D].

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

---

## 9. Tasti fisici della Flip

- **MIDI-090** — Stame DEVE leggere i tasti direttamente da evdev (`/dev/input/event5`) e NON DEVE usare insieme il gamepad di SDL, che legge lo stesso dispositivo con un'altra mappatura e lascia tasti "già premuti" [O]. Lo strato di piattaforma traduce i codici in un enum portabile con prefisso `PAD_*`. I nomi `BTN_*` sono vietati, perché collidono con le macro di `linux/input.h` [O].

| Tasto | Codice evdev [O] |
|---|---|
| A, B, X, Y | 305, 304, 308, 307 |
| L1, R1 | 310, 311 |
| L2, R2 | assi `ABS_Z`, `ABS_RZ` (0–255) |
| SELECT, START, MENU | 314, 315, 316 |
| L3, R3 | 317, 318 |
| Croce | `ABS_HAT0X`, `ABS_HAT0Y` |
| Levette | assi ABS 0/1 (sinistra) e 3/4 (destra), limiti letti con `EVIOCGABS` |

- **MIDI-091** — L2 e R2 contano come premuti sopra 128 e rilasciati sotto 64 [D]. Le levette hanno una zona morta pari al 50% della corsa [D].

### 9.1 Schema a fuoco (sempre attivo)

- **MIDI-092** — Profilo `flip_tasti`: i tasti della Flip DEVONO seguire lo **schema a fuoco** di `30-interfaccia.md` UI-132, sia con la MPK collegata sia senza [D; **deciso da Luigi il 13/10/2026**]. Il pannello ha un **fuoco** su uno degli 11 controlli rotanti, evidenziato a video:

| Tasto Flip | Evento | Funzione |
|---|---|---|
| L1 / R1 | `PNL_FOCUS_STEP(−1/+1)` | Sposta il fuoco, in giro ciclico: Sound, Perform, FX, Key, Bass, Loop, BPM, Volume, Options, Chord Voicing, Bass Voicing |
| Croce su / giù | `PNL_ENC_TURN(ENC_FOCUS, +1/−1)`, ripetizione come MIDI-082 | Ruota l'encoder con il fuoco, oppure scorre la lista aperta |
| Croce destra / sinistra | `PNL_ENC_TURN(ENC_FOCUS, +1/−1)`, con ripetizione | Come su / giù |
| A | `PNL_ENC_DOWN/UP(ENC_FOCUS)` | Pressione dell'encoder con il fuoco: conferma; tenere = tenere; A tenuto + croce = premere e ruotare |
| B | `PNL_BACK` | Indietro |
| **X** | **PUSH** (§8.6) | Tenuto: la manopola della MPK toccata o girata viene "premuta" (premere, tenere, premere e ruotare). Senza MPK non fa nulla |
| Y | `PNL_ENC_DOWN/UP(ENC_BASS_VOICING)` | Bass Voicing premuto: il modificatore delle combinazioni (Y + A con il fuoco su Loop = uscita hard dal loop) |
| SELECT | `PNL_ENC_DOWN/UP(ENC_OPTIONS)` | Pulsante di Options |
| START | `PNL_ENC_DOWN/UP(ENC_BPM)` | Pulsante di BPM (beat o metronomo) |
| MENU | `PNL_MACRO(MACRO_SYSTEM_MENU)` | Menu della piattaforma (`30` UI-129): Panic, Pocket Mode, Quit Stame… |
| L2, R2, L3, R3, levette | — | Liberi |

- **MIDI-095** — **Uscita dall'app:** l'unica strada DEVE essere MENU → «Quit Stame», oltre a `SIGTERM` (`50` PLT-086). Non c'è una combinazione di tasti riservata: SELECT e START servono già a Options e BPM [D].

### 9.2 Modo tascabile (opzionale)

Serve per suonare Stame anche senza la MPK, in viaggio. È più povero dell'originale: niente velocity, una sola fondamentale alla volta, scelta con la levetta. Però copre tutte le funzioni.

- **MIDI-093** — Stame DOVREBBE offrire un **modo tascabile**, una variante del profilo `flip_tasti` che sostituisce lo schema di §9.1 [D]:

| Comando | Evento | Funzione |
|---|---|---|
| Levetta sinistra | sceglie la classe di nota: 12 settori da 30°, Do in alto, in senso orario per semitoni; isteresi di 5° ai bordi | Nessun evento da sola |
| A | `PNL_KEY_DOWN(settore, 100)` alla pressione, `PNL_KEY_UP` al rilascio; se il settore cambia con A premuto: `KEY_UP` del vecchio e `KEY_DOWN` del nuovo | Tasto della tastiera (velocity fissa 100 [D]) |
| L2, L1, R1, R2 | `PNL_CHORD_DOWN/UP`: Dim, Min, Maj, Sus | Tasti tipo, nello stesso ordine da sinistra a destra dell'Orchid |
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

typedef enum {                      /* i controlli rotanti dell'Orchid */
    ENC_SOUND, ENC_PERFORM, ENC_FX, ENC_KEY, ENC_BASS, ENC_LOOP,
    ENC_BPM, ENC_VOLUME, ENC_OPTIONS, ENC_CHORD_VOICING, ENC_BASS_VOICING,
    ENC_COUNT,
    ENC_FOCUS = 0x40                /* pseudo-encoder: lo risolve il nucleo (MIDI-104) */
} enc_id_t;

typedef enum {                      /* gli 8 tasti accordo */
    CHB_DIM, CHB_MIN, CHB_MAJ, CHB_SUS, CHB_6, CHB_MIN7, CHB_MAJ7, CHB_9, CHB_COUNT
} chord_btn_t;

typedef enum {
    MACRO_LOOP_STOP, MACRO_LOOP_CLEAR, MACRO_PANIC, MACRO_SYSTEM_MENU
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

typedef enum { SRC_MPK, SRC_FLIP, SRC_COUNT } src_t;

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
typedef struct {
    const char *name;
    void (*reset)(void *st);
    /* messaggio MIDI completo -> 0..max eventi; ritorna quanti */
    int  (*on_midi)(void *st, uint8_t port, const uint8_t *m, uint16_t n,
                    uint32_t t_us, pnl_event_t *out, int max);
    /* tasto della console (PAD_*) o asse -> eventi */
    int  (*on_pad)(void *st, uint16_t pad_code, int32_t value,
                   uint32_t t_us, pnl_event_t *out, int max);
    /* chiamata ogni 10 ms: ripetizioni, soglie a tempo */
    int  (*on_tick)(void *st, uint32_t t_us, pnl_event_t *out, int max);
    /* sorgente persa: rilasci sintetici di tutto ciò che è premuto */
    int  (*on_lost)(void *st, uint32_t t_us, pnl_event_t *out, int max);
} ctl_profile_t;
```

- **MIDI-102** — Più sorgenti possono essere attive insieme (MPK e tasti della Flip). Il nucleo DEVE tenere lo stato di pressione **per sorgente**: un controllo risulta premuto se lo è in almeno una sorgente; `PNL_ENC_UP` o `PNL_CHORD_UP` di una sorgente non rilascia il controllo tenuto da un'altra [D].

### 10.2 Profili previsti

| Profilo | Sorgente | Uso |
|---|---|---|
| `mpk_stame` | MPK porta 1 | Programma STAME (§8.5); passa da solo a `mpk_fabbrica` (§8.8) |
| `mpk_fabbrica` | MPK porta 1 | Programma di fabbrica o sconosciuto, funzioni ridotte |
| `flip_tasti` | evdev | Schema a fuoco (§9.1) o modo tascabile, se acceso dal menu (§9.2) |

Un profilo generico per qualunque tastiera MIDI, con apprendimento dei controlli, è nell'Appendice A.

### 10.3 Riconoscimento dei gesti

Gli encoder dell'Orchid hanno quattro gesti [M]: **premere** (commuta), **ruotare** (valore), **tenere premuto** (menu o lock), **premere e ruotare** (funzione secondaria).

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
    DOWN, !ruotato -> G_PRESS(e)
    sempre         -> G_RELEASE(e); stato = IDLE
```

| Costante | Valore | Etichetta |
|---|---|---|
| `T_HOLD` per Bass e BPM | 1 s | [M] |
| `T_HOLD` per Key, Perform, FX, Sound, Loop, Volume, Options, Bass Voicing | 1 s | [V VO-12] |
| `T_HOLD2` per Loop (uscita morbida dopo 2 s) | 2 s | [M] |

  Il nucleo legge anche se un encoder è tenuto (`DOWN` o `HELD`) per le combinazioni: per esempio `G_PRESS(ENC_LOOP)` con `ENC_BASS_VOICING` tenuto = uscita hard dal loop [M]. Il significato di ogni gesto sta in `10` e `30`.

### 10.4 Il fuoco

- **MIDI-104** — `ENC_FOCUS` DEVE essere risolto dal nucleo, in questo ordine [D]:
  1. l'encoder che ha aperto la lista, il menu o l'overlay visibile (Options, menu Loop, lista dei suoni, dei modi, degli effetti, dei beat);
  2. altrimenti il **fuoco del pannello**: un solo valore, condiviso da tutte le sorgenti, che parte da Sound. Lo cambiano `PNL_FOCUS_STEP` e la pressione di un encoder da qualunque sorgente (`PNL_ENC_DOWN(e)` con `e` ≠ `ENC_FOCUS` porta il fuoco su `e`). Così « », il joystick della MPK e la croce della Flip ruotano Bass, Loop e Options subito dopo averne premuto il pulsante.

  Lo schermo DEVE mostrare quale encoder ha il fuoco (resa in `30`).

- **MIDI-105** — **Verso dei comandi verticali** [D, 13/10/2026]. Croce ▲▼ della Flip e joystick ▲▼ della MPK emettono `PNL_ENC_TURN(ENC_FOCUS | PNL_F_VERTICAL, ±1)` con su = +1. Il nucleo DEVE:
  - con una lista o un menu aperto, invertire il segno: su = voce precedente, cioè più in alto sullo schermo (`30` UI-157);
  - senza lista, usare il segno così com'è: su = valore più alto.
  Le rotazioni vere (manopole, « », croce ◀▶) non portano il flag e seguono sempre la regola orario = successiva (`30` UI-074).

### 10.5 Esempio: dal byte al gesto

```
MPK porta 1:  B0 48 01            (K3 relativo, +1)
midi_parse -> {port 0, B0 48 01}
mpk_stame  -> acc[K3] = 1 < step 2: nessun evento
MPK porta 1:  B0 48 01
mpk_stame  -> acc[K3] = 2 -> PNL_ENC_TURN(ENC_SOUND, +1)
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

---

## 12. Verifiche da fare sulla MPK (sintesi)

L'elenco completo dei 29 test è nelle [Questioni aperte](#questioni-aperte); comandi e procedure nel §18 della guida alla Plus. Prima di tutto: porta OTG mai forzata in host; **nessun SysEx di programma senza backup e senza l'ok di Luigi** (MIDI-077).

| Priorità | Test | Cosa decide |
|---|---|---|
| 1 — senza questi non si parte | VM-25 driver e riconoscimento; VM-1 consumo; VM-2 DIN come interfaccia; VM-26 hot-plug | MIDI-025, MIDI-070, MIDI-110…116 |
| 2 — taratura della mappa | VM-8 Relative e accelerazione; VM-9 e VM-29 joystick; VM-13 LED del trasporto; VM-15 pedale; VM-22 Trpt e PadAT globali; VM-27 latenza e traffico | MIDI-081…085 |
| 3 — clock e CV | VM-5 clock in ingresso alla MPK; VM-6 Clock Out; VM-4 sorgente della CV; VM-7 tracking della CV | MIDI-038, MIDI-086 |
| 4 — comodità | VM-12 LED dei pad; VM-16 nomi delle manopole; VM-11 Program Change; VM-23 cambio di programma; VM-20 nota più bassa; VM-28 velocity dei pad | MIDI-087, MIDI-089 |
| 5 — solo con l'ok di Luigi | VM-10 lettura SysEx; VM-21 backup dei programmi; VM-24 traffico dell'editor | MIDI-077 |

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
| T-MIDI-11 | MPK: B8 giù, K6 +1, B8 su entro 1 s | `G_PRESS(ENC_KEY)`; nessun cambio di tonalità |
| T-MIDI-12 | MPK: due Do (48 e 60) premuti, rilascio di 48 | Un solo `PNL_KEY_DOWN(0)`; `PNL_KEY_UP(0)` solo al rilascio di 60 |
| T-MIDI-13 | MPK scollegata con accordo tenuto, poi ricollegata | Rilasci sintetici, suono interno chiuso; al ricollegamento Note Off sul DIN e CC 123 + 120 |
| T-MIDI-14 | K3 in Absolute (programma di fabbrica), valore da 40 a 44 | Profilo in fabbrica; 2 scatti di Sound con `step` = 2 |
| T-MIDI-15 | Nomi esposti | Nessuno comincia con "orchid" (anche "Orchid", " ORCHID") |

---

## Appendice A — Migliorie opzionali (spente per default)

Per il principio di fedeltà queste opzioni esistono ma partono spente [D].

- **MIDI-200** — **Clock in**: opzione MIDI Clock = Out (default) / In. Con In il tempo segue gli `F8` del DIN IN (media su 24–48 tick); loop e beat seguono `FA`, `FB`, `FC` e SPP; lo spegnimento del clock in ripristina l'ultimo BPM interno.
- **MIDI-201** — **`FB` alla ripresa** dalla pausa del loop, mantenendo la posizione, al posto di `FA`.
- **MIDI-202** — **CC di stato come comandi** in ingresso (103, 107, 108, 112, 113): Key, BPM, Perform e volume dalla DAW. BPM sopra 127: CC 112 + CC 113 come MSB/LSB, oppure solo SysEx.
- **MIDI-203** — **Program Change** in ingresso per il Sound; **CC 7** per il volume master.
- **MIDI-204** — **Ingresso accordi**: le note di un canale scelto fanno da tastiera dell'Orchid (fondamentale + tasti accordo su note fisse), cosa che l'Orchid non fa.
- **MIDI-205** — **Inoltro** di pitch wheel e mod wheel della MPK sul canale Performance.
- **MIDI-206** — **Latch** con il pedale della MPK (l'Orchid non ha né latch né hold [O]).
- **MIDI-207** — **Zone della tastiera** della MPK: ottava più bassa = solo basso, resto = accordi.
- **MIDI-208** — **Altre uscite**: interfaccia USB-MIDI class compliant su hub; RTP-MIDI via Wi-Fi verso il computer; gadget USB `f_midi` se il kernel lo permette (senza MPK). Nome sempre "Stame".
- **MIDI-209** — **Doppio Note Off 3.92** sul flusso Chord, solo per i confronti (MIDI-017).
- **MIDI-210** — **Profilo generico** per qualunque tastiera MIDI, con apprendimento dei controlli.
- **MIDI-211** — **Caricamento di STAME via SysEx** all'avvio, solo alle condizioni di MIDI-077.

---

## Questioni aperte

### Da verificare su un Orchid vero (VO)

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

### Decisioni di progetto da confermare con Luigi (D)

| ID | Decisione | Proposta |
|---|---|---|
| D-1 | Mappa dei pad del banco B e del PUSH (B8) | **Decisa il 13/10/2026**: pad = pulsanti funzione come in §8.5; il banco A fa gli 8 tasti accordo; PUSH anche sul tasto X della Flip |
| D-2 | Il tasto Stop della MPK come scorciatoia del looper (pressione = stop/pausa, tenuto 1 s = Clear) | **Deciso il 13/10/2026** (mappa scelta da Luigi) |
| D-3 | Tasti della Flip e modo tascabile | **Deciso il 13/10/2026**: schema a fuoco sempre attivo; modo tascabile opzionale, acceso dal menu (§9.1, §9.2). Resta da provare la disposizione del tascabile |
| D-4 | Ingresso dal DIN IN attivo per default, con il rischio di anello se un apparecchio esterno rimanda indietro i messaggi | Attivo; valutare un'opzione o un rilevamento dell'eco |
| D-5 | Clock verso la porta 1 della MPK attivo per default | Sì |
| D-6 | ID SysEx 7D con famiglia "ST" finché il progetto resta un prototipo | Sì |
| D-7 | Convenzione dei nomi delle note (Do centrale = C4) | Da allineare con `10` e `30` |

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
| `30-interfaccia.md` | Resa di fuoco, overlay, avvisi (MPK occupata, programma non STAME, modo tascabile), menu Options > Audio and MIDI, menu di sistema (MENU) | Eventi `PNL_BACK`, `ENC_FOCUS`, `MACRO_SYSTEM_MENU` |
| `50-piattaforma-flip.md` | Thread di input e di scrittura MIDI, apertura rawmidi, evdev, conversione da campioni a tempo reale per clock e note, budget di latenza e jitter, porta OTG e hub | Requisiti di temporizzazione (MIDI-032), code (MIDI-004), sequenza di avvio (§8.9), hot-plug (§11) |
| `90-questioni-aperte.md` | — | Le verifiche VO-1…15, VM-1…29 e le decisioni D-1…7 |
