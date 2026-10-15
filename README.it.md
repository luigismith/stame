<p align="center">
  <img src="docs/sito/img/icona_x4.png" alt="Il marchio di Stame: tre stami che salgono da un ricettacolo, le antere come teste di nota" width="140">
</p>

# Stame

**Un clone fedele e aperto dell'Orchid, il synth ad accordi, cresciuto su una console.**

*[English](README.md) · Italiano* · **Sito:** https://luigismith.github.io/stame/index.it.html

Tieni un tasto accordo, premi un tasto, ed esce un accordo con il suo voicing e il suo basso. L'[Orchid](https://telepathicinstruments.com/) di Telepathic Instruments fa questo, più strum, arpeggi, pattern, un beat e un looper. **Stame** fa lo stesso — tutto, dalle finestre del voicing ai Secret Chords — su una console **Miyoo Flip**, suonata con una **Akai MPK mini IV** e un **macro pad** a quindici tasti. E poi, avendo più tasti, più manopole e più CPU dell'originale, qualcosa in più.

Il nome viene dal fiore: l'editor dell'Orchid si chiama *Pistil*, lo stame è l'altra metà. Il resto dell'identità viene da una serra degli anni Settanta (*The Secret Life of Plants*, *Plantasia* di Mort Garson) e da Linneo, che classificò le piante contando gli stami. Una nota è uno stame: una triade è *Triandria*, e la schermata d'avvio lo dice.

> **Stato:** fase 1, *vetrina 0.1* che gira sulla Flip: suona, fa i loop, ha una demo. La fase 2 porterà lo stesso nucleo su hardware dedicato. Progetto indipendente, non affiliato a Telepathic Instruments; nel repository non c'è nessun dato di fabbrica dell'originale.

<p align="center">
  <img src="docs/sito/img/postazione.jpg" width="100%" alt="La postazione: la MPK mini IV a sinistra, il macro pad in linea con i tasti a destra, la Miyoo Flip aperta sopra il pad">
</p>
<p align="center">
  <img src="docs/sito/img/plancia_notte.png" width="32%" alt="Pagina di gioco, tema Notte">
  <img src="docs/sito/img/plancia_tocco.png" width="32%" alt="La banda mostra il controllo appena toccato">
  <img src="docs/sito/img/plancia_comandi.png" width="32%" alt="Pagina dei comandi">
  <img src="docs/sito/img/plancia_looper.png" width="32%" alt="Looper">
  <img src="docs/sito/img/plancia_giorno.png" width="32%" alt="Tema Giorno">
  <img src="docs/sito/img/plancia_geek.png" width="32%" alt="Vista Geek Out">
</p>

## Suonarlo, in tre righe

1. **Tieni un pad, premi un tasto.** Fila alta Dim, Min, Maj, Sus; fila bassa le estensioni 6, m7, M7, 9. Il tasto dà la fondamentale; la manopola grande del macro pad sposta la finestra del voicing.
2. **Gira una manopola, la banda risponde.** K1 Sound, K2 Perform, K3 FX, K4 Key, K5 Bass, K6 Loop, K7 BPM, K8 Volume; premi il tasto gemello sul pad (T1–T8) per «premerla». T13 è un Lock, come il Caps Lock: le tre manopole a scatti del pad diventano Sound, Perform e Key.
3. **REC, quattro battute, ⊕ per sovraincidere.** I pulsanti del trasporto della MPK sono il looper; STOP/PLAY accende il beat. T12 tenuto un secondo è il Panic, tre secondi il Reset.

Il [manuale](docs/manuale/manuale.md) e il [prontuario](docs/manuale/prontuario.md) di una pagina dicono tutto il resto.

## Cosa c'è dentro

- **Il suono.** Due motori (Sound e Bass) su sedici voci a 48 kHz, tre modelli di sintesi che seguono l'originale — VA, FM e un Reed Piano a modello fisico — più un'aggiunta di Stame, il **campionatore SMP**, che suona un banco di 88 MB di campioni CC0: pianoforti (Kawai a coda, due verticali, FM piano e Clavisynth del TX81Z), clavicembali, quattro registri d'organo a canne, flauti dolci dal soprano al basso, ocarina, armoniche, sax tenore e saxello, didgeridoo, arpa, strumstick, đàn tranh, salterio, tre lamellofoni, vibrafono, marimba, balafon, xilofono, glockenspiel, campane tubolari, campane a mano, bicchieri. Due slot di effetti per motore, delay, riverbero. Settantanove suoni (37 di sintesi, 42 campionati) e dodici bassi, progettati per Stame, nessun preset dell'originale.
- **Performance:** Strum, Strum 2 Octaves, Slop, Arpeggiate (1 e 2 ottave), Pattern, Harp, con il Lock. **Beat:** dodici pattern con tre kit a campioni (Studio, Jazz, 808) e un kit sintetizzato in stile CR-78. **Looper:** un loop di eventi, quattro battute con count-in, sovraincisione, pausa, undo, clear.
- **La plancia.** Una plancia «calma» a 640×480: accordo, tempo, tastiera e il controllo appena toccato; gli undici controlli e il dettaglio arrivano a richiesta. Sei viste, due temi (Notte, un VFD; Giorno, un LCD riflettente), un carattere a punti e cifre a sette segmenti disegnati per Stame. Vedi [docs/identita](docs/identita/README.md).
- **La demo.** Venti secondi senza ingressi e Stame suona a giro i suoi quattro brani originali («Acacia», «Felce», «Pistillo», «Alga»), mostrando ogni gesto sulla plancia: accordi, basso, loop e sovraincisioni, un loop di batteria suonato sui tasti, piano, vibrafono, kalimba, sax, organo e campane campionati, i due temi, un ritardando.
- **Il nucleo è portabile.** `src/core`, `src/dsp`, `src/ui`, `src/gfx` e `src/ui_flip` sono C11 puro: niente heap, niente I/O, niente SDL nel percorso audio. Tutto ciò che è specifico della piattaforma sta in `src/platform/`. Il controllo di portabilità compila il nucleo come codice freestanding per Cortex-M7, così la fase 2 resta onesta.

