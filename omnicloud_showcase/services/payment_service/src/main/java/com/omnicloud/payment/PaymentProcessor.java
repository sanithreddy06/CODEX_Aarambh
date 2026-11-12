package com.omnicloud.payment;

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
