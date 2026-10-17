# Stame — manuale d'uso

Bozza 1, 15/10/2026. Per chi suona, non per chi programma: la specifica sta in `docs/specifica/`, il prontuario da stampare in `prontuario.md`.

Stame è un clone fedele dell'Orchid di Telepathic Instruments: fa tutto quello che fa l'Orchid e, avendo più tasti, più manopole e più potenza, qualcosa in più. Nella fase 1 vive sulla **Miyoo Flip** (schermo e cervello) e si suona con la **Akai MPK mini IV** (tasti, pad e manopole) e un **macro pad** a 15 tasti e 3 manopole. Questo manuale descrive la **vetrina 0.1**, cioè quello che oggi gira sulla Flip; dove la specifica prevede di più, lo dice con un **«previsto»**.

## 1. La postazione

Come nella foto del 15/10/2026:

- **MPK mini IV a sinistra**, nel preset **DAW** (è di fabbrica, non va programmato). La sinistra sta sugli 8 pad, la destra sui tasti; le 8 manopole K1…K8 sono sopra i tasti, a destra; sotto le manopole, il trasporto (UNDO, LOOP, STOP/PLAY, REC, ⊕).
- **Macro pad a destra**, in linea con i tasti, con le manopole verso destra: le due piccole in alto (**m1** vicina ai tasti, **m2** sul bordo), la grande **M** in basso. Si usa solo via cavo, sullo strato di fabbrica 3 (o sull'1, reso uguale al 3).
- **Flip sopra il pad**, aperta, con lo schermo verso chi suona: è un display a portata di sguardo, fuori dalle mani. I suoi tasti funzionano sempre, qualunque cosa sia collegata: sono la console di gestione (§9.2).
- MPK e pad entrano in un **hub USB 2.0 semplice, senza Power Delivery**, sulla porta USB-C **di sopra** della Flip. Mai forzare la porta in modalità host dal sistema: Stame non lo fa e non va fatto a mano.

### 1.1 Le tre combinazioni

Stame si adatta a cosa è collegato (17/10/2026). La Flip c'è sempre, e i suoi tasti funzionano sempre.

| | MK4 + pad | solo MK4 | solo pad |
|---|---|---|---|
| fondamentali | tasti della MK4, con la velocity | tasti della MK4 | **T1…T12** del pad: Do…Si, velocity fissa |
| tipi ed estensioni | pad del banco A | pad del banco A | **M** il tipo, **m1** l'estensione: restano tenuti |
| gli 8 controlli | K1…K8; SHIFT + K per premere | K1…K8; SHIFT + K | il fuoco: L1/R1 della Flip, **m2** gira e preme |
| Chord Voicing | M | **nav** (il fuoco parte da lì) | il fuoco |
| Bass Voicing · Mod | m1 · m1 premuta | il fuoco · Y | il fuoco · m1 premuta |
| Options | T9 | SELECT | SELECT |
| Hold | T1 (o X) | **X** | **X** |
| Fill | T4 (o START) | **START** tenuto | — |
| Beat on/off | STOP/PLAY | STOP/PLAY | START |
| Tap, Scene | T2, T5…T8 | — | — |
| Metronomo, Save Loop | T3, T10 | MENU | MENU |
| Panic | T12 tenuto, SHIFT + STOP/PLAY | SHIFT + STOP/PLAY, MENU | MENU |
| batteria | pad del banco B, T11 | pad del banco B, Y + STOP/PLAY | m1 premuta + START |

Il cambio avviene quando attacchi o stacchi un apparecchio, appena le mani sono ferme.

## 2. Accendere e spegnere

![L'avvio: i tre stami si accendono sul vetrino](img/avvio.png)

1. Sulla Flip: **App › Musica › Stame**. Per 2,6 secondi il vetrino mostra i tre stami che si accendono, con il logo sonoro, e le righe dell'inizializzazione.
2. Se non tocchi niente, **parte la demo** (i brani «Acacia», «Felce» e «Pistillo», a giro). Un tasto, un pad o una nota la fermano e lo strumento è tuo.
3. Per uscire: **MENU › Quit Stame** (esce subito, senza conferma). Uscita di sicurezza: **MENU tenuto 2 secondi**. Accensione e spegnimento della Flip e il volume di sistema restano a spruceOS.

Lo stato della MPK e del pad si vede nella testata, in alto: a riposo c'è solo la batteria; «NO MPK» lampeggia finché la tastiera non c'è, salvo quando suoni con il solo pad (§7.1); «PAD» in rosso vuol dire che il macro pad non si apre o manda codici sconosciuti (§10).

## 3. Suonare un accordo

![La pagina di gioco: Do maggiore, con la forma d'onda dietro il nome, la tastiera con treble e basso, la banda a riposo](img/gioco.png)

- **Pad = tipo ed estensione.** Fila in alto, da sinistra: **Dim, Min, Maj, Sus**. Fila in basso: **6, m7, M7, 9**. Tieni un tipo e premi un tasto: suona l'accordo con quella fondamentale. Un'estensione aggiunge sempre lo stesso intervallo (il 6 non diventa 13; la 9 è la seconda, dentro la finestra). Dim + m7 dà il semidiminuito.
- **Tasti = fondamentale.** Conta solo il nome della nota: l'ottava del tasto e OCT−/OCT+ della MPK non cambiano nulla, perché il registro lo decide il **Chord Voicing**. La tastiera è monofonica: un tasto nuovo sostituisce il precedente. Un tasto senza tipo, con la Key mode spenta, suona una **nota singola**.
- **Chord Voicing (manopola grande M del pad).** Tutte le note dell'accordo cadono in una finestra di un'ottava che parte dalla nota d'inizio: girando in su la nota più bassa sale di un'ottava, in giù la più alta scende; dodici scatti = la stessa voicing un'ottava sopra. Il valore va da 1 a 60 (la banda mostra «VOICING 032 C♯3»). Mentre giri, se l'accordo sta suonando si riattacca.
- **Bass Voicing (m1).** L'ottava del basso, 0…48. Il basso è sempre la fondamentale.
- **Premere M: Split ↔ Octave** per le note singole. In **Octave** i 12 tasti suonano l'ottava che contiene la nota d'inizio; in **Split** la finestra vale anche per le note singole, e il punto di divisione si sposta con il voicing.
- **Key mode (K4 / SHIFT + K4).** Premere Key accende o spegne la tonalità: con la Key mode accesa un tasto senza tipo suona l'accordo del suo grado (Do in Fa♯ minore dà il suo accordo) e la testata della zona accordo scrive la tonalità. Girare Key sceglie la tonalità fra le 42 (e accende la Key mode se era spenta). **Premere e girare Key = Transpose**, ±12 semitoni, su tutta l'uscita, loop compreso. Previsto: Key tenuto + tasto per la scelta rapida (con Min tenuto per la minore).
- **Play Style (Options).** **Simple**: suona ciò che tieni. **Advanced**: l'accordo resta anche se lasci il tipo; le estensioni si aggiungono a quello che suona. **Free**: come Advanced, e l'accordo si può cambiare o riattaccare più volte con il tasto tenuto.
- **Secret Chords (Options):** combinazioni di più tipi tenuti insieme che danno accordi nascosti. Con la voce spenta vale l'ultimo tipo premuto.

## 4. I controlli, uno per uno

![La pagina dei comandi (T15): le 11 celle con valore, fuoco e sigla del comando; «S+K1» è SHIFT + K1](img/comandi.png)

![Il controllo appena toccato: girando FX la banda scrive REVERB 04 e la cella si accende](img/tocco.png)

![La lista dei suoni (SHIFT + K1): nome, motore e famiglia](img/lista_suoni.png)

L'Orchid ha nove encoder che si girano e si premono e due manopole di voicing. Su Stame ogni comando ha **una casa sola** (16/10/2026): il **girare** sta sulle manopole K1…K8 della MPK (senza scatti), il **premere** su **SHIFT + K** della stessa MPK (tieni SHIFT e tocchi la manopola: è «premuta»), le **liste** sulla manopola di navigazione con − (Back) e + (Menu) accanto. Il macro pad tiene Options (T9), i due voicing (M, m1) e le cose che l'Orchid non ha (§7). I gesti sono quattro:

| Gesto | Come si fa |
|---|---|
| **premi** | SHIFT + K toccata e lasciata (vale al rilascio di SHIFT, così si distingue dal premi-e-gira); T9 e M un tocco |
| **tieni** | SHIFT + K toccata, SHIFT tenuto 1 secondo; scatta alla soglia |
| **premi e gira** | SHIFT + K girata; oppure premi e giri una manopola del pad |
| **gira** | la manopola |

Dove stanno: K1 Sound, K2 Perform, K3 FX, K4 Key / K5 Bass, K6 Loop, K7 BPM, K8 Volume sulla MPK; T9 Options; M Chord Voicing; m1 Bass Voicing (vedi §7 per il Lock, che cambia il mestiere di M, m1, m2). Premere un controllo porta anche il **fuoco** su di lui: da lì la manopola di navigazione della MPK lo gira e lo preme.

| Controllo | Gira | Premi | Tieni 1 s | Premi e gira |
|---|---|---|---|---|
| **Sound** | i 97 suoni: 55 di sintesi (Glass Pollen, Night Greenhouse, Anther Keys, Slow Stamen, Fern Pluck, Copper Reed, Orbit Choir, Moss Strings, Dew Mallet, Tape Fern, Seed Organ, Sun Room, Linnaeus Lead, Petal Brass, Root Drone, Vetro Pad, Moonflower, Thistle Lead, Lichen Organ, Nectar EP, Ivy Pluck, Bramble Brass, Cocoon Pad, Spore Bells, Rootstock, Birch Keys, Pollen Choir, Reed Marsh, Clover Strings, Frost Pad, Cactus Pluck, Heliotrope, Underbrush, Dandelion, Sundew, Lotus Flute, Pine Organ e, cupi e techno, Nightshade, Belladonna, Mandrake Stab, Dub Moss, Acid Nettle, Hogweed Hoover, Cypress Saw, Mycelium, Puffball Pulse, Charred Keys, Charcoal Organ, Tar Drone, Wolfsbane Lead, Datura Bells, Bog Rumble, Blackthorn Sync, Ironwood Perc, Burdock Chords) e 42 campionati (Grand Piano, Upright Piano, FM Piano, Vibraphone, Marimba, Glockenspiel, Tubular Bells, Concert Harp, Kalimba, Harpsichord, Pipe Organ, Alto Recorder, Tenor Sax, TX Piano, Clavisynth, Knight Upright, Italian Cembalo, Lute Stop, Grand Organ, Flute Organ, Full Organ, Sop. Recorder, Tenor Recorder, Bass Recorder, Ocarina, Harmonica, Chromatic Harp, Saxello, Didgeridoo, Strumstick, Dan Tranh, Bowed Psaltery, Pluck Psaltery, Mbira, Nyunga Nyunga, Kenya Kalimba, Hand Chimes, Tube Glock, Bowed Vibes, Balafon, Xylophone, Wine Glasses); ogni suono porta il suo Perform | lista dei suoni per nome | previsto: Save / Save As / Delete | — |
| **Perform** | la quantità del modo: Strum, Strum 2 Oct, Slop e Harp 1…10; Arpeggiate e Arp 2 Oct il tipo 1…6; Pattern il numero 1…13; 0 = spento | lista dei modi | **Lock**: il Perform non cambia più al cambio di suono (la cella mostra LOCK) | — |
| **FX** | intensità 0…10 dell'effetto principale del suono (REVERB, CHORUS, ENSEMBLE, PHASER, FLANGER, DRIVE, TREMOLO, DELAY) | mostra l'effetto | **Lock** dell'effetto | — |
| **Key** | la tonalità (accende la Key mode) | Key mode on/off | previsto: scelta rapida | **Transpose** ±12 |
| **Bass** | i 18 bassi (Round Root, Sub Floor, Pluck Bass, Reed Bass, Velvet Sub, Wood Bass, Taproot, Peat Sub, Bark Bass, Pod Bass, Thorn Bass, Moss Sub, Reese Root, Acid Sedge, Henbane Sub, Fen Rumble, Spore Bass, Ironroot) | basso on/off | previsto: lista dei modi | — |
| **Loop** | con il loop in corso sceglie fra le tre voci in Z3 (OVERDUB, PAUSE, CLEAR o UNDO; STOP, PLAY…) | da fermo **REC** (con un loop messo da parte con T10, lo riprende); altrimenti esegue la voce scelta | previsto: 2 s = Save Loop / uscita morbida (oggi T10 del pad) | — |
| **BPM** | 60…200 (o il **tap tempo** su T2) | Beat o metronomo on/off (anche STOP/PLAY della MPK) | lista: **2/4, 3/4, 4/4, 6/8** (metronomo) e i 14 Beat **Funk, Bossa, Motorik, Lounge, Shuffle, Halftime, Boom Bap, Disco, Samba, Ballad, Train, Chip, Techno, Dub**, ognuno con il suo kit (studio, jazz, 808, techno; Chip è la sintesi) | **Beat Volume** 0…99 |
| **Volume** | volume master 0…99 | batteria della Flip | — | **Bass Volume** 0…99 |
| **Options** | cambia la vista (fuori dalla lista) | lista: Exit, View, Play Style, Single Notes, Secret Chords | — | — |
| **Chord Voicing** (M) | finestra ±1 semitono per scatto | Split ↔ Octave | — | — |
| **Bass Voicing** (m1) | ottava del basso | il modificatore **Mod**: Mod + Loop (REC) = uscita forzata dal loop (Clear); Mod + Bass = basso on/off, come Bass da solo; Mod + BPM = batteria a tastiera, che oggi ha il suo tasto T11 | — | — |

Liste: la voce in cima è Exit; la manopola di navigazione scorre, premuta sceglie, − chiude (senza MPK: croce, A e B della Flip). Una lista si chiude da sola dopo 10 secondi, e si chiude anche toccando un altro controllo. Ogni controllo toccato accende la **banda** in fondo allo schermo con il suo nome e valore in grande: è l'overlay dell'Orchid, che qui non copre l'accordo.

## 5. Il looper, passo per passo

![Il loop suona: PLAY, giro e battuta, le note del loop in viola sulla tastiera](img/looper.png)

Il looper registra **eventi** (note), non audio: cambiando BPM cambia la velocità del loop, cambiando suono cambia il suono del loop, il transpose vale anche per il loop.

1. **Registrare.** Premi **REC** della MPK (è il pulsante di Loop). Il metronomo conta **una battuta** («04» … «01» sulla banda) e poi registra **4 battute**; le note suonate un attimo prima del via entrano a tempo. Finite le 4 battute il loop suona da solo e il pannello in alto a destra mostra ▶ PLAY, la battuta («2/4») e il giro. Durante il count-in e la registrazione la cornice del pannello è rossa.
2. **Sovraincidere.** Con il loop che suona: Loop girato fino a OVERDUB e premuto, oppure **⊕** della MPK. Suona sopra: tutto quello che fai entra in un nuovo strato, giro dopo giro. Per chiudere lo strato: ancora ⊕ (o la voce STOP).
3. **Pausa e ripresa.** **LOOP** della MPK mette in pausa (le note si spengono); di nuovo LOOP riparte da capo, con il trasporto, così Beat e loop restano allineati.
4. **Undo.** **UNDO** della MPK, o la voce UNDO, toglie l'ultimo strato; con il solo primo strato diventa Clear.
5. **Cancellare.** La voce CLEAR, oppure **SHIFT + UNDO** sulla MPK: via tutto, il looper torna fermo.
6. **Mettere da parte.** **T10 Save Loop** del pad ferma il loop e lo tiene in memoria: REC lo riprende da capo invece di registrarne uno nuovo; CLEAR da fermo lo butta. Mod + REC (m1 premuta) è l'uscita forzata: cancella subito.
7. Previsti: Waiting Room con la scelta delle battute (Free, 1, 2, 4, 8, 16), salvataggio in 10 slot.

## 6. Beat e metronomo

![La lista di BPM tenuto: metriche del metronomo e i 14 Beat](img/lista_beat.png)

- **BPM premuto** (SHIFT + K7, oppure **STOP/PLAY** della MPK) accende e spegne il Beat scelto; con un metronomo scelto, accende il clic. Il trasporto riparte dalla battuta 1.
- **T3 METRO** del pad accende un metronomo indipendente dal Beat: clicca sui battiti anche sopra un Beat, e da solo mette in moto il trasporto. In testata «METRO».
- **T2 TAP**: batti il tempo sul tasto; dal secondo tocco il BPM segue la media degli ultimi quattro.
- **T4 FILL**: finché lo tieni il Beat suona la sua battuta di riempimento (rullate, tom), poi torna al pattern. In testata «FILL».
- **BPM tenuto** apre la lista: le quattro metriche (2/4, 3/4, 4/4, 6/8) scelgono il metronomo; sotto, i sei Beat. La spunta segna la scelta.
- **BPM premuto e girato** regola il volume del Beat.
- Con il looper in moto, spegnere il Beat lo zittisce soltanto: il tempo del loop continua.
- In alto a destra: i battiti della battuta come celle che si accendono, il BPM a sette segmenti.

### 6.1 Loop di batteria dalla tastiera

Lo stesso principio degli accordi, per la batteria: **T11 DRUMS** del pad (oppure Mod + BPM, come sull'Orchid) accende la **batteria a tastiera**. I 12 tasti suonano il kit del Beat scelto: Do cassa, Do♯ rimshot, Re rullante, Re♯ battimani, Mi charleston chiuso, Fa tom basso, Fa♯ charleston aperto, Sol tom alto, Sol♯ maracas, La conga, La♯ campanaccio, Si piatto. Se il looper registra o sovraincide, ogni colpo entra nel loop **quantizzato al sedicesimo**, come le note. Pad, basso e Perform restano fermi; un altro T11 torna agli accordi. Sulla plancia: «DRUMS» nella zona accordo e le sigle sui tasti C4…B4, che si accendono al colpo.

![Batteria a tastiera: DRUMS, le sigle degli strumenti sui tasti, i colpi registrati nel loop](img/drums.png)

### 6.2 La drum machine dal vivo

![La pagina dei comandi sotto DRUMS: le celle KIT, ROLL e ACCENT al posto di Sound, Perform e Bass](img/drums_comandi.png)

Stessa filosofia dell'Orchid: premi tasti, muovi manopole, il loop di batteria nasce mentre suoni. Niente da programmare a passi.

- **I pad del banco B** della MPK sono otto pad di batteria con la velocity, sempre, anche senza DRUMS: premi BANK e suoni la batteria sopra gli accordi del loop. Fila bassa cassa, rullante, rimshot, battimani; fila alta charleston chiuso e aperto, tom basso, piatto.
- Con **DRUMS acceso** tre manopole cambiano mestiere, e le celle lo scrivono:
  - **K1 KIT**: il kit (Beat = quello del Beat scelto, poi Studio, Jazz, 808, Techno, Chip);
  - **K2 ROLL**: tieni un tasto o un pad e il colpo si ripete a tempo: Off, 1/4, 1/8, 1/8T, 1/16, 1/16T, 1/32. Il primo colpo è il tuo, le ripetizioni entrano nel loop sulla griglia;
  - **K5 ACCENT**: quanto conta la forza del tocco, da 0 (colpi tutti uguali) a 10 (tutta la dinamica).
- Previsti: K4 Swing sulla griglia, K3 effetto sulla batteria.

## 7. Il macro pad

![Lock acceso (T13): la testata scrive LOCK SOUND PERFORM KEY e le celle dicono quale manopola fa cosa](img/lock.png)

Quindici tasti in tre file da cinque e tre manopole a scatti. Con una tastiera collegata (dal 16/10/2026) il pad non rifà i comandi della MPK: tiene Options, Panic, Lock, View, Page e i due voicing, e i tasti liberi fanno **quello che l'Orchid non ha**. Senza tastiera il pad è lo strumento (§7.1).

| | col. 1 | col. 2 | col. 3 | col. 4 | col. 5 |
|---|---|---|---|---|---|
| in alto | **T1** Hold | **T2** Tap tempo | **T3** Metronomo | **T4** Fill (tenuto) | **T13 LOCK** |
| in mezzo | **T5** Scene 1 | **T6** Scene 2 | **T7** Scene 3 | **T8** Scene 4 | **T14 VIEW** |
| in basso | **T9** Options | **T10** Save Loop | **T11** Drums | **T12** Panic (tenuto 1 s) | **T15 PAGE** |

- **T1 HOLD**: l'accordo resta a suonare anche quando lasci i tasti, finché non premi un tasto nuovo o non spegni il Hold. Serve per girare le manopole con tutte e due le mani. In testata «HOLD».
- **T2 TAP**, **T3 METRO**, **T4 FILL**: il tempo battuto, il metronomo indipendente dal Beat, la battuta di riempimento tenuta (§6).
- **T5…T8 SCENE 1…4**: un tocco richiama suono, basso, Perform, effetto, tonalità e basso acceso/spento; tenuto 1 secondo salva com'è adesso (la banda scrive «Scene 2 saved»). Una scena vuota lo dice. Le scene restano sulla SD (`Saves/stame/scene.txt`).
- **T9 OPTIONS**: la lista delle opzioni (premi), poi si scorre con la manopola di navigazione.
- **T10 SAVE LOOP**: ferma il loop e lo tiene da parte (§5).
- **T11 DRUMS**: la batteria a tastiera (§6.1).
- **T12 PANIC** scatta solo dopo 1 secondo: spegne tutte le note; tenuto 3 secondi fa il **Reset** (loop, Beat, transpose, Perform, Hold, metronomo da capo). Sulla MPK: **SHIFT + STOP/PLAY**.
- **T13 LOCK, a scatto come il Caps Lock.** Un tocco accende, un altro spegne; non si tiene. Le manopole della MPK non hanno scatti, quelle del pad sì: con il Lock acceso le tre manopole del pad diventano gli encoder che hanno bisogno degli scatti, con tutti i loro gesti.

| Manopola | Lock spento | Lock acceso |
|---|---|---|
| **M** (grande) | Chord Voicing · premi = Split/Octave | **Sound** · premi = lista · tieni = previsto Save |
| **m1** | Bass Voicing · premi = Mod | **Perform** · premi = lista dei modi · tieni = Lock del Perform |
| **m2** | volume del Beat · premi e gira = volume del basso | **Key** · premi = Key mode · premi e gira = Transpose |

  Finché è acceso la testata mostra **LOCK SOUND PERFORM KEY**; nella pagina dei comandi le celle dicono quale manopola fa cosa. Liste, fuoco e conferma stanno sulla manopola di navigazione della MPK. Se stacchi il pad, il Lock si spegne.
- **T14 VIEW**: Geek Out e, al tocco dopo, la vista di prima.
- **T15 PAGE**: apre la pagina dei comandi della Flip e la tiene aperta finché non lo ripremi (o premi −).
- Se il pad non c'è: Options è SELECT della Flip, Mod è Y, Hold è X, Fill è START tenuto; il fuoco parte da Chord Voicing, quindi la manopola di navigazione della MK4 gira i rivolti, e L1/R1 lo portano su Bass Voicing (§1.1).

### 7.1 Senza tastiera: il pad è lo strumento

![Il pad strumento: M su Min, m1 su m7, il Sol tenuto; la testata scrive MIN m7](img/pad_strumento.png)

Se colleghi solo il pad, il pad suona (17/10/2026). La mano sinistra sta sui tasti, la destra sulle manopole.

| | col. 1 | col. 2 | col. 3 | col. 4 | col. 5 |
|---|---|---|---|---|---|
| in alto | **Do** | **Do♯** | **Re** | **Re♯** | **T13 LOCK** |
| in mezzo | **Mi** | **Fa** | **Fa♯** | **Sol** | **T14 VIEW** |
| in basso | **Sol♯** | **La** | **La♯** | **Si** | **T15 PAGE** |

| Manopola | Gira | Premi |
|---|---|---|
| **M** (grande) | il **tipo d'accordo**: nessuno, Dim, Min, Maj, Sus | toglie tipo ed estensione: di nuovo l'accordo di Key |
| **m1** | l'**estensione**: nessuna, 6, m7, M7, 9 | Mod |
| **m2** | il controllo con il fuoco (lo scegli con L1/R1 della Flip) o la lista aperta | preme il controllo con il fuoco; premi e gira = premi e gira |

- Tipo ed estensione **restano tenuti** finché non li cambi: è come tenere premuti i tasti accordo dell'Orchid. La testata li scrive (per esempio **MIN m7**). Se giri M mentre una nota suona, l'accordo cambia sotto le dita.
- Con la **Key mode** accesa e nessun tipo, ogni fondamentale suona l'accordo della scala, come sull'Orchid: è il modo più semplice di suonare con il solo pad.
- **T13 LOCK** funziona come sempre: M, m1 e m2 diventano Sound, Perform e Key (Key premuta = Key mode).
- I tasti del pad non hanno velocity: suonano a 100.
- Dalla Flip: **X** = Hold, **START** = Beat on/off, SELECT = Options, Y = Mod, MENU = Panic, Metronome e Save Loop. La batteria a tastiera è **m1 premuta + START**: i dodici tasti suonano il kit.
- Quando il pad diventa lo strumento, la banda lo dice: «Pad plays notes». Se attacchi la MK4, il pad torna ai comandi appena lo lasci.

## 8. La MPK mini IV

| Comando | Fa |
|---|---|
| 25 tasti | i 12 tasti dell'Orchid (conta solo il nome della nota) |
| pad, banco A | Dim Min Maj Sus (sopra) · 6 m7 M7 9 (sotto) |
| pad, banco B | otto pad di batteria con la velocity (§6.2) |
| K1…K8 | girano Sound, Perform, FX, Key / Bass, Loop, BPM, Volume |
| SHIFT | **PUSH**: tenuto, la manopola K toccata è «premuta»; toccata e girata, premuta e girata; tenuto 1 s con la manopola toccata, tenuta |
| manopola di navigazione | gira = liste e fuoco; premi = conferma; premi e gira = premi-e-gira del controllo con il fuoco. È la casa della navigazione, con − e +. Senza pad il fuoco parte da Chord Voicing (§1.1) |
| − / + | Back / menu della piattaforma |
| UNDO | Undo del loop; **SHIFT + UNDO = Clear** |
| LOOP | pausa e ripresa del loop |
| STOP/PLAY | Beat on/off; **SHIFT + STOP/PLAY = Panic** |
| REC | Loop: registra, poi sovraincide |
| ⊕ | overdub: entra ed esce |
| ruote | pitch bend e modulazione del suono |
| pedale | sustain |
| BANK A/B, OCT−/+, ARP, LATCH, NOTE REPEAT, TAP, PLUGIN/DAW | interni della MPK: Stame li ignora. Attenzione: SHIFT insieme a un pad cambia i modi interni della MPK; se succede, torna al preset DAW |

## 9. La Flip

### 9.1 Lo schermo

![La vista Geek Out (T14): note, intervalli, finestre, Play Style, la barra completa in testata](img/geek.png)

![Lo stesso accordo nel tema Notte: vetro scuro e fosfori (MENU › Theme)](img/notte.png)

Il vetrino mostra, dall'alto: la **testata** (batteria; avvisi solo quando servono; LOCK), la **zona accordo** (tonalità e transpose, il nome dell'accordo in grande), la **zona tempo e loop** (BPM, battiti, il looper quando lavora), la **tastiera** a quattro ottave (treble in acqua, basso in ambra, loop in viola, i granelli della tonalità) e in fondo la **banda**, che mostra in grande il controllo appena toccato e, a riposo, il suono.

Due pagine:
- **pagina di gioco**: quello che serve mentre si suona;
- **pagina dei comandi**: al posto della tastiera, le 11 celle dei controlli con valore, fuoco e la sigla del comando. Si apre con i tasti del fuoco della Flip (L1, R1, croce, A, X) e si chiude da sola 5 secondi dopo l'ultimo, o con B; con **T15** del pad si apre e resta aperta.

Sei **viste** per la zona accordo (Options › View, o **T14**): **React**, **Chord** (quella di fabbrica), **Keyboard**, **Chord+Kb**, **Notes** (le note scritte), **Geek Out** (note, intervalli, finestre, cartellino di Linneo, attività MIDI, voci, carico, livelli: la barra completa in testata).

Due **temi** (MENU › Theme): **Giorno** (LCD riflettente, quello con cui Stame parte) e **Notte** (vetro scuro e fosfori). La demo parte nel tema che hai scelto e passa all'altro solo per mostrarlo.

### 9.2 I tasti

I tasti della Flip funzionano **sempre**, qualunque cosa sia collegata (17/10/2026): sono la console di gestione. Solo X e START cambiano compito secondo la tastiera.

| Tasto | Fa |
|---|---|
| L1 / R1 | sposta il fuoco fra gli 11 controlli (Sound, Perform, FX, Key, Bass, Loop, BPM, Volume, Options, Chord Voicing, Bass Voicing) e apre la pagina dei comandi |
| croce | gira il controllo con il fuoco, o scorre la lista aperta (con ripetizione se tenuta) |
| A | preme il controllo con il fuoco: conferma; tenuto = tieni; A tenuto + croce = premi e gira |
| B | indietro: chiude liste, overlay e pagina dei comandi |
| X | Hold; con la MPK mini Plus, il suo PUSH |
| Y | Bass Voicing premuto: il modificatore Mod |
| SELECT | Options |
| START | BPM: Beat on/off; con la MK4 (che ha STOP/PLAY), Fill finché lo tieni |
| MENU | il menu della piattaforma; tenuto 2 s esce da Stame |

### 9.3 Il menu della piattaforma (MENU, o + della MPK)

![Il menu della piattaforma](img/menu.png)

| Voce | Fa |
|---|---|
| Exit | chiude il menu |
| Panic | spegne tutte le note, subito |
| Metronome | On / Off: il metronomo indipendente dal Beat (come T3 del pad) |
| Save Loop | ferma il loop e lo tiene da parte; REC lo riprende (come T10 del pad) |
| Theme | Light (Giorno, il default) / Dark (Notte) |
| Linnaeus Tag | On / Off: il cartellino con la classe dell'accordo (TRIANDRIA, TETRANDRIA…) in Geek Out |
| Legend | On / Off: le sigle dei comandi nelle celle della pagina dei comandi |
| Meters | On / Off: voci, carico e livelli nella barra di Geek Out |
| Demo | Auto / Off: la demo dopo 20 secondi senza ingressi |
| Play Demo Song | il brano successivo della demo, subito |
| Quit Stame | esce (subito) |

Previsti: Pocket Mode (suonare con la sola Flip), MPK Status, Learn Pad, Note Labels, Beat Flash, Ghost Chord, Boot Sound, Debug.

## 10. La demo

Sono quattro brani originali di Stame, suonati a giro: **«Acacia»** (poco meno di quattro minuti: accordi in Harp, lista dei Beat, count-in e registrazione del loop, overdub, Lock del Perform, transpose, cambi di suono e di vista, i due temi, il ritardando), **«Felce»** (una bossa con piano a coda, vibrafono, kalimba in overdub, sax tenore, arpa e glockenspiel), **«Pistillo»** (apre con la batteria a tastiera: il kit 808 suonato sui tasti entra nel loop con count-in e sovraincisione, poi sopra FM piano e Sub Floor, marimba, organo a canne nel loop, flauto dolce, campane tubolari e transpose) e **«Alga»** (lento e sott'acqua: un pad, il giro nel loop con Moonflower e Peat Sub, campane a mano, glockenspiel in sovraincisione, ocarina, il Beat Ballad, bicchieri e ritardando). La demo parte da sola dopo 20 secondi senza ingressi (e subito dopo l'avvio). Qualunque tasto, pad o nota la ferma e rimette a posto loop, Beat, transpose e opzioni. Per non farla partire: MENU › Demo › Off. Per sentire il brano dopo: MENU › Play Demo Song.

## 11. Cosa fare se

| Vedi | Vuol dire | Fai |
|---|---|---|
| **NO MPK** lampeggia in testata | la tastiera non è collegata o non è riconosciuta | controlla cavo e hub (porta di sopra, hub senza Power Delivery); la MPK si riconosce dal nome «MPK mini IV» |
| **MPK FACTORY** | con la Plus: non è attivo il programma STAME | con la MPK mini IV non compare: basta il preset DAW |
| **PAD** in rosso | il macro pad non si apre in esclusiva, o manda codici che nessuna mappa conosce | ricollega il pad; usa lo strato 3 (o rendi l'1 uguale al 3). Previsto: MENU › Learn Pad |
| «Pad disconnected» | il pad si è staccato: i tasti tenuti si rilasciano, il Lock si spegne | ricollegalo |
| **CLIP** in testata | l'uscita satura | abbassa Volume, o il volume del basso o del Beat |
| **XRUN** | l'audio ha perso un periodo (crepitii) | in `launch.sh` porta `STAME_AUDIO_FRAMES` a 1024 |
| una nota resta appesa | — | Panic: T12 tenuto 1 s, oppure SHIFT + STOP/PLAY; se il Hold è acceso (HOLD in testata) spegnilo con T1 |
| Stame non risponde | — | MENU tenuto 2 s |

## 12. Glossario

- **Accordo a blocco**: tutte le note insieme, senza performance.
- **Banda**: la striscia in fondo allo schermo, che risponde al controllo toccato.
- **Beat**: una battuta di batteria in loop, scelta dalla lista di BPM.
- **Count-in**: la battuta di metronomo prima della registrazione.
- **Finestra**: l'ottava in cui cadono le note dell'accordo, decisa dal Chord Voicing.
- **Fill**: la battuta di riempimento del Beat, finché T4 è tenuto.
- **Fuoco**: il controllo su cui agisce la manopola di navigazione (e, senza MPK, croce e A della Flip); lo sposta la pressione di qualunque encoder.
- **Hold**: l'accordo resta a suonare dopo il rilascio (T1).
- **Key mode**: la tonalità accesa: i tasti suonano i gradi.
- **Lock (Perform, FX)**: il valore non cambia al cambio di suono.
- **LOCK (T13)**: le manopole del pad fanno Sound, Perform e Key.
- **Mod**: Bass Voicing premuto (m1 o Y), il modificatore delle combinazioni.
- **Overlay**: il nome e il valore del controllo toccato, nella banda.
- **Pad strumento**: il macro pad senza tastiera: T1…T12 sono le fondamentali, M e m1 tengono tipo ed estensione (§7.1).
- **PUSH**: SHIFT tenuto (B8 o X con la Plus): la manopola K toccata risulta premuta.
- **Scena**: suono, basso, Perform, effetto, tonalità e basso salvati su T5…T8.
- **Split / Octave**: come si distribuiscono le note singole sui 12 tasti.
- **Strato**: ogni passata di overdub nel loop.
- **Voicing**: la disposizione delle note nella finestra.
