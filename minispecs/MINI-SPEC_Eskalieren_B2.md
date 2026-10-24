# Mini-SPEC · B2 Eskalieren mit Rollenprüfung

## Anforderung und Vertrag
POST /api/tickets/{id}/eskalieren nach openapi.yaml. Nur der exakte Headerwert
X-Aufrufer: mensch darf eskalieren. agent, fehlende und unbekannte Werte ergeben
403 vor dem Ticket-Abruf. Ungültige/unbekannte Nummern ergeben für mensch 404.
Erfolg: 200 mit Ticket; Wiederholung bleibt eskaliert. Kein neuer MCP-Aufruf (erst B3).
Gateway reicht X-Aufrufer durch. Die Rollenangabe ist kein Identitätsnachweis.
Die automatische A2-Eskalation über Nachrichten bleibt bestehen.

## Audit und Ablauf
Implementierung in tickets/audit/, persistentes JSONL unter
laufzeit/audit/eskalation.jsonl (nicht versioniert). Jeder am Endpunkt eintreffende
Versuch wird mit UTC-Zeitpunkt, angefragter Ticketnummer, Aufrufer und Entscheidung
freigegeben/abgewiesen/nicht_gefunden geschrieben. Keine Kundentexte.
Die Freigabe wird vor der Statusänderung gespeichert; sie belegt die Entscheidung,
nicht eine atomar garantierte Durchführung. Ein Absturz dazwischen ist möglich.
Audit-Ausfall: 503, keine Änderung, interner Fehler mit Korrelationsnummer im Dienstlog.
Ein ausgefallenes Audit kann den Versuch selbst nicht dauerhaft speichern.
Ein Lock verhindert vermischte Zeilen innerhalb des Ticket-Service-Prozesses.

## Tests
Mensch: 200 und eskaliert; Wiederholung: 200; agent/fehlend/unbekannt: 403,
Status unverändert. Unbekannte/ungültige Nummer: 404 für mensch, sonst 403.
Jeder Fall erzeugt einen Audit-Eintrag. Audit bleibt nach erneutem Öffnen lesbar.
Audit-Ausfall verändert kein Ticket. Gateway-Weiterleitung wird geprüft.
