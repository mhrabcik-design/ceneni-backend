"""
Skript pro vymazání všech dat z databáze a nový import.
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from database.price_db import PriceDatabase

def clear_database():
    db_url = os.getenv("DATABASE_URL")
    print(f"🗑️ Mažu všechna data z: {db_url.split('@')[-1]}")
    
    db = PriceDatabase(db_url)
    
    with db.engine.connect() as conn:
        conn.execute(text("DELETE FROM prices"))
        conn.execute(text("DELETE FROM items"))
        conn.execute(text("DELETE FROM sources"))
        conn.commit()
    
    stats = db.get_stats()
    print(f"✅ Hotovo. Items: {stats['items']}, Prices: {stats['prices']}")

if __name__ == "__main__":
    clear_database()
