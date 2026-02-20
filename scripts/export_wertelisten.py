"""
Export reference data (Wertelisten) to Markdown for the research AI prompt.

Reads seed JSON files and generates a Markdown document with all valid codes
that the research AI should use in its output.

Usage:
    uv run python scripts/export_wertelisten.py [--output PATH]

Default output: ../hersteller_marken_serien_recherche/Wertelisten_Referenzdaten.md
"""
import json
import argparse
from datetime import date
from pathlib import Path

SEED_DIR = Path(__file__).parent.parent / "seed"
DEFAULT_OUTPUT = (
    Path(__file__).parent.parent.parent
    / "hersteller_marken_serien_recherche"
    / "Wertelisten_Referenzdaten.md"
)


def load_json(filename: str) -> list[dict]:
    path = SEED_DIR / filename
    if not path.exists():
        print(f"WARNUNG: {path} nicht gefunden, ueberspringe.")
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def generate_markdown() -> str:
    rechtsformen = load_json("rechtsformen.json")
    lizenzen = load_json("medien_lizenzen.json")

    lines = [
        "# Wertelisten & Referenzdaten fuer die Hersteller-Recherche",
        "",
        f"> **Stand:** {date.today().isoformat()}",
        "> **Quelle:** UDO API (unternehmensdaten.org) — automatisch generiert",
        "> **Script:** `udo__api/scripts/export_wertelisten.py`",
        "",
        "Diese Datei enthaelt die gueltigen Codes fuer strukturierte Felder im Recherche-JSON.",
        "Die Recherche-KI soll diese Codes in den entsprechenden `_code`-Feldern verwenden,",
        "damit der Import in die UDO API ohne Mapping-Warnungen funktioniert.",
        "",
        "---",
        "",
        "## 1. Rechtsformen (`rechtsform_code`)",
        "",
        "Verwende den **Code** im Feld `hersteller.rechtsform_code`.",
        "Das Freitext-Feld `hersteller.rechtsform` kann zusaetzlich befuellt werden.",
        "",
        "| Code | Kurzform | Langform | Land |",
        "|------|----------|----------|------|",
    ]

    # Group by country
    by_land: dict[str, list[dict]] = {}
    for rf in rechtsformen:
        land = rf.get("land_code", "??")
        by_land.setdefault(land, []).append(rf)

    for land in sorted(by_land.keys()):
        for rf in sorted(by_land[land], key=lambda x: x["code"]):
            lines.append(
                f"| `{rf['code']}` | {rf['name']} | {rf.get('name_lang', '')} | {land} |"
            )

    lines.extend([
        "",
        "### Beispiel im JSON",
        "",
        "```json",
        '{',
        '  "hersteller": {',
        '    "rechtsform": "GmbH (Gesellschaft mit beschraenkter Haftung)",',
        '    "rechtsform_code": "gmbh"',
        '  }',
        '}',
        "```",
        "",
        "---",
        "",
        "## 2. Medien-Lizenzen (`lizenz_code`)",
        "",
        "Verwende den **Code** im Feld `logo.lizenz_code`.",
        "Das Freitext-Feld `logo.lizenz` kann zusaetzlich befuellt werden.",
        "",
        "### Kategorien",
        "",
        "| Kategorie | Bedeutung |",
        "|-----------|-----------|",
        "| `frei` | Frei nutzbar (Public Domain, CC0, eigene Erstellung) |",
        "| `eingeschraenkt` | Nutzbar mit Bedingungen (CC BY-SA, CC BY-NC) |",
        "| `geschuetzt` | Geschuetzt, Nutzung nur mit Genehmigung (Trademark, Copyright) |",
        "",
        "### Verfuegbare Lizenzen",
        "",
        "| Code | Name | Kategorie | Beschreibung |",
        "|------|------|-----------|--------------|",
    ])

    for liz in sorted(lizenzen, key=lambda x: (x.get("kategorie", ""), x["code"])):
        lines.append(
            f"| `{liz['code']}` | {liz['name']} | {liz.get('kategorie', '')} "
            f"| {liz.get('beschreibung', '')} |"
        )

    lines.extend([
        "",
        "### Typische Zuordnungen",
        "",
        "| Logo-Typ | Empfohlener Code | Begruendung |",
        "|----------|-----------------|-------------|",
        "| Reines Textlogo (z.B. Schriftzug) | `pd_textlogo` | Keine Schoepfungshoehe |",
        "| Markenlogo mit Grafik-Elementen | `trademark` | Eingetragene Marke |",
        "| Logo von Wikipedia/Wikimedia | Lizenz der Datei pruefen | Oft `pd_textlogo` oder `trademark` |",
        "| Selbst erstelltes Logo | `eigenkreation` | Volle Nutzungsrechte |",
        "| Vom Hersteller freigegebenes Pressematerial | `pressefreigabe` | Fuer Presse/Info freigegeben |",
        "",
        "### Beispiel im JSON",
        "",
        "```json",
        '{',
        '  "logo": {',
        '    "dateiname": "mga_entertainment_logo.svg",',
        '    "format": "svg",',
        '    "quelle_url": "https://commons.wikimedia.org/wiki/File:MGA_Entertainment_logo.svg",',
        '    "lizenz": "PD-textlogo (Public Domain, reines Textlogo)",',
        '    "lizenz_code": "pd_textlogo"',
        '  }',
        '}',
        "```",
        "",
        "---",
        "",
        "## 3. Unternehmenstypen (zur Information)",
        "",
        "Werden beim Import automatisch zugewiesen. Kein Feld im JSON noetig.",
        "",
        "| Typ | Beschreibung |",
        "|-----|-------------|",
        "| Hersteller | Produziert eigene Produkte |",
        "| Lieferant | Beliefert den Handel |",
        "| Grosshaendler | Vertreibt Produkte mehrerer Hersteller |",
        "| Haendler | Verkauft an Endkunden |",
        "| Importeur | Bringt auslaendische Produkte in den Markt |",
        "| Dienstleister | Erbringt Dienstleistungen |",
        "",
        "---",
        "",
        "## 4. Medienarten (zur Information)",
        "",
        "Werden beim Import automatisch gesetzt. Kein Feld im JSON noetig.",
        "",
        "| Code | Beschreibung |",
        "|------|-------------|",
        "| `LOGO` | Firmen- oder Markenlogo |",
        "| `LOGO_ICON` | Logo-Icon/Favicon |",
        "| `TITELBILD` | Titelbild/Header |",
        "| `FOTO` | Foto |",
        "| `STOREFRONT` | Geschaeftsfoto/-ansicht |",
        "",
    ]
    )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Export Wertelisten to Markdown")
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    md = generate_markdown()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(md, encoding="utf-8")
    print(f"Wertelisten exportiert nach: {args.output}")
    print(f"  Rechtsformen: {len(load_json('rechtsformen.json'))} Eintraege")
    print(f"  Medien-Lizenzen: {len(load_json('medien_lizenzen.json'))} Eintraege")


if __name__ == "__main__":
    main()
