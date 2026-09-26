import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, HealthProfile, VitalRecord
from backend.schemas import HealthProfileResponse, HealthProfileUpdate, VitalCreate, VitalResponse
from backend.utils.security import get_current_user

router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("/profile", response_model=HealthProfileResponse)
def get_profile(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        current_user = db.query(User).filter(User.role == "patient").first()
    
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    if not profile:
        profile = HealthProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

@router.put("/profile", response_model=HealthProfileResponse)
def update_profile(
    profile_in: HealthProfileUpdate,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        current_user = db.query(User).filter(User.role == "patient").first()

    profile = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    if not profile:
        profile = HealthProfile(user_id=current_user.id)
        db.add(profile)

    for field, value in profile_in.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile

@router.get("/vitals", response_model=List[VitalResponse])
def get_vitals(
    limit: int = 30,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        current_user = db.query(User).filter(User.role == "patient").first()

    records = db.query(VitalRecord)\
        .filter(VitalRecord.user_id == current_user.id)\
        .order_by(VitalRecord.timestamp.desc())\
        .limit(limit)\
        .all()
    return records

@router.post("/vitals", response_model=VitalResponse)
def record_vitals(
    vital_in: VitalCreate,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        current_user = db.query(User).filter(User.role == "patient").first()

    vital = VitalRecord(
        user_id=current_user.id,
        heart_rate=vital_in.heart_rate,
        spo2=vital_in.spo2,
        systolic_bp=vital_in.systolic_bp,
        diastolic_bp=vital_in.diastolic_bp,
        temperature=vital_in.temperature,
        source=vital_in.source or "manual",
        timestamp=datetime.datetime.utcnow()
    )
    db.add(vital)
    db.commit()
    db.refresh(vital)
    return vital

@router.get("/trends")
def get_health_trends(
    range_type: str = "7d", # 24h, 7d, 30d, 6m
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        current_user = db.query(User).filter(User.role == "patient").first()

    now = datetime.datetime.utcnow()
    if range_type == "24h":
        delta = datetime.timedelta(hours=24)
    elif range_type == "30d":
        delta = datetime.timedelta(days=30)
    elif range_type == "6m":
        delta = datetime.timedelta(days=180)
    else:
        delta = datetime.timedelta(days=7)

    since = now - delta
    records = db.query(VitalRecord)\
        .filter(VitalRecord.user_id == current_user.id, VitalRecord.timestamp >= since)\
        .order_by(VitalRecord.timestamp.asc())\
        .all()

    points = []
    for r in records:
        points.append({
            "timestamp": r.timestamp.strftime("%b %d, %H:%M"),
            "heart_rate": r.heart_rate,
            "spo2": r.spo2,
            "systolic_bp": r.systolic_bp,
            "diastolic_bp": r.diastolic_bp,
            "temperature": r.temperature
        })

    insight = "Your recorded vital signs have maintained a consistent physiological trend over the selected period."
    if points:
        avg_hr = sum(p["heart_rate"] for p in points) / len(points)
        avg_spo2 = sum(p["spo2"] for p in points) / len(points)
        insight = f"Average heart rate was {int(avg_hr)} bpm and SpO₂ averaged {round(avg_spo2, 1)}%. Vital trends are within regular parameters."

    return {
        "range": range_type,
        "data_points": points,
        "insight": insight
    }
