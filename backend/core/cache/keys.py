"""Centralised cache key builders."""

def stock_level_key(product_id: int, location_id: int) -> str:
    return f"stock:{product_id}:{location_id}"

def customer_balance_key(customer_id: int) -> str:
    return f"customer:balance:{customer_id}"

def route_run_key(run_id: int) -> str:
    return f"route:run:{run_id}"