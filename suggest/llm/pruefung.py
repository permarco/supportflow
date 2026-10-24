"""Vertrag und zusätzliche Formularregeln für lokale Einschätzungen."""
from suggest.llm.port import ModellFehler

# Die vier Felder aus openapi.yaml; engere Werte sind Vorgaben des lokalen Adapters.
EINSCHAETZUNG_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["kategorie", "prioritaet", "aktionen", "begruendung"],
    "properties": {
        "kategorie": {"type": "string", "enum": [
            "Account", "Abrechnung", "Technisch", "Reklamation", "Sonstiges"]},
        "prioritaet": {"type": "string", "enum": ["tief", "mittel", "hoch"]},
        "aktionen": {"type": "array", "minItems": 1, "maxItems": 1,
                     "items": {"type": "string", "enum": ["antworten", "eskalieren", "schliessen"]}},
        "begruendung": {"type": "string"},
    },
}

def pruefe_einschaetzung(ergebnis):
    """Weist ungültige Ausgaben vollständig ab, ohne sie zu korrigieren."""
    if not isinstance(ergebnis, dict):
        raise ModellFehler("Einschätzung muss ein JSON-Objekt sein.")
    if set(ergebnis) != set(EINSCHAETZUNG_SCHEMA["required"]):
        raise ModellFehler("Einschätzung enthält fehlende oder zusätzliche Felder.")

    felder = EINSCHAETZUNG_SCHEMA["properties"]
    for feld in ("kategorie", "prioritaet", "begruendung"):
        if not isinstance(ergebnis[feld], str):
            raise ModellFehler(f"Einschätzung: {feld} muss Text sein.")
        if "enum" in felder[feld] and ergebnis[feld] not in felder[feld]["enum"]:
            raise ModellFehler(f"Einschätzung: {feld} enthält einen unerlaubten Wert.")

    aktionen = ergebnis["aktionen"]
    if not isinstance(aktionen, list) or len(aktionen) != 1:
        raise ModellFehler("Einschätzung muss genau eine Aktion enthalten.")
    if not isinstance(aktionen[0], str) or aktionen[0] not in felder["aktionen"]["items"]["enum"]:
        raise ModellFehler("Einschätzung enthält eine unerlaubte Aktion.")
    return ergebnis


def pruefe_entwurf(text):
    """Konservativer Filter vor jeder Ausgabe; kein semantischer Sicherheitsbeweis."""
    import re
    import unicodedata
    if not isinstance(text, str) or not text.strip():
        raise ModellFehler("Lokaler Antwortentwurf ist leer oder unlesbar.")
    normal = unicodedata.normalize("NFKC", text).casefold()
    normal = normal.replace("geben sie ihr passwort niemals weiter.", "")
    if re.search(r"passw[oö]r|password|kennwort|einmalcode|einmal-code|"
                 r"zugangsdaten|zugangsschlüssel|zugangsschluessel|"
                 r"api[- ]?key|token|\bpin\b|\botp\b|sicherheitscode|"
                 r"bestätigungscode|2fa|2-fa|wiederherstellungscode", normal):
        raise ModellFehler("Lokaler Antwortentwurf hat die Sicherheitsprüfung nicht bestanden.")
    return text
