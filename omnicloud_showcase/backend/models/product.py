from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(40), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    inventory_count = Column(Integer, default=0)
