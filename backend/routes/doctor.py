import json
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, HealthProfile, VitalRecord, RiskAssessment, Alert, DoctorNote
from backend.schemas import DoctorNoteCreate, DoctorNoteResponse
from backend.utils.security import get_current_user

router = APIRouter(prefix="/api/doctor", tags=["Healthcare Worker Portal"])

@router.get("/patients")
def list_patients(
    risk_filter: Optional[str] = Query(None, description="All, High Risk, Moderate Risk, Low Risk"),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(User).filter(User.role == "patient")
    if search:
        query = query.filter(User.name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%"))
    
    patients = query.all()
    results = []
    
    for p in patients:
        profile = p.profile
        latest_vital = db.query(VitalRecord).filter(VitalRecord.user_id == p.id).order_by(VitalRecord.timestamp.desc()).first()
        latest_risk = db.query(RiskAssessment).filter(RiskAssessment.user_id == p.id).order_by(RiskAssessment.timestamp.desc()).first()
        active_alerts = db.query(Alert).filter(Alert.user_id == p.id, Alert.status == "active").count()
        latest_note = db.query(DoctorNote).filter(DoctorNote.patient_id == p.id).order_by(DoctorNote.timestamp.desc()).first()

        risk_level = latest_risk.risk_level if latest_risk else "Low Risk"
        risk_score = latest_risk.risk_score if latest_risk else 18.0

        if risk_filter and risk_filter.lower() != "all":
            if risk_filter.lower() not in risk_level.lower():
                continue

        results.append({
            "id": p.id,
            "name": p.name,
            "email": p.email,
            "phone": p.phone or (profile.emergency_contact_phone if profile else "N/A"),
            "age": profile.age if profile else 32,
            "gender": profile.gender if profile else "Male",
            "existing_conditions": profile.existing_conditions if profile else "None",
            "risk_level": risk_level,
            "risk_score": risk_score,
            "active_alerts_count": active_alerts,
            "latest_vitals": {
                "heart_rate": latest_vital.heart_rate if latest_vital else 72.0,
                "spo2": latest_vital.spo2 if latest_vital else 98.0,
                "systolic_bp": latest_vital.systolic_bp if latest_vital else 120.0,
                "diastolic_bp": latest_vital.diastolic_bp if latest_vital else 80.0,
                "temperature": latest_vital.temperature if latest_vital else 98.6,
                "timestamp": latest_vital.timestamp.strftime("%b %d, %H:%M") if latest_vital else "Recent"
            } if latest_vital else None,
            "follow_up_status": latest_note.follow_up_status if latest_note else "Under Review"
        })

    return results

@router.get("/patients/{patient_id}")
def get_patient_details(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(User).filter(User.id == patient_id, User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    profile = patient.profile
    vitals = db.query(VitalRecord).filter(VitalRecord.user_id == patient_id).order_by(VitalRecord.timestamp.desc()).limit(15).all()
    assessments = db.query(RiskAssessment).filter(RiskAssessment.user_id == patient_id).order_by(RiskAssessment.timestamp.desc()).limit(5).all()
    alerts = db.query(Alert).filter(Alert.user_id == patient_id).order_by(Alert.timestamp.desc()).limit(10).all()
    notes = db.query(DoctorNote).filter(DoctorNote.patient_id == patient_id).order_by(DoctorNote.timestamp.desc()).all()

    return {
        "patient": {
            "id": patient.id,
            "name": patient.name,
            "email": patient.email,
            "phone": patient.phone,
            "created_at": patient.created_at.isoformat()
        },
        "profile": {
            "age": profile.age if profile else 30,
            "gender": profile.gender if profile else "Male",
            "height": profile.height if profile else 170.0,
            "weight": profile.weight if profile else 70.0,
            "emergency_contact": f"{profile.emergency_contact_name} ({profile.emergency_contact_phone})" if profile else "N/A",
            "existing_conditions": profile.existing_conditions if profile else "None"
        },
        "vitals_history": [
            {
                "id": v.id,
                "heart_rate": v.heart_rate,
                "spo2": v.spo2,
                "systolic_bp": v.systolic_bp,
                "diastolic_bp": v.diastolic_bp,
                "temperature": v.temperature,
                "timestamp": v.timestamp.strftime("%Y-%m-%d %H:%M")
            } for v in vitals
        ],
        "assessments": [
            {
                "id": a.id,
                "risk_score": a.risk_score,
                "risk_level": a.risk_level,
                "contributing_factors": json.loads(a.contributing_factors),
                "recommendations": json.loads(a.recommendations),
                "timestamp": a.timestamp.strftime("%Y-%m-%d %H:%M")
            } for a in assessments
        ],
        "alerts": [
            {
                "id": al.id,
                "alert_type": al.alert_type,
                "severity": al.severity,
                "message": al.message,
                "status": al.status,
                "timestamp": al.timestamp.strftime("%Y-%m-%d %H:%M")
            } for al in alerts
        ],
        "notes": [
            {
                "id": n.id,
                "notes": n.notes,
                "follow_up_status": n.follow_up_status,
                "timestamp": n.timestamp.strftime("%Y-%m-%d %H:%M")
            } for n in notes
        ]
    }

@router.post("/notes", response_model=DoctorNoteResponse)
def add_doctor_note(
    note_in: DoctorNoteCreate,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doctor_id = current_user.id if current_user and current_user.role == "doctor" else 2
    note = DoctorNote(
        doctor_id=doctor_id,
        patient_id=note_in.patient_id,
        notes=note_in.notes,
        follow_up_status=note_in.follow_up_status or "Under Review",
        timestamp=datetime.datetime.utcnow()
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note
