"""python3 -m tickets — startet den Ticket-Service auf Port 8766 (einzeln; normal: ./service.sh)."""
from basis import dienst

if __name__ == "__main__":
    dienst.starte("tickets", 8766)
