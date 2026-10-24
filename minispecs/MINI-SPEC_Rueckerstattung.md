# Mini-SPEC · Rückerstattungen sicher eskalieren

## Anforderung und Vertrag

Eine verlangte oder offene Rückerstattung erhält im Suggest-Service die Aktion
`eskalieren`, unabhängig vom Modellvorschlag. Kategorie und Priorität bleiben bestehen.
Die Begründung wird durch einen nachvollziehbaren Hinweis auf die Service-Regel ersetzt.
Das bestehende Schema `Einschaetzung` in openapi.yaml genügt; keine neuen API-Felder.

## Ablauf und Textfälle

Nach erfolgreicher Adapterantwort wird dieselbe Regel bei GET /api/suggest und beim
Empfang von `eingereicht` angewendet. Ungültige lokale Antworten bleiben ModellFehler;
die Regel repariert keine ungültigen Ausgaben. Sie gilt auch beim Fake.
GET speichert nichts. Asynchron eskaliert der Ticket-Service wie bisher nach Empfang
von `klassifiziert`; der Auftrags-Timestamp bleibt unverändert.

Erkannt werden Rückerstattung/Rueckerstattung, Erstattung, Erstattungsantrag,
zurückerstatten/zurueckerstatten, erstatten sowie Geld zurück/zurueck in Titel oder Text.
Ein Treffer gilt vorsorglich als offen. Ausnahme: Der gesamte Text ist eine kurze,
eindeutige Abschlussbestätigung wie «Rückerstattung erhalten, danke», «Ich habe die
Rückerstattung erhalten» oder «Das Geld ist zurück». Zusätzliche Forderungen, Negationen
und mehrdeutige Sätze fallen nicht unter diese Ausnahme. Ein Titel mit einer weiteren
Forderung (z. B. «Weitere Rückerstattung») verhindert ebenfalls die Ausnahme.
Eine Abschlussbestätigung wird nicht eigenständig geschlossen; der Modellvorschlag bleibt.

Die begrenzte deutsche Texterkennung garantiert keine Erkennung beliebiger Umschreibungen,
Sprachen oder Tippfehler. Eine strukturierte Auswahl im Formular folgt separat.
Die Service-Regel entscheidet keine Auszahlung und führt keine Rückerstattung aus.

## Tests

- Offene Rückerstattung überschreibt auch `schliessen` und falsche Modellkategorie.
- Erstattung, Bitte um Erstattung und Geld zurück werden erkannt.
- Abschlussbestätigung löst keine zusätzliche Eskalation aus.
- «nicht erhalten», Teilrückzahlung und weitere Forderung eskalieren.
- Beide Eintrittspunkte wenden die Regel an; Timestamp bleibt erhalten.
- Das Ergebnis aus dem asynchronen Pfad eskaliert das Ticket im Ticket-Speicher.
- ModellFehler verhindert weiterhin die Ergebnisnachricht.

LLM=fake bleibt aktiv. Frontend und vorhandene Playwright-Tests bleiben unverändert.
