"""
Domain Pydantic Schemas for Agentic AI Manufacturing Quality System
Strictly enforces the 5 Safety / Certainty Levels required for industrial decision-support.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class CertaintyLevel(str, Enum):
    OBSERVED_FACT = "Observed Fact"
    MODEL_PREDICTION = "Model Prediction"
    STATISTICAL_FINDING = "Statistical Finding"
    HYPOTHESIS = "Hypothesis"
    CONFIRMED_ROOT_CAUSE = "Confirmed Root Cause"

class BatchStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    CONFORMING = "CONFORMING"
    QUALITY_HOLD = "QUALITY_HOLD"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class ActionStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    VERIFIED = "VERIFIED"

# --- Product & Specification ---
class ProductSpec(BaseModel):
    product_id: str = "PROD-PS-101"
    name: str = "Precision Shaft"
    part_number: str = "PS-2026-101"
    machine_id: str = "CNC-04"
    material: str = "Carbon Steel"
    manufacturing_process: str = "CNC Lathe Turning & Grinding"
    inspection_parameter: str = "shaft_diameter"
    unit: str = "mm"
    nominal_mm: float = 50.00
    tolerance_mm: float = 0.05
    usl: float = 50.05
    lsl: float = 49.95
    inspection_frequency: str = "100% or 5-sample continuous sub-group"

# --- Production Batch ---
class ProductionBatch(BaseModel):
    batch_id: str = "BATCH-0245"
    product_id: str = "PROD-PS-101"
    part_number: str = "PS-2026-101"
    machine: str = "CNC-04"
    shift: str = "Night Shift"
    material: str = "Carbon Steel"
    material_lot: str = "LOT-CS-9842"
    quantity: int = 500
    start_time: str = "2026-10-10 02:00:00"
    end_time: Optional[str] = "2026-10-10 06:30:00"
    status: BatchStatus = BatchStatus.QUALITY_HOLD
    operator: str = "J. Smith (OP-44)"

# --- Agent 1: Data Intake Output Contract (Requirement 3) ---
class UnitConversionRecord(BaseModel):
    sample_id: str
    original_value: float
    original_unit: str
    converted_value_mm: float

class DataIntakeOutput(BaseModel):
    batch_id: str = "BATCH-0245"
    part_number: str = "PS-2026-101"
    machine: str = "CNC-04"
    quantity: int = 500
    material: str = "Carbon Steel"
    shift: str = "Night"
    inspection_parameter: str = "shaft_diameter"
    nominal_mm: float = 50.00
    tolerance_mm: float = 0.05
    usl: float = 50.05
    lsl: float = 49.95
    missing_fields: List[str] = Field(default_factory=list)
    unit_conversions: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    needs_info: bool = False
    measurements: List[Dict[str, Any]] = Field(default_factory=list)
    certainty: CertaintyLevel = CertaintyLevel.OBSERVED_FACT

# --- Inspection Measurement ---
class MeasurementItem(BaseModel):
    sample_id: str
    measured_value: float
    deviation_from_nominal: float
    deviation_from_limit: float
    is_conforming: bool
    status: str
    certainty: CertaintyLevel = CertaintyLevel.OBSERVED_FACT

class InspectionReport(BaseModel):
    batch_id: str
    total_inspected: int
    accepted: int
    nonconforming: int
    rejection_rate_percent: float
    measurements: List[MeasurementItem]
    nominal_mm: float
    tolerance_mm: float
    usl: float
    lsl: float
    certainty: CertaintyLevel = CertaintyLevel.OBSERVED_FACT

# --- Visual Inspection ---
class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int

class VisualDefectPrediction(BaseModel):
    image_id: str
    batch_id: str
    source: str = "MVTec AD (proxy part)"
    category: str = "metal_nut"
    defect_detected: bool
    anomaly_score: float = 0.0
    defect_type: str
    raw_class: str = "good"
    confidence: float
    location: str
    bbox: Optional[Dict[str, int]] = None
    bounding_box: Optional[BoundingBox] = None
    severity: str = "High"
    certainty: CertaintyLevel = CertaintyLevel.MODEL_PREDICTION
    label: str = "MODEL_PREDICTION"
    model_version: str = "mvtec-two-stage-v1.0"
    image_url: Optional[str] = None
    annotated_image_url: Optional[str] = None

# --- Process Monitoring & Telemetry ---
class TelemetryDataPoint(BaseModel):
    timestamp: str
    spindle_speed_rpm: float
    feed_rate_mmrev: float
    coolant_temperature_c: float
    machine_vibration_mms: float
    tool_usage_cycles: int
    motor_current_a: float
    cycle_time_s: float
    is_anomaly: bool = False
    anomaly_score: float = 0.0
    flags: List[str] = []
    certainty: CertaintyLevel = CertaintyLevel.STATISTICAL_FINDING

class ProcessMonitoringReport(BaseModel):
    batch_id: str
    machine: str
    total_data_points: int
    anomalies_detected: int
    critical_parameters: List[str]
    vibration_current: float
    vibration_baseline: float
    vibration_status: str
    tool_cycles_current: int
    tool_cycles_baseline: int
    tool_status: str
    temperature_current: float
    temperature_baseline: float
    drift_detected: bool
    certainty: CertaintyLevel = CertaintyLevel.STATISTICAL_FINDING

# --- SPC (Statistical Process Control) ---
class NelsonRuleViolation(BaseModel):
    rule_number: int
    rule_name: str
    description: str
    sample_indices: List[int]
    severity: str

class SPCReport(BaseModel):
    batch_id: str
    sample_size: int
    mean: float
    std_dev: float
    ucl: float  # Statistical Upper Control Limit (Mean + 3 sigma)
    lcl: float  # Statistical Lower Control Limit (Mean - 3 sigma)
    cl: float   # Center Line (Mean)
    usl: float  # Engineering Upper Specification Limit
    lsl: float  # Engineering Lower Specification Limit
    cp: float   # Capability index Cp = (USL - LSL) / (6 * sigma)
    cpk: float  # Process capability Cpk = min((USL - mean)/(3*sigma), (mean - LSL)/(3*sigma))
    pp: float   # Performance Pp
    ppk: float  # Performance Ppk
    capability_assessment: str
    chart_data: List[Dict[str, Any]]
    nelson_violations: List[NelsonRuleViolation]
    distinction_warning: str = (
        "SPECIFICATION LIMITS (USL/LSL = 50.05/49.95) are engineering tolerance boundaries. "
        "STATISTICAL CONTROL LIMITS (UCL/LCL) represent natural 3-sigma process variation. "
        "They are mathematically and operationally distinct concepts."
    )
    certainty: CertaintyLevel = CertaintyLevel.STATISTICAL_FINDING

# --- RCA (Root Cause Analysis) ---
class HypothesisEvidence(BaseModel):
    hypothesis_id: str
    title: str
    description: str
    category: str  # Machine, Method, Material, Manpower, Measurement, Milieu (6M)
    confidence_score: float
    supporting_evidence: List[str]
    contradicting_evidence: List[str]
    required_confirmation: str
    status: str = "Under Investigation"
    certainty: CertaintyLevel = CertaintyLevel.HYPOTHESIS

class FiveWhysItem(BaseModel):
    level: int
    question: str
    answer: str
    evidence: str

class FishboneCategory(BaseModel):
    category: str
    factors: List[str]

class HistoricalIncident(BaseModel):
    incident_id: str
    date: str
    title: str
    defect_type: str
    machine: str
    material: str
    confirmed_root_cause: str
    similarity_score: float
    action_taken: str
    certainty: CertaintyLevel = CertaintyLevel.CONFIRMED_ROOT_CAUSE

class RCAReport(BaseModel):
    incident_id: str
    batch_id: str
    problem_statement: str
    ranked_hypotheses: List[HypothesisEvidence]
    five_whys: List[FiveWhysItem]
    fishbone_diagram: List[FishboneCategory]
    historical_matches: List[HistoricalIncident]
    correlation_vs_causation_note: str = (
        "IMPORTANT: Statistical correlation does not establish proven causation. "
        "Hypotheses require physical engineering verification before confirmation."
    )
    certainty: CertaintyLevel = CertaintyLevel.HYPOTHESIS

# --- CAPA (Corrective and Preventive Action) ---
class ActionItem(BaseModel):
    action_id: str
    type: str  # Immediate Containment, Potential Corrective Action, Preventive Action
    description: str
    assigned_role: str
    due_date: str
    status: ActionStatus = ActionStatus.PENDING
    evidence_required: str
    completion_date: Optional[str] = None
    effectiveness_metric: Optional[str] = None

class CAPAReport(BaseModel):
    capa_id: str
    incident_id: str
    batch_id: str
    containment_actions: List[ActionItem]
    corrective_actions: List[ActionItem]
    preventive_actions: List[ActionItem]
    requires_engineer_approval: bool = True
    approval_status: str = "PENDING_ENGINEER_APPROVAL"
    approver: Optional[str] = None
    approved_at: Optional[str] = None
    effectiveness_result: Optional[str] = None

# --- Quality Reviewer / Critic ---
class CriticReview(BaseModel):
    verified_spec_references: bool
    validated_calculations: bool
    cv_predictions_verified: bool
    unsupported_causal_claims_detected: bool
    review_comments: List[str]
    critic_verdict: str  # APPROVED, CONDITIONAL_APPROVAL, REASSESSMENT_REQUIRED
    certainty: CertaintyLevel = CertaintyLevel.STATISTICAL_FINDING

# --- Human Approval ---
class HumanApprovalRequest(BaseModel):
    approved_by: str
    decision: str  # ACCEPT_FINDINGS, REJECT_FINDINGS, REQUEST_REASSESSMENT
    engineering_comments: str
    confirmed_root_cause: Optional[str] = None
    approved_capa_ids: List[str] = []
    disposition: str  # QUARANTINE_BATCH, REWORK_WINDOW, SCRAP, RELEASE_WITH_DEVIATION

# --- Full Agent Execution State ---
class AgentStepLog(BaseModel):
    step_number: int
    agent_name: str
    status: str
    input_summary: str
    tool_calls: List[str]
    output_summary: str
    certainty_level: CertaintyLevel
    duration_ms: int
    timestamp: str

# --- RAG Knowledge Base Schemas ---
class KnowledgeStatusResponse(BaseModel):
    status: str
    collection_name: str
    persist_directory: str
    document_count: int
    embedding_model: str
    embedding_type: str
    llm_mode: str
    llm_enabled: bool
    available_source_files: List[str] = []
    last_ingestion: Optional[Dict[str, Any]] = None
    warnings: List[str] = []

class KnowledgeIngestRequest(BaseModel):
    source_paths: Optional[List[str]] = None
    force_reindex: bool = False

class KnowledgeIngestResponse(BaseModel):
    status: str
    files_discovered: int
    files_processed: int
    files_updated: int
    files_skipped: int
    chunks_added: int
    chunks_updated: int
    chunks_deleted: int
    per_file_status: Dict[str, Any] = {}
    warnings: List[str] = []
    errors: List[str] = []

class KnowledgeQueryRequest(BaseModel):
    query: str
    top_k: int = 5
    category: Optional[str] = None
    source_file: Optional[str] = None
    batch_id: Optional[str] = None
    machine_id: Optional[str] = None
    part_number: Optional[str] = None
    record_id: Optional[str] = None

class KnowledgeMatchItem(BaseModel):
    id: str
    text: str
    source_file: str
    record_id: Optional[str] = None
    category: str
    metadata: Dict[str, Any] = {}
    chunk_index: int = 0
    distance: float = 0.0
    similarity_score: float = 0.0
    distance_metric: str = "cosine_distance"
    rank: int = 1

class KnowledgeQueryResponse(BaseModel):
    query: str
    answer: str
    answer_mode: str
    llm_enabled: bool
    results_count: int
    matches: List[KnowledgeMatchItem] = []
    sources: List[str] = []
    distance_metric: str = "cosine_distance"
    warnings: List[str] = []
