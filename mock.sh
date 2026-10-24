#!/usr/bin/env bash
# Der Mock aus Block 2 — zum Vergleich und als Rückfall. Derselbe Port wie service.sh: nur einer läuft.
cd "$(dirname "$0")"
exec python3 mock_assistent.py --www www "$@"
