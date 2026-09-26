from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, HealthProfile
from backend.schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from backend.utils.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    user = User(
        name=user_in.name,
        email=user_in.email,
        phone=user_in.phone,
        password_hash=hash_password(user_in.password),
        role=user_in.role or "patient"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialize health profile
    profile = HealthProfile(
        user_id=user.id,
        emergency_contact_name=user_in.emergency_contact_name or "Emergency Contact",
        emergency_contact_phone=user_in.emergency_contact_phone or "+91 98765 43210",
        emergency_contact_relationship=user_in.emergency_contact_relationship or "Family"
    )
    db.add(profile)
    db.commit()

    token = create_access_token({"sub": user.email, "role": user.role, "id": user.id})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.email == login_data.email) | (User.phone == login_data.email)
    ).first()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your email/phone and password."
        )

    token = create_access_token({"sub": user.email, "role": user.role, "id": user.id})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return UserResponse.model_validate(current_user)
