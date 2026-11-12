from pydantic import BaseModel
from typing import Optional

class ProductCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    price: float
    stock: int
    category: Optional[str] = "General"

class ProductResponse(BaseModel):
    id: int
    title: str
    price: float
    stock: int
    category: str
