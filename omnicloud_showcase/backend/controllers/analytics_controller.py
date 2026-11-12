from fastapi import APIRouter
from backend.services.billing_service import calculate_aggregate_revenue

router = APIRouter()

@router.get("/dashboard")
async def get_analytics_dashboard():
    """Compiles executive KPI performance indicators."""
    revenue = calculate_aggregate_revenue()
    return {"daily_volume": 1250, "revenue_total": revenue, "active_tenants": 48}
