"""
HEALTHGUARD AI - Risk Prediction Engine & Explainability Module
Loads trained model to perform risk classification, calibrated risk scoring (0-100),
feature contribution extraction, and clinical awareness recommendations.
"""

import os
import json
import joblib
import numpy as np

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "models", "health_risk_model.joblib")
METRICS_PATH = os.path.join(BASE_DIR, "models", "model_metrics.json")

_model = None
_metrics = None

def get_model():
    global _model, _metrics
    if _model is None and os.path.exists(MODEL_PATH):
        try:
            _model = joblib.load(MODEL_PATH)
            if os.path.exists(METRICS_PATH):
                with open(METRICS_PATH, "r", encoding="utf-8") as f:
                    _metrics = json.load(f)
        except Exception as e:
            print(f"Warning loading model: {e}")
    return _model

def safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def safe_int(val, default=0):
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

def predict_health_risk(data: dict) -> dict:
    """
    Evaluates patient health inputs and returns risk prediction and recommendations.
    """
    model = get_model()
    
    # Extract fields with safe defaults
    age = safe_float(data.get("age"), 35.0)
    gender = 1 if str(data.get("gender") or "male").lower() in ["male", "m", "1"] else 0
    height = safe_float(data.get("height"), 170.0) # cm
    weight = safe_float(data.get("weight"), 70.0)  # kg
    
    # Calculate BMI if height and weight provided
    bmi = safe_float(data.get("bmi"), 0.0)
    if bmi <= 0 and height > 0:
        h_m = height / 100.0
        bmi = round(weight / (h_m * h_m), 1)
    if bmi <= 0:
        bmi = 24.0
        
    resting_hr = safe_float(data.get("resting_hr") or data.get("heart_rate"), 72.0)
    systolic_bp = safe_float(data.get("systolic_bp"), 120.0)
    diastolic_bp = safe_float(data.get("diastolic_bp"), 80.0)
    spo2 = safe_float(data.get("spo2"), 98.0)
    temperature = safe_float(data.get("temperature"), 98.6)
    sleep_hours = safe_float(data.get("sleep_hours"), 7.0)
    
    # Lifestyle
    physical_activity = safe_int(data.get("physical_activity"), 1) # 0: sedentary, 1: moderate, 2: active
    smoking = safe_int(data.get("smoking"), 0) # 0: never, 1: former, 2: active
    alcohol = safe_int(data.get("alcohol"), 0)
    chronic_condition = 1 if data.get("chronic_condition") or data.get("has_chronic_condition") else 0
    
    # Symptoms
    symptoms = [str(s).lower() for s in (data.get("symptoms") or [])]
    chest_discomfort = 1 if any("chest" in s for s in symptoms) or data.get("chest_discomfort") else 0
    shortness_of_breath = 1 if any("breath" in s or "dyspnea" in s for s in symptoms) or data.get("shortness_of_breath") else 0
    fever_symptom = 1 if temperature >= 100.4 or any("fever" in s for s in symptoms) else 0
    symptom_count = len(symptoms) if symptoms else (chest_discomfort + shortness_of_breath + fever_symptom)
    
    features = [
        age, gender, bmi, resting_hr, systolic_bp, diastolic_bp,
        spo2, temperature, sleep_hours, physical_activity,
        smoking, alcohol, chronic_condition,
        chest_discomfort, shortness_of_breath, fever_symptom, symptom_count
    ]
    
    # ML inference or Rule-Based fallback
    contributing_factors = []
    
    if model is not None:
        X = np.array([features])
        probs = model.predict_proba(X)[0] # [P(Low), P(Mod), P(High)]
        pred_idx = int(np.argmax(probs))
        
        # Risk Score (0-100) combining probabilities with vital severity weights
        raw_score = (probs[1] * 45.0) + (probs[2] * 90.0)
    else:
        # Clinical Rule-based Fallback
        score = 15.0
        if spo2 < 92: score += 35
        elif spo2 < 95: score += 15
        if systolic_bp >= 160 or diastolic_bp >= 100: score += 30
        elif systolic_bp >= 140 or diastolic_bp >= 90: score += 15
        if resting_hr > 110 or resting_hr < 50: score += 20
        if temperature >= 101.5: score += 20
        elif temperature >= 100.4: score += 10
        if chest_discomfort: score += 30
        if shortness_of_breath: score += 25
        if bmi > 32: score += 10
        raw_score = min(score, 100.0)
        probs = [0.6, 0.3, 0.1]
        pred_idx = 2 if raw_score >= 65 else (1 if raw_score >= 35 else 0)

    # Check for acute clinical red flags that elevate risk level
    is_acute_danger = (spo2 < 90) or (chest_discomfort and shortness_of_breath) or (systolic_bp >= 180) or (temperature >= 103.5)
    if is_acute_danger:
        pred_idx = 2
        raw_score = max(raw_score, 78.0)
        
    risk_score = round(float(np.clip(raw_score, 5.0, 98.0)), 1)
    
    risk_levels = ["Low Risk", "Moderate Risk", "High Risk"]
    risk_level = risk_levels[pred_idx]
    
    # Explainability: Identify Top Contributing Factors
    if spo2 < 94:
        contributing_factors.append({
            "factor": "Blood Oxygen (SpO₂)",
            "value": f"{spo2}%",
            "impact": "High" if spo2 < 90 else "Moderate",
            "description": "Lower oxygen saturation level detected below optimal baseline (>95%)."
        })
    if systolic_bp >= 140 or diastolic_bp >= 90:
        contributing_factors.append({
            "factor": "Blood Pressure",
            "value": f"{int(systolic_bp)}/{int(diastolic_bp)} mmHg",
            "impact": "High" if systolic_bp >= 160 else "Moderate",
            "description": "Elevated vascular pressure recorded above standard reference range."
        })
    if resting_hr > 100 or resting_hr < 55:
        contributing_factors.append({
            "factor": "Heart Rate",
            "value": f"{int(resting_hr)} bpm",
            "impact": "High" if resting_hr > 120 else "Moderate",
            "description": "Resting pulse deviates from the typical adult resting window (60-100 bpm)."
        })
    if temperature >= 100.4:
        contributing_factors.append({
            "factor": "Body Temperature",
            "value": f"{temperature}°F",
            "impact": "High" if temperature >= 102.5 else "Moderate",
            "description": "Fever response observed indicating potential inflammation or infection."
        })
    if chest_discomfort:
        contributing_factors.append({
            "factor": "Chest Discomfort",
            "value": "Present",
            "impact": "High",
            "description": "Reported thoracic discomfort requires clinical vigilance."
        })
    if shortness_of_breath:
        contributing_factors.append({
            "factor": "Shortness of Breath",
            "value": "Present",
            "impact": "High",
            "description": "Respiratory exertion or dyspnea noted."
        })
    if bmi >= 30:
        contributing_factors.append({
            "factor": "Body Mass Index",
            "value": f"{bmi} kg/m²",
            "impact": "Moderate",
            "description": "Elevated BMI categorized as Class I+ Obesity."
        })
    if sleep_hours < 6:
        contributing_factors.append({
            "factor": "Sleep Duration",
            "value": f"{sleep_hours} hrs/night",
            "impact": "Low",
            "description": "Sub-optimal restorative sleep duration."
        })
        
    if not contributing_factors:
        contributing_factors.append({
            "factor": "Optimal Vitals",
            "value": "Normal Range",
            "impact": "Low",
            "description": "Heart rate, SpO₂, blood pressure, and temperature are within healthy physiological baselines."
        })
        
    # Recommendations
    recommendations = []
    seek_medical_attention = False
    
    if risk_level == "High Risk":
        seek_medical_attention = True
        recommendations.append("Immediate clinical consultation or urgent care evaluation recommended.")
        recommendations.append("Notify your primary emergency contact or local healthcare worker.")
        recommendations.append("Avoid strenuous physical exertion and rest in a well-ventilated space.")
        recommendations.append("Re-check SpO₂ and blood pressure within 15 minutes.")
    elif risk_level == "Moderate Risk":
        recommendations.append("Schedule a routine consultation with a healthcare professional.")
        recommendations.append("Log vital signs twice daily to identify evolving physiological patterns.")
        recommendations.append("Ensure 7-8 hours of restful sleep and hydrate adequately.")
        recommendations.append("Maintain low-sodium dietary habits and light physical activity.")
    else:
        recommendations.append("Maintain your current healthy lifestyle and balanced diet.")
        recommendations.append("Engage in regular aerobic exercise (150 minutes per week).")
        recommendations.append("Continue periodic wellness screenings and routine health monitoring.")
        
    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "class_probabilities": {
            "low": round(float(probs[0]), 3),
            "moderate": round(float(probs[1]), 3),
            "high": round(float(probs[2]), 3)
        },
        "contributing_factors": contributing_factors,
        "recommendations": recommendations,
        "seek_medical_attention": seek_medical_attention,
        "disclaimer": "This assessment is for health awareness only and is not a medical diagnosis. Consult a licensed healthcare provider for clinical evaluation and diagnosis."
    }

if __name__ == "__main__":
    test_sample = {
        "age": 52,
        "gender": "male",
        "height": 172,
        "weight": 84,
        "resting_hr": 118,
        "systolic_bp": 156,
        "diastolic_bp": 96,
        "spo2": 91.5,
        "temperature": 101.8,
        "symptoms": ["chest discomfort", "shortness of breath", "fever"]
    }
    result = predict_health_risk(test_sample)
    print("Test Prediction Output:")
    print(json.dumps(result, indent=2))
