"""Suggest-Service: Einschätzung und Antwortentwurf — alles, was ein LLM braucht. Port 8767.

Eigener Dienst, weil er einen eigenen Änderungsgrund und ein eigenes Profil hat: Sekunden statt
Millisekunden, Kosten je Aufruf, Modell und Regeln ändern sich oft (SPEC ADR-1, revidiert).
Das LLM liegt hinter dem Port in llm/ (ADR-2).
"""
