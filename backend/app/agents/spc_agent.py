"""
Agent 5: Statistical Process Control (SPC) Agent
Calculates statistical control limits (UCL, CL, LCL), identifies Nelson rule violations,
and computes process capability indices (Cp, Cpk, Pp, Ppk).
Strictly separates Engineering Specification Limits (USL/LSL) from Statistical Control Limits (UCL/LCL).
"""
import time
import numpy as np
from typing import Dict, Any, List
from backend.app.agents.base_agent import BaseQualityAgent
from backend.app.models.schemas import CertaintyLevel, SPCReport, NelsonRuleViolation

class StatisticalProcessControlAgent(BaseQualityAgent):
    def __init__(self):
        super().__init__(
            name="Agent 5 — Statistical Process Control Agent",
            role="Monitor manufacturing-process stability using statistical techniques and capability indices",
            certainty_level=CertaintyLevel.STATISTICAL_FINDING
        )

    def analyze_process_capability_and_control(
        self,
        batch_id: str,
        values: List[float],
        usl: float = 50.05,
        lsl: float = 49.95,
        nominal: float = 50.00
    ) -> Dict[str, Any]:
        start = time.time()
        tool_calls = [
            "tool_compute_moments_mean_sigma",
            "tool_calculate_imr_control_limits",
            "tool_evaluate_nelson_rules",
            "tool_calculate_cp_cpk_indices"
        ]

        data = np.array(values, dtype=float)
        n = len(data)

        mean = float(np.mean(data))
        # Sample standard deviation (Bessel's correction)
        std_dev = float(np.std(data, ddof=1)) if n > 1 else 0.001

        # I-MR (Individuals & Moving Range) moving range sigma estimation
        if n > 1:
            moving_ranges = np.abs(np.diff(data))
            mr_bar = float(np.mean(moving_ranges))
            # d2 constant for sample subgroup of size 2 is 1.128
            sigma_mr = mr_bar / 1.128 if mr_bar > 0 else std_dev
        else:
            sigma_mr = std_dev

        # Statistical Control Limits (3-sigma natural process limits)
        ucl = round(mean + 3.0 * sigma_mr, 4)
        lcl = round(mean - 3.0 * sigma_mr, 4)
        cl = round(mean, 4)

        # Nelson Rules & Western Electric rules detection
        violations: List[NelsonRuleViolation] = []

        # Rule 1: Beyond 3 sigma (outside UCL or LCL)
        rule1_hits = [i for i, x in enumerate(data) if x > ucl or x < lcl]
        if rule1_hits:
            violations.append(
                NelsonRuleViolation(
                    rule_number=1,
                    rule_name="Extreme Point Out of Statistical Control",
                    description=f"{len(rule1_hits)} point(s) exceed 3-sigma statistical control limits [{lcl}, {ucl}].",
                    sample_indices=rule1_hits,
                    severity="Critical"
                )
            )

        # Rule 2: 9 points in a row on one side of center line (shift)
        run_len = 0
        side = None
        for i, x in enumerate(data):
            current_side = "high" if x > cl else "low"
            if current_side == side:
                run_len += 1
            else:
                side = current_side
                run_len = 1
            if run_len >= 9:
                violations.append(
                    NelsonRuleViolation(
                        rule_number=2,
                        rule_name="Process Mean Shift",
                        description="Nine or more consecutive points fall on the same side of the center line.",
                        sample_indices=list(range(max(0, i-8), i+1)),
                        severity="High"
                    )
                )
                break

        # Rule 3: 6 points in a row steadily increasing or decreasing (drift/wear)
        inc_count, dec_count = 1, 1
        drift_hits = []
        for i in range(1, len(data)):
            if data[i] > data[i-1]:
                inc_count += 1
                dec_count = 1
            elif data[i] < data[i-1]:
                dec_count += 1
                inc_count = 1
            else:
                inc_count = 1
                dec_count = 1

            if inc_count >= 6:
                drift_hits = list(range(i - 5, i + 1))
                violations.append(
                    NelsonRuleViolation(
                        rule_number=3,
                        rule_name="Continuous Upward Trend / Tool Wear Drift",
                        description="Six consecutive points steadily increasing, indicating progressive tool wear or thermal drift.",
                        sample_indices=drift_hits,
                        severity="High"
                    )
                )
                break

        # Calculate Capability Indices (Cp, Cpk, Pp, Ppk)
        # Cp = (USL - LSL) / (6 * sigma_within)
        spec_width = usl - lsl
        cp = round(spec_width / (6.0 * sigma_mr), 3) if sigma_mr > 0 else 0.0

        cpu = (usl - mean) / (3.0 * sigma_mr) if sigma_mr > 0 else 0.0
        cpl = (mean - lsl) / (3.0 * sigma_mr) if sigma_mr > 0 else 0.0
        cpk = round(min(cpu, cpl), 3)

        # Performance indices (overall variation)
        pp = round(spec_width / (6.0 * std_dev), 3) if std_dev > 0 else 0.0
        ppu = (usl - mean) / (3.0 * std_dev) if std_dev > 0 else 0.0
        ppl = (mean - lsl) / (3.0 * std_dev) if std_dev > 0 else 0.0
        ppk = round(min(ppu, ppl), 3)

        if cpk >= 1.33:
            cap_assessment = "Capable & Centered Process (Meets Automotive IATF Standards)"
        elif cpk >= 1.00:
            cap_assessment = "Marginally Capable Process (Requires Tight Process Supervision)"
        else:
            cap_assessment = "Incapable Process (High Defect Risk — Cpk < 1.0 indicates spec violations)"

        # Prepare rich chart data series
        chart_data = []
        for i, val in enumerate(data):
            val_f = float(round(float(val), 4))
            chart_data.append({
                "sample_index": i + 1,
                "sample_id": f"P{i+1:03d}",
                "value": val_f,
                "ucl": float(ucl),
                "lcl": float(lcl),
                "cl": float(cl),
                "usl": float(usl),
                "lsl": float(lsl),
                "is_out_of_control": bool(val_f > ucl or val_f < lcl),
                "is_out_of_spec": bool(val_f > usl or val_f < lsl)
            })

        warning_note = ""
        if n < 30:
            warning_note = f"SAMPLE SIZE WARNING: Only n={n} observations available. Standard SPC requires n>=30 for robust Cpk capability estimation."

        report = SPCReport(
            batch_id=batch_id,
            sample_size=n,
            mean=round(mean, 4),
            std_dev=round(std_dev, 4),
            ucl=ucl,
            lcl=lcl,
            cl=cl,
            usl=usl,
            lsl=lsl,
            cp=cp,
            cpk=cpk,
            pp=pp,
            ppk=ppk,
            capability_assessment=cap_assessment,
            chart_data=chart_data,
            nelson_violations=violations,
            distinction_warning=(
                f"{warning_note} | SPECIFICATION LIMITS (USL={usl}, LSL={lsl}) represent engineering design tolerance. "
                f"STATISTICAL CONTROL LIMITS (UCL={ucl}, LCL={lcl}) represent actual 3-sigma manufacturing capability."
            ),
            certainty=CertaintyLevel.STATISTICAL_FINDING
        )

        duration = int((time.time() - start) * 1000)
        log_entry = self.log_execution(
            step_number=5,
            input_summary=f"Evaluated SPC for n={n} points against USL={usl}, LSL={lsl}",
            tool_calls=tool_calls,
            output_summary=(
                f"SPC Findings: Mean={mean:.4f}mm, StdDev={std_dev:.4f}mm, UCL={ucl}mm, LCL={lcl}mm. "
                f"Cp={cp}, Cpk={cpk}. {len(violations)} Nelson Rule violations detected."
            ),
            duration_ms=duration
        )

        return {
            "report": report,
            "log": log_entry
        }

spc_agent = StatisticalProcessControlAgent()
