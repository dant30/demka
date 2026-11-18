"""Cache helpers."""
from django.core.cache import cache


def invalidate(prefix: str) -> None:
    if hasattr(cache, "delete_pattern"):
        cache.delete_pattern(f"{prefix}*")


def get_or_set(key, value, timeout: int = 300):
    v = cache.get(key)
    if v is None:
        cache.set(key, value, timeout=timeout)
        return value
    return v