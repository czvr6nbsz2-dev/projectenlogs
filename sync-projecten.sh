#!/bin/bash
# Sync projecten/*.md van GitHub naar iCloud
# Draait bij opstarten via launchd

REPO="czvr6nbsz2-dev/projectenlogs"
BRANCH="main"
ICLOUD_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/projectenlog/projecten"
LOG="/tmp/projectenlog-sync.log"

echo "$(date '+%Y-%m-%d %H:%M:%S')  Sync gestart" >> "$LOG"

mkdir -p "$ICLOUD_DIR"

# Download alle .md bestanden via Python (voorkomt problemen met spaties)
curl -s "https://api.github.com/repos/$REPO/contents/projecten?ref=$BRANCH" \
  | python3 -c "
import sys, json, urllib.request, urllib.parse, os
icloud = os.path.expanduser('$ICLOUD_DIR')
for f in json.load(sys.stdin):
    name = f['name']
    if not name.endswith('.md'):
        continue
    encoded = urllib.parse.quote(name)
    url = 'https://raw.githubusercontent.com/$REPO/$BRANCH/projecten/' + encoded
    dest = os.path.join(icloud, name)
    urllib.request.urlretrieve(url, dest)
    print('Gesynct: ' + name)
" 2>&1 | while IFS= read -r line; do
  echo "$(date '+%Y-%m-%d %H:%M:%S')  $line" >> "$LOG"
done

echo "$(date '+%Y-%m-%d %H:%M:%S')  Sync klaar" >> "$LOG"
