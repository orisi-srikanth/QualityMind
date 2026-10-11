"""
Workflow State Schema for Multi-Agent Orchestration
Maintains synchronized immutable audit trace, execution logs, and findings across all agents.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from backend.app.models.schemas import (
    ProductionBatch, InspectionReport, VisualDefectPrediction,
    ProcessMonitoringReport, SPCReport, RCAReport, CAPAReport,
    CriticReview, AgentStepLog, HumanApprovalRequest
)

class WorkflowState(BaseModel):
    workflow_id: str
    batch_id: str
    status: str = "INITIALIZED"  # INITIALIZED, RUNNING, COMPLETED, PENDING_HUMAN_APPROVAL, SIGNED_OFF
    current_agent: Optional[str] = None
    execution_trace: List[AgentStepLog] = []

    # Agent Outputs
    batch_metadata: Optional[Dict[str, Any]] = None
    dimensional_report: Optional[InspectionReport] = None
    visual_prediction: Optional[VisualDefectPrediction] = None
    process_report: Optional[ProcessMonitoringReport] = None
    spc_report: Optional[SPCReport] = None
    rca_report: Optional[RCAReport] = None
    capa_report: Optional[CAPAReport] = None
    critic_review: Optional[CriticReview] = None
    human_approval: Optional[HumanApprovalRequest] = None

    # Error handling & flags
    has_defects: bool = False
    has_anomalies: bool = False
    has_spc_violations: bool = False
    completed_at: Optional[str] = None
