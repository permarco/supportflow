"""Persistentes Entscheidungsprotokoll für B2, ohne Kundentexte."""
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

DATEI = Path(__file__).resolve().parents[2] / "laufzeit" / "audit" / "eskalation.jsonl"
_sperre = threading.Lock()


def protokolliere(ticket_id, aufrufer, entscheidung):
    eintrag = {"zeitpunkt": datetime.now(timezone.utc).isoformat(),
               "ticket_id": ticket_id, "aufrufer": aufrufer, "entscheidung": entscheidung}
    with _sperre:
        DATEI.parent.mkdir(parents=True, exist_ok=True)
        with DATEI.open("a", encoding="utf-8") as datei:
            datei.write(json.dumps(eintrag, ensure_ascii=False) + "\n")
            datei.flush()
            os.fsync(datei.fileno())
