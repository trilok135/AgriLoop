from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import Payment, Transaction, PaymentStatus
from app.integrations.payment_gateway import get_payment_gateway
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.gateway = get_payment_gateway()
    
    def process_payment(self, transaction: Transaction) -> Payment:
        """Process payment for a transaction."""
        # Check if payment already exists
        existing_payment = self.db.query(Payment).filter(
            Payment.transaction_id == transaction.id
        ).first()
        
        if existing_payment:
            if existing_payment.status == PaymentStatus.SUCCESS:
                logger.info(f"Payment already successful for transaction {transaction.transaction_id}")
                return existing_payment
            # If failed/pending, we can retry
        
        # Create payment via gateway
        reference = f"TXN-{transaction.transaction_id}"
        gateway_result = self.gateway.create_payment(transaction.total_amount, reference)
        
        # Create payment record
        payment = Payment(
            payment_id=gateway_result["payment_id"],
            transaction_id=transaction.id,
            provider=gateway_result["provider"],
            provider_reference=gateway_result.get("provider_reference"),
            amount=gateway_result["amount"],
            status=PaymentStatus(gateway_result["status"])
        )
        
        self.db.add(payment)
        self.db.flush()
        
        # If gateway returned CREATED (like Razorpay), we may need to verify
        if payment.status == PaymentStatus.PENDING or payment.status.__class__.__name__ == "CREATED":
            # In production, this would be async via webhook
            # For demo, we'll verify immediately if mock
            if settings.payment_provider == "mock":
                payment.status = PaymentStatus.SUCCESS
        
        # Update transaction status
        if payment.status == PaymentStatus.SUCCESS:
            transaction.status = transaction.status.__class__.COMPLETED
        
        self.db.commit()
        self.db.refresh(payment)
        
        return payment
    
    def verify_payment(self, payment: Payment) -> Payment:
        """Verify payment status with gateway."""
        gateway_result = self.gateway.verify_payment(payment.payment_id)
        
        payment.status = PaymentStatus(gateway_result["status"])
        
        # Update transaction
        transaction = self.db.query(Transaction).filter(
            Transaction.id == payment.transaction_id
        ).first()
        
        if transaction:
            if payment.status == PaymentStatus.SUCCESS:
                transaction.status = transaction.status.__class__.COMPLETED
            elif payment.status == PaymentStatus.FAILED:
                transaction.status = transaction.status.__class__.FAILED
        
        self.db.commit()
        self.db.refresh(payment)
        
        return payment
