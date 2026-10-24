"""B2: Rollenprüfung vor jeder manuellen Eskalation."""
from basis.fehler import fehler
from basis.http import json_antwort, route
from tickets.audit.protokoll import protokolliere
from tickets.speicher import speicher


@route("POST", "/api/tickets/{id}/eskalieren")
def eskalieren(anfrage):
    nummer = anfrage.params["id"]
    aufrufer = anfrage.headers.get("x-aufrufer")
    ticket = None
    if aufrufer != "mensch":
        entscheidung = "abgewiesen"
    else:
        ticket = speicher.finde(nummer) if nummer.isascii() and nummer.isdigit() else None
        entscheidung = "freigegeben" if ticket is not None else "nicht_gefunden"
    try:
        protokolliere(nummer, aufrufer, entscheidung)
    except OSError as exc:
        return fehler("audit_nicht_verfuegbar", "Eskalation gerade nicht möglich.", 503,
                      intern=f"Audit fehlgeschlagen: {exc}")
    if entscheidung == "abgewiesen":
        return fehler("eskalation_verboten", "Nur menschliche Aufrufer dürfen eskalieren.", 403,
                      intern=f"Eskalation von Ticket {nummer!r} abgewiesen")
    if ticket is None:
        return fehler("ticket_unbekannt", "Ticket nicht gefunden.", 404,
                      intern=f"Eskalation: Ticket {nummer!r} unbekannt")
    return json_antwort(speicher.setze_status(ticket["id"], "eskaliert"))
