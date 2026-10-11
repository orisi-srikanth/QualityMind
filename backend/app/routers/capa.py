"""
Corrective & Preventive Action Endpoints (Agent 7)
Generates 3-tiered action plans (Containment, Corrective, Preventive) requiring human sign-off.
"""
from fastapi import APIRouter
from backend.app.agents.capa_agent import capa_agent

router = APIRouter()

@router.get("/capa/plan", tags=["CAPA"], summary="Generate 3-tiered CAPA action plan", description="Generate 3-tiered CAPA recommendations: Immediate Containment (quarantine), Corrective Action (tool replacement), and Preventive Action (SPC gate).")
def get_capa(incident_id: str = "INC-2026-088", batch_id: str = "BATCH-0245"):
    res = capa_agent.generate_capa_plan(incident_id=incident_id, batch_id=batch_id, machine="CNC-04")
    return {"capa": res["capa"], "log": res["log"]}
