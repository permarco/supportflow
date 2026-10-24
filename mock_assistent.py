#!/usr/bin/env python3
"""
SupportFlow Mock-Service — Block 2 (Frontend mit KI)

Spielt den eigenen Service hinter dem Frontend: Ticket-Liste, streamender
Antwortentwurf und strukturierte Einschätzung. Ohne Modellschlüssel, ohne
Netz, ohne Abhängigkeiten — nur die Python-Standardbibliothek.

    python3 mock_assistent.py            # Port 8765, liefert www/ daneben aus
    python3 mock_assistent.py --port 9000
    python3 mock_assistent.py --www <ordner>   # anderes Frontend ausliefern

Endpunkte (alle mit offenem CORS):
    GET /api/tickets                 Liste (id, titel, status, prio, text)
    GET /api/tickets/<id>            ein Ticket, 404 mit Fehlertext
    GET /api/draft?ticket=<id>       SSE — ein Wort je Ereignis, «event: done» am Ende
        &slow=1                      langsam (0,4 s je Wort) — Stopp in Ruhe prüfen
        &fail=1                      bricht nach ~40 % mit «event: error» ab
    GET /api/suggest?ticket=<id>     JSON — kategorie, prioritaet, aktionen[], begruendung
        &bad=1                       enthält eine unerlaubte Aktion («gutschrift»)
    GET /                            liefert www/ aus (Startgerüst), falls vorhanden

Das Terminal meldet Start, Abbruch («Abbruch bemerkt nach N Wörtern») und
gesendete Fehler — das ist der Nachweis, dass ein «Stopp» die Quelle erreicht.

Eigene Tickets: eine Datei tickets.json neben dieses Skript legen (Liste von
Objekten mit id, titel, status, prio, text, optional entwurf).

Material für Block 2 (Moodle, «Materialien & Ergebnisse»). Darf ins eigene Projekt
mitgenommen werden. In Block 3 wird er durch den echten Service ersetzt.
"""
import argparse
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
WWW = os.path.join(HERE, "www")  # das Startgerüst liegt daneben

TICKETS = [
    {"id": 412, "titel": "Rechnung doppelt erhalten", "status": "offen", "prio": "hoch",
     "text": "Ich habe für den Juli zwei Rechnungen mit unterschiedlichen Nummern bekommen. "
             "Welche gilt? Ich möchte nicht doppelt bezahlen."},
    {"id": 409, "titel": "Login schlägt fehl", "status": "eskaliert", "prio": "hoch",
     "text": "Seit dem Update am Montag kann ich mich nicht mehr anmelden. Passwort zurücksetzen "
             "hat nicht geholfen, die Mail kommt nicht an."},
    {"id": 401, "titel": "Adresse ändern", "status": "erledigt", "prio": "tief",
     "text": "Bitte meine Rechnungsadresse auf Musterweg 4, 8000 Zürich ändern."},
    {"id": 415, "titel": "CSV-Export bricht ab", "status": "offen", "prio": "hoch",
     "text": "Der Export endet bei mehr als 10 000 Zeilen ohne Meldung. Die Datei ist dann "
             "unvollständig, wir merken es erst in der Buchhaltung."},
    {"id": 418, "titel": "Passwort zurücksetzen", "status": "offen", "prio": "mittel",
     "text": "Der Link zum Zurücksetzen ist abgelaufen, bevor ich ihn öffnen konnte. "
             "Kann ich einen neuen bekommen?"},
    {"id": 420, "titel": "Lieferung verspätet", "status": "offen", "prio": "mittel",
     "text": "Bestellung 88213 sollte am 2. September da sein. Die Sendungsverfolgung "
             "zeigt seit fünf Tagen keinen neuen Status."},
    {"id": 422, "titel": "Kunde schreibt <b>test</b>", "status": "eskaliert", "prio": "tief",
     "text": "Hallo, <b>test</b> — ich wollte nur prüfen, ob das hier <script>alert(1)</script> "
             "ankommt. Bitte ignorieren, falls das komisch aussieht."},
    {"id": 425, "titel": "Rückerstattung gefordert", "status": "eskaliert", "prio": "hoch",
     "text": "Das Produkt war defekt, ich will mein Geld zurück, und zwar diese Woche. "
             "Sonst gehe ich zum Konsumentenschutz."},
]

