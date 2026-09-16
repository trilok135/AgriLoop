import pytest
from app.models import User, UserRole


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["demo_mode"] is True


def test_auth_otp_flow(client):
    # Send OTP
    res_otp = client.post("/api/auth/send-otp", json={"phone": "9876543210"})
    assert res_otp.status_code == 200
    assert res_otp.json()["demo_otp"] == "123456"

    # Verify OTP
    res_verify = client.post("/api/auth/verify-otp", json={"phone": "9876543210", "otp": "123456"})
    assert res_verify.status_code == 200
    token = res_verify.json()["access_token"]
    assert token.startswith("mock-token-")

    # Get Current User
    res_me = client.get("/api/auth/me?phone=9876543210")
    assert res_me.status_code == 200
    assert res_me.json()["phone"] == "9876543210"


def test_bale_lifecycle_api_flow(client, db):
    # 1. Create operator user
    operator = User(phone="9998887770", role=UserRole.OPERATOR)
    db.add(operator)
    db.commit()
    db.refresh(operator)

    # 2. POST /api/bale-certificate
    cert_req = {
        "farmer_id": "F001",
        "operator_id": str(operator.id),
        "crop_type": "Paddy",
        "residue_type": "Paddy Straw",
        "declared_quantity_kg": 500.0,
        "hub_id": "HUB001",
        "latitude": 10.7905,
        "longitude": 78.7047
    }
    cert_res = client.post("/api/bale-certificate", json=cert_req)
    assert cert_res.status_code == 201
    cert_data = cert_res.json()
    bale_id = cert_data["bale_id"]
    certificate_id = cert_data["certificate_id"]
    assert cert_data["status"] == "CREATED"
    assert cert_data["qr_code"] == f"/static/qr/{certificate_id}.png"

    # 3. GET /api/bale/{bale_id}
    bale_info = client.get(f"/api/bale/{bale_id}")
    assert bale_info.status_code == 200
    assert bale_info.json()["farmer_id"] == "F001"

    # 4. POST /api/pool
    pool_req = {"bale_id": bale_id}
    pool_res = client.post("/api/pool", json=pool_req)
    assert pool_res.status_code == 200
    pool_data = pool_res.json()
    assert pool_data["bale_id"] == bale_id
    assert pool_data["hub_id"] == "HUB001"
    assert pool_data["risk_score"] == 87
    assert pool_data["risk_level"] == "HIGH"

    # 5. POST /api/weigh-event
    weigh_req = {
        "bale_id": bale_id,
        "measured_weight_kg": 480.0,
        "moisture_percentage": 14.5,
        "density": 95.0,
        "operator_id": "9998887770"
    }
    weigh_res = client.post("/api/weigh-event", json=weigh_req)
    assert weigh_res.status_code == 200
    weigh_data = weigh_res.json()
    
    assert weigh_data["verification"]["verified"] is True
    assert weigh_data["transaction"]["verified_weight"] == 480.0
    assert weigh_data["transaction"]["total_amount"] == 1440.0
    assert weigh_data["payment"]["status"] == "SUCCESS"
    assert weigh_data["documents_generated"] == 4

    txn_id = weigh_data["transaction"]["transaction_id"]

    # 6. GET /api/documents/{transaction_id}
    docs_res = client.get(f"/api/documents/{txn_id}")
    assert docs_res.status_code == 200
    docs = docs_res.json()
    assert len(docs) == 4
    doc_types = [d["document_type"] for d in docs]
    assert "E_INVOICE" in doc_types
    assert "E_WAY_BILL" in doc_types
    assert "DISPATCH_NOTE" in doc_types
    assert "PAYMENT_RECORD" in doc_types

    # 7. GET /api/custody/{bale_id}
    custody_res = client.get(f"/api/custody/{bale_id}")
    assert custody_res.status_code == 200
    custody_data = custody_res.json()
    assert custody_data["bale_id"] == bale_id
    assert len(custody_data["events"]) >= 4

    # 8. GET /api/bale/verify/{bale_id}
    qr_verify_res = client.get(f"/api/bale/verify/{bale_id}")
    assert qr_verify_res.status_code == 200
    verify_data = qr_verify_res.json()
    assert verify_data["bale_id"] == bale_id
    assert verify_data["status"] == "PAID"
