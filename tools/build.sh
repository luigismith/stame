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

case "${1:-}" in
    test)        do_test ;;
    portabilita) do_portabilita ;;
    ciao)        do_ciao ;;
    flip|pc|render|pacchetto) echo "target '$1' non ancora disponibile (fasi F2–F5)"; exit 2 ;;
    *) echo "uso: tools/build.sh test|portabilita|ciao|flip|pc|render|pacchetto"; exit 2 ;;
esac
