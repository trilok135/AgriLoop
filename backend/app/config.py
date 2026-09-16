import json
from typing import Dict, Any
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./agriloop.db"
    
    # App
    demo_mode: bool = True
    secret_key: str = "dev-secret-change-in-production"
    app_name: str = "AgriLoop API"
    app_version: str = "1.0.0"
    
    # Payment
    payment_provider: str = "mock"
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    
    # E-way bill
    eway_bill_provider: str = "mock"
    eway_bill_api_url: str = ""
    eway_bill_username: str = ""
    eway_bill_password: str = ""
    
    # AI Layer
    ai_provider: str = "mock"
    ai_api_url: str = ""
    
    # Reference prices (JSON string)
    reference_prices_json: str = '{"paddy_straw": {"region": "TN", "season": "2026-KHARIF", "rate_per_kg": 3.0}}'
    
    # Fees & Thresholds
    daily_custody_fee_per_bale: float = 5.0
    max_weight_deviation_percent: float = 10.0
    max_moisture_percentage: float = 20.0
    min_density: float = 80.0
    max_density: float = 150.0
    
    # File storage
    static_files_path: str = "static"
    qr_codes_path: str = "static/qr"
    documents_path: str = "static/documents"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def reference_prices(self) -> Dict[str, Any]:
        return json.loads(self.reference_prices_json)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
