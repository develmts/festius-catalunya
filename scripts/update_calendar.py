# scripts/update_calendar.py
from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

import requests

# ---------------------------------------------------------------------
# Configuració general
# ---------------------------------------------------------------------
URL = (
    "https://analisi.transparenciacatalunya.cat/"
    "download/xxnh-f2kn/text/calendar"
)

DATA_DIR = Path("data")
ICS_LATEST = DATA_DIR / "festes_nacionals_catalunya_latest.ics"

# Patró robust: permet espais inicials i apòstrofs diferents
PATTERN = re.compile(
    r"^\s*SUMMARY:Festa d['’]àmbit nacional\b",
    re.IGNORECASE,
)


def main() -> None:
    """Descarrega i filtra el calendari oficial de Catalunya."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1️⃣ Descarrega el fitxer complet
    try:
        resp = requests.get(URL, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Error descarregant el fitxer oficial: {e}")
        return

    ics_lines = resp.text.splitlines()

    # 2️⃣ Filtra només els esdeveniments d'àmbit nacional
    events: list[str] = []
    current: list[str] = []
    keep = False
    count = 0

    for raw_line in ics_lines:
        line = raw_line.strip()

        if line.startswith("BEGIN:VEVENT"):
            current = [line]
            keep = False
            continue

        if line.startswith("END:VEVENT"):
            current.append(line)
            if keep:
                events.extend(current)
                count += 1
            current = []
            continue

        current.append(line)
        if PATTERN.search(line):
            keep = True

    # 3️⃣ Construeix el fitxer ICS final
    header = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//develmts//Festius Catalunya Auto//CA",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Festius oficials de Catalunya",
    ]
    new_ics = header + events + ["END:VCALENDAR"]
    content = "\n".join(new_ics)

    # 4️⃣ Escriu fitxer de l'any actual
    year = datetime.now().year
    year_path = DATA_DIR / f"festes_nacionals_catalunya_{year}.ics"
    year_path.write_text(content, encoding="utf-8")

    # 5️⃣ Crea o reemplaça el fitxer "latest" sincronitzat
    shutil.copyfile(year_path, ICS_LATEST)

    print(
        f"✅ Actualitzats {count} esdeveniments d'àmbit nacional "
        f"per a {year}. Fitxer: {ICS_LATEST}"
    )


if __name__ == "__main__":
    main()
