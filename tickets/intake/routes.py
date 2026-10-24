"""Endpunkte des Ticket-Eingangs — Vertrag: openapi.yaml.

GET /api/tickets, GET /api/tickets/{id} und POST /api/tickets (Mini-SPEC «Ticket einreichen»).
"""
import threading

from basis.fehler import fehler
from basis.http import route, json_antwort, log
from basis.warteschlange import sende
from tickets.speicher import speicher


@route("GET", "/api/tickets")
def tickets_liste(anfrage):
    return json_antwort(speicher.alle())


@route("GET", "/api/tickets/{id}")
def ticket_lesen(anfrage):
    """Ein Ticket — oder 404 in der Fehlerform. Unbekannt und «keine Zahl» ergeben dieselbe Antwort."""
    nummer = anfrage.params["id"]
    ticket = speicher.finde(nummer) if nummer.isdigit() else None
    if ticket is None:
        return fehler("ticket_unbekannt", "Ticket nicht gefunden.", 404, intern=f"angefragt: {nummer!r}")
    return json_antwort(ticket)


_bekannt = {}                      # Idempotency-Key -> Ticketnummer (Block 4: in der Datenbank)
_ausstehend = {}                   # Noch nicht erfolgreich abgelegte Aufträge, nur im Speicher.
_sperre = threading.Lock()


@route("POST", "/api/tickets")
def ticket_einreichen(anfrage):
    """Ein Ticket einreichen — MINI-SPEC_Einreichen.md.

    Gleicher Idempotency-Key ein zweites Mal: kein neues Ticket, sondern das erste, mit 200.
    """
    try:
        daten = anfrage.json() or {}
    except ValueError:
        daten = {}
    titel = str(daten.get("titel") or "").strip()
    text = str(daten.get("text") or "").strip()
    if not titel:
        return fehler("titel_fehlt", "Bitte einen Titel angeben.", 400, intern=f"eingegangen: {daten!r}")

    schluessel = anfrage.headers.get("idempotency-key")
    with _sperre:
        if schluessel and schluessel in _bekannt:
            log(f"Wiederholung erkannt ({schluessel}) → Ticket {_bekannt[schluessel]}")
            ticket = speicher.finde(_bekannt[schluessel])
            status = 200
        else:
            ticket = speicher.anlegen({"titel": titel, "text": text})
            _ausstehend[ticket["id"]] = speicher.beauftrage_einschaetzung(ticket["id"])
            if schluessel:
                _bekannt[schluessel] = ticket["id"]
            status = 201
        if ticket["id"] in _ausstehend:
            try:
                sende("eingereicht", _ausstehend[ticket["id"]])
            except OSError as exc:
                return fehler("warteschlange_nicht_verfuegbar", "Einschätzung konnte nicht beauftragt werden.",
                              503, intern=str(exc))
            del _ausstehend[ticket["id"]]
    if status == 201:
        log(f"Ticket {ticket['id']} angelegt")
    return json_antwort(ticket, status)
