from fastapi import FastAPI, Depends, HTTPException, Header
from backend.controllers.auth_controller import router as auth_router
from backend.controllers.order_controller import router as order_router
from backend.controllers.analytics_controller import router as analytics_router

app = FastAPI(title="OmniCloud Core Enterprise API", version="2.4.0")

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(order_router, prefix="/api/v1/orders", tags=["Orders"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])

@app.get("/api/v1/health")
async def health_check():
    """Public health probing endpoint."""
    return {"status": "healthy", "service": "OmniCloud Platform"}
