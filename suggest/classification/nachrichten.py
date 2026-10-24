"""Asynchrone Einschätzung — eingereicht nach klassifiziert, gemäss ADR-3."""
from basis.warteschlange import empfaenger, sende
from suggest.llm import classifier
from suggest.classification.regeln import wende_regeln_an


@empfaenger("eingereicht")
def bei_eingereicht(nachricht):
    ticket = {feld: nachricht[feld] for feld in ("id", "titel", "text")}
    einschaetzung = classifier().klassifiziere(ticket)
    einschaetzung = wende_regeln_an(ticket, einschaetzung)
    # Fehler weiterreichen: Die Warteschlange wiederholt mit demselben Auftrag.
    sende("klassifiziert", {"id": nachricht["id"],
                            "angefordert_am": nachricht["angefordert_am"],
                            "einschaetzung": einschaetzung})
