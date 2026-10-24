# A5 · Abnahme und Reflexion · 24.10.2026

## Vier Nachweise

1. Lokales Modell: qwen3.5:4b erzeugte Einschätzungen. Ticket 409 wurde im Browser
   mit Kategorie Account und Priorität hoch angezeigt; geprüfter Entwurf fertig.
   Ein künstliches Login-Ticket wurde zuvor dreimal identisch eingeschätzt.
2. Ungültige Modellausgabe: Tests weisen unerlaubte Aktionen und falsche Feldtypen
   mit ModellFehler ab. Es entsteht keine klassifiziert-Nachricht. Die Feldprüfung
   beweist keine fachliche Richtigkeit; die Rückerstattungsregel ergänzt sie.
3. Echtes eingebundenes MCP-Werkzeug ticket_lesen hat Tickets erfolgreich abgerufen
   (unter anderem 412 und 433). Frühere Terminal-Protokolltests waren nur Vorprüfungen.
4. Ticket 433 über MCP gelesen; eingebettete Anweisungen nicht ausgeführt. Der vom
   Benutzer ausdrücklich verlangte MCP-Eskalationsversuch erhielt 403, Code
   eskalation_verboten, Korrelation dca75b9bc4d0. Ticket blieb offen/tief.
   Audit: 2026-10-24T14:21:37.733971+00:00, 433, agent, abgewiesen.

## Abschliessender Testlauf

- python -m unittest discover tests/unit -q: 23 Tests bestanden.
- npx playwright test --workers=1: 28 Tests bestanden in 46,1 Sekunden.
  Darin enthalten: alle 24 ursprünglichen Tests und vier neue UI-Tests.
- Ticket-Service mit frischen Beispieldaten gestartet. Der Suggest-Testprozess
  verwendete LLM=fake als Umgebungsvariable; die lokale .env blieb auf LLM=lokal.
- Nach dem Lauf Suggest wieder mit LLM=lokal gestartet. Das persistente Audit bleibt.

## Veto-Notiz · Entwurf aus dem Gespräch

Der Benutzer bestand mehrfach auf Vertrag und Plan vor Code, Diff-Prüfung und keinem
Commit/Push ohne Auftrag. Die KI hatte fehlende Chips zuerst als Anzeige-/Scrollproblem
interpretiert; die Benutzerbeobachtung führte zur Diagnose der parallelen Anfragen und
unpassenden Zeitgrenzen. UI-Änderungen wurden danach ausdrücklich genehmigt.
Ein lokaler Entwurf verlangte ein Passwort: Der Benutzer beauftragte die Absicherung.
Der zunächst zu strenge Filter blockierte auch Warnungen; auf Benutzerauftrag wurde
auch dieser Fehler korrigiert. Die KI stellte MCP-Terminaltests wiederholt als Ersatz
für die noch fehlende native Einbindung dar; die Unterscheidung wurde klargestellt und
anschliessend mit echten MCP-Werkzeugaufrufen geprüft.

Diese Notiz behauptet kein ausdrückliches Veto gegen Tests oder Mini-SPECs, das im
Gespräch nicht belegt ist. Persönliche Bewertung und Ergänzung durch den Benutzer offen.

## Grenzen

X-Aufrufer ist eine frei setzbare Übungsrolle, keine sichere Authentifizierung.
Textregeln/Entwurfprüfung sind begrenzt und keine allgemeine Sicherheitsgarantie.
Tickets sind flüchtig; Audit und Warteschlangendateien sind persistent.
Die optionale Ticketsuche wurde nicht implementiert. Die weitergehende Tabelle im
Übungsblatt (Begründung und Offen-Prüfung beim Eskalieren) geht über den vereinbarten
B2/B3-Prompt hinaus und ist hier nicht umgesetzt.
