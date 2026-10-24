"""python3 -m gateway — Eingang auf Port 8765 (einzeln; normal: ./service.sh).

Weiterleitung (Präfix → Dienst):
    /api/tickets   → Ticket-Service  :8766
    /api/suggest   → Suggest-Service :8767
    /api/draft     → Suggest-Service :8767
Ströme (text/event-stream) werden Zeile für Zeile durchgereicht. Bricht der Browser ab, schliesst
der Gateway die Verbindung zum Dienst — der Abbruch erreicht die Quelle (wie in Block 2).
"""
import http.client
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from basis.fehler import fehlerdaten

WEITERLEITUNG = [
    ("/api/tickets", ("127.0.0.1", 8766)),
    ("/api/suggest", ("127.0.0.1", 8767)),
    ("/api/draft", ("127.0.0.1", 8767)),
]
WWW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "www")
DURCHREICHEN = {"content-type", "idempotency-key", "accept"}


def log(msg):
    print(time.strftime("%H:%M:%S"), "[gateway]", msg, flush=True)


def ziel(pfad):
    for praefix, adresse in WEITERLEITUNG:
        if pfad == praefix or pfad.startswith(praefix + "/"):
            return adresse
    return None


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def do_GET(self):
        self._weiter("GET")

    def do_POST(self):
        self._weiter("POST")

    def do_PUT(self):
        self._weiter("PUT")

    def do_DELETE(self):
        self._weiter("DELETE")

    def _json(self, status, obj, intern=None):
        obj = fehlerdaten(obj["code"], obj["meldung"], intern or self.path, log)
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _weiter(self, methode):
        pfad = urlparse(self.path).path
        adresse = ziel(pfad)
        if adresse is None:
            if methode == "GET" and not pfad.startswith("/api/"):
                return self._statisch(pfad)
            return self._json(404, {"code": "pfad_unbekannt", "meldung": "Diesen Endpunkt gibt es nicht."})
        laenge = int(self.headers.get("Content-Length") or 0)
        rumpf = self.rfile.read(laenge) if laenge else None
        kopf = {k: v for k, v in self.headers.items() if k.lower() in DURCHREICHEN}
        verbindung = http.client.HTTPConnection(*adresse, timeout=30)
        try:
            verbindung.request(methode, self.path, body=rumpf, headers=kopf)
            antwort = verbindung.getresponse()
            typ = antwort.getheader("Content-Type", "")
            if not typ.startswith("text/event-stream"):
                body = antwort.read()
        except (OSError, http.client.HTTPException) as exc:
            verbindung.close()
            return self._json(503, {"code": "dienst_nicht_erreichbar",
                                    "meldung": "Der Dienst ist gerade nicht erreichbar."},
                              intern=f"{methode} {pfad} → :{adresse[1]}: {exc!r}")
        if typ.startswith("text/event-stream"):
            return self._strom(antwort, verbindung, pfad, adresse)
        verbindung.close()
        self.send_response(antwort.status)
        self.send_header("Content-Type", typ or "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        log(f"{methode} {pfad} → :{adresse[1]} → {antwort.status}")

    def _strom(self, antwort, verbindung, pfad, adresse):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        log(f"GET {pfad} → :{adresse[1]} → Strom")
        try:
            while True:
                zeile = antwort.readline()
                if not zeile:
                    break
                self.wfile.write(zeile)
                if zeile in (b"\n", b"\r\n"):
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            log(f"GET {pfad} → Browser hat abgebrochen — Verbindung zum Dienst geschlossen")
        finally:
            verbindung.close()

    def _statisch(self, pfad):
        if pfad in ("", "/"):
            pfad = "/index.html"
        voll = os.path.normpath(os.path.join(WWW, pfad.lstrip("/")))
        if not voll.startswith(WWW) or not os.path.isfile(voll):
            return self._json(404, {"code": "datei_unbekannt", "meldung": f"{pfad} nicht gefunden"})
        typ = {"html": "text/html", "js": "text/javascript", "css": "text/css",
               "json": "application/json"}.get(voll.rsplit(".", 1)[-1], "application/octet-stream")
        with open(voll, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", f"{typ}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    log("http://localhost:8765 · Frontend aus www/ · "
        + " · ".join(f"{p} → :{a[1]}" for p, a in WEITERLEITUNG))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
