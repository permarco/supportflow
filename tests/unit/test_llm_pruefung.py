"""Ungültige Modellausgaben dürfen keine Wirkung entfalten."""
import io
import json
import unittest
from unittest.mock import patch

from suggest.llm.lokal import LokalLLM
from suggest.llm.port import ModellFehler
from suggest.llm.pruefung import pruefe_einschaetzung
from suggest.classification.nachrichten import bei_eingereicht


class FeldpruefungTest(unittest.TestCase):
    def setUp(self):
        self.gueltig = {"kategorie": "Account", "prioritaet": "hoch",
                        "aktionen": ["antworten"], "begruendung": "Login ist blockiert."}

    def test_gueltig_bleibt_unveraendert(self):
        self.assertEqual(pruefe_einschaetzung(self.gueltig), self.gueltig)

    def test_ungueltige_ausgaben(self):
        faelle = [None, [], "Text", 3, True]
        for feld in self.gueltig:
            faelle.append({k: v for k, v in self.gueltig.items() if k != feld})
        faelle.append(dict(self.gueltig, zusatz="unerwartet"))
        for feld in ("kategorie", "prioritaet", "begruendung"):
            for wert in (None, 1, True, [], {}):
                faelle.append(dict(self.gueltig, **{feld: wert}))
        for feld, wert in [("kategorie", "Unbekannt"), ("prioritaet", "kritisch"),
                           ("aktionen", "antworten"), ("aktionen", None),
                           ("aktionen", []), ("aktionen", ["gutschrift"]),
                           ("aktionen", ["antworten", "eskalieren"]),
                           ("aktionen", [None]), ("aktionen", [{}])]:
            faelle.append(dict(self.gueltig, **{feld: wert}))
        for ausgabe in faelle:
            with self.subTest(ausgabe=ausgabe), self.assertRaises(ModellFehler):
                pruefe_einschaetzung(ausgabe)

    def modellantwort(self, ergebnis):
        return io.BytesIO(json.dumps({"choices": [{"finish_reason": "stop",
            "message": {"content": json.dumps(ergebnis)}}]}).encode())

    def test_adapter_prueft_vor_rueckgabe(self):
        for ergebnis in (self.gueltig, dict(self.gueltig, aktionen=["gutschrift"])):
            with self.subTest(ergebnis=ergebnis), patch.object(
                    LokalLLM, "_oeffne", return_value=self.modellantwort(ergebnis)):
                if ergebnis == self.gueltig:
                    self.assertEqual(LokalLLM().klassifiziere({}), self.gueltig)
                else:
                    with self.assertRaises(ModellFehler):
                        LokalLLM().klassifiziere({})

    def test_ungueltig_sendet_keine_klassifiziert_nachricht(self):
        auftrag = {"id": 999, "titel": "Test", "text": "Test",
                   "angefordert_am": "2026-10-24T10:15:30.123456Z"}
        with patch("suggest.classification.nachrichten.classifier", return_value=LokalLLM()), \
             patch.object(LokalLLM, "_oeffne", return_value=self.modellantwort(
                 dict(self.gueltig, aktionen=["gutschrift"]))), \
             patch("suggest.classification.nachrichten.sende") as sende:
            with self.assertRaises(ModellFehler):
                bei_eingereicht(auftrag)
            sende.assert_not_called()
