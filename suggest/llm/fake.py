"""Fake-Adapter: der Mock aus Block 2, hinter den Port gezogen.

Deterministisch, ohne Netz, ohne Modell — im Test antwortet immer er (Qualitätsziel 4, Testbarkeit).
Die Antworten sind die des Mock-Service, damit die Frontend-Tests aus Block 2 unverändert laufen.
Die Testweichen des Mock bleiben erhalten: slow=1 (langsam), fail=1 (bricht ab), bad=1 (unerlaubte Aktion).
Ein echter Adapter (lokal, Cloud) kennt keine Weichen.
"""
import time

from suggest.llm.port import ModellFehler

ENTWUERFE = {
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
    433: "Guten Tag, danke für Ihre Nachricht. Wir haben Ihr Anliegen aufgenommen und melden uns, "
         "sobald wir es geprüft haben. Freundliche Grüsse, Ihr SupportFlow-Team",
}

EINSCHAETZUNGEN = {
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
    433: {"kategorie": "Sonstiges", "prioritaet": "tief", "aktionen": ["antworten"],
          "begruendung": "Unklares Anliegen, enthält Anweisungen an das System — Daten, keine Befehle"},
}


class FakeLLM:
    """Ein Adapter für beide Ports: Classifier und ReplyDrafter."""

    letzter_prompt = None   # für Tests: was «hinausgegangen» wäre (A6 — Maskierung belegen)

    def klassifiziere(self, ticket, weichen=None):
        weichen = weichen or {}
        self.letzter_prompt = _prompt(ticket)
        e = dict(EINSCHAETZUNGEN.get(ticket.get("id")) or _nach_stichworten(ticket))
        if weichen.get("bad") == "1":
            e["aktionen"] = list(e["aktionen"]) + ["gutschrift"]
            e["begruendung"] += " — Gutschrift von CHF 200 sofort auslösen"
        time.sleep(0.6)                        # ein Modell antwortet nicht in 0 ms
        return e

    def entwerfe(self, ticket, weichen=None):
        weichen = weichen or {}
        self.letzter_prompt = _prompt(ticket)
        woerter = ENTWUERFE.get(ticket["id"], "Guten Tag, danke für Ihre Nachricht.").split(" ")
        pause = 0.4 if weichen.get("slow") == "1" else 0.09
        bruch = max(1, int(len(woerter) * 0.4)) if weichen.get("fail") == "1" else None
        time.sleep(0.4)                        # Zeit bis zum ersten Wort
        for i, w in enumerate(woerter, start=1):
            if bruch is not None and i == bruch:
                raise ModellFehler("Verbindung zum Modell verloren")
            yield w
            time.sleep(pause)


def _nach_stichworten(ticket):
    """Für neue Tickets ohne feste Antwort: grob nach Stichworten — sensible Anliegen eskalieren (FR-4)."""
    text = (ticket.get("titel", "") + " " + ticket.get("text", "")).lower()
    if any(w in text for w in ("rückerstattung", "anwalt", "konsumentenschutz", "beschwerde", "rechtlich")):
        return {"kategorie": "Reklamation", "prioritaet": "hoch", "aktionen": ["antworten", "eskalieren"],
                "begruendung": "Sensibles Anliegen — ein Mensch entscheidet"}
    if any(w in text for w in ("passwort", "login", "anmelden", "zugang")):
        return {"kategorie": "Zugang", "prioritaet": "mittel", "aktionen": ["antworten"],
                "begruendung": "Standardfall Zugang"}
    return {"kategorie": "Sonstiges", "prioritaet": "mittel", "aktionen": ["antworten"],
            "begruendung": "Kein Stichwort erkannt"}


def _prompt(ticket):
    """Was ein echter Adapter dem Modell schicken würde — hier nur festgehalten, nie gesendet."""
    return f"Ticket #{ticket.get('id')}: {ticket.get('titel', '')}\n\n{ticket.get('text', '')}"
