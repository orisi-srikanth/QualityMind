"""
Agent 3: Dimensional & Specification Compliance Agent
Performs deterministic comparison of measured product characteristics against engineering specifications.
Calculates deviations, rejection percentages, and flags specification non-conformances.
"""
import time
from typing import Dict, Any, List
from backend.app.agents.base_agent import BaseQualityAgent
from backend.app.models.schemas import CertaintyLevel, InspectionReport, MeasurementItem

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
        tolerance_mm: float = 0.05
    ) -> Dict[str, Any]:
        start = time.time()
        tool_calls = ["tool_calculate_spec_limits", "tool_deterministic_tolerance_check"]

        usl = round(nominal_mm + tolerance_mm, 4)
        lsl = round(nominal_mm - tolerance_mm, 4)

        evaluated_items: List[MeasurementItem] = []
        accepted_count = 0
        nonconforming_count = 0

        for m in measurements:
            sample_id = m.get("sample_id", "UNK")
            val = float(m.get("measured_value"))
            dev_nominal = round(val - nominal_mm, 4)

            dev_limit = 0.0
            is_conforming = True
            status = "PASS"

            if val > usl:
                is_conforming = False
                dev_limit = round(val - usl, 4)
                status = "FAIL_HIGH"
                nonconforming_count += 1
            elif val < lsl:
                is_conforming = False
                dev_limit = round(lsl - val, 4)
                status = "FAIL_LOW"
                nonconforming_count += 1
            else:
                accepted_count += 1

            evaluated_items.append(
                MeasurementItem(
                    sample_id=sample_id,
                    measured_value=val,
                    deviation_from_nominal=dev_nominal,
                    deviation_from_limit=dev_limit,
                    is_conforming=is_conforming,
                    status=status,
                    certainty=CertaintyLevel.OBSERVED_FACT
                )
            )

        total = len(evaluated_items)
        rejection_pct = round((nonconforming_count / total * 100.0) if total > 0 else 0.0, 2)

        report = InspectionReport(
            batch_id=batch_id,
            total_inspected=total,
            accepted=accepted_count,
            nonconforming=nonconforming_count,
            rejection_rate_percent=rejection_pct,
            measurements=evaluated_items,
            nominal_mm=nominal_mm,
            tolerance_mm=tolerance_mm,
            usl=usl,
            lsl=lsl,
            certainty=CertaintyLevel.OBSERVED_FACT
        )

        duration = int((time.time() - start) * 1000)
        log_entry = self.log_execution(
            step_number=3,
            input_summary=f"Evaluated {total} measurements against USL={usl}mm, LSL={lsl}mm",
            tool_calls=tool_calls,
            output_summary=(
                f"Inspection Results: {nonconforming_count}/{total} nonconforming "
                f"({rejection_pct}% rejection rate). Nonconforming parts exceed USL by up to "
                f"+{max([i.deviation_from_limit for i in evaluated_items if not i.is_conforming] or [0.0]):.3f} mm."
            ),
            duration_ms=duration
        )

        return {
            "report": report,
            "log": log_entry
        }

compliance_agent = DimensionalComplianceAgent()
