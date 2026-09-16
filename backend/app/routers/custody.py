from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import CustodyResponse, CustodyEventResponse, DocumentResponse
from app.services.custody_service import get_custody_service
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api", tags=["custody", "documents"])


@router.get("/custody/{bale_id}", response_model=CustodyResponse)
def get_custody(
    bale_id: str,
    db: Session = Depends(get_db)
):
    """Get complete custody timeline for a bale."""
    
    custody_service = get_custody_service(db)
    custody = custody_service.get_custody_timeline(bale_id)
    
    if not custody:
        raise HTTPException(status_code=404, detail="Bale not found")
    
    events = [
        CustodyEventResponse(
            status=e["status"],
            location=e["location"],
            operator_id=e["operator_id"],
            note=e["note"],
            timestamp=e["timestamp"]
        )
        for e in custody["events"]
    ]
    
    return CustodyResponse(
        bale_id=custody["bale_id"],
        current_location=custody["current_location"],
        current_status=custody["current_status"],
        events=events
    )


@router.get("/custody/{bale_id}/fee")
def get_custody_fee(
    bale_id: str,
    db: Session = Depends(get_db)
):
    """Calculate custody fee for a bale."""
    
    custody_service = get_custody_service(db)
    fee = custody_service.calculate_custody_fee(bale_id)
    
    if "error" in fee:
        raise HTTPException(status_code=404, detail=fee["error"])
    
    return fee
