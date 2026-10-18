#!/bin/sh
# tools/deploy-attendi.sh — aspetta che la Flip risponda sulla porta 22 e poi fa il deploy, una volta.
#
#   sh tools/build.sh pacchetto && sh tools/deploy-attendi.sh [minuti]
#
# La Flip chiude SSH quando resta ferma e il Wi-Fi riparte con calma dopo la sveglia: invece di
# riprovare a mano, questo script prova ogni 20 secondi per i minuti dati (45 di default) e lancia
# tools/deploy.sh al primo tentativo che risponde. Esce con 3 se la Flip non ha risposto.
cd "$(dirname "$0")/.." || exit 1
[ -f build/pacchetto/App/Stame/stame ] || { echo "manca build/pacchetto: prima sh tools/build.sh pacchetto"; exit 1; }
MAX=$((${1:-45} * 60))
T=0
while [ "$T" -lt "$MAX" ]; do
    if timeout 8 sh tools/flip-ssh.sh "true" > /dev/null 2>&1; then
        echo "$(date +%H:%M:%S) la Flip risponde: deploy"
        exec sh tools/deploy.sh
    fi
    sleep 20
    T=$((T + 20))
done
echo "$(date +%H:%M:%S) la Flip non ha risposto in ${1:-45} minuti (Impostazioni > Rete: IP e Attiva SSH; Wi-Fi da spegnere e riaccendere)"
exit 3
