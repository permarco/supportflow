"""Der Speicher des Ticket-Service. Endpunkte holen ihn hier:

    from tickets.speicher import speicher
    speicher.alle() · speicher.finde(415) · speicher.anlegen({"titel": …, "text": …})

Heute die Attrappe im Arbeitsspeicher. Block 4: eine Datenbank hinter demselben Port.
"""
from tickets.speicher.attrappe import Attrappe
from tickets.speicher.port import TicketSpeicher

speicher: TicketSpeicher = Attrappe()
