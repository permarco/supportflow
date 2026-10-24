# Transfer · Schnitt, Vertrag, Werkzeug, Mini-ADR für Ihr Projekt

Die Übung TRANSFER am Ende des Präsenztags: vier Zeilen, die Sie unverändert in den Meilenstein
«Services» übernehmen — für **Ihr** Projekt, nicht für SupportFlow. Unten die Vorlage und je ein
Beispiel aus dem heutigen Tag.

## 1 · Der Schnitt

| Modul | Änderungsgrund — wer verlangt Änderungen, wie oft? | Profil — Last, Zeit, Kosten |
|---|---|---|
| … | … | … |
| … | … | … |

**Die Naht dazwischen:** Was fliesst über die Grenze, in welche Richtung?

Beispiel SupportFlow: `intake` (Kunde, selten; unter 300 ms, Lastspitzen) ↔ `classification`
(Support-Leitung und Modellwechsel, monatlich; Sekunden, kostet je Aufruf). Naht: Ticket hin,
Kategorie · Priorität · Konfidenz zurück — heute ein Funktionsaufruf über eine Warteschlange, morgen ein Vertrag.

## 2 · Ein Endpunkt, vollständig

| Angabe | Ihr Endpunkt |
|---|---|
| Form | Felder und erlaubte Werte — sonst nichts |
| Fehlerfall | Statuscode und die eine Fehlerform |
| Wiederholung | was beim zweiten Mal passiert |
| Datenklasse | wer die Daten sehen darf |
| Zusage | eine Zahl mit Quelle — geraten zählt nicht |

Beispiel: `POST /api/tickets` · 201 Ticket / 200 dasselbe Ticket bei gleichem `Idempotency-Key` /
422 Fehlerform · personenbezogen · p95 < 300 ms (NfA-1).

## 3 · Ein Werkzeug für einen Agenten

| Werkzeug | Stufe (autonom · mit Freigabe · nicht angeboten) | was der Server prüft |
|---|---|---|
| … | … | … |

Gegenprobe: Steht die Prüfung im Server — oder nur in der Beschreibung des Werkzeugs?

## 4 · Das Mini-ADR — synchron oder asynchron

```markdown
**ADR-n · <Titel: der Entscheid in einem Satz>**
*Folgt aus:* <Qualitätsziel oder Anforderung>
*Entscheid:* <was wir tun — und was wir bewusst nicht tun>
*Preis:* <was uns der Entscheid kostet>
*Revidieren, wenn:* <die Bedingung, unter der wir neu prüfen>
```

Beispiel von heute (SPEC §8):

**ADR-3 · Klassifikation asynchron, entkoppelt vom Intake**
*Folgt aus:* Performance (5) — NfA-1 verlangt < 300 ms, ein LLM-Aufruf dauert länger.
*Entscheid:* Der Intake schreibt das Ticket und quittiert sofort; die Analyse läuft danach über eine
interne Warteschlange.
*Preis:* Das Dashboard zeigt kurz Tickets ohne Klassifikation — «offen» ist ein eigener Zustand;
fehlgeschlagene Analysen brauchen einen Wiederholmechanismus.
*Revidieren, wenn:* das Modell zuverlässig unter 200 ms antwortet.

Gegenprobe für alle vier Zeilen: Könnte eine fremde Person Ihren Vertrag prüfen, ohne Sie zu fragen?
