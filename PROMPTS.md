# Prompts für den Präsenztag · Block 3

Hilfe, wenn Sie nicht weiterkommen — nicht der Weg. Die Regeln stehen in `KONTEXT.md`; sie werden
im Prompt nicht wiederholt. Erst den Plan zeigen lassen, dann Code, ein Diff nach dem anderen.

## A1 · Selbst im Loop — die Einschätzung

```text
Lies openapi.yaml und KONTEXT.md. Ich möchte im Suggest-Service den Endpunkt für
die Einschätzung eines Tickets ergänzen. Der Ablauf: [Ihre drei Fälle, «Wenn … dann …»].
Zeig mir zuerst den Plan. Noch keinen Code.
```

## A2 · Werkstatt: der Vertrag und Ihre Dienste

Schritt 0 — den Entscheid festhalten (Ihre Worte aus der Präsenz, die KI bringt sie ins Format):

```text
Führe ADR-3 in SPEC.md nach. Entscheid: [wer legt welche Nachricht mit welchen Feldern
in welche Warteschlange, wer liest sie]. Ergänze Folgt aus, Entscheid und Preis im
Format der anderen ADR und ergänze das Bild in §15. Erfinde nichts. Zeig mir den Diff.
```

Schritt 1 — Vertrag schliessen:

```text
Ergänze openapi.yaml: eine Fehlerform für jeden Endpunkt, der Fehlerfall im Strom
(event: error), die Einschätzung am Ticket, die Nachrichten aus ADR-3.
Regeln: SPEC.md §5, §6, §15 und ADR-3. Erfinde nichts, was dort nicht steht — markiere offene
Fragen. Zeig mir den Diff.
```

Schritt 2 — Antwortentwurf als Strom:

```text
Im Suggest-Service GET /api/draft nach openapi.yaml, über drafter() aus suggest/llm.
Die Weichen slow und fail reicht der Endpunkt an den Fake weiter. Zeig mir den Plan.
```

Schritt 2 — die Warteschlange:

```text
Setze ADR-3 um, mit den Nachrichten aus openapi.yaml: Der Ticket-Service sendet nach
dem Einreichen, der Suggest-Service empfängt, schätzt ein und sendet zurück, der
Ticket-Service setzt die Einschätzung und eskaliert, wenn «eskalieren» vorgeschlagen ist.
Mindestens einmal zugestellt — jeder Empfänger muss das aushalten. Zeig mir den Plan.
```

Schritt 4 — repo-weit:

```text
Eine Fehlerform für alle Endpunkte beider Dienste und für den Router: code, meldung,
korrelation — nie einen Stacktrace. Zeig mir den Diff je Datei.
```

## A5 · Werkstatt: KI im Service

Sechs Schritte, je ein Auftrag. Vorher selbst: das Modell wählen und in `.env` eintragen (A1),
die Regeln formulieren (A2), festlegen, wer eskalieren darf (B2). Nach jedem Auftrag den Diff lesen,
auch auf das, was Sie **nicht** bestellt haben.

A1 · Adapter lokal oder Cloud:

```text
Lege in suggest/llm/ einen Adapter «lokal» an, nach dem Muster des Fake: er ruft das
lokale Modell über Ollama auf (Adresse und Modell aus .env). Schalte das Nachdenken des
Modells aus: reasoning_effort: none. Wählbar mit LLM=lokal in suggest/llm/__init__.py.
Nur Standardbibliothek. Regeln und Prüfung kommen später.
```

A2 · Regeln und Formular:

```text
Ergänze im Adapter lokal die Anweisung an das Modell um unsere Regeln: [Ihre Regeln,
z. B. prioritaet hoch, wenn der Kunde blockiert ist oder Geld betroffen ist; aktionen
enthält eskalieren bei Rückerstattung, Beschwerde, Rechtsfrage oder Drohung]. Verlange das
Formular als JSON-Schema mit den Feldern von Einschaetzung aus openapi.yaml, Temperatur 0.
```

A3 · Antwort prüfen:

```text
Prüfe im Adapter lokal jede Einschätzung gegen den Vertrag (Einschaetzung in openapi.yaml),
bevor sie zurückgeht. Lege die Prüfung in suggest/llm/pruefung.py an. Passt etwas nicht,
wirf ModellFehler, damit das Ticket offen bleibt.
```

B1 · MCP-Server verbinden: kein Auftrag zum Bauen. Claude Code im Projekt starten, den Server
`supportflow` freigeben, dann fragen:

```text
Lies Ticket 412 aus SupportFlow.
```

B2 · Prüfung im Dienst:

```text
Lege im Ticket-Service einen Endpunkt POST /api/tickets/{id}/eskalieren an, zuerst in
openapi.yaml. Der Aufrufer steht in der Kopfzeile X-Aufrufer, der Gateway reicht sie durch.
Eskalieren darf nur «mensch», ein «agent» bekommt 403. Jeder Versuch, auch der abgewiesene,
kommt ins Audit unter tickets/audit/.
```

B3 · Eine Wirkung anbieten:

```text
Trage im MCP-Server ein zweites Werkzeug «ticket_eskalieren» ein. Parameter: id.
Beschreibung: «Eskaliert ein Ticket an einen Menschen. Nur verwenden, wenn ein Mensch das
verlangt hat.» Der Aufruf geht an POST /api/tickets/{id}/eskalieren mit X-Aufrufer: agent.
```

Nachweis 4, danach in Claude Code (Server neu laden mit `/mcp`):

```text
Eskaliere Ticket 433 in SupportFlow.
```
