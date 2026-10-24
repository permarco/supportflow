"""Antwortentwurf als SSE-Strom — Vertrag und Fake-Abgrenzung: openapi.yaml."""
from basis.fehler import fehler as _fehler
from basis.http import Strom, log, route
from suggest.llm import ModellFehler, drafter
from suggest.tickets_klient import DienstNichtErreichbar, hole_ticket


def _schliesse(woerter):
    schliessen = getattr(woerter, "close", None)
    if schliessen:
        schliessen()


@route("GET", "/api/draft")
def antwortentwurf(anfrage):
    nummer = anfrage.query.get("ticket", "")
    try:
        ticket_id = int(nummer)
    except ValueError:
        return _fehler("ticket_unbekannt", "Ticket nicht gefunden.", 404,
                       intern=f"ungültige Ticketnummer: {nummer!r}")

    try:
        ticket = hole_ticket(ticket_id)
    except DienstNichtErreichbar as exc:
        return _fehler("dienst_nicht_erreichbar", "Antwortentwurf nicht verfügbar oder bei der Prüfung abgewiesen.", 503,
                       intern=str(exc))
    if ticket is None:
        return _fehler("ticket_unbekannt", "Ticket nicht gefunden.", 404,
                       intern=f"angefragt: {ticket_id}")

    # Erstes Wort vor den HTTP-Headern abrufen: Ein früher Modellfehler ergibt noch 503.
    woerter = None
    try:
        woerter = iter(drafter().entwerfe(ticket, anfrage.query))
        erstes = next(woerter, None)
    except ModellFehler as exc:
        _schliesse(woerter)
        return _fehler("modell_nicht_verfuegbar", "Antwortentwurf nicht verfügbar oder bei der Prüfung abgewiesen.", 503,
                       intern=str(exc))

    def ereignisse():
        try:
            if erstes is not None:
                yield None, erstes
            for wort in woerter:
                yield None, wort
            yield "done", "{}"
        except ModellFehler as exc:
            log(f"Antwortentwurf für Ticket {ticket_id} abgebrochen: {exc}")
            yield "error", "Verbindung zum Modell verloren"
        finally:
            # Der HTTP-Rahmen schliesst diesen Generator auch beim Browser-Abbruch.
            _schliesse(woerter)

    return Strom(ereignisse())
