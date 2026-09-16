from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, PyEnum):
    OPERATOR = "operator"
    FARMER = "farmer"
    ADMIN = "admin"


class BaleStatus(str, PyEnum):
    CREATED = "CREATED"
    POOLED = "POOLED"
    STORED = "STORED"
    WEIGHED = "WEIGHED"
    VERIFIED = "VERIFIED"
    PAID = "PAID"
    DISPATCHED = "DISPATCHED"
    DELIVERED = "DELIVERED"


class TransactionStatus(str, PyEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PaymentStatus(str, PyEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class DocumentType(str, PyEnum):
    E_INVOICE = "E_INVOICE"
    E_WAY_BILL = "E_WAY_BILL"
    DISPATCH_NOTE = "DISPATCH_NOTE"
    PAYMENT_RECORD = "PAYMENT_RECORD"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.OPERATOR)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    bales_created = relationship("Bale", back_populates="operator")


class Bale(Base):
    __tablename__ = "bales"
    
    id = Column(Integer, primary_key=True, index=True)
    bale_id = Column(String(50), unique=True, index=True, nullable=False)
    certificate_id = Column(String(50), unique=True, index=True, nullable=False)
    farmer_id = Column(String(50), index=True, nullable=False)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crop_type = Column(String(50), nullable=False)
    residue_type = Column(String(50), nullable=False)
    declared_weight = Column(Float, nullable=False)
    moisture = Column(Float, nullable=True)
    density = Column(Float, nullable=True)
    hub_id = Column(String(50), index=True, nullable=False)
    pool_id = Column(String(50), ForeignKey("pools.pool_id"), index=True, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(Enum(BaleStatus), default=BaleStatus.CREATED, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    operator = relationship("User", back_populates="bales_created")
    pool = relationship("Pool", back_populates="bales", foreign_keys=[pool_id])
    weigh_events = relationship("WeighEvent", back_populates="bale")
    transactions = relationship("Transaction", back_populates="bale")
    custody_events = relationship("CustodyEvent", back_populates="bale")


class Pool(Base):
    __tablename__ = "pools"
    
    id = Column(Integer, primary_key=True, index=True)
    pool_id = Column(String(50), unique=True, index=True, nullable=False)
    hub_id = Column(String(50), index=True, nullable=False)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=False)
    priority = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    bales = relationship("Bale", back_populates="pool")


class WeighEvent(Base):
    __tablename__ = "weigh_events"
    
    id = Column(Integer, primary_key=True, index=True)
    bale_id = Column(Integer, ForeignKey("bales.id"), nullable=False, unique=True)
    measured_weight = Column(Float, nullable=False)
    moisture = Column(Float, nullable=True)
    density = Column(Float, nullable=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    verified = Column(Integer, default=0)
    verification_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    bale = relationship("Bale", back_populates="weigh_events")
    operator = relationship("User")


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, index=True, nullable=False)
    bale_id = Column(Integer, ForeignKey("bales.id"), nullable=False, index=True)
    buyer_id = Column(String(50), nullable=True)
    verified_weight = Column(Float, nullable=False)
    reference_rate = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    bale = relationship("Bale", back_populates="transactions")
    payment = relationship("Payment", back_populates="transaction", uselist=False)
    documents = relationship("Document", back_populates="transaction")


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String(50), unique=True, index=True, nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False, unique=True)
    provider = Column(String(50), nullable=False)
    provider_reference = Column(String(100), nullable=True)
    amount = Column(Float, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    transaction = relationship("Transaction", back_populates="payment")


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(50), unique=True, index=True, nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False, index=True)
    document_type = Column(Enum(DocumentType), nullable=False)
    url = Column(String(500), nullable=False)
    status = Column(String(20), default="GENERATED")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    transaction = relationship("Transaction", back_populates="documents")


class CustodyEvent(Base):
    __tablename__ = "custody_events"
    
    id = Column(Integer, primary_key=True, index=True)
    bale_id = Column(Integer, ForeignKey("bales.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    location = Column(String(100), nullable=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    note = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    bale = relationship("Bale", back_populates="custody_events")
    operator = relationship("User")
