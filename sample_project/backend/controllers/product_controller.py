from fastapi import APIRouter, HTTPException
from typing import List
from sample_project.backend.schemas.product_schema import ProductCreate, ProductResponse

router = APIRouter(prefix="/products", tags=["Products"])

fake_products_db = [
    {"id": 1, "title": "Ergonomic Mechanical Keyboard", "price": 129.99, "stock": 45, "category": "Electronics"},
    {"id": 2, "title": "Noise Cancelling Headphones", "price": 249.50, "stock": 20, "category": "Electronics"},
    {"id": 3, "title": "Minimalist Standing Desk", "price": 389.00, "stock": 12, "category": "Furniture"}
]

@router.get("", response_model=List[ProductResponse])
def list_products():
    """Retrieves all active catalog products."""
    return fake_products_db

@router.get("/{product_id}", response_model=ProductResponse)
def get_product_by_id(product_id: int):
    """Retrieves product details for a given identifier."""
    for p in fake_products_db:
        if p["id"] == product_id:
            return p
    raise HTTPException(status_code=404, detail="Product not found")

@router.post("", response_model=ProductResponse, status_code=201)
def create_new_product(payload: ProductCreate):
    """Creates a new product record in the catalog."""
    new_prod = {
        "id": len(fake_products_db) + 1,
        "title": payload.title,
        "price": payload.price,
        "stock": payload.stock,
        "category": payload.category or "General"
    }
    fake_products_db.append(new_prod)
    return new_prod
