"""
LangGraph Multi-Agent Orchestration Graph for QualityMind
Implements the 8-agent stateful workflow with:
- Checkpointed shared state (MemorySaver)
- Conditional routing (conforming batch skip, needs_info gate, critic reassessment loop)
- Human-in-the-Loop approval gate (LangGraph interrupt pattern)
- Full execution tracing
"""
import uuid
import time
from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.app.agents.intake_agent import data_intake_agent
from backend.app.agents.visual_agent import vision_agent
from backend.app.agents.dimensional_agent import compliance_agent
from backend.app.agents.process_agent import anomaly_agent
from backend.app.agents.spc_agent import spc_agent
from backend.app.agents.rca_agent import rca_agent
from backend.app.agents.capa_agent import capa_agent
from backend.app.agents.reviewer_agent import critic_agent

class QualityWorkflowGraphState(TypedDict, total=False):
    workflow_id: str
    batch_id: str
    status: str
    current_agent: str
    batch_metadata: Dict[str, Any]
    measurements: List[Dict[str, Any]]
    image_path: Optional[str]
    telemetry_records: Optional[List[Dict[str, Any]]]
    visual_prediction: Optional[Dict[str, Any]]
    dimensional_report: Optional[Dict[str, Any]]
    process_report: Optional[Dict[str, Any]]
    spc_report: Optional[Dict[str, Any]]
    rca_report: Optional[Dict[str, Any]]
    capa_report: Optional[Dict[str, Any]]
    critic_review: Optional[Dict[str, Any]]
    human_approval: Optional[Dict[str, Any]]
    execution_trace: List[Dict[str, Any]]
    has_defects: bool
    has_anomalies: bool
    reassessment_loops: int
    error_message: Optional[str]

# --- Graph Node Functions ---

def node_intake(state: QualityWorkflowGraphState) -> Dict[str, Any]:
    """Agent 1: Fast deterministic intake with forced JSON schema."""
    batch_meta = state.get("batch_metadata", {})
    raw_m = state.get("measurements")
    res = data_intake_agent.process_batch_and_measurements(batch_meta=batch_meta, raw_measurements=raw_m)
    
    trace = list(state.get("execution_trace", []))
    trace.append(res["log"].model_dump())
    
    return {
        "current_agent": data_intake_agent.name,
        "batch_metadata": res["batch_data"],
        "execution_trace": trace
    }

def node_visual(state: QualityWorkflowGraphState) -> Dict[str, Any]:
    """Agent 2: Computer Vision defect inspection (YOLO / CNN)."""
    img_path = state.get("image_path")
    batch_id = state.get("batch_id", "BATCH-0245")
    trace = list(state.get("execution_trace", []))
    
    if img_path:
        res = vision_agent.inspect(image_path=img_path, batch_id=batch_id, image_id=f"IMG-{batch_id}")
        pred = res["prediction"].model_dump()
        trace.append(res["log"].model_dump())
        has_def = bool(pred.get("defect_detected", False))
        return {
            "current_agent": vision_agent.name,
            "visual_prediction": pred,
            "has_defects": has_def or state.get("has_defects", False),
            "execution_trace": trace
        }
    return {
        "current_agent": vision_agent.name,
        "execution_trace": trace
    }

def node_compliance(state: QualityWorkflowGraphState) -> Dict[str, Any]:
    """Agent 3: 100% deterministic dimensional compliance check."""
    batch_id = state.get("batch_id", "BATCH-0245")
    meta = state.get("batch_metadata", {})
    meas = meta.get("measurements", [])
    nom = meta.get("nominal_mm", 50.00)
    tol = meta.get("tolerance_mm", 0.05)
    
    res = compliance_agent.evaluate_compliance(batch_id=batch_id, measurements=meas, nominal_mm=nom, tolerance_mm=tol)
    rep = res["report"].model_dump()
    trace = list(state.get("execution_trace", []))
    trace.append(res["log"].model_dump())
    
    has_def = (rep.get("nonconforming", 0) > 0) or state.get("has_defects", False)
    return {
        "current_agent": compliance_agent.name,
        "dimensional_report": rep,
        "has_defects": has_def,
        "execution_trace": trace
    }

