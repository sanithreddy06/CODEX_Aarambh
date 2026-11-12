import os
import zipfile
from pathlib import Path

def create_showcase_project():
    base_dir = Path("omnicloud_showcase")
    if base_dir.exists():
        import shutil
        shutil.rmtree(base_dir, ignore_errors=True)

    # -------------------------------------------------------------
    # 1. ROOT MANIFESTS
    # -------------------------------------------------------------
    files = {
        "package.json": """{
  "name": "omnicloud-enterprise",
  "version": "2.4.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "express": "^4.18.2",
    "lucide-react": "^0.344.0"
  },
  "devDependencies": {
    "typescript": "^5.3.3",
    "@types/react": "^18.2.0",
    "@types/node": "^20.0.0",
    "vitest": "^1.3.0"
  }
}
""",
        "requirements.txt": """fastapi>=0.110.0
uvicorn>=0.28.0
sqlalchemy>=2.0.25
pydantic>=2.6.0
python-jose>=3.3.0
pytest>=8.0.0
httpx>=0.27.0
""",
        "pom.xml": """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.omnicloud</groupId>
    <artifactId>payment-gateway</artifactId>
    <version>1.0.0</version>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
    </dependencies>
</project>
""",
        "Dockerfile": """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
""",
        "docker-compose.yml": """version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./prod.db
""",

        # -------------------------------------------------------------
        # 2. PYTHON BACKEND (FastAPI + SQLAlchemy + Multi-Layer Architecture)
        # -------------------------------------------------------------
        "backend/__init__.py": "",
        "backend/main.py": """from fastapi import FastAPI, Depends, HTTPException, Header
from backend.controllers.auth_controller import router as auth_router
from backend.controllers.order_controller import router as order_router
from backend.controllers.analytics_controller import router as analytics_router

app = FastAPI(title="OmniCloud Core Enterprise API", version="2.4.0")

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(order_router, prefix="/api/v1/orders", tags=["Orders"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])

@app.get("/api/v1/health")
async def health_check():
    \"\"\"Public health probing endpoint.\"\"\"
    return {"status": "healthy", "service": "OmniCloud Platform"}
""",

        # Controllers
        "backend/controllers/__init__.py": "",
        "backend/controllers/auth_controller.py": """from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from backend.services.auth_service import authenticate_user, register_new_account
from backend.models.user import User

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

@router.post("/login")
async def login(payload: LoginRequest):
    \"\"\"Authenticates user credentials and issues signed JWT bearer token.\"\"\"
    token = authenticate_user(payload.email, payload.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {"access_token": token, "token_type": "bearer"}

@router.post("/register")
async def register(payload: RegisterRequest):
    \"\"\"Enrolls a new customer account in database.\"\"\"
    user = register_new_account(payload.username, payload.email, payload.password)
    return {"status": "created", "user_id": user.id, "email": user.email}
""",

        "backend/controllers/order_controller.py": """from fastapi import APIRouter, HTTPException, Depends
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
    \"\"\"Processes an e-commerce order checkout transaction.\"\"\"
    order = place_order(
        customer_id=payload.customer_id,
        items=[item.model_dump() for item in payload.items],
        shipping_address=payload.shipping_address
    )
    return {"status": "confirmed", "order_id": order.id, "total": order.total_amount}

@router.get("/{order_id}", dependencies=[Depends(verify_jwt_auth)])
async def retrieve_order(order_id: int):
    \"\"\"Fetches complete order breakdown including line items and status.\"\"\"
    order = get_order_details(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order record not found.")
    return {"id": order.id, "status": order.status, "total": order.total_amount}
""",

        "backend/controllers/analytics_controller.py": """from fastapi import APIRouter
from backend.services.billing_service import calculate_aggregate_revenue

router = APIRouter()

@router.get("/dashboard")
async def get_analytics_dashboard():
    \"\"\"Compiles executive KPI performance indicators.\"\"\"
    revenue = calculate_aggregate_revenue()
    return {"daily_volume": 1250, "revenue_total": revenue, "active_tenants": 48}
""",

        # Services
        "backend/services/__init__.py": "",
        "backend/services/auth_service.py": """from typing import Optional
from backend.models.user import User

def authenticate_user(email: str, password: str) -> Optional[str]:
    \"\"\"Verifies hashed credentials and returns JWT signature.\"\"\"
    if email == "admin@omnicloud.io" and password == "secret":
        return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy_access_token"
    return None

def register_new_account(username: str, email: str, password: str) -> User:
    \"\"\"Creates User record entity and initiates activation email.\"\"\"
    new_user = User(id=101, username=username, email=email, role="customer")
    return new_user
""",

        "backend/services/order_service.py": """from typing import List, Dict, Any
from backend.models.order import Order
from backend.models.product import Product
from backend.services.notification_service import dispatch_order_alert

def calculate_discount(price: float, discount_percent: float) -> float:
    \"\"\"Computes promotional rate reduction.\"\"\"
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Invalid discount range")
    return price * (1.0 - (discount_percent / 100.0))

def place_order(customer_id: int, items: List[Dict[str, Any]], shipping_address: str) -> Order:
    \"\"\"Executes business rules, updates inventory, and creates persistent Order record.\"\"\"
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
    \"\"\"Queries order entity from data layer.\"\"\"
    return Order(id=order_id, customer_id=42, status="shipped", total_amount=199.95)
""",

        "backend/services/notification_service.py": """def dispatch_order_alert(order_id: int, customer_id: int):
    \"\"\"Enqueues push notification and customer receipt email.\"\"\"
    print(f"Dispatched confirmation alert for Order #{order_id} to customer #{customer_id}")
""",

        # Intentional Circular Dependency Loop for Topology Detection
        "backend/services/billing_service.py": """from backend.services.invoice_service import generate_invoice_reference

def calculate_aggregate_revenue() -> float:
    \"\"\"Aggregates tenant billing volume.\"\"\"
    ref = generate_invoice_reference("TENANT-99")
    return 84250.50

def get_billing_status(account_id: str) -> str:
    return "current"
""",

        "backend/services/invoice_service.py": """from backend.services.billing_service import get_billing_status

def generate_invoice_reference(tenant_id: str) -> str:
    \"\"\"Generates unique ledger receipt code with billing verification.\"\"\"
    status = get_billing_status(tenant_id)
    return f"INV-{tenant_id}-{status.upper()}"
""",

        # Database Models (SQLAlchemy)
        "backend/models/__init__.py": "",
        "backend/models/user.py": """from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="customer")
    is_active = Column(Boolean, default=True)

    orders = relationship("Order", back_populates="customer")
""",

        "backend/models/order.py": """from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(30), default="pending")
    total_amount = Column(Float, nullable=False)
    shipping_address = Column(String(255), nullable=False)

    customer = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
""",

        "backend/models/product.py": """from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(40), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    inventory_count = Column(Integer, default=0)
""",

        # -------------------------------------------------------------
        # 3. TYPESCRIPT & REACT FRONTEND (Presentation Layer)
        # -------------------------------------------------------------
        "frontend/src/types/models.ts": """export interface UserProfile {
  id: number;
  username: string;
  email: string;
  role: 'customer' | 'admin';
}

export interface OrderRecord {
  id: number;
  total_amount: number;
  status: 'pending' | 'processing' | 'shipped' | 'cancelled';
  items_count: number;
}
""",

        "frontend/src/services/apiClient.ts": """import axios from 'axios';
import { OrderRecord, UserProfile } from '../types/models';

const API_BASE = '/api/v1';

export const apiClient = {
  async fetchOrders(): Promise<OrderRecord[]> {
    const res = await fetch(`${API_BASE}/orders`);
    return res.json();
  },

  async createOrder(payload: { customer_id: number; items: any[]; shipping_address: string }) {
    return axios.post(`${API_BASE}/orders`, payload);
  },

  async login(email: string, password: string) {
    return axios.post(`${API_BASE}/auth/login`, { email, password });
  }
};
""",

        "frontend/src/components/OrderDashboard.tsx": """import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/apiClient';
import { OrderRecord } from '../types/models';

export const OrderDashboard: React.FC = () => {
  const [orders, setOrders] = useState<OrderRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.fetchOrders().then((data) => {
      setOrders(data);
      setLoading(false);
    });
  }, []);

  const handleCreateSample = async () => {
    await apiClient.createOrder({
      customer_id: 42,
      shipping_address: '100 Innovation Way',
      items: [{ product_id: 1, quantity: 2, unit_price: 29.99 }]
    });
  };

  return (
    <div className="p-6 bg-slate-900 text-white rounded-xl">
      <h2 className="text-xl font-bold">Enterprise Order Management</h2>
      <button onClick={handleCreateSample} className="mt-4 px-4 py-2 bg-indigo-600 rounded">
        Submit Order
      </button>
      {loading ? <p>Loading orders...</p> : <p>Total Orders Loaded: {orders.length}</p>}
    </div>
  );
};
""",

        # -------------------------------------------------------------
        # 4. JAVA SPRING BOOT MICROSERVICE
        # -------------------------------------------------------------
        "services/payment_service/src/main/java/com/omnicloud/payment/PaymentController.java": """package com.omnicloud.payment;

import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class PaymentController {

    private final PaymentProcessor processor = new PaymentProcessor();

    @PostMapping("/charge")
    public Map<String, Object> chargeCard(@RequestBody Map<String, Object> chargeRequest) {
        double amount = ((Number) chargeRequest.getOrDefault("amount", 0.0)).doubleValue();
        String customer = (String) chargeRequest.get("customer_id");
        return processor.executeCharge(customer, amount);
    }

    @GetMapping("/verify/{transactionId}")
    public Map<String, Object> verifyPayment(@PathVariable String transactionId) {
        return Map.of("transaction_id", transactionId, "status", "settled");
    }
}
""",

        "services/payment_service/src/main/java/com/omnicloud/payment/PaymentProcessor.java": """package com.omnicloud.payment;

import java.util.Map;
import java.util.UUID;

public class PaymentProcessor {

    public Map<String, Object> executeCharge(String customerId, double amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("Amount must be greater than zero");
        }
        String txId = "TXN-" + UUID.randomUUID().toString().substring(0, 8);
        return Map.of(
            "transaction_id", txId,
            "customer_id", customerId,
            "status", "authorized",
            "amount", amount
        );
    }
}
""",

        "services/payment_service/src/main/java/com/omnicloud/payment/PaymentEntity.java": """package com.omnicloud.payment;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Column;

@Entity
@Table(name = "payment_transactions")
public class PaymentEntity {

    @Id
    private String transactionId;

    @Column(nullable = false)
    private Double amount;

    @Column(nullable = false)
    private String status;

    public String getTransactionId() { return transactionId; }
    public void setTransactionId(String id) { this.transactionId = id; }
}
""",

        # -------------------------------------------------------------
        # 5. JAVASCRIPT & PRISMA DATA LAYER
        # -------------------------------------------------------------
        "services/node_webhooks/webhookRouter.js": """const express = require('express');
const router = express.Router();

router.post('/webhooks/stripe', (req, res) => {
    const event = req.body;
    if (event.type === 'payment_intent.succeeded') {
        console.log('Payment succeeded:', event.data.object.id);
    }
    res.json({ received: true });
});

router.get('/webhooks/status', (req, res) => {
    res.json({ service: 'Webhook Consumer', status: 'online' });
});

module.exports = router;
""",

        "prisma/schema.prisma": """datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model AuditLog {
  id        String   @id @default(uuid())
  action    String
  actorId   String
  timestamp DateTime @default(now())
  metadata  String?
}
""",

        # -------------------------------------------------------------
        # 6. CONFIG & CREDENTIAL SCANNER DEMO
        # -------------------------------------------------------------
        "config/system_env.txt": """# Enterprise Service Defaults
API_TIMEOUT_SECONDS=30
LOG_LEVEL=INFO
# Note: Demo credential for security finding demonstration:
DEMO_GATEWAY_KEY="AKIAIOSFODNN7EXAMPLE"
"""
    }

    # Write all files to disk
    for rel_path, content in files.items():
        dest = base_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")

    # Package into root omnicloud_showcase.zip
    zip_dest = Path("omnicloud_showcase.zip")
    with zipfile.ZipFile(zip_dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in base_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(base_dir).as_posix()
                zf.write(file_path, arcname)

    # Also copy to frontend public so it can be loaded with 1 click
    public_dest = Path("frontend/dist/omnicloud_showcase.zip")
    if public_dest.parent.is_dir():
        import shutil
        shutil.copy2(zip_dest, public_dest)

    print(f"Successfully generated {zip_dest.name} ({zip_dest.stat().st_size} bytes)")

if __name__ == "__main__":
    create_showcase_project()
