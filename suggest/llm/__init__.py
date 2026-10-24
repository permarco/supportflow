"""Port und Adapter zum LLM (ADR-2). Die Fachlogik holt sich den Adapter hier — nie direkt.

    from suggest.llm import classifier, drafter
    einschaetzung = classifier().klassifiziere(ticket)
    for wort in drafter().entwerfe(ticket): ...

Welcher Adapter antwortet, steht in .env: LLM=fake (Tests, Standard) | lokal | cloud.
Die Adapter «lokal» und «cloud» gibt es noch nicht.
"""
import os

from suggest.llm.port import Classifier, ModellFehler, ReplyDrafter  # noqa: F401

_ADAPTER = None


def _adapter():
    global _ADAPTER
    if _ADAPTER is None:
        wahl = os.environ.get("LLM", "fake")
        if wahl == "fake":
            from suggest.llm.fake import FakeLLM
            _ADAPTER = FakeLLM()
        else:
            raise ModellFehler(f"LLM={wahl}: diesen Adapter gibt es noch nicht")
    return _ADAPTER


def classifier() -> Classifier:
    return _adapter()


def drafter() -> ReplyDrafter:
    return _adapter()
