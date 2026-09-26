import json
import datetime
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, HealthProfile, VitalRecord, RiskAssessment, Alert, SymptomRecord
from backend.utils.security import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard Summary"])

@router.get("/summary")
def get_dashboard_summary(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        current_user = db.query(User).filter(User.role == "patient").first()
    
    user_id = current_user.id if current_user else 1

    profile = db.query(HealthProfile).filter(HealthProfile.user_id == user_id).first()
    latest_vital = db.query(VitalRecord).filter(VitalRecord.user_id == user_id).order_by(VitalRecord.timestamp.desc()).first()
    latest_risk = db.query(RiskAssessment).filter(RiskAssessment.user_id == user_id).order_by(RiskAssessment.timestamp.desc()).first()
    active_alerts = db.query(Alert).filter(Alert.user_id == user_id, Alert.status == "active").all()
    latest_symptoms = db.query(SymptomRecord).filter(SymptomRecord.user_id == user_id).order_by(SymptomRecord.timestamp.desc()).first()

    # Calculate BMI
    bmi = 24.2
    if profile and profile.height > 0:
        h_m = profile.height / 100.0
        bmi = round(profile.weight / (h_m * h_m), 1)

    return {
        "user": {
            "id": current_user.id if current_user else 1,
            "name": current_user.name if current_user else "Rahul Sharma",
            "email": current_user.email if current_user else "rahul.sharma@example.com",
            "role": current_user.role if current_user else "patient"
        },
        "vitals": {
            "heart_rate": latest_vital.heart_rate if latest_vital else 72.0,
            "spo2": latest_vital.spo2 if latest_vital else 98.4,
            "systolic_bp": latest_vital.systolic_bp if latest_vital else 118.0,
            "diastolic_bp": latest_vital.diastolic_bp if latest_vital else 78.0,
            "temperature": latest_vital.temperature if latest_vital else 98.6,
            "bmi": bmi,
            "last_updated": latest_vital.timestamp.isoformat() if latest_vital else datetime.datetime.utcnow().isoformat()
        },
        "risk": {
            "level": latest_risk.risk_level if latest_risk else "Low Risk",
            "score": latest_risk.risk_score if latest_risk else 18.0,
            "last_assessed": latest_risk.timestamp.isoformat() if latest_risk else None,
            "contributing_factors": json.loads(latest_risk.contributing_factors) if latest_risk else [],
            "recommendations": json.loads(latest_risk.recommendations) if latest_risk else []
        },
        "recent_symptoms": json.loads(latest_symptoms.symptoms) if latest_symptoms else ["None Reported"],
        "active_alerts_count": len(active_alerts),
        "alerts": [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "detected_parameter": a.detected_parameter,
                "timestamp": a.timestamp.isoformat()
            } for a in active_alerts
        ]
    }
