"""Konfiguration aus .env — ohne Abhängigkeit.

    LLM=fake | lokal | cloud
    LLM_BASE_URL=http://localhost:11434/v1
    LLM_MODEL=qwen3:8b
    LLM_API_KEY=…

Umgebungsvariablen, die schon gesetzt sind, gewinnen gegenüber .env.
"""
import os


def lade_env(pfad=None):
    pfad = pfad or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if not os.path.exists(pfad):
        return
    with open(pfad, encoding="utf-8") as f:
        for zeile in f:
            zeile = zeile.strip()
            if not zeile or zeile.startswith("#") or "=" not in zeile:
                continue
            k, v = zeile.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def einstellung(name, standard=None):
    return os.environ.get(name, standard)
