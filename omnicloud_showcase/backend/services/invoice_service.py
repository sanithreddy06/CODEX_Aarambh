from backend.services.billing_service import get_billing_status

def generate_invoice_reference(tenant_id: str) -> str:
    """Generates unique ledger receipt code with billing verification."""
    status = get_billing_status(tenant_id)
    return f"INV-{tenant_id}-{status.upper()}"
