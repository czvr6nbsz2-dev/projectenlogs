#!/usr/bin/env python3
"""Sync projecten/*.md naar Apple Notities (map 'Projectenlog')."""

import os
import re
import subprocess
import sys

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTEN_DIR = os.path.join(REPO_DIR, "projecten")
FOLDER_NAME = "Projectenlog"


def md_to_html(md: str) -> str:
    """Converteer projectlog-markdown naar eenvoudige HTML voor Apple Notes."""
    lines = md.strip().split("\n")
    html_parts: list[str] = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append("<br>")
            continue

        # ## datum
        if stripped.startswith("## "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            date_text = stripped[3:]
            html_parts.append(f"<h2>{date_text}</h2>")
            continue

        # Subsectie-koppen (Besluiten / afspraken:, Signalen / aandachtspunten:)
        if stripped.endswith(":") and not stripped.startswith("-"):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f"<b>{stripped}</b>")
            continue

        # Bullet
        if stripped.startswith("- "):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{stripped[2:]}</li>")
            continue

        # Overige tekst
        html_parts.append(f"<p>{stripped}</p>")

    if in_list:
        html_parts.append("</ul>")

    return "\n".join(html_parts)


def note_exists(name: str) -> bool:
    """Check of een notitie met deze naam al bestaat."""
    result = subprocess.run(
        ["osascript", "-e", f'''
tell application "Notes"
    try
        set n to first note of folder "{FOLDER_NAME}" whose name is "{name}"
        return "yes"
    on error
        return "no"
    end try
end tell'''],
        capture_output=True, text=True
    )
    return result.stdout.strip() == "yes"


def create_note(name: str, html_body: str):
    """Maak een nieuwe notitie aan."""
    # Titel wordt de <h1>, body volgt daarna
    full_html = f"<h1>{name}</h1>\n{html_body}"
    subprocess.run(
        ["osascript", "-e", f'''
tell application "Notes"
    set f to folder "{FOLDER_NAME}"
    make new note at f with properties {{name:"{name}", body:"{_escape(full_html)}"}}
end tell'''],
        capture_output=True, text=True
    )


def update_note(name: str, html_body: str):
    """Werk een bestaande notitie bij."""
    full_html = f"<h1>{name}</h1>\n{html_body}"
    subprocess.run(
        ["osascript", "-e", f'''
tell application "Notes"
    set f to folder "{FOLDER_NAME}"
    set n to first note of f whose name is "{name}"
    set body of n to "{_escape(full_html)}"
end tell'''],
        capture_output=True, text=True
    )


def _escape(s: str) -> str:
    """Escape voor AppleScript string."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def sync_all():
    """Sync alle projecten naar Apple Notities."""
    if not os.path.isdir(PROJECTEN_DIR):
        print("Geen projecten/ map gevonden.")
        return

    # Zorg dat de map bestaat
    subprocess.run(
        ["osascript", "-e", f'''
tell application "Notes"
    try
        get folder "{FOLDER_NAME}"
    on error
        make new folder with properties {{name:"{FOLDER_NAME}"}}
    end try
end tell'''],
        capture_output=True, text=True
    )

    count = 0
    for filename in sorted(os.listdir(PROJECTEN_DIR)):
        if not filename.endswith(".md") or filename.startswith(".") or filename == "_onbekend.md":
            continue

        filepath = os.path.join(PROJECTEN_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            continue

        name = filename.removesuffix(".md")
        html = md_to_html(content)

        if note_exists(name):
            update_note(name, html)
            print(f"  Bijgewerkt: {name}")
        else:
            create_note(name, html)
            print(f"  Aangemaakt: {name}")
        count += 1

    print(f"{count} notities gesynchroniseerd.")


if __name__ == "__main__":
    sync_all()
