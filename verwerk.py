from __future__ import annotations

import json
import logging
import os
import re
import shutil
import sys
from collections import defaultdict
from datetime import date, datetime

from openai import OpenAI

# Load .env file if present (for API key)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _val = _line.split("=", 1)
                os.environ.setdefault(_key.strip(), _val.strip())

from config import (
    CLIENT_FOLDERS,
    DOCS_DIR,
    ICLOUD_INBOX,
    ICLOUD_PROCESSED,
    ICLOUD_PROJECTEN,
    ONBEKEND_PROJECT,
    PROJECTEN,
    TEXT_MODEL,
    USE_LOCAL_PATHS,
)

# Gebruik iCloud paden (Mac) of lokale repo paden (GitHub Actions)
if USE_LOCAL_PATHS:
    INBOX = os.path.join(BASE_DIR, "input", "inbox")
    PROCESSED = os.path.join(BASE_DIR, "input", "processed")
    PROJECTEN_DIR = os.path.join(BASE_DIR, "projecten")
else:
    INBOX = os.path.expanduser(ICLOUD_INBOX)
    PROCESSED = os.path.expanduser(ICLOUD_PROCESSED)
    PROJECTEN_DIR = os.path.expanduser(ICLOUD_PROJECTEN)

AUDIO_EXTENSIONS = (".m4a", ".wav", ".mp3", ".webm", ".mp4")
TEXT_EXTENSIONS = (".txt", ".md")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

client = OpenAI()


# ---------------------------------------------------------------------------
# Directory setup
# ---------------------------------------------------------------------------

def ensure_dirs():
    os.makedirs(INBOX, exist_ok=True)
    os.makedirs(PROCESSED, exist_ok=True)
    os.makedirs(PROJECTEN_DIR, exist_ok=True)


def collect_inbox_files() -> list[str]:
    """Collect supported files from iCloud inbox."""
    all_files: list[str] = []
    if not os.path.isdir(INBOX):
        return all_files
    for filename in sorted(os.listdir(INBOX)):
        ext = os.path.splitext(filename)[1].lower()
        if ext in AUDIO_EXTENSIONS + TEXT_EXTENSIONS:
            full_path = os.path.join(INBOX, filename)
            if os.path.isfile(full_path):
                all_files.append(full_path)
    return all_files


# ---------------------------------------------------------------------------
# Date extraction
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def extract_date(file_path: str) -> str:
    """Return YYYY-MM-DD from the filename, or fall back to file mtime."""
    basename = os.path.basename(file_path)
    m = _DATE_RE.search(basename)
    if m:
        return m.group(1)
    mtime = os.path.getmtime(file_path)
    return date.fromtimestamp(mtime).isoformat()


def extract_time_label(file_path: str) -> str:
    """Return HH:MM from filename (e.g. '2026-01-30_09-14.m4a' → '09:14'), or ''."""
    basename = os.path.splitext(os.path.basename(file_path))[0]
    m = re.search(r"\d{4}-\d{2}-\d{2}_(\d{2})-(\d{2})", basename)
    if m:
        return f"{m.group(1)}:{m.group(2)}"
    return ""


# ---------------------------------------------------------------------------
# Audio / text reading
# ---------------------------------------------------------------------------

def transcribe(audio_path: str) -> str:
    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            file=f,
            model="whisper-1",
        )
    return transcript.text


def read_text(text_path: str) -> str:
    with open(text_path, "r", encoding="utf-8") as f:
        return f.read()


def get_plain_text(file_path: str) -> str | None:
    if os.path.getsize(file_path) == 0:
        log.warning("Overgeslagen (leeg bestand): %s", file_path)
        return None
    ext = os.path.splitext(file_path)[1].lower()
    if ext in AUDIO_EXTENSIONS:
        return transcribe(file_path)
    if ext in TEXT_EXTENSIONS:
        return read_text(file_path)
    return None


