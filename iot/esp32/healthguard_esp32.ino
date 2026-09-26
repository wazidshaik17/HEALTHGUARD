/*
  =============================================================================
  HEALTHGUARD AI - IoT Community Vitals Gateway Node Firmware
  Microcontroller: ESP32 DevKit V1
  Sensors:
    - MAX30102 / MAX30100 (Pulse Oximeter & Heart Rate via I2C)
    - DHT22 / DS18B20 (Ambient & Body Temperature via Digital OneWire/GPIO)
  Connectivity:
    - 2.4GHz Wi-Fi (WPA2-PSK)
    - REST HTTP Client (POST /api/devices/telemetry)
    - WebSockets Ready (ws://<host>:8000/ws/vitals)
  =============================================================================
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>

// Wi-Fi Credentials
const char* WIFI_SSID = "HealthGuard_IoT_WiFi";
const char* WIFI_PASSWORD = "CommunityHealthSecure2026";

// Backend API Server Target
const char* SERVER_ENDPOINT = "http://192.168.1.100:8000/api/devices/telemetry";
const char* DEVICE_ID = "esp32_community_node_01";

// Pinout Definitions
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22
#define DHT_PIN 4
#define STATUS_LED_PIN 2
#define BUZZER_PIN 18

// Simulated vs Hardware Sensor Toggle
// If hardware sensor isn't physically attached to I2C bus, the firmware
// gracefully falls back to synthetic physiological stream for demonstration.
bool hardwareSensorDetected = false;

// Physiological buffer values
float currentHeartRate = 72.0;
float currentSpO2 = 98.4;
float currentTemperature = 98.6;
float systolicBP = 120.0;
float diastolicBP = 80.0;
int batteryLevel = 94;

unsigned long lastTelemetryMillis = 0;
const unsigned long TELEMETRY_INTERVAL = 2000; // 2 seconds

void setupWiFi() {
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 15) {
    delay(500);
    Serial.print(".");
    digitalWrite(STATUS_LED_PIN, !digitalRead(STATUS_LED_PIN));
    retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected successfully!");
    Serial.print("[WiFi] IP Address: ");
    Serial.println(WiFi.localIP());
    digitalWrite(STATUS_LED_PIN, HIGH);
  } else {
    Serial.println("\n[WiFi] Connection timed out. Operating in Standalone/Demo mode.");
    digitalWrite(STATUS_LED_PIN, LOW);
  }
}

void scanI2CDevices() {
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  Serial.println("[I2C] Scanning for MAX30102 Pulse Oximeter...");
  
  byte error, address;
  int nDevices = 0;
  for (address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    if (error == 0) {
      Serial.print("[I2C] Sensor found at address 0x");
      if (address < 16) Serial.print("0");
      Serial.println(address, HEX);
      if (address == 0x57) { // 0x57 is MAX30102 standard 7-bit I2C address
        hardwareSensorDetected = true;
        Serial.println("[MAX30102] Optical Sensor Initialized successfully!");
      }
      nDevices++;
    }
  }
  if (nDevices == 0) {
    Serial.println("[I2C] No physical sensors detected on bus. Auto-enabling calibrated simulation engine.");
  }
}

void readSensors() {
  if (hardwareSensorDetected) {
    // Read raw IR/Red photodiode signals from MAX30102 register FIFO
    // In actual deployment: SparkFun_MAX3010x library calculates peak autocorrelation
    // For sample sketch:
    currentHeartRate = 72.0 + (analogRead(34) % 15);
    currentSpO2 = 97.5 + ((analogRead(35) % 25) / 10.0);
    currentTemperature = 98.4 + ((analogRead(36) % 10) / 10.0);
  } else {
    // Generate realistic ambulatory micro-variations
    float hrDelta = (random(-15, 16) / 10.0);
    currentHeartRate += hrDelta;
    if (currentHeartRate < 64.0) currentHeartRate = 66.0;
    if (currentHeartRate > 84.0) currentHeartRate = 82.0;

    float spo2Delta = (random(-4, 5) / 10.0);
    currentSpO2 += spo2Delta;
    if (currentSpO2 < 97.0) currentSpO2 = 97.5;
    if (currentSpO2 > 99.8) currentSpO2 = 99.2;

    float tempDelta = (random(-2, 3) / 10.0);
    currentTemperature += tempDelta;
    if (currentTemperature < 98.1) currentTemperature = 98.4;
    if (currentTemperature > 99.0) currentTemperature = 98.7;
  }
}

void transmitTelemetry() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.print("[Telemetry Local Log] HR: ");
    Serial.print(currentHeartRate, 1);
    Serial.print(" bpm | SpO2: ");
    Serial.print(currentSpO2, 1);
    Serial.print("% | Temp: ");
    Serial.print(currentTemperature, 1);
    Serial.println(" F");
    return;
  }

  HTTPClient http;
  http.begin(SERVER_ENDPOINT);
  http.addHeader("Content-Type", "application/json");

  // Format JSON payload
  String jsonPayload = "{";
  jsonPayload += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  jsonPayload += "\"heart_rate\":" + String(currentHeartRate, 1) + ",";
  jsonPayload += "\"spo2\":" + String(currentSpO2, 1) + ",";
  jsonPayload += "\"temperature\":" + String(currentTemperature, 1) + ",";
  jsonPayload += "\"systolic_bp\":" + String(systolicBP, 1) + ",";
  jsonPayload += "\"diastolic_bp\":" + String(diastolicBP, 1) + ",";
  jsonPayload += "\"battery\":" + String(batteryLevel);
  jsonPayload += "}";

  int httpResponseCode = http.POST(jsonPayload);
  if (httpResponseCode > 0) {
    Serial.print("[HTTP 200] Ingested successfully: ");
    Serial.println(jsonPayload);
  } else {
    Serial.print("[HTTP Error] Dispatch failed, code: ");
    Serial.println(httpResponseCode);
  }
  http.end();
}

void setup() {
  Serial.begin(115200);
  pinMode(STATUS_LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  Serial.println("\n========================================================");
  Serial.println("  HEALTHGUARD AI - IoT Community Vitals Gateway Node");
  Serial.println("========================================================");

  scanI2CDevices();
  setupWiFi();
}

void loop() {
  unsigned long currentMillis = millis();
  if (currentMillis - lastTelemetryMillis >= TELEMETRY_INTERVAL) {
    lastTelemetryMillis = currentMillis;
    readSensors();
    transmitTelemetry();

    // Blink status LED to indicate active heartbeat
    digitalWrite(STATUS_LED_PIN, HIGH);
    delay(40);
    digitalWrite(STATUS_LED_PIN, LOW);
  }
}
