#!/bin/sh
# Stame: synth ad accordi per la Miyoo Flip (la vetrina della plancia con il synth vero).
# Sorgenti e specifica nel repo del progetto. Non cambia CPU, otg_mode, mixer o servizi (PLT-084).
APPDIR="$(cd "$(dirname "$0")" && pwd)"
SAVES=/mnt/SDCARD/Saves/stame
LOG=/mnt/SDCARD/Saves/spruce/stame.log
mkdir -p "$SAVES/preset" "$SAVES/loop" "$(dirname "$LOG")"
[ -f "$LOG" ] && [ "$(wc -c < "$LOG")" -gt 1048576 ] && mv "$LOG" "$LOG.1"
cd "$APPDIR" || exit 1
# periodo dell'audio in frame: 512 (10,7 ms); con crepitii provare 1024
export STAME_AUDIO_FRAMES="${STAME_AUDIO_FRAMES:-512}"
STAME_SAVES="$SAVES" exec ./stame >> "$LOG" 2>&1
