#!/bin/sh
# tools/deploy.sh — copia build/pacchetto/App/Stame sulla Flip e controlla gli MD5 (PLT-094).
#
#   sh tools/build.sh pacchetto && sh tools/deploy.sh
#
# Se Stame è aperta si ferma e lo dice: non si chiudono app e non si premono tasti da remoto
# mentre qualcuno usa la console. Il binario si scrive come stame.new e poi si rinomina.
# Non tocca mai otg_mode, il mixer, i servizi di spruce o la memoria interna.
cd "$(dirname "$0")/.." || exit 1
SSH="sh tools/flip-ssh.sh"
P=build/pacchetto/App/Stame
D=/mnt/SDCARD/App/Stame
[ -f "$P/stame" ] || { echo "manca $P: prima sh tools/build.sh pacchetto"; exit 1; }

if $SSH "pidof stame" > /dev/null 2>&1; then
    echo "Stame è aperta sulla Flip: chiudila dal MENU (Quit Stame) e rilancia il deploy."
    exit 2
fi

$SSH "mkdir -p '$D'" || exit 1
for f in "$P"/*; do
    n=$(basename "$f")
    if [ "$n" = stame ]; then
        $SSH "cat > '$D/stame.new' && chmod +x '$D/stame.new' && mv -f '$D/stame.new' '$D/stame'" < "$f" || exit 1
    else
        $SSH "cat > '$D/$n'" < "$f" || exit 1
    fi
done
$SSH "chmod +x '$D/launch.sh'; sync"

ok=1
for f in "$P"/*; do
    n=$(basename "$f")
    a=$(md5sum < "$f" | cut -c1-32)
    b=$($SSH "md5sum < '$D/$n'" | cut -c1-32)
    if [ "$a" = "$b" ]; then echo "ok    $n"; else echo "DIVERSO $n ($a / $b)"; ok=0; fi
done
[ "$ok" = 1 ] && echo "deploy: ok — sulla Flip in App > Musica > Stame" || { echo "deploy: MD5 diversi"; exit 1; }
