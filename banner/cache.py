# banner/cache.py

class BannerCache:
    def __init__(self):
        self._cache = {
            "members": None,
            "online": None,
            "voice": None,
            "boosts": None
        }

    def has_changed(self, stats: dict) -> bool:
        changed = False
        for key, value in stats.items():
            if self._cache.get(key) != value:
                self._cache[key] = value
                changed = True
        return changed
