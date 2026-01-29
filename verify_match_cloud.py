import os
import sys
from dotenv import load_dotenv

# Load env to get DATABASE_URL
load_dotenv()

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from database.price_db import PriceDatabase

def test_cloud_search():
    db_url = os.getenv("DATABASE_URL")
    print(f"Connecting to: {db_url.split('@')[-1]}") # Hide password
    
    db = PriceDatabase(db_url)
    
    # Test queries based on user screenshot
    queries = [
        "Svorka uzemňovací",
        "Krabice KO 68",
        "Krabice KO 97",
        "Krabice KU 68",
        "Trubka ohebná 23 mm", 
        "CY 6 ZZ",
        "Vodič v trubce"
    ]
    
    print("\n--- Testing Search Logic ---")
    for q in queries:
        print(f"\nQuery: '{q}'")
        try:
            results = db.search(q, limit=1)
            if results:
                print(f"✅ Found: {results[0]['item']} (Score logic hidden)")
                print(f"   Price: {results[0]['price_material']} + {results[0]['price_labor']}")
            else:
                print(f"❌ No match found.")
                
            # Debugging tokens logic
            q_norm = q.lower().strip()
            tokens = [t for t in q_norm.split() if len(t) > 2]
            print(f"   (Tokens > 2 chars: {tokens})")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_cloud_search()
