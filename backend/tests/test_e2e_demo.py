import pytest
from app.models import User, UserRole, BaleStatus, PaymentStatus


def test_e2e_demo_flow(client, db):
    """
    End-to-End Demo Verification matching exact user prompt requirements:
    Farmer: F001
    Crop: Paddy
    Declared residue: 500 kg
    Hub: HUB001
    Risk: 87 / HIGH
    """
    # 0. Setup Operator
    operator_phone = "9876543210"
    user = db.query(User).filter(User.phone == operator_phone).first()
    if not user:
        user = User(phone=operator_phone, role=UserRole.OPERATOR)
        db.add(user)
        db.commit()
        db.refresh(user)

    # 1. Create Bale Certificate (POST /bale-certificate)
    cert_payload = {
        "farmer_id": "F001",
        "operator_id": str(user.id),
        "crop_type": "Paddy",
        "residue_type": "Paddy Straw",
        "declared_quantity_kg": 500.0,
        "hub_id": "HUB001",
        "latitude": 10.7905,
        "longitude": 78.7047
    }
    
    response = client.post("/api/bale-certificate", json=cert_payload)
    assert response.status_code == 201, f"Failed: {response.text}"
    cert_data = response.json()

    bale_id = cert_data["bale_id"]
    certificate_id = cert_data["certificate_id"]
    qr_code = cert_data["qr_code"]

    assert bale_id.startswith("BAL-2026-")
    assert certificate_id.startswith("CERT-2026-")
    assert cert_data["status"] == BaleStatus.CREATED.value
    assert qr_code == f"/static/qr/{certificate_id}.png"

    print(f"\n[1] Bale Certificate Created: Bale={bale_id}, Cert={certificate_id}, QR={qr_code}")

    # 2. Pool Assignment (POST /pool)
    pool_payload = {"bale_id": bale_id}
    pool_response = client.post("/api/pool", json=pool_payload)
    assert pool_response.status_code == 200, f"Failed: {pool_response.text}"
    pool_data = pool_response.json()

    assert pool_data["bale_id"] == bale_id
    assert pool_data["hub_id"] == "HUB001"
    assert pool_data["risk_score"] == 87
    assert pool_data["risk_level"] == "HIGH"
    assert pool_data["priority"] == "HIGH"

    print(f"[2] Pool Assigned: Pool={pool_data['pool_id']}, Risk={pool_data['risk_score']} ({pool_data['risk_level']}), Priority={pool_data['priority']}")

    # 3. Weigh Event (POST /weigh-event)
    weigh_payload = {
        "bale_id": bale_id,
        "measured_weight_kg": 480.0,
        "moisture_percentage": 14.5,
        "density": 95.0,
        "operator_id": operator_phone
    }
    weigh_response = client.post("/api/weigh-event", json=weigh_payload)
    assert weigh_response.status_code == 200, f"Failed: {weigh_response.text}"
    weigh_data = weigh_response.json()

    # Verification checks
    verif = weigh_data["verification"]
    assert verif["verified"] is True
    assert verif["weight_deviation_percent"] == 4.0  # (500 - 480)/500 * 100 = 4%
    assert verif["moisture_valid"] is True
    assert verif["density_valid"] is True

    # Financial checks
    txn = weigh_data["transaction"]
    assert txn["verified_weight"] == 480.0
    assert txn["reference_rate"] == 3.0
    assert txn["total_amount"] == 1440.0  # 480 kg * 3.0 = 1440.0

    # Payment checks
    pymt = weigh_data["payment"]
    assert pymt["status"] == PaymentStatus.SUCCESS.value
    assert pymt["amount"] == 1440.0

    # Document count
    assert weigh_data["documents_generated"] == 4

    transaction_id = txn["transaction_id"]
    print(f"[3] Weigh Event Verified: Weight=480kg (Dev=4.0%), Total=Rs.1440, Payment={pymt['payment_id']} (SUCCESS)")

    # 4. Fetch Documents (GET /documents/:transactionId)
    docs_response = client.get(f"/api/documents/{transaction_id}")
    assert docs_response.status_code == 200, f"Failed: {docs_response.text}"
    docs = docs_response.json()

    doc_map = {d["document_type"]: d for d in docs}
    assert "E_INVOICE" in doc_map
    assert "E_WAY_BILL" in doc_map
    assert "DISPATCH_NOTE" in doc_map
    assert "PAYMENT_RECORD" in doc_map

    for d_type, d_obj in doc_map.items():
        assert d_obj["status"] == "GENERATED"

    print(f"[4] Documents Verified: Generated {len(docs)} documents for TXN {transaction_id}")

    # 5. Fetch Custody Timeline (GET /custody/:baleId)
    custody_response = client.get(f"/api/custody/{bale_id}")
    assert custody_response.status_code == 200, f"Failed: {custody_response.text}"
    custody_data = custody_response.json()

    assert custody_data["bale_id"] == bale_id
    events = custody_data["events"]
    assert len(events) >= 4

    statuses = [e["status"] for e in events]
    assert "CREATED" in statuses
    assert "POOLED" in statuses
    assert "VERIFIED" in statuses
    assert "PAID" in statuses

    print(f"[5] Custody Timeline Verified: {len(events)} events recorded. Current status: {custody_data['current_status']}")
