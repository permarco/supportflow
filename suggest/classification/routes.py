"""Ticket einschätzen — minispecs/MINI-SPEC_Einschaetzung.md."""
from basis.fehler import fehler as _fehler
from basis.http import json_antwort, route
from suggest.llm import classifier, ModellFehler
from suggest.classification.regeln import wende_regeln_an
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

    try:
        ergebnis = classifier().klassifiziere(ticket, anfrage.query)
    except ModellFehler as exc:
        return _fehler("modell_nicht_verfuegbar", "Einschätzung gerade nicht möglich.", 503,
                       intern=str(exc))
    return json_antwort(wende_regeln_an(ticket, ergebnis))
