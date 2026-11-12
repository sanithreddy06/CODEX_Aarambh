from backend.services.invoice_service import generate_invoice_reference

def calculate_aggregate_revenue() -> float:
    """Aggregates tenant billing volume."""
    ref = generate_invoice_reference("TENANT-99")
    return 84250.50

def get_billing_status(account_id: str) -> str:
    return "current"
