"""
Pareto Analysis Service (80/20 Rule)
Calculates defect and root-cause frequency distributions with cumulative percentages.
Supports dimensions: defect_type, machine, product_family, root_cause, rejection_reason.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.db.models import QualityIncident, RCAHypothesis, Batch, Product, Machine
from backend.app.core.guardrails import EpistemicLabel

class ParetoService:
    """Computes Pareto distributions and isolates the vital few."""

    @staticmethod
    def compute_pareto(
        db: Session,
        dimension: str = "defect_type",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Aggregates quality events by dimension and calculates cumulative percentages.
        """
        query = db.query(QualityIncident)
        if start_date:
            try:
                dt_start = datetime.fromisoformat(start_date)
                query = query.filter(QualityIncident.created_at >= dt_start)
            except Exception:
                pass
        if end_date:
            try:
                dt_end = datetime.fromisoformat(end_date)
                query = query.filter(QualityIncident.created_at <= dt_end)
            except Exception:
                pass

        incidents = query.all()
        counts: Dict[str, int] = {}

        if dimension == "defect_type":
            for inc in incidents:
                key = inc.defect_type or "Unclassified"
                counts[key] = counts.get(key, 0) + 1

        elif dimension == "machine":
            for inc in incidents:
                key = inc.batch.machine.code if (inc.batch and inc.batch.machine) else "Unknown Machine"
                counts[key] = counts.get(key, 0) + 1

        elif dimension == "product_family":
            for inc in incidents:
                key = inc.batch.product.family if (inc.batch and inc.batch.product) else "Unknown Family"
                counts[key] = counts.get(key, 0) + 1

        elif dimension == "root_cause":
            # ONLY include confirmed root causes verified by Quality Engineers
            q = (
                db.query(RCAHypothesis)
                .join(QualityIncident, RCAHypothesis.incident_id == QualityIncident.id)
                .filter(RCAHypothesis.label == EpistemicLabel.CONFIRMED_ROOT_CAUSE.value)
            )
            if start_date:
                try:
                    q = q.filter(QualityIncident.created_at >= datetime.fromisoformat(start_date))
                except Exception:
                    pass
            if end_date:
                try:
                    q = q.filter(QualityIncident.created_at <= datetime.fromisoformat(end_date))
                except Exception:
                    pass
            confirmed_hypos = q.all()
            for h in confirmed_hypos:
                key = h.title or "Unconfirmed"
                counts[key] = counts.get(key, 0) + 1

        elif dimension == "rejection_reason":
            for inc in incidents:
                key = f"{inc.defect_type} ({inc.severity})"
                counts[key] = counts.get(key, 0) + 1

        else:
            for inc in incidents:
                counts[inc.defect_type] = counts.get(inc.defect_type, 0) + 1

        if not counts:
            return {
                "dimension": dimension,
                "total_incidents": 0,
                "categories_count": 0,
                "vital_few_categories": [],
                "items": [],
                "label": EpistemicLabel.STATISTICAL_FINDING.value,
                "analysis_note": "No incidents found matching the specified criteria."
            }

        # Sort descending by count
        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        total_occurrences = sum(c for _, c in sorted_items)

        items_list = []
        cumulative_sum = 0
        vital_few = []
        vital_cutoff_reached = False

        for category, count in sorted_items:
            cumulative_sum += count
            pct = round((count / total_occurrences) * 100.0, 1) if total_occurrences > 0 else 0.0
            cum_pct = round((cumulative_sum / total_occurrences) * 100.0, 1) if total_occurrences > 0 else 0.0

            if not vital_cutoff_reached:
                vital_few.append(category)
                is_vital = True
                if cum_pct >= 80.0:
                    vital_cutoff_reached = True
            else:
                is_vital = False

            items_list.append({
                "category": category,
                "count": count,
                "percentage": pct,
                "cumulative_percentage": cum_pct,
                "is_vital_few": is_vital
            })

        return {
            "dimension": dimension,
            "total_incidents": total_occurrences,
            "categories_count": len(items_list),
            "vital_few_categories": vital_few,
            "items": items_list,
            "label": EpistemicLabel.STATISTICAL_FINDING.value,
            "analysis_note": f"Categories contributing to 80% of quality events isolated under Pareto 80/20 principle."
        }

pareto_service = ParetoService()
