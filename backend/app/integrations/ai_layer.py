from abc import ABC, abstractmethod
from typing import Dict, Any, Protocol
import os
import json
from app.models import Bale, WeighEvent
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class AIDataProvider(Protocol):
    """Protocol for AI/Data layer integration."""
    
    def get_risk_score(self, hub_id: str) -> Dict[str, Any]: ...
    
    def get_pooling_recommendation(self, bale: Bale) -> Dict[str, Any]: ...
    
    def verify_quality(self, bale: Bale, weigh_event: WeighEvent) -> Dict[str, Any]: ...


class MockAIDataProvider:
    """Mock AI provider using static data."""
    
    def __init__(self):
        import os
        import json
        self.data_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "risk_scores.json"
        )
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
        result = data.get(hub_id, {"risk_score": 50, "risk_level": "MEDIUM"})
        logger.info(f"MOCK AI: Risk score for {hub_id}: {result}")
        return result
    
    def get_pooling_recommendation(self, bale: Bale) -> Dict[str, Any]:
        risk_data = self.get_risk_score(bale.hub_id)
        risk_score = risk_data.get("risk_score", 50)
        risk_level = risk_data.get("risk_level", "MEDIUM")
        
        if risk_level == "HIGH":
            priority = "HIGH"
        elif risk_level == "MEDIUM":
            priority = "MEDIUM"
        else:
            priority = "LOW"
        
        pool_id = f"POOL-{risk_level.upper()}-{bale.hub_id[-3:]}"
        
        return {
            "pool_id": pool_id,
            "hub_id": bale.hub_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "priority": priority
        }
    
    def verify_quality(self, bale: Bale, weigh_event: WeighEvent) -> Dict[str, Any]:
        # For MVP, use the same verification service
        # Later this could call ML model for quality grading
        from app.services.verification_service import verification_service
        return verification_service.verify(bale, weigh_event)


class LiveAIDataProvider:
    """Live AI provider (to be implemented when AI layer is ready)."""
    
    def __init__(self):
        self.api_url = settings.ai_api_url
    
    def get_risk_score(self, hub_id: str) -> Dict[str, Any]:
        # TODO: Call AI service
        raise NotImplementedError("Live AI provider not implemented")
    
    def get_pooling_recommendation(self, bale: Bale) -> Dict[str, Any]:
        raise NotImplementedError("Live AI provider not implemented")
    
    def verify_quality(self, bale: Bale, weigh_event: WeighEvent) -> Dict[str, Any]:
        raise NotImplementedError("Live AI provider not implemented")


def get_ai_provider() -> AIDataProvider:
    """Factory function to get the configured AI provider."""
    if settings.ai_provider == "live":
        return LiveAIDataProvider()
    return MockAIDataProvider()
