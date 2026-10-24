# mcp_geruest — die zweite Tür zum Ticket-Service (Werkstatt A5)

Ein MCP-Server mit **zwei** Werkzeugen (`ticket_lesen`, `ticket_eskalieren`), nur Standardbibliothek. Ihr KI-Werkzeug
startet ihn selbst über `.mcp.json`; von Hand: `python3 -m mcp_geruest`.

- Er ruft den Ticket-Service **über den Gateway** (`SUPPORTFLOW_URL`, Standard `http://localhost:8765`).
  `./service.sh` muss laufen.
- Er prüft nichts Fachliches. Was erlaubt ist, entscheidet der Ticket-Service — so hält die Grenze
  auch, wenn ein Agent die REST-Schnittstelle direkt ruft.
- Neue Werkzeuge aus Ihrem Werkzeug-Vertrag: in `WERKZEUGE` eintragen (Beschreibung, Eingabeschema,
  Funktion). Wer das offizielle SDK (`pip install mcp`) nimmt, baut dasselbe mit weniger Zeilen.

Probe ohne KI-Werkzeug:

```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"ticket_lesen","arguments":{"id":415}}}' \
  | python3 -m mcp_geruest
```

## B3 · Eskalationsversuch

`ticket_eskalieren(id)` sendet POST /api/tickets/{id}/eskalieren über den Gateway,
immer mit X-Aufrufer: agent. Der Aufrufer ist kein Werkzeugparameter.
B2 verweigert den Versuch mit HTTP 403 und protokolliert ihn. MCP liefert isError=true
mit der Fehlerantwort; das Ticket bleibt unverändert. Die Beschreibung ersetzt keine
Berechtigungsprüfung. Zum Laden des neuen Werkzeugs muss der MCP-Client neu verbinden;
eine clientseitige Werkzeug-Allowlist muss auch ticket_eskalieren enthalten.
