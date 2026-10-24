"""Gemeinsame Fehlerform: öffentliche Meldung, interne Details nur im korrelierten Log."""
import uuid


def fehlerdaten(code, meldung, intern, logger):
    korrelation = uuid.uuid4().hex[:12]
    logger(f"[{korrelation}] {code}: {intern}")
    return {"code": code, "meldung": meldung, "korrelation": korrelation}


def fehler(code, meldung, status, intern):
    # Lokaler Import vermeidet einen Importzyklus mit dem HTTP-Router.
    from basis.http import json_antwort, log

    return json_antwort(fehlerdaten(code, meldung, intern, log), status)
