from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

# --- Auth Schemas ---
class UserCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    password: str
    role: Optional[str] = "patient"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str
    remember_me: Optional[bool] = False

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    role: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- Health Profile ---
class HealthProfileUpdate(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    existing_conditions: Optional[str] = None
    sleep_hours: Optional[float] = None
    physical_activity: Optional[int] = None
    smoking: Optional[int] = None
    alcohol: Optional[int] = None

class HealthProfileResponse(BaseModel):
    id: int
    user_id: int
    age: int
    gender: str
    height: float
    weight: float
    emergency_contact_name: str
    emergency_contact_phone: str
    emergency_contact_relationship: str
    existing_conditions: str
    sleep_hours: float
    physical_activity: int
    smoking: int
    alcohol: int

    class Config:
        from_attributes = True

# --- Vitals Schemas ---
class VitalCreate(BaseModel):
    heart_rate: float
    spo2: float
    systolic_bp: float
    diastolic_bp: float
    temperature: float
    source: Optional[str] = "manual"

class VitalResponse(BaseModel):
    id: int
    user_id: int
    heart_rate: float
    spo2: float
    systolic_bp: float
    diastolic_bp: float
    temperature: float
    source: str
    timestamp: datetime

    class Config:
        from_attributes = True

# --- Risk Assessment ---
class RiskPredictRequest(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    bmi: Optional[float] = None
    heart_rate: Optional[float] = None
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    spo2: Optional[float] = None
    temperature: Optional[float] = None
    symptoms: Optional[List[str]] = []
    existing_conditions: Optional[str] = None
    sleep_hours: Optional[float] = None
    physical_activity: Optional[int] = None
    smoking: Optional[int] = None
    alcohol: Optional[int] = None

class ContributingFactor(BaseModel):
    factor: str
    value: str
    impact: str
    description: str

class RiskAssessmentResponse(BaseModel):
    id: Optional[int] = None
    risk_level: str
    risk_score: float
    class_probabilities: Optional[dict] = None
    contributing_factors: List[ContributingFactor]
    recommendations: List[str]
    seek_medical_attention: bool
    disclaimer: str
    timestamp: Optional[datetime] = None

# --- Symptoms ---
class SymptomCreate(BaseModel):
    symptoms: List[str]
    severity: Optional[str] = "mild"
    duration_days: Optional[int] = 1
    notes: Optional[str] = None

class SymptomResponse(BaseModel):
    id: int
    user_id: int
    symptoms: str
    severity: str
    duration_days: int
    notes: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True

# --- Alerts ---
class AlertResponse(BaseModel):
    id: int
    user_id: int
    alert_type: str
    severity: str
    message: str
    detected_parameter: Optional[str]
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True

# --- Devices ---
class DeviceCreate(BaseModel):
    device_name: str
    device_type: Optional[str] = "Smart Health Band"

class DeviceResponse(BaseModel):
    id: int
    user_id: int
    device_name: str
    device_type: str
    connection_status: str
    last_seen: datetime

    class Config:
        from_attributes = True

# --- Doctor Notes ---
class DoctorNoteCreate(BaseModel):
    patient_id: int
    notes: str
    follow_up_status: Optional[str] = "Under Review"

class DoctorNoteResponse(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    notes: str
    follow_up_status: str
    timestamp: datetime

    class Config:
        from_attributes = True
