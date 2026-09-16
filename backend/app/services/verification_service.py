import json
from typing import Dict, Any
from app.config import get_settings
from app.models import Bale, WeighEvent

settings = get_settings()


class VerificationService:
    def __init__(self):
        self.max_weight_deviation = settings.max_weight_deviation_percent
        self.max_moisture = settings.max_moisture_percentage
        self.min_density = settings.min_density
        self.max_density = settings.max_density
    
    def verify(self, bale: Bale, weigh_event: WeighEvent) -> Dict[str, Any]:
        """Verify weight, moisture, and density against declared values."""
        declared_weight = bale.declared_weight
        measured_weight = weigh_event.measured_weight
        
        # Weight deviation check
        if declared_weight == 0:
            weight_deviation = 100.0
        else:
            weight_deviation = abs(declared_weight - measured_weight) / declared_weight * 100
        
        weight_valid = weight_deviation <= self.max_weight_deviation
        
        # Moisture check
        moisture = weigh_event.moisture
        moisture_valid = True
        if moisture is not None:
            moisture_valid = moisture <= self.max_moisture
        
        # Density check
        density = weigh_event.density
        density_valid = True
        if density is not None:
            density_valid = self.min_density <= density <= self.max_density
        
        # Overall verification
        verified = weight_valid and moisture_valid and density_valid
        
        details = {
            "declared_weight": declared_weight,
            "measured_weight": measured_weight,
            "weight_deviation_percent": round(weight_deviation, 2),
            "weight_valid": weight_valid,
            "moisture": moisture,
            "moisture_valid": moisture_valid,
            "density": density,
            "density_valid": density_valid,
            "thresholds": {
                "max_weight_deviation_percent": self.max_weight_deviation,
                "max_moisture_percentage": self.max_moisture,
                "min_density": self.min_density,
                "max_density": self.max_density
            }
        }
        
        return {
            "verified": verified,
            "weight_deviation_percent": round(weight_deviation, 2),
            "moisture_valid": moisture_valid,
            "density_valid": density_valid,
            "details": json.dumps(details)
        }


verification_service = VerificationService()
