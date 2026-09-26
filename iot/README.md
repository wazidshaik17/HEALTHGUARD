# HEALTHGUARD AI - IoT Vitals Gateway Architecture

## 1. Overview
The **HEALTHGUARD AI IoT Gateway** interfaces physical patient monitoring sensors (MAX30102 pulse oximeter and DHT22/DS18B20 temperature probes) with the cloud/local intelligence layer. It samples photoplethysmography (PPG) waveforms, calculates continuous oxygen saturation (SpO₂) and heart rate (bpm), and streams structured JSON payloads to the FastAPI backend over HTTP POST or WebSockets.

---

## 2. Hardware Pinout & Wiring

| Sensor Pin | ESP32 DevKit Pin | Function / Protocol |
| :--- | :--- | :--- |
| **MAX30102 VIN** | 3V3 / 5V | Power Supply |
| **MAX30102 GND** | GND | Ground |
| **MAX30102 SDA** | GPIO 21 | I2C Serial Data |
| **MAX30102 SCL** | GPIO 22 | I2C Serial Clock |
| **DHT22 VCC** | 3V3 | Power Supply |
| **DHT22 GND** | GND | Ground |
| **DHT22 DATA** | GPIO 4 | Digital One-Wire Data (with 10k pull-up) |
| **Status Heartbeat LED** | GPIO 2 (Internal LED) | Activity & Transmission indicator |
| **Buzzer / Audio Alarm** | GPIO 18 | Local Audible Alert during Critical Anomaly |

---

## 3. Communication Protocol

### HTTP Endpoint
`POST http://<SERVER_HOST>:8000/api/devices/telemetry`

**Payload Schema:**
```json
{
  "device_id": "esp32_community_node_01",
  "heart_rate": 74.2,
  "spo2": 98.4,
  "temperature": 98.6,
  "systolic_bp": 120.0,
  "diastolic_bp": 80.0,
  "battery": 94
}
```

### WebSocket Stream
`ws://<SERVER_HOST>:8000/ws/vitals`

Bi-directional channel streaming live vital ticks every 1.5 seconds and receiving remote alert control signals.

---

## 4. Hardware-Free Demonstration Mode
If physical sensors or microcontrollers are not attached:
1. The firmware automatically detects the empty I2C bus and enables an internal high-fidelity physiological simulator.
2. The web frontend also features an autonomous **Client-Side Simulation Engine** with instant Anomaly Triggers (Tachycardia, Hypoxemia, Severe Fever) for exhibition judges and evaluators.
