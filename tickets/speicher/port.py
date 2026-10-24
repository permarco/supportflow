"""Der Port zum Speicher. Der Ticket-Service kennt nur diese Schnittstelle — nie eine Datenbank.

Heute antwortet eine Attrappe im Arbeitsspeicher (attrappe.py). In Block 4 tritt eine echte
Datenbank an ihre Stelle, ohne dass sich an den Endpunkten etwas ändert.
"""
from typing import Protocol


class TicketSpeicher(Protocol):
    def alle(self) -> list[dict]: ...
    def finde(self, id: int) -> dict | None: ...
    def anlegen(self, daten: dict) -> dict:
        """Vergibt die nächste Nummer, setzt status «offen» und gibt das neue Ticket zurück."""
    def setze_status(self, id: int, status: str) -> dict | None: ...
    def setze_einschaetzung(self, id: int, einschaetzung: dict) -> dict | None: ...
    def beauftrage_einschaetzung(self, id: int) -> dict | None:
        """Speichert einen neuen internen Auftrag und liefert die eingereicht-Nachricht."""
    def uebernehme_einschaetzung(self, id: int, angefordert_am: str, einschaetzung: dict) -> bool:
        """Übernimmt nur das erste aktuelle Ergebnis, inklusive Eskalation, atomar."""
