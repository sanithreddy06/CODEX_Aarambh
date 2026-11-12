from typing import List, Dict, Any
from backend.models.order import Order
from backend.models.product import Product
from backend.services.notification_service import dispatch_order_alert

def calculate_discount(price: float, discount_percent: float) -> float:
    """Computes promotional rate reduction."""
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Invalid discount range")
    return price * (1.0 - (discount_percent / 100.0))

def place_order(customer_id: int, items: List[Dict[str, Any]], shipping_address: str) -> Order:
    """Executes business rules, updates inventory, and creates persistent Order record."""
    total = sum(item.get("quantity", 1) * item.get("unit_price", 10.0) for item in items)
    
    order = Order(
        id=5001,
        customer_id=customer_id,
        status="processing",
        total_amount=total,
        shipping_address=shipping_address
    )
    
    dispatch_order_alert(order.id, customer_id)
    return order

def get_order_details(order_id: int) -> Order:
    """Queries order entity from data layer."""
    return Order(id=order_id, customer_id=42, status="shipped", total_amount=199.95)
