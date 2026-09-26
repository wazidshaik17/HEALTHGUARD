# HEALTHGUARD AI – AI-Based Community Health Risk Prediction & Early Warning System

> **Student Innovation Project – Healthcare Technology**  
> *Smarter Health. Earlier Awareness. Better Decisions.*

---

## 🌟 Executive Summary
**HEALTHGUARD AI** is an AI-powered community healthcare platform built to address the escalating need for accessible, intelligent, preventive, and technology-driven healthcare solutions. It enables citizens and healthcare workers to continuously monitor vital parameters, receive machine-learning risk predictions, track longitudinal physiological trends, and obtain automated early-warning alerts.

> [!IMPORTANT]
> **Clinical Notice & Medical Disclaimer:**  
> HEALTHGUARD AI is strictly an **early-risk awareness and health-support system, NOT a replacement for doctors or professional medical diagnosis.** The AI models predict probability-based community risk categories without claiming definitive disease diagnoses.

---

## 🚀 Key Features

### 1. 🔐 User Authentication & Role-Based Access Control
- **Authentication**: Email or mobile login, salted SHA-256 key derivation (PBKDF2, 100,000 iterations), and JWT bearer tokens.
- **Roles & Tailored Portals**:
  - **Patient / Citizen**: Overview cards, AI risk assessment, IoT stream, symptom checker, emergency contact management.
  - **Doctor / Healthcare Worker**: Community patient roster, triage priority badges, vital trajectory inspection, and clinical follow-up notes.
  - **Administrator**: Infrastructure health, AI model inference latency, IoT device fleet status, and community risk distribution analytics.
- **1-Click Hackathon Evaluator Login**: Instant role switching for evaluation without manual signup.

### 2. 🤖 AI Health Risk Assessment & Explainability
- **Machine Learning Engine**: Trained `RandomForestClassifier` (85.2% accuracy, 0.85 F1-score) and baseline `LogisticRegression` on 12,000 clinically grounded community health records.
- **Inputs**: Age, gender, BMI, resting pulse, blood pressure (systolic/diastolic), SpO₂ saturation, body temperature, lifestyle factors (sleep, physical activity, smoking, alcohol), and acute symptoms.
- **Outputs**:
  - **Risk Category**: Low Risk (&lt;35), Moderate Risk (35–64), High Risk (≥65).
  - **Risk Score**: 0 to 100 composite index.
  - **Explainability**: Top contributing physiological factors with relative risk weights.
  - **Tailored Recommendations**: Non-diagnostic preventive guidance and clinical consultation referrals.

### 3. 📡 Real-Time IoT Biometric Monitoring
- **Hardware Ready**: ESP32 DevKit firmware (`iot/esp32/healthguard_esp32.ino`) with MAX30102 pulse oximeter and DHT22 temperature sensor.
- **Streaming Gateway**: Bi-directional WebSockets (`/ws/vitals`) and REST telemetry endpoint (`POST /api/devices/telemetry`).
- **Demo Mode**: Built-in physiological simulator with natural sinus arrhythmia and zero-hardware offline capability.
- **Live Waveform Chart**: Real-time sliding 25-second telemetry window.

### 4. 🚨 AI Early Warning System & Emergency SOS
- **Configurable Clinical Triggers**:
  - Tachycardia (&gt;100 bpm) / Bradycardia (&lt;55 bpm)
  - Hypoxemia (SpO₂ &lt;92%)
  - High Pyrexia / Severe Fever (&gt;100.4°F)
  - Stage 2 Hypertension (&gt;140/90 mmHg)
- **Multi-Channel Alert Dispatch**: In-app notification banners, alert tray, and one-click emergency SMS/WhatsApp dispatch simulation to primary contacts.
- **National Emergency Dialers**: 108 (Ambulance), 112 (National Emergency), 104 (Health Helpline).

### 5. 📈 Health Trend Analytics
- Longitudinal historical charts covering **24 Hours**, **7 Days**, **30 Days**, and **6 Months**.
- Tracks pulse rate, blood oxygen, blood pressure bands, and AI risk score trajectories with plain-language medical summaries.

### 6. 🩺 Interactive Symptom Checker
- Multi-symptom selector with dynamic clinical follow-up questions (duration, severity, acute onset).
- Automated triage: Supportive Home Care, Routine Outpatient Visit, or Urgent Medical Care.

