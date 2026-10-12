"""
FastAPI Enterprise Application Entry Point
Agentic AI Manufacturing Quality Inspection & Root Cause Analysis System
Serves unified REST API, Static inspection media, and Production React Frontend.
"""
import os
import sys

# Ensure both repo root and backend directory are in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_current_dir)
_repo_dir = os.path.dirname(_backend_dir)
for _d in [_repo_dir, _backend_dir]:
    if _d not in sys.path:
        sys.path.insert(0, _d)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from backend.app.routers.api_router import router as api_router
from backend.app.routers.knowledge_router import router as knowledge_router
from backend.app.database.session import Base, engine
import backend.app.database.models

tags_metadata = [
    {"name": "Auth", "description": "Authentication, persona tokens, and RBAC profile"},
    {"name": "Products & Machines", "description": "Product catalogs, machine assets, and nominal specifications"},
    {"name": "Batches", "description": "Production batch management and anchor batch tracking"},
    {"name": "Inspection", "description": "Dimensional inspection intake and boundary-safe spec verification (Agent 1 & Agent 3)"},
    {"name": "Vision", "description": "Visual surface defect detection and proxy localization (Agent 2)"},
    {"name": "Process Monitoring", "description": "Real-time CNC telemetry, machine vibration, and anomaly detection (Agent 4)"},
    {"name": "SPC & Capability", "description": "Statistical Process Control, I-MR charts, Nelson rules, and Cp/Cpk indices (Agent 5)"},
    {"name": "Incidents", "description": "Quality incident records and Non-Conformance Reports (NCR)"},
    {"name": "Root Cause Analysis", "description": "5-Whys, 6M Ishikawa, and evidence-weighted causal reasoning (Agent 6)"},
    {"name": "RAG", "description": "In-process ChromaDB vector knowledge retrieval and SOP search"},
    {"name": "Pareto", "description": "Defect distribution and Vital Few analysis (IATF 16949)"},
    {"name": "CAPA", "description": "Corrective and Preventive Action planning and containment (Agent 7)"},
    {"name": "Workflows (Agents)", "description": "Stateful 8-Agent orchestration network and execution traces"},
    {"name": "Effectiveness", "description": "Two-proportion z-test statistical verification of CAPA efficacy"},
    {"name": "Dashboard", "description": "Aggregated factory floor metrics and real-time plant KPIs"},
    {"name": "Reports", "description": "ISO 9001 / IATF 16949 audit dossier PDF generation"},
    {"name": "System", "description": "Platform health, version telemetry, and runtime diagnostics"},
]

api_description = """
## QualityMind: Agentic Manufacturing Quality Decision-Support Platform

QualityMind is an enterprise industrial quality intelligence system engineered for high-precision CNC manufacturing cells. It orchestrates eight specialized AI agents with deterministic statistical process control, boundary-safe tolerance verification, computer vision defect localization, 8-parameter process anomaly detection, and human-in-the-loop engineering disposition.

### Mandatory Epistemic Labeling & Audit Governance
Every finding, chart, and recommendation is strictly partitioned into one of five epistemic labels:
- **`[OBSERVED FACT]`**: Verified direct measurements from calibrated sensors and gauges.
- **`[MODEL PREDICTION]`**: Inferences from computer vision and machine learning models.
- **`[STATISTICAL FINDING]`**: 3-sigma control limits, Nelson rule trips, and capability indices.
- **`[HYPOTHESIS]`**: Causal theories generated during Root Cause Analysis (RCA) requiring physical verification.
- **`[CONFIRMED ROOT CAUSE]`**: Final causal classification elevated exclusively by authenticated Quality Engineers.

### Human-in-the-Loop Decision Support
In compliance with IATF 16949 and ISO 9001, QualityMind functions exclusively as decision-support. It never autonomously releases batches, scraps parts, adjusts machine offsets, or stops production lines.

### Demo Personas & Credentials
Click the **Authorize** button at the top right to authenticate using Bearer JWT tokens.
- **Admin**: `admin@precisionaero.com` / `Admin123!` (Full platform administration & configuration)
- **Quality Engineer**: `engineer@precisionaero.com` / `Engineer123!` (Authorized to confirm root causes, sign off batches, approve CAPAs)
- **Operator**: `operator@precisionaero.com` / `Operator123!` (Inspection intake, telemetry monitoring; read-only on approvals)

**How to Authorize from Swagger:**
1. Call `POST /api/auth/login` with your username and password.
2. Copy the returned `access_token` string.
3. Click the green **Authorize** button at the top right of this page, paste the token, and click **Authorize**.
"""

app = FastAPI(
    title="QualityMind API",
    description=api_description,
    version="2.0.0",
    openapi_tags=tags_metadata,
    contact={
        "name": "Quality Engineering Team",
        "email": "quality@precisionaero.com"
    },
    license_info={
        "name": "Proprietary / Precision Aerospace Manufacturing",
        "url": "https://precisionaero.com/license"
    }
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database and Sample Assets on Startup
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

# Static files mount for uploaded/annotated inspection images
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
os.makedirs(os.path.join(static_dir, "uploads", "samples"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "uploads", "annotated"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=os.path.join(static_dir, "uploads")), name="uploads")

# Include API and Knowledge routers exactly once
app.include_router(api_router)
app.include_router(knowledge_router)

@app.get("/health", tags=["System"], summary="System Health & Readiness Check", description="Returns operational health status, active agents count, and governance mode.")
def health_check():
    return {
        "status": "HEALTHY",
        "system": "Agentic AI Manufacturing Quality Inspection & RCA System",
        "version": "2.0.0",
        "agents_active": 8,
        "mode": "HUMAN_IN_THE_LOOP_DECISION_SUPPORT"
    }

# Mount React Frontend Production Build (if built)
dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(dist_dir):
    assets_dir = os.path.join(dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        file_path = os.path.join(dist_dir, full_path)
        if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_dir, "index.html"))
else:
    @app.get("/", include_in_schema=False)
    def root_redirect():
        return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
