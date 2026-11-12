from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from sample_project.backend.services.order_service import place_order

router = APIRouter(prefix="/orders", tags=["Orders"])

class OrderItemSchema(BaseModel):
    product_id: int
    quantity: int
    unit_price: float

class CreateOrderRequest(BaseModel):
    user_id: int
    items: List[OrderItemSchema]
    shipping_address: str

@router.post("", status_code=201)
def checkout_order(payload: CreateOrderRequest):
    """Processes order placement, inventory verification, and settlement."""
    if not payload.items:
        raise HTTPException(status_code=400, detail="Cart cannot be empty")
    
    order = place_order(
        user_id=payload.user_id,
        items=[it.dict() for it in payload.items],
        shipping_address=payload.shipping_address
    )
    return order
