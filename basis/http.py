"""Kleiner HTTP-Rahmen aus der Standardbibliothek: Router, JSON, Server-Sent Events.

Jeder Dienst (tickets, suggest) ist ein eigener Prozess mit eigenem Port und benutzt diesen Rahmen.

Ein Endpunkt ist eine Funktion mit @route("GET", "/api/tickets/{id}"). Sie bekommt eine Anfrage
und gibt eine Antwort zurück — json_antwort(), text_antwort() oder Strom() für SSE.
Nichts hier kennt Tickets. Das ist Sache der Dienste.

    from basis.http import route, json_antwort

    @route("GET", "/api/hallo/{name}")
    def hallo(anfrage):
        return json_antwort({"hallo": anfrage.params["name"]})
"""
import json
import os
import re
import time
import traceback
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

_ROUTEN = []          # (methode, pfad, regex, funktion)
_NAME = "service"     # Name des Dienstes im Log


def log(msg):
    print(time.strftime("%H:%M:%S"), f"[{_NAME}]", msg, flush=True)


# ---------- Routen ----------

def route(methode, pfad):
    """Registriert eine Funktion für Methode und Pfad. {name} im Pfad wird zu anfrage.params[name]."""
    regex = re.compile("^" + re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", pfad) + "$")

    def deko(f):
        _ROUTEN.append((methode.upper(), pfad, regex, f))
        return f
    return deko


def routen():
    """Alle registrierten Routen — für Übersicht und Tests."""
    return [(m, p) for m, p, _, _ in _ROUTEN]


# ---------- Anfrage und Antwort ----------

@dataclass
class Anfrage:
    methode: str
    pfad: str
    query: dict        # {"ticket": "415"} — je Schlüssel der erste Wert
    params: dict       # aus dem Pfadmuster, z. B. {"id": "415"}
    headers: dict      # Schlüssel kleingeschrieben
    rumpf: bytes

    def json(self):
        return json.loads(self.rumpf or b"null")


@dataclass
class Antwort:
    status: int = 200
    body: bytes = b""
    typ: str = "application/json; charset=utf-8"
    headers: dict = field(default_factory=dict)


def json_antwort(obj, status=200, headers=None):
    return Antwort(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   headers=headers or {})


def text_antwort(text, status=200, typ="text/plain; charset=utf-8"):
    return Antwort(status, text.encode("utf-8"), typ)


class Strom:
    """Server-Sent Events. `ereignisse` liefert Paare (event, data); event None = nur data.

        def woerter():
            for w in text.split(" "):
                yield None, w
            yield "done", "{}"
        return Strom(woerter())

    Bricht der Empfänger ab, wird der Generator geschlossen und der Abbruch im Log vermerkt —
    so hört auch das dahinterliegende Modell auf zu rechnen.
    """

    def __init__(self, ereignisse):
        self.ereignisse = ereignisse


# ---------- Server ----------

class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):          # eigenes Log statt Standard-Zugriffslog
        pass

    def handle(self):                      # abgebrochene Verbindungen sind Alltag, kein Traceback wert
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def do_GET(self):
        self._bearbeite("GET")

    def do_POST(self):
        self._bearbeite("POST")

    def do_PUT(self):
        self._bearbeite("PUT")

    def do_DELETE(self):
        self._bearbeite("DELETE")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")

    def _bearbeite(self, methode):
        u = urlparse(self.path)
        laenge = int(self.headers.get("Content-Length") or 0)
        rumpf = self.rfile.read(laenge) if laenge else b""
        query = {k: v[0] for k, v in parse_qs(u.query).items()}
        headers = {k.lower(): v for k, v in self.headers.items()}

        for m, _, regex, f in _ROUTEN:
            treffer = regex.match(u.path)
            if m == methode and treffer:
                anfrage = Anfrage(methode, u.path, query, treffer.groupdict(), headers, rumpf)
                try:
                    antwort = f(anfrage)
                except Exception as e:                       # noqa: BLE001
                    # Entwicklungsmodus aus dem Vorprojekt: Fehler samt Ablauf zurückgeben
                    log(f"{methode} {u.path} → 500 {e!r}")
                    antwort = json_antwort({"error": repr(e), "trace": traceback.format_exc()}, 500)
                return self._sende(antwort, anfrage)

        self._sende(json_antwort({"error": f"{methode} {u.path} nicht gefunden"}, 404))

    def _sende(self, antwort, anfrage=None):
        if isinstance(antwort, Strom):
            return self._strom(antwort, anfrage)
        if not isinstance(antwort, Antwort):
            raise TypeError(f"Endpunkt muss eine Antwort oder einen Strom zurückgeben, nicht {type(antwort).__name__}")
        self.send_response(antwort.status)
        self._cors()
        self.send_header("Content-Type", antwort.typ)
        self.send_header("Content-Length", str(len(antwort.body)))
        for k, v in antwort.headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(antwort.body)
        if anfrage:
            log(f"{anfrage.methode} {anfrage.pfad} → {antwort.status}")

    def _strom(self, strom, anfrage):
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        pfad = anfrage.pfad if anfrage else "?"
        log(f"GET {pfad} → Strom beginnt")
        n = 0
        ereignisse = iter(strom.ereignisse)
        try:
            for event, data in ereignisse:
                zeile = (f"event: {event}\n" if event else "") + f"data: {data}\n\n"
                self.wfile.write(zeile.encode("utf-8"))
                self.wfile.flush()
                n += 1
            log(f"GET {pfad} → Strom fertig ({n} Ereignisse)")
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            log(f"GET {pfad} → Strom abgebrochen nach {n} Ereignissen — Generierung gestoppt")
        finally:
            schliessen = getattr(ereignisse, "close", None)
            if schliessen:
                schliessen()

def starte(port, name):
    """Startet den Dienst; blockiert bis Ctrl-C."""
    global _NAME
    _NAME = name
    srv = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    log(f"http://localhost:{port} · Routen: {', '.join(m + ' ' + p for m, p in routen()) or 'noch keine'}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
