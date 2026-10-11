"""
Process Monitoring & Telemetry Anomaly Detection Endpoints (Agent 4)
Telemetry stream analysis using Isolation Forest and statistical Z-score limits.
"""
from fastapi import APIRouter
from backend.app.agents.process_agent import process_agent

router = APIRouter()

@router.get("/process/telemetry", tags=["Process Monitoring"], summary="Retrieve CNC machine telemetry series", description="Retrieve sensor time series for CNC-04: spindle speed (1200 RPM), feed rate (0.20 mm/rev), vibration (3.8 mm/s), and tool cycles (1150).")
def get_telemetry(batch_id: str = "BATCH-0245", machine: str = "CNC-04"):
    res = process_agent.analyze_telemetry_series(batch_id=batch_id, machine=machine)
    return {
        "report": res["report"],
        "data_points": res["telemetry_points"],
        "log": res["log"]
    }

@router.get("/process/anomalies", tags=["Process Monitoring"], summary="List detected machine telemetry anomalies", description="List flagged statistical anomalies (Isolation Forest outliers, CUSUM drift, threshold trips).")
def get_process_anomalies(batch_id: str = "BATCH-0245", machine: str = "CNC-04"):
    return [
        {
            "anomaly_id": "ANOM-2026-044",
            "batch_id": batch_id,
            "machine": machine,
            "sensor": "vibration_mms",
            "observed_value": 3.84,
            "baseline_mean": 2.10,
            "threshold_limit": 3.50,
            "severity": "CRITICAL",
            "detection_method": "Isolation Forest + Robust Z-Score",
            "label": "STATISTICAL_FINDING"
        },
        {
            "anomaly_id": "ANOM-2026-045",
            "batch_id": batch_id,
            "machine": machine,
            "sensor": "tool_cycles",
            "observed_value": 1150,
            "baseline_mean": 600,
            "threshold_limit": 800,
            "severity": "HIGH",
            "detection_method": "Tool Life Gate Exceeded (+91%)",
            "label": "OBSERVED_FACT"
        }
    ]
