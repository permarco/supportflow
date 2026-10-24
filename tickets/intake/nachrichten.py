"""Ergebnisse gehören zum Ticket-Service; doppelte und veraltete Ergebnisse verwerfen."""
from basis.http import log
from basis.warteschlange import empfaenger
from tickets.speicher import speicher


@empfaenger("klassifiziert")
def bei_klassifiziert(nachricht):
    uebernommen = speicher.uebernehme_einschaetzung(
        nachricht["id"], nachricht["angefordert_am"], nachricht["einschaetzung"])
    log(f"Einschätzung für Ticket {nachricht['id']}: "
        + ("übernommen" if uebernommen else "ignoriert (kein offener passender Auftrag)"))
