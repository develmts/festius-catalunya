# scripts/update_calendar.py
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import requests


# URL oficial (trencada en dues línies perquè no superi el límit)
URL = (
    "https://analisi.transparenciacatalunya.cat/"
    "download/xxnh-f2kn/text/calendar"
)

DATA_DIR = Path("data")
ICS_PATH_LATEST = DATA_DIR / "festes_nacionals_catalunya_latest.ics"

# Regex robusta: accepta ' i ’, ancora a inici de línia i ignora maj/min
PATTERN = re.compile(
    r"^SUMMARY:Festa d['’]àmbit nacional\b",  # E501 ok: línia curta
    re.IGNORECASE,
)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    resp = requests.get(URL, timeout=30)
    resp.raise_for_status()
    ics_lines = resp.text.splitlines()

    events: list[str] = []
    current_event: list[str] = []
    keep_event = False
    kept_count = 0

    for line in ics_lines:
        if line.startswith("BEGIN:VEVENT"):
            current_event = [line]
            keep_event = False
            continue

        if line.startswith("END:VEVENT"):
            current_event.append(line)
            if keep_event:
                events.extend(current_event)
                kept_count += 1
            current_event = []
            continue

        # línies dins l’esdeveniment
        current_event.append(line)
        if PATTERN.search(line):
            keep_event = True

    header = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//develmts//Festius Catalunya Auto//CA",
        "CALSCALE:GREGORIAN",
    ]

    new_ics = header + events + ["END:VCALENDAR"]
    content = "\n".join(new_ics)

    ICS_PATH_LATEST.write_text(content, encoding="utf-8")

    year = datetime.now().year
    year_path = DATA_DIR / f"festes_nacionals_catalunya_{year}.ics"
    year_path.write_text(content, encoding="utf-8")

    print(f"Actualitzat {kept_count} esdeveniments d'àmbit nacional.")


if __name__ == "__main__":
    main()
