from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import Bale, CustodyEvent, BaleStatus
from app.config import get_settings
from datetime import datetime, timedelta
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class CustodyService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_event(
        self,
        bale: Bale,
        status: str,
        location: Optional[str] = None,
        operator_id: Optional[int] = None,
        note: Optional[str] = None
    ) -> CustodyEvent:
        """Create a custody event for a bale."""
        event = CustodyEvent(
            bale_id=bale.id,
            status=status,
            location=location,
            operator_id=operator_id,
            note=note,
            timestamp=datetime.utcnow()
        )
        
        self.db.add(event)
        
        # Update bale current status/location
        bale.status = BaleStatus(status)
        if location:
            bale.pool_id = location  # Using pool_id as current location for simplicity
        
        self.db.flush()
        return event
    
    def get_custody_timeline(self, bale_id: str) -> Dict[str, Any]:
        """Get complete custody timeline for a bale."""
        bale = self.db.query(Bale).filter(Bale.bale_id == bale_id).first()
        if not bale:
            return None
        
        events = self.db.query(CustodyEvent).filter(
            CustodyEvent.bale_id == bale.id
        ).order_by(CustodyEvent.timestamp).all()
        
        event_list = [
            {
                "status": e.status,
                "location": e.location,
                "operator_id": e.operator_id,
                "note": e.note,
                "timestamp": e.timestamp
            }
            for e in events
        ]
        
        current_location = bale.pool_id or bale.hub_id
        current_status = bale.status.value
        
        return {
            "bale_id": bale.bale_id,
            "current_location": current_location,
            "current_status": current_status,
            "events": event_list
        }
    
    def calculate_custody_fee(self, bale_id: str) -> Dict[str, Any]:
        """Calculate custody fee for a bale."""
        bale = self.db.query(Bale).filter(Bale.bale_id == bale_id).first()
        if not bale:
            return {"error": "Bale not found"}
        
        events = self.db.query(CustodyEvent).filter(
            CustodyEvent.bale_id == bale.id
        ).order_by(CustodyEvent.timestamp).all()
        
        if not events:
            return {"days_in_custody": 0, "fee": 0}
        
        # Find CREATED and DISPATCHED/DELIVERED events
        created_event = next((e for e in events if e.status == "CREATED"), None)
        dispatch_event = next((e for e in events if e.status in ["DISPATCHED", "DELIVERED"]), None)
        
        start_time = created_event.timestamp if created_event else bale.created_at
        end_time = dispatch_event.timestamp if dispatch_event else datetime.utcnow()
        
        days = (end_time - start_time).days
        if days < 1:
            days = 1  # Minimum 1 day
        
        daily_fee = settings.daily_custody_fee_per_bale
        total_fee = days * daily_fee
        
        return {
            "bale_id": bale_id,
            "days_in_custody": days,
            "daily_fee": daily_fee,
            "total_fee": total_fee,
            "start_date": start_time,
            "end_date": end_time,
            "status": "active" if not dispatch_event else "closed"
        }


def get_custody_service(db: Session) -> CustodyService:
    return CustodyService(db)
