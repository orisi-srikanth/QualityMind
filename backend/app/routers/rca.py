"""
Root Cause Analysis & Historical Incidents Endpoints (Agent 6)
Performs 5-Whys, 6M Ishikawa fishbone, evidence ranking, and semantic RAG retrieval.
"""
from fastapi import APIRouter
from backend.app.agents.rca_agent import rca_agent
from backend.app.services.rag_search import vector_store

router = APIRouter()

@router.get("/incidents", tags=["Incidents"], summary="List Quality Incidents and Non-Conformance Reports (NCR)", description="List all active and closed Quality Non-Conformance Reports with assigned severity and status.")
def get_incidents():
    return [
        {
            "incident_id": "INC-2026-088",
            "batch_id": "BATCH-0245",
            "title": "Dimensional Non-Conformance: Oversized Shaft Diameter",
            "defect_type": "Oversized shaft diameter",
            "machine": "CNC-04",
            "severity": "High",
            "status": "OPEN",
            "created_at": "2026-10-10 05:45:00",
            "impacted_quantity": "500 units on Quality Hold",
            "primary_hypothesis": "Tool Flank Wear (88% confidence)",
            "critic_verdict": "APPROVED"
        },
        {
            "incident_id": "INC-2026-082",
            "batch_id": "BATCH-0238",
            "title": "Visual Defect: Surface Chatter Scratches",
            "defect_type": "surface_scratch",
            "machine": "CNC-04",
            "severity": "Medium",
            "status": "CLOSED",
            "created_at": "2026-10-08 14:20:00",
            "impacted_quantity": "40 units reworked",
            "primary_hypothesis": "Spindle harmonic vibration",
            "critic_verdict": "APPROVED"
        }
    ]

@router.get("/rca/analyze", tags=["Root Cause Analysis"], summary="Execute 5-Whys and 6M Ishikawa Root Cause Analysis", description="Execute 6M Ishikawa fishbone analysis, 5-Whys causal chains, and evidence weighting across candidate root causes.")
def get_rca(incident_id: str = "INC-2026-088", batch_id: str = "BATCH-0245"):
    res = rca_agent.analyze_incident(
        incident_id=incident_id,
        batch_id=batch_id,
        defect_type="Oversized shaft diameter",
        max_measured_val=50.08,
        usl=50.05,
        vibration_val=3.8,
        tool_cycles=1150
    )
    return {"report": res["report"], "log": res["log"]}

@router.get("/rca/rag-search", tags=["Root Cause Analysis"], summary="Vector semantic search across historical NCR archives", description="Search historical quality incidents and SOP archives in ChromaDB. Query 'oversized shaft diameter' returns historical match NCR-019.")
def search_historical_incidents(q: str = "Oversized shaft diameter tool wear", top_k: int = 4):
    matches = vector_store.search(query=q, top_k=top_k)
    return {"query": q, "matches": matches}
