import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Alert
from backend.schemas import AlertResponse
from backend.utils.security import get_current_user
from backend.websockets.vitals_hub import hub

router = APIRouter(prefix="/api/alerts", tags=["Early Warning Alerts"])

@router.get("", response_model=List[AlertResponse])
def get_alerts(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        current_user = db.query(User).filter(User.role == "patient").first()

    return db.query(Alert)\
        .filter(Alert.user_id == current_user.id)\
        .order_by(Alert.timestamp.desc())\
        .limit(20)\
        .all()

@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "acknowledged"
    db.commit()
    return {"status": "acknowledged", "id": alert_id}

@router.post("/trigger")
def trigger_demo_alert(
    anomaly_type: str = "tachycardia", # tachycardia, hypoxemia, fever, hypertension
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        current_user = db.query(User).filter(User.role == "patient").first()

    hub.set_anomaly(anomaly_type)
    
    # Also save to DB immediately
    titles = {
        "tachycardia": ("Tachycardia Critical Alert", "Heart Rate: 138 bpm", "Sustained resting heart rate exceeded safe threshold of 100 bpm."),
        "hypoxemia": ("Hypoxemia Warning", "SpO₂: 89.2%", "Peripheral blood oxygen dropped below critical minimum of 92%."),
        "fever": ("High Pyrexia Alert", "Temperature: 103.2°F", "Severe body temperature detected indicating febrile infection."),
        "hypertension": ("Hypertension Stage 2", "BP: 168/104 mmHg", "Severe vascular blood pressure spike recorded.")
    }
    
    title, param, msg = titles.get(anomaly_type, ("Health Parameter Warning", "Vitals Anomaly", "Abnormal physiological deviation detected."))
    alert = Alert(
        user_id=current_user.id,
        alert_type=title,
        severity="critical" if anomaly_type != "fever" else "warning",
        detected_parameter=param,
        message=msg,
        status="active",
        timestamp=datetime.datetime.utcnow()
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    return {
        "status": "triggered",
        "anomaly_type": anomaly_type,
        "alert": AlertResponse.model_validate(alert)
    }

@router.post("/reset-anomaly")
def reset_anomaly():
    hub.clear_anomaly()
    return {"status": "normal"}
