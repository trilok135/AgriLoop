import os
import pytest
from app.models import Bale, User, UserRole, BaleStatus, Transaction, TransactionStatus, PaymentStatus, DocumentType
from app.integrations.ai_layer import get_ai_provider, MockAIDataProvider
from app.integrations.payment_gateway import get_payment_gateway, MockPaymentGateway
from app.integrations.eway_bill import get_eway_bill_provider, MockEWayBillProvider
from app.services.qr_service import qr_service
from app.services.verification_service import verification_service
from app.services.custody_service import CustodyService
from app.services.document_service import DocumentService
from app.services.payment_service import PaymentService
from app.services.transaction_service import TransactionService


def test_ai_provider_mock():
    provider = get_ai_provider()
    assert isinstance(provider, MockAIDataProvider)
    
    score = provider.get_risk_score("HUB001")
    assert score["risk_score"] == 87
    assert score["risk_level"] == "HIGH"
    
    score_default = provider.get_risk_score("HUB_UNKNOWN")
    assert score_default["risk_score"] == 50
    assert score_default["risk_level"] == "MEDIUM"


def test_qr_service():
    path = qr_service.generate_qr("CERT-TEST-001", "BAL-TEST-001")
    assert os.path.exists(path)
    url = qr_service.get_qr_url("CERT-TEST-001")
    assert url == "/static/qr/CERT-TEST-001.png"


def test_payment_gateway_mock():
    gateway = get_payment_gateway()
    assert isinstance(gateway, MockPaymentGateway)
    
    res = gateway.create_payment(1440.0, "TXN-TEST-001")
    assert res["status"] == "SUCCESS"
    assert res["amount"] == 1440.0


def test_eway_bill_mock(db):
    bale = Bale(
        bale_id="BAL-EWB-001",
        certificate_id="CERT-EWB-001",
        farmer_id="F001",
        operator_id=1,
        crop_type="Paddy",
        residue_type="Paddy Straw",
        declared_weight=500.0,
        hub_id="HUB001"
    )
    db.add(bale)
    db.flush()
    
    txn = Transaction(
        transaction_id="TXN-EWB-001",
        bale_id=bale.id,
        verified_weight=480.0,
        reference_rate=3.0,
        total_amount=1440.0,
        status=TransactionStatus.PENDING
    )
    db.add(txn)
    db.flush()
    
    provider = get_eway_bill_provider()
    assert isinstance(provider, MockEWayBillProvider)
    ewb = provider.generate(txn)
    assert ewb["document_type"] == "E_WAY_BILL"
    assert ewb["status"] == "GENERATED"
    assert ewb["document_id"] == "EWB-MOCK-TXN-EWB-001"


def test_verification_service():
    class DummyBale:
        declared_weight = 500.0
    
    class DummyWeigh:
        measured_weight = 480.0
        moisture = 15.0
        density = 100.0
    
    res = verification_service.verify(DummyBale(), DummyWeigh())
    assert res["verified"] is True
    assert res["weight_deviation_percent"] == 4.0
    assert res["moisture_valid"] is True
    assert res["density_valid"] is True
    
    # Failing moisture test
    class DummyWeighHighMoisture:
        measured_weight = 480.0
        moisture = 25.0
        density = 100.0
    
    res_fail = verification_service.verify(DummyBale(), DummyWeighHighMoisture())
    assert res_fail["verified"] is False
    assert res_fail["moisture_valid"] is False
