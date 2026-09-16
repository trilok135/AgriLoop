from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import Bale, Transaction, WeighEvent, TransactionStatus, BaleStatus
from app.services.verification_service import verification_service
from app.services.payment_service import PaymentService
from app.services.document_service import DocumentService
from app.services.custody_service import CustodyService, get_custody_service
from app.config import get_settings
from datetime import datetime
import json
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class TransactionService:
    def __init__(self, db: Session):
        self.db = db
        self.payment_service = PaymentService(db)
        self.document_service = DocumentService(db)
        self.custody_service = get_custody_service(db)
    
    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID."""
        count = self.db.query(Transaction).count() + 1
        return f"TXN-{datetime.utcnow().strftime('%Y%m%d')}-{count:04d}"
    
    def _get_reference_rate(self, residue_type: str, region: str = "TN") -> float:
        """Get reference rate from config."""
        prices = settings.reference_prices
        key = residue_type.lower().replace(" ", "_")
        if key in prices:
            return prices[key].get("rate_per_kg", 3.0)
        return 3.0  # Default
    
    def process_weigh_event(
        self,
        bale: Bale,
        measured_weight: float,
        moisture: Optional[float],
        density: Optional[float],
        operator_id: int
    ) -> Dict[str, Any]:
        """Process weigh event: verify, create transaction, payment, documents."""
        
        # Check if weigh event already exists (idempotency)
        existing_weigh = self.db.query(WeighEvent).filter(
            WeighEvent.bale_id == bale.id
        ).first()
        
        if existing_weigh:
            logger.warning(f"Weigh event already exists for bale {bale.bale_id}")
            # Return existing result
            return self._get_existing_result(bale, existing_weigh)
        
        # Validate bale state
        valid_states = [BaleStatus.POOLED, BaleStatus.STORED, BaleStatus.WEIGHED]
        if bale.status not in valid_states:
            raise ValueError(f"Bale not in valid state for weighing: {bale.status}")
        
        # Create weigh event record
        weigh_event = WeighEvent(
            bale_id=bale.id,
            measured_weight=measured_weight,
            moisture=moisture,
            density=density,
            operator_id=operator_id,
            verified=0
        )
        self.db.add(weigh_event)
        self.db.flush()
        
        # Verify
        verification_result = verification_service.verify(bale, weigh_event)
        verified = verification_result["verified"]
        
        weigh_event.verified = 1 if verified else 0
        weigh_event.verification_details = verification_result["details"]
        
        # Update bale status
        if verified:
            bale.status = BaleStatus.VERIFIED
        else:
            bale.status = BaleStatus.WEIGHED  # Weighed but not verified
        
        self.db.flush()
        
        # Create custody event
        self.custody_service.create_event(
            bale=bale,
            status="WEIGHED" if not verified else "VERIFIED",
            location=bale.hub_id,
            operator_id=operator_id,
            note=f"Weighed: {measured_weight}kg, Verified: {verified}"
        )
        
        result = {
            "verification": {
                "verified": verified,
                "weight_deviation_percent": verification_result["weight_deviation_percent"],
                "moisture_valid": verification_result["moisture_valid"],
                "density_valid": verification_result["density_valid"],
                "details": verification_result["details"]
            }
        }
        
        if verified:
            # Calculate transaction
            reference_rate = self._get_reference_rate(bale.residue_type)
            total_amount = measured_weight * reference_rate
            
            transaction = Transaction(
                transaction_id=self._generate_transaction_id(),
                bale_id=bale.id,
                buyer_id=None,  # Would be set when buyer purchases
                verified_weight=measured_weight,
                reference_rate=reference_rate,
                total_amount=total_amount,
                status=TransactionStatus.PENDING
            )
            
            self.db.add(transaction)
            self.db.flush()
            
            # Process payment
            payment = self.payment_service.process_payment(transaction)
            
            # Generate documents
            documents = self.document_service.generate_all_documents(transaction)
            
            # Update custody
            self.custody_service.create_event(
                bale=bale,
                status="PAID",
                location=bale.hub_id,
                operator_id=operator_id,
                note=f"Payment processed: {payment.payment_id}"
            )
            
            # Update bale status
            bale.status = BaleStatus.PAID
            
            result["transaction"] = {
                "id": transaction.id,
                "transaction_id": transaction.transaction_id,
                "bale_id": bale.bale_id,
                "buyer_id": transaction.buyer_id,
                "verified_weight": transaction.verified_weight,
                "reference_rate": transaction.reference_rate,
                "total_amount": transaction.total_amount,
                "status": transaction.status.value,
                "created_at": transaction.created_at
            }
            
            result["payment"] = {
                "payment_id": payment.payment_id,
                "status": payment.status.value,
                "amount": payment.amount,
                "provider": payment.provider
            }
            
            result["documents_generated"] = len(documents)
            result["message"] = "Weigh event processed successfully. Transaction completed."
        else:
            result["message"] = "Weight verification failed. Transaction not created."
        
        self.db.commit()
        return result
    
    def _get_existing_result(self, bale: Bale, weigh_event: WeighEvent) -> Dict[str, Any]:
        """Get result for existing weigh event (idempotent)."""
        verification = json.loads(weigh_event.verification_details) if weigh_event.verification_details else {}
        
        result = {
            "verification": {
                "verified": bool(weigh_event.verified),
                "weight_deviation_percent": verification.get("weight_deviation_percent", 0),
                "moisture_valid": verification.get("moisture_valid", False),
                "density_valid": verification.get("density_valid", False),
                "details": weigh_event.verification_details
            },
            "message": "Weigh event already recorded (idempotent)"
        }
        
        # Check for existing transaction
        transaction = self.db.query(Transaction).filter(
            Transaction.bale_id == bale.id
        ).first()
        
        if transaction:
            result["transaction"] = {
                "id": transaction.id,
                "transaction_id": transaction.transaction_id,
                "bale_id": bale.bale_id,
                "buyer_id": transaction.buyer_id,
                "verified_weight": transaction.verified_weight,
                "reference_rate": transaction.reference_rate,
                "total_amount": transaction.total_amount,
                "status": transaction.status.value,
                "created_at": transaction.created_at
            }
            
            if transaction.payment:
                result["payment"] = {
                    "payment_id": transaction.payment.payment_id,
                    "status": transaction.payment.status.value,
                    "amount": transaction.payment.amount,
                    "provider": transaction.payment.provider
                }
            
            docs = self.document_service.get_documents(transaction.transaction_id)
            result["documents_generated"] = len(docs)
        
        return result
