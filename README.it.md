<p align="center">
  <img src="docs/sito/img/icona_x4.png" alt="Il marchio di Stame: tre stami che salgono da un ricettacolo, le antere come teste di nota" width="140">
</p>

# Stame

**Uno strumento ad accordi, aperto, cresciuto su una console.**

*[English](README.md) · Italiano* · **Sito:** https://luigismith.github.io/stame/index.it.html

Tieni un tasto accordo, premi un tasto, ed esce un accordo intero, con il suo voicing e il suo basso. Una mano sceglie il tipo (Dim, Min, Maj, Sus) e le estensioni (6, m7, M7, 9), l'altra la fondamentale; le finestre del voicing spostano l'accordo in alto e in basso, le performance (strum, arpeggi, pattern, arpa) lo fanno muovere, un Beat e un looper a eventi fanno i loop mentre suoni. Tutto si suona, niente si programma a passi. **Stame** lo fa su una console **Miyoo Flip**, suonata con una **Akai MPK mini IV** e un **macro pad** a quindici tasti; e, avendo più tasti, più manopole e più CPU di uno strumento dedicato, fa qualcosa in più.

Il nome viene dal fiore: lo stame porta il polline, il pistillo lo riceve; Stame è la parte che dà. Il resto dell'identità viene da una serra degli anni Settanta (*The Secret Life of Plants*, *Plantasia* di Mort Garson) e da Linneo, che classificò le piante contando gli stami. Una nota è uno stame: una triade è *Triandria*, e la schermata d'avvio lo dice.

> **Stato:** fase 1, *vetrina 0.1* che gira sulla Flip: suona, fa i loop, ha una demo. La fase 2 porterà lo stesso nucleo su hardware dedicato. Progetto indipendente: nel repository non ci sono preset, firmware né suoni di altri strumenti.

<p align="center">
  <img src="docs/sito/img/plancia_giorno.png" width="32%" alt="Pagina di gioco, tema Giorno">
  <img src="docs/sito/img/plancia_tocco.png" width="32%" alt="La banda mostra il controllo appena toccato">
  <img src="docs/sito/img/plancia_comandi.png" width="32%" alt="Pagina dei comandi">
  <img src="docs/sito/img/plancia_looper.png" width="32%" alt="Looper">
  <img src="docs/sito/img/plancia_notte.png" width="32%" alt="Tema Notte">
  <img src="docs/sito/img/plancia_geek.png" width="32%" alt="Vista Geek Out">
</p>

## Suonarlo, in tre righe

1. **Tieni un pad, premi un tasto.** Fila alta Dim, Min, Maj, Sus; fila bassa le estensioni 6, m7, M7, 9. Il tasto dà la fondamentale; la manopola grande del macro pad sposta la finestra del voicing.
2. **Gira una manopola, la banda risponde.** K1 Sound, K2 Perform, K3 FX, K4 Key, K5 Bass, K6 Loop, K7 BPM, K8 Volume; premi il tasto gemello sul pad (T1–T8) per «premerla». tieni T13 per un drop: Beat, batteria del loop e basso tacciono e rientrano sul battito dopo.
3. **REC, quattro battute, ⊕ per sovraincidere.** I pulsanti del trasporto della MPK sono il looper; STOP/PLAY accende il beat. T12 tenuto un secondo è il Panic, tre secondi il Reset.

