# platform/llm — der Port zum LLM (ADR-2)

| Datei | Was |
|---|---|
| `port.py` | die zwei Schnittstellen, die die Fachlogik kennt: `Classifier`, `ReplyDrafter` — und `ModellFehler` |
| `fake.py` | der Mock aus Block 2 hinter dem Port: feste Antworten, Testweichen `slow` · `fail` · `bad`. **Im Test immer er.** |
| `__init__.py` | `classifier()` und `drafter()` liefern den Adapter laut `.env` (`LLM=fake \| lokal \| cloud`) |

Die Adapter `lokal` (Ollama) und `cloud` (Anbieter mit Schlüssel) gibt es noch nicht —
beide über die OpenAI-kompatible API, derselbe Code mit anderer Adresse. Davor sitzt die Maskierung (ADR-4).

Der Fake liefert die **Werte des Mock** (Kategorie «Zugang», «Export» …), nicht die der SPEC — er spielt
den Mock, damit die Frontend-Tests aus Block 2 unverändert laufen. Ein echter Adapter liefert die
Kategorien aus SPEC §5.
