# Mini-SPEC · Ticket einschätzen

## Anforderung

Das Support-Team kann für ein vorhandenes Ticket eine Einschätzung anfordern. Diese enthält
Kategorie, Priorität, vorgeschlagene Aktionen und eine Begründung (Teilumfang von SPEC FR-2).
In A1 kommt die Einschätzung vom vorhandenen Fake hinter dem LLM-Port (`LLM=fake`).

## Vertrag

`GET /api/suggest?ticket=<id>` mit dem erforderlichen Query-Parameter `ticket` vom Typ Ganzzahl.
Wo: Suggest-Service, Paket `classification`.

- **200:** JSON nach dem bestehenden Schema `Einschaetzung` mit den Pflichtfeldern
  `kategorie` (Zeichenkette), `prioritaet` (`tief` | `mittel` | `hoch`),
  `aktionen` (Liste von Zeichenketten) und `begruendung` (Zeichenkette).
- **404:** Ticket unbekannt; JSON nach dem bestehenden Schema `Fehler`.
- **503:** Ticket-Service nicht erreichbar oder Zeitgrenze überschritten; JSON nach dem
  bestehenden Schema `Fehler`.

Die Fehlerform enthält `code`, `meldung` und `korrelation`, niemals einen Stacktrace.

Die bestehende `openapi.yaml` soll vor der Implementierung gezielt um die Antworten 404 und 503
für diesen Endpunkt ergänzt werden. Diese Vertragsänderung ist ausdrücklich beauftragt.
Die Erfolgsantwort und die übrigen Endpunkte bleiben unverändert.

## Ablauf

- **Wenn das Ticket vorhanden ist**, holt der Suggest-Service es über `hole_ticket(id)` beim
  Ticket-Service, fordert über den bestehenden LLM-Port die Fake-Einschätzung an und antwortet
  mit 200 und der Einschätzung.
- **Wenn das Ticket unbekannt ist**, antwortet der Suggest-Service mit 404 in der Fehlerform.
  Der Fake wird nicht aufgerufen.
- **Wenn der Ticket-Service nicht erreichbar ist oder innerhalb der Zeitgrenze von 2 Sekunden
  nicht antwortet**, antwortet der Suggest-Service mit 503 in der Fehlerform.

Der Aufruf verändert das Ticket nicht. Der Suggest-Service besitzt und speichert keine Tickets.
Das Speichern der Einschätzung am Ticket und die asynchrone Verarbeitung folgen in A2.

## Tests und Abnahme

- Ein vorhandenes Ticket anfragen: Antwort 200 mit den vier vereinbarten Einschätzungsfeldern
  und einer Priorität aus der erlaubten Werteliste.
- Eine unbekannte Ticketnummer anfragen: Antwort 404 mit `code`, `meldung` und `korrelation`.
- Den Ticket-Service allein stoppen und erneut eine Einschätzung anfragen: Antwort 503 mit
  `code`, `meldung` und `korrelation`. Bei einem schweigenden Dienst greift die Zeitgrenze
  von 2 Sekunden für den Ticket-Abruf.
- Die bestehenden Playwright-Tests gegen die drei Dienste ausführen:
  `npx playwright test`. Ziel laut Übung A1: 19 von 24 Tests grün.

## Abgrenzung

Diese Mini-SPEC umfasst genau die drei genannten Fälle. Fehlende oder ungültige
`ticket`-Parameter sind kein zusätzlicher Abnahmefall dieses Auftrags.

Kein Antwortentwurf, keine Warteschlange und keine Anbindung eines echten Modells in diesem
Schritt. Frontend und bestehende Tests bleiben unverändert. Neue Testdateien sind nicht
beauftragt. Die Dienste startet und stoppt der Benutzer selbst.