# ---------------------------------------------------------------------------
# Reference context (unchanged)
# ---------------------------------------------------------------------------

def gather_reference_context() -> str:
    """Scan client folders in Documents for project names, people, and companies."""
    if not os.path.isdir(DOCS_DIR):
        return ""

    lines: list[str] = []
    for folder in CLIENT_FOLDERS:
        folder_path = os.path.join(DOCS_DIR, folder)
        if not os.path.isdir(folder_path):
            continue

        lines.append(f"\n{folder}/")
        try:
            for item in sorted(os.listdir(folder_path)):
                if item.startswith("."):
                    continue
                sub_path = os.path.join(folder_path, item)
                if os.path.isdir(sub_path):
                    lines.append(f"  {item}/")
                    try:
                        subs = [
                            s
                            for s in sorted(os.listdir(sub_path))
                            if not s.startswith(".")
                        ]
                        for sub in subs[:15]:
                            lines.append(f"    {sub}")
                    except PermissionError:
                        pass
                else:
                    lines.append(f"  {item}")
        except PermissionError:
            pass

    if not lines:
        return ""

    return "\n".join(lines)


def gather_contacts() -> str:
    """Read contacts from Apple Contacts, filtered to known clients."""
    try:
        import Contacts as CN
    except ImportError:
        return ""

    filter_terms: set[str] = set()
    for project_name in PROJECTEN:
        parts = project_name.split(" – ")
        if parts:
            filter_terms.add(parts[0].lower())
    for aliases in PROJECTEN.values():
        for alias in aliases:
            filter_terms.add(alias.lower())

    try:
        store = CN.CNContactStore.alloc().init()
        keys = [
            CN.CNContactGivenNameKey,
            CN.CNContactFamilyNameKey,
            CN.CNContactOrganizationNameKey,
            CN.CNContactJobTitleKey,
        ]
        request = CN.CNContactFetchRequest.alloc().initWithKeysToFetch_(keys)
        lines: list[str] = []

        def handler(contact, stop):
            given = contact.givenName() or ""
            family = contact.familyName() or ""
            org = contact.organizationName() or ""
            title = contact.jobTitle() or ""
            combined = f"{org} {title}".lower()
            if not any(term in combined for term in filter_terms):
                return
            naam = f"{given} {family}".strip()
            if naam:
                parts = [naam]
                if org:
                    parts.append(org)
                if title:
                    parts.append(title)
                lines.append(" | ".join(parts))

        store.enumerateContactsWithFetchRequest_error_usingBlock_(
            request, None, handler
        )
        return "\n".join(lines)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

def build_prompt(text: str, entry_date: str) -> str:
    project_list = "\n".join(
        f"- {name} (aliassen: {', '.join(aliases)})"
        for name, aliases in PROJECTEN.items()
    )

    reference = gather_reference_context()
    contacts = gather_contacts()

    ref_block = ""
    if reference:
        ref_block += f"""
REFERENTIEMATERIAAL (gebruik voor correcte spelling van namen, bedrijven en projecten):
{reference}
"""
    if contacts:
        ref_block += f"""
CONTACTPERSONEN (gebruik voor correcte spelling van namen en bedrijven):
{contacts}
"""

    return f"""Je verwerkt een werknotitie tot projectlogboek-entries.

BEKENDE PROJECTEN:
{project_list}
{ref_block}

INSTRUCTIES:
- Splits de inhoud per project.
- Koppel alleen als de relatie redelijk zeker is.
- Bij twijfel of algemene inhoud → wijs toe aan "{ONBEKEND_PROJECT}".
- Eén notitie kan meerdere projecten opleveren.
- Gebruik exact het onderstaande Markdown-format per entry.
- Wees zakelijk en compact. Geen aannames of verzinsels.

FORMAT PER ENTRY (gebruik geen ## datumregel, alleen de secties):

Besluiten / afspraken:
- …

Signalen / aandachtspunten:
- …

BELANGRIJK: Laat een sectie volledig weg als er geen inhoud voor is. Als er geen besluiten/afspraken zijn, neem "Besluiten / afspraken:" niet op. Als er geen signalen/aandachtspunten zijn, neem "Signalen / aandachtspunten:" niet op. Neem nooit een sectie op met een leeg streepje.

Geef je antwoord als JSON: een array van objecten met "project" (exact de projectnaam uit bovenstaande lijst, of "{ONBEKEND_PROJECT}") en "entry" (de inhoud ZONDER datumregel).

Voorbeeld:
[
  {{"project": "SWZ – Veemarkt", "entry": "Besluiten / afspraken:\\n- …\\n\\nSignalen / aandachtspunten:\\n- …"}},
  {{"project": "{ONBEKEND_PROJECT}", "entry": "Besluiten / afspraken:\\n- …"}}
]

TEKST:
{text}"""


