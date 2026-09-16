from abc import ABC, abstractmethod
from typing import Dict, Any
from app.config import get_settings
from app.models import Transaction
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class EWayBillProvider(ABC):
    """Abstract E-way bill provider."""
    
    @abstractmethod
    def generate(self, transaction: Transaction) -> Dict[str, Any]:
        """Generate e-way bill."""
        pass


class MockEWayBillProvider(EWayBillProvider):
    """Mock E-way bill provider for demo/testing."""
    
    def generate(self, transaction: Transaction) -> Dict[str, Any]:
        bale = transaction.bale
        
        logger.info(f"MOCK E-WAY BILL: Generating for transaction {transaction.transaction_id}")
        
        payload = {
            "transaction_id": transaction.transaction_id,
            "bale_id": bale.bale_id,
            "from_location": f"Hub {bale.hub_id}",
            "to_location": "Buyer Location",
            "value": transaction.total_amount,
            "weight": transaction.verified_weight,
            "mode": "MOCK"
        }
        
        # Validate required fields
        required = ["from_location", "to_location", "value", "weight"]
        for field in required:
            if not payload.get(field):
                raise ValueError(f"Missing required field for e-way bill: {field}")
        
        return {
            "document_type": "E_WAY_BILL",
            "status": "GENERATED",
            "document_id": f"EWB-MOCK-{transaction.transaction_id}",
            "mode": "MOCK",
            "payload": payload
        }


class ProductionEWayBillProvider(EWayBillProvider):
    """Production E-way bill provider (GSTN integration)."""
    
    def __init__(self):
        self.api_url = settings.eway_bill_api_url
        self.username = settings.eway_bill_username
        self.password = settings.eway_bill_password
    
    def generate(self, transaction: Transaction) -> Dict[str, Any]:
        # TODO: Implement actual GSTN E-way bill API integration
        # This would require valid credentials and API access
        raise NotImplementedError("Production E-way bill integration not implemented")


def get_eway_bill_provider() -> EWayBillProvider:
    """Factory function to get the configured e-way bill provider."""
    if settings.eway_bill_provider == "production":
        return ProductionEWayBillProvider()
    return MockEWayBillProvider()
