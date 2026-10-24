# SupportFlow · Service (Block 3)

Regeln für jedes KI-Werkzeug, das in diesem Projekt arbeitet (Cursor, Copilot, Codex, Gemini, …).
Claude Code liest stattdessen `CLAUDE.md` — gleicher Inhalt.

1. Lies zuerst `KONTEXT.md`. Dort stehen Stack, Vertrag, Abnahmekriterien und Verbote.
   Sie gelten für jede Aufgabe.
2. Der Vertrag des Service steht in `openapi.yaml` — Feldnamen und Werte daraus sind verbindlich.
3. Was das System fachlich tun soll, steht in `SPEC.md` — nur lesen, wenn eine Aufgabe darauf
   verweist.
4. Arbeitsweise: Erst den Plan zeigen, dann Code. Ein Baustein je Diff. Nichts umbenennen, was
   nicht Teil des Auftrags ist. Keine neue Abhängigkeit ohne Rückfrage. Das Frontend unter `www/`
   wird nicht verändert.
