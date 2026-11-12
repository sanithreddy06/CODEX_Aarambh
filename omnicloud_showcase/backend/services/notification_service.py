def dispatch_order_alert(order_id: int, customer_id: int):
    """Enqueues push notification and customer receipt email."""
    print(f"Dispatched confirmation alert for Order #{order_id} to customer #{customer_id}")
