import qrcode
import os
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


class QRService:
    def __init__(self):
        self.output_dir = settings.qr_codes_path
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_qr(self, certificate_id: str, bale_id: str) -> str:
        """Generate QR code for bale certificate."""
        # QR encodes the verification endpoint
        verification_url = f"/api/bale/verify/{bale_id}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(verification_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        filename = f"{certificate_id}.png"
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath)
        
        logger.info(f"QR code generated: {filepath}")
        return filepath
    
    def get_qr_url(self, certificate_id: str) -> str:
        """Get the URL path for the QR code."""
        return f"/static/qr/{certificate_id}.png"


qr_service = QRService()