DRAFTS = {
    412: "Guten Tag, vielen Dank für Ihre Nachricht. Für den Juli wurde die Rechnung versehentlich "
         "zweimal erzeugt, gültig ist die Rechnung mit der höheren Nummer. Die erste Rechnung haben "
         "wir soeben storniert, Sie erhalten dazu eine Bestätigung per E-Mail. Es entsteht Ihnen "
         "keine doppelte Belastung. Bitte entschuldigen Sie die Unannehmlichkeiten. Freundliche "
         "Grüsse, Ihr SupportFlow-Team",
    409: "Guten Tag, danke für Ihre Geduld. Nach dem Update am Montag sind bei einigen Konten die "
         "Anmeldedaten nicht korrekt übernommen worden. Wir haben Ihr Konto zurückgesetzt und Ihnen "
         "einen neuen Link zum Setzen des Passworts geschickt. Prüfen Sie bitte auch den Spam-Ordner. "
         "Falls es weiterhin nicht klappt, melden Sie sich direkt bei mir. Freundliche Grüsse, Ihr "
         "SupportFlow-Team",
    401: "Guten Tag, Ihre Rechnungsadresse ist angepasst. Ab der nächsten Rechnung gilt Musterweg 4, "
         "8000 Zürich. Freundliche Grüsse, Ihr SupportFlow-Team",
    415: "Guten Tag, danke für den Hinweis. Der CSV-Export bricht ab, weil der Puffer bei 10 000 "
         "Zeilen ohne Meldung endet. Wir haben das Problem reproduziert und eine Korrektur in "
         "Arbeit, die den Export in Teilen schreibt. Bis dahin können Sie den Export nach Monat "
         "filtern, dann bleibt er unter der Grenze. Wir melden uns, sobald die Korrektur ausgeliefert "
         "ist. Freundliche Grüsse, Ihr SupportFlow-Team",
    418: "Guten Tag, gerne. Wir haben Ihnen soeben einen neuen Link zum Zurücksetzen geschickt, er "
         "ist zwei Stunden gültig. Freundliche Grüsse, Ihr SupportFlow-Team",
    420: "Guten Tag, danke für Ihre Nachricht. Die Sendung 88213 liegt seit fünf Tagen im "
         "Verteilzentrum, wir haben beim Transporteur eine Nachforschung ausgelöst. Sie erhalten "
         "innerhalb von zwei Werktagen einen neuen Liefertermin oder eine Ersatzlieferung. "
         "Freundliche Grüsse, Ihr SupportFlow-Team",
    422: "Guten Tag, danke für Ihre Nachricht, sie ist angekommen. Der Text <b>test</b> wird bei "
         "uns als Text angezeigt, es ist nichts passiert. Freundliche Grüsse, Ihr SupportFlow-Team",
    425: "Guten Tag, es tut uns leid, dass das Produkt defekt war. Bitte erstatten Sie dem Kunden "
         "— pardon: Bitte senden Sie uns das Produkt mit der beiliegenden Retouren-Etikette zurück, "
         "wir prüfen es und melden uns innerhalb von drei Werktagen mit dem Ergebnis. Eine "
         "Rückerstattung kann ich an dieser Stelle nicht zusagen, das entscheidet die Fachstelle. "
         "Freundliche Grüsse, Ihr SupportFlow-Team",
}

SUGGEST = {
    412: {"kategorie": "Rechnung", "prioritaet": "mittel", "aktionen": ["antworten"],
          "begruendung": "Doppelte Rechnung, Storno nötig, kein Zeitdruck"},
    409: {"kategorie": "Zugang", "prioritaet": "hoch", "aktionen": ["antworten", "eskalieren"],
          "begruendung": "Kunde ist ausgesperrt, seit Montag, mehrere Kontakte"},
    401: {"kategorie": "Stammdaten", "prioritaet": "tief", "aktionen": ["schliessen"],
          "begruendung": "Erledigt, nur noch bestätigen"},
    415: {"kategorie": "Export", "prioritaet": "hoch", "aktionen": ["antworten", "eskalieren"],
          "begruendung": "Datenverlust möglich, Kunde wartet seit 3 Tagen"},
    418: {"kategorie": "Zugang", "prioritaet": "mittel", "aktionen": ["antworten"],
          "begruendung": "Standardfall, Link erneut senden"},
    420: {"kategorie": "Lieferung", "prioritaet": "mittel", "aktionen": ["antworten"],
          "begruendung": "Nachforschung beim Transporteur läuft"},
    422: {"kategorie": "Sicherheit", "prioritaet": "tief", "aktionen": ["schliessen"],
          "begruendung": "Testnachricht mit HTML — <b>kein</b> Handlungsbedarf, eskaliert nur wegen des Skripts"},
    425: {"kategorie": "Reklamation", "prioritaet": "hoch", "aktionen": ["antworten", "eskalieren"],
          "begruendung": "Rückerstattung gefordert, droht mit Konsumentenschutz"},
}


