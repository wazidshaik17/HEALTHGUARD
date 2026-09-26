import os
import sys
import json
import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.database import SessionLocal, Base, engine
from backend.models import User, HealthProfile, VitalRecord, RiskAssessment, Alert, Device, DoctorNote
from backend.utils.security import hash_password

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).count() > 0:
            print("Database already contains records. Skipping seed.")
            return

        print("Seeding HEALTHGUARD AI database with realistic community healthcare data...")

        # 1. Main Patient: Rahul Sharma
        p1 = User(
            name="Rahul Sharma",
            email="rahul@healthguard.ai",
            phone="+91 98765 43210",
            password_hash=hash_password("password123"),
            role="patient"
        )
        db.add(p1)
        db.commit()
        db.refresh(p1)

        p1_profile = HealthProfile(
            user_id=p1.id,
            age=34,
            gender="Male",
            height=174.0,
            weight=71.5,
            emergency_contact_name="Anita Sharma",
            emergency_contact_phone="+91 98765 88990",
            emergency_contact_relationship="Spouse",
            existing_conditions="None reported",
            sleep_hours=7.5,
            physical_activity=1,
            smoking=0,
            alcohol=0
        )
        db.add(p1_profile)

        # 2. Doctor: Dr. Ananya Sen, MD
        doc = User(
            name="Dr. Ananya Sen, MD",
            email="dr.ananya@healthguard.ai",
            phone="+91 98111 22334",
            password_hash=hash_password("password123"),
            role="doctor"
        )
        db.add(doc)

        # 3. Admin: HealthGuard Administrator
        adm = User(
            name="Administrator",
            email="admin@healthguard.ai",
            phone="+91 98000 11223",
            password_hash=hash_password("password123"),
            role="admin"
        )
        db.add(adm)
        db.commit()

        # 4. Additional Patients for Doctor Roster
        p2 = User(
            name="Vikram Patel",
            email="vikram.patel@example.com",
            phone="+91 98220 33445",
            password_hash=hash_password("password123"),
            role="patient"
        )
        db.add(p2)
        db.commit()
        db.refresh(p2)
        db.add(HealthProfile(
            user_id=p2.id, age=58, gender="Male", height=168.0, weight=86.0,
            emergency_contact_name="Sanjay Patel", emergency_contact_phone="+91 98220 99887", emergency_contact_relationship="Son",
            existing_conditions="Hypertension Stage 1", physical_activity=0, smoking=1
        ))

        p3 = User(
            name="Priya Nair",
            email="priya.nair@example.com",
            phone="+91 98330 44556",
            password_hash=hash_password("password123"),
            role="patient"
        )
        db.add(p3)
        db.commit()
        db.refresh(p3)
        db.add(HealthProfile(
            user_id=p3.id, age=42, gender="Female", height=160.0, weight=64.0,
            emergency_contact_name="Ramesh Nair", emergency_contact_phone="+91 98330 11223", emergency_contact_relationship="Spouse",
            existing_conditions="Mild Asthma", physical_activity=1
        ))

        p4 = User(
            name="Meera Sundaram",
            email="meera.sundaram@example.com",
            phone="+91 98440 55667",
            password_hash=hash_password("password123"),
            role="patient"
        )
        db.add(p4)
        db.commit()
        db.refresh(p4)
        db.add(HealthProfile(
            user_id=p4.id, age=66, gender="Female", height=155.0, weight=69.0,
            emergency_contact_name="Karthik Sundaram", emergency_contact_phone="+91 98440 99001", emergency_contact_relationship="Son",
            existing_conditions="Type 2 Diabetes", physical_activity=0
        ))
        db.commit()

        # 5. Seed Historical Vitals for Rahul Sharma (last 7 days)
        now = datetime.datetime.utcnow()
        vitals_data = [
            (now - datetime.timedelta(days=6), 70, 98.6, 118, 76, 98.4),
            (now - datetime.timedelta(days=5), 72, 98.2, 120, 78, 98.5),
            (now - datetime.timedelta(days=4), 75, 97.9, 122, 80, 98.6),
            (now - datetime.timedelta(days=3), 71, 98.5, 119, 78, 98.4),
            (now - datetime.timedelta(days=2), 74, 98.1, 121, 79, 98.7),
            (now - datetime.timedelta(days=1), 73, 98.4, 120, 78, 98.6),
            (now - datetime.timedelta(hours=6), 72, 98.6, 118, 77, 98.5),
            (now, 74, 98.4, 120, 78, 98.6),
        ]
        for t, hr, o2, s_bp, d_bp, temp in vitals_data:
            db.add(VitalRecord(
                user_id=p1.id, heart_rate=hr, spo2=o2, systolic_bp=s_bp, diastolic_bp=d_bp,
                temperature=temp, source="iot", timestamp=t
            ))

        # Vitals for Vikram Patel (High Risk vitals)
        db.add(VitalRecord(user_id=p2.id, heart_rate=128, spo2=91.2, systolic_bp=158, diastolic_bp=98, temperature=99.2, source="iot", timestamp=now))
        # Vitals for Priya Nair (Moderate)
        db.add(VitalRecord(user_id=p3.id, heart_rate=88, spo2=96.5, systolic_bp=136, diastolic_bp=88, temperature=98.8, source="manual", timestamp=now))
        # Vitals for Meera Sundaram (Moderate with fever)
        db.add(VitalRecord(user_id=p4.id, heart_rate=94, spo2=95.8, systolic_bp=142, diastolic_bp=86, temperature=101.4, source="iot", timestamp=now))

        # 6. Seed Initial Assessments
        db.add(RiskAssessment(
            user_id=p1.id,
            risk_score=18.5,
            risk_level="Low Risk",
            contributing_factors=json.dumps([{
                "factor": "Optimal Vitals", "value": "Normal Range", "impact": "Low",
                "description": "Heart rate, SpO₂, blood pressure, and temperature are within healthy baseline."
            }]),
            recommendations=json.dumps([
                "Maintain your active lifestyle and balanced diet.",
                "Continue routine preventive monitoring twice weekly.",
                "Ensure consistent 7-8 hours of sleep."
            ]),
            timestamp=now - datetime.timedelta(days=1)
        ))

        db.add(RiskAssessment(
            user_id=p2.id,
            risk_score=82.0,
            risk_level="High Risk",
            contributing_factors=json.dumps([
                {"factor": "Blood Oxygen (SpO₂)", "value": "91.2%", "impact": "High", "description": "Hypoxemic threshold reached."},
                {"factor": "Heart Rate", "value": "128 bpm", "impact": "High", "description": "Tachycardia observed."},
                {"factor": "Blood Pressure", "value": "158/98 mmHg", "impact": "High", "description": "Stage 2 Hypertension."}
            ]),
            recommendations=json.dumps([
                "Urgent medical consultation strongly advised.",
                "Rest quietly and avoid physical activity.",
                "Emergency contact notified."
            ]),
            timestamp=now
        ))

        # 7. Seed Sample Alerts
        db.add(Alert(
            user_id=p2.id,
            alert_type="Tachycardia & Hypoxemia Critical Alert",
            severity="critical",
            detected_parameter="HR: 128 bpm | SpO₂: 91.2%",
            message="Simultaneous elevated pulse and low blood oxygen detected by IoT PulseBand.",
            status="active",
            timestamp=now - datetime.timedelta(minutes=15)
        ))

        db.add(Alert(
            user_id=p4.id,
            alert_type="Pyrexia Warning",
            severity="warning",
            detected_parameter="Temp: 101.4°F",
            message="Elevated body temperature recorded.",
            status="active",
            timestamp=now - datetime.timedelta(hours=2)
        ))

        # 8. Seed Connected Devices
        db.add(Device(user_id=p1.id, device_name="HealthGuard PulseBand Pro", device_type="Smart Health Band", connection_status="streaming", last_seen=now))
        db.add(Device(user_id=p1.id, device_name="ESP32 Health Gateway Node", device_type="IoT Microcontroller", connection_status="connected", last_seen=now))

        # 9. Seed Doctor Notes
        db.add(DoctorNote(
            doctor_id=doc.id,
            patient_id=p1.id,
            notes="Routine annual checkup completed. Cardiovascular vitals and SpO₂ are optimal. Recommended continuing regular exercise.",
            follow_up_status="Routine Follow-up",
            timestamp=now - datetime.timedelta(days=12)
        ))
        db.add(DoctorNote(
            doctor_id=doc.id,
            patient_id=p2.id,
            notes="Observed acute tachycardia and oxygen drop. Prescribed ambulatory Holter monitoring and scheduled in-clinic ECG.",
            follow_up_status="High Priority",
            timestamp=now - datetime.timedelta(hours=1)
        ))

        db.commit()
        print("Seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
