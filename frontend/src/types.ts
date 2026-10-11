export type CertaintyLevel = 
  | "Observed Fact"
  | "Model Prediction"
  | "Statistical Finding"
  | "Hypothesis"
  | "Confirmed Root Cause";

export interface ProductSpec {
  product_id: string;
  name: string;
  part_number: string;
  machine_id: string;
  material: string;
  manufacturing_process: string;
  inspection_parameter: string;
  unit: string;
  nominal_mm: float;
  tolerance_mm: float;
  usl: float;
  lsl: float;
  inspection_frequency: string;
}

export type float = number;

export interface ProductionBatch {
  batch_id: string;
  product_id: string;
  part_number: string;
  machine: string;
  material: string;
  material_lot: string;
  shift: string;
  quantity: number;
  start_time: string;
  end_time?: string;
  status: string;
  operator: string;
  rejection_rate?: string;
  nonconforming_count?: number;
}

export interface MeasurementItem {
  sample_id: string;
  measured_value: number;
  deviation_from_nominal: number;
  deviation_from_limit: number;
  is_conforming: boolean;
  status: string;
  certainty: CertaintyLevel;
}

export interface InspectionReport {
  batch_id: string;
  total_inspected: number;
  accepted: number;
  nonconforming: number;
  rejection_rate_percent: number;
  measurements: MeasurementItem[];
  nominal_mm: number;
  tolerance_mm: number;
  usl: number;
  lsl: number;
  certainty: CertaintyLevel;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface VisualDefectPrediction {
  image_id: string;
  batch_id: string;
  source?: string;
  category?: string;
  defect_detected: boolean;
  anomaly_score?: number;
  defect_type: string;
  raw_class?: string;
  confidence: number;
  location: string;
  bbox?: BoundingBox;
  bounding_box?: BoundingBox;
  severity: string;
  certainty: CertaintyLevel;
  label?: string;
  model_version?: string;
  image_url?: string;
  annotated_image_url?: string;
}

export interface TelemetryDataPoint {
  timestamp: string;
  spindle_speed_rpm: number;
  feed_rate_mmrev: number;
  coolant_temperature_c: number;
  machine_vibration_mms: number;
  tool_usage_cycles: number;
  motor_current_a: number;
  cycle_time_s: number;
  is_anomaly: boolean;
  anomaly_score: number;
  flags: string[];
  certainty: CertaintyLevel;
}

export interface ProcessMonitoringReport {
  batch_id: string;
  machine: string;
  total_data_points: number;
  anomalies_detected: number;
  critical_parameters: string[];
  vibration_current: number;
  vibration_baseline: number;
  vibration_status: string;
  tool_cycles_current: number;
  tool_cycles_baseline: number;
  tool_status: string;
  temperature_current: number;
  temperature_baseline: number;
  drift_detected: boolean;
  certainty: CertaintyLevel;
}

export interface NelsonRuleViolation {
  rule_number: number;
  rule_name: string;
  description: string;
  sample_indices: number[];
  severity: string;
}

export interface SPCReport {
  batch_id: string;
  sample_size: number;
  mean: number;
  std_dev: number;
  ucl: number;
  lcl: number;
  cl: number;
  usl: number;
  lsl: number;
  cp: number;
  cpk: number;
  pp: number;
  ppk: number;
  capability_assessment: string;
  chart_data: Array<{
    sample_index: number;
    sample_id: string;
    value: number;
    ucl: number;
    lcl: number;
    cl: number;
    usl: number;
    lsl: number;
    is_out_of_control: boolean;
    is_out_of_spec: boolean;
  }>;
  nelson_violations: NelsonRuleViolation[];
  distinction_warning: string;
  certainty: CertaintyLevel;
}

export interface HypothesisEvidence {
  hypothesis_id: string;
  title: string;
  description: string;
  category: string;
  confidence_score: number;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  required_confirmation: string;
  status: string;
  certainty: CertaintyLevel;
}

export interface FiveWhysItem {
  level: number;
  question: string;
  answer: string;
  evidence: string;
}

export interface FishboneCategory {
  category: string;
  factors: string[];
}

export interface HistoricalIncident {
  incident_id: string;
  date: string;
  title: string;
  defect_type: string;
  machine: string;
  material: string;
  confirmed_root_cause: string;
  similarity_score: number;
  action_taken: string;
  certainty: CertaintyLevel;
}

export interface RCAReport {
  incident_id: string;
  batch_id: string;
  problem_statement: string;
  ranked_hypotheses: HypothesisEvidence[];
  five_whys: FiveWhysItem[];
  fishbone_diagram: FishboneCategory[];
  historical_matches: HistoricalIncident[];
  correlation_vs_causation_note: string;
  certainty: CertaintyLevel;
}

export interface ActionItem {
  action_id: string;
  type: string;
  description: string;
  assigned_role: string;
  due_date: string;
  status: string;
  evidence_required: string;
  completion_date?: string;
  effectiveness_metric?: string;
}

export interface CAPAReport {
  capa_id: string;
  incident_id: string;
  batch_id: string;
  containment_actions: ActionItem[];
  corrective_actions: ActionItem[];
  preventive_actions: ActionItem[];
  requires_engineer_approval: boolean;
  approval_status: string;
  approver?: string;
  approved_at?: string;
  effectiveness_result?: string;
}

export interface CriticReview {
  verified_spec_references: boolean;
  validated_calculations: boolean;
  cv_predictions_verified: boolean;
  unsupported_causal_claims_detected: boolean;
  review_comments: string[];
  critic_verdict: string;
  certainty: CertaintyLevel;
}

export interface AgentStepLog {
  step_number: number;
  agent_name: string;
  status: string;
  input_summary: string;
  tool_calls: string[];
  output_summary: string;
  certainty_level: CertaintyLevel;
  duration_ms: number;
  timestamp: string;
}

export interface WorkflowState {
  workflow_id: string;
  batch_id: string;
  status: string;
  current_agent?: string;
  execution_trace: AgentStepLog[];
  batch_metadata?: any;
  dimensional_report?: InspectionReport;
  visual_prediction?: VisualDefectPrediction;
  process_report?: ProcessMonitoringReport;
  spc_report?: SPCReport;
  rca_report?: RCAReport;
  capa_report?: CAPAReport;
  critic_review?: CriticReview;
  human_approval?: any;
  has_defects: boolean;
  has_anomalies: boolean;
  has_spc_violations: boolean;
  completed_at?: string;
}

export interface TestScenarioResult {
  test_id: string;
  scenario: string;
  input: string;
  initial_state: string;
  expected_result: string;
  actual_result: string;
  agents_involved: string[];
  ml_model_output: string;
  evidence: string;
  status: "PASS" | "FAIL";
}
