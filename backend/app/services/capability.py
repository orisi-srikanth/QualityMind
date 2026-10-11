"""
Process Capability & Performance Engine (Cp, Cpk, Pp, Ppk)
Strictly adheres to AIAG SPC guidelines with mandatory sample size guardrails.
Refuses computation when n < 5 and issues strong warnings when n < 30.
"""
from typing import List, Dict, Any, Optional
import numpy as np
from scipy import stats
from backend.app.core.guardrails import EpistemicLabel

class ProcessCapabilityEngine:
    """Computes short-term capability (Cp/Cpk) and long-term performance (Pp/Ppk)."""

    @staticmethod
    def calculate_capability(
        values: List[float],
        usl: float,
        lsl: float,
        target: Optional[float] = None,
        is_in_control: bool = True
    ) -> Dict[str, Any]:
        """
        Calculates Cp, Cpk, Pp, Ppk with normality verification and sample size guardrails.
        """
        n = len(values)
        vals = np.array(values, dtype=float)

        # Guardrail 1: Refuse computation if n < 5
        if n < 5:
            return {
                "status": "INSUFFICIENT_DATA",
                "sample_size": n,
                "message": f"Sample size n={n} is insufficient to calculate process capability (minimum n >= 5 required).",
                "cp": None,
                "cpk": None,
                "pp": None,
                "ppk": None,
                "warnings": ["CRITICAL: Subgroup size too small for statistical estimation (n < 5)."],
                "assessment": "Insufficient Data for Capability Assessment",
                "label": EpistemicLabel.STATISTICAL_FINDING.value
            }

        warnings = []

        # Guardrail 2: Hard warning if n < 30
        if n < 30:
            warnings.append(
                f"Preliminary estimate: n={n} is less than the recommended AIAG guideline (n >= 30). "
                f"Capability indices have wide confidence intervals and require ongoing production data."
            )

        # Zero variance check
        var_sample = float(np.var(vals, ddof=1))
        if var_sample <= 1e-9:
            return {
                "status": "ZERO_VARIANCE",
                "sample_size": n,
                "message": "Zero variance detected in sample readings.",
                "cp": None,
                "cpk": None,
                "pp": None,
                "ppk": None,
                "warnings": ["Sample exhibits zero variance. Cannot compute capability ratio."],
                "assessment": "Zero Variance",
                "label": EpistemicLabel.STATISTICAL_FINDING.value
            }

        mean_val = float(np.mean(vals))
        s_overall = float(np.std(vals, ddof=1))  # Overall standard deviation

        # Short-term within-subgroup variation (using Moving Range for individuals)
        moving_ranges = np.abs(np.diff(vals))
        mr_bar = float(np.mean(moving_ranges)) if len(moving_ranges) > 0 else s_overall
        sigma_within = mr_bar / 1.128 if mr_bar > 0 else s_overall

        tolerance = usl - lsl

        # Guardrail 3: Process not in statistical control
        if not is_in_control:
            warnings.append(
                "Process exhibits special-cause out-of-control conditions (Nelson rules triggered). "
                "Capability indices (Cp/Cpk) assume statistical stability and are therefore unreliable."
            )

        # Guardrail 4: Normality test (Shapiro-Wilk)
        is_normal = True
        normality_p_value = 1.0
        if n >= 8:
            try:
                stat, p_val = stats.shapiro(vals)
                normality_p_value = round(float(p_val), 4)
                if p_val < 0.05:
                    is_normal = False
                    warnings.append(
                        f"Normality assumption rejected (Shapiro-Wilk p={normality_p_value:.4f} < 0.05). "
                        f"Standard capability equations may overestimate true yield."
                    )
            except Exception:
                pass

        # Capability Indices: Cp & Cpk (using sigma_within)
        cp = round(tolerance / (6.0 * sigma_within), 4) if sigma_within > 0 else 0.0
        cpu = (usl - mean_val) / (3.0 * sigma_within) if sigma_within > 0 else 0.0
        cpl = (mean_val - lsl) / (3.0 * sigma_within) if sigma_within > 0 else 0.0
        cpk = round(float(min(cpu, cpl)), 4)

        # Performance Indices: Pp & Ppk (using s_overall)
        pp = round(tolerance / (6.0 * s_overall), 4) if s_overall > 0 else 0.0
        ppu = (usl - mean_val) / (3.0 * s_overall) if s_overall > 0 else 0.0
        ppl = (mean_val - lsl) / (3.0 * s_overall) if s_overall > 0 else 0.0
        ppk = round(float(min(ppu, ppl)), 4)

        # Interpretation band guidance
        if cpk < 1.00:
            assessment = "Not Capable (High risk of nonconformance, Cpk < 1.00)"
        elif cpk < 1.33:
            assessment = "Marginally Capable (Adequate but requires close process monitoring, 1.00 <= Cpk < 1.33)"
        elif cpk < 1.67:
            assessment = "Capable (Conforms to standard manufacturing quality benchmarks, 1.33 <= Cpk < 1.67)"
        else:
            assessment = "Highly Capable / Six-Sigma Quality (Cpk >= 1.67)"

        return {
            "status": "COMPUTED",
            "sample_size": n,
            "mean": round(mean_val, 4),
            "sigma_within": round(sigma_within, 5),
            "sigma_overall": round(s_overall, 5),
            "usl": usl,
            "lsl": lsl,
            "tolerance_band": round(tolerance, 4),
            "cp": cp,
            "cpk": cpk,
            "pp": pp,
            "ppk": ppk,
            "is_normal": is_normal,
            "normality_p_value": normality_p_value,
            "assessment": assessment,
            "warnings": warnings,
            "guidance_notice": "Decision-support interpretation only. Capability indices are guidance metrics and do not constitute disposition decisions.",
            "label": EpistemicLabel.STATISTICAL_FINDING.value
        }

capability_engine = ProcessCapabilityEngine()
