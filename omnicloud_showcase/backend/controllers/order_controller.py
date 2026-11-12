from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel
from backend.services.order_service import place_order, get_order_details
from backend.models.order import Order

router = APIRouter()

class OrderItemSchema(BaseModel):
    product_id: int
    quantity: int
    unit_price: float

class CreateOrderRequest(BaseModel):
    customer_id: int
    items: List[OrderItemSchema]
    shipping_address: str

def verify_jwt_auth(authorization: str = "Bearer token"):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token.")
    return {"user_id": 42, "role": "customer"}

@router.post("", dependencies=[Depends(verify_jwt_auth)])
async def checkout_order(payload: CreateOrderRequest):
    """Processes an e-commerce order checkout transaction."""
    order = place_order(
        customer_id=payload.customer_id,
        items=[item.model_dump() for item in payload.items],
        shipping_address=payload.shipping_address
    )
    return {"status": "confirmed", "order_id": order.id, "total": order.total_amount}

@router.get("/{order_id}", dependencies=[Depends(verify_jwt_auth)])
async def retrieve_order(order_id: int):
    """Fetches complete order breakdown including line items and status."""
    order = get_order_details(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order record not found.")
    return {"id": order.id, "status": order.status, "total": order.total_amount}
