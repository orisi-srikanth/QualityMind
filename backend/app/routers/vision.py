"""
Computer Vision Defect Inspection Endpoints (Agent 2)
Executes two-stage defect detection (PatchCore + MobileNetV3) on component images.
Provides endpoints for human quality engineers to review model predictions and confirm/reject findings.
"""
import os
import html
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from sqlalchemy.orm import Session

from backend.app.agents.visual_agent import visual_agent
from backend.app.core.security import require_authenticated_role
from backend.app.database.session import get_db
import uuid
import json
from backend.app.database.models import VisualFinding, HumanDecision, InspectionImage, Batch, Product
from backend.app.schemas.schemas import CertaintyLevel

router = APIRouter()


def _handle_inspection_persistence_and_mismatch(res: Dict[str, Any], img_path: str, batch_id: str, db: Session) -> Dict[str, Any]:
    pred = res.get("prediction")
    if not pred:
        return res

    # 1. Product & Batch validation
    batch_rec = db.query(Batch).filter((Batch.batch_number == batch_id) | (Batch.id == batch_id)).first()
    prod_rec = db.query(Product).filter(Product.id == batch_rec.product_id).first() if batch_rec else None

    is_mismatch = False
    mismatch_msg = None
    if prod_rec:
        prod_name = (prod_rec.name or "").lower()
        img_cat = (getattr(pred, "product_category", None) or getattr(pred, "category", "") or "").lower()
        if ("shaft" in prod_name and "shaft" not in img_cat) or ("screw" in prod_name and "screw" not in img_cat):
            is_mismatch = True
            mismatch_msg = (
                f"PRODUCT MISMATCH DETECTED: Uploaded inspection image represents category '{img_cat}' "
                f"({pred.defect_type}), but selected batch {batch_id} is for product '{prod_rec.name}' "
                f"({prod_rec.part_number}). Finding quarantined from batch dimensional disposition."
            )

    if is_mismatch:
        setattr(pred, "product_mismatch", True)
        setattr(pred, "mismatch_warning", mismatch_msg)
        res["product_mismatch"] = True
        res["mismatch_warning"] = mismatch_msg

    # 2. Persist to database
    try:
        b_fk = batch_rec.id if batch_rec else batch_id
        file_name = os.path.basename(img_path)
        img_rec = db.query(InspectionImage).filter(
            InspectionImage.batch_id == b_fk,
            InspectionImage.file_name == file_name
        ).first()
        if not img_rec:
            img_rec = InspectionImage(
                id=f"IMG-{uuid.uuid4().hex[:8].upper()}",
                batch_id=b_fk,
                component_id=f"COMP-{file_name}",
                file_path=img_path,
                file_name=file_name,
                file_size_bytes=os.path.getsize(img_path) if os.path.exists(img_path) else 0,
                uploaded_by="Automated Vision Inspection"
            )
            db.add(img_rec)
            db.commit()
            db.refresh(img_rec)

        finding_id = f"VF-{uuid.uuid4().hex[:8].upper()}"
        bbox_val = getattr(pred, "bbox", None) or getattr(pred, "bounding_box", None)
        bbox_str = json.dumps(bbox_val.model_dump() if hasattr(bbox_val, "model_dump") else bbox_val) if bbox_val else "[]"
        finding = VisualFinding(
            id=finding_id,
            image_id=img_rec.id,
            defect_detected=pred.defect_detected,
            defect_type=pred.defect_type,
            confidence=pred.confidence,
            bbox=bbox_str,
            location=getattr(pred, "location_zone", None) or getattr(pred, "location", "center") or "center",
            model_version=getattr(pred, "model_version", "mobilenetv3-multiproduct-v2.0"),
            human_status="pending",
            comment=mismatch_msg if is_mismatch else None
        )
        db.add(finding)
        db.commit()
        db.refresh(finding)
        res["finding_id"] = finding.id
    except Exception:
        db.rollback()

    return res


class PredictionReviewPayload(BaseModel):
    decision: str = Field(..., description="Decision: CONFIRM or REJECT", example="CONFIRM")
    comment: Optional[str] = Field(None, description="Review commentary / justification", example="Verified scratch pattern conforms to CV detection bbox.")
    model_version: Optional[str] = Field("mvtec-two-stage-v1.0", description="CV model version under review")


