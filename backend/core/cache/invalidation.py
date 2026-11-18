"""Cache invalidation helpers — call from app signals."""
from django.core.cache import cache


def _drop(pattern: str) -> None:
    if hasattr(cache, "delete_pattern"):
        cache.delete_pattern(pattern)


def invalidate_stock(product_id: int) -> None:
    _drop(f"stock:{product_id}:*")


def invalidate_customer(customer_id: int) -> None:
    _drop(f"customer:{customer_id}:*")
    _drop(f"customer:balance:{customer_id}")


def invalidate_route_run(run_id: int) -> None:
    _drop(f"route:run:{run_id}:*")