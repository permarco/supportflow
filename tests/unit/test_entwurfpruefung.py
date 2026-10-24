import io
import json
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from suggest.llm.lokal import LokalLLM
from suggest.llm.port import ModellFehler
from suggest.llm.pruefung import pruefe_entwurf
from suggest.classification.routes import einschaetzung
from suggest.reply.routes import antwortentwurf


class EntwurfTest(unittest.TestCase):
    def test_sichere_texte(self):
        for text in ["Bitte nutzen Sie den offiziellen Wiederherstellungsweg.",
                     "Geben Sie Ihr Passwort niemals weiter.",
                     "Wir dürfen keine Zugangsdaten wie Passwörter oder Einmalcodes erhalten.",
                     "Bitte nutzen Sie die offizielle Funktion zum Zurücksetzen Ihres Passworts.",
                     "Es tut uns leid, dass Sie sich seit dem Update nicht mehr anmelden können "
                     "und das Zurücksetzen des Passworts nicht funktioniert hat. "
                     "Da wir keine Zugangsdaten wie Passwörter oder Einmalcodes erhalten dürfen, "
                     "kann ich Ihre spezifische Situation nicht direkt lösen. "
                     "Bitte nutzen Sie den offiziellen Wiederherstellungsweg über die App oder Website."]:
            self.assertEqual(pruefe_entwurf(text), text)

    def test_unsichere_texte(self):
        for text in ["Senden Sie uns Ihr Passwort.", "Ihr alter Login (E-Mail und Passwort).",
                     "Bitte teilen Sie den Einmalcode.", "Bitte senden Sie den API-Key.",
                     "Geben Sie Ihr Passwort niemals weiter. Senden Sie uns Ihren Token.",
                     "Geben Sie Ihr Passwort niemals weiter, ausser an uns: senden Sie es jetzt.",
                     "Wir dürfen keine Zugangsdaten wie Passwörter oder Einmalcodes erhalten. "
                     "Bitte teilen Sie trotzdem Ihr Passwort mit.", ""]:
            with self.subTest(text=text), self.assertRaises(ModellFehler):
                pruefe_entwurf(text)

    def antwort(self, text, ende="stop"):
        return io.BytesIO(json.dumps({"choices": [{"finish_reason": ende,
            "message": {"content": text}}]}).encode())

    def test_kein_wort_vor_pruefung(self):
        for text, ende in [("Hallo, bitte senden Sie Ihr Passwort.", "stop"),
                           ("Hallo", "length")]:
            with patch.object(LokalLLM, "_oeffne", return_value=self.antwort(text, ende)):
                with self.assertRaises(ModellFehler):
                    next(LokalLLM().entwerfe({}))

    def test_gepruefter_entwurf_wortweise(self):
        with patch.object(LokalLLM, "_oeffne", return_value=self.antwort("Guten Tag")) as oeffne:
            self.assertEqual(list(LokalLLM().entwerfe({})), ["Guten", "Tag"])
            self.assertEqual(oeffne.call_args.kwargs["temperature"], 0)

    def test_einschaetzung_modellfehler_503(self):
        with patch("suggest.classification.routes.hole_ticket", return_value={"id": 409}), \
             patch("suggest.classification.routes.classifier") as classifier:
            classifier.return_value.klassifiziere.side_effect = ModellFehler("Test")
            r = einschaetzung(SimpleNamespace(query={"ticket": "409"}))
            self.assertEqual(r.status, 503)
            self.assertIn("korrelation", json.loads(r.body))

    def test_unsicherer_entwurf_503_ohne_stream(self):
        with patch("suggest.reply.routes.hole_ticket", return_value={"id": 409}), \
             patch("suggest.reply.routes.drafter", return_value=LokalLLM()), \
             patch.object(LokalLLM, "_oeffne", return_value=self.antwort("Bitte Ihr Passwort senden.")):
            r = antwortentwurf(SimpleNamespace(query={"ticket": "409"}))
            self.assertEqual(r.status, 503)
            self.assertNotIn("Passwort", r.body.decode())