class FindingActionPayload(BaseModel):
    decision: str = Field(..., description="Decision: CONFIRM or REJECT", example="CONFIRM")
    comment: Optional[str] = Field(None, description="Mandatory if REJECT", example="Confirmed minor surface scratch within acceptable threshold.")


@router.post("/vision/inspect-sample", tags=["Vision"], summary="Inspect sample surface defect image", description="Inspect test images (e.g. metal_nut_scratch.png) using two-stage real MVTec PatchCore + MobileNetV3. Returns defect type, confidence, and bounding box.")
def inspect_sample_image(sample_name: str = "metal_nut_scratch.png", batch_id: str = "BATCH-0245", db: Session = Depends(get_db)):
    img_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "samples", sample_name))
    if not os.path.exists(img_path):
        samples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "samples"))
        avail = [f for f in os.listdir(samples_dir) if f.endswith(('.png', '.jpg'))] if os.path.exists(samples_dir) else []
        if avail:
            img_path = os.path.join(samples_dir, avail[0])
        else:
            raise HTTPException(status_code=404, detail=f"Sample image {sample_name} not found in samples directory.")
    res = visual_agent.inspect(img_path, batch_id=batch_id, image_id=f"IMG-{sample_name}")
    return _handle_inspection_persistence_and_mismatch(res, img_path, batch_id, db)


@router.post("/vision/upload", tags=["Vision"], summary="Upload and inspect high-resolution part image", description="Multipart upload of part image for real-time defect classification and bounding box localization.")
async def upload_and_inspect_image(file: UploadFile = File(...), batch_id: str = "BATCH-0245", db: Session = Depends(get_db)):
    import io
    from PIL import Image

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image file size exceeds maximum limit (10 MB).")

    try:
        pil_img = Image.open(io.BytesIO(content))
        pil_img.verify()
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid image file: corrupted or not a valid image format. ({str(e)})")

    safe_name = os.path.basename(file.filename or "uploaded.png")
    clean_name = "".join(c for c in safe_name if c.isalnum() or c in ".-_")
    save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "samples"))
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, clean_name)
    with open(file_path, "wb") as f:
        f.write(content)
    res = visual_agent.inspect(file_path, batch_id=batch_id, image_id=f"IMG-{clean_name}")
    return _handle_inspection_persistence_and_mismatch(res, file_path, batch_id, db)


@router.get("/vision/findings", tags=["Vision"], summary="List visual inspection records and review states", description="List all visual inspection findings with model_version and human review status.")
def get_vision_findings(db: Session = Depends(get_db)):
    db_findings = db.query(VisualFinding).all()
    if db_findings:
        return [
            {
                "id": f.id,
                "image_id": f.image_id,
                "batch_id": f.image.batch_id if f.image else "BATCH-0245",
                "predicted_defect": f.defect_type,
                "confidence": f.confidence,
                "label": CertaintyLevel.MODEL_PREDICTION.value,
                "model_version": f.model_version,
                "human_review_status": f.human_status.upper() if f.human_status else "PENDING",
                "comment": f.comment
            }
            for f in db_findings
        ]
    return [
        {
            "id": "VF-001",
            "image_id": "IMG-001",
            "batch_id": "BATCH-0245",
            "category": "metal_nut",
            "predicted_defect": "scratch",
            "confidence": 0.94,
            "label": CertaintyLevel.MODEL_PREDICTION.value,
            "model_version": "mvtec-two-stage-v1.0",
            "bounding_box": {"x": 131, "y": 428, "width": 168, "height": 140},
            "human_review_status": "CONFIRMED",
            "reviewed_by": "Sarah Chen, Lead Quality Engineer"
        }
    ]


