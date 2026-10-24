import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from tickets.audit import protokoll
from tickets.escalation.routes import eskalieren
from tickets.speicher import attrappe
from gateway.__main__ import Handler


class EskalierenTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.datei = Path(self.tmp.name) / "audit.jsonl"
        for p in [patch.object(protokoll, "DATEI", self.datei),
                  patch.object(attrappe, "_TICKETS", [{"id": 412, "titel": "Test",
                      "text": "Test", "status": "offen", "prio": "hoch"}])]:
            p.start()
            self.addCleanup(p.stop)

    def aufruf(self, rolle, nummer="412"):
        return eskalieren(SimpleNamespace(params={"id": nummer},
            headers={} if rolle is None else {"x-aufrufer": rolle}))

    def audit(self):
        return [json.loads(zeile) for zeile in self.datei.read_text(encoding="utf-8").splitlines()]

    def test_mensch_und_wiederholung(self):
        for _ in range(2):
            r = self.aufruf("mensch")
            self.assertEqual(r.status, 200)
            self.assertEqual(json.loads(r.body)["status"], "eskaliert")
        self.assertEqual(len(self.audit()), 2)
        self.assertEqual(self.audit()[0]["entscheidung"], "freigegeben")
        self.assertIn("zeitpunkt", self.audit()[0])

    def test_unberechtigte_ohne_wirkung(self):
        for rolle in ["agent", None, "admin", "Mensch", ""]:
            with self.subTest(rolle=rolle):
                r = self.aufruf(rolle)
                self.assertEqual(r.status, 403)
                self.assertEqual(set(json.loads(r.body)), {"code", "meldung", "korrelation"})
                self.assertEqual(attrappe.Attrappe().finde(412)["status"], "offen")
        self.assertEqual(len(self.audit()), 5)
        self.assertTrue(all(e["entscheidung"] == "abgewiesen" for e in self.audit()))

    def test_unbekannt_und_ungueltig(self):
        for nummer in ["99999", "abc"]:
            self.assertEqual(self.aufruf("mensch", nummer).status, 404)
            self.assertEqual(self.aufruf("agent", nummer).status, 403)
        self.assertEqual(len(self.audit()), 4)

    def test_audit_ausfall_verhindert_statusaenderung(self):
        with patch("tickets.escalation.routes.protokolliere", side_effect=OSError("Test")):
            self.assertEqual(self.aufruf("mensch").status, 503)
        self.assertEqual(attrappe.Attrappe().finde(412)["status"], "offen")

    def test_gateway_reicht_header_durch(self):
        handler = object.__new__(Handler)
        handler.path = "/api/tickets/412/eskalieren"
        handler.headers = {"X-Aufrufer": "agent"}
        handler.wfile = io.BytesIO()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        with patch("gateway.__main__.http.client.HTTPConnection") as connection:
            response = connection.return_value.getresponse.return_value
            response.getheader.return_value = "application/json"
            response.read.return_value = b"{}"
            response.status = 403
            handler._weiter("POST")
            self.assertEqual(connection.return_value.request.call_args.kwargs["headers"]["X-Aufrufer"], "agent")
            handler.send_response.assert_called_once_with(403)
