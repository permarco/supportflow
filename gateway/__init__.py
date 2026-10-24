"""Gateway: der eine Eingang für den Browser. Port 8765 — derselbe wie der Mock aus Block 2.

Liefert das Frontend (www/) aus und leitet /api/… an den zuständigen Dienst weiter. Das Frontend
und seine Tests merken nicht, dass es jetzt zwei Dienste sind. Keine Fachlogik.
"""
