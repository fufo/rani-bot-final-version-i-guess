"""
╔══════════════════════════════════════════════════════════╗
║         TELEGRAM SHOP BOT - CACHING LAYER                ║
║  In-memory TTL cache to reduce DB reads on hot paths     ║
╚══════════════════════════════════════════════════════════╝
"""

import time
import logging
from typing import Any, Optional, Dict, Tuple

logger = logging.getLogger(__name__)


class TTLCache:
    """Simple thread-safe TTL cache."""

    def __init__(self, default_ttl: float = 60.0, max_size: int = 1000):
        self._store: Dict[str, Tuple[Any, float]] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires = entry
        if time.time() > expires:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        if len(self._store) >= self.max_size:
            self._evict()
        self._store[key] = (value, time.time() + (ttl or self.default_ttl))

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def delete_prefix(self, prefix: str) -> int:
        keys = [k for k in list(self._store.keys()) if k.startswith(prefix)]
        for k in keys:
            del self._store[k]
        return len(keys)

    def clear(self) -> None:
        self._store.clear()

    def _evict(self) -> None:
        now = time.time()
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]
        # If still too large, remove oldest entries
        if len(self._store) >= self.max_size:
            oldest = sorted(self._store.items(), key=lambda x: x[1][1])
            for k, _ in oldest[: len(oldest) // 4]:
                del self._store[k]


# ─────────────────────────────────────────────
#  Singleton cache instances (named by scope)
# ─────────────────────────────────────────────

# Settings — changes rarely, cache 2 min
settings_cache: TTLCache = TTLCache(default_ttl=120.0)

# Product / category listings — invalidated on admin edits
products_cache: TTLCache = TTLCache(default_ttl=60.0)

# User profiles — short TTL because balance changes
user_cache: TTLCache = TTLCache(default_ttl=15.0, max_size=5000)

# Statistics — refreshed on demand
stats_cache: TTLCache = TTLCache(default_ttl=30.0)


def invalidate_product(product_id: Optional[int] = None) -> None:
    """Bust product-related cache entries."""
    if product_id:
        products_cache.delete(f"product:{product_id}")
    products_cache.delete_prefix("products:cat:")
    products_cache.delete_prefix("products:admin:")
    products_cache.delete("categories:all")
    stats_cache.clear()


def invalidate_user(user_id: int) -> None:
    user_cache.delete(f"user:{user_id}")


def invalidate_settings(key: Optional[str] = None) -> None:
    if key:
        settings_cache.delete(f"setting:{key}")
    else:
        settings_cache.clear()
