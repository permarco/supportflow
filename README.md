# SupportFlow · Startprojekt Block 3

Das Frontend aus Block 2 läuft nicht mehr gegen den Mock, sondern gegen **zwei eigene Dienste hinter
einem Gateway**. Das Frontend und seine Tests bleiben unverändert — sie merken den Wechsel nicht.
Aufbau und Gründe: `SPEC.md` §15 und ADR-1, ADR-3, ADR-7, ADR-8.

```
Browser ──▶ Gateway :8765 ──▶ Ticket-Service :8766 ──▶ Speicher-Attrappe (Block 4: Datenbank)
                        └──▶ Suggest-Service :8767 ──▶ LLM hinter dem Port (Fake · lokal · Cloud)
             Ticket-Service ⇄ Warteschlange ⇄ Suggest-Service   (asynchron, ADR-3, festgelegt in A2)
```

## Starten

```bash
./service.sh                       # alle drei Dienste; Frontend auf http://localhost:8765
npm install                        # einmalig, für die Tests (Node 20+)
npx playwright install chromium    # einmalig
npx playwright test                # die Tests aus Block 2 — gegen Ihre Dienste
./llm_probe.sh                     # das LLM aus .env antwortet? (Vorbereitung 3)
./mock.sh                          # zum Vergleich: der Mock aus Block 2 (statt service.sh, selber Port)
```

Windows (PowerShell): drei Fenster mit `python -m tickets`, `python -m suggest`, `python -m gateway`.

## Was drin ist

| Ordner / Datei | Was |
|---|---|
| `openapi.yaml` | **der Vertrag** zwischen Frontend und Diensten — noch lückenhaft (A2) |
| `minispecs/MINI-SPEC_Einreichen.md` | die Mini-SPEC aus der Live-Demo — Muster für jede neue Fähigkeit |
| `gateway/` | der eine Eingang auf Port 8765 — Frontend und Weiterleitung, keine Fachlogik |
| `tickets/` | Ticket-Service: `intake` (Liste, Detail, Einreichen) · `escalation` · `audit` · `speicher/` (Port + Attrappe) |
| `suggest/` | Suggest-Service: `classification` (A1) · `reply` (A2) · `llm/` (Port + Fake, ADR-2) · `tickets_klient.py` |
| `basis/` | gemeinsame Technik: Router, Fehlerform, Warteschlange, Aufruf eines anderen Dienstes |
| `mcp_geruest/` · `.mcp.json` | MCP-Server mit einem Werkzeug (`ticket_lesen`) — die zweite Tür zum Ticket-Service für KI-Werkzeuge (Werkstatt A5). Claude Code fragt beim ersten Start einmal nach |
| `laufzeit/warteschlange/` | entsteht beim Start: je Thema ein Ordner, je Nachricht eine Datei (`ls` zeigt, was wartet) |
| `.env` | `LLM=fake \| lokal \| cloud` — welcher Adapter antwortet; `TICKETS_URL` |
| `www/`, `tests/` | das Frontend aus Block 2 und seine Playwright-Tests — **das Messinstrument, nicht anfassen** |
| `mock.sh` · `mock_assistent.py` | der Mock aus Block 2, zum Vergleich |
| `KONTEXT.md` | wie wir bauen — Abschnitt «Service». **Liest die KI bei jedem Auftrag.** |
| `SPEC.md` · `PROMPTS.md` · `TRANSFER.md` | was SupportFlow tut und warum · Prompts der Übungen · Vorlage Transfer |
| `CLAUDE.md`, `AGENTS.md`, `.claude/settings.json` | binden `KONTEXT.md` ein |

## Mit Ihrem KI-Werkzeug verbinden

Das Werkzeug muss `KONTEXT.md` kennen. Claude Code liest `CLAUDE.md`, andere Werkzeuge `AGENTS.md`.
Probe: «Welche Dienste gibt es, und wem gehören die Tickets?»

Ticket **#422** enthält `<b>test</b>`, Ticket **#433** Anweisungen an das System — beides Absicht.
