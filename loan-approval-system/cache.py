"""
Simple In-Memory Cache with TTL
Caches agent outputs to avoid duplicate LLM calls.
"""
import time
from typing import Any, Optional, Dict
from logging_config import get_logger

logger = get_logger(__name__)

CACHE_TTL_SECONDS = 300  # 5 minutes


class CacheEntry:
    """Single cache entry with timestamp."""

    def __init__(self, value: Any, ttl: int = CACHE_TTL_SECONDS):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() - self.created_at > self.ttl

    def __repr__(self):
        age = time.time() - self.created_at
        return f"<CacheEntry age={age:.1f}s ttl={self.ttl}s>"


class AgentCache:
    """Simple in-memory cache for agent outputs."""

    def __init__(self, default_ttl: int = CACHE_TTL_SECONDS):
        self._cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if exists and not expired.

        Args:
            key: Cache key (e.g., "APP001:profile")

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self.misses += 1
            return None

        entry = self._cache[key]

        if entry.is_expired():
            logger.info(f"Cache expired: {key} (age={time.time() - entry.created_at:.1f}s)")
            del self._cache[key]
            self.misses += 1
            return None

        self.hits += 1
        logger.debug(f"Cache HIT: {key}")
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store value in cache.

        Args:
            key: Cache key (e.g., "APP001:profile")
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        ttl = ttl or self.default_ttl
        self._cache[key] = CacheEntry(value, ttl=ttl)
        logger.debug(f"Cache SET: {key} (ttl={ttl}s)")

    def clear(self, pattern: Optional[str] = None) -> None:
        """
        Clear cache entries.

        Args:
            pattern: Clear only keys matching pattern (e.g., "APP001:*")
                    If None, clears entire cache
        """
        if pattern is None:
            self._cache.clear()
            logger.info("Cache cleared (all entries)")
            return

        # Simple pattern matching
        keys_to_delete = [k for k in self._cache.keys() if pattern.replace("*", "") in k]
        for key in keys_to_delete:
            del self._cache[key]
        logger.info(f"Cache cleared ({len(keys_to_delete)} entries matching '{pattern}')")

    def cleanup_expired(self) -> int:
        """Remove expired entries from cache."""
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired_keys:
            del self._cache[key]
        if expired_keys:
            logger.debug(f"Cache cleanup: removed {len(expired_keys)} expired entries")
        return len(expired_keys)

    def stats(self) -> dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "entries": len(self._cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(hit_rate, 2),
        }


# Global cache instance
_agent_cache = AgentCache()


def get_cache(key: str) -> Optional[Any]:
    """Get value from global cache."""
    return _agent_cache.get(key)


def set_cache(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """Set value in global cache."""
    _agent_cache.set(key, value, ttl)


def cache_key(applicant_id: str, agent_name: str) -> str:
    """Generate cache key for agent output."""
    return f"{applicant_id}:{agent_name}"


def clear_cache(pattern: Optional[str] = None) -> None:
    """Clear cache entries."""
    _agent_cache.clear(pattern)


def cache_stats() -> dict:
    """Get cache statistics."""
    return _agent_cache.stats()
