# tickets/audit · B2

protokoll.py schreibt jeden Eskalationsversuch als JSON-Zeile nach
laufzeit/audit/eskalation.jsonl. Enthalten sind UTC-Zeitpunkt, Ticketnummer,
Aufrufer und Entscheidung. Die Datei bleibt über Neustarts bestehen.
Details und Ausfallverhalten: minispecs/MINI-SPEC_Eskalieren_B2.md.
