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

# Klíčová slova pro odstranění - POUZE položky které ZAČÍNAJÍ těmito slovy
# Toto jsou opravdu jen součty kapitol, ne validní položky
BLACKLIST_STARTSWITH = [
    'celkem',
    'součet',
    'mezisoučet', 
    'total',
    'základ daně',
    'dph ',
    'dph:',
]

# Přesné shody - položky které jsou přesně tento text
BLACKLIST_EXACT = [
    'silnoproud',
    'slaboproud',
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
            item_id, name = item.id, item.name.lower().strip()
            
            should_delete = False
            
            # Kontrola 1: Začíná některým z klíčových slov součtů?
            for keyword in BLACKLIST_STARTSWITH:
                if name.startswith(keyword):
                    should_delete = True
                    break
            
            # Kontrola 2: Je to přesná shoda s obecným názvem kapitoly?
            if not should_delete:
                if name in BLACKLIST_EXACT:
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
