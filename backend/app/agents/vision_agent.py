"""
Agent 2: Visual Quality Inspection Agent
Executes PyTorch and OpenCV defect detection models on product images.
Detects surface scratches, cracks, dents, and localizes them with bounding boxes and confidence scores.
"""
import os
import time
from typing import Dict, Any, Optional
from backend.app.agents.base_agent import BaseQualityAgent
from backend.app.models.schemas import CertaintyLevel, VisualDefectPrediction, BoundingBox
from backend.app.cv_model.defect_detector import vision_model

class VisualQualityInspectionAgent(BaseQualityAgent):
    def __init__(self):
        super().__init__(
            name="Agent 2 — Visual Quality Inspection Agent",
            role="Use computer vision to identify, localize and classify visible manufacturing defects",
            certainty_level=CertaintyLevel.MODEL_PREDICTION
        )

    def inspect(self, image_path: str, batch_id: str = "BATCH-0245", image_id: str = "IMG-001", category: Optional[str] = None) -> Dict[str, Any]:
        start = time.time()
        tool_calls = [
            "tool_patchcore_anomaly_localization",
            "tool_mobilenet_defect_classification",
            "tool_generate_defect_overlay"
        ]

        annotated_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "annotated"))
        result = vision_model.inspect_image(image_path, image_id=image_id, category=category, output_annotated_dir=annotated_dir)

        bbox_dict = result.get("bbox") or result.get("bounding_box")
        bbox_obj = BoundingBox(**bbox_dict) if bbox_dict else None

        annotated_url = f"/uploads/annotated/{result.get('annotated_filename')}" if result.get('annotated_filename') else None
        image_url = f"/uploads/samples/{os.path.basename(image_path)}"

        prediction = VisualDefectPrediction(
            image_id=image_id,
            batch_id=batch_id,
            source=result.get("source", "MVTec AD (proxy part)"),
            category=result.get("category", "metal_nut"),
            defect_detected=result["defect_detected"],
            anomaly_score=result.get("anomaly_score", 0.0),
            defect_type=result["defect_type"],
            raw_class=result.get("raw_class", "good"),
            confidence=result["confidence"],
            location=result["location"],
            bbox=bbox_dict,
            bounding_box=bbox_obj,
            severity="Critical" if result["defect_type"] in ["surface_scratch", "dent_deformation", "thread_damage"] else "Minor",
            certainty=CertaintyLevel.MODEL_PREDICTION,
            label="MODEL_PREDICTION",
            model_version=result.get("model_version", "mvtec-two-stage-v1.0"),
            image_url=image_url,
            annotated_image_url=annotated_url
        )

        duration = int((time.time() - start) * 1000)
        log_entry = self.log_execution(
            step_number=2,
            input_summary=f"Processed product inspection image {image_id} for batch {batch_id} (Category: {prediction.category})",
            tool_calls=tool_calls,
            output_summary=(
                f"CV Model Prediction: defect_detected={prediction.defect_detected}, "
                f"type={prediction.defect_type}, anomaly_score={prediction.anomaly_score:.3f}, "
                f"confidence={prediction.confidence:.2%}, location={prediction.location}"
            ),
            duration_ms=duration
        )

        return {
            "prediction": prediction,
            "metrics": result.get("metrics"),
            "log": log_entry
        }

vision_agent = VisualQualityInspectionAgent()