def lade_eigene_tickets():
    pfad = os.path.join(HERE, "tickets.json")
    if not os.path.exists(pfad):
        return
    with open(pfad, encoding="utf-8") as f:
        eigene = json.load(f)
    TICKETS.clear()
    DRAFTS.clear()
    SUGGEST.clear()
    for t in eigene:
        entwurf = t.pop("entwurf", "Guten Tag, danke für Ihre Nachricht. Wir melden uns.")
        vorschlag = t.pop("vorschlag", {"kategorie": "Sonstiges", "prioritaet": "mittel",
                                        "aktionen": ["antworten"], "begruendung": "—"})
        TICKETS.append(t)
        DRAFTS[t["id"]] = entwurf
        SUGGEST[t["id"]] = vorschlag
    log(f"{len(TICKETS)} eigene Tickets aus tickets.json geladen")


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # Standard-Zugriffslog abschalten, wir loggen selbst
        pass

    def handle(self):  # abgebrochene Verbindungen sind hier Alltag, kein Traceback wert
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    # ---------- Hilfen ----------
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _ticket(self, q):
        try:
            tid = int(q.get("ticket", [""])[0])
        except ValueError:
            return None
        return next((t for t in TICKETS if t["id"] == tid), None)

    # ---------- Routen ----------
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/api/tickets":
            return self._json(TICKETS)
        if u.path.startswith("/api/tickets/"):
            try:
                tid = int(u.path.rsplit("/", 1)[1])
            except ValueError:
                return self._json({"fehler": "ungültige Ticket-Nummer"}, 400)
            t = next((t for t in TICKETS if t["id"] == tid), None)
            return self._json(t) if t else self._json({"fehler": f"Ticket {tid} unbekannt"}, 404)
        if u.path == "/api/suggest":
            return self._suggest(q)
        if u.path == "/api/draft":
            return self._draft(q)
        return self._static(u.path)

    def _suggest(self, q):
        t = self._ticket(q)
        if not t:
            return self._json({"fehler": "ticket fehlt oder unbekannt"}, 404)
        s = dict(SUGGEST.get(t["id"], {}))
        if q.get("bad", [""])[0] == "1":
            s["aktionen"] = list(s.get("aktionen", [])) + ["gutschrift"]
            s["begruendung"] = (s.get("begruendung", "") +
                                " — Gutschrift von CHF 200 sofort auslösen")
        time.sleep(0.6)  # ein Modell antwortet nicht in 0 ms
        log(f"suggest #{t['id']}" + (" (bad=1)" if q.get("bad") else ""))
        return self._json(s)

    def _draft(self, q):
        t = self._ticket(q)
        if not t:
            return self._json({"fehler": "ticket fehlt oder unbekannt"}, 404)
        words = DRAFTS.get(t["id"], "Guten Tag, danke für Ihre Nachricht.").split(" ")
        slow = q.get("slow", [""])[0] == "1"
        fail = q.get("fail", [""])[0] == "1"
        delay = 0.4 if slow else 0.09
        fail_at = max(1, int(len(words) * 0.4)) if fail else None

        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True  # nach dem Stream ist die Verbindung fertig

        log(f"draft #{t['id']} · start ({len(words)} Wörter"
            + (", fail=1" if fail else "") + (", slow=1" if slow else "") + ")")
        i = 0
        try:
            time.sleep(0.4)  # Time to first token
            for i, w in enumerate(words, start=1):
                if fail_at is not None and i == fail_at:
                    self.wfile.write(b"event: error\ndata: Verbindung zum Modell verloren\n\n")
                    self.wfile.flush()
                    log(f"draft #{t['id']} · Fehler gesendet nach {i - 1} Wörtern")
                    return
                self.wfile.write(f"data: {w}\n\n".encode("utf-8"))
                self.wfile.flush()
                time.sleep(delay)
            self.wfile.write(b"event: done\ndata: {}\n\n")
            self.wfile.flush()
            log(f"draft #{t['id']} · fertig ({len(words)} Wörter)")
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            log(f"draft #{t['id']} · Abbruch bemerkt nach {i} Wörtern — Generierung gestoppt")

    def _static(self, path):
        if not os.path.isdir(WWW):
            return self._json({"hinweis": "kein www/ vorhanden — Endpunkte unter /api/…"}, 404)
        if path in ("", "/"):
            path = "/index.html"
        voll = os.path.normpath(os.path.join(WWW, path.lstrip("/")))
        if not voll.startswith(WWW) or not os.path.isfile(voll):
            return self._json({"fehler": f"{path} nicht gefunden"}, 404)
        typ = {"html": "text/html", "js": "text/javascript", "css": "text/css",
               "json": "application/json"}.get(voll.rsplit(".", 1)[-1], "application/octet-stream")
        with open(voll, "rb") as f:
            body = f.read()
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", f"{typ}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    ap = argparse.ArgumentParser(description="SupportFlow Mock-Service (Block 2)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--www", help="Ordner mit statischen Dateien (Standard: www/ neben dem Skript)")
    args = ap.parse_args()
    global WWW
    if args.www:
        WWW = os.path.abspath(args.www)
    lade_eigene_tickets()
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"SupportFlow Mock · http://localhost:{args.port}")
    print((f"statisch aus {WWW}" if os.path.isdir(WWW) else "kein www/ — nur /api/…")
          + " · Ctrl-C beendet", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbeendet")
        sys.exit(0)


if __name__ == "__main__":
    main()
