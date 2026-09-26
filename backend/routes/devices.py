import datetime
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Device, VitalRecord
from backend.schemas import DeviceCreate, DeviceResponse
from backend.utils.security import get_current_user
from backend.websockets.vitals_hub import hub

router = APIRouter(prefix="/api/devices", tags=["IoT Devices"])

class TelemetryPayload(BaseModel):
    device_id: Optional[str] = "esp32_max30102"
    heart_rate: float
    spo2: float
    temperature: float
    systolic_bp: Optional[float] = 120.0
    diastolic_bp: Optional[float] = 80.0
    battery: Optional[int] = 95

@router.get("", response_model=List[DeviceResponse])
def get_devices(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        current_user = db.query(User).filter(User.role == "patient").first()
    return db.query(Device).filter(Device.user_id == current_user.id).all()

@router.post("/connect", response_model=DeviceResponse)
def connect_device(
    device_in: DeviceCreate,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        current_user = db.query(User).filter(User.role == "patient").first()

    device = Device(
        user_id=current_user.id,
        device_name=device_in.device_name,
        device_type=device_in.device_type or "Smart Health Band",
        connection_status="connected",
        last_seen=datetime.datetime.utcnow()
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device

@router.post("/telemetry")
def ingest_iot_telemetry(payload: TelemetryPayload, db: Session = Depends(get_db)):
    """
    Ingestion endpoint for ESP32 / Arduino / Smartwatch hardware over HTTP POST.
    Updates the live WebSocket broadcast hub and records the reading into database.
    """
    # Find active patient user
    user = db.query(User).filter(User.role == "patient").first()
    user_id = user.id if user else 1

    vital = VitalRecord(
        user_id=user_id,
        heart_rate=payload.heart_rate,
        spo2=payload.spo2,
        systolic_bp=payload.systolic_bp or 120.0,
        diastolic_bp=payload.diastolic_bp or 80.0,
        temperature=payload.temperature,
        source="iot_esp32",
        timestamp=datetime.datetime.utcnow()
    )
    db.add(vital)
    db.commit()

    # Update current vitals in hub
    hub.current_vitals.update({
        "heart_rate": payload.heart_rate,
        "spo2": payload.spo2,
        "temperature": payload.temperature,
        "systolic_bp": payload.systolic_bp or 120.0,
        "diastolic_bp": payload.diastolic_bp or 80.0,
        "sensor_status": "streaming",
        "device_name": payload.device_id or "ESP32 MAX30102 Gateway",
        "battery": payload.battery or 95,
        "timestamp": datetime.datetime.utcnow().isoformat()
    })

    return {"status": "telemetry_ingested", "heart_rate": payload.heart_rate, "spo2": payload.spo2}