Il [manuale](docs/manuale/manuale.md) e il [prontuario](docs/manuale/prontuario.md) di una pagina dicono tutto il resto; sul sito sono anche pagine web: [manuale](https://luigismith.github.io/stame/manuale.html), [prontuario](https://luigismith.github.io/stame/prontuario.html).

## Cosa c'è dentro

- **Il suono.** Due motori (Sound e Bass) su sedici voci a 48 kHz, tre modelli di sintesi che seguono l'originale — VA, FM e un Reed Piano a modello fisico — più un'aggiunta di Stame, il **campionatore SMP**, che suona un banco di 94 MB di campioni CC0: pianoforti (Kawai a coda, due verticali, FM piano e Clavisynth del TX81Z), clavicembali, quattro registri d'organo a canne, flauti dolci dal soprano al basso, ocarina, armoniche, sax tenore e saxello, didgeridoo, arpa, strumstick, đàn tranh, salterio, tre lamellofoni, vibrafono, marimba, balafon, xilofono, glockenspiel, campane tubolari, campane a mano, bicchieri. Due slot di effetti per motore, delay, riverbero. Duecentotrentadue suoni (181 di sintesi, 51 campionati) e trentotto bassi, progettati per Stame, dai pad di vetro alle linee acid; dal 126 al 150 fanno ognuno una cosa che non ti aspetti, dal bordone che resta sotto ogni accordo al nastro che si ferma, e i cinquanta dal 151 al 200 sono tutti di sintesi, per genere: synthwave, lo-fi, house, ambient, chiptune, organi e piani elettrici, archi, ottoni, campane, stab techno, voci e pizzichi; dal 201 al 232 quelli per l'ambient, la trance e la psytrance (supersaw, trance gate, squelch, zap, una salita), con i bassi profondi e quelli corti, fatti per rotolare.
- **Performance:** Strum, Strum 2 Octaves, Slop, Arpeggiate (1 e 2 ottave), Pattern, Harp, con il Lock. **Beat:** sessantaquattro pattern e quarantatré kit: quattro a campioni (Studio, Jazz, 808, Techno), il Chip sintetizzato in stile CR-78 e una libreria di 38 kit sintetizzati che non chiedono campioni — drum machine analogiche, il pop e il gate degli anni Ottanta, tom elettronici, electro dei robot, minimal, dub, garage, jungle, industriale, glitch, sci-fi, lo-fi, chip, acustici e spazzole, percussioni del mondo (djembe, tabla, gamelan, latine, taiko, darbuka, cajón), trance e psytrance. E la batteria che si inventa: con DRUMS acceso le tre manopole del pad danno densità, uno di trentaquattro stili e variazione a un loop di due battute che cambia mentre suona; sotto DRUMS il basso può rotolare a sedicesimi, come nella psytrance. **Ambient:** T14 fa suonare Stame quasi da solo — accordi lenti nella tonalità, il basso sotto e note sparse su giri di lunghezze diverse, guidati dalle tre manopole del pad e da qualunque accordo suoni tu. **Looper:** un loop di eventi, quattro battute con count-in, sovraincisione, pausa, undo, clear.
- **La plancia.** Una plancia «calma» a 640×480: accordo, tempo, tastiera e il controllo appena toccato; gli undici controlli e il dettaglio arrivano a richiesta. Sei viste, due temi (Giorno, un LCD riflettente, il default; Notte, un VFD), un carattere a punti e cifre a sette segmenti disegnati per Stame. Vedi [docs/identita](docs/identita/README.md).
- **La demo.** Venti secondi senza ingressi e Stame suona a giro i suoi sei brani originali («Acacia», «Felce», «Pistillo», «Alga», «Cicuta», «Torba»), mostrando ogni gesto sulla plancia: accordi, basso, loop e sovraincisioni, un loop di batteria suonato sui tasti, piano, vibrafono, kalimba, sax, organo e campane campionati, i due temi, un ritardando.
- **Il nucleo è portabile.** `src/core`, `src/dsp`, `src/ui`, `src/gfx` e `src/ui_flip` sono C11 puro: niente heap, niente I/O, niente SDL nel percorso audio. Tutto ciò che è specifico della piattaforma sta in `src/platform/`. Il controllo di portabilità compila il nucleo come codice freestanding per Cortex-M7, così la fase 2 resta onesta.

### Specificato, non ancora fatto

Salvataggio degli User Sound e caricamento di un banco di fabbrica privato; Waiting Room e lunghezza del loop, slot del loop, uscita morbida e forzata; batteria sui tasti e le altre combinazioni con Mod; MIDI in uscita sul DIN, clock e controllo esterno; Pocket Mode, Learn Pad, pagina di stato della MPK; il case (progettato, non tagliato); l'hardware della fase 2. La lista completa, requisito per requisito, è nella specifica.

## Installare

Serve una **Miyoo Flip** con [Cirmolo](https://github.com/luigismith/cirmolo) o spruceOS, e la **MPK mini IV** nel preset **DAW** (il macro pad su un hub USB 2.0 semplice, senza Power Delivery, sulla porta USB-C di sopra).

- **Con Cirmolo:** App › Musica › **Installa Stame**, con il Wi-Fi acceso. Scarica l'ultima [release](https://github.com/luigismith/stame/releases), controlla l'archivio e mette Stame in Musica. Poi la voce si nasconde: quando esce una versione nuova, Cirmolo la rimostra all'avvio come **Aggiorna Stame** (con il Wi-Fi acceso).
- **A mano:** scarica `Stame-<versione>.7z` dalla [release](https://github.com/luigismith/stame/releases) e scompattalo nella radice della scheda SD: crea `App/Stame`. Con spruceOS Stame compare fra le app.

## Compilare e installare dai sorgenti

Servono: una Miyoo Flip con un firmware basato su spruceOS, una Akai MPK mini IV nel preset **DAW**, se si vuole il macro pad su un hub USB 2.0 semplice (senza Power Delivery) sulla porta USB-C di sopra della Flip. Sul PC: la Git Bash di Windows, [Zig](https://ziglang.org/) 0.17 (`zig cc` è il compilatore C, anche per aarch64), gli header di SDL2, Python 3 con `numpy` e `soundfile` per il banco dei campioni.

```sh
sh tools/build.sh test          # test unitari del nucleo sul PC
sh tools/build.sh portabilita   # header ammessi, simboli avvelenati, compilazione di prova Cortex-M7
sh tools/build.sh render        # renderer offline: fotogrammi PNG e WAV della demo
python -I tools/campioni.py     # scarica i campioni CC0 e costruisce build/campioni/stame.smp (una volta)
sh tools/build.sh pacchetto     # l'app per la Flip in build/pacchetto/App/Stame
sh tools/deploy.sh              # la copia via SSH (l'indirizzo della Flip in tools/flip.ip, fuori da git)
sh tools/release.sh 0.1.0       # l'archivio della release: build/release/Stame-0.1.0.7z e il suo SHA-256
```

`test` e `portabilita` devono passare prima di ogni commit. Sulla Flip Stame compare in **App › Musica** (**App › Altro** su un menu senza aree). Senza il banco dei campioni i suoni campionati tacciono e i quattro kit a campioni ricadono nel Chip sintetizzato; tutto il resto suona, i 35 kit sintetizzati compresi.

## Documenti

| | |
|---|---|
| [docs/specifica](docs/specifica/00-panoramica.md) | la specifica funzionale, scritta prima del codice: accordi e performance, suono, interfaccia, MIDI e controlli, la piattaforma Flip, il case. Ogni requisito ha un ID e un'etichetta di fonte ([M] manuale, [O] osservato, [D] dedotto, [V] da verificare sullo strumento); le convenzioni in [CONVENZIONI.md](docs/specifica/CONVENZIONI.md) |
| [docs/manuale](docs/manuale/manuale.md) | il manuale d'uso e il [prontuario](docs/manuale/prontuario.md) |
| [docs/identita](docs/identita/README.md) | l'identità: storia, marchio, temi, caratteri, avvio, logo sonoro |
| [hardware/case](hardware/case/README.md) | il case, bozza 5: compensato di betulla, un piano di acrilico nero inciso, PETG; generato da `genera.py` ([specifica](docs/specifica/60-case.md)) |
| [docs/disegni](docs/disegni/README.md) | i disegni della plancia e dei controlli |

## Crediti e licenze

- Stame (codice, specifica, identità, case) è rilasciato con la [licenza MIT](LICENSE), © 2026 Luigi Massari.
- Il banco dei campioni usa solo campioni **CC0**: la [Versilian Community Sample Library](https://github.com/sgossner/VCSL) e i campioni di [Sonic Pi](https://github.com/sonic-pi-net/sonic-pi/tree/dev/etc/samples) da freesound.org. Ogni file è elencato in [assets/campioni/FONTI.md](assets/campioni/FONTI.md).
- Il font bitmap [Spleen](third_party/spleen/LICENSE), BSD 2-Clause, © Frederic Cambus.
- Il repository non contiene dati di fabbrica di altri strumenti (niente preset, niente firmware, nessuna registrazione): il comportamento è descritto nella specifica, e ogni requisito dice da dove viene.
