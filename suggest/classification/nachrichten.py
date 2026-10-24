"""Asynchrone Einschätzung — eingereicht nach klassifiziert, gemäss ADR-3."""
from basis.warteschlange import empfaenger, sende
from suggest.llm import classifier


@empfaenger("eingereicht")
def bei_eingereicht(nachricht):
    ticket = {feld: nachricht[feld] for feld in ("id", "titel", "text")}
    einschaetzung = classifier().klassifiziere(ticket)
    # Fehler weiterreichen: Die Warteschlange wiederholt mit demselben Auftrag.
    sende("klassifiziert", {"id": nachricht["id"],
                            "angefordert_am": nachricht["angefordert_am"],
                            "einschaetzung": einschaetzung})
