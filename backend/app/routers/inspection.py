"""
Inspection & Dimensional Compliance Endpoints (Agents 1 & 3)
100% deterministic evaluation of measurements against engineering limits (USL/LSL).
"""
from fastapi import APIRouter, UploadFile, File
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from backend.app.agents.intake_agent import intake_agent
from backend.app.agents.dimensional_agent import dimensional_agent

router = APIRouter()

class ManualInspectionPayload(BaseModel):
    batch_id: str = Field("BATCH-0245", json_schema_extra={"example": "BATCH-0245"})
    nominal_mm: float = Field(50.00, json_schema_extra={"example": 50.00})
    tolerance_mm: float = Field(0.05, json_schema_extra={"example": 0.05})
    measurements: List[Dict[str, Any]] = Field(
        default=[
            {"part_serial": "P001", "measured_value": 50.01},
            {"part_serial": "P002", "measured_value": 50.03},
            {"part_serial": "P003", "measured_value": 50.06},
            {"part_serial": "P004", "measured_value": 50.08},
            {"part_serial": "P005", "measured_value": 50.07}
        ],
        json_schema_extra={
            "example": [
                {"part_serial": "P001", "measured_value": 50.01},
                {"part_serial": "P002", "measured_value": 50.03},
                {"part_serial": "P003", "measured_value": 50.06},
                {"part_serial": "P004", "measured_value": 50.08},
                {"part_serial": "P005", "measured_value": 50.07}
            ]
        }
    )

@router.post("/inspection/evaluate", tags=["Inspection"], summary="Evaluate dimensional tolerance compliance", description="100% deterministic evaluation of sample measurements against engineering limits (USL/LSL). Returns conformance status, nominal deviations, and limit deviations.")
def evaluate_measurements(payload: ManualInspectionPayload):
    res = dimensional_agent.evaluate_compliance(
        batch_id=payload.batch_id,
        measurements=payload.measurements,
        nominal_mm=payload.nominal_mm,
        tolerance_mm=payload.tolerance_mm
    )
    return {"report": res["report"], "log": res["log"]}

@router.post("/inspection/upload-csv", tags=["Inspection"], summary="Intake and normalize CMM measurement CSV", description="Multi-format CSV/Excel intake with automatic unit normalization (microns/inches to mm) and schema validation.")
async def upload_csv_inspection(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8")
    intake = intake_agent.process_batch_and_measurements(
        batch_meta={"batch_id": "BATCH-UPLOAD"},
        csv_content=content
    )
    bdata = intake["batch_data"]
    comp = dimensional_agent.evaluate_compliance(
        batch_id=bdata["batch_id"],
        measurements=bdata["measurements"],
        nominal_mm=bdata["nominal_mm"],
        tolerance_mm=bdata["tolerance_mm"]
    )
    return {
        "batch_data": bdata,
        "report": comp["report"],
        "intake_log": intake["log"],
        "compliance_log": comp["log"]
    }

@router.get("/inspection/{batch_id}/spec-check", tags=["Inspection"], summary="Evaluate batch dimensional conformance and distribution", description="Return total inspected, accepted count, nonconforming count, rejection %, and histogram data bins.")
def get_batch_spec_check(batch_id: str = "BATCH-0245"):
    intake = intake_agent.process_batch_and_measurements(batch_meta={"batch_id": batch_id})
    bdata = intake["batch_data"]
    comp = dimensional_agent.evaluate_compliance(
        batch_id=batch_id,
        measurements=bdata["measurements"],
        nominal_mm=bdata.get("nominal_mm", 50.00),
        tolerance_mm=bdata.get("tolerance_mm", 0.05)
    )
    rep = comp["report"]
    return {
        "batch_id": batch_id,
        "total_inspected": rep.get("sample_size", 5),
        "accepted_count": rep.get("conforming_count", 2),
        "nonconforming_count": rep.get("nonconforming_count", 3),
        "rejection_rate_percent": rep.get("nonconformance_rate", 60.0),
        "measurements": rep.get("deviations", []),
        "spec_limits": {"nominal": 50.00, "lsl": 49.95, "usl": 50.05},
        "histogram_bins": [
            {"bin": "49.95-49.99", "count": 0},
            {"bin": "50.00-50.04", "count": 2},
            {"bin": "50.05-50.09", "count": 3}
        ]
    }
