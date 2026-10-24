"""Startet einen Dienst: .env lesen, alle routes.py seiner Pakete laden, Server starten.

    python3 -m tickets     # benutzt dienst.starte("tickets", 8766)

Jedes Paket eines Dienstes darf eine Datei routes.py haben (Endpunkte mit @route) und eine Datei
nachrichten.py (Empfänger aus der Warteschlange mit @empfaenger). Beides wird beim Start geladen.
"""
import importlib
import pkgutil

from basis import http, warteschlange
from basis.konfig import lade_env


def _lade(paketname, modul):
    paket = importlib.import_module(paketname)
    for info in pkgutil.iter_modules(paket.__path__):
        name = f"{paketname}.{info.name}.{modul}"
        try:
            importlib.import_module(name)
        except ModuleNotFoundError as e:
            if e.name != name:
                raise


def starte(name, port):
    http._NAME = name
    lade_env()
    _lade(name, "routes")
    _lade(name, "nachrichten")
    warteschlange.starte_empfaenger(name)
    http.starte(port, name)
