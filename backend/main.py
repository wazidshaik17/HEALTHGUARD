import asyncio
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.database import Base, engine
from backend.seed import seed_database
from backend.websockets.vitals_hub import hub
from backend.routes import (
    auth,
    health,
    risk,
    symptoms,
    alerts,
    devices,
    doctor,
    admin,
    dashboard
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    seed_database()
    # Start background telemetry broadcast task
    asyncio.create_task(hub.start_broadcasting())
    yield
    # Shutdown
    hub.stop_broadcasting()

app = FastAPI(
    title="HEALTHGUARD AI",
    description="AI-Based Community Health Risk Prediction & Early Warning System API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth.router)
app.include_router(health.router)
app.include_router(risk.router)
app.include_router(symptoms.router)
app.include_router(alerts.router)
app.include_router(devices.router)
app.include_router(doctor.router)
app.include_router(admin.router)
app.include_router(dashboard.router)

# WebSocket Endpoint
@app.websocket("/ws/vitals")
async def websocket_vitals_endpoint(websocket: WebSocket):
    await hub.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Parse possible control commands from client
            try:
                import json
                msg = json.loads(data)
                if msg.get("action") == "trigger_anomaly":
                    hub.set_anomaly(msg.get("type", "tachycardia"))
                elif msg.get("action") == "clear_anomaly":
                    hub.clear_anomaly()
            except Exception:
                pass
    except WebSocketDisconnect:
        hub.disconnect(websocket)
    except Exception:
        hub.disconnect(websocket)

@app.get("/")
def root():
    return {
        "project": "HEALTHGUARD AI",
        "tagline": "AI-Based Community Health Risk Prediction & Early Warning System",
        "status": "online",
        "documentation": "/docs",
        "version": "1.0.0"
    }

@app.get("/api/health-check")
def health_check():
    return {
        "status": "healthy",
        "api": "FastAPI",
        "ai_model": "Random Forest Community Risk v1.0",
        "iot_hub": "Active",
        "websocket_endpoint": "/ws/vitals"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
