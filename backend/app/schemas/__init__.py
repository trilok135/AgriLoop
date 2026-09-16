from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class UserRole(str, Enum):
    OPERATOR = "operator"
    FARMER = "farmer"
    ADMIN = "admin"


class BaleStatus(str, Enum):
    CREATED = "CREATED"
    POOLED = "POOLED"
    STORED = "STORED"
    WEIGHED = "WEIGHED"
    VERIFIED = "VERIFIED"
    PAID = "PAID"
    DISPATCHED = "DISPATCHED"
    DELIVERED = "DELIVERED"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class DocumentType(str, Enum):
    E_INVOICE = "E_INVOICE"
    E_WAY_BILL = "E_WAY_BILL"
    DISPATCH_NOTE = "DISPATCH_NOTE"
    PAYMENT_RECORD = "PAYMENT_RECORD"


# Bale schemas
class BaleCertificateCreate(BaseModel):
    operator_id: str = Field(..., description="Operator ID")
    farmer_id: str = Field(..., description="Farmer ID")
    crop_type: str = Field(..., description="Crop type (e.g., paddy)")
    residue_type: str = Field(..., description="Residue type (e.g., paddy_straw)")
    declared_quantity_kg: float = Field(..., gt=0, description="Declared quantity in kg")
    hub_id: str = Field(..., description="Hub ID")
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class BaleCertificateResponse(BaseModel):
    bale_id: str
    certificate_id: str
    status: BaleStatus
    qr_code: str
    
    class Config:
        from_attributes = True


class BaleResponse(BaseModel):
    id: int
    bale_id: str
    certificate_id: str
    farmer_id: str
    operator_id: int
    crop_type: str
    residue_type: str
    declared_weight: float
    moisture: Optional[float]
    density: Optional[float]
    hub_id: str
    pool_id: Optional[str]
    status: BaleStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


# Pool schemas
class PoolRecommendation(BaseModel):
    pool_id: str
    hub_id: str
    risk_score: int
    risk_level: str
    priority: str


class PoolAssignRequest(BaseModel):
    bale_id: str


class PoolAssignResponse(BaseModel):
    bale_id: str
    pool_id: str
    hub_id: str
    risk_score: int
    risk_level: str
    priority: str
    
    class Config:
        from_attributes = True


# Weigh schemas
class WeighEventCreate(BaseModel):
    bale_id: str = Field(..., description="Bale ID")
    measured_weight_kg: float = Field(..., gt=0, description="Measured weight in kg")
    moisture_percentage: Optional[float] = Field(None, ge=0, le=100, description="Moisture percentage")
    density: Optional[float] = Field(None, gt=0, description="Density")
    operator_id: str = Field(..., description="Operator ID")


class VerificationResult(BaseModel):
    verified: bool
    weight_deviation_percent: float
    moisture_valid: bool
    density_valid: bool
    details: str


class WeighEventResponse(BaseModel):
    id: int
    bale_id: str
    measured_weight: float
    moisture: Optional[float]
    density: Optional[float]
    verified: bool
    verification_details: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Transaction schemas
class TransactionResponse(BaseModel):
    id: int
    transaction_id: str
    bale_id: str
    buyer_id: Optional[str] = None
    verified_weight: float
    reference_rate: float
    total_amount: float
    status: TransactionStatus
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    payment_id: str
    status: PaymentStatus
    amount: float
    provider: str


class WeighEventResult(BaseModel):
    verification: VerificationResult
    transaction: Optional[TransactionResponse]
    payment: Optional[PaymentResponse]
    documents_generated: int
    message: str


# Document schemas
class DocumentResponse(BaseModel):
    document_id: str
    document_type: DocumentType
    url: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# Custody schemas
class CustodyEventResponse(BaseModel):
    status: str
    location: Optional[str]
    operator_id: Optional[int]
    note: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True


class CustodyResponse(BaseModel):
    bale_id: str
    current_location: Optional[str]
    current_status: str
    events: List[CustodyEventResponse]
    
    class Config:
        from_attributes = True


# Auth schemas
class SendOTPRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")


class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Error schemas
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