### 7. 🇮🇳 11 Indian Languages Supported
Full localization breaking language barriers for rural and urban community health:
1. **English**
2. **Hindi (हिंदी)**
3. **Telugu (తెలుగు)**
4. **Tamil (தமிழ்)**
5. **Kannada (ಕನ್ನಡ)**
6. **Malayalam (മലയാളം)**
7. **Marathi (मराठी)**
8. **Bengali (বাংলা)**
9. **Gujarati (ગુજરાતી)**
10. **Punjabi (ਪੰਜਾਬੀ)**
11. **Odia (ଓଡ଼ିଆ)**

### 8. 🌗 Modern UI/UX & 3-Way Theme Engine
- Light Mode (clinical white medical interface)
- Dark Mode (high-contrast night monitoring)
- System Default (syncs with OS preferences)
- Anti-FOUC inline scripts to eliminate theme flicker.

---

## 🛠️ Architecture & Technology Stack

```
HEALTHGUARD AI
│
├── frontend/                     # React 18 + Vite + Tailwind CSS + Recharts + Lucide Icons
│   ├── src/
│   │   ├── components/           # Header, Sidebar, DemoToolbar, HealthCard, EmergencyModal
│   │   ├── context/              # AuthContext, ThemeContext, VitalsStreamContext
│   │   ├── i18n/                 # 11 Indian language dictionaries
│   │   └── pages/                # 11 production-style responsive pages
│
├── backend/                      # Python FastAPI + SQLAlchemy + WebSockets
│   ├── main.py                   # App entrypoint, CORS, routers & WebSocket endpoint
│   ├── database.py               # SQLite database engine (PostgreSQL compatible)
│   ├── models.py                 # SQLAlchemy relational data models
│   ├── schemas.py                # Pydantic v2 validation schemas
│   ├── seed.py                   # Pre-populates realistic community demo records
│   ├── routes/                   # Auth, Health, Risk, Symptoms, Alerts, Devices, Doctor, Admin
│   └── websockets/               # VitalsHub real-time telemetry connection manager
│
├── ml/                           # Scikit-learn Machine Learning Pipeline
│   ├── dataset/generate_dataset.py # 12,000 community health records generator
│   ├── train.py                  # Random Forest & Logistic Regression trainer
│   ├── predict.py                # Standalone inference & explainability engine
│   └── models/                   # Serialized .joblib model artifacts & metrics
│
└── iot/                          # Embedded Hardware & Sensor Gateway
    ├── esp32/healthguard_esp32.ino # Arduino C++ sketch for ESP32 + MAX30102 + DHT22
    ├── esp32/wokwi_diagram.json  # Wokwi web simulator schematic
    └── README.md                 # Hardware wiring, pinout table, and HTTP/WS protocol
```

---

## ⚡ Quick Start & Run Instructions

### 1. Backend Server Setup
From the project root:

```bash
# Using uv (Python 3.12)
uv pip install -r backend/requirements.txt

# Run dataset generation and ML model training (if not already trained)
python ml/dataset/generate_dataset.py
python ml/train.py

# Launch FastAPI backend with WebSockets on port 8000
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

*Interactive API Swagger Documentation:* `http://127.0.0.1:8000/docs`

### 2. Frontend Application Setup
In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

*Frontend Web Application:* `http://localhost:5173`

---

## 🧑‍⚖️ Hackathon Evaluator 60-Second Walkthrough

1. Open `http://localhost:5173`.
2. Notice the **Hackathon Evaluator Toolbar** in the bottom right corner.
3. Click **"Launch 60-Second Guided Tour"** to step through:
   - **Landing Page**: View the 8-step interactive architecture workflow diagram.
   - **Citizen Dashboard**: Inspect calm clinical status cards (Heart Rate, SpO₂, Blood Pressure, Temp, BMI).
   - **AI Risk Assessment**: Click *"Autofill with Live IoT Vitals"* and submit to view Scikit-learn risk stratification, contributing factors, and recommendations.
   - **Live IoT Monitoring**: Watch the continuous real-time ECG/SpO₂ waveform chart.
   - **Trigger Anomaly**: Click *"Tachycardia (138 bpm)"* or *"Low SpO₂ (89%)"* in the Demo Toolbar. Watch the early warning banner fire and open the automated Emergency SOS dispatch modal!
   - **Doctor Portal**: Switch to Doctor role to review the patient roster and record clinical follow-up notes.
   - **Admin Console**: Inspect system telemetry, AI model response latency, and community risk distribution.
   - **Language & Theme**: Toggle through Indian languages (e.g. Hindi, Telugu, Tamil) and switch Light / Dark / System themes.

---

## 📜 License & Acknowledgements
Developed as a Student Innovation Project in Healthcare Technology. Designed with clinical responsibility, patient data safety, and accessible community health empowerment in mind.
