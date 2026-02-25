PROJECTEN = {
    "SWZ – Veemarkt": ["Veemarkt"],
    "SWZ – Spoorzone": ["Spoorzone"],
    "SWZ – Roelenkwartier / Buro 11": ["Roelenkwartier", "Buro 11"],
    "SWZ – Gildenhof": ["Gildenhof"],
    "SWZ – Waterlelie": ["Waterlelie"],
    "SWZ – Vechtrand": ["Vechtrand"],
    "SWZ – Zwolle Zuid Zuid": ["Zwolle Zuid", "Zwolle Zuid Zuid"],
    "SWZ – Knarrenhof": ["Knarrenhof"],

    "Openbaar Belang – Parkeren Zwolle": ["Parkeren Zwolle"],

    "Gooi en Om – Kanjerhof": ["Kanjerhof"],
    "Gooi en Om – Kininelaantje": ["Kininelaantje"],

    "Woonbedrijf – Stadshart Woensel": ["Stadshart Woensel"],
    "Woonbedrijf – Limbeek": ["Limbeek"],
    "Woonbedrijf – Vaartbroek": ["Vaartbroek"],

    "Idealis – RvC": ["RvC", "Raad van Commissarissen"],

    "Kennemerhart – Jansstraat": ["Jansstraat"],

    "Wonen Limburg – Kazernekwartier Charlie": ["Kazernekwartier", "Charlie"],
    "Wonen Limburg – Veilingterrein": ["Veilingterrein"],
    "Wonen Limburg – Kiekweg": ["Kiekweg", "beschut wonen"],
    "Wonen Limburg – Rabobank Venray": ["Rabobank Venray", "Rabobank"],
    "Wonen Limburg – Servaashof Vigo": ["Servaashof", "Vigo"],
    "Wonen Limburg – VieCuri": ["VieCuri"],
}

PROJECT_MAP = "projecten"
ONBEKEND_PROJECT = "_onbekend"

# Default LLM model (later eenvoudig aanpasbaar)
TEXT_MODEL = "gpt-4o"

# Documentenmap voor referentiecontext (mapnamen, contactpersonen, spelling)
DOCS_DIR = "/Users/arthur/Documents"

# Clientmappen in DOCS_DIR die als referentie worden meegenomen
CLIENT_FOLDERS = [
    "SWZ",
    "Gooi en Om",
    "Haarlem Jansstraat",
    "Idealis",
    "OpenbaarBelang",
    "Stadshart Woensel - Eindhoven",
    "Wonen Limburg",
    "Woonbedrijf",
    "Smart2Result",
]

# Contactenbestand (xlsx) voor correcte spelling van namen en bedrijven
CONTACTEN_FILE = "/Users/arthur/Documents/Smart2Result/Contacten.xlsx"

# Data paden - standaard iCloud (Mac), maar te overschrijven via environment
# voor GitHub Actions of andere omgevingen
ICLOUD_BASE = "~/Library/Mobile Documents/com~apple~CloudDocs/projectenlog"
ICLOUD_INBOX = "~/Library/Mobile Documents/com~apple~CloudDocs/projectenlog/input/inbox"
ICLOUD_PROCESSED = "~/Library/Mobile Documents/com~apple~CloudDocs/projectenlog/input/processed"
ICLOUD_PROJECTEN = "~/Library/Mobile Documents/com~apple~CloudDocs/projectenlog/projecten"

# Als PROJECTENLOG_LOCAL is gezet, gebruik lokale repo paden (voor GitHub Actions)
USE_LOCAL_PATHS = bool(__import__("os").environ.get("GITHUB_ACTIONS"))
