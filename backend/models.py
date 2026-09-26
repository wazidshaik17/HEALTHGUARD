import datetime
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    phone = Column(String(30), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="patient", nullable=False)  # patient, doctor, admin
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    profile = relationship("HealthProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    vitals = relationship("VitalRecord", back_populates="user", cascade="all, delete-orphan")
    symptoms = relationship("SymptomRecord", back_populates="user", cascade="all, delete-orphan")
    assessments = relationship("RiskAssessment", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")

class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    age = Column(Integer, default=30)
    gender = Column(String(20), default="Male")
    height = Column(Float, default=172.0)  # cm
    weight = Column(Float, default=70.0)   # kg
    emergency_contact_name = Column(String(120), default="Primary Contact")
    emergency_contact_phone = Column(String(30), default="+91 98765 43210")
    emergency_contact_relationship = Column(String(50), default="Family Member")
    existing_conditions = Column(Text, default="None")
    sleep_hours = Column(Float, default=7.5)
    physical_activity = Column(Integer, default=1)  # 0: Sedentary, 1: Moderate, 2: Active
    smoking = Column(Integer, default=0)            # 0: Never, 1: Former, 2: Active
    alcohol = Column(Integer, default=0)            # 0: None, 1: Moderate, 2: Heavy

    user = relationship("User", back_populates="profile")

class VitalRecord(Base):
    __tablename__ = "vital_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    heart_rate = Column(Float, nullable=False)
    spo2 = Column(Float, nullable=False)
    systolic_bp = Column(Float, nullable=False)
    diastolic_bp = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)  # in Fahrenheit
    source = Column(String(30), default="manual")  # iot, manual, demo
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="vitals")

class SymptomRecord(Base):
    __tablename__ = "symptoms"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symptoms = Column(Text, nullable=False)  # JSON or comma-separated list
    severity = Column(String(20), default="mild")  # mild, moderate, severe
    duration_days = Column(Integer, default=1)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="symptoms")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    risk_score = Column(Float, nullable=False)      # 0 to 100
    risk_level = Column(String(30), nullable=False) # Low Risk, Moderate Risk, High Risk
    contributing_factors = Column(Text, nullable=False)  # JSON string
    recommendations = Column(Text, nullable=False)       # JSON string
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="assessments")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alert_type = Column(String(50), nullable=False) # e.g. Tachycardia, Hypoxemia, Hypertensive Crisis
    severity = Column(String(20), default="warning") # info, warning, critical
    message = Column(Text, nullable=False)
    detected_parameter = Column(String(80), nullable=True)
    status = Column(String(20), default="active")   # active, acknowledged
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="alerts")

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_name = Column(String(100), nullable=False)
    device_type = Column(String(50), default="Smart Health Band")  # Smartwatch, Pulse Oximeter, ESP32 Gateway
    connection_status = Column(String(30), default="connected")    # connected, streaming, disconnected
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="devices")

class DoctorNote(Base):
    __tablename__ = "doctor_notes"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(Text, nullable=False)
    follow_up_status = Column(String(40), default="Under Review") # Stable, Routine Follow-up, High Priority
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
