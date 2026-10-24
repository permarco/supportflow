"""Der Port zum LLM (ADR-2). Die Fachlogik kennt nur diese zwei Schnittstellen — nie einen Anbieter.

Welcher Adapter dahinter antwortet, entscheidet LLM=fake | lokal | cloud in .env (siehe __init__.py).
Im Test antwortet immer der Fake.
"""
from typing import Iterator, Protocol


class ModellFehler(Exception):
    """Das Modell hat nicht oder unbrauchbar geantwortet. Das System bleibt nutzbar (FR-2)."""


class Classifier(Protocol):
    def klassifiziere(self, ticket: dict, weichen: dict | None = None) -> dict:
        """Einschätzung zu einem Ticket: {kategorie, prioritaet, aktionen[], begruendung}.

        Die Antwort ist Modellausgabe — der Service prüft sie, bevor sie Wirkung entfaltet (SPEC §9).
        `weichen` kennt nur der Fake (Testweichen des Mock aus Block 2: bad=1)."""


class ReplyDrafter(Protocol):
    def entwerfe(self, ticket: dict, weichen: dict | None = None) -> Iterator[str]:
        """Antwortentwurf, Wort für Wort — so, wie das Modell ihn erzeugt.

        Bricht der Empfänger ab, wird der Iterator geschlossen; der Adapter hört dann auf.
        `weichen` kennt nur der Fake (slow=1, fail=1). Fehler: ModellFehler."""
