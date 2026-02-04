import time

class CacheManager:
    def __init__(self, ttl_seconds=3600):
        self._cache = {}  # {(query, type, threshold): (result, timestamp)}
        self.ttl = ttl_seconds

    def get(self, query, price_type, threshold):
        key = (query.lower().strip(), price_type, threshold)
        if key in self._cache:
            result, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return result
            else:
                del self._cache[key]
        return None

    def set(self, query, price_type, threshold, result):
        key = (query.lower().strip(), price_type, threshold)
        self._cache[key] = (result, time.time())

    def invalidate(self, query=None):
        """Invalidate entries for a specific query or clear all."""
        if query:
            q_norm = query.lower().strip()
            # Remove all keys that match this query (across all types/thresholds)
            keys_to_del = [k for k in self._cache.keys() if k[0] == q_norm]
            for k in keys_to_del:
                del self._cache[k]
        else:
            self._cache.clear()

    def clear(self):
        self._cache.clear()

    def get_stats(self):
        return len(self._cache)
