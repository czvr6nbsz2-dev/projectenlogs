#!/bin/bash
# Nachtelijke taak: pull remote wijzigingen en sync naar iCloud
# Draait via launchd (com.arthur.projectenlog.plist)

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="/tmp/projectenlog.log"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S')  $*" >> "$LOG"; }

log "=== Nightly run gestart ==="

# 1. Pull laatste wijzigingen van GitHub (o.a. verwerkte audio)
cd "$REPO_DIR"
if git fetch origin main >> "$LOG" 2>&1 && git reset --hard origin/main >> "$LOG" 2>&1; then
  log "Git pull geslaagd"
else
  log "Git pull mislukt (geen netwerk?)"
fi

# 2. Sync projecten naar Apple Notities
if [ -f "$REPO_DIR/sync-notes.py" ]; then
  python3 "$REPO_DIR/sync-notes.py" >> "$LOG" 2>&1
  log "Apple Notities sync gedaan"
fi

log "=== Nightly run klaar ==="
