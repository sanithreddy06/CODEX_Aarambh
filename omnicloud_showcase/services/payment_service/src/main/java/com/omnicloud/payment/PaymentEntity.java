package com.omnicloud.payment;

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