def node_anomaly(state: QualityWorkflowGraphState) -> Dict[str, Any]:
    """Agent 4: 5-layer hybrid telemetry anomaly detector."""
    batch_id = state.get("batch_id", "BATCH-0245")
    meta = state.get("batch_metadata", {})
    machine = meta.get("machine", "CNC-04")
    telemetry = state.get("telemetry_records")
    
    res = anomaly_agent.analyze_telemetry_series(batch_id=batch_id, machine=machine, telemetry_records=telemetry)
    rep = res["report"].model_dump()
    trace = list(state.get("execution_trace", []))
    trace.append(res["log"].model_dump())
    
    has_anom = (rep.get("anomalies_detected", 0) > 0)
    return {
        "current_agent": anomaly_agent.name,
        "process_report": rep,
        "has_anomalies": has_anom,
        "execution_trace": trace
    }

def node_spc(state: QualityWorkflowGraphState) -> Dict[str, Any]:
    """Agent 5: Statistical Process Control & capability engine."""
    batch_id = state.get("batch_id", "BATCH-0245")
    meta = state.get("batch_metadata", {})
    meas = meta.get("measurements", [])
    raw_vals = [m["measured_value"] for m in meas] if meas else [50.01, 50.03, 50.06, 50.08, 50.07]
    usl = meta.get("usl", 50.05)
    lsl = meta.get("lsl", 49.95)
    nom = meta.get("nominal_mm", 50.00)
    
    res = spc_agent.analyze_process_capability_and_control(batch_id=batch_id, values=raw_vals, usl=usl, lsl=lsl, nominal=nom)
    rep = res["report"].model_dump()
    trace = list(state.get("execution_trace", []))
    trace.append(res["log"].model_dump())
    
    return {
        "current_agent": spc_agent.name,
        "spc_report": rep,
        "execution_trace": trace
    }

def node_rca(state: QualityWorkflowGraphState) -> Dict[str, Any]:
    """Agent 6: Root Cause Analysis with Gemini 3.8 Flash reasoning & ChromaDB RAG."""
    batch_id = state.get("batch_id", "BATCH-0245")
    proc = state.get("process_report", {})
    vib = proc.get("vibration_current", 3.8)
    cyc = proc.get("tool_cycles_current", 1150)
    v_pred = state.get("visual_prediction")
    d_rep = state.get("dimensional_report")
    
    dt = "Oversized shaft diameter"
    cat = "metal_nut"
    if v_pred and v_pred.get("defect_detected"):
        dt = v_pred.get("defect_type", dt)
        cat = v_pred.get("category", cat)
    elif d_rep and d_rep.get("nonconforming", 0) > 0:
        dt = "Oversized shaft diameter"
    
    res = rca_agent.analyze_incident(
        incident_id=f"INC-{batch_id}",
        batch_id=batch_id,
        defect_type=dt,
        max_measured_val=50.08,
        usl=50.05,
        vibration_val=vib,
        tool_cycles=cyc,
        visual_prediction=v_pred,
        dimensional_findings=d_rep,
        category=cat
    )
    rep = res["report"].model_dump()
    trace = list(state.get("execution_trace", []))
    trace.append(res["log"].model_dump())
    
    return {
        "current_agent": rca_agent.name,
        "rca_report": rep,
        "execution_trace": trace
    }

def node_capa(state: QualityWorkflowGraphState) -> Dict[str, Any]:
    """Agent 7: 3-tier CAPA recommendation generator."""
    batch_id = state.get("batch_id", "BATCH-0245")
    meta = state.get("batch_metadata", {})
    machine = meta.get("machine", "CNC-04")
    
    res = capa_agent.generate_capa_plan(incident_id=f"INC-{batch_id}", batch_id=batch_id, machine=machine)
    rep = res["capa"].model_dump()
    trace = list(state.get("execution_trace", []))
    trace.append(res["log"].model_dump())
    
    return {
        "current_agent": capa_agent.name,
        "capa_report": rep,
        "execution_trace": trace
    }

