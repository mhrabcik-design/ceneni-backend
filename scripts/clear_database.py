"""
Skript pro vymazání všech dat z databáze a nový import.
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from database.price_db import PriceDatabase

def clear_database():
    db_url = os.getenv("DATABASE_URL")
    print(f"🗑️ Mažu všechna data z: {db_url.split('@')[-1]}")
    
    db = PriceDatabase(db_url)
    
    print("🧹 Dropping all tables...")
    db.metadata.drop_all(db.engine)
    print("🏗️ Creating fresh tables...")
    db.metadata.create_all(db.engine)
    
    stats = db.get_stats()
    print(f"✅ Hotovo. Items: {stats['items']}, Prices: {stats['prices']}")

if __name__ == "__main__":
    clear_database()
