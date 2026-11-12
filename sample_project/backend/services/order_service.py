from typing import Dict, List, Any

fake_orders = []

def calculate_order_total(items: List[Dict[str, Any]]) -> float:
    """Calculates gross total order value from items list."""
    total = 0.0
    for item in items:
        total += item.get("quantity", 1) * item.get("unit_price", 0.0)
    return round(total, 2)

def place_order(user_id: int, items: List[Dict[str, Any]], shipping_address: str) -> Dict[str, Any]:
    """Orchestrates order placement, validation, and settlement."""
    total = calculate_order_total(items)
    order = {
        "id": len(fake_orders) + 1,
        "user_id": user_id,
        "total_amount": total,
        "status": "paid",
        "shipping_address": shipping_address,
        "items": items
    }
    fake_orders.append(order)
    return order
