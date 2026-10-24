# SupportFlow · Projekt-Kontext

Support-Ticket-Assistent für ein kleines Team. Das Frontend steht; jetzt entsteht der Service dahinter,
und der Mock verschwindet.
Dieses Dokument ist die Eingabe für den KI-Assistenten: Es beschreibt, was in keinem
Trainingsdatensatz steht — unseren Stack, unseren Vertrag, unsere Regeln.

## Aus Block 1 — Kurzfassung, vollständig in `SPEC.md`

- **Ziel:** Support-Anfragen entgegennehmen, mit einem LLM klassifizieren (Kategorie, Priorität,
  Konfidenz), dem Support-Team eine Antwort vorschlagen — **der Mensch entscheidet und sendet.**
- **Qualitätsziele, priorisiert:** 1. Datenschutz (keine ungeprüften Kundendaten an externe LLM) ·
  2. Nachvollziehbarkeit (jede KI-Entscheidung begründet).
- **Vertrauensgrenze:** zwischen unserem Service und dem LLM-Provider. Was zurückkommt, ist
  ungeprüfte Eingabe.
- Rollen: Kunde (reicht ein) · Support-Mitarbeitende (prüfen, senden) · Leitung (überwacht).
- Anforderungen, Architektur-Entscheide und Guardrails im Detail: `SPEC.md` — nur lesen, wenn der
  Auftrag darauf zeigt.

## Frontend

### Stack

- Frontend: HTML + ein ES-Modul je Bildschirm unter `www/` (z. B. `www/uebersicht.js`).
- **Das Frontend wird nicht verändert.** Es ist das Messinstrument: Seine Tests unter `tests/`
  sagen, ob der Service den Vertrag erfüllt.
- Kein Framework, kein Build-Schritt.
- Bausteine: `www/components.js` (StatusChip, TicketZeile, STIL) — aus dem Vorprojekt
  übernommen. Verwenden, nicht neu bauen.
- Die Seite wird vom Service unter `http://localhost:8765/` ausgeliefert (bisher vom Mock).

### Datenvertrag

- `Ticket = { id, titel, status, prio, text }`, ab A2 dazu `einschaetzung` (optional, gesetzt aus der
  Warteschlange «klassifiziert»)
- `status`: `offen` | `eskaliert` | `erledigt` · `prio`: `tief` | `mittel` | `hoch`
- Quelle: `GET http://localhost:8765/api/tickets` (Liste) und `/api/tickets/<id>` (ein Ticket).
- **Keine weiteren Felder** als diese — auch nicht «zur Sicherheit».
- Assistent: `GET /api/draft?ticket=<id>` streamt den Antwortentwurf (SSE, ein Wort je Ereignis,
  `event: done` am Ende, `event: error` bei Fehler). `GET /api/suggest?ticket=<id>` liefert
  `{ kategorie, prioritaet, aktionen[], begruendung }` am Stück.

### Abnahmekriterien — das muss jeder Bildschirm erfüllen

- **Tastatur:** ohne Maus bedienbar. Mit Tab erreicht man jedes Element, mit Enter löst man es aus.
  In Listen bewegt man sich mit den Pfeiltasten auf und ab, Enter öffnet.
- **Kundentext:** Text von Kunden (Titel, Text eines Tickets) wird angezeigt, nie ausgeführt
  (technisch: `textContent`, kein `innerHTML`).
- **Leer- und Fehlerfall:** Wenn keine Daten da sind oder der Service nicht antwortet, sieht man
  das auf der Seite.
- **Grösse:** Die Seite bleibt klein, unter 100 kB, gemessen im Netzwerk-Tab.

### Design-Variablen

- Farben, Abstände, Schrift nur über `var(--…)` aus `www/variablen.css`. Keine festen Werte im Code.

### Komponenten

- Status nur über `StatusChip(status)`, Ticket-Zeilen nur über `TicketZeile(t)` aus `components.js`.
- Keine eigenen Chips, keine eigenen Zeilen, keine Inline-Styles.

### Tests

- Playwright unter `tests/`, Aufruf `npx playwright test`.
- Ein Test je Verhalten.

### Verbote

- Nichts Fremdes einbauen, ohne zu fragen: keine neue Bibliothek, kein Paket, kein CDN-Link.
- Alles Klickbare ist ein Link oder ein Knopf (`<a>`, `<button>`), nie ein `div` mit `onclick`.

## Assistent

### Zustände
- wartet · Text strömt · fertig · abgebrochen · Fehler — jeder Zustand ist auf der Seite sichtbar.
- Eine abgebrochene Antwort ist als unvollständig gekennzeichnet.

### Stufen je Aktion
| Aktion | Stufe | in der Oberfläche |
|---|---|---|
| Kategorie, Priorität vorschlagen | autonom | Chip «Vorschlag», ein Klick übernimmt, ein zweiter nimmt zurück |
| Antwortentwurf ins Antwortfeld übernehmen | autonom | Knopf; das Feld bleibt editierbar und ist sichtbar als «Antwortentwurf» markiert |
| Antwort an den Kunden senden | mit Bestätigung | Knopf «Senden …», Rückfrage nennt den Empfänger |
| Ticket schliessen · eskalieren | mit Bestätigung | Knopf, dann Rückfrage |
| Kundendaten anzeigen · Gutschrift auslösen | nie | kein Element — auch nicht ausgegraut |

### Erlaubte Aktionen
- Nur `antworten`, `eskalieren`, `schliessen` aus `aktionen` bekommen ein Element. Alles andere: nichts.
- Die Einschätzung wird vor dem Rendern gegen den Datenvertrag geprüft; unbekannte Felder und Werte
  werden verworfen. Die Begründung ist Text, nie HTML.

### Stopp und Ausfall
- Stopp schliesst die Verbindung zum Service. Nachweis: das Mock-Terminal meldet «Abbruch bemerkt».
- Antwortet der Service nicht (5 s), zeigt die Seite den Zustand «Fehler» — nie ewig «wartet».

### Senden
- Nur per Klick mit Rückfrage. Nie automatisch.

## Service

### Aufbau — drei Prozesse, ein Start (SPEC §15, ADR-1)
- `./service.sh` startet alle drei. Jeder loggt mit Namen: `[gateway]`, `[tickets]`, `[suggest]`.
- Dienste startet und stoppt die Person am Rechner, nie die KI. Die KI startet keine Prozesse und
  weicht nicht auf andere Ports aus; sie sagt, wann neu gestartet werden muss.
- **Gateway** `gateway/` · Port 8765 · liefert `www/` aus, leitet `/api/…` weiter. Keine Fachlogik.
- **Ticket-Service** `tickets/` · Port 8766 · Pakete `intake` · `escalation` · `audit`.
  Er **besitzt die Tickets**. Zugriff nur über `from tickets.speicher import speicher` (Port, ADR-8).
- **Suggest-Service** `suggest/` · Port 8767 · Pakete `classification` · `reply`. Er besitzt keine Tickets —
  er holt sie mit `hole_ticket(id)` aus `suggest/tickets_klient.py` (Zeitgrenze 2 s).
- Gemeinsame Technik in `basis/`: `http.py` (Router, JSON, Strom), die Fehlerform (heute die Funktion `fehler()` in
  `tickets/intake/routes.py`, ab A2 Schritt 4 einmal in `basis/fehler.py`),
  `warteschlange.py` (Nachrichten zwischen den Diensten), `klient.py` (Aufruf eines anderen Dienstes).
- Ein Endpunkt ist eine Funktion mit `@route` in `routes.py` eines Pakets, ein Empfänger aus der
  Warteschlange eine Funktion mit `@empfaenger` in `nachrichten.py`. Beides wird beim Start geladen.
- Python 3, nur Standardbibliothek. Kein Framework, keine neue Abhängigkeit.

### Vertrag
- `openapi.yaml` ist der Vertrag. Pfade, Feldnamen und erlaubte Werte daraus sind verbindlich —
  das Frontend kennt nur sie. **Zuerst den Vertrag ändern, dann den Code.**
- Fehler immer in der einen Fehlerform `{code, meldung, korrelation}` — nie ein Stacktrace nach aussen.
- Der Antwortentwurf ist ein Strom (Server-Sent Events): `data:` je Wort, `event: done` am Ende,
  `event: error` bei Fehler — `Strom(...)` aus `basis/http.py`.
- Eine neue Fähigkeit beginnt mit einer Mini-SPEC (Anforderung · Vertrag · Ablauf · Tests),
  Muster: `minispecs/MINI-SPEC_Einreichen.md`.

### Zwischen den Diensten
- Synchron nur, wo jemand auf die Antwort wartet — immer mit Zeitgrenze. Schweigt der andere Dienst:
  503 in der Fehlerform, das Ticket bleibt bearbeitbar (FR-2).
- Asynchron über `basis/warteschlange.py`: `sende(thema, nachricht)` und `@empfaenger(thema)`.
  Zustellung **mindestens einmal** — jeder Empfänger muss dieselbe Nachricht zweimal aushalten.

### MCP — die zweite Tür
- `mcp_geruest/` ist ein MCP-Server (stdio, nur Standardbibliothek) und eine Tür zum **Ticket-Service**.
  Jedes Werkzeug ruft einen Endpunkt über den Gateway — nie den Speicher direkt.
- Was erlaubt ist, prüft der Ticket-Service in seiner Fachlogik, nicht die Werkzeugbeschreibung.

### LLM
- Kein LLM-Aufruf ausserhalb von `suggest/llm/` (ADR-2). Die Fachlogik ruft `classifier()`
  und `drafter()` — nie einen Anbieter.
- Im Test antwortet der Fake (`LLM=fake` in `.env`). Was vom Modell zurückkommt, ist Eingabe und
  wird geprüft, bevor es Wirkung hat.

### Tests
- Playwright unter `tests/` gegen den Gateway auf Port 8765: `npx playwright test`.
- Unit-Tests für die Dienste: `python3 -m unittest discover tests/unit`.

## Arbeitsweise

- Erst den Plan zeigen, dann Code.
- Ein Baustein je Diff. Diffs kurz halten und lesbar.
- Nichts umbenennen oder umstrukturieren, was nicht Teil des Auftrags ist.
- Das Frontend unter `www/` bleibt unverändert.
