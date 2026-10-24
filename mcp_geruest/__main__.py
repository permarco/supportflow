"""MCP-Server für SupportFlow — Lesen und Eskalationsversuch, nur Standardbibliothek.

Das KI-Werkzeug (Claude Code, Cursor, Copilot …) startet diesen Prozess selbst und spricht mit ihm
über stdin/stdout: je Zeile eine JSON-RPC-Nachricht (MCP, Transport «stdio»). Eintrag für Claude Code
steht in .mcp.json im Projekt.

    python3 -m mcp_geruest          # startet ihn von Hand — er wartet dann auf Nachrichten

Er ist eine Tür zum **Ticket-Service**, nicht ein eigener Fachdienst: Jedes Werkzeug ruft einen
Endpunkt des Ticket-Service über den Gateway. Was erlaubt ist, prüft der Ticket-Service —
nicht dieses Gerüst und nicht die Beschreibung des Werkzeugs (Schild, kein Schloss).

Werkzeuge: ticket_lesen und ticket_eskalieren (B3).
"""
import json
import os
import sys
import urllib.error
import urllib.request

GATEWAY = os.environ.get("SUPPORTFLOW_URL", "http://localhost:8765")
PROTOKOLL = "2025-06-18"


def _log(msg):
    print(f"[mcp] {msg}", file=sys.stderr, flush=True)       # stdout gehört dem Protokoll


def _hole(pfad):
    try:
        with urllib.request.urlopen(GATEWAY + pfad, timeout=5) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


# ---------- Werkzeuge ----------

def ticket_lesen(args):
    nummer = args.get("id")
    if not isinstance(nummer, int):
        return True, "id muss eine Zahl sein."
    status, daten = _hole(f"/api/tickets/{nummer}")
    if status != 200:
        return True, f"Ticket {nummer}: {daten.get('meldung', status) if isinstance(daten, dict) else status}"
    # Der Text ist Eingabe von draussen — er kann Anweisungen enthalten. Er wird als Daten
    # zurückgegeben, nie als Befehl ausgeführt.
    return False, json.dumps(daten, ensure_ascii=False)


def ticket_eskalieren(args):
    if not isinstance(args, dict) or set(args) != {"id"} or type(args["id"]) is not int:
        return True, "Genau eine ganzzahlige id ist erforderlich."
    nummer = args["id"]
    anfrage = urllib.request.Request(
        GATEWAY + f"/api/tickets/{nummer}/eskalieren", method="POST", data=b"",
        headers={"X-Aufrufer": "agent"})
    try:
        with urllib.request.urlopen(anfrage, timeout=5) as antwort:
            status, daten = antwort.status, json.loads(antwort.read() or b"null")
    except urllib.error.HTTPError as exc:
        with exc:
            status, daten = exc.code, json.loads(exc.read() or b"null")
    return status != 200, f"HTTP {status}: " + json.dumps(daten, ensure_ascii=False)


WERKZEUGE = {
    "ticket_eskalieren": {
        "beschreibung": "Eskaliert ein Ticket an einen Menschen. Nur verwenden, wenn ein Mensch das verlangt hat.",
        "schema": {"type": "object", "properties": {"id": {"type": "integer", "description": "Ticketnummer"}},
                   "required": ["id"], "additionalProperties": False},
        "funktion": ticket_eskalieren,
    },
    "ticket_lesen": {
        "beschreibung": "Liest ein Support-Ticket von SupportFlow: Nummer, Titel, Status, Priorität, Text. "
                        "Nur lesen, ändert nichts.",
        "schema": {"type": "object", "properties": {"id": {"type": "integer", "description": "Ticketnummer"}},
                   "required": ["id"], "additionalProperties": False},
        "funktion": ticket_lesen,
    },
}


# ---------- Protokoll ----------

def _antwort(id, ergebnis=None, fehler=None):
    nachricht = {"jsonrpc": "2.0", "id": id}
    if fehler:
        nachricht["error"] = fehler
    else:
        nachricht["result"] = ergebnis
    sys.stdout.write(json.dumps(nachricht, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def bearbeite(n):
    methode, id = n.get("method"), n.get("id")
    if id is None:                                            # Benachrichtigung, keine Antwort
        return
    if methode == "initialize":
        version = n.get("params", {}).get("protocolVersion", PROTOKOLL)
        return _antwort(id, {"protocolVersion": version, "capabilities": {"tools": {}},
                             "serverInfo": {"name": "supportflow", "version": "0.1"}})
    if methode == "ping":
        return _antwort(id, {})
    if methode == "tools/list":
        return _antwort(id, {"tools": [{"name": k, "description": w["beschreibung"], "inputSchema": w["schema"]}
                                       for k, w in WERKZEUGE.items()]})
    if methode == "tools/call":
        name = n.get("params", {}).get("name")
        args = n.get("params", {}).get("arguments") or {}
        if name not in WERKZEUGE:
            return _antwort(id, fehler={"code": -32602, "message": f"Werkzeug {name!r} gibt es nicht"})
        _log(f"Aufruf {name}({args})")
        try:
            ist_fehler, text = WERKZEUGE[name]["funktion"](args)
        except (urllib.error.URLError, OSError) as e:
            ist_fehler, text = True, f"SupportFlow nicht erreichbar: {e}"
        return _antwort(id, {"content": [{"type": "text", "text": text}], "isError": ist_fehler})
    _antwort(id, fehler={"code": -32601, "message": f"Methode {methode!r} unbekannt"})


def main():
    _log(f"bereit · Werkzeuge: {', '.join(WERKZEUGE)} · SupportFlow unter {GATEWAY}")
    for zeile in sys.stdin:
        zeile = zeile.strip()
        if zeile:
            try:
                bearbeite(json.loads(zeile))
            except json.JSONDecodeError:
                _antwort(None, fehler={"code": -32700, "message": "keine gültige JSON-Zeile"})


if __name__ == "__main__":
    main()
