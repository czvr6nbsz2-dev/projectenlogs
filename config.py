PROJECTEN = {
    "SWZ – Veemarkt": ["Veemarkt"],
    "SWZ – Spoorzone": ["Spoorzone"],
    "SWZ – Roelenkwartier / Buro 11": ["Roelenkwartier", "Buro 11"],
    "SWZ – Gildenhof": ["Gildenhof"],
    "SWZ – Waterlelie": ["Waterlelie"],
    "SWZ – Vechtrand": ["Vechtrand"],
    "SWZ – Zwolle Zuid Zuid": ["Zwolle Zuid", "Zwolle Zuid Zuid"],

    "Openbaar Belang – Parkeren Zwolle": ["Parkeren Zwolle"],

    "Gooi en Om – Kanjerhof": ["Kanjerhof"],
    "Gooi en Om – Kininelaantje": ["Kininelaantje"],

    "Woonbedrijf – Stadshart Woensel": ["Stadshart Woensel"],

    "Idealis – RvC": ["RvC", "Raad van Commissarissen"],

    "Kennemerhart – Jansstraat": ["Jansstraat"],

    "Wonen Limburg – n.t.b.": ["Wonen Limburg"],
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
    "Smart2Result",
]

# Contactenbestand (xlsx) voor correcte spelling van namen en bedrijven
CONTACTEN_FILE = "/Users/arthur/Documents/Smart2Result/Contacten.xlsx"

# iCloud Drive inbox (hier komen opnames van iPhone binnen)
ICLOUD_INBOX = "~/Library/Mobile Documents/com~apple~CloudDocs/projectenlog/input/inbox"
