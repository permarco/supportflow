"""python3 -m suggest — startet den Suggest-Service auf Port 8767 (einzeln; normal: ./service.sh)."""
from basis import dienst

if __name__ == "__main__":
    dienst.starte("suggest", 8767)
