from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Bale, BaleStatus
from app.schemas import WeighEventCreate, WeighEventResult, VerificationResult
from app.services.transaction_service import TransactionService
import logging

router = APIRouter(prefix="/api", tags=["weigh"])
logger = logging.getLogger(__name__)


@router.post("/weigh-event", response_model=WeighEventResult)
def create_weigh_event(
    data: WeighEventCreate,
    db: Session = Depends(get_db)
):
    """Record weigh event - triggers verification, payment, and document generation."""
    
    bale = db.query(Bale).filter(Bale.bale_id == data.bale_id).first()
    if not bale:
        raise HTTPException(status_code=404, detail="Bale not found")
    
    # Validate bale state for weighing
    valid_states = [BaleStatus.POOLED, BaleStatus.STORED, BaleStatus.WEIGHED]
    if bale.status not in valid_states:
        raise HTTPException(
            status_code=400,
            detail=f"Bale must be in POOLED/STORED/WEIGHED state for weighing, current: {bale.status}"
        )
    
    # Find operator
    from app.models import User
    operator = db.query(User).filter(User.phone == data.operator_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    
    # Process weigh event
    transaction_service = TransactionService(db)
    
    try:
        result = transaction_service.process_weigh_event(
            bale=bale,
            measured_weight=data.measured_weight_kg,
            moisture=data.moisture_percentage,
            density=data.density,
            operator_id=operator.id
        )
        
        return WeighEventResult(
            verification=VerificationResult(**result["verification"]),
            transaction=result.get("transaction"),
            payment=result.get("payment"),
            documents_generated=result.get("documents_generated", 0),
            message=result["message"]
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Weigh event processing failed: {e}")
        raise HTTPException(status_code=500, detail="Weigh event processing failed")
