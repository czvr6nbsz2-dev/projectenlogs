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
if git pull origin main >> "$LOG" 2>&1; then
  log "Git pull geslaagd"
else
  log "Git pull mislukt (geen netwerk?)"
fi

# 2. Sync projecten naar iCloud
if [ -f "$REPO_DIR/sync-projecten.sh" ]; then
  bash "$REPO_DIR/sync-projecten.sh"
  log "iCloud sync gedaan"
fi

log "=== Nightly run klaar ==="
