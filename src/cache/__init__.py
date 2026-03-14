import time

class Cache:
    def __init__(self, ttl):
        self.ttl = ttl
        self.cache = {}
        self.expiry = {}

    def set(self, key, value):
        self.cache[key] = value
        self.expiry[key] = time.time() + self.ttl

    def get(self, key):
        if key in self.cache:
            if time.time() < self.expiry[key]:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.expiry[key]
        return None

    def clear(self):
        self.cache.clear()
        self.expiry.clear()