from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.config import get_settings
import requests
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class PaymentGateway(ABC):
    """Abstract payment gateway interface."""
    
    @abstractmethod
    def create_payment(self, amount: float, reference: str) -> Dict[str, Any]:
        """Create a payment and return payment details."""
        pass
    
    @abstractmethod
    def verify_payment(self, payment_id: str) -> Dict[str, Any]:
        """Verify payment status."""
        pass


class MockPaymentGateway(PaymentGateway):
    """Mock payment gateway for demo/testing."""
    
    def create_payment(self, amount: float, reference: str) -> Dict[str, Any]:
        logger.info(f"MOCK PAYMENT: Creating payment for {amount} (ref: {reference})")
        return {
            "payment_id": f"PAY-MOCK-{reference}",
            "status": "SUCCESS",
            "amount": amount,
            "provider": "MOCK",
            "provider_reference": f"MOCK_REF_{reference}"
        }
    
    def verify_payment(self, payment_id: str) -> Dict[str, Any]:
        logger.info(f"MOCK PAYMENT: Verifying payment {payment_id}")
        return {
            "payment_id": payment_id,
            "status": "SUCCESS",
            "provider": "MOCK"
        }


class RazorpayGateway(PaymentGateway):
    """Razorpay payment gateway (test mode)."""
    
    def __init__(self):
        self.key_id = settings.razorpay_key_id
        self.key_secret = settings.razorpay_key_secret
        self.base_url = "https://api.razorpay.com/v1"
    
    def _get_auth(self):
        return (self.key_id, self.key_secret)
    
    def create_payment(self, amount: float, reference: str) -> Dict[str, Any]:
        """Create a Razorpay order."""
        if not self.key_id or not self.key_secret:
            raise ValueError("Razorpay credentials not configured")
        
        url = f"{self.base_url}/orders"
        data = {
            "amount": int(amount * 100),  # Razorpay expects paise
            "currency": "INR",
            "receipt": reference,
            "payment_capture": 1
        }
        
        try:
            response = requests.post(url, json=data, auth=self._get_auth())
            response.raise_for_status()
            order = response.json()
            
            return {
                "payment_id": order["id"],
                "status": "CREATED",
                "amount": amount,
                "provider": "RAZORPAY",
                "provider_reference": order["id"]
            }
        except requests.RequestException as e:
            logger.error(f"Razorpay order creation failed: {e}")
            raise
    
    def verify_payment(self, payment_id: str) -> Dict[str, Any]:
        """Verify Razorpay payment."""
        if not self.key_id or not self.key_secret:
            raise ValueError("Razorpay credentials not configured")
        
        url = f"{self.base_url}/payments/{payment_id}"
        
        try:
            response = requests.get(url, auth=self._get_auth())
            response.raise_for_status()
            payment = response.json()
            
            return {
                "payment_id": payment["id"],
                "status": "SUCCESS" if payment["status"] == "captured" else "FAILED",
                "amount": payment["amount"] / 100,
                "provider": "RAZORPAY",
                "provider_reference": payment["id"]
            }
        except requests.RequestException as e:
            logger.error(f"Razorpay payment verification failed: {e}")
            raise


def get_payment_gateway() -> PaymentGateway:
    """Factory function to get the configured payment gateway."""
    if settings.payment_provider == "razorpay":
        return RazorpayGateway()
    return MockPaymentGateway()
