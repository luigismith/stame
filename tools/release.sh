#!/bin/sh
# release.sh — il pacchetto di una release per la Flip.
#
# Uso: sh tools/release.sh 0.1.0
#
# Rifà il pacchetto (tools/build.sh pacchetto), ci scrive VERSION e la licenza, e lo chiude in
# build/release/Stame-<versione>.7z: dentro c'è App/Stame, da scompattare nella radice della SD
# (sulla Flip lo fa l'app «Stame» di Cirmolo, nell'area Musica, oppure a mano). Accanto scrive lo
# SHA-256 dell'archivio, che l'installatore controlla dopo lo scaricamento.
# 7-Zip: SEVENZ indica 7z.exe se non sta in C:\Program Files\7-Zip.
set -e
VER="$1"
case "$VER" in
    [0-9]*.[0-9]*.[0-9]*) ;;
    *) echo "uso: sh tools/release.sh <versione, per esempio 0.1.0>"; exit 2 ;;
esac
SEVENZ="${SEVENZ:-/c/Program Files/7-Zip/7z.exe}"
[ -x "$SEVENZ" ] || { echo "manca 7-Zip: $SEVENZ"; exit 1; }
[ -f build/campioni/stame.smp ] || { echo "manca il banco dei campioni: python -I tools/campioni.py"; exit 1; }

sh tools/build.sh pacchetto > /dev/null
P=build/pacchetto/App/Stame
printf '%s\n' "$VER" > "$P/VERSION"
cp LICENSE "$P/LICENSE"

mkdir -p build/release
OUT="build/release/Stame-$VER.7z"
rm -f "$OUT" "$OUT.sha256"
( cd build/pacchetto && "$SEVENZ" a -t7z -mx=7 "../release/Stame-$VER.7z" App/Stame > /dev/null )
sha256sum "$OUT" | cut -d' ' -f1 > "$OUT.sha256"
echo "release: ok — $OUT ($(wc -c < "$OUT") byte), sha256 $(cat "$OUT.sha256")"
