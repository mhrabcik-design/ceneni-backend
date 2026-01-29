"""
Skript pro vyčištění databáze od součtů kapitol a nesmyslných položek.
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from database.price_db import PriceDatabase

# Klíčová slova pro odstranění (součty kapitol, hlavičky)
BLACKLIST_KEYWORDS = [
    'celkem',
    'součet',
    'mezisoučet',
    'total',
    'silnoproud',
    'slaboproud',
    'vzduchotechnika',
    'měření a regulace',
    'zdravotechnika',
    'elektroinstalace',
    'vytápění',
    'chlazení',
    'přípojky',
    'přeložky',
    'osvětlení kapitola',
    'základ daně',
    'dph',
    'recyklační',
    'autorský',
]

def cleanup_database():
    db_url = os.getenv("DATABASE_URL")
    print(f"🧹 Čistím databázi: {db_url.split('@')[-1]}")
    
    db = PriceDatabase(db_url)
    
    # Získat statistiky před
    stats_before = db.get_stats()
    print(f"📊 Před: {stats_before['items']} položek, {stats_before['prices']} cen")
    
    deleted_count = 0
    
    with db.engine.connect() as conn:
        # Najít všechny položky
        items = conn.execute(text("SELECT id, name FROM items")).fetchall()
        
        for item in items:
            item_id, name = item.id, item.name.lower()
            
            # Kontrola zda název obsahuje blacklist klíčové slovo
            should_delete = False
            for keyword in BLACKLIST_KEYWORDS:
                if keyword in name:
                    should_delete = True
                    break
            
            # Také smazat položky, které jsou pouze čísla nebo velmi krátké
            if not should_delete:
                clean_name = ''.join(c for c in name if c.isalpha())
                if len(clean_name) < 3:
                    should_delete = True
            
            if should_delete:
                print(f"  🗑️ Mažu: {item.name[:60]}...")
                conn.execute(text(f"DELETE FROM prices WHERE item_id = {item_id}"))
                conn.execute(text(f"DELETE FROM items WHERE id = {item_id}"))
                deleted_count += 1
        
        conn.commit()
    
    # Získat statistiky po
    stats_after = db.get_stats()
    print(f"\n✅ Hotovo!")
    print(f"📊 Po: {stats_after['items']} položek, {stats_after['prices']} cen")
    print(f"🗑️ Smazáno: {deleted_count} položek")

if __name__ == "__main__":
    cleanup_database()
