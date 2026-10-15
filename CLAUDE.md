# Stame

Clone fedele dell'Orchid (ORC—1) di Telepathic Instruments. Fase 1: app nativa per la **Miyoo Flip**, suonata con la **Akai MPK mini Plus**. Fase 2: hardware dedicato (probabilmente Teensy 4.1 + Audio Shield).

- Nota di progetto nel second brain: `10-Progetti/Stame - clone fedele dell'Orchid.md`.
- Specifica funzionale: `docs/specifica/`. Si parte da `00-panoramica.md`. Le convenzioni (ID dei requisiti, etichette [M]/[O]/[D]/[V]) sono in `CONVENZIONI.md`.

## Regole
- **Separato da OpenOrc / Cirmolo:** niente codice, cartelle o confronti in comune.
- **La fedeltà all'originale è il minimo:** tutto quello che fa l'Orchid, Stame lo fa, e quel comportamento non si altera. Con più tasti, controlli e potenza Stame può fare di più: le aggiunte si implementano (Luigi, 15/10/2026), purché non tolgano niente all'originale e, se sono uno stato, si vedano sulla plancia (Lock, View e Page del macro pad sono le prime).
- **Nucleo portabile:** `core`, `dsp` e `gfx` in C11 puro, senza SDL, ALSA, malloc o lock nel percorso audio. Tutto ciò che è specifico della piattaforma sta in `platform/`.
- Il clone **non** deve usare l'ID SysEx `00 22 0C` né un nome di porta MIDI che inizi con "orchid".
- I preset di fabbrica 3.92 sono dati privati: non vanno messi nel repo.
- **Miyoo Flip:** mai forzare la porta USB-C OTG in modalità host senza prima spiegare il rischio e chiedere l'ok.
- **MPK mini Plus:** niente SysEx sui programmi senza backup e senza l'ok di Luigi.

## Build e test
- Nella Git Bash: `sh tools/build.sh test` (compila ed esegue i test del nucleo), `sh tools/build.sh portabilita` (header ammessi, simboli avvelenati, compilazione di prova Cortex-M7), `sh tools/build.sh ciao` (ELF aarch64 di prova per la Flip). La variabile `ZIG` indica `zig.exe` se non sta in `D:\dev\toolchain\zig-x86_64-windows-0.17.0`.
- Plancia e vetrina: `sh tools/build.sh render` (PNG della plancia sul PC: `build/pc/stame-render.exe <cartella> <ms della demo>…`), `sh tools/build.sh pacchetto` (vetrina per la Flip in `build/pacchetto/App/Stame`), poi `sh tools/deploy.sh` (SSH; indirizzo in `tools/flip.ip`, fuori da git). `stame --prova` sulla Flip misura il disegno senza toccare schermo e tasti.
- Identità visiva e sonora: `docs/identita/README.md`. Case: `python -I hardware/case/genera.py` (pezzi in `hardware/case/out/`).
- `test` e `portabilita` devono passare prima di ogni commit. I test seguono i vettori della specifica (`TV-xx`) e citano i requisiti con il loro ID.
- Il nucleo (`src/core`, `dsp`, `ui`, `gfx`, `ui_flip`) include solo gli header di PLT-001 e compila anche senza `STAME_HOST`; i test e la piattaforma compilano con `-DSTAME_HOST`.
- Script e sorgenti con fine riga LF; gli script si scrivono con l'editor, non con heredoc (PLT-073).