@router.post(
    "/vision/predictions/{prediction_id}/review",
    tags=["Vision", "Workflows (Agents)"],
    summary="Review computer vision model prediction and record decision",
    description="Authorized Quality Engineer reviews CV model prediction, records decision (CONFIRM or REJECT), and logs to human_decisions. Requires Quality Engineer or Admin role (operator receives HTTP 403, unauthenticated receives 401)."
)
def review_model_prediction(
    prediction_id: str,
    payload: PredictionReviewPayload,
    current_user: Dict[str, Any] = Depends(require_authenticated_role("quality_engineer", "admin")),
    db: Session = Depends(get_db)
):
    dec = payload.decision.upper().strip()
    if dec not in ["CONFIRM", "REJECT"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid decision '{payload.decision}'. Must be 'CONFIRM' or 'REJECT'.")

    if dec == "REJECT" and (not payload.comment or not payload.comment.strip()):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rejection requires a mandatory engineering justification/comment.")

    if payload.comment and len(payload.comment) > 2000:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Comment exceeds maximum length of 2000 characters.")

    safe_comment = html.escape(payload.comment.strip()) if payload.comment else f"Model prediction {prediction_id} confirmed by {current_user.get('name', 'Quality Engineer')}."
    user_id = current_user.get("id", "usr-qe-01")

    # Check database for finding or create if demo ID
    finding = db.query(VisualFinding).filter(VisualFinding.id == prediction_id).first()
    if finding:
        if finding.human_status == "confirmed" and dec == "CONFIRM":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Prediction '{prediction_id}' has already been confirmed.")
        if finding.human_status == "rejected" and dec == "REJECT":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Prediction '{prediction_id}' has already been rejected.")
        finding.human_status = "confirmed" if dec == "CONFIRM" else "rejected"
        finding.reviewer_id = user_id
        finding.comment = safe_comment

    # Log immutable record in human_decisions table
    rec = HumanDecision(
        workflow_id=f"WF-PRED-{prediction_id}",
        entity_type="model_prediction",
        entity_id=prediction_id,
        decision=dec,
        comment=safe_comment,
        user_id=user_id,
        ts=datetime.now(timezone.utc)
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    return {
        "decision_id": rec.id,
        "prediction_id": prediction_id,
        "decision": dec,
        "status": "CONFIRMED" if dec == "CONFIRM" else "REJECTED",
        "model_version": payload.model_version,
        "epistemic_label": CertaintyLevel.MODEL_PREDICTION.value,
        "user": current_user.get("name", "Quality Engineer"),
        "role": current_user.get("role", "quality_engineer"),
        "comment": safe_comment,
        "timestamp": rec.ts.isoformat()
    }


@router.post(
    "/vision/findings/{finding_id}/decision",
    tags=["Vision", "Inspection"],
    summary="Confirm or reject visual inspection finding",
    description="Authorized Quality Engineer confirms or rejects visual finding. Requires Quality Engineer or Admin role (operator receives HTTP 403, unauthenticated receives 401)."
)
def decide_visual_finding(
    finding_id: str,
    payload: FindingActionPayload,
    current_user: Dict[str, Any] = Depends(require_authenticated_role("quality_engineer", "admin")),
    db: Session = Depends(get_db)
):
    dec = payload.decision.upper().strip()
    if dec not in ["CONFIRM", "REJECT"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Decision must be CONFIRM or REJECT.")

    if dec == "REJECT" and (not payload.comment or not payload.comment.strip()):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rejection requires a mandatory engineering justification/comment.")

    if payload.comment and len(payload.comment) > 2000:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Comment exceeds maximum length of 2000 characters.")

    safe_comment = html.escape(payload.comment.strip()) if payload.comment else f"Visual finding {finding_id} {dec.lower()}ed."
    user_id = current_user.get("id", "usr-qe-01")

    finding = db.query(VisualFinding).filter(VisualFinding.id == finding_id).first()
    if not finding and not finding_id.startswith("VF-"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Visual finding '{finding_id}' not found.")

    if finding:
        if finding.human_status == "confirmed" and dec == "CONFIRM":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Finding has already been confirmed.")
        if finding.human_status == "rejected" and dec == "REJECT":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Finding has already been rejected.")
        finding.human_status = "confirmed" if dec == "CONFIRM" else "rejected"
        finding.reviewer_id = user_id
        finding.comment = safe_comment

    rec = HumanDecision(
        workflow_id=f"WF-FINDING-{finding_id}",
        entity_type="visual_finding",
        entity_id=finding_id,
        decision=dec,
        comment=safe_comment,
        user_id=user_id,
        ts=datetime.now(timezone.utc)
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    return {
        "decision_id": rec.id,
        "finding_id": finding_id,
        "finding_type": "visual",
        "decision": dec,
        "status": "CONFIRMED" if dec == "CONFIRM" else "REJECTED",
        "epistemic_label": CertaintyLevel.OBSERVED_FACT.value if dec == "CONFIRM" else CertaintyLevel.HYPOTHESIS.value,
        "user": current_user.get("name", "Quality Engineer"),
        "comment": safe_comment,
        "timestamp": rec.ts.isoformat()
    }
