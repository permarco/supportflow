# Mini-SPEC · Lokaler Assistent: Wartezeit und Entwurfprüfung

Die ausdrücklich genehmigte UI-Ausnahme ersetzt die bisherige gemeinsame 5-Sekunden-
Abbruchfrist. Einschätzung und Entwurf erhalten eigene Controller und eigene Zustände.
Stopp beendet beide Browseranfragen; alte Antworten dürfen keinen neuen Lauf überschreiben.
UI: 110 Sekunden Gesamtfrist je Anfrage; Gateway: 100 Sekunden Socket-Timeout für
Suggest/Draft, sonst 30; lokales Modell: 90 Sekunden je blockierendem Netzwerkzugriff.
Diese Socket-Timeouts sind keine garantierte Gesamtlaufzeit. Die UI begrenzt die Wartezeit.

ModellFehler bei Einschätzung wird als 503 mit gemeinsamer Fehlerform ausgegeben.
Der lokale Entwurf wird vollständig erzeugt (maximal 512 Tokens), geprüft und erst danach
wortweise als SSE ausgegeben. Der Fake behält sein unmittelbares Streaming.
Die vollständige Vorprüfung verzögert das erste Wort. Während des blockierenden Modellaufrufs
beendet Browser-Stopp die Anzeige, aber die serverseitige Berechnung kann bis zur Antwort
oder Zeitgrenze weiterlaufen. Keine Behauptung sofortiger Modell-Abbruchweiterleitung.

Prompt: keine Anforderung von Passwörtern, Einmalcodes, PIN, Tokens oder Zugangsschlüsseln;
keine erfundenen Konten, Kontaktadressen oder behaupteten ausgeführten Massnahmen.
Lokale Ausgaben mit sensiblen Begriffen werden vorsorglich verworfen. Ausnahmen sind eng definierte vollständige Warn- und Wiederherstellungssätze,
unter anderem «Geben Sie Ihr Passwort niemals weiter.» und die diagnostizierte
Warnung, dass der Support keine Zugangsdaten erhalten darf. Weitere Aufforderungen
im selben Satz oder Folgesatz werden weiterhin geprüft. Ein abgelehnter oder
abgeschnittener Entwurf liefert vor Streambeginn 503; kein Teiltext gelangt ins UI.
Der Filter ist konservativ und keine semantische Sicherheitsgarantie für beliebige
Umschreibungen. Menschliche Prüfung vor Versand bleibt erforderlich.

Tests: langsame unabhängige UI-Anfragen, Teilfehler, Stopp/Neustart; sichere/unsichere und
abgeschnittene Entwürfe, keine Ausgabe vor Prüfung; ModellFehler -> 503; Fake-Regression.
