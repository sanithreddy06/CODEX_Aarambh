package com.omnicloud.payment;

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