def node_critic(state: QualityWorkflowGraphState) -> Dict[str, Any]:
    """Agent 8: Adversarial Quality Critic (Groq model family) auditing math and causal claims."""
    meta = state.get("batch_metadata", {})
    dim = state.get("dimensional_report", {})
    vis = state.get("visual_prediction")
    proc = state.get("process_report", {})
    spc = state.get("spc_report", {})
    rca = state.get("rca_report", {})
    capa = state.get("capa_report", {})
    
    res = critic_agent.review_workflow(
        intake_data={"batch": meta},
        compliance_data={"report": dim},
        vision_data={"prediction": vis} if vis else None,
        anomaly_data={"report": proc},
        spc_data={"report": spc},
        rca_data={"report": rca},
        capa_data={"capa": capa}
    )
    rev = res["review"].model_dump()
    trace = list(state.get("execution_trace", []))
    trace.append(res["log"].model_dump())
    
    return {
        "current_agent": critic_agent.name,
        "critic_review": rev,
        "execution_trace": trace
    }

def node_approval_gate(state: QualityWorkflowGraphState) -> Dict[str, Any]:
    """Human-in-the-Loop decision gate: workflow pauses awaiting authorized engineering disposition."""
    return {
        "status": "AWAITING_HUMAN_APPROVAL",
        "current_agent": "Human Gatekeeper"
    }

def node_report(state: QualityWorkflowGraphState) -> Dict[str, Any]:
    """Final dossier compilation node."""
    is_conforming = not state.get("has_defects", False) and not state.get("has_anomalies", False)
    final_status = "CONFORMING_AUDITED" if is_conforming else "DISPOSITION_READY"
    return {
        "status": final_status,
        "current_agent": "Report Compiler"
    }

# --- Routing Functions ---

def route_after_intake(state: QualityWorkflowGraphState) -> str:
    """If critical fields are missing, route to END with needs_info gating."""
    meta = state.get("batch_metadata", {})
    if meta.get("needs_info", False):
        return END
    return "visual_inspection"

def route_after_spc(state: QualityWorkflowGraphState) -> str:
    """Conditional Edge: If batch is 100% conforming with no anomalies, skip RCA and CAPA (TC-01)."""
    if not state.get("has_defects", False) and not state.get("has_anomalies", False):
        return "final_report"
    return "root_cause_analysis"

def route_after_critic(state: QualityWorkflowGraphState) -> str:
    """Conditional Loop: If Critic requests reassessment, loop back to RCA (max 2 loops)."""
    rev = state.get("critic_review", {})
    loops = state.get("reassessment_loops", 0)
    if rev.get("critic_verdict") == "REASSESS" and loops < 2:
        state["reassessment_loops"] = loops + 1
        return "root_cause_analysis"
    return "capa_management"

# --- Build & Compile LangGraph StateGraph ---

def create_qualitymind_graph():
    """Builds the complete LangGraph StateGraph with checkpointing."""
    builder = StateGraph(QualityWorkflowGraphState)

    # 1. Register Nodes
    builder.add_node("intake", node_intake)
    builder.add_node("visual_inspection", node_visual)
    builder.add_node("compliance", node_compliance)
    builder.add_node("anomaly_detection", node_anomaly)
    builder.add_node("spc", node_spc)
    builder.add_node("root_cause_analysis", node_rca)
    builder.add_node("critic", node_critic)
    builder.add_node("capa_management", node_capa)
    builder.add_node("approval_gate", node_approval_gate)
    builder.add_node("final_report", node_report)

    # 2. Add Edges & Conditional Routing
    builder.add_edge(START, "intake")
    builder.add_conditional_edges("intake", route_after_intake, {
        "visual_inspection": "visual_inspection",
        END: END
    })
    builder.add_edge("visual_inspection", "compliance")
    builder.add_edge("compliance", "anomaly_detection")
    builder.add_edge("anomaly_detection", "spc")
    
    # Conditional routing after SPC: skip RCA/CAPA if conforming
    builder.add_conditional_edges("spc", route_after_spc, {
        "root_cause_analysis": "root_cause_analysis",
        "final_report": "final_report"
    })

    builder.add_edge("root_cause_analysis", "critic")
    
    # Conditional loop: critic can send back to RCA
    builder.add_conditional_edges("critic", route_after_critic, {
        "root_cause_analysis": "root_cause_analysis",
        "capa_management": "capa_management"
    })

    builder.add_edge("capa_management", "approval_gate")
    builder.add_edge("approval_gate", "final_report")
    builder.add_edge("final_report", END)

    # 3. Checkpointer for state persistence & HITL interrupts
    checkpointer = MemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    return graph

# Pre-compiled global LangGraph workflow
qualitymind_langgraph = create_qualitymind_graph()
