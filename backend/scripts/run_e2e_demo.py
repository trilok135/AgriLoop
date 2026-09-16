import os
import sys
import json
import requests
from time import sleep

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from app.main import app

def run_demo():
    print("=" * 60)
    print(" AGRILOOP MVP END-TO-END DEMO EXECUTION")
    print("=" * 60)
    print("Scenario details:")
    print(" - Farmer ID: F001")
    print(" - Crop Type: Paddy")
    print(" - Declared Residue: 500 kg")
    print(" - Hub ID: HUB001")
    print(" - Risk Score: 87 / HIGH")
    print("=" * 60)

    client = TestClient(app)

    # 1. POST /api/bale-certificate
    print("\n[STEP 1] Generating Bale Certificate...")
    cert_payload = {
        "farmer_id": "F001",
        "operator_id": "1",
        "crop_type": "Paddy",
        "residue_type": "Paddy Straw",
        "declared_quantity_kg": 500.0,
        "hub_id": "HUB001",
        "latitude": 10.7905,
        "longitude": 78.7047
    }
    res1 = client.post("/api/bale-certificate", json=cert_payload)
    assert res1.status_code == 201, f"Step 1 Failed: {res1.text}"
    cert_data = res1.json()

    bale_id = cert_data["bale_id"]
    certificate_id = cert_data["certificate_id"]
    qr_code = cert_data["qr_code"]
    print(f"  ✓ Bale ID: {bale_id}")
    print(f"  ✓ Certificate ID: {certificate_id}")
    print(f"  ✓ QR Code generated at: {qr_code}")
    print(f"  ✓ Status: {cert_data['status']}")

    # 2. POST /api/pool
    print("\n[STEP 2] Assigning Bale to Risk-Weighted Collection Pool...")
    pool_payload = {"bale_id": bale_id}
    res2 = client.post("/api/pool", json=pool_payload)
    assert res2.status_code == 200, f"Step 2 Failed: {res2.text}"
    pool_data = res2.json()

    print(f"  ✓ Assigned Pool ID: {pool_data['pool_id']}")
    print(f"  ✓ Hub ID: {pool_data['hub_id']}")
    print(f"  ✓ Risk Score: {pool_data['risk_score']} ({pool_data['risk_level']})")
    print(f"  ✓ Collection Priority: {pool_data['priority']}")

    # 3. POST /api/weigh-event
    print("\n[STEP 3] Recording Weighing & Moisture/Density Verification Event...")
    weigh_payload = {
        "bale_id": bale_id,
        "measured_weight_kg": 480.0,
        "moisture_percentage": 14.5,
        "density": 95.0,
        "operator_id": "+1234567890"  # Will create user if needed or match phone
    }
    # First create operator user with phone +1234567890 in DB if using live DB
    from app.database import SessionLocal
    from app.models import User, UserRole
    db = SessionLocal()
    op = db.query(User).filter(User.phone == "+1234567890").first()
    if not op:
        op = User(phone="+1234567890", role=UserRole.OPERATOR)
        db.add(op)
        db.commit()
    db.close()

    res3 = client.post("/api/weigh-event", json=weigh_payload)
    assert res3.status_code == 200, f"Step 3 Failed: {res3.text}"
    weigh_data = res3.json()

    verif = weigh_data["verification"]
    print(f"  ✓ Quality Verification: VERIFIED ({verif['details']})")
    print(f"    - Weight Deviation: {verif['weight_deviation_percent']}% (Max allowed: 10%)")
    print(f"    - Moisture Valid: {verif['moisture_valid']}")
    print(f"    - Density Valid: {verif['density_valid']}")

    txn = weigh_data["transaction"]
    print(f"  ✓ Transaction ID: {txn['transaction_id']}")
    print(f"    - Verified Weight: {txn['verified_weight']} kg")
    print(f"    - Reference Rate: ₹{txn['reference_rate']}/kg")
    print(f"    - Calculated Total Amount: {txn['verified_weight']} kg × ₹{txn['reference_rate']}/kg = ₹{txn['total_amount']}")

    pymt = weigh_data["payment"]
    print(f"  ✓ Payment Triggered: Payment ID={pymt['payment_id']} (Status: {pymt['status']}, Amount: ₹{pymt['amount']})")
    print(f"  ✓ Documents Generated Count: {weigh_data['documents_generated']}")

    transaction_id = txn["transaction_id"]

    # 4. GET /api/documents/:transactionId
    print("\n[STEP 4] Retrieving Generated Digital Documents...")
    res4 = client.get(f"/api/documents/{transaction_id}")
    assert res4.status_code == 200, f"Step 4 Failed: {res4.text}"
    docs = res4.json()

    for doc in docs:
        print(f"  ✓ Document Type: {doc['document_type']:<15} | ID: {doc['document_id']:<30} | URL: {doc['url']}")

    # 5. GET /api/custody/:baleId
    print("\n[STEP 5] Retrieving Complete Chain-of-Custody Timeline...")
    res5 = client.get(f"/api/custody/{bale_id}")
    assert res5.status_code == 200, f"Step 5 Failed: {res5.text}"
    custody = res5.json()

    print(f"  ✓ Current Location: {custody['current_location']}")
    print(f"  ✓ Current Status:   {custody['current_status']}")
    print("  ✓ Timeline Events:")
    for ev in custody["events"]:
        print(f"     - [{ev['timestamp']}] {ev['status']:<12} at Location: {str(ev['location']):<10} | Note: {ev['note']}")

    print("\n" + "=" * 60)
    print(" AGRILOOP MVP END-TO-END DEMO SUCCESSFUL!")
    print("=" * 60)

if __name__ == "__main__":
    run_demo()
