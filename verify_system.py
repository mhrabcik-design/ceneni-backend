from backend.services.data_manager import DataManager
from unittest.mock import MagicMock
import os
import datetime

# Setup DataManager
dm = DataManager(db_url="sqlite:///test_prices_v2.db")

# Mock AI
dm.ai = MagicMock()

def mock_extract(text, filename, file_type='supplier'):
    if file_type == 'internal':
        return {
            "vendor": "Internal History",
            "date": "2024-01-01",
            "items": [
                {"raw_name": "Internal Item Labor Only", "price_labor": 500.0, "unit": "hod"}
            ]
        }
    else:
        return {
            "vendor": "Supplier Inc",
            "date": "2025-05-20",
            "items": [
                {"raw_name": "Supplier Item Material", "price_material": 100.0, "unit": "ks"}
            ]
        }

dm.ai.extract_from_text.side_effect = mock_extract

# Test 1: Supplier
print("Testing Supplier Ingest...")
with open("quote.pdf", "w") as f: f.write("dummy")
res1 = dm.process_file("quote.pdf")
print(f"Supplier Result: {res1}")

# Test 2: Internal
print("\nTesting Internal Ingest...")
os.makedirs("Input/02_Historie_Excel", exist_ok=True)
internal_path = "Input/02_Historie_Excel/budget.xlsx"
with open(internal_path, "w") as f: f.write("dummy")
res2 = dm.process_file(internal_path)
print(f"Internal Result: {res2}")

# Verify DB
print("\nVerifying DB Content...")
items = dm.db.search_items("Item")
for item in items:
    print(f"Found Item: {item['name']}")
    history = dm.db.get_price_history(item['id'])
    for h in history:
        print(f"  -> Date: {h['date']}, Vendor: {h['vendor']}, Mat: {h['price_material']}, Lab: {h['price_labor']}")

# Cleanup
try:
    os.remove("quote.pdf")
    os.remove(internal_path)
    if os.path.exists("test_prices_v2.db"):
        os.remove("test_prices_v2.db")
except: pass
