"""
Script to normalize existing item names in the database.
- Removes line breaks, tabs, and excessive spaces.
- Removes sequential IDs (e.g. '1. ', 'a) ').
- Merges duplicate items resulting from normalization.
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment
root_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
load_dotenv(os.path.join(root_dir, '.env'))
sys.path.append(os.path.join(root_dir, 'backend'))

from database.price_db import PriceDatabase  # noqa: E402

def normalize_database():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in .env")
        return

    print("🚀 Starting database normalization...")
    db = PriceDatabase(db_url)
    
    stats_before = db.get_stats()
    print(f"📊 Before: {stats_before['items']} items")

    updated_count = 0
    merged_count = 0

    with db.engine.connect() as conn:
        # 1. Fetch all items
        items = conn.execute(text("SELECT id, name FROM items")).fetchall()
        
        # We'll keep track of items we've already processed/merged
        processed_ids = set()
        
        for item_id, original_name in items:
            if item_id in processed_ids:
                continue
                
            cleaned_name = db._clean_item_name(original_name)
            
            if cleaned_name != original_name:
                norm_name = cleaned_name.lower().strip()
                
                # Check if an item with this name already exists
                existing = conn.execute(
                    text("SELECT id FROM items WHERE (name = :name OR normalized_name = :norm) AND id != :id"),
                    {"name": cleaned_name, "norm": norm_name, "id": item_id}
                ).fetchone()
                
                if existing:
                    target_id = existing[0]
                    print(f"  🔗 Merging: '{original_name}' -> matches existing '{cleaned_name}' (ID {target_id})")
                    
                    # Redirect all prices from current item to the existing one
                    conn.execute(
                        text("UPDATE prices SET item_id = :target_id WHERE item_id = :old_id"),
                        {"target_id": target_id, "old_id": item_id}
                    )
                    
                    # Delete the now-redundant item
                    conn.execute(
                        text("DELETE FROM items WHERE id = :old_id"),
                        {"old_id": item_id}
                    )
                    
                    processed_ids.add(item_id)
                    merged_count += 1
                else:
                    try:
                        # Update the current item with its cleaned name
                        print(f"  ✨ Cleaned: '{original_name}' -> '{cleaned_name}'")
                        conn.execute(
                            text("UPDATE items SET name = :name, normalized_name = :norm WHERE id = :id"),
                            {"name": cleaned_name, "norm": norm_name, "id": item_id}
                        )
                        updated_count += 1
                    except Exception as e:
                        # If we still hit a unique constraint, try to merge with the item that caused it
                        print(f"  ⚠️ Conflict updating '{cleaned_name}', attempting emergency merge...")
                        actual_existing = conn.execute(
                            text("SELECT id FROM items WHERE name = :name OR normalized_name = :norm"),
                            {"name": cleaned_name, "norm": norm_name}
                        ).fetchone()
                        
                        if actual_existing:
                            target_id = actual_existing[0]
                            conn.execute(
                                text("UPDATE prices SET item_id = :target_id WHERE item_id = :old_id"),
                                {"target_id": target_id, "old_id": item_id}
                            )
                            conn.execute(
                                text("DELETE FROM items WHERE id = :old_id"),
                                {"old_id": item_id}
                            )
                            merged_count += 1
                        else:
                            print(f"  ❌ Failed to resolve conflict for '{cleaned_name}': {e}")

        
        conn.commit()

    stats_after = db.get_stats()
    print("\n✅ Finished!")
    print(f"✨ Items cleaned: {updated_count}")
    print(f"🔗 Items merged: {merged_count}")
    print(f"📊 After: {stats_after['items']} items")

if __name__ == "__main__":
    normalize_database()
