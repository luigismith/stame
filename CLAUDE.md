# Stame

Strumento ad accordi che rifà fedelmente uno strumento esistente, «l'originale». Fase 1: app nativa per la **Miyoo Flip**, suonata con la **Akai MPK mini IV** (MK4, dal 15/10/2026; prima la Plus) e il macro pad BRIMFORD. Fase 2: hardware dedicato (probabilmente Teensy 4.1 + Audio Shield).

- Nota di progetto nel second brain: la nota di Stame in `10-Progetti/`.
- Specifica funzionale: `docs/specifica/`. Si parte da `00-panoramica.md`. Le convenzioni (ID dei requisiti, etichette [M]/[O]/[D]/[V]) sono in `CONVENZIONI.md`.

## Regole
- **L'originale nel repo non si nomina** (Luigi, 18/10/2026): codice, commenti, documenti, sito e commit dicono «l'originale» e descrivono il principio; il nome sta solo nelle note private.
- **Separato da Cirmolo e dagli altri progetti di Luigi:** niente codice, cartelle o confronti in comune.
- **La fedeltà all'originale è il minimo:** tutto quello che fa l'originale, Stame lo fa, e quel comportamento non si altera. Con più tasti, controlli e potenza Stame può fare di più: le aggiunte si implementano (Luigi, 15/10/2026), purché non tolgano niente all'originale e, se sono uno stato, si vedano sulla plancia (Lock, View e Page del macro pad sono le prime).
- **Nucleo portabile:** `core`, `dsp` e `gfx` in C11 puro, senza SDL, ALSA, malloc o lock nel percorso audio. Tutto ciò che è specifico della piattaforma sta in `platform/`.
- Stame **non** deve usare l'ID SysEx `00 22 0C`, che non è suo, né un nome di porta MIDI che inizi con il nome dell'originale (T-MIDI-15).
- I preset di fabbrica 3.92 sono dati privati: non vanno messi nel repo.
- **Miyoo Flip:** mai forzare la porta USB-C OTG in modalità host senza prima spiegare il rischio e chiedere l'ok.
- **MPK mini Plus:** niente SysEx sui programmi senza backup e senza l'ok di Luigi. Sulla MK4 la prova dei LED dei pad (CASE-033) si fa solo con Luigi presente, senza SysEx.

## Build e test
- Nella Git Bash: `sh tools/build.sh test` (compila ed esegue i test del nucleo), `sh tools/build.sh portabilita` (header ammessi, simboli avvelenati, compilazione di prova Cortex-M7), `sh tools/build.sh ciao` (ELF aarch64 di prova per la Flip). La variabile `ZIG` indica `zig.exe` se non sta in `D:\dev\toolchain\zig-x86_64-windows-0.17.0`.
- Plancia e vetrina: `sh tools/build.sh render` (PNG della plancia sul PC: `build/pc/stame-render.exe <cartella> <ms della demo>…`), `sh tools/build.sh pacchetto` (vetrina per la Flip in `build/pacchetto/App/Stame`), poi `sh tools/deploy.sh` (SSH; indirizzo in `tools/flip.ip`, fuori da git; `sh tools/deploy-attendi.sh [minuti]` aspetta che la Flip risponda e poi lo lancia). `stame --prova` sulla Flip misura il disegno senza toccare schermo e tasti.
- Fuori da git, su ogni PC: Zig e gli header di SDL2 2.32.10 (variabili `ZIG` e `SDL_INCLUDE`, di default in `D:\dev\toolchain`); Python con `numpy` e `soundfile` per `tools/campioni.py`, che scarica i campioni CC0 in `private/samples` (circa 830 MB) e scrive `build/campioni/stame.smp`; per il deploy `tools/flip.ip` e lo script askpass (`FLIP_ASKPASS`, di default `D:\dev\build\askpass.sh`). Senza banco `pacchetto` avvisa e `deploy.sh` lascia sulla Flip quello che c'è. Su una rete non propria, a fine lavoro l'SSH della Flip va rispento (PLT-096).
- Suoni, demo e manuale: `tools/patch.py` (patch, nomi, Perform di default, livelli `LIVELLO_DB`), `tools/demo.py` (scrive `src/platform/vetrina/demo_song.c`), `stame-render --suoni` (misura i livelli) e `--scene` (schermate di `docs/manuale/`); `python -I docs/disegni/sorgenti/hardware.py` rifà i disegni dei comandi (MPK, pad, Flip, postazione) di manuale e prontuario.
- Identità visiva e sonora: `docs/identita/README.md`. Case: `python -I hardware/case/genera.py` (pezzi in `hardware/case/out/`).
- `test` e `portabilita` devono passare prima di ogni commit. I test seguono i vettori della specifica (`TV-xx`) e citano i requisiti con il loro ID.
- Il nucleo (`src/core`, `dsp`, `ui`, `gfx`, `ui_flip`) include solo gli header di PLT-001 e compila anche senza `STAME_HOST`; i test e la piattaforma compilano con `-DSTAME_HOST`.
- Script e sorgenti con fine riga LF; gli script si scrivono con l'editor, non con heredoc (PLT-073).
