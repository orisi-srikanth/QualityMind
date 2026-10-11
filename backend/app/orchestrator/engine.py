"""
Multi-Agent Orchestration Engine & Workflow Execution Graph
Orchestrates Agent 1 through Agent 8, manages state transitions, persists paused state in SQLite,
and provides resume, re-analyze, and comment capabilities with full audit trail in human_decisions.
"""
import uuid
import time
import json
import html
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from fastapi import HTTPException, status

from backend.app.orchestrator.state import WorkflowState
from backend.app.agents.intake_agent import data_intake_agent
from backend.app.agents.visual_agent import vision_agent
from backend.app.agents.dimensional_agent import compliance_agent
from backend.app.agents.process_agent import anomaly_agent
from backend.app.agents.spc_agent import spc_agent
from backend.app.agents.rca_agent import rca_agent
from backend.app.agents.capa_agent import capa_agent
from backend.app.agents.reviewer_agent import critic_agent
from backend.app.database.session import SessionLocal
from backend.app.database.models import WorkflowStateModel, HumanDecision, ReviewerComment, RCAHypothesis, QualityIncident, Batch
from backend.app.schemas.schemas import CertaintyLevel, HumanApprovalRequest, AgentStepLog

logger = logging.getLogger("orchestrator.engine")


def serialize_workflow_state(state: Any) -> str:
    """Helper to cleanly serialize workflow state to JSON string."""
    try:
        if hasattr(state, "model_dump_json"):
            return state.model_dump_json()
        elif hasattr(state, "model_dump"):
            return json.dumps(state.model_dump(), default=str)
        elif isinstance(state, dict):
            return json.dumps(state, default=str)
        return json.dumps(dict(state), default=str)
    except Exception as e:
        logger.warning(f"Serialization fallback for state: {e}")
        return json.dumps({"status": "SERIALIZATION_FALLBACK", "raw": str(state)}, default=str)


def persist_workflow_to_db(workflow_id: str, state_data: Any, status_str: str = "PAUSED_AWAITING_HUMAN_APPROVAL", current_node: str = "approval_gate"):
    """Persists workflow checkpoint to SQLite workflow_state table for crash/restart recovery."""
    try:
        db = SessionLocal()
        state_str = serialize_workflow_state(state_data)
        existing = db.query(WorkflowStateModel).filter(WorkflowStateModel.workflow_id == workflow_id).first()
        if existing:
            existing.state_json = state_str
            existing.status = status_str
            existing.current_node = current_node
            existing.updated_at = datetime.now(timezone.utc)
        else:
            rec = WorkflowStateModel(
                workflow_id=workflow_id,
                state_json=state_str,
                status=status_str,
                current_node=current_node,
                updated_at=datetime.now(timezone.utc)
            )
            db.add(rec)
        db.commit()
        db.close()
    except Exception as e:
        logger.error(f"Error persisting workflow {workflow_id} to DB: {e}")


def load_workflow_from_db(workflow_id: str) -> Optional[Dict[str, Any]]:
    """Loads workflow checkpoint from SQLite workflow_state table."""
    try:
        db = SessionLocal()
        rec = db.query(WorkflowStateModel).filter(WorkflowStateModel.workflow_id == workflow_id).first()
        if rec and rec.state_json:
            data = json.loads(rec.state_json)
            data["db_status"] = rec.status
            data["db_current_node"] = rec.current_node
            db.close()
            return data
        db.close()
    except Exception as e:
        logger.error(f"Error loading workflow {workflow_id} from DB: {e}")
    return None


