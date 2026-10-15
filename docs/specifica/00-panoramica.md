# Stame — specifica funzionale, versione per la Miyoo Flip

> Stato: **bozza 1**, 13/10/2026. Scritta dalle ricerche del second brain di Luigi, prima di qualunque riga di codice. Convenzioni (ID dei requisiti, etichette [M]/[O]/[D]/[V], dati privati) in [`CONVENZIONI.md`](CONVENZIONI.md).

## 1. Cos'è
Stame è un **clone fedele dell'Orchid (ORC—1)** di Telepathic Instruments: lo stesso comportamento musicale (accordi, Secret Chords, voicing a finestra, Key mode, basso, Play Style, Perform, beat, looper, MIDI) e lo stesso suono (motori VA, FM e Reed Piano, basso, effetti).

Il progetto procede in due fasi:
1. **Fase 1, questa specifica:** un'app nativa per la **Miyoo Flip**, suonata con la **Akai MPK mini Plus** collegata in USB, affiancata da un **macro pad BRIMFORD** (15 tasti e 3 manopole) che fa da pulsanti degli encoder.
2. **Fase 2:** uno strumento hardware dedicato, probabilmente Teensy 4.1 + Audio Shield, che riusa il nucleo senza modificarlo.

Il nome viene dal fiore: l'editor ufficiale dell'Orchid si chiama Pistil (pistillo), lo stame è l'altra metà.

## 2. Principi
1. **Fedeltà al comportamento e al suono dell'originale.** Le migliorie vanno in appendice, come opzioni spente per default.
2. **Lo schermo invece NON si clona** (decisione di Luigi del 13/10/2026). La Flip ha uno schermo 640×480 a colori, quindi mostra una **plancia nativa** con tutto ciò che serve o è utile vedere in tempo reale. Dal 15/10/2026 è una **plancia calma**: mentre si suona mostra accordo, tempo, tastiera e il controllo appena toccato; i comandi e il dettaglio arrivano quando servono (30, UI-140). Le 6 viste dell'OLED 128×128 restano specificate solo per l'hardware della fase 2.
3. **Nucleo portabile.** `core`, `dsp`, `ui`, `gfx` e `ui_flip` sono in C11 puro: niente heap, niente I/O, niente SDL o ALSA. La piattaforma passa la memoria come array statici.
4. **Separato da OpenOrc / Cirmolo:** niente codice né confronti in comune.
5. **Identità propria in MIDI:** mai l'ID SysEx `00 22 0C` né nomi di porta che inizino con "orchid".
6. **Dati privati fuori dal repo:** i preset di fabbrica 3.92 si caricano solo da `Saves/stame/privato/` sulla SD della Flip.

## 3. Architettura in una figura

```
  MPK mini Plus ──USB──┐                        ┌──> DIN OUT della MPK (porta 2)
  (porta 1: tasti,     │   platform/flip        │
   pad, manopole)      ▼                        │
  tasti Flip ─evdev─> [profili controller] ──> pnl_event_t ──> core ──> dsp ──> ALSA hw (48 kHz)
  macro pad ─evdev─┘    (sez. 40 §10)              │  accordi, voicing, key,   VA/FM/RP,
                                                   │  basso, play style,       basso, FX,
                                                   │  beat, looper, MIDI out   16 voci
                                                   ▼
                                              ui_model_t ──> ui_flip ──> framebuffer 640×480 ──> SDL2
                                                         └─> ui_oled (fase 2, OLED 128×128)
```

- **Thread** (sez. 50 §4): audio in tempo reale (unico proprietario dello stato del nucleo), MIDI in, MIDI out, UI. Comunicano con code SPSC lock-free e snapshot in triplo buffer.
- **Audio:** ALSA diretto su `hw`, 48 kHz, periodo di 256 frame, blocchi DSP da 16 campioni. Obiettivo di latenza tasto → suono: mediana sotto i 15 ms, 95° percentile sotto i 25 ms.
- **Build:** Zig (`zig cc`) per aarch64 Linux glibc 2.27 sulla Flip; sul PC test unitari, render audio offline e simulatore SDL.

## 4. Controlli in breve
Il dettaglio sta nella sez. 40 §8–§10 e nella sez. 30. Decisioni di Luigi del 13/10/2026; la mappa con il macro pad è del 13/10/2026 (sez. 40 §8.10). Il principio: le manopole K1–K8 della MPK e i tasti T1–T8 del macro pad sono **due griglie gemelle 4×2**, e Tn è il pulsante dell'encoder la cui manopola è Kn.

