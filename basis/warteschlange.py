"""Eine Warteschlange aus Dateien — sichtbar im Terminal, ohne Broker.

    from basis.warteschlange import sende, empfaenger

    sende("<thema>", {"id": 434, …})          # legt eine Datei ab

    @empfaenger("<thema>")                    # in nachrichten.py
    def bei_nachricht(nachricht): ...

Jedes Thema ist ein Ordner unter laufzeit/warteschlange/<thema>/, jede Nachricht eine JSON-Datei.
    ls laufzeit/warteschlange/<thema>/        # was wartet

Zustellung: MINDESTENS EINMAL. Eine Nachricht wird erst gelöscht, wenn der Empfänger fertig ist.
Stürzt er vorher ab, kommt sie beim nächsten Start wieder — also kann dieselbe Nachricht zweimal
kommen. Der Empfänger muss das aushalten (Idempotenz).
Scheitert der Empfänger dreimal, wandert die Nachricht nach _fehlgeschlagen/ statt im Kreis zu laufen.
Ein echter Vermittler (RabbitMQ, Kafka, …) tut dasselbe, nur robuster und über Rechner hinweg.
"""
import json
import os
import threading
import time
import uuid

from basis.http import log

ORDNER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "laufzeit", "warteschlange")
MAX_VERSUCHE = 3
_EMPFAENGER = {}      # thema -> funktion


def _thema_ordner(thema):
    pfad = os.path.join(ORDNER, thema)
    os.makedirs(pfad, exist_ok=True)
    return pfad


def sende(thema, nachricht):
    """Legt eine Nachricht ab und kehrt sofort zurück — der Absender wartet nicht."""
    pfad = _thema_ordner(thema)
    name = f"{time.time():.6f}-{uuid.uuid4().hex[:8]}"
    umschlag = {"id": name, "thema": thema, "versuche": 0, "inhalt": nachricht}
    tmp = os.path.join(pfad, name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(umschlag, f, ensure_ascii=False)
    os.replace(tmp, os.path.join(pfad, name + ".json"))       # erst jetzt sichtbar
    log(f"→ Warteschlange «{thema}» ({name})")
    return name


def empfaenger(thema):
    """Registriert eine Funktion, die Nachrichten eines Themas verarbeitet."""
    def deko(f):
        _EMPFAENGER[thema] = f
        return f
    return deko


def _schleife(thema, f):
    pfad = _thema_ordner(thema)
    fehl = os.path.join(pfad, "_fehlgeschlagen")
    # was beim letzten Mal in Arbeit war, kommt zurück (mindestens einmal)
    for datei in os.listdir(pfad):
        if datei.endswith(".inarbeit"):
            os.replace(os.path.join(pfad, datei), os.path.join(pfad, datei[:-len(".inarbeit")] + ".json"))
    while True:
        for datei in sorted(d for d in os.listdir(pfad) if d.endswith(".json")):
            quelle = os.path.join(pfad, datei)
            arbeit = quelle[:-len(".json")] + ".inarbeit"
            try:
                os.replace(quelle, arbeit)                      # die Nachricht gehört jetzt uns
            except FileNotFoundError:
                continue
            with open(arbeit, encoding="utf-8") as h:
                umschlag = json.load(h)
            try:
                f(umschlag["inhalt"])
                os.remove(arbeit)
                log(f"← Warteschlange «{thema}» verarbeitet ({umschlag['id']})")
            except Exception as e:                              # noqa: BLE001
                umschlag["versuche"] += 1
                umschlag["letzter_fehler"] = repr(e)
                if umschlag["versuche"] >= MAX_VERSUCHE:
                    os.makedirs(fehl, exist_ok=True)
                    ziel = os.path.join(fehl, umschlag["id"] + ".json")
                    log(f"✗ Warteschlange «{thema}»: {umschlag['id']} nach {MAX_VERSUCHE} Versuchen → _fehlgeschlagen/")
                else:
                    ziel = quelle
                    log(f"✗ Warteschlange «{thema}»: {umschlag['id']} Versuch {umschlag['versuche']} — {e!r}")
                with open(arbeit, "w", encoding="utf-8") as h:
                    json.dump(umschlag, h, ensure_ascii=False)
                os.replace(arbeit, ziel)
        time.sleep(0.2)


def starte_empfaenger(dienst):
    for thema, f in _EMPFAENGER.items():
        threading.Thread(target=_schleife, args=(thema, f), daemon=True, name=f"{dienst}:{thema}").start()
        log(f"hört auf Warteschlange «{thema}»")
