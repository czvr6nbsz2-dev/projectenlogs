# projectlog

Persoonlijk projectgeheugen dat audio- en tekstnotities verwerkt tot gestructureerde, chronologische projectlogboeken in Markdown.

## Vereisten

- Python >= 3.10
- macOS
- OpenAI API-key als environment variable: `export OPENAI_API_KEY=sk-...`
- Python-pakket: `pip install openai`

## Projectstructuur

```
projectenlog/
├── verwerk.py          # Hoofdscript (code — in git)
├── config.py           # Configuratie (code — in git)
├── .gitignore
├── README.md
├── input/
│   ├── inbox/          # Onverwerkte bestanden (data — niet in git)
│   └── processed/      # Archief per datum (data — niet in git)
│       └── 2026-01-30/
└── projecten/          # Logboeken per project (data — niet in git)
    ├── SWZ – Veemarkt.md
    └── _onbekend.md
```

## Gebruik

### Interactief (handmatig)

```bash
cd /pad/naar/projectenlog
python verwerk.py
```

Het script verwerkt alle bestanden in `input/inbox/`, vraagt bij onbekende projecten om toewijzing, en biedt zoektermen aan.

### Batchmodus (automatisch, non-interactive)

```bash
python verwerk.py --batch
```

Geen user input nodig. Onbekende entries worden opgeslagen in `_onbekend.md`. Geschikt voor cron/launchd.

## Mobiele opname

De workflow is ontworpen voor snel opnemen onderweg:

1. **iPhone Shortcut** start audio-opname bij aanroep
2. Sla op als `.m4a` met datum+tijd in bestandsnaam, bijv. `2026-01-30_09-14.m4a`
3. Bestand komt via **iCloud Drive** terecht in `input/inbox/`

Het script herkent de datum en tijd uit de bestandsnaam en vermeldt het tijdstip bij de logboek-entry.

## Nachtelijke verwerking

### Optie 1: cron

```bash
crontab -e
```

Voeg toe:

```
0 0 * * * cd /pad/naar/projectenlog && /usr/local/bin/python3 verwerk.py --batch >> /tmp/projectlog.log 2>&1
```

### Optie 2: launchd (aanbevolen op macOS)

Maak `~/Library/LaunchAgents/com.user.projectlog.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.projectlog</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/pad/naar/projectenlog/verwerk.py</string>
        <string>--batch</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/pad/naar/projectenlog</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>OPENAI_API_KEY</key>
        <string>sk-...</string>
    </dict>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>0</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/projectlog.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/projectlog.log</string>
</dict>
</plist>
```

Activeer:

```bash
launchctl load ~/Library/LaunchAgents/com.user.projectlog.plist
```

## Meerdere opnames per dag

Alle bestanden van dezelfde kalenderdag worden samengevoegd in één datumsectie per projectlogboek:

```markdown
## 2026-01-30

Besluiten / afspraken:
- besluit A (memo 09:14)
- afspraak B (memo 16:40)

Signalen / aandachtspunten:
- signaal X
```

De datum wordt afgeleid uit de bestandsnaam (`YYYY-MM-DD`), of bij afwezigheid uit de file modified time.

## Archivering

Verwerkte bestanden worden niet verwijderd maar verplaatst naar:

```
input/processed/YYYY-MM-DD/
```

## GitHub-werkwijze

GitHub is source of truth voor **code**, niet voor data.

**In git (commitbaar):**
- `verwerk.py`
- `config.py`
- `README.md`
- `.gitignore`

**Niet in git (lokale data):**
- `input/inbox/*` — onverwerkte bestanden
- `input/processed/*` — archief
- `projecten/*.md` — logboeken

### Lokaal opzetten na clone

```bash
git clone <repo-url>
cd projectenlog
pip install openai
mkdir -p input/inbox input/processed projecten
export OPENAI_API_KEY=sk-...
```

## Onderhoud

Alle configuratie verloopt uitsluitend via `config.py`:
- Projecten toevoegen of verwijderen: pas `PROJECTEN` aan
- LLM-model wijzigen: pas `TEXT_MODEL` aan
