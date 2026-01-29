from backend.database.price_db import PriceDatabase

db = PriceDatabase()
results = db.search("CYKY")
print(f"Found {len(results)} matches for 'CYKY':")
for r in results:
    print(f"  {r['item']} | Mat: {r['price_material']} | Labor: {r['price_labor']} | Source: {r['source']}")
