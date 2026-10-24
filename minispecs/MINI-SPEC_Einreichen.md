# Mini-SPEC · Ticket einreichen

> Entstanden in der Live-Demo, Block 3. Die erste Fassung hatte die Zeile «Wiederholung» nicht —
> die KI hat genau gebaut, was dastand, und beim zweiten Senden entstand ein zweites Ticket.
> Die Zeile kam zuerst hierher, dann in `openapi.yaml`, erst dann in den Code.

## Anforderung

Eine Kundin meldet ein Problem. Es entsteht **genau ein** Ticket mit Nummer und Status «offen»
(SPEC FR-1). Die Quittung kommt sofort (NfA-1: unter 300 ms) — eingeschätzt wird später.

## Vertrag

`POST /api/tickets` mit `titel` und `text` → das neue Ticket. Wo: Ticket-Service, Paket `intake`.

## Ablauf

- **Wenn** Titel und Text da sind, **dann** entsteht ein Ticket mit der nächsten Nummer, Status «offen»,
  Antwort 201 mit dem Ticket. Es erscheint sofort in der Liste.
- **Wenn** der Titel fehlt oder leer ist, **dann** entsteht kein Ticket; Antwort 400 in der Fehlerform.
- **Wiederholung: Wenn** dieselbe Einreichung ein zweites Mal kommt (gleicher Schlüssel im Kopf
  `Idempotency-Key`), **dann** entsteht **kein** zweites Ticket; Antwort 200 mit dem ersten Ticket.

## Tests

- Statusübersicht: «offen» steigt nach einer Einreichung um eins.
- Zweimal mit demselben Schlüssel senden: «offen» steigt nur einmal.
- Ohne Titel: 400, «offen» unverändert.
