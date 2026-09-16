from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserRole
from app.schemas import SendOTPRequest, VerifyOTPRequest, TokenResponse
from app.config import get_settings
from datetime import datetime, timedelta
import uuid

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["auth"])

# In-memory OTP store for demo (use Redis in production)
otp_store = {}


@router.post("/send-otp")
def send_otp(
    data: SendOTPRequest,
    db: Session = Depends(get_db)
):
    """Send mock OTP to phone number."""
    
    # Generate mock OTP (always 123456 in demo mode)
    if settings.demo_mode:
        otp = "123456"
    else:
        import random
        otp = str(random.randint(100000, 999999))
    
    otp_store[data.phone] = {
        "otp": otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=5)
    }
    
    # Log OTP for demo (NEVER do this in production!)
    print(f"MOCK OTP for {data.phone}: {otp}")
    
    return {
        "message": "OTP sent successfully",
        "demo_otp": otp if settings.demo_mode else None
    }


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(
    data: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    """Verify OTP and return access token."""
    
    stored = otp_store.get(data.phone)
    if not stored:
        raise HTTPException(status_code=400, detail="OTP not found or expired")
    
    if datetime.utcnow() > stored["expires_at"]:
        del otp_store[data.phone]
        raise HTTPException(status_code=400, detail="OTP expired")
    
    if stored["otp"] != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # OTP verified - get or create user
    user = db.query(User).filter(User.phone == data.phone).first()
    if not user:
        user = User(phone=data.phone, role=UserRole.OPERATOR)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Clear OTP
    del otp_store[data.phone]
    
    # Generate simple token (use JWT in production)
    token = f"mock-token-{user.id}-{uuid.uuid4().hex[:16]}"
    
    return TokenResponse(access_token=token)


@router.get("/me")
def get_current_user(
    phone: str,  # In production, get from token
    db: Session = Depends(get_db)
):
    """Get current user info."""
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "phone": user.phone,
        "role": user.role.value,
        "created_at": user.created_at
    }
