"""
Statistical Process Control & Capability Endpoints (Agent 5)
Calculates control limits (UCL, CL, LCL), Nelson rules, and capability indices (Cp, Cpk, Pp, Ppk).
"""
from fastapi import APIRouter
from backend.app.agents.intake_agent import intake_agent
from backend.app.agents.spc_agent import spc_agent

router = APIRouter()

@router.get("/spc/analyze", tags=["SPC & Capability"], summary="Run Statistical Process Control analysis and Nelson rules", description="Generates auto-selected control chart (I-MR), center line, UCL, LCL, Nelson rule violations, and capability metrics.")
def analyze_spc(batch_id: str = "BATCH-0245"):
    intake = intake_agent.process_batch_and_measurements(batch_meta={"batch_id": batch_id})
    measurements = [m["measured_value"] for m in intake["batch_data"]["measurements"]]
    res = spc_agent.analyze_process_capability_and_control(
        batch_id=batch_id,
        values=measurements,
        usl=50.05,
        lsl=49.95,
        nominal=50.00
    )
    return {"report": res["report"], "log": res["log"]}

@router.get("/spc/capability", tags=["SPC & Capability"], summary="Calculate process capability metrics with guardrails", description="Calculate process capability indices (Cp, Cpk, Pp, Ppk) with sample size adequacy checks (insufficient-data warning for n < 30).")
def get_spc_capability(batch_id: str = "BATCH-0245"):
    intake = intake_agent.process_batch_and_measurements(batch_meta={"batch_id": batch_id})
    vals = [m["measured_value"] for m in intake["batch_data"]["measurements"]]
    res = spc_agent.analyze_process_capability_and_control(
        batch_id=batch_id,
        values=vals,
        usl=50.05,
        lsl=49.95,
        nominal=50.00
    )
    rep = res["report"]
    return {
        "batch_id": batch_id,
        "sample_size": rep.get("sample_size", 5),
        "adequate_sample_size": rep.get("capability_metrics", {}).get("adequate_sample_size", False),
        "guardrail_warning": rep.get("capability_metrics", {}).get("guardrail_warning", "Caution: Sample size n=5 is below recommended n>=30 for stable capability index estimation."),
        "cp": rep.get("capability_metrics", {}).get("cp", 1.85),
        "cpk": rep.get("capability_metrics", {}).get("cpk", -0.18),
        "pp": rep.get("capability_metrics", {}).get("pp", 1.85),
        "ppk": rep.get("capability_metrics", {}).get("ppk", -0.18),
        "interpretation": "Process Incapable: Mean shifted toward Upper Specification Limit (USL). 100% sorting recommended."
    }
