"""Service-Regel unabhängig vom Modell und über beide Eintrittspunkte prüfen."""
import json
import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

from suggest.classification.regeln import wende_regeln_an
from suggest.classification.routes import einschaetzung
from suggest.classification.nachrichten import bei_eingereicht
from tickets.speicher import attrappe


class RueckerstattungTest(unittest.TestCase):
    def setUp(self):
        self.modell = {"kategorie": "Sonstiges", "prioritaet": "tief",
                       "aktionen": ["schliessen"], "begruendung": "Erledigt."}
        self.ticket = {"id": 999, "titel": "Rückerstattung",
                       "text": "Bitte erstatten Sie meinen Kauf nach meiner Rückgabe."}

    def test_offene_faelle(self):
        for text in [self.ticket["text"], "Ich möchte mein Geld zurück.",
                     "Bitte um Erstattung", "Rueckerstattung gefordert",
                     "Rückerstattung nicht erhalten", "Rückerstattung nur teilweise erhalten",
                     "Rückerstattung erhalten, aber ich fordere eine weitere Rückerstattung."]:
            with self.subTest(text=text):
                r = wende_regeln_an({"titel": "Anliegen", "text": text}, self.modell)
                self.assertEqual(r["aktionen"], ["eskalieren"])
                self.assertEqual(r["prioritaet"], "tief")
                self.assertEqual(r["kategorie"], "Sonstiges")
                self.assertIn("Service-Regel", r["begruendung"])
        self.assertEqual(self.modell["aktionen"], ["schliessen"])

    def test_abschluss_und_andere_anliegen(self):
        for text in ["Rückerstattung erhalten, danke", "Ich habe die Rückerstattung erhalten.",
                     "Das Geld ist zurück.", "Bitte mein Passwort zurücksetzen."]:
            with self.subTest(text=text):
                self.assertEqual(wende_regeln_an({"titel": "", "text": text}, self.modell), self.modell)
        self.assertEqual(wende_regeln_an({"titel": "Weitere Rückerstattung",
            "text": "Rückerstattung erhalten, danke"}, self.modell)["aktionen"], ["eskalieren"])

    def test_bereits_eskaliert_bleibt_eine_aktion(self):
        r = wende_regeln_an(self.ticket, dict(self.modell, aktionen=["eskalieren"]))
        self.assertEqual(r["aktionen"], ["eskalieren"])

    def test_http_wendet_regel_an(self):
        with patch("suggest.classification.routes.hole_ticket", return_value=self.ticket), \
             patch("suggest.classification.routes.classifier") as classifier:
            classifier.return_value.klassifiziere.return_value = self.modell
            antwort = einschaetzung(SimpleNamespace(query={"ticket": "999"}))
        self.assertEqual(antwort.status, 200)
        self.assertEqual(json.loads(antwort.body)["aktionen"], ["eskalieren"])

    def test_asynchron_eskaliert_im_speicher_mit_timestamp(self):
        # Isolierter Speicher, keine laufenden Dienste oder Warteschlangendateien.
        with patch.object(attrappe, "_TICKETS", [dict(self.ticket, status="offen", prio="mittel")]), \
             patch.object(attrappe, "_AUFTRAEGE", {}), \
             patch("suggest.classification.nachrichten.classifier") as classifier, \
             patch("suggest.classification.nachrichten.sende") as sende:
            speicher = attrappe.Attrappe()
            auftrag = speicher.beauftrage_einschaetzung(999)
            classifier.return_value.klassifiziere.return_value = deepcopy(self.modell)
            bei_eingereicht(auftrag)
            thema, ergebnis = sende.call_args.args
            self.assertEqual(thema, "klassifiziert")
            self.assertEqual(ergebnis["angefordert_am"], auftrag["angefordert_am"])
            self.assertTrue(speicher.uebernehme_einschaetzung(ergebnis["id"],
                ergebnis["angefordert_am"], ergebnis["einschaetzung"]))
            self.assertEqual(speicher.finde(999)["status"], "eskaliert")
