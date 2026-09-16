import json
import os
from typing import Dict, Any
from app.config import get_settings
from app.models import Bale, Pool
from sqlalchemy.orm import Session

settings = get_settings()


class MockAIDataProvider:
    """Mock AI provider that reads from static JSON file."""
    
    def __init__(self):
        self.data_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "risk_scores.json")
        self._risk_data = None
    
    def _load_risk_data(self) -> Dict[str, Any]:
        if self._risk_data is None:
            try:
                with open(self.data_path, "r") as f:
                    self._risk_data = json.load(f)
            except FileNotFoundError:
                self._risk_data = {}
        return self._risk_data
    
    def get_risk_score(self, hub_id: str) -> Dict[str, Any]:
        data = self._load_risk_data()
        return data.get(hub_id, {"risk_score": 50, "risk_level": "MEDIUM"})
    
    def get_pooling_recommendation(self, bale: Bale) -> Dict[str, Any]:
        risk_data = self.get_risk_score(bale.hub_id)
        risk_score = risk_data.get("risk_score", 50)
        risk_level = risk_data.get("risk_level", "MEDIUM")
        
        # Determine priority based on risk level
        if risk_level == "HIGH":
            priority = "HIGH"
        elif risk_level == "MEDIUM":
            priority = "MEDIUM"
        else:
            priority = "LOW"
        
        # Generate pool ID
        pool_id = f"POOL-{risk_level.upper()}-{bale.hub_id[-3:]}"
        
        return {
            "pool_id": pool_id,
            "hub_id": bale.hub_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "priority": priority
        }


class PoolingService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_provider = MockAIDataProvider()
    
    def assign_pool(self, bale: Bale) -> Pool:
        """Assign bale to a pool based on AI recommendation."""
        recommendation = self.ai_provider.get_pooling_recommendation(bale)
        
        # Check if pool exists, create if not
        pool = self.db.query(Pool).filter(Pool.pool_id == recommendation["pool_id"]).first()
        if not pool:
            pool = Pool(
                pool_id=recommendation["pool_id"],
                hub_id=recommendation["hub_id"],
                risk_score=recommendation["risk_score"],
                risk_level=recommendation["risk_level"],
                priority=recommendation["priority"]
            )
            self.db.add(pool)
            self.db.flush()
        
        # Update bale
        bale.pool_id = pool.pool_id
        bale.status = bale.status.__class__.POOLED
        
        return pool


def get_pooling_recommendation(bale: Bale) -> Dict[str, Any]:
    """Standalone function for getting pooling recommendation (for AI layer interface)."""
    provider = MockAIDataProvider()
    return provider.get_pooling_recommendation(bale)
