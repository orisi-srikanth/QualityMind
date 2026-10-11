"""
Multi-Agent Orchestration Engine & Workflow Execution Graph
Orchestrates Agent 1 through Agent 8, manages state transitions, and records complete execution visibility.
"""
import uuid
import time
from typing import Dict, Any, Optional, List
from backend.app.orchestrator.state import WorkflowState
from backend.app.agents.intake_agent import data_intake_agent
from backend.app.agents.visual_agent import vision_agent
from backend.app.agents.dimensional_agent import compliance_agent
from backend.app.agents.process_agent import anomaly_agent
from backend.app.agents.spc_agent import spc_agent
from backend.app.agents.rca_agent import rca_agent
from backend.app.agents.capa_agent import capa_agent
from backend.app.agents.reviewer_agent import critic_agent

class QualityWorkflowOrchestrator:
    def __init__(self):
        self.active_workflows: Dict[str, WorkflowState] = {}

    def run_full_pipeline(
        self,
        batch_meta: Dict[str, Any],
        measurements: Optional[List[Dict[str, Any]]] = None,
        image_path: Optional[str] = None,
        telemetry_records: Optional[List[Dict[str, Any]]] = None,
        workflow_id: Optional[str] = None
    ) -> WorkflowState:
        w_id = workflow_id or f"WF-{uuid.uuid4().hex[:8].upper()}"
        batch_id = batch_meta.get("batch_id", "BATCH-0245")

        state = WorkflowState(
            workflow_id=w_id,
            batch_id=batch_id,
            status="RUNNING"
        )
        self.active_workflows[w_id] = state

        # STEP 1: Agent 1 - Data Intake
        state.current_agent = data_intake_agent.name
        intake_res = data_intake_agent.process_batch_and_measurements(
            batch_meta=batch_meta,
            raw_measurements=measurements
        )
        state.batch_metadata = intake_res["batch_data"]
        state.execution_trace.append(intake_res["log"])

        # STEP 2: Agent 2 - Visual Inspection (if image available)
        if image_path:
            state.current_agent = vision_agent.name
            vision_res = vision_agent.inspect(
                image_path=image_path,
                batch_id=batch_id,
                image_id=f"IMG-{batch_id}"
            )
            state.visual_prediction = vision_res["prediction"]
            state.execution_trace.append(vision_res["log"])
            if state.visual_prediction.defect_detected:
                state.has_defects = True
        else:
            vision_res = None

        # STEP 3: Agent 3 - Dimensional & Specification Compliance
        state.current_agent = compliance_agent.name
        parsed_meas = state.batch_metadata.get("measurements", [])
        nom = state.batch_metadata.get("nominal_mm", 50.0)
        tol = state.batch_metadata.get("tolerance_mm", 0.05)

        comp_res = compliance_agent.evaluate_compliance(
            batch_id=batch_id,
            measurements=parsed_meas,
            nominal_mm=nom,
            tolerance_mm=tol
        )
        state.dimensional_report = comp_res["report"]
        state.execution_trace.append(comp_res["log"])
        if state.dimensional_report.nonconforming > 0:
            state.has_defects = True

        # STEP 4: Agent 4 - Process Monitoring & Anomaly Detection
        state.current_agent = anomaly_agent.name
        anomaly_res = anomaly_agent.analyze_telemetry_series(
            batch_id=batch_id,
            machine=state.batch_metadata.get("machine", "CNC-04"),
            telemetry_records=telemetry_records
        )
        state.process_report = anomaly_res["report"]
        state.execution_trace.append(anomaly_res["log"])
        if state.process_report.anomalies_detected > 0:
            state.has_anomalies = True

        # STEP 5: Agent 5 - Statistical Process Control (SPC)
        state.current_agent = spc_agent.name
        raw_vals = [m["measured_value"] for m in parsed_meas]
        spc_res = spc_agent.analyze_process_capability_and_control(
            batch_id=batch_id,
            values=raw_vals,
            usl=state.batch_metadata.get("usl", 50.05),
            lsl=state.batch_metadata.get("lsl", 49.95),
            nominal=nom
        )
        state.spc_report = spc_res["report"]
        state.execution_trace.append(spc_res["log"])
        if len(state.spc_report.nelson_violations) > 0 or state.spc_report.cpk < 1.0:
            state.has_spc_violations = True

        # STEP 6: Agent 6 - Root Cause Analysis (RCA)
        state.current_agent = rca_agent.name
        max_val = max(raw_vals) if raw_vals else 50.08
        rca_res = rca_agent.analyze_incident(
            incident_id=f"INC-{batch_id}",
            batch_id=batch_id,
            defect_type="Oversized shaft diameter",
            max_measured_val=max_val,
            usl=state.batch_metadata.get("usl", 50.05),
            vibration_val=state.process_report.vibration_current,
            tool_cycles=state.process_report.tool_cycles_current
        )
        state.rca_report = rca_res["report"]
        state.execution_trace.append(rca_res["log"])

        # STEP 7: Agent 7 - Corrective & Preventive Action (CAPA)
        state.current_agent = capa_agent.name
        capa_res = capa_agent.generate_capa_plan(
            incident_id=f"INC-{batch_id}",
            batch_id=batch_id,
            machine=state.batch_metadata.get("machine", "CNC-04")
        )
        state.capa_report = capa_res["capa"]
        state.execution_trace.append(capa_res["log"])

        # STEP 8: Agent 8 - Quality Reviewer / Critic
        state.current_agent = critic_agent.name
        critic_res = critic_agent.review_workflow(
            intake_data=intake_res,
            compliance_data=comp_res,
            vision_data=vision_res,
            anomaly_data=anomaly_res,
            spc_data=spc_res,
            rca_data=rca_res,
            capa_data=capa_res
        )
        state.critic_review = critic_res["review"]
        state.execution_trace.append(critic_res["log"])

        # Completion & Transition to Human Approval
        state.status = "PENDING_HUMAN_APPROVAL"
        state.current_agent = "Human Quality Engineer (Gatekeeper)"
        state.completed_at = time.strftime("%Y-%m-%d %H:%M:%S")

        self.active_workflows[w_id] = state
        return state

    def run_langgraph_pipeline(
        self,
        batch_meta: Dict[str, Any],
        measurements: Optional[List[Dict[str, Any]]] = None,
        image_path: Optional[str] = None,
        telemetry_records: Optional[List[Dict[str, Any]]] = None,
        workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Executes full multi-agent orchestration via compiled LangGraph StateGraph with checkpointing."""
        from backend.app.orchestrator.langgraph_orchestration import qualitymind_langgraph
        w_id = workflow_id or f"WF-LG-{uuid.uuid4().hex[:8].upper()}"
        batch_id = batch_meta.get("batch_id", "BATCH-0245")

        init_state = {
            "workflow_id": w_id,
            "batch_id": batch_id,
            "batch_metadata": batch_meta,
            "measurements": measurements or [],
            "image_path": image_path,
            "telemetry_records": telemetry_records,
            "execution_trace": [],
            "has_defects": False,
            "has_anomalies": False,
            "reassessment_loops": 0
        }

        result_state = qualitymind_langgraph.invoke(
            init_state,
            config={"configurable": {"thread_id": w_id}}
        )
        return result_state

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
        return self.active_workflows.get(workflow_id)

orchestrator = QualityWorkflowOrchestrator()