# ---------------------------------------------------------------------------
# Parsing & writing
# ---------------------------------------------------------------------------

def strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text[text.index("\n") + 1 :]
    if text.endswith("```"):
        text = text[: text.rfind("```")]
    return text.strip()


def parse_entries(llm_output: str) -> list[dict]:
    return json.loads(strip_code_fences(llm_output))


def read_existing_log(project: str) -> str:
    """Read the existing log file for a project, or return ''."""
    safe_name = project.replace("/", "-").replace("\\", "-")
    path = os.path.join(PROJECTEN_DIR, f"{safe_name}.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def write_log(project: str, content: str):
    """Overwrite the log file for a project."""
    safe_name = project.replace("/", "-").replace("\\", "-")
    path = os.path.join(PROJECTEN_DIR, f"{safe_name}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def append_to_date_section(existing: str, entry_date: str, new_bullets: str) -> str:
    """Merge new_bullets into the correct ## YYYY-MM-DD section.

    If a section for entry_date already exists, the new bullets are appended
    into the matching sub-sections (Besluiten / afspraken, Signalen / aandachtspunten).
    Otherwise a new section is appended at the end.
    """
    header = f"## {entry_date}"

    if header not in existing:
        # New date section — append at end
        block = f"{header}\n\n{new_bullets.strip()}\n\n"
        return existing.rstrip("\n") + "\n\n" + block if existing.strip() else block

    # Date section exists — merge bullets into it
    lines = existing.split("\n")
    section_start = None
    section_end = None

    for i, line in enumerate(lines):
        if line.strip() == header:
            section_start = i
        elif section_start is not None and line.startswith("## "):
            section_end = i
            break

    if section_start is None:
        # Shouldn't happen, but fallback
        block = f"{header}\n\n{new_bullets.strip()}\n\n"
        return existing.rstrip("\n") + "\n\n" + block

    if section_end is None:
        section_end = len(lines)

    existing_section = "\n".join(lines[section_start:section_end])
    merged_section = _merge_subsections(existing_section, new_bullets, header)

    result_lines = lines[:section_start] + merged_section.split("\n") + lines[section_end:]
    return "\n".join(result_lines)


def _merge_subsections(existing_section: str, new_bullets: str, header: str) -> str:
    """Merge new bullet content into an existing date section."""
    subsection_names = ["Besluiten / afspraken:", "Signalen / aandachtspunten:"]

    # Parse new bullets into subsections
    new_parts = _split_subsections(new_bullets, subsection_names)
    existing_parts = _split_subsections(existing_section, subsection_names)

    result = [header, ""]
    for name in subsection_names:
        combined = []
        if name in existing_parts:
            combined.extend(existing_parts[name])
        if name in new_parts:
            combined.extend(new_parts[name])
        if combined:
            result.append(name)
            result.extend(combined)
            result.append("")

    return "\n".join(result).rstrip("\n") + "\n"


def _split_subsections(text: str, names: list[str]) -> dict[str, list[str]]:
    """Split text into named subsections, returning {name: [bullet lines]}."""
    result: dict[str, list[str]] = {}
    current = None
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped in names:
            current = stripped
            result[current] = []
        elif current and stripped.startswith("- "):
            result[current].append(line)
    return result


# ---------------------------------------------------------------------------
# Archiving
# ---------------------------------------------------------------------------

def move_to_processed(file_path: str, file_date: str):
    """Move file to input/processed/YYYY-MM-DD/, avoiding overwrites."""
    date_dir = os.path.join(PROCESSED, file_date)
    os.makedirs(date_dir, exist_ok=True)

    basename = os.path.basename(file_path)
    dest = os.path.join(date_dir, basename)

    if os.path.exists(dest):
        name, ext = os.path.splitext(basename)
        counter = 1
        while os.path.exists(dest):
            dest = os.path.join(date_dir, f"{name}_{counter}{ext}")
            counter += 1
    shutil.move(file_path, dest)


# ---------------------------------------------------------------------------
# Interactive helpers (kept for manual use)
# ---------------------------------------------------------------------------

def ask_project_assignment(entry_content: str) -> str:
    """Ask the user which project an unknown entry belongs to."""
    print("\n  -- Onbekend project --")
    for line in entry_content.strip().splitlines():
        print(f"  {line}")
    print()

    projects = list(PROJECTEN.keys())
    for i, name in enumerate(projects, 1):
        print(f"  {i:2d}. {name}")
    print(f"   0. Bewaar in {ONBEKEND_PROJECT}")

    while True:
        try:
            choice = input("\n  Keuze (nummer): ").strip()
            num = int(choice)
            if num == 0:
                return ONBEKEND_PROJECT
            if 1 <= num <= len(projects):
                return projects[num - 1]
        except (ValueError, EOFError):
            pass
        print("  Ongeldig nummer, probeer opnieuw.")


def suggest_aliases(project: str, entry_content: str):
    """Suggest new aliases for the project and offer to add them to config.py."""
    current = PROJECTEN[project]

    prompt = f"""Analyseer deze werknotitie die is toegewezen aan project "{project}".
Huidige zoektermen: {', '.join(current)}

Welke extra zoektermen of sleutelwoorden uit deze tekst zouden helpen om soortgelijke notities
automatisch aan dit project toe te wijzen? Geef maximaal 3 korte, specifieke termen.
Geen termen die al in de huidige lijst staan. Geen generieke woorden.

Geef je antwoord als JSON-array van strings, bijv. ["term1", "term2"].

Tekst:
{entry_content}"""

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        suggestions = json.loads(strip_code_fences(response.choices[0].message.content))
    except (json.JSONDecodeError, ValueError):
        return

    suggestions = [s for s in suggestions if s not in current]
    if not suggestions:
        return

    print(f"\n  Voorgestelde zoektermen voor '{project}':")
    for i, term in enumerate(suggestions, 1):
        print(f"    {i}. {term}")
    print(f"    0. Geen toevoegen")

    choice = input("\n  Welke toevoegen? (nummers gescheiden door komma, of 0): ").strip()
    if choice in ("0", ""):
        return

    try:
        indices = [int(x.strip()) for x in choice.split(",")]
        to_add = [suggestions[i - 1] for i in indices if 1 <= i <= len(suggestions)]
    except (ValueError, IndexError):
        return

    if not to_add:
        return

    update_config_aliases(project, to_add)
    PROJECTEN[project].extend(to_add)
    print(f"  Toegevoegd aan config.py: {', '.join(to_add)}")


def update_config_aliases(project: str, new_aliases: list[str]):
    """Add new aliases to config.py for the given project."""
    config_path = os.path.join(BASE_DIR, "config.py")
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()

    escaped_project = re.escape(f'"{project}"')
    pattern = rf'({escaped_project}:\s*\[)([^\]]*?)(\])'

    def replacer(m):
        existing = m.group(2).rstrip()
        additions = ", ".join(f'"{a}"' for a in new_aliases)
        return f"{m.group(1)}{existing}, {additions}{m.group(3)}"

    new_content = re.sub(pattern, replacer, content)

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(new_content)


# ---------------------------------------------------------------------------
# File processing
# ---------------------------------------------------------------------------

def process_file(file_path: str, file_date: str, time_label: str) -> list[dict]:
    """Process a single file and return list of {project, entry} dicts.

    Does NOT write to log files — the caller handles merging per day.
    """
    log.info("Verwerken: %s", os.path.basename(file_path))

    text = get_plain_text(file_path)
    if not text or not text.strip():
        log.info("  Overgeslagen (leeg bestand): %s", os.path.basename(file_path))
        return []

    if time_label:
        text = f"[memo {time_label}] {text}"

    prompt = build_prompt(text, file_date)

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )

    llm_output = response.choices[0].message.content

    try:
        entries = parse_entries(llm_output)
    except (json.JSONDecodeError, ValueError) as e:
        log.warning("  Fout bij parseren LLM-uitvoer: %s", e)
        return [{"project": ONBEKEND_PROJECT, "entry": llm_output}]

    return entries


def run_batch():
    """Non-interactive batch mode: process all inbox files grouped by date."""
    ensure_dirs()

    supported = collect_inbox_files()

    if not supported:
        log.info("Geen bestanden in inbox.")
        return

    # Group files by date
    by_date: dict[str, list[str]] = defaultdict(list)
    for file_path in supported:
        file_date = extract_date(file_path)
        by_date[file_date].append(file_path)

    # Process each date group
    for file_date in sorted(by_date):
        # Collect all entries for this date across files
        # {project: [bullet_text, ...]}
        day_entries: dict[str, list[str]] = defaultdict(list)

        for file_path in by_date[file_date]:
            time_label = extract_time_label(file_path)
            entries = process_file(file_path, file_date, time_label)

            for entry in entries:
                project = entry.get("project", ONBEKEND_PROJECT)
                content = entry.get("entry", "")
                if content.strip():
                    day_entries[project].append(content.strip())

            move_to_processed(file_path, file_date)

        # Merge into log files
        for project, bullets_list in day_entries.items():
            combined_bullets = "\n\n".join(bullets_list)
            existing = read_existing_log(project)
            merged = append_to_date_section(existing, file_date, combined_bullets)
            write_log(project, merged)
            log.info("  -> %s  (%s)", project, file_date)

    log.info("Klaar.")


def run_interactive():
    """Interactive mode: process files with user prompts for unknown projects."""
    ensure_dirs()

    supported = collect_inbox_files()

    if not supported:
        print("Geen bestanden in inbox.")
        return

    by_date: dict[str, list[str]] = defaultdict(list)
    for file_path in supported:
        file_date = extract_date(file_path)
        by_date[file_date].append(file_path)

    for file_date in sorted(by_date):
        day_entries: dict[str, list[str]] = defaultdict(list)

        for file_path in by_date[file_date]:
            time_label = extract_time_label(file_path)
            entries = process_file(file_path, file_date, time_label)

            for entry in entries:
                project = entry.get("project", ONBEKEND_PROJECT)
                content = entry.get("entry", "")
                if not content.strip():
                    continue

                if project == ONBEKEND_PROJECT:
                    project = ask_project_assignment(content)
                    if project != ONBEKEND_PROJECT:
                        suggest_aliases(project, content)

                day_entries[project].append(content.strip())

            move_to_processed(file_path, file_date)

        for project, bullets_list in day_entries.items():
            combined_bullets = "\n\n".join(bullets_list)
            existing = read_existing_log(project)
            merged = append_to_date_section(existing, file_date, combined_bullets)
            write_log(project, merged)
            print(f"  -> {project}  ({file_date})")

    print("Klaar.")


def main():
    if "--batch" in sys.argv:
        run_batch()
    else:
        run_interactive()


if __name__ == "__main__":
    main()
