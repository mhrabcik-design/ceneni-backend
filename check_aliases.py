import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from database.price_db import PriceDatabase
from sqlalchemy import select, text

db = PriceDatabase()
with db.engine.connect() as conn:
    # Check if table exists and has data
    try:
        count = conn.execute(text("SELECT COUNT(*) FROM item_aliases")).scalar()
        print(f"Total aliases in DB: {count}")
        
        if count > 0:
            last_aliases = conn.execute(text("SELECT * FROM item_aliases ORDER BY created_at DESC LIMIT 5")).fetchall()
            print("\nLatest 5 aliases:")
            for row in last_aliases:
                print(row)
                
            # Check item 1 specifically if it's there
            # ...
    except Exception as e:
        print(f"Error checking aliases: {e}")
