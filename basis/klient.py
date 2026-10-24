"""Ein Dienst ruft einen anderen — synchron, mit Zeitgrenze.

    from basis.klient import hole_json, DienstNichtErreichbar
    status, daten = hole_json("http://localhost:8766/api/tickets/409")

Jeder Aufruf über das Netz kann ausbleiben. Deshalb endet er nach `zeitgrenze` Sekunden,
und «nicht erreichbar» ist ein eigener Fehler — kein 500 mit Stacktrace.
"""
import json
import urllib.error
import urllib.request


class DienstNichtErreichbar(Exception):
    """Der andere Dienst antwortet nicht (aus, zu langsam, Netz weg)."""


def hole_json(url, zeitgrenze=2.0):
    """GET auf einen anderen Dienst. Gibt (status, json) zurück; 4xx/5xx sind Antworten, keine Ausnahmen."""
    try:
        with urllib.request.urlopen(url, timeout=zeitgrenze) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"null")
        except ValueError:
            return e.code, None
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        raise DienstNichtErreichbar(f"{url}: {e}") from e
