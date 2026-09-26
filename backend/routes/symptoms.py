import json
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, SymptomRecord
from backend.schemas import SymptomCreate, SymptomResponse
from backend.utils.security import get_current_user

router = APIRouter(prefix="/api/symptoms", tags=["Symptom Checker"])

COMMON_SYMPTOMS_LIST = [
    {"id": "fever", "name": "Fever / Elevated Body Temp", "category": "General"},
    {"id": "cough", "name": "Persistent Cough", "category": "Respiratory"},
    {"id": "shortness_of_breath", "name": "Shortness of Breath / Dyspnea", "category": "Respiratory", "red_flag": True},
    {"id": "chest_discomfort", "name": "Chest Discomfort / Tightness", "category": "Cardiovascular", "red_flag": True},
    {"id": "headache", "name": "Moderate to Severe Headache", "category": "Neurological"},
    {"id": "fatigue", "name": "Unusual Fatigue / Lethargy", "category": "General"},
    {"id": "dizziness", "name": "Dizziness / Lightheadedness", "category": "Neurological"},
    {"id": "nausea", "name": "Nausea / Vomiting", "category": "Gastrointestinal"},
    {"id": "body_pain", "name": "Body Pain / Myalgia", "category": "Musculoskeletal"},
    {"id": "sore_throat", "name": "Sore Throat", "category": "ENT"},
    {"id": "palpitations", "name": "Rapid or Fluttering Heartbeat", "category": "Cardiovascular", "red_flag": True}
]

@router.get("/common")
def get_common_symptoms():
    return COMMON_SYMPTOMS_LIST

@router.get("", response_model=List[SymptomResponse])
def get_user_symptoms(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        current_user = db.query(User).filter(User.role == "patient").first()
    return db.query(SymptomRecord)\
        .filter(SymptomRecord.user_id == current_user.id)\
        .order_by(SymptomRecord.timestamp.desc())\
        .all()

@router.post("/analyze")
def analyze_symptoms(
    data: SymptomCreate,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        current_user = db.query(User).filter(User.role == "patient").first()

    symptoms_lower = [s.lower() for s in data.symptoms]
    has_red_flags = any("chest" in s or "breath" in s or "palpitation" in s for s in symptoms_lower)
    
    if has_red_flags or data.severity == "severe":
        triage_category = "Urgent Medical Attention Advised"
        recommendations = [
            "Cardiovascular or respiratory red flags detected. Seek in-person clinical assessment.",
            "Contact your emergency contact or nearest health center.",
            "Rest quietly; avoid physical exertion."
        ]
        urgency = "High"
    elif data.duration_days > 4 or data.severity == "moderate":
        triage_category = "Routine Healthcare Consultation Recommended"
        recommendations = [
            "Persistent symptoms warrant evaluation by a primary healthcare practitioner.",
            "Maintain symptom log and track body temperature twice daily.",
            "Stay well hydrated with warm fluids and electrolyte balance."
        ]
        urgency = "Moderate"
    else:
        triage_category = "Self-Care & Continued Monitoring"
        recommendations = [
            "Adequate hydration and 8 hours of restorative rest.",
            "Over-the-counter supportive relief if recommended by your pharmacist.",
            "Re-assess if symptoms worsen or persist beyond 48 hours."
        ]
        urgency = "Low"

    # Save to history
    record = SymptomRecord(
        user_id=current_user.id if current_user else 1,
        symptoms=json.dumps(data.symptoms),
        severity=data.severity or "mild",
        duration_days=data.duration_days or 1,
        notes=data.notes,
        timestamp=datetime.datetime.utcnow()
    )
    db.add(record)
    db.commit()

    return {
        "symptoms": data.symptoms,
        "triage_category": triage_category,
        "urgency": urgency,
        "recommendations": recommendations,
        "disclaimer": "This symptom assessment is intended for health awareness and education only, not definitive diagnosis."
    }
