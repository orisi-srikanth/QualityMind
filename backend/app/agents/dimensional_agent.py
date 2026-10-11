"""
Agent 3: Dimensional & Specification Compliance Agent
Performs 100% deterministic comparison of measured product characteristics against engineering specifications.
Calculates deviations, rejection percentages, and flags specification non-conformances.
Uses SpecificationEngine (Decimal/NumPy). Zero LLM involvement in arithmetic or conformance decisions.
"""
import time
from typing import Dict, Any, List, Optional
from backend.app.agents.base_agent import BaseQualityAgent
from backend.app.models.schemas import CertaintyLevel, InspectionReport, MeasurementItem
from backend.app.services.spec_check import SpecificationEngine


class DimensionalComplianceAgent(BaseQualityAgent):
    def __init__(self):
        super().__init__(
            name="Agent 3 — Dimensional & Specification Compliance Agent",
            role="Compare measured product characteristics against engineering specifications",
            certainty_level=CertaintyLevel.OBSERVED_FACT
        )

    def evaluate_compliance(
        self,
        batch_id: str,
        measurements: List[Dict[str, Any]],
        nominal_mm: float = 50.00,
        tolerance_mm: float = 0.05,
        tol_plus: Optional[float] = None,
        tol_minus: Optional[float] = None,
        usl: Optional[float] = None,
        lsl: Optional[float] = None,
        parameter_name: str = "shaft_diameter"
    ) -> Dict[str, Any]:
        start = time.time()
        tool_calls = ["tool_calculate_spec_limits", "tool_deterministic_tolerance_check"]

        eff_plus = tol_plus if tol_plus is not None else tolerance_mm
        eff_minus = tol_minus if tol_minus is not None else tolerance_mm

        # Pure deterministic evaluation via SpecificationEngine
        spec_result = SpecificationEngine.evaluate_compliance(
            batch_id=batch_id,
            nominal_mm=nominal_mm,
            tol_plus=eff_plus,
            tol_minus=eff_minus,
            measurements=measurements,
            parameter_name=parameter_name,
            usl=usl,
            lsl=lsl
        )

        evaluated_items: List[MeasurementItem] = []
        for item in spec_result["measurements"]:
            evaluated_items.append(
                MeasurementItem(
                    sample_id=item["sample_id"],
                    measured_value=item["measured_value"],
                    deviation_from_nominal=item["deviation_from_nominal"],
                    deviation_from_limit=item["deviation_from_limit"],
                    is_conforming=item["is_conforming"],
                    status=item["status"],
                    certainty=CertaintyLevel.OBSERVED_FACT
                )
            )

        eff_usl = spec_result["usl"] if spec_result["usl"] is not None else round(nominal_mm + eff_plus, 4)
        eff_lsl = spec_result["lsl"] if spec_result["lsl"] is not None else round(nominal_mm - eff_minus, 4)

        report = InspectionReport(
            batch_id=batch_id,
            total_inspected=spec_result["total_inspected"],
            accepted=spec_result["accepted"],
            nonconforming=spec_result["nonconforming"],
            rejection_rate_percent=spec_result["rejection_rate_percent"],
            measurements=evaluated_items,
            nominal_mm=nominal_mm,
            tolerance_mm=eff_plus,
            usl=eff_usl,
            lsl=eff_lsl,
            certainty=CertaintyLevel.OBSERVED_FACT
        )

        duration = int((time.time() - start) * 1000)
        max_dev = spec_result["max_deviation_from_limit"]
        log_entry = self.log_execution(
            step_number=3,
            input_summary=f"Evaluated {spec_result['total_inspected']} measurements against USL={eff_usl}mm, LSL={eff_lsl}mm",
            tool_calls=tool_calls,
            output_summary=(
                f"Inspection Results: {spec_result['nonconforming']}/{spec_result['total_inspected']} nonconforming "
                f"({spec_result['rejection_rate_percent']}% rejection rate). Max deviation: +{max_dev:.4f} mm."
            ),
            duration_ms=duration
        )

        return {
            "report": report,
            "spec_data": spec_result,
            "log": log_entry
        }

compliance_agent = DimensionalComplianceAgent()
dimensional_agent = compliance_agent
ComplianceAgent = DimensionalComplianceAgent
DimensionalAgent = DimensionalComplianceAgent

__all__ = [
    "DimensionalComplianceAgent",
    "ComplianceAgent",
    "DimensionalAgent",
    "compliance_agent",
    "dimensional_agent",
]