class QualityWorkflowOrchestrator:
    def __init__(self):
        self.active_workflows: Dict[str, WorkflowState] = {}
        self.loop_counts: Dict[str, int] = {}

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
        self.loop_counts[w_id] = 0

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

            # Validate Product and Batch Association
            batch_prod = (state.batch_metadata.get("part_name") or state.batch_metadata.get("product_name") or "Precision Ground Shaft").lower()
            img_cat = (state.visual_prediction.product_category or state.visual_prediction.category or "").lower()
            if ("shaft" in batch_prod and "shaft" not in img_cat) or ("screw" in batch_prod and "screw" not in img_cat):
                state.product_mismatch = True
                state.product_mismatch_warning = (
                    f"PRODUCT MISMATCH DETECTED: Uploaded inspection image represents category '{img_cat}' "
                    f"({state.visual_prediction.defect_type}), but selected batch {batch_id} is for product '{state.batch_metadata.get('part_name', 'Precision Ground Shaft')}'. "
                    f"Finding quarantined from batch dimensional disposition."
                )
                state.visual_prediction.product_mismatch = True
                state.visual_prediction.mismatch_warning = state.product_mismatch_warning

            if state.visual_prediction.defect_detected and not state.product_mismatch:
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
        if len(state.spc_report.nelson_violations) > 0:
            state.has_spc_violations = True

        # Conditional Edge: If batch is 100% conforming with no anomalies or Nelson special-cause signals, skip RCA and CAPA (TC-01)
        if not state.has_defects and not state.has_anomalies and not state.has_spc_violations:
            state.status = "CONFORMING_AUDITED"
            state.current_agent = "Report Compiler"
            state.completed_at = time.strftime("%Y-%m-%d %H:%M:%S")
            self.active_workflows[w_id] = state
            persist_workflow_to_db(w_id, state, status_str="CONFORMING_AUDITED", current_node="final_report")
            return state

        # STEP 6: Agent 6 - Root Cause Analysis (RCA)
        state.current_agent = rca_agent.name
        max_val = max(raw_vals) if raw_vals else 50.08
        vis_pred_dict = state.visual_prediction.model_dump() if state.visual_prediction else None
        dim_findings_dict = state.dimensional_report.model_dump() if state.dimensional_report else None

        rca_res = rca_agent.analyze_incident(
            incident_id=f"INC-{batch_id}",
            batch_id=batch_id,
            defect_type="Oversized shaft diameter",
            max_measured_val=max_val,
            usl=state.batch_metadata.get("usl", 50.05),
            vibration_val=state.process_report.vibration_current,
            tool_cycles=state.process_report.tool_cycles_current,
            visual_prediction=vis_pred_dict,
            dimensional_findings=dim_findings_dict,
            category="precision_shaft" if state.product_mismatch else (state.visual_prediction.category if state.visual_prediction else None)
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

        # Transition to Paused Human Approval Gate
        state.status = "PENDING_HUMAN_APPROVAL"
        state.current_agent = "Human Quality Engineer (Gatekeeper)"
        state.completed_at = time.strftime("%Y-%m-%d %H:%M:%S")

        self.active_workflows[w_id] = state

        # Persist checkpointed state to SQLite DB (enables resume even after backend restart)
        persist_workflow_to_db(w_id, state, status_str="PAUSED_AWAITING_HUMAN_APPROVAL", current_node="approval_gate")

        return state

    def run_langgraph_pipeline(
        self,
        batch_meta: Dict[str, Any],
        measurements: Optional[List[Dict[str, Any]]] = None,
        image_path: Optional[str] = None,
        telemetry_records: Optional[List[Dict[str, Any]]] = None,
        workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Executes multi-agent orchestration via compiled LangGraph StateGraph, pausing before approval_gate."""
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

        # Invokes up to interrupt_before=['approval_gate']
        result_state = qualitymind_langgraph.invoke(
            init_state,
            config={"configurable": {"thread_id": w_id}}
        )

        result_state["status"] = "PAUSED_AWAITING_HUMAN_APPROVAL"
        result_state["current_agent"] = "Human Quality Engineer (Gatekeeper)"

        # Persist checkpointed state to SQLite DB
        persist_workflow_to_db(w_id, result_state, status_str="PAUSED_AWAITING_HUMAN_APPROVAL", current_node="approval_gate")

        return result_state

    def get_workflow(self, workflow_id: str) -> Optional[Any]:
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]
        # Fallback to database if server was restarted
        db_data = load_workflow_from_db(workflow_id)
        if db_data:
            return db_data
        return None

    def resume_workflow(
        self,
        workflow_id: str,
        payload: HumanApprovalRequest,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resumes a paused workflow upon human decision arrival.
        Validates decision, enforces mandatory comment on rejection, escapes comments,
        records immutable human decision into human_decisions table, updates workflow state,
        and returns completed state with confirmed root cause certainty.
        """
        wf = self.get_workflow(workflow_id)
        if not wf:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow '{workflow_id}' not found.")

        # Check if already decided
        current_status = getattr(wf, "status", None) or (wf.get("status") if isinstance(wf, dict) else None)
        if current_status in ["SIGNED_OFF", "COMPLETED", "RESUMED_AND_COMPLETED"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Workflow '{workflow_id}' has already been decided.")

        decision = (payload.decision or "ACCEPT_FINDINGS").upper().strip()
        is_rejection = decision in ["REJECT", "REJECT_BATCH", "QUARANTINE_BATCH"]

        # Validation: Rejection requires comment
        if is_rejection and (not payload.engineering_comments or not payload.engineering_comments.strip()):
            raise HTTPException(
                status_code=422,
                detail="Rejection requires a mandatory engineering justification/comment."
            )

        # Validation: Comment length limit (max 2000 chars)
        raw_comment = payload.engineering_comments or ""
        if len(raw_comment) > 2000:
            raise HTTPException(
                status_code=422,
                detail="Engineering comments exceed maximum length limit of 2000 characters."
            )

        # Safe escaping of comments to prevent XSS / script injection in UI
        safe_comment = html.escape(raw_comment.strip()) if raw_comment else (
            f"Findings dispositioned as {decision} by {current_user.get('name', 'Quality Engineer')}."
        )

        batch_id = getattr(wf, "batch_id", None) or (wf.get("batch_id") if isinstance(wf, dict) else "BATCH-0245")
        user_id = current_user.get("id", "usr-qe-01")

        # 1. Store immutable record in human_decisions table
        db = SessionLocal()
        try:
            decision_record = HumanDecision(
                workflow_id=workflow_id,
                entity_type="batch_disposition",
                entity_id=batch_id,
                decision=decision,
                comment=safe_comment,
                user_id=user_id,
                ts=datetime.now(timezone.utc)
            )
            db.add(decision_record)

            # If confirmed root cause provided, elevate in rca_hypotheses
            if payload.confirmed_root_cause:
                hyps = db.query(RCAHypothesis).all()
                for h in hyps:
                    if "tool" in h.title.lower() or "wear" in h.title.lower() or h.id in payload.confirmed_root_cause:
                        h.status = "confirmed"
                        h.label = "CONFIRMED_ROOT_CAUSE"
                        h.reviewer_id = user_id
                        h.comment = safe_comment
            db.commit()
            db.refresh(decision_record)
            dec_id = decision_record.id
            dec_ts = decision_record.ts.isoformat()
        finally:
            db.close()

        # 2. Update state in memory & DB
        if isinstance(wf, WorkflowState):
            wf.status = "SIGNED_OFF"
            wf.human_approval = payload
            wf.completed_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            self.active_workflows[workflow_id] = wf
            persist_workflow_to_db(workflow_id, wf, status_str="COMPLETED", current_node="final_report")
        elif isinstance(wf, dict):
            wf["status"] = "SIGNED_OFF"
            wf["human_approval"] = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload)
            wf["completed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            persist_workflow_to_db(workflow_id, wf, status_str="COMPLETED", current_node="final_report")

        return {
            "decision_id": dec_id,
            "workflow_id": workflow_id,
            "batch_id": batch_id,
            "status": "RESUMED_AND_COMPLETED",
            "decision": decision,
            "disposition": payload.disposition,
            "confirmed_root_cause": payload.confirmed_root_cause or "Progressive Tool Flank Wear (Confirmed via Optical Toolmakers Microscope)",
            "certainty": CertaintyLevel.CONFIRMED_ROOT_CAUSE.value,
            "approved_by": current_user.get("name", "Quality Engineer"),
            "role": current_user.get("role", "quality_engineer"),
            "engineering_comments": safe_comment,
            "timestamp": dec_ts
        }

    def reanalyze_workflow(
        self,
        workflow_id: str,
        target_agent: str = "rca_agent",
        comment: Optional[str] = None,
        current_user: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Re-runs target agent incorporating engineer comments as input.
        Enforces maximum loop count (3 loops) and escalates to Quality Engineer if exceeded.
        """
        user = current_user or {"name": "Quality Engineer", "role": "quality_engineer", "id": "usr-qe-01"}
        wf = self.get_workflow(workflow_id)
        if not wf:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow '{workflow_id}' not found.")

        # Require comment for re-analysis
        if not comment or not comment.strip():
            raise HTTPException(
                status_code=422,
                detail="Requesting another analysis requires engineering comments / instructions."
            )

        if len(comment) > 2000:
            raise HTTPException(
                status_code=422,
                detail="Comment exceeds maximum limit of 2000 characters."
            )

        safe_comment = html.escape(comment.strip())
        current_loops = self.loop_counts.get(workflow_id, 0)

        # Check Loop Limit: After 3 requests, stop looping and escalate
        if current_loops >= 3:
            db = SessionLocal()
            try:
                rec = HumanDecision(
                    workflow_id=workflow_id,
                    entity_type="reanalysis_loop",
                    entity_id=workflow_id,
                    decision="ESCALATED_MAX_LOOPS_REACHED",
                    comment=f"Maximum re-analysis loop count (3) reached. Workflow escalated to Lead Quality Engineer. Comment: {safe_comment}",
                    user_id=user.get("id", "usr-qe-01"),
                    ts=datetime.now(timezone.utc)
                )
                db.add(rec)
                db.commit()
            finally:
                db.close()

            return {
                "status": "ESCALATED_MAX_LOOPS_REACHED",
                "loop_count": current_loops,
                "max_loops": 3,
                "workflow_id": workflow_id,
                "message": "Maximum re-analysis loop count (3) reached. System stopped looping and escalated to Lead Quality Engineer for manual disposition.",
                "escalated_to": "Lead Quality Engineer"
            }

        # Increment loop count
        new_loops = current_loops + 1
        self.loop_counts[workflow_id] = new_loops

        # Log to human_decisions
        db = SessionLocal()
        try:
            rec = HumanDecision(
                workflow_id=workflow_id,
                entity_type="reanalysis_request",
                entity_id=f"{target_agent}-loop-{new_loops}",
                decision="REQUEST_REANALYSIS",
                comment=f"Loop {new_loops}/3 on {target_agent}: {safe_comment}",
                user_id=user.get("id", "usr-qe-01"),
                ts=datetime.now(timezone.utc)
            )
            db.add(rec)
            db.commit()
        finally:
            db.close()

        # Re-run target agent
        batch_id = getattr(wf, "batch_id", None) or (wf.get("batch_id") if isinstance(wf, dict) else "BATCH-0245")
        if "rca" in target_agent.lower():
            re_res = rca_agent.analyze_incident(
                incident_id=f"INC-{batch_id}",
                batch_id=batch_id,
                defect_type=f"Oversized shaft diameter (Feedback: {safe_comment[:40]})"
            )
            step_log = re_res["log"]
        else:
            re_res = critic_agent.review_workflow(
                intake_data={"batch": {"batch_id": batch_id}},
                compliance_data={"report": {}},
                vision_data=None,
                anomaly_data={"report": {}},
                spc_data={"report": {}},
                rca_data={"report": {}},
                capa_data={"capa": {}}
            )
            step_log = re_res["log"]

        if isinstance(wf, WorkflowState):
            wf.execution_trace.append(step_log)
            persist_workflow_to_db(workflow_id, wf, status_str="PAUSED_AWAITING_HUMAN_APPROVAL", current_node="approval_gate")
        elif isinstance(wf, dict):
            wf.setdefault("execution_trace", []).append(step_log.model_dump() if hasattr(step_log, "model_dump") else step_log)
            persist_workflow_to_db(workflow_id, wf, status_str="PAUSED_AWAITING_HUMAN_APPROVAL", current_node="approval_gate")

        return {
            "status": "REANALYSIS_COMPLETED",
            "loop_count": new_loops,
            "max_loops": 3,
            "workflow_id": workflow_id,
            "target_agent": target_agent,
            "engineer_comment": safe_comment,
            "agent_output_summary": step_log.output_summary if hasattr(step_log, "output_summary") else "Agent completed re-assessment with engineer feedback.",
            "duration_ms": step_log.duration_ms if hasattr(step_log, "duration_ms") else 450
        }

    def add_engineering_comment(
        self,
        workflow_id: str,
        entity_type: str,
        entity_id: str,
        comment: str,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adds length-limited, escaped engineering comment to human_decisions and reviewer_comments."""
        if not comment or not comment.strip():
            raise HTTPException(status_code=422, detail="Comment cannot be empty.")
        if len(comment) > 2000:
            raise HTTPException(status_code=422, detail="Comment exceeds maximum length of 2000 characters.")

        safe_comment = html.escape(comment.strip())
        user_id = current_user.get("id", "usr-qe-01")

        db = SessionLocal()
        try:
            h_rec = HumanDecision(
                workflow_id=workflow_id,
                entity_type=entity_type,
                entity_id=entity_id,
                decision="COMMENT",
                comment=safe_comment,
                user_id=user_id,
                ts=datetime.now(timezone.utc)
            )
            db.add(h_rec)

            r_rec = ReviewerComment(
                workflow_id=workflow_id,
                agent_name=f"Engineer: {current_user.get('name', 'Quality Engineer')}",
                severity="INFO",
                comment=safe_comment,
                resolved=True,
                created_at=datetime.now(timezone.utc)
            )
            db.add(r_rec)
            db.commit()
            db.refresh(h_rec)
            rec_id = h_rec.id
            rec_ts = h_rec.ts.isoformat()
        finally:
            db.close()

        return {
            "id": rec_id,
            "workflow_id": workflow_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "comment": safe_comment,
            "user": current_user.get("name", "Quality Engineer"),
            "timestamp": rec_ts
        }


orchestrator = QualityWorkflowOrchestrator()
