# Convenzioni della specifica di Stame

Stame è un clone fedele dell'Orchid (ORC—1) di Telepathic Instruments. Questa specifica descrive la **versione per la Miyoo Flip**, un'app nativa suonata con la **Akai MPK mini Plus**. L'hardware dedicato arriverà dopo. Qui conta solo una cosa: il nucleo deve restare portabile.

## Principi
1. **Prima la fedeltà all'originale.** Le migliorie (latch, clock in, più scale…) vanno solo in appendice, come opzioni spente per default.
2. **Nucleo portabile.** `core` (accordi, performance, looper, MIDI logico), `dsp` (sintesi, effetti) e `gfx` (framebuffer 1 bit 128×128) sono in C11 puro: niente SDL, niente ALSA, niente malloc nel percorso audio. Lo strato `platform/flip` fa da ponte verso SDL2, ALSA ed evdev.
3. **Separazione da OpenOrc.** Mai citare, confrontare o riusare OpenOrc / Cirmolo.

## Forma
- Italiano con tutti gli accenti. Termini tecnici e identificatori restano nella forma originale.
- Requisiti numerati con prefisso di sezione (`ACC-001`, `SND-001`, `UI-001`, `MIDI-001`, `PLT-001`) e verbi normativi: **DEVE**, **NON DEVE**, **DOVREBBE**, **PUÒ**.
- Tabelle e pseudocodice dove servono: lo scopo è poter scrivere codice e test direttamente dalla specifica.
- Ogni dato di comportamento porta un'etichetta di affidabilità:
  - `[M]` dal manuale o dalla documentazione ufficiale;
  - `[O]` osservato (video, firmware, utenti, Pistil);
  - `[D]` dedotto o ricostruito;
  - `[V]` **da verificare su un Orchid vero**: è il valore di default scelto per ora, con il riferimento al test.
- Ogni sezione chiude con **Questioni aperte** e **Dipendenze da altre sezioni**.

## Dati privati
I preset di fabbrica 3.92 sono dati privati: servono solo per studio e non vanno distribuiti. La specifica può descriverne il **formato** e citarne i nomi, ma NON DEVE copiare i valori dei parametri.

## File
| File | Contenuto |
|---|---|
| `00-panoramica.md` | scopo, architettura, glossario, indice |
| `10-accordi-e-performance.md` | motore degli accordi, voicing, key mode, basso, play style, pattern, beat, looper |
| `20-suono.md` | motori VA/FM/Reed Piano, basso, effetti, preset, voci |
| `30-interfaccia.md` | schermo 128×128, viste, overlay, gesti; resa sulla Flip |
| `40-midi-e-controlli.md` | MIDI in/out, clock, SysEx; MPK mini Plus e programma "STAME"; tasti della Flip |
| `50-piattaforma-flip.md` | app nativa, SDL2/ALSA/evdev, toolchain, budget di latenza e CPU, struttura del codice |
| `90-questioni-aperte.md` | verifiche da fare sull'Orchid e sulla MPK, dati mancanti |
