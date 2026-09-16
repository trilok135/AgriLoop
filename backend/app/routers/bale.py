from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Bale, User, BaleStatus, Pool
from app.schemas import (
    BaleCertificateCreate, BaleCertificateResponse, BaleResponse,
    PoolAssignRequest, PoolAssignResponse
)
from app.services.qr_service import qr_service
from app.services.pooling_service import PoolingService, get_pooling_recommendation
from app.services.custody_service import get_custody_service
from app.integrations.ai_layer import get_ai_provider
from datetime import datetime
import uuid

router = APIRouter(prefix="/api", tags=["bales"])


def generate_bale_id() -> str:
    """Generate unique bale ID."""
    return f"BAL-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:5].upper()}"


def generate_certificate_id() -> str:
    """Generate unique certificate ID."""
    return f"CERT-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:5].upper()}"


@router.post("/bale-certificate", response_model=BaleCertificateResponse, status_code=status.HTTP_201_CREATED)
def create_bale_certificate(
    data: BaleCertificateCreate,
    db: Session = Depends(get_db)
):
    """Create a digital certificate for a new bale."""
    
    # Validate operator exists
    operator = db.query(User).filter(User.id == int(data.operator_id)).first()
    if not operator:
        # For demo, create operator if not exists
        operator = User(phone=data.operator_id, role="operator")
        db.add(operator)
        db.flush()
    
    # Generate IDs
    bale_id = generate_bale_id()
    certificate_id = generate_certificate_id()
    
    # Create bale record
    bale = Bale(
        bale_id=bale_id,
        certificate_id=certificate_id,
        farmer_id=data.farmer_id,
        operator_id=operator.id,
        crop_type=data.crop_type,
        residue_type=data.residue_type,
        declared_weight=data.declared_quantity_kg,
        hub_id=data.hub_id,
        latitude=data.latitude,
        longitude=data.longitude,
        status=BaleStatus.CREATED
    )
    
    db.add(bale)
    db.flush()
    
    # Generate QR code
    qr_path = qr_service.generate_qr(certificate_id, bale_id)
    qr_url = qr_service.get_qr_url(certificate_id)
    
    # Create initial custody event
    custody_service = get_custody_service(db)
    custody_service.create_event(
        bale=bale,
        status="CREATED",
        location=data.hub_id,
        operator_id=operator.id,
        note=f"Bale certificate created at {data.hub_id}"
    )
    
    db.commit()
    db.refresh(bale)
    
    return BaleCertificateResponse(
        bale_id=bale_id,
        certificate_id=certificate_id,
        status=BaleStatus.CREATED,
        qr_code=qr_url
    )


@router.post("/pool", response_model=PoolAssignResponse)
def assign_pool(
    data: PoolAssignRequest,
    db: Session = Depends(get_db)
):
    """Assign bale to a collection pool based on AI risk assessment."""
    
    bale = db.query(Bale).filter(Bale.bale_id == data.bale_id).first()
    if not bale:
        raise HTTPException(status_code=404, detail="Bale not found")
    
    if bale.status != BaleStatus.CREATED:
        raise HTTPException(
            status_code=400,
            detail=f"Bale must be in CREATED state, current: {bale.status}"
        )
    
    # Get AI recommendation
    ai_provider = get_ai_provider()
    recommendation = ai_provider.get_pooling_recommendation(bale)
    
    # Create or get pool
    pool = db.query(Pool).filter(Pool.pool_id == recommendation["pool_id"]).first()
    if not pool:
        pool = Pool(
            pool_id=recommendation["pool_id"],
            hub_id=recommendation["hub_id"],
            risk_score=recommendation["risk_score"],
            risk_level=recommendation["risk_level"],
            priority=recommendation["priority"]
        )
        db.add(pool)
        db.flush()
    
    # Update bale
    bale.pool_id = pool.pool_id
    bale.status = BaleStatus.POOLED
    
    # Create custody event
    custody_service = get_custody_service(db)
    custody_service.create_event(
        bale=bale,
        status="POOLED",
        location=pool.pool_id,
        operator_id=bale.operator_id,
        note=f"Assigned to pool {pool.pool_id} (risk: {pool.risk_level})"
    )
    
    db.commit()
    db.refresh(bale)
    
    return PoolAssignResponse(
        bale_id=bale.bale_id,
        pool_id=pool.pool_id,
        hub_id=pool.hub_id,
        risk_score=pool.risk_score,
        risk_level=pool.risk_level,
        priority=pool.priority
    )


@router.get("/bale/{bale_id}", response_model=BaleResponse)
def get_bale(
    bale_id: str,
    db: Session = Depends(get_db)
):
    """Get bale details (used by QR verification)."""
    
    bale = db.query(Bale).filter(Bale.bale_id == bale_id).first()
    if not bale:
        raise HTTPException(status_code=404, detail="Bale not found")
    
    return BaleResponse(
        id=bale.id,
        bale_id=bale.bale_id,
        certificate_id=bale.certificate_id,
        farmer_id=bale.farmer_id,
        operator_id=bale.operator_id,
        crop_type=bale.crop_type,
        residue_type=bale.residue_type,
        declared_weight=bale.declared_weight,
        moisture=bale.moisture,
        density=bale.density,
        hub_id=bale.hub_id,
        pool_id=bale.pool_id,
        status=bale.status,
        created_at=bale.created_at
    )


@router.get("/bale/verify/{bale_id}")
def verify_bale_qr(
    bale_id: str,
    db: Session = Depends(get_db)
):
    """QR code verification endpoint - returns current bale status."""
    
    bale = db.query(Bale).filter(Bale.bale_id == bale_id).first()
    if not bale:
        raise HTTPException(status_code=404, detail="Bale not found")
    
    # Get custody timeline
    custody_service = get_custody_service(db)
    custody = custody_service.get_custody_timeline(bale_id)
    
    return {
        "bale_id": bale.bale_id,
        "certificate_id": bale.certificate_id,
        "status": bale.status.value,
        "farmer_id": bale.farmer_id,
        "crop_type": bale.crop_type,
        "residue_type": bale.residue_type,
        "declared_weight": bale.declared_weight,
        "hub_id": bale.hub_id,
        "pool_id": bale.pool_id,
        "created_at": bale.created_at,
        "custody": custody
    }
