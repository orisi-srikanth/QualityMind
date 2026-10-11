"""
Reports, Dashboard Analytics & Audit Dossier Endpoints
Pareto charts, CAPA effectiveness z-tests, executive KPIs, and ISO 9001 PDF generation.
"""
import os
from fastapi import APIRouter, Response
from typing import Optional
from backend.app.services.pdf_report import generate_quality_pdf_report
from backend.app.orchestrator.engine import orchestrator

router = APIRouter()

@router.get("/pareto", tags=["Pareto"], summary="Defect Pareto distribution and Vital Few analysis", description="IATF 16949 Vital Few analysis calculating cumulative frequencies, Pareto classifications, and recommendation actions.")
def get_pareto(
    dimension: str = "defect_type",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    from backend.app.services.pareto import pareto_service
    from backend.app.database.session import SessionLocal
    db = SessionLocal()
    try:
        return pareto_service.compute_pareto(db=db, dimension=dimension, start_date=from_date, end_date=to_date)
    finally:
        db.close()

@router.get("/effectiveness/{capa_id}", tags=["Effectiveness"], summary="Verify CAPA intervention efficacy via two-proportion z-test", description="Two-proportion z-test evaluation comparing pre- and post-intervention rejection rates with statistical p-value and association disclaimer.")
def get_capa_effectiveness(capa_id: str = "CAPA-2026-088-01"):
    from backend.app.services.effectiveness import effectiveness_engine
    return effectiveness_engine.evaluate_capa_effectiveness(capa_id=capa_id)

@router.get("/dashboard/summary", tags=["Dashboard"], summary="Retrieve executive quality dashboard KPIs", description="Executive KPIs: acceptance rate, rejection rate, active incidents, open CAPAs, machine status, Pareto distribution, and SPC state.")
def get_dashboard_summary():
    return {
        "overall_health_score": 87.4,
        "active_batches_count": 3,
        "total_inspected_today": 1250,
        "acceptance_rate_percent": 94.8,
        "rejection_rate_percent": 5.2,
        "active_quality_incidents": 2,
        "machine_anomalies_detected": 1,
        "open_capas": 3,
        "overdue_capas": 0,
        "primary_machine_status": {
            "machine_id": "CNC-04",
            "status": "ATTENTION_REQUIRED",
            "vibration_mms": 3.8,
            "vibration_baseline": 2.1,
            "tool_cycles": 1150,
            "tool_cycle_limit": 800,
            "health_index": "62%"
        },
        "top_defect_categories": [
            {"defect": "Oversized shaft diameter", "count": 18, "percentage": 52.9},
            {"defect": "Surface scratch", "count": 9, "percentage": 26.5},
            {"defect": "Micro crack", "count": 4, "percentage": 11.8},
            {"defect": "Surface dent", "count": 3, "percentage": 8.8}
        ],
        "spc_status": {
            "process_capability_cpk": -0.18,
            "capability_state": "Incapable (Mean shifted toward USL)",
            "nelson_rules_active": ["Rule 1: Extreme Point Beyond 3-Sigma", "Rule 3: Continuous Upward Drift"]
        }
    }

@router.get("/reports/pdf", tags=["Reports"], summary="Download ISO 9001 / IATF 16949 audit dossier PDF report", description="Generates and streams comprehensive 12-section ISO 9001 / IATF 16949 compliant Audit Report PDF with embedded charts and epistemic labels.")
def download_pdf_report(batch_id: str = "BATCH-0245"):
    sample_img = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "samples", "sample_scratch.jpg"))
    state = orchestrator.run_full_pipeline(
        batch_meta={"batch_id": batch_id, "nominal_mm": 50.00, "tolerance_mm": 0.05},
        image_path=sample_img if os.path.exists(sample_img) else None
    )
    pdf_bytes = generate_quality_pdf_report(state.model_dump())
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Quality_Audit_Report_{batch_id}.pdf"}
    )
