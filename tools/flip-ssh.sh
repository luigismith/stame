#!/bin/sh
# tools/flip-ssh.sh — esegue un comando sulla Miyoo Flip via SSH (PLT-093).
#
# L'indirizzo sta in tools/flip.ip (fuori da git: cambia da una rete all'altra). La password
# predefinita di spruce arriva da uno script askpass fuori dal repo (FLIP_ASKPASS, per default
# D:\dev\build\askpass.sh): qui non c'è nessuna password (PLT-074).
#
#   sh tools/flip-ssh.sh 'uname -a'
cd "$(dirname "$0")/.." || exit 1
IPFILE=tools/flip.ip
[ -f "$IPFILE" ] || { echo "manca tools/flip.ip con l'indirizzo della Flip (Impostazioni > Rete)"; exit 1; }
IP=$(head -1 "$IPFILE" | tr -d '\r\n ')
ASKPASS="${FLIP_ASKPASS:-/d/dev/build/askpass.sh}"
[ -x "$ASKPASS" ] || { echo "manca lo script askpass $ASKPASS (variabile FLIP_ASKPASS)"; exit 1; }
mkdir -p build
export SSH_ASKPASS="$ASKPASS" SSH_ASKPASS_REQUIRE=force DISPLAY=:0
# l'ssh della Git Bash: quello di Windows (che su alcuni PC viene prima nel PATH) non lancia un askpass .sh
SSHBIN=/usr/bin/ssh
[ -x "$SSHBIN" ] || SSHBIN=ssh
exec "$SSHBIN" -o UserKnownHostsFile=build/known_hosts_flip -o StrictHostKeyChecking=accept-new \
    -o PubkeyAuthentication=no -o ConnectTimeout=10 "spruce@$IP" "$@"