| Controllo | Funzione |
|---|---|
| 37 tasti MPK | i 12 tasti dell'Orchid (classe di nota + velocity) |
| Pad banco A | gli **8 tasti accordo a sinistra dell'Orchid**, stessa disposizione: sopra Dim, Min, Maj, Sus; sotto 6, m7, M7, 9 |
| K1–K8 | rotazione di **Sound, Perform, FX, Key** (fila alta) e **Bass, Loop, BPM, Volume** (fila bassa) |
| Macro pad T1–T8 | pulsanti degli stessi otto encoder, nella stessa posizione delle manopole; **Tn tenuto + Kn** = premere e ruotare (T4 + K4 = transpose) |
| Macro pad T9–T12 | Options, Back, menu della piattaforma, Panic (solo tenuto 1 s) |
| Macro pad M / m1 / m2 | manopola grande = Chord Voicing (pressione: Split ↔ Octave); piccola m1 = Bass Voicing (pressione: il modificatore); piccola m2 = liste e fuoco (pressione: conferma) |
| Rec / Play / Stop | Loop / BPM / stop o pausa del loop (tenuto 1 s = Clear); PUSH + Stop = Panic |
| « » e joystick | ruotano il controllo con il fuoco; joystick → conferma, ← indietro |
| Ruote e pedale | pitch bend, modulazione, sustain del Sound |
| Pad banco B | **riserva** senza macro pad: B1 Key, B2 Bass, B3 Perform, B4 Chord Voicing, B5 Loop, B6 BPM, B7 Options, B8 PUSH |
| PUSH (B8 **o tasto X della Flip**) + Kn | **riserva** senza macro pad: pressione della manopola Kn (premere, tenere, premere e ruotare) |
| Tasti Flip | **schema a fuoco**: L1/R1 spostano il fuoco, croce ruota, A preme, B indietro, X PUSH, Y modificatore Bass Voicing, SELECT Options, START BPM, MENU menu della piattaforma |
| MENU → Quit Stame | **unica** uscita dall'app |
| MENU → Learn Pad | solo se il macro pad non è stato programmato con i codici previsti (F13–F24 e tastierino numerico) |
| Modo tascabile | opzionale, da MENU: si suona con i soli tasti della Flip |

Il macro pad (BRIMFORD CusKeyboard0227) è una tastiera USB HID: Stame lo legge da evdev in esclusiva, solo via cavo, su un hub USB 2.0 senza Power Delivery insieme alla MPK. Il case che tiene insieme MPK, macro pad e Flip è in `60-case.md`.

## 5. Indice della specifica

| File | Contenuto | Requisiti |
|---|---|---|
| [`10-accordi-e-performance.md`](10-accordi-e-performance.md) | input logici, 64 combinazioni di accordi, Secret Chords, naming, voicing a finestra, Key mode (42 tonalità), basso, Play Style, Strum/Slop/Arp/Pattern/Harp, clock a 96 PPQN, beat, looper, vettori di test | `ACC-` |
| [`20-suono.md`](20-suono.md) | architettura audio e pool di 16 voci, patch da 135 byte e `.inc` di Pistil, curve, motori VA/FM/Reed Piano, inviluppi, LFO, matrice, basso, effetti, macro, budget CPU, test | `SND-` |
| [`30-interfaccia.md`](30-interfaccia.md) | `ui_model_t`, plancia 640×480 della Flip, overlay e menu, gesti, menu della piattaforma; renderer OLED per la fase 2 | `UI-` |
| [`40-midi-e-controlli.md`](40-midi-e-controlli.md) | MIDI dell'Orchid replicato, clock e trasporto, identità e SysEx, MPK mini Plus e programma "STAME", tasti della Flip, strato di input logico, hot-plug e panic | `MIDI-` |
| [`50-piattaforma-flip.md`](50-piattaforma-flip.md) | hardware e sistema della Flip, moduli e API del nucleo, thread, audio, MIDI, input, video, persistenza, build, test, deploy, gotcha, portabilità verso Teensy, piano per fasi F0–F6 | `PLT-` |
| [`60-case.md`](60-case.md) | case della fase 1 (bozza 2): telaio di betulla, mascherina della MPK, culla e visiera della Flip, vano del macro pad; pezzi generati da `hardware/case/genera.py` | `CASE-` |
| [`../identita/README.md`](../identita/README.md) | **identità**: la storia (lo stame, la serra degli anni Settanta, Linneo), il marchio dei tre stami, la plancia come vetrino a fluorescenza, caratteri, palette, case e logo sonoro | — |
| [`../disegni/stame-plancia-e-controlli.pdf`](../disegni/stame-plancia-e-controlli.pdf) | **disegni**: la plancia della Flip in cinque stati, MPK e Flip con la funzione di ogni comando, gesti, ricette d'uso, preparazione | — |
| [`90-questioni-aperte.md`](90-questioni-aperte.md) | tutte le verifiche (Orchid, MPK, Flip), i dati mancanti e le decisioni ancora da prendere | — |

