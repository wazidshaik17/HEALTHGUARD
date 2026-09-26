import asyncio
import json
import random
import datetime
from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect

class VitalsHub:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.is_broadcasting = False
        self.broadcast_task: asyncio.Task = None
        self.anomaly_mode = None  # None, 'tachycardia', 'hypoxemia', 'fever', 'hypertension'
        
        # Current physiological baseline
        self.current_vitals = {
            "heart_rate": 74.0,
            "spo2": 98.2,
            "systolic_bp": 120.0,
            "diastolic_bp": 80.0,
            "temperature": 98.6,
            "sensor_status": "streaming",
            "device_name": "HealthGuard PulseBand Pro",
            "battery": 94,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send initial snapshot immediately
        await websocket.send_json({
            "type": "vitals_snapshot",
            "data": self.current_vitals,
            "active_alert": None
        })

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for dead in disconnected:
            self.disconnect(dead)

    def set_anomaly(self, anomaly_type: str):
        self.anomaly_mode = anomaly_type

    def clear_anomaly(self):
        self.anomaly_mode = None

    def generate_next_tick(self) -> Dict[str, Any]:
        """Generates physiological readings with natural autonomic fluctuations or anomalies."""
        mode = self.anomaly_mode

        if mode == "tachycardia":
            hr = random.uniform(128.0, 144.0)
            spo2 = random.uniform(93.0, 96.0)
            sys_bp = random.uniform(135.0, 150.0)
            dia_bp = random.uniform(88.0, 95.0)
            temp = random.uniform(98.6, 99.4)
            alert = {
                "alert_type": "Tachycardia Detected",
                "severity": "critical",
                "detected_parameter": f"Heart Rate: {int(hr)} bpm",
                "message": f"Sustained elevated resting heart rate ({int(hr)} bpm) exceeded safety threshold (100 bpm).",
                "recommended_action": "Rest immediately, hydrate, avoid stimulants. Alert emergency contact if palpitations persist.",
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        elif mode == "hypoxemia":
            hr = random.uniform(88.0, 106.0)
            spo2 = random.uniform(87.5, 91.0)
            sys_bp = random.uniform(122.0, 134.0)
            dia_bp = random.uniform(80.0, 88.0)
            temp = random.uniform(98.4, 99.0)
            alert = {
                "alert_type": "Hypoxemia / Low SpO₂",
                "severity": "critical",
                "detected_parameter": f"SpO₂: {round(spo2, 1)}%",
                "message": f"Peripheral oxygen saturation ({round(spo2, 1)}%) dropped below the critical threshold of 92%.",
                "recommended_action": "Sit upright, check sensor placement, deep breathing. Immediate medical attention recommended if respiratory difficulty occurs.",
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        elif mode == "fever":
            hr = random.uniform(92.0, 108.0)
            spo2 = random.uniform(96.0, 98.0)
            sys_bp = random.uniform(118.0, 128.0)
            dia_bp = random.uniform(76.0, 84.0)
            temp = random.uniform(102.2, 103.8)
            alert = {
                "alert_type": "High Pyrexia / Severe Fever",
                "severity": "warning",
                "detected_parameter": f"Temperature: {round(temp, 1)}°F",
                "message": f"High fever detected ({round(temp, 1)}°F) exceeding standard febrile limits.",
                "recommended_action": "Hydrate with electrolyte fluids, apply cool compress, contact physician if fever persists > 24 hours.",
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        elif mode == "hypertension":
            hr = random.uniform(82.0, 96.0)
            spo2 = random.uniform(96.0, 98.5)
            sys_bp = random.uniform(164.0, 178.0)
            dia_bp = random.uniform(102.0, 112.0)
            temp = random.uniform(98.4, 98.8)
            alert = {
                "alert_type": "Hypertension Crisis Alert",
                "severity": "critical",
                "detected_parameter": f"BP: {int(sys_bp)}/{int(dia_bp)} mmHg",
                "message": f"Significantly elevated vascular pressure ({int(sys_bp)}/{int(dia_bp)} mmHg) detected.",
                "recommended_action": "Rest quietly for 5 minutes and repeat measurement. Seek emergency evaluation if headache or chest pain occurs.",
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        else:
            # Normal baseline with physiological respiratory sinus arrhythmia
            hr = self.current_vitals["heart_rate"] + random.uniform(-1.5, 1.5)
            hr = max(64.0, min(84.0, hr))
            spo2 = self.current_vitals["spo2"] + random.uniform(-0.2, 0.2)
            spo2 = max(97.0, min(99.8, spo2))
            sys_bp = self.current_vitals["systolic_bp"] + random.uniform(-1.2, 1.2)
            sys_bp = max(114.0, min(126.0, sys_bp))
            dia_bp = self.current_vitals["diastolic_bp"] + random.uniform(-0.8, 0.8)
            dia_bp = max(74.0, min(82.0, dia_bp))
            temp = self.current_vitals["temperature"] + random.uniform(-0.1, 0.1)
            temp = max(98.2, min(99.0, temp))
            alert = None

        self.current_vitals = {
            "heart_rate": round(hr, 1),
            "spo2": round(spo2, 1),
            "systolic_bp": round(sys_bp, 1),
            "diastolic_bp": round(dia_bp, 1),
            "temperature": round(temp, 1),
            "sensor_status": "streaming",
            "device_name": "HealthGuard PulseBand Pro",
            "battery": 94,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

        return {
            "type": "vitals_update",
            "data": self.current_vitals,
            "alert": alert
        }

    async def start_broadcasting(self):
        if self.is_broadcasting:
            return
        self.is_broadcasting = True
        while self.is_broadcasting:
            if self.active_connections:
                payload = self.generate_next_tick()
                await self.broadcast(payload)
            await asyncio.sleep(1.5)

    def stop_broadcasting(self):
        self.is_broadcasting = False

hub = VitalsHub()
