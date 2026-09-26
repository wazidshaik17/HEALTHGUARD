import json
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, HealthProfile, RiskAssessment, Alert, VitalRecord
from backend.schemas import RiskPredictRequest, RiskAssessmentResponse
from backend.utils.security import get_current_user
from backend.ai.risk_predictor import evaluate_risk

router = APIRouter(prefix="/api/risk", tags=["AI Risk Assessment"])

@router.post("/predict", response_model=RiskAssessmentResponse)
def assess_risk(
    req: RiskPredictRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        current_user = db.query(User).filter(User.role == "patient").first()

    # Pre-fill profile info if not supplied in request
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first() if current_user else None
    
    data = req.model_dump()
    if profile:
        if not data.get("age"): data["age"] = profile.age
        if not data.get("gender"): data["gender"] = profile.gender
        if not data.get("height"): data["height"] = profile.height
        if not data.get("weight"): data["weight"] = profile.weight
        if data.get("sleep_hours") is None: data["sleep_hours"] = profile.sleep_hours
        if data.get("physical_activity") is None: data["physical_activity"] = profile.physical_activity
        if data.get("smoking") is None: data["smoking"] = profile.smoking
        if data.get("alcohol") is None: data["alcohol"] = profile.alcohol
        if not data.get("existing_conditions"): data["existing_conditions"] = profile.existing_conditions

    # Run AI evaluation
    result = evaluate_risk(data)

    # Save assessment to database
    assessment = RiskAssessment(
        user_id=current_user.id if current_user else 1,
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        contributing_factors=json.dumps(result["contributing_factors"]),
        recommendations=json.dumps(result["recommendations"]),
        timestamp=datetime.datetime.utcnow()
    )
    db.add(assessment)

    # If vitals were passed, log them as a new vital record
    if req.heart_rate or req.spo2:
        vital = VitalRecord(
            user_id=current_user.id if current_user else 1,
            heart_rate=req.heart_rate or 72.0,
            spo2=req.spo2 or 98.0,
            systolic_bp=req.systolic_bp or 120.0,
            diastolic_bp=req.diastolic_bp or 80.0,
            temperature=req.temperature or 98.6,
            source="assessment",
            timestamp=datetime.datetime.utcnow()
        )
        db.add(vital)

    # If high risk or critical factors detected, create an early warning alert
    if result["risk_level"] == "High Risk":
        alert = Alert(
            user_id=current_user.id if current_user else 1,
            alert_type="High Risk Assessment Alert",
            severity="critical",
            detected_parameter=f"Risk Score: {result['risk_score']}/100",
            message="AI Health Risk Assessment flagged elevated risk parameters requiring clinical attention.",
            status="active",
            timestamp=datetime.datetime.utcnow()
        )
        db.add(alert)

    db.commit()
    db.refresh(assessment)

    return RiskAssessmentResponse(
        id=assessment.id,
        risk_level=result["risk_level"],
        risk_score=result["risk_score"],
        class_probabilities=result.get("class_probabilities"),
        contributing_factors=result["contributing_factors"],
        recommendations=result["recommendations"],
        seek_medical_attention=result["seek_medical_attention"],
        disclaimer=result["disclaimer"],
        timestamp=assessment.timestamp
    )

@router.get("/history")
def get_risk_history(
    limit: int = 10,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        current_user = db.query(User).filter(User.role == "patient").first()

    records = db.query(RiskAssessment)\
        .filter(RiskAssessment.user_id == current_user.id)\
        .order_by(RiskAssessment.timestamp.desc())\
        .limit(limit)\
        .all()

    history = []
    for r in records:
        history.append({
            "id": r.id,
            "risk_score": r.risk_score,
            "risk_level": r.risk_level,
            "contributing_factors": json.loads(r.contributing_factors),
            "recommendations": json.loads(r.recommendations),
            "timestamp": r.timestamp.isoformat()
        })
    return history