### Specificato, non ancora fatto

Salvataggio degli User Sound e caricamento di un banco di fabbrica privato; Waiting Room e lunghezza del loop, slot del loop, uscita morbida e forzata; batteria sui tasti e le altre combinazioni con Mod; MIDI in uscita sul DIN, clock e controllo esterno; Pocket Mode, Learn Pad, pagina di stato della MPK; il case (progettato, non tagliato); l'hardware della fase 2. La lista completa, requisito per requisito, è nella specifica.

## Compilare e installare

Servono: una Miyoo Flip con un firmware basato su spruceOS, una Akai MPK mini IV nel preset **DAW**, se si vuole il macro pad su un hub USB 2.0 semplice (senza Power Delivery) sulla porta USB-C di sopra della Flip. Sul PC: la Git Bash di Windows, [Zig](https://ziglang.org/) 0.17 (`zig cc` è il compilatore C, anche per aarch64), gli header di SDL2, Python 3 con `numpy` e `soundfile` per il banco dei campioni.

```sh
sh tools/build.sh test          # test unitari del nucleo sul PC
sh tools/build.sh portabilita   # header ammessi, simboli avvelenati, compilazione di prova Cortex-M7
sh tools/build.sh render        # renderer offline: fotogrammi PNG e WAV della demo
python -I tools/campioni.py     # scarica i campioni CC0 e costruisce build/campioni/stame.smp (una volta)
sh tools/build.sh pacchetto     # l'app per la Flip in build/pacchetto/App/Stame
sh tools/deploy.sh              # la copia via SSH (l'indirizzo della Flip in tools/flip.ip, fuori da git)
```

`test` e `portabilita` devono passare prima di ogni commit. Sulla Flip Stame compare in **App › Musica** (**App › Altro** su un menu senza aree). Senza il banco dei campioni i suoni campionati e i kit tacciono; tutto il resto suona.

## Documenti

| | |
|---|---|
| [docs/specifica](docs/specifica/00-panoramica.md) | la specifica funzionale, scritta prima del codice: accordi e performance, suono, interfaccia, MIDI e controlli, la piattaforma Flip, il case. Ogni requisito ha un ID e un'etichetta di fonte ([M] manuale, [O] osservato, [D] dedotto, [V] da verificare su un Orchid vero); le convenzioni in [CONVENZIONI.md](docs/specifica/CONVENZIONI.md) |
| [docs/manuale](docs/manuale/manuale.md) | il manuale d'uso e il [prontuario](docs/manuale/prontuario.md) |
| [docs/identita](docs/identita/README.md) | l'identità: storia, marchio, temi, caratteri, avvio, logo sonoro |
| [hardware/case](hardware/case/README.md) | il case, bozza 3: compensato di betulla, acrilico nero inciso, PETG; generato da `genera.py` ([specifica](docs/specifica/60-case.md)) |
| [docs/disegni](docs/disegni/README.md) | i disegni della plancia e dei controlli |

## Crediti e licenze

- Stame (codice, specifica, identità, case) è rilasciato con la [licenza MIT](LICENSE), © 2026 Luigi Massari.
- Il banco dei campioni usa solo campioni **CC0**: la [Versilian Community Sample Library](https://github.com/sgossner/VCSL) e i campioni di [Sonic Pi](https://github.com/sonic-pi-net/sonic-pi/tree/dev/etc/samples) da freesound.org. Ogni file è elencato in [assets/campioni/FONTI.md](assets/campioni/FONTI.md).
- Il font bitmap [Spleen](third_party/spleen/LICENSE), BSD 2-Clause, © Frederic Cambus.
- **Orchid** e **Pistil** sono nomi di Telepathic Instruments. Stame è un progetto indipendente, non affiliato a loro e non approvato da loro. Il repository non contiene dati di fabbrica dell'originale (niente preset, niente firmware, nessuna registrazione dei suoi suoni): il comportamento è descritto dal manuale pubblico e dall'ascolto, e ogni requisito dice da dove viene. Se hai un Orchid, le questioni segnate [V] nella specifica sono quelle a cui solo tu puoi rispondere.
