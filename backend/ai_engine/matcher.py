import difflib
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class SmartMatcher:
    def __init__(self, db):
        self.db = db

    def find_best_match(self, query):
        if not query:
            return None
        
        # Clean query
        q_clean = query.lower().replace(',', ' ').replace('/', ' ').replace('(', ' ').replace(')', ' ').strip()
        words = [w for w in q_clean.split() if len(w) > 2]
        
        if not words:
            return None
        
        print(f"Matching query: '{query}'")
        
        # Strategy 1: Multi-keyword search
        # We look for items that contain as many keywords as possible
        candidates = []
        seen_ids = set()
        
        # Try searching for items containing at least one of the first 5 words
        for w in words[:5]:
            results = self.db.search(w, limit=50)
            for r in results:
                if r['id'] not in seen_ids:
                    candidates.append(r)
                    seen_ids.add(r['id'])
        
        if not candidates:
            print("  No candidates found in DB.")
            return None
            
        ranked = []
        for cand in candidates:
            # Get aliases for scoring to ensure alias-matches get high scores
            item_name = cand['item'].lower()
            
            # If the DB search already provided a match_score (which includes aliases), 
            # we can use that as a base or fetch aliases for re-calculation.
            # To stay consistent with SmartMatcher's word-overlap logic:
            item_id = cand.get('id')
            aliases_text = ""
            if item_id:
                # We can't easily join here without DB access, but cand might have it 
                # or we can assume the item name is augmented or just use what we have.
                # Actually, let's look at the candidates' data again.
                pass

            # Since SmartMatcher is used for 'finding' but db.search already did the heavy lifting,
            # let's make sure we at least check if the query words are in the name.
            # If we want to truly support aliases here, we should ideally have them in 'cand'.
            
            # Simple approach: If the candidate doesn't match well by name, 
            # but it WAS returned by db.search, let's trust the db.search score if it's high.
            db_score = cand.get('match_score', 0)
            
            # Count how many query words are in the candidate name
            words_in_name = sum(1 for w in words if w in item_name)
            word_score = words_in_name / len(words) if words else 0
            
            # Fuzzy ratio with name
            fuzzy_score = difflib.SequenceMatcher(None, q_clean, item_name).ratio()
            
            # combine: If DB score is high (alias match), we respect it.
            final_score = max((word_score * 0.7) + (fuzzy_score * 0.3), db_score)
            
            ranked.append((final_score, cand))
        
        # Sort by score
        ranked.sort(key=lambda x: x[0], reverse=True)
        
        if ranked:
            best_score, best_match = ranked[0]
            print(f"  Best match: '{best_match['item']}' (Score: {best_score:.2f})")
            
            # Threshold: 0.2 is quite low, but construction items are specific
            if best_score > 0.2:
                return best_match
        
        print("  No match passed the score threshold.")
        return None

if __name__ == "__main__":
    from backend.database.price_db import PriceDatabase
    db = PriceDatabase()
    matcher = SmartMatcher(db)
    
    test_queries = [
        "CYKY-J 3x1.5",
        "stožár",
        "AYKY"
    ]
    
    for q in test_queries:
        match = matcher.find_best_match(q)
        if match:
            print(f"QUERY: {q} -> MATCH: {match['item']} (Source: {match['source']}, Price: {match['price_material']})")
        else:
            print(f"QUERY: {q} -> NO MATCH")
