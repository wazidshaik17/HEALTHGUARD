"""
HEALTHGUARD AI - Machine Learning Model Training Pipeline
Trains Random Forest and Logistic Regression models on community health data.
Exports model artifacts, feature importances, and evaluation metrics.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report, confusion_matrix

FEATURE_COLUMNS = [
    "age",
    "gender",
    "bmi",
    "resting_hr",
    "systolic_bp",
    "diastolic_bp",
    "spo2",
    "temperature",
    "sleep_hours",
    "physical_activity",
    "smoking",
    "alcohol",
    "chronic_condition",
    "chest_discomfort",
    "shortness_of_breath",
    "fever_symptom",
    "symptom_count"
]

TARGET_COLUMN = "risk_level"

def train_health_models():
    base_dir = os.path.dirname(__file__)
    data_path = os.path.join(base_dir, "dataset", "community_health_data.csv")
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}. Run generate_dataset.py first.")
        
    df = pd.read_csv(data_path)
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 1. Random Forest Classifier
    rf_model = RandomForestClassifier(
        n_estimators=120,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42
    )
    rf_model.fit(X_train, y_train)
    
    rf_preds = rf_model.predict(X_test)
    rf_probs = rf_model.predict_proba(X_test)
    
    # 2. Logistic Regression Baseline
    lr_model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    lr_model.fit(X_train_scaled, y_train)
    lr_preds = lr_model.predict(X_test_scaled)
    
    # Metrics
    rf_acc = accuracy_score(y_test, rf_preds)
    rf_prec, rf_rec, rf_f1, _ = precision_recall_fscore_support(y_test, rf_preds, average="weighted")
    
    lr_acc = accuracy_score(y_test, lr_preds)
    lr_prec, lr_rec, lr_f1, _ = precision_recall_fscore_support(y_test, lr_preds, average="weighted")
    
    # Feature Importances
    importances = dict(zip(FEATURE_COLUMNS, [round(float(val), 4) for val in rf_model.feature_importances_]))
    sorted_importances = dict(sorted(importances.items(), key=lambda item: item[1], reverse=True))
    
    metrics = {
        "model_name": "Random Forest Health Risk Classifier",
        "n_samples": len(df),
        "n_features": len(FEATURE_COLUMNS),
        "features": FEATURE_COLUMNS,
        "rf_metrics": {
            "accuracy": round(float(rf_acc), 4),
            "precision": round(float(rf_prec), 4),
            "recall": round(float(rf_rec), 4),
            "f1_score": round(float(rf_f1), 4)
        },
        "lr_baseline_metrics": {
            "accuracy": round(float(lr_acc), 4),
            "precision": round(float(lr_prec), 4),
            "recall": round(float(lr_rec), 4),
            "f1_score": round(float(lr_f1), 4)
        },
        "feature_importances": sorted_importances,
        "risk_levels": {
            "0": "Low Risk",
            "1": "Moderate Risk",
            "2": "High Risk"
        }
    }
    
    # Save artifacts
    model_file = os.path.join(models_dir, "health_risk_model.joblib")
    scaler_file = os.path.join(models_dir, "scaler.joblib")
    metrics_file = os.path.join(models_dir, "model_metrics.json")
    
    joblib.dump(rf_model, model_file)
    joblib.dump(scaler, scaler_file)
    
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
        
    print("Training Completed Successfully!")
    print(f"Random Forest Accuracy: {rf_acc:.4f} | F1: {rf_f1:.4f}")
    print(f"Logistic Regression Accuracy: {lr_acc:.4f} | F1: {lr_f1:.4f}")
    print(f"Saved model to {model_file}")
    print("Top Contributing Features:")
    for feat, imp in list(sorted_importances.items())[:6]:
        print(f"  - {feat}: {imp*100:.1f}%")

if __name__ == "__main__":
    train_health_models()
