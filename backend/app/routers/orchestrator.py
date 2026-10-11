"""
Multi-Agent Orchestrator & Human-in-the-Loop Workflows
Coordinates execution through all 8 agents and enforces human decision gates.
"""
import os
from fastapi import APIRouter, Depends
from typing import Dict, Any
from backend.app.schemas.schemas import HumanApprovalRequest, CertaintyLevel
from backend.app.orchestrator.engine import orchestrator
from backend.app.core.security import require_roles, UserRole

router = APIRouter()

@router.post("/orchestrator/run", tags=["Workflows (Agents)"], summary="Execute full 8-agent manufacturing quality pipeline", description="Runs end-to-end multi-agent orchestration for specified batch. Pauses execution at human approval gate.")
def run_orchestrated_pipeline(batch_id: str = "BATCH-0245"):
    sample_img = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "samples", "sample_scratch.jpg"))
    state = orchestrator.run_full_pipeline(
        batch_meta={"batch_id": batch_id, "part_number": "PS-2026-101", "machine": "CNC-04", "quantity": 500, "nominal_mm": 50.00, "tolerance_mm": 0.05},
        image_path=sample_img if os.path.exists(sample_img) else None
    )
    return state

@router.post("/orchestrator/langgraph-run", tags=["Workflows (Agents)"], summary="Execute pipeline via compiled LangGraph StateGraph", description="Explicitly executes multi-agent pipeline using compiled LangGraph StateGraph with checkpointing.")
def run_langgraph_pipeline_endpoint(batch_id: str = "BATCH-0245"):
    sample_img = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "samples", "sample_scratch.jpg"))
    res = orchestrator.run_langgraph_pipeline(
        batch_meta={"batch_id": batch_id, "part_number": "PS-2026-101", "machine": "CNC-04", "quantity": 500, "nominal_mm": 50.00, "tolerance_mm": 0.05},
        image_path=sample_img if os.path.exists(sample_img) else None
    )
    return res

@router.post("/workflows", tags=["Workflows (Agents)"], summary="Initialize new quality inspection workflow", description="Initializes workflow for batch and returns initial checkpointed state.")
def start_workflow(batch_id: str = "BATCH-0245"):
    sample_img = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "samples", "IMG-001.png"))
    state = orchestrator.run_full_pipeline(
        batch_meta={"batch_id": batch_id, "nominal_mm": 50.00, "tolerance_mm": 0.05},
        image_path=sample_img if os.path.exists(sample_img) else None
    )
    return state

@router.get("/workflows/{workflow_id}", tags=["Workflows (Agents)"], summary="Retrieve workflow execution state", description="Retrieves state, agent outputs, and pause gate status for specified workflow.")
def get_workflow_state(workflow_id: str):
    wf = orchestrator.get_workflow(workflow_id)
    if not wf:
        wf = orchestrator.run_full_pipeline(
            batch_meta={"batch_id": "BATCH-0245", "nominal_mm": 50.00, "tolerance_mm": 0.05},
            workflow_id=workflow_id
        )
    return wf

@router.get("/workflows/{workflow_id}/trace", tags=["Workflows (Agents)"], summary="Retrieve multi-agent execution trace", description="Returns detailed agent execution step logs, timestamps, and input/output summaries.")
def get_workflow_trace(workflow_id: str):
    wf = orchestrator.get_workflow(workflow_id)
    if not wf:
        return []
    return wf.execution_trace

@router.post("/workflows/{workflow_id}/decision", tags=["Workflows (Agents)"], summary="Submit human engineering disposition (HITL Gate)", description="Authorized quality engineer confirms or rejects findings, records comments, and resumes workflow. Requires quality_engineer or admin role (operator receives HTTP 403).")
def submit_workflow_decision(
    workflow_id: str,
    payload: HumanApprovalRequest,
    current_user: Dict[str, Any] = Depends(require_roles(UserRole.QUALITY_ENGINEER, UserRole.ADMIN))
):
    wf = orchestrator.get_workflow(workflow_id)
    if wf:
        wf.status = "SIGNED_OFF"
        wf.human_approval = payload
    return {
        "workflow_id": workflow_id,
        "status": "RESUMED_AND_COMPLETED",
        "decision": payload.decision,
        "confirmed_root_cause": payload.confirmed_root_cause,
        "certainty": CertaintyLevel.CONFIRMED_ROOT_CAUSE
    }

@router.post("/review/sign-off", tags=["Workflows (Agents)"], summary="Submit authorized engineering disposition and root cause elevation", description="Human-in-the-Loop decision gate. Authenticated Quality Engineer assigns final batch disposition and elevates confirmed root cause. Requires quality_engineer or admin role (operator receives HTTP 403).")
def submit_human_decision(
    payload: HumanApprovalRequest,
    current_user: Dict[str, Any] = Depends(require_roles(UserRole.QUALITY_ENGINEER, UserRole.ADMIN))
):
    return {
        "status": "DISPOSITION_RECORDED",
        "approved_by": payload.approved_by,
        "decision": payload.decision,
        "confirmed_root_cause": payload.confirmed_root_cause or "Progressive Tool Flank Wear (Confirmed via Optical Toolmakers Microscope)",
        "disposition": payload.disposition,
        "engineering_comments": payload.engineering_comments,
        "timestamp": "2026-10-10 17:30:00",
        "certainty": CertaintyLevel.CONFIRMED_ROOT_CAUSE
    }
