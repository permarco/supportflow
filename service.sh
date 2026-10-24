#!/usr/bin/env bash
# Startet SupportFlow: Gateway :8765 (Frontend + Weiterleitung), Ticket-Service :8766, Suggest-Service :8767.
# Alle drei loggen ins selbe Terminal — der Name in Klammern sagt, wer spricht. Ctrl-C beendet alle.
# Derselbe Port 8765 wie der Mock — beide zugleich geht nicht. Nur Python 3 nötig.
cd "$(dirname "$0")"
trap 'kill $(jobs -p) 2>/dev/null' INT TERM EXIT
python3 -u -m tickets &
python3 -u -m suggest &
python3 -u -m gateway &
wait
