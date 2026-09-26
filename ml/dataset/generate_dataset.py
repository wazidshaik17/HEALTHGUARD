"""
HEALTHGUARD AI - Synthetic Community Health Dataset Generator
Generates clinically grounded physiological and lifestyle records for training
the Community Health Risk Prediction model.

Target categories:
  0: Low Risk (Routine health awareness & preventive lifestyle)
  1: Moderate Risk (Follow-up recommended, lifestyle adjustments)
  2: High Risk (Timely clinical consultation / immediate medical evaluation recommended)
"""

import os
import numpy as np
import pandas as pd

def generate_health_dataset(n_samples: int = 12000, random_seed: int = 42) -> pd.DataFrame:
    np.random.seed(random_seed)
    
    # Demographics
    age = np.random.randint(18, 85, size=n_samples)
    gender = np.random.choice([0, 1], size=n_samples, p=[0.51, 0.49]) # 0: Female, 1: Male
    
    # BMI: Normal (18.5-24.9), Overweight (25-29.9), Obese (30+)
    bmi = np.random.normal(loc=26.5, scale=5.2, size=n_samples)
    bmi = np.clip(bmi, 16.0, 45.0)
    
    # Resting Heart Rate (bpm): Normal 60-100, Bradycardia < 60, Tachycardia > 100
    resting_hr = np.random.normal(loc=74.0, scale=14.0, size=n_samples)
    resting_hr = np.clip(resting_hr, 45.0, 145.0)
    
    # Blood Pressure (Systolic / Diastolic mmHg)
    # Systolic correlates with age and BMI
    systolic_bp = 100 + (age * 0.35) + ((bmi - 22) * 0.9) + np.random.normal(0, 12, size=n_samples)
    systolic_bp = np.clip(systolic_bp, 85.0, 205.0)
    
    diastolic_bp = 65 + (systolic_bp * 0.25) + np.random.normal(0, 7, size=n_samples)
    diastolic_bp = np.clip(diastolic_bp, 50.0, 125.0)
    
    # SpO2 (%): Normal 95-100%, Hypoxemia < 92%
    # Majority healthy with a long tail of acute/chronic respiratory dips
    spo2_base = np.random.beta(a=35, b=1.5, size=n_samples) * 100
    spo2 = np.clip(spo2_base, 82.0, 100.0)
    
    # Body Temperature (Fahrenheit): Normal 97.0-99.0 F, Fever > 100.4 F
    temp_base = np.random.normal(loc=98.4, scale=0.75, size=n_samples)
    # Ingest 12% probability of fever spike
    has_fever_spike = np.random.rand(n_samples) < 0.12
    temp_base[has_fever_spike] += np.random.uniform(1.8, 4.8, size=np.sum(has_fever_spike))
    temperature = np.clip(temp_base, 96.0, 104.5)
    
    # Lifestyle parameters
    sleep_hours = np.random.normal(loc=7.1, scale=1.4, size=n_samples)
    sleep_hours = np.clip(sleep_hours, 3.5, 11.0)
    
    # Physical Activity: 0: Sedentary, 1: Moderate, 2: Active
    physical_activity = np.random.choice([0, 1, 2], size=n_samples, p=[0.38, 0.44, 0.18])
    
    # Smoking: 0: Non-smoker, 1: Ex-smoker, 2: Active smoker
    smoking = np.random.choice([0, 1, 2], size=n_samples, p=[0.62, 0.18, 0.20])
    
    # Alcohol: 0: None, 1: Moderate/Occasional, 2: Heavy
    alcohol = np.random.choice([0, 1, 2], size=n_samples, p=[0.58, 0.32, 0.10])
    
    # Chronic conditions: 0: None, 1: Present (Hypertension/Diabetes/Asthma)
    chronic_prob = np.clip(0.10 + (age * 0.006) + ((bmi > 30) * 0.18), 0.05, 0.75)
    chronic_condition = (np.random.rand(n_samples) < chronic_prob).astype(int)
    
    # Acute Symptoms
    chest_discomfort = (np.random.rand(n_samples) < (0.04 + (age > 50) * 0.06 + (systolic_bp > 150) * 0.10)).astype(int)
    shortness_of_breath = (np.random.rand(n_samples) < (0.05 + (spo2 < 93) * 0.45 + (bmi > 32) * 0.08)).astype(int)
    fever_symptom = (temperature >= 100.4).astype(int)
    fatigue_or_dizziness = (np.random.rand(n_samples) < 0.22).astype(int)
    symptom_count = chest_discomfort + shortness_of_breath + fever_symptom + fatigue_or_dizziness
    
    # Clinically Grounded Composite Risk Score calculation (0 to 100)
    risk_score = np.zeros(n_samples)
    
    # Vitals deviation contributions
    # 1. SpO2 score
    risk_score += np.where(spo2 < 90, 35, np.where(spo2 < 94, 20, np.where(spo2 < 96, 8, 0)))
    
    # 2. Blood Pressure score
    risk_score += np.where(systolic_bp >= 160, 28, np.where(systolic_bp >= 140, 16, np.where(systolic_bp >= 130, 8, 0)))
    risk_score += np.where(diastolic_bp >= 100, 18, np.where(diastolic_bp >= 90, 10, 0))
    
    # 3. Heart Rate score
    risk_score += np.where((resting_hr > 120) | (resting_hr < 50), 22, np.where((resting_hr > 100) | (resting_hr < 55), 10, 0))
    
    # 4. Temperature score
    risk_score += np.where(temperature >= 102.5, 25, np.where(temperature >= 100.4, 14, 0))
    
    # 5. Critical Symptoms
    risk_score += chest_discomfort * 28
    risk_score += shortness_of_breath * 24
    risk_score += fatigue_or_dizziness * 6
    
    # 6. Demographics & Comorbidities
    risk_score += (age > 65) * 8
    risk_score += (bmi >= 32) * 10
    risk_score += chronic_condition * 12
    risk_score += (smoking == 2) * 8
    risk_score += (physical_activity == 0) * 5
    risk_score += (sleep_hours < 5.5) * 6
    
    # Add random physiological variation
    risk_score += np.random.normal(0, 4.0, size=n_samples)
    risk_score = np.clip(risk_score, 0, 100)
    
    # Assign Risk Categories
    # 0: Low (< 35)
    # 1: Moderate (35 <= score < 65)
    # 2: High (>= 65)
    risk_level = np.where(risk_score >= 65, 2, np.where(risk_score >= 35, 1, 0))
    
    df = pd.DataFrame({
        "age": age,
        "gender": gender,
        "bmi": np.round(bmi, 1),
        "resting_hr": np.round(resting_hr, 0).astype(int),
        "systolic_bp": np.round(systolic_bp, 0).astype(int),
        "diastolic_bp": np.round(diastolic_bp, 0).astype(int),
        "spo2": np.round(spo2, 1),
        "temperature": np.round(temperature, 1),
        "sleep_hours": np.round(sleep_hours, 1),
        "physical_activity": physical_activity,
        "smoking": smoking,
        "alcohol": alcohol,
        "chronic_condition": chronic_condition,
        "chest_discomfort": chest_discomfort,
        "shortness_of_breath": shortness_of_breath,
        "fever_symptom": fever_symptom,
        "symptom_count": symptom_count,
        "risk_score": np.round(risk_score, 1),
        "risk_level": risk_level
    })
    
    return df

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__))
    os.makedirs(out_dir, exist_ok=True)
    df = generate_health_dataset()
    csv_path = os.path.join(out_dir, "community_health_data.csv")
    df.to_csv(csv_path, index=False)
    print(f"Generated {len(df)} samples saved to {csv_path}")
    print("Class distribution:")
    print(df["risk_level"].value_counts(normalize=True))
