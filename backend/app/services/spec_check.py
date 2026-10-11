"""
Deterministic Specification & Dimensional Compliance Engine
100% Deterministic Arithmetic (NumPy / Decimal). Zero LLM involvement in conformance decisions.
Guarantees boundary safety (e.g. 50.05 mm is strictly conforming for 50.00 +/- 0.05).
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
import numpy as np
from backend.app.core.guardrails import EpistemicLabel

class SpecificationEngine:
    """Computes engineering limits, evaluations, and tolerance band proximity."""

    @staticmethod
    def evaluate_compliance(
        batch_id: str,
        nominal_mm: float,
        tol_plus: float,
        tol_minus: float,
        measurements: List[Dict[str, Any]],
        parameter_name: str = "shaft_diameter"
    ) -> Dict[str, Any]:
        """
        Evaluates physical sample measurements against engineering specification limits.
        Uses 4-decimal precision rounding to avoid IEEE 754 float boundary errors.
        """
        # Decimal conversions for deterministic boundary safety
        d_nom = Decimal(str(nominal_mm))
        d_plus = Decimal(str(tol_plus)) if tol_plus is not None else None
        d_minus = Decimal(str(tol_minus)) if tol_minus is not None else None

        d_usl = (d_nom + d_plus).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP) if d_plus is not None else None
        d_lsl = (d_nom - d_minus).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP) if d_minus is not None else None

        usl = float(d_usl) if d_usl is not None else None
        lsl = float(d_lsl) if d_lsl is not None else None
        tolerance_band = (usl - lsl) if (usl is not None and lsl is not None) else None

        evaluated_items = []
        conforming_count = 0
        nonconforming_count = 0
        max_deviation = 0.0
        values = []

        for idx, m in enumerate(measurements):
            if isinstance(m, (int, float, Decimal)):
                val = float(m)
                comp_id = f"P{idx+1:03d}"
            else:
                val = float(m["measured_value"] if "measured_value" in m else m.get("value", 0.0))
                comp_id = m.get("component_id", f"P{idx+1:03d}")
            values.append(val)
            d_val = Decimal(str(val)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

            # Strict boundary check with one-sided tolerance support
            is_conforming = True
            dev_from_limit = 0.0
            status = "CONFORMING"

            if d_usl is not None and d_val > d_usl:
                is_conforming = False
                status = "EXCEEDS_USL"
                dev_from_limit = float(d_val - d_usl)
            elif d_lsl is not None and d_val < d_lsl:
                is_conforming = False
                status = "BELOW_LSL"
                dev_from_limit = float(d_lsl - d_val)

            if is_conforming:
                conforming_count += 1
            else:
                nonconforming_count += 1

            dev_from_nominal = float(d_val - d_nom)
            if abs(dev_from_limit) > max_deviation:
                max_deviation = abs(dev_from_limit)

            # Tolerance band usage per part = (x - nominal) / tol_plus
            part_usage = float((d_val - d_nom) / d_plus) if (d_plus is not None and d_plus > 0) else 0.0

            evaluated_items.append({
                "sample_id": comp_id,
                "component_id": comp_id,
                "measured_value": val,
                "nominal_mm": nominal_mm,
                "deviation_from_nominal": round(dev_from_nominal, 4),
                "deviation_from_limit": round(dev_from_limit, 4),
                "tolerance_band_usage": round(part_usage, 4),
                "tolerance_band_usage_percent": round(part_usage * 100.0, 2),
                "is_conforming": is_conforming,
                "status": status,
                "label": EpistemicLabel.OBSERVED_FACT.value
            })

        total = len(measurements)
        rejection_rate = round((nonconforming_count / total * 100.0), 2) if total > 0 else 0.0

        # Trend analysis (linear slope across sequence)
        trend_slope = 0.0
        if len(values) >= 2:
            x = np.arange(len(values))
            slope, _ = np.polyfit(x, values, 1)
            trend_slope = round(float(slope), 5)

        # Proximity to limit (% of tolerance band consumed by mean)
        mean_val = float(np.mean(values)) if values else nominal_mm
        std_sample = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
        std_pop = float(np.std(values, ddof=0)) if len(values) > 0 else 0.0
        tolerance_used_pct = round((abs(mean_val - nominal_mm) / (tolerance_band / 2.0)) * 100.0, 1) if (tolerance_band is not None and tolerance_band > 0) else 0.0

        return {
            "batch_id": batch_id,
            "parameter": parameter_name,
            "nominal_mm": nominal_mm,
            "tolerance_plus": tol_plus,
            "tolerance_minus": tol_minus,
            "usl": usl,
            "lsl": lsl,
            "total_inspected": total,
            "accepted": conforming_count,
            "conforming_count": conforming_count,
            "nonconforming": nonconforming_count,
            "nonconforming_count": nonconforming_count,
            "rejection_rate_percent": rejection_rate,
            "max_deviation_from_limit": round(max_deviation, 4),
            "max_deviation_mm": round(max_deviation, 4),
            "mean_measured": round(mean_val, 4),
            "mean": round(mean_val, 4),
            "std_dev_sample": round(std_sample, 6),
            "std_dev_pop": round(std_pop, 6),
            "trend_slope": trend_slope,
            "tolerance_band_used_percent": tolerance_used_pct,
            "measurements": evaluated_items,
            "evaluated_items": evaluated_items,
            "label": EpistemicLabel.OBSERVED_FACT.value,
            "disposition_notice": "Observed sample result. Final physical product disposition is an authorized human decision."
        }

spec_engine = SpecificationEngine()
