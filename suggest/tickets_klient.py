"""Der Suggest-Service besitzt keine Tickets. Er fragt den Ticket-Service — synchron, mit Zeitgrenze.

    from suggest.tickets_klient import hole_ticket
    ticket = hole_ticket(409)       # dict · None, wenn es das Ticket nicht gibt
                                    # DienstNichtErreichbar, wenn der Ticket-Service schweigt
"""
from basis.klient import DienstNichtErreichbar, hole_json  # noqa: F401
from basis.konfig import einstellung


def hole_ticket(id):
    basis_url = einstellung("TICKETS_URL", "http://localhost:8766")
    status, daten = hole_json(f"{basis_url}/api/tickets/{int(id)}")
    if status == 404:
        return None
    if status != 200:
        raise DienstNichtErreichbar(f"Ticket-Service antwortet {status}")
    return daten
