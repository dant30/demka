"""Caching decorators — hashes args to avoid non-hashable keys."""
import hashlib
import json
from functools import wraps

from django.core.cache import cache


def _key(prefix: str, name: str, args, kwargs) -> str:
    raw = json.dumps({"a": args, "k": kwargs}, default=str, sort_keys=True)
    return f"{prefix}:{name}:{hashlib.md5(raw.encode()).hexdigest()}"


def cache_result(timeout: int = 300, key_prefix: str = "cache"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            k = _key(key_prefix, func.__name__, args, kwargs)
            result = cache.get(k)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(k, result, timeout=timeout)
            return result
        return wrapper
    return decorator


def invalidate_cache(prefix: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if hasattr(cache, "delete_pattern"):
                cache.delete_pattern(f"{prefix}*")
            return result
        return wrapper
    return decorator