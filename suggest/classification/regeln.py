"""Deterministische Fachregeln nach der Adapterprüfung; siehe Mini-SPEC Rückerstattung."""
import re

_ANLIEGEN = re.compile(
    r"\b(?:rückerstattung\w*|rueckerstattung\w*|erstattung\w*|"
    r"(?:zurück|zurueck)?erstatte\w*)\b|\bgeld\s+(?:zurück|zurueck)\b")
_ABSCHLUSS = re.compile(
    r"(?:danke[,! .]*)?(?:(?:ich habe (?:die |meine )?|(?:die |meine )?)"
    r"(?:rückerstattung|rueckerstattung|erstattung) (?:bereits |vollständig )?erhalten"
    r"|(?:das |mein )?geld ist (?:zurück|zurueck))"
    r"[.! ,]*(?:danke|vielen dank)?[.! ]*")
_NEUTRALE_TITEL = {"", "danke", "erledigt", "rückerstattung", "rueckerstattung",
                   "erstattung", "geld zurück", "geld zurueck"}


def wende_regeln_an(ticket, einschaetzung):
    """Offene Rückerstattung erzwingt Eskalation; Eingaben werden nicht verändert."""
    titel = ticket.get("titel", "").strip().casefold()
    text = ticket.get("text", "").strip().casefold()
    if not _ANLIEGEN.search(titel + "\n" + text):
        return einschaetzung
    if _ABSCHLUSS.fullmatch(text) and (
            titel in _NEUTRALE_TITEL or _ABSCHLUSS.fullmatch(titel)):
        return einschaetzung
    return {**einschaetzung, "aktionen": ["eskalieren"],
            "begruendung": "Service-Regel: Das Ticket enthält ein offenes oder nicht eindeutig "
                           "abgeschlossenes Rückerstattungsanliegen und wird zur Prüfung eskaliert."}
