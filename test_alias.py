import requests
import json

BASE_URL = "http://localhost:8000"

def test_alias_system():
    # 1. Search for a nonsense term
    query = "rigips_super_deska_v3"
    print(f"Searching for unknown query: '{query}'")
    resp = requests.post(f"{BASE_URL}/match", json={"items": [query]})
    results = resp.json()
    
    match = results.get(query)
    if match and match.get('match_score', 0) > 0.4:
        print(f"❌ Error: Found match before learning: {match.get('original_name')}")
    else:
        print("✅ Correct: No match found initially.")

    # 2. Pick an item to link (let's find one first)
    print("Finding a target item...")
    search_resp = requests.get(f"{BASE_URL}/search?q=sadrokarton")
    items = search_resp.json()
    if not items:
        print("❌ Error: No items found in DB to test with.")
        return
    
    target_item = items[0]
    print(f"Target item: {target_item['name']} (ID: {target_item['id']})")

    # 3. Learn the alias
    print(f"Linking '{query}' -> '{target_item['name']}'")
    learn_resp = requests.post(f"{BASE_URL}/feedback/learn", json={
        "query": query,
        "item_id": target_item['id']
    })
    print(f"Learn response: {learn_resp.status_code} - {learn_resp.text}")

    # 4. Search again
    print(f"Searching again for: '{query}'")
    resp_again = requests.post(f"{BASE_URL}/match", json={"items": [query]})
    results_again = resp_again.json()
    match_again = results_again.get(query)
    
    if match_again and match_again.get('item_id') == target_item['id']:
        print(f"✅ Success! Found match via alias: {match_again.get('original_name')} (Score: {match_again.get('match_score')})")
    else:
        print(f"❌ Error: Match not found after learning. Result: {match_again}")

if __name__ == "__main__":
    try:
        test_alias_system()
    except Exception as e:
        print(f"Test failed: {e}")
        print("Make sure the backend is running at http://localhost:8000")
