"""Ticket einschätzen — minispecs/MINI-SPEC_Einschaetzung.md."""
from basis.fehler import fehler as _fehler
from basis.http import json_antwort, route
from suggest.llm import classifier
from suggest.tickets_klient import DienstNichtErreichbar, hole_ticket


@route("GET", "/api/suggest")
def einschaetzung(anfrage):
    nummer = anfrage.query.get("ticket", "")
    try:
        ticket_id = int(nummer)
    except ValueError:
        return _fehler("ticket_unbekannt", "Ticket nicht gefunden.", 404,
                       intern=f"ungültige Ticketnummer: {nummer!r}")

    try:
        ticket = hole_ticket(ticket_id)
    except DienstNichtErreichbar as exc:
        return _fehler("dienst_nicht_erreichbar", "Einschätzung gerade nicht möglich.", 503,
                       intern=str(exc))

    if ticket is None:
        return _fehler("ticket_unbekannt", "Ticket nicht gefunden.", 404,
                       intern=f"angefragt: {ticket_id}")

    return json_antwort(classifier().klassifiziere(ticket, anfrage.query))
