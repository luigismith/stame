# Stame — specifica funzionale, versione per la Miyoo Flip

> Stato: **bozza 1**, 13/10/2026. Scritta dalle ricerche del second brain di Luigi, prima di qualunque riga di codice. Convenzioni (ID dei requisiti, etichette [M]/[O]/[D]/[V], dati privati) in [`CONVENZIONI.md`](CONVENZIONI.md).

## 1. Cos'è
Stame è un **clone fedele dell'Orchid (ORC—1)** di Telepathic Instruments: lo stesso comportamento musicale (accordi, Secret Chords, voicing a finestra, Key mode, basso, Play Style, Perform, beat, looper, MIDI) e lo stesso suono (motori VA, FM e Reed Piano, basso, effetti).

Il progetto procede in due fasi:
1. **Fase 1, questa specifica:** un'app nativa per la **Miyoo Flip**, suonata con la **Akai MPK mini Plus** collegata in USB.
2. **Fase 2:** uno strumento hardware dedicato, probabilmente Teensy 4.1 + Audio Shield, che riusa il nucleo senza modificarlo.

Il nome viene dal fiore: l'editor ufficiale dell'Orchid si chiama Pistil (pistillo), lo stame è l'altra metà.

## 2. Principi
1. **Fedeltà al comportamento e al suono dell'originale.** Le migliorie vanno in appendice, come opzioni spente per default.
2. **Lo schermo invece NON si clona** (decisione di Luigi del 13/10/2026). La Flip ha uno schermo 640×480 a colori, quindi mostra una **plancia nativa** con tutto ciò che serve o è utile vedere in tempo reale. Le 6 viste dell'OLED 128×128 restano specificate solo per l'hardware della fase 2.
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
                        (sez. 40 §10)              │  accordi, voicing, key,   VA/FM/RP,
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
Il dettaglio sta nella sez. 40 §8–§10 e nella sez. 30. Decisioni di Luigi del 13/10/2026:

| Controllo | Funzione |
|---|---|
| 37 tasti MPK | i 12 tasti dell'Orchid (classe di nota + velocity) |
| Pad banco A | gli **8 tasti accordo a sinistra dell'Orchid**, stessa disposizione: sopra Dim, Min, Maj, Sus; sotto 6, m7, M7, 9 |
| Pad banco B | pulsanti funzione: B1 Key, B2 Bass, B3 Perform, B4 Chord Voicing, B5 Loop, B6 BPM, B7 Options, B8 PUSH |
| K1–K8 | rotazione di Chord Voicing, Bass Voicing, Sound, Perform, FX, Key, BPM, Volume |
| PUSH (B8 **o tasto X della Flip**) + Kn | pressione della manopola Kn: premere, tenere, premere e ruotare |
| Rec / Play / Stop | Loop / BPM / stop o pausa del loop (tenuto 1 s = Clear); PUSH + Stop = Panic |
| « » e joystick | ruotano il controllo con il fuoco; joystick → conferma, ← indietro |
| Ruote e pedale | pitch bend, modulazione, sustain del Sound |
| Tasti Flip | **schema a fuoco**: L1/R1 spostano il fuoco, croce ruota, A preme, B indietro, X PUSH, Y modificatore Bass Voicing, SELECT Options, START BPM, MENU menu della piattaforma |
| MENU → Quit Stame | **unica** uscita dall'app |
| Modo tascabile | opzionale, da MENU: si suona con i soli tasti della Flip |

## 5. Indice della specifica

| File | Contenuto | Requisiti |
|---|---|---|
| [`10-accordi-e-performance.md`](10-accordi-e-performance.md) | input logici, 64 combinazioni di accordi, Secret Chords, naming, voicing a finestra, Key mode (42 tonalità), basso, Play Style, Strum/Slop/Arp/Pattern/Harp, clock a 96 PPQN, beat, looper, vettori di test | `ACC-` |
| [`20-suono.md`](20-suono.md) | architettura audio e pool di 16 voci, patch da 135 byte e `.inc` di Pistil, curve, motori VA/FM/Reed Piano, inviluppi, LFO, matrice, basso, effetti, macro, budget CPU, test | `SND-` |
| [`30-interfaccia.md`](30-interfaccia.md) | `ui_model_t`, plancia 640×480 della Flip, overlay e menu, gesti, menu della piattaforma; renderer OLED per la fase 2 | `UI-` |
| [`40-midi-e-controlli.md`](40-midi-e-controlli.md) | MIDI dell'Orchid replicato, clock e trasporto, identità e SysEx, MPK mini Plus e programma "STAME", tasti della Flip, strato di input logico, hot-plug e panic | `MIDI-` |
| [`50-piattaforma-flip.md`](50-piattaforma-flip.md) | hardware e sistema della Flip, moduli e API del nucleo, thread, audio, MIDI, input, video, persistenza, build, test, deploy, gotcha, portabilità verso Teensy, piano per fasi F0–F6 | `PLT-` |
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
| **Fuoco** | il controllo rotante del pannello a cui vanno « », joystick e croce della Flip |
| **PUSH** | B8 o X della Flip tenuto: la manopola della MPK toccata viene "premuta" |
| **Pistil** | editor ufficiale dei suoni dell'Orchid; Stame legge il suo formato `.inc` |
| **`ui_model_t`** | lo stato completo da mostrare, prodotto dal nucleo e disegnato dai renderer |
| **[M] [O] [D] [V]** | manuale, osservato, dedotto, da verificare su un Orchid vero |
