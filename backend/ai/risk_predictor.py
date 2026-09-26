import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from ml.predict import predict_health_risk, get_model
except ImportError:
    # Direct fallback if running in standalone backend folder
    from ml.predict import predict_health_risk, get_model

def evaluate_risk(data: dict) -> dict:
    return predict_health_risk(data)