## 6. Piano di sviluppo (sintesi della sez. 50 §16)
Ogni fase si chiude con l'ascolto di Luigi, non solo con le prove automatiche.

| Fase | Contenuto |
|---|---|
| F0 | repo e toolchain: struttura, `build.sh` (`test`, `portabilita`), code SPSC con test |
| F1 | nucleo sul PC: accordi, Secret Chords, nomi, voicing, Key mode, Play Style, parser MIDI e mappa MPK, con i test |
| F2 | primo suono offline: pool di voci, motore VA con il basso, `stame-render` su WAV, test golden |
| F3 | simulatore su PC: plancia, tastiera del PC e MPK collegata al PC |
| F4 | prima nota sulla Flip: verifiche di piattaforma, ALSA, rawmidi con la Plus |
| F5 | app sulla Flip: plancia, tasti, persistenza, deploy, hot-plug, sospensione, uscita |
| F6 | app completa: tutti i motori, effetti, preset, looper, MIDI out e clock, ottimizzazioni |

## 7. Glossario
| Termine | Significato |
|---|---|
| **Treble** | le note dell'accordo, distinte dal basso |
| **Voicing a finestra** | algoritmo dell'Orchid che piazza le note dell'accordo dentro una finestra di altezze scelta dal Chord Voicing Dial |
| **Secret Chords** | combinazioni di tasti accordo che danno accordi fuori tabella |
| **Key mode** | i tasti seguono una tonalità: l'accordo diatonico arriva senza premere i tasti tipo |
| **Play Style** | come i tasti accordo e la tastiera interagiscono (Simple, Advanced, Free) |
| **Perform** | modi di esecuzione: Strum, Slop, Arp, Pattern, Harp… |
| **Fuoco** | il controllo rotante del pannello a cui vanno m2 del macro pad, « », joystick e croce della Flip |
| **Macro pad** | il BRIMFORD CusKeyboard0227 (USB `1189:8840`): 15 tasti (T1–T12 i pulsanti e i comandi di sistema; T13 Lock delle manopole, T14 View, T15 Page: 40 MIDI-131, MIDI-132) e 3 manopole (M, m1, m2), profilo `pad_brimford` |
| **PUSH** | B8 o X della Flip tenuto: la manopola della MPK toccata viene "premuta"; riserva per quando il macro pad non c'è |
| **Pistil** | editor ufficiale dei suoni dell'Orchid; Stame legge il suo formato `.inc` |
| **`ui_model_t`** | lo stato completo da mostrare, prodotto dal nucleo e disegnato dai renderer |
| **[M] [O] [D] [V]** | manuale, osservato, dedotto, da verificare su un Orchid vero |
| **Vetrina** | pilota dimostrativo che mostra la plancia sulla Flip con il motore degli accordi vero e il resto simulato (sez. 50 §15.1) |
| **Matrice** | il font a punti 5×7 di Stame, per il nome dell'accordo e la scritta STAME |
| **Cartellino di Linneo** | la classe dell'accordo contata in stami: TRIANDRIA per tre note, TETRANDRIA per quattro; nella vista Geek Out (UI-161) |
| **Plancia calma** | la plancia della Flip dal 15/10/2026: quattro cose mentre si suona, i comandi e il dettaglio a richiesta (UI-140) |
| **Banda** | la riga in fondo alla plancia: il controllo appena toccato in grande, a riposo il suono (UI-154) |
| **Pagina dei comandi** | le 11 celle dei controlli al posto della tastiera, aperte dai tasti del fuoco della Flip e chiuse dopo 5 s, oppure aperte e tenute da T15 del macro pad (UI-142a) |
