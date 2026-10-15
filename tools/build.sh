#!/bin/sh
# tools/build.sh — build di Stame (PLT-072). Script POSIX, gira nella Git Bash di Windows.
#
#   tools/build.sh test          compila ed esegue i test del nucleo sul PC
#   tools/build.sh portabilita   controlli di portabilità del nucleo (PLT-106, PLT-107)
#   tools/build.sh ciao          prova della toolchain aarch64 per la Flip (F0)
#   tools/build.sh flip|pc|render|pacchetto   (fasi successive)
#
# Variabili: ZIG (zig.exe), SDL_INCLUDE (header SDL2, solo per flip e pc).
set -eu
cd "$(dirname "$0")/.."

ZIG="${ZIG:-/d/dev/toolchain/zig-x86_64-windows-0.17.0/zig.exe}"
CFLAGS="-std=c11 -O2 -Wall -Wextra -Werror -Wdouble-promotion -Wvla -ffp-contract=off -fno-math-errno"
MODULI_PORTABILI="src/core src/dsp src/ui src/gfx src/ui_flip"
# PLT-001, più stdatomic.h per spsc.h (PLT-015)
HEADER_AMMESSI="stdint.h stdbool.h stddef.h string.h math.h float.h limits.h stdatomic.h"

# git non tiene le cartelle vuote: si guardano solo quelle che esistono
dir_portabili()      { for d in $MODULI_PORTABILI; do [ -d "$d" ] && echo "$d"; done; return 0; }
sorgenti_portabili() { find $(dir_portabili) -name '*.c' | sort; }
file_portabili()     { find $(dir_portabili) \( -name '*.c' -o -name '*.h' \) | sort; }

do_test() {
    mkdir -p build/pc
    # shellcheck disable=SC2046,SC2086
    "$ZIG" cc $CFLAGS -DSTAME_HOST -Isrc $(sorgenti_portabili) tests/unit/*.c -o build/pc/stame-test.exe
    ./build/pc/stame-test.exe
}

do_portabilita() {
    ok=1
    # PLT-106: nei moduli portabili solo gli header ammessi
    for f in $(file_portabili); do
        for h in $(sed -n 's/^[[:space:]]*#[[:space:]]*include[[:space:]]*<\([^>]*\)>.*/\1/p' "$f"); do
            case " $HEADER_AMMESSI " in
                *" $h "*) ;;
                *) echo "header vietato in $f: <$h>"; ok=0 ;;
            esac
        done
    done
    [ "$ok" = 1 ] || { echo "portabilita: FALLITA"; exit 1; }

    mkdir -p build/portabilita
    # PLT-002: compilazione senza STAME_HOST, quindi con i simboli avvelenati
    for f in $(file_portabili); do compila_portabile "$f" ""; done
    # PLT-107: compilazione di prova per Cortex-M7, freestanding, con gli header minimi di tests/shim
    for f in $(file_portabili); do
        compila_portabile "$f" ".m7" -target thumb-freestanding-eabihf -mcpu=cortex_m7 -Itests/shim
    done
    echo "portabilita: ok ($(file_portabili | wc -l | tr -d ' ') file)"
}

# Compila un file del nucleo: $1 = file, $2 = suffisso dell'oggetto, poi le opzioni extra.
# Un header (spsc.h è solo header) si compila incluso da un file di appoggio.
compila_portabile() {
    f="$1"; suf="$2"; shift 2
    case "$f" in
        *.c) src="$f" ;;
        *)   src="build/portabilita/$(basename "$f").c"; printf '#include "%s"\n' "$f" > "$src" ;;
    esac
    # shellcheck disable=SC2086
    "$ZIG" cc $CFLAGS -I. -Isrc "$@" -c "$src" -o "build/portabilita/$(basename "$f")$suf.o"
}

# F0: un «ciao» per la Flip, compilato con la toolchain di PLT-070 e i link di PLT-071
do_ciao() {
    mkdir -p build/flip
    # shellcheck disable=SC2086
    "$ZIG" cc $CFLAGS -target aarch64-linux-gnu.2.27 -mcpu=cortex_a55 tools/ciao.c \
        -o build/flip/ciao -lpthread -ldl -lm
    file build/flip/ciao
    echo "ciao: ok — da provare sulla Flip: scp build/flip/ciao root@<ip>:/tmp/ && ssh root@<ip> /tmp/ciao"
}

SDL_INCLUDE="${SDL_INCLUDE:-/d/dev/toolchain/sdl2/SDL2-2.32.10/include}"
VETRINA="src/platform/vetrina/vetrina.c src/platform/vetrina/patch_vetrina.c src/platform/vetrina/vetrina_dsp.c src/platform/vetrina/demo_song.c src/platform/vetrina/banco.c"

# render: stame-render per il PC, scrive i fotogrammi della plancia in PNG (PLT-076, solo immagini)
do_render() {
    mkdir -p build/pc
    # shellcheck disable=SC2046,SC2086
    "$ZIG" cc $CFLAGS -DSTAME_HOST -Isrc $(sorgenti_portabili) $VETRINA src/platform/offline/render.c \
        -o build/pc/stame-render.exe
    echo "render: ok — build/pc/stame-render.exe <cartella> [ms…] [--boot ms…] [--icona file.png]"
}

# flip: la vetrina per la Miyoo Flip (aarch64, SDL caricata con dlopen: niente link a SDL, PLT-071)
do_flip() {
    mkdir -p build/flip
    [ -f "$SDL_INCLUDE/SDL.h" ] || { echo "manca SDL.h in $SDL_INCLUDE (variabile SDL_INCLUDE)"; exit 1; }
    # shellcheck disable=SC2046,SC2086
    "$ZIG" cc $CFLAGS -DSTAME_HOST -target aarch64-linux-gnu.2.27 -mcpu=cortex_a55 -Isrc -I"$SDL_INCLUDE" \
        $(sorgenti_portabili) $VETRINA src/platform/flip/*.c -o build/flip/stame -lpthread -ldl -lm
    file build/flip/stame 2>/dev/null || ls -l build/flip/stame
}

# pacchetto: build/pacchetto/App/Stame, pronta per tools/deploy.sh (PLT-082, PLT-083)
do_pacchetto() {
    do_flip
    do_render
    P=build/pacchetto/App/Stame
    rm -rf build/pacchetto
    mkdir -p "$P"
    cp app/Stame/config.json app/Stame/launch.sh "$P/"
    cp build/flip/stame "$P/stame"
    cp assets/suoni/stame_avvio.wav "$P/stame_avvio.wav"
    # il banco dei campioni (20 §7b), se tools/campioni.py lo ha costruito
    if [ -f build/campioni/stame.smp ]; then cp build/campioni/stame.smp "$P/stame.smp"; else echo "attenzione: manca build/campioni/stame.smp (python -I tools/campioni.py)"; fi
    ./build/pc/stame-render.exe build/pacchetto --icona "$P/icon.png" > /dev/null
    cp third_party/spleen/LICENSE "$P/LICENSE-spleen"
    echo "pacchetto: ok — $P"
    ls -l "$P"
}

case "${1:-}" in
    test)        do_test ;;
    portabilita) do_portabilita ;;
    ciao)        do_ciao ;;
    render)      do_render ;;
    flip)        do_flip ;;
    pacchetto)   do_pacchetto ;;
    pc) echo "target 'pc' (simulatore con finestra) non ancora disponibile"; exit 2 ;;
    *) echo "uso: tools/build.sh test|portabilita|ciao|render|flip|pacchetto"; exit 2 ;;
esac
