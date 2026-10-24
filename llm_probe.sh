#!/usr/bin/env bash
# llm_probe.sh — ruft das LLM aus .env einmal auf. Beleg für die Vorbereitung 3.
#
#   ./llm_probe.sh                       # liest .env; Standard: Ollama, qwen3:8b
#   LLM_MODEL=qwen3:4b ./llm_probe.sh    # anderes lokales Modell
#
# Erwartet: eine kurze Antwort auf «Hallo». Alles andere ist ein Fehler.
set -e
cd "$(dirname "$0")"
if [ -f .env ]; then set -a; . ./.env; set +a; fi
: "${LLM_BASE_URL:=http://localhost:11434/v1}"
: "${LLM_MODEL:=qwen3:8b}"
: "${LLM_API_KEY:=ollama}"

antwort=$(curl -sf --max-time 120 "$LLM_BASE_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $LLM_API_KEY" \
  -d "{\"model\":\"$LLM_MODEL\",\"messages\":[
        {\"role\":\"system\",\"content\":\"Antworte auf Deutsch mit genau einem Wort.\"},
        {\"role\":\"user\",\"content\":\"Hallo\"}]}") || {
  echo "✗ Kein LLM erreichbar unter $LLM_BASE_URL — läuft Ollama? (ollama list) Stimmt der Schlüssel?"; exit 1; }

echo "$antwort" | python -c '
import json,sys
d=json.load(sys.stdin)
text=d["choices"][0]["message"]["content"].strip()
print("✓ LLM antwortet:", text)
print("  Modell:", d.get("model"), "· Token:", d.get("usage",{}).get("total_tokens","?"))'
