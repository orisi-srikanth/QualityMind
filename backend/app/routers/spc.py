"""
Statistical Process Control & Capability Endpoints (Agent 5)
Calculates control limits (UCL, CL, LCL), Nelson rules, and capability indices (Cp, Cpk, Pp, Ppk).
Strictly adheres to AIAG SPC guidelines and IATF 16949:2016 Section 8.5.1.
Enforces sample size guardrails (n < 5 suppressed, 5 <= n < 30 preliminary with warnings)
and assumption checks (normality, stability, variance, drift, outliers, mixed lots).
"""
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, Body, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.database.models import Batch, InspectionCharacteristic, SPCResult
from backend.app.agents.intake_agent import intake_agent
from backend.app.agents.spc_agent import spc_agent
from backend.app.services.capability import capability_engine
from backend.app.schemas.schemas import CapabilityRequest, CapabilityResponse

router = APIRouter()

def _persist_spc_result(
    db: Session,
    batch_identifier: str,
    cl: float,
    ucl: float,
    lcl: float,
    cp: Optional[float],
    cpk: Optional[float],
    pp: Optional[float],
    ppk: Optional[float],
    n: int,
    violations: list,
    warnings: list,
    characteristic_id: Optional[str] = None
) -> Optional[str]:
    """Helper to persist capability and control metrics into spc_results table."""
    try:
        # Resolve batch
        batch = db.query(Batch).filter(
            (Batch.id == batch_identifier) | (Batch.batch_number == batch_identifier)
        ).first()
        actual_batch_id = batch.id if batch else batch_identifier

        # Resolve characteristic
        char_obj = None
        if characteristic_id:
            char_obj = db.query(InspectionCharacteristic).filter(
                (InspectionCharacteristic.id == characteristic_id) |
                (InspectionCharacteristic.name == characteristic_id)
            ).first()
        if not char_obj:
            char_obj = db.query(InspectionCharacteristic).filter(
                InspectionCharacteristic.name == "shaft_diameter"
            ).first()
        actual_char_id = char_obj.id if char_obj else (characteristic_id or "char-ps-01")

        violations_serialized = []
        for v in violations:
            if hasattr(v, "model_dump"):
                violations_serialized.append(v.model_dump())
            elif hasattr(v, "dict"):
                violations_serialized.append(v.dict())
            elif isinstance(v, dict):
                violations_serialized.append(v)
            else:
                violations_serialized.append(str(v))

        record = SPCResult(
            batch_id=actual_batch_id,
            characteristic_id=actual_char_id,
            chart_type="I-MR",
            center_line=float(cl),
            ucl=float(ucl),
            lcl=float(lcl),
            violations_json=json.dumps(violations_serialized),
            cp=float(cp) if cp is not None else None,
            cpk=float(cpk) if cpk is not None else None,
            pp=float(pp) if pp is not None else None,
            ppk=float(ppk) if ppk is not None else None,
            n=int(n),
            warnings_json=json.dumps(warnings)
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record.id
    except Exception as e:
        db.rollback()
        return None

SUFFICIENT_EXAMPLE = {
    "batch_id": "BATCH-SUFFICIENT-01",
    "status": "sufficient",
    "sample_size": 100,
    "mean": 50.0012,
    "std_dev": 0.0098,
    "sigma_within": 0.0096,
    "sigma_within_method": "Moving Range MR-bar / d2 (d2=1.128 for n=2 consecutive differences)",
    "sigma_overall": 0.0098,
    "sigma_overall_method": "Sample Standard Deviation s (ddof=1)",
    "usl": 50.05,
    "lsl": 49.95,
    "target": 50.00,
    "tolerance_band": 0.10,
    "cp": 1.7361,
    "cpk": 1.6944,
    "cpu": 1.6944,
    "cpl": 1.7778,
    "pp": 1.7007,
    "ppk": 1.6599,
    "ppu": 1.6599,
    "ppl": 1.7415,
    "cpk_ci_95": {
        "lower": 1.4852,
        "upper": 1.9036,
        "standard_error": 0.1067,
        "confidence_level": 0.95,
        "note": "95% confidence interval [1.4852, 1.9036] based on n=100 observations."
    },
    "normality_test": {
        "test": "Shapiro-Wilk",
        "statistic": 0.9912,
        "p_value": 0.7421,
        "alpha": 0.05,
        "is_normal": True
    },
    "stability_test": {
        "is_in_control": True,
        "violations": []
    },
    "trend_test": {
        "is_trending": False,
        "slope": 0.00001,
        "p_value": 0.6512,
        "alpha": 0.05
    },
    "outliers": [],
    "assessment": "Capable Process (1.33 <= Cpk < 1.67) — Conforms to standard industrial quality benchmarks.",
    "interpretation_band": "Capable (1.33 to 1.67)",
    "benchmark_source": "AIAG Statistical Process Control (SPC) Reference Manual (2nd Edition) & IATF 16949:2016 Section 8.5.1",
    "warnings": [],
    "guidance_notice": "DECISION GUIDANCE ONLY: Capability indices are statistical indicators for process improvement and supervision. QualityMind does not perform automatic lot acceptance, rejection, or quarantine decisions solely based on capability metrics without authorized quality engineering disposition.",
    "future_guarantee_disclaimer": "DISCLAIMER: Process capability metrics reflect historical statistical performance under observed conditions and do NOT constitute a guarantee of future zero-defect production or parts conformity.",
    "label": "[STATISTICAL_FINDING]"
}

INSUFFICIENT_EXAMPLE = {
    "batch_id": "BATCH-SMALL-03",
    "status": "insufficient_data",
    "sample_size": 3,
    "mean": None,
    "std_dev": None,
    "sigma_within": None,
    "sigma_within_method": None,
    "sigma_overall": None,
    "sigma_overall_method": "Sample Standard Deviation s (ddof=1)",
    "usl": 50.05,
    "lsl": 49.95,
    "target": 50.00,
    "tolerance_band": None,
    "cp": None,
    "cpk": None,
    "cpu": None,
    "cpl": None,
    "pp": None,
    "ppk": None,
    "ppu": None,
    "ppl": None,
    "cpk_ci_95": None,
    "normality_test": None,
    "stability_test": None,
    "trend_test": None,
    "outliers": [],
    "assessment": "Insufficient Data for Capability Assessment",
    "interpretation_band": None,
    "benchmark_source": "AIAG Statistical Process Control (SPC) Reference Manual (2nd Edition) & IATF 16949:2016 Section 8.5.1",
    "warnings": [
        "INSUFFICIENT DATA: Sample size n=3 is below minimum threshold (n >= 5) required for statistical capability estimation. Numeric capability indices suppressed."
    ],
    "guidance_notice": "DECISION GUIDANCE ONLY: Capability indices are statistical indicators for process improvement and supervision. QualityMind does not perform automatic lot acceptance, rejection, or quarantine decisions solely based on capability metrics without authorized quality engineering disposition.",
    "future_guarantee_disclaimer": "DISCLAIMER: Process capability metrics reflect historical statistical performance under observed conditions and do NOT constitute a guarantee of future zero-defect production or parts conformity.",
    "label": "[STATISTICAL_FINDING]"
}

@router.get(
    "/spc/analyze",
    tags=["SPC & Capability"],
    summary="Run Statistical Process Control analysis and Nelson rules",
    description="Generates auto-selected control chart (I-MR), center line, UCL, LCL, Nelson rule violations, and capability metrics with DB persistence."
)
def analyze_spc(batch_id: str = "BATCH-0245", db: Session = Depends(get_db)):
    intake = intake_agent.process_batch_and_measurements(batch_meta={"batch_id": batch_id})
    measurements = [m["measured_value"] for m in intake["batch_data"]["measurements"]]
    res = spc_agent.analyze_process_capability_and_control(
        batch_id=batch_id,
        values=measurements,
        usl=50.05,
        lsl=49.95,
        nominal=50.00
    )
    rep = res["report"]
    _persist_spc_result(
        db=db,
        batch_identifier=batch_id,
        cl=rep.cl,
        ucl=rep.ucl,
        lcl=rep.lcl,
        cp=rep.cp,
        cpk=rep.cpk,
        pp=rep.pp,
        ppk=rep.ppk,
        n=rep.sample_size,
        violations=rep.nelson_violations,
        warnings=rep.warnings
    )
    return {"report": rep, "log": res["log"]}

@router.get(
    "/spc/capability",
    tags=["SPC & Capability"],
    summary="Calculate process capability metrics with guardrails",
    description=(
        "Calculates process capability indices (Cp, Cpk, Pp, Ppk) with sample size adequacy checks "
        "(insufficient-data status and numeric suppression for n < 5; prominent warning for 5 <= n < 30). "
        "Evaluates normality (Shapiro-Wilk), statistical stability (Nelson rules), process drift, "
        "and zero-variance conditions."
    ),
    responses={
        200: {
            "description": "Calculated capability metrics or insufficient-data status with guardrails.",
            "content": {
                "application/json": {
                    "examples": {
                        "sufficient_sample": {
                            "summary": "Sufficient In-Control Sample (n = 100)",
                            "description": "Demonstrates normal in-control dataset exceeding n >= 30 sufficiency threshold.",
                            "value": SUFFICIENT_EXAMPLE
                        },
                        "insufficient_sample": {
                            "summary": "Insufficient Sample (n = 3)",
                            "description": "Demonstrates strict refusal and numeric suppression for sample size n < 5.",
                            "value": INSUFFICIENT_EXAMPLE
                        }
                    }
                }
            }
        }
    }
)
def get_spc_capability(batch_id: str = "BATCH-0245", db: Session = Depends(get_db)):
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

    _persist_spc_result(
        db=db,
        batch_identifier=batch_id,
        cl=rep.cl,
        ucl=rep.ucl,
        lcl=rep.lcl,
        cp=rep.cp,
        cpk=rep.cpk,
        pp=rep.pp,
        ppk=rep.ppk,
        n=rep.sample_size,
        violations=rep.nelson_violations,
        warnings=rep.warnings
    )

    return {
        "batch_id": batch_id,
        "status": rep.status,
        "sample_size": rep.sample_size,
        "mean": rep.mean,
        "std_dev": rep.std_dev,
        "sigma_within": rep.sigma_within,
        "sigma_within_method": rep.sigma_within_method,
        "sigma_overall": rep.sigma_overall,
        "sigma_overall_method": rep.sigma_overall_method,
        "usl": rep.usl,
        "lsl": rep.lsl,
        "target": 50.00,
        "tolerance_band": round(rep.usl - rep.lsl, 4) if (rep.usl is not None and rep.lsl is not None) else None,
        "cp": rep.cp,
        "cpk": rep.cpk,
        "pp": rep.pp,
        "ppk": rep.ppk,
        "cpk_ci_95": rep.cpk_ci_95,
        "assessment": rep.capability_assessment,
        "interpretation_band": rep.interpretation_band,
        "benchmark_source": "AIAG Statistical Process Control (SPC) Reference Manual (2nd Edition) & IATF 16949:2016 Section 8.5.1",
        "warnings": rep.warnings,
        "guidance_notice": rep.guidance_notice or (
            "DECISION GUIDANCE ONLY: Capability indices are statistical indicators for process improvement and supervision. "
            "QualityMind does not perform automatic lot acceptance, rejection, or quarantine decisions solely based on capability metrics "
            "without authorized quality engineering disposition."
        ),
        "future_guarantee_disclaimer": rep.future_guarantee_disclaimer or (
            "DISCLAIMER: Process capability metrics reflect historical statistical performance under observed conditions "
            "and do NOT constitute a guarantee of future zero-defect production or parts conformity."
        ),
        "label": "[STATISTICAL_FINDING]"
    }

@router.post(
    "/spc/capability",
    tags=["SPC & Capability"],
    summary="Compute process capability for custom measurement dataset",
    description="Submits arbitrary measurement readings, tolerance specifications, and metadata to evaluate capability and statistical assumptions.",
    response_model=CapabilityResponse,
    responses={
        200: {
            "description": "Calculated capability metrics or guardrail refusal.",
            "content": {
                "application/json": {
                    "examples": {
                        "sufficient_sample": {
                            "summary": "Sufficient Sample Example (n = 100)",
                            "value": SUFFICIENT_EXAMPLE
                        },
                        "insufficient_sample": {
                            "summary": "Insufficient Sample Example (n = 3)",
                            "value": INSUFFICIENT_EXAMPLE
                        }
                    }
                }
            }
        }
    }
)
def compute_custom_capability(
    payload: CapabilityRequest = Body(...),
    db: Session = Depends(get_db)
):
    cap_res = capability_engine.calculate_capability(
        values=payload.values,
        usl=payload.usl,
        lsl=payload.lsl,
        target=payload.nominal,
        subgroup_size=payload.subgroup_size,
        machine_ids=payload.machine_ids,
        batch_ids=payload.batch_ids
    )

    # Persist if batch_id provided
    if payload.batch_id and cap_res["sample_size"] >= 2:
        cl_val = cap_res.get("mean") or 0.0
        s_val = cap_res.get("sigma_within") or cap_res.get("sigma_overall") or 0.001
        ucl_val = cl_val + 3.0 * s_val
        lcl_val = cl_val - 3.0 * s_val
        _persist_spc_result(
            db=db,
            batch_identifier=payload.batch_id,
            cl=cl_val,
            ucl=ucl_val,
            lcl=lcl_val,
            cp=cap_res.get("cp"),
            cpk=cap_res.get("cpk"),
            pp=cap_res.get("pp"),
            ppk=cap_res.get("ppk"),
            n=cap_res["sample_size"],
            violations=[],
            warnings=cap_res.get("warnings", [])
        )

    cap_res["batch_id"] = payload.batch_id
    return cap_res
