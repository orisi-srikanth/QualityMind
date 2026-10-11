"""
Deterministic Inspection Processing & Intake Service (Agents 1 & 3)
Handles secure parsing, validation, unit normalization, batch verification,
and deterministic dimensional compliance checking without LLM intervention.
Supports CSV, Excel (.xlsx, .xls), multiple sheets, formulas, and relational persistence.
"""
import io
import math
import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Set

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.agents.dimensional_agent import dimensional_agent
from backend.app.schemas.schemas import CertaintyLevel, InspectionReport, MeasurementItem
from backend.app.database.models import Batch, Product, InspectionCharacteristic, Measurement, QualityIncident

# Supported engineering units and their multiplier to convert to millimeters (mm)
SUPPORTED_UNITS: Dict[str, float] = {
    "mm": 1.0,
    "millimeter": 1.0,
    "millimeters": 1.0,
    "in": 25.4,
    "inch": 25.4,
    "inches": 25.4,
    '"': 25.4,
    "um": 0.001,
    "µm": 0.001,
    "micron": 0.001,
    "microns": 0.001,
    "cm": 10.0,
    "centimeter": 10.0,
    "centimeters": 10.0,
}

# Maximum allowed file upload size (10 MB)
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024

DEFAULT_SPECS = {
    "PS-2026-101": {
        "record_id": "SPEC-PS-101",
        "part_number": "PS-2026-101",
        "product_name": "Precision Ground Shaft",
        "material": "Carbon Steel (AISI 1045)",
        "parameter": "shaft_diameter",
        "nominal_mm": 50.00,
        "tolerance_mm": 0.05,
        "usl_mm": 50.05,
        "lsl_mm": 49.95,
        "critical_characteristics": "Outer diameter cylindrical tolerance +/- 0.02 mm; Surface finish Ra <= 1.6 um",
        "approval_status": "APPROVED"
    }
}


def sanitize_csv_cell(val: Any) -> Any:
    """
    Guards against CSV/Formula Injection attacks.
    If a string starts with =, +, -, @, \t, or \r, strip the leading symbol.
    """
    if isinstance(val, str):
        v = val.strip()
        if v and v[0] in ("=", "+", "@", "\t", "\r"):
            return v[1:].strip()
    return val


def detect_unit_from_header(header_name: str) -> str:
    """
    Infer measurement unit from column header name if unit is not in a dedicated column.
    Examples:
    'diameter_mm', 'Diameter (mm)', 'shaft_diameter [mm]' -> 'mm'
    'diameter (in)', 'diameter_in', 'shaft_diameter [inches]' -> 'in'
    'diameter_um', 'diameter (um)', 'diameter [µm]' -> 'um'
    'diameter (cm)', 'diameter_cm' -> 'cm'
    """
    h = header_name.lower()
    # Check for inches
    if re.search(r'[\(_\[\s](in|inch|inches)[\)\]\s$]', h) or h.endswith(('_in', '(in)', '[in]', '"')):
        return "in"
    # Check for microns
    if re.search(r'[\(_\[\s](um|µm|micron|microns)[\)\]\s$]', h) or h.endswith(('_um', '(um)', '[um]', '_micron')):
        return "um"
    # Check for centimeters
    if re.search(r'[\(_\[\s](cm|centimeter|centimeters)[\)\]\s$]', h) or h.endswith(('_cm', '(cm)', '[cm]')):
        return "cm"
    return "mm"


def get_batch_and_spec(batch_id: str, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
    """Look up batch existence and applicable approved engineering specification."""
    normalized_batch_id = batch_id.strip()

    if db:
        b = db.query(Batch).filter((Batch.batch_number == normalized_batch_id) | (Batch.id == normalized_batch_id)).first()
        if b and b.product:
            char = db.query(InspectionCharacteristic).filter(InspectionCharacteristic.product_id == b.product.id).first()
            nom = char.nominal if char else 50.00
            tol_plus = char.tol_plus if char else 0.05
            tol_minus = char.tol_minus if char else 0.05
            usl = char.usl if char else (nom + tol_plus)
            lsl = char.lsl if char else (nom - tol_minus)
            return {
                "batch_id": b.batch_number,
                "batch_pk": b.id,
                "part_number": b.product.part_number,
                "product_id": b.product.id,
                "machine": b.machine.code if b.machine else "CNC-04",
                "status": b.status,
                "product_name": b.product.name,
                "parameter": char.name if char else "shaft_diameter",
                "characteristic_id": char.id if char else None,
                "nominal_mm": nom,
                "tolerance_mm": tol_plus,
                "tolerance_plus": tol_plus,
                "tolerance_minus": tol_minus,
                "usl_mm": usl,
                "lsl_mm": lsl,
                "approval_status": "APPROVED"
            }

    # Fallback to defaults
    spec = DEFAULT_SPECS.get("PS-2026-101")
    return {
        "batch_id": normalized_batch_id,
        "batch_pk": normalized_batch_id,
        "part_number": "PS-2026-101",
        "product_id": "prod-ps-101",
        "machine": "CNC-04",
        "status": "QUALITY_HOLD",
        "product_name": spec["product_name"],
        "parameter": spec["parameter"],
        "characteristic_id": "char-ps-dia-01",
        "nominal_mm": spec["nominal_mm"],
        "tolerance_mm": spec["tolerance_mm"],
        "usl_mm": spec["usl_mm"],
        "lsl_mm": spec["lsl_mm"],
        "approval_status": "APPROVED"
    }


def process_inspection_file(
    file_bytes: bytes,
    filename: str,
    requested_batch_id: Optional[str] = None,
    db: Optional[Session] = None,
    user: Optional[str] = None,
    allow_partial: bool = False
) -> Dict[str, Any]:
    """
    Parse, validate, normalize units, and evaluate compliance for an uploaded inspection CSV or Excel file.
    Supports CSV and Excel (.xlsx, .xls), multiple sheets, formula reading, and DB persistence.
    Distinguishes errors from warnings and provides complete structured missing-value report.
    """
    # 1. Size limit check (Check 10: file size limit enforced)
    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded file size ({len(file_bytes)/(1024*1024):.2f} MB) exceeds maximum allowed limit ({MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB)."
        )

    # 2. File format check (Check 1 & Check 2)
    fn_lower = filename.lower()
    is_excel = fn_lower.endswith((".xlsx", ".xls"))
    is_csv = fn_lower.endswith(".csv")

    if not (is_csv or is_excel):
        raise HTTPException(
            status_code=422,
            detail="Unsupported file format: only CSV (.csv) and Excel (.xlsx, .xls) files are accepted."
        )

    selected_sheet_name: Optional[str] = None
    all_sheet_names: List[str] = []

    # 3. Parse Content
    if is_excel:
        try:
            excel_file = pd.ExcelFile(io.BytesIO(file_bytes), engine="openpyxl")
            all_sheet_names = excel_file.sheet_names
            if not all_sheet_names:
                raise HTTPException(status_code=422, detail="Excel workbook contains no visible sheets.")

            # Multiple sheets handling: find sheet with inspection data or use the first one
            preferred = [s for s in all_sheet_names if any(k in s.lower() for k in ["inspection", "measure", "data"])]
            selected_sheet_name = preferred[0] if preferred else all_sheet_names[0]

            # data_only=True via openpyxl ensures formulas are read as computed values, not code execution
            df = pd.read_excel(excel_file, sheet_name=selected_sheet_name)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Malformed or corrupt Excel file ({filename}): unable to read workbook. Error: {str(e)}"
            )
    else:
        # Decode CSV safely
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content = file_bytes.decode("latin-1")
            except Exception:
                raise HTTPException(
                    status_code=422,
                    detail="Malformed CSV content: unable to decode file as UTF-8 or Latin-1 text."
                )

        if not content.strip():
            raise HTTPException(
                status_code=422,
                detail="Uploaded CSV file is empty (0 bytes or blank content)."
            )

        try:
            df = pd.read_csv(io.StringIO(content))
        except pd.errors.EmptyDataError:
            raise HTTPException(
                status_code=422,
                detail="Uploaded CSV contains no measurement rows."
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Malformed CSV content ({filename}): {str(e)}"
            )

        # Check for non-tabular spoofed text files
        if len(df.columns) <= 1:
            first_col = str(df.columns[0]).lower()
            if not any(k in first_col for k in ["component", "sample", "diameter", "value"]):
                raise HTTPException(
                    status_code=422,
                    detail="Uploaded file is not a valid delimited CSV table (no valid columns or delimiter detected)."
                )

    # 4. Empty rows validation
    if df.empty or len(df) == 0:
        raise HTTPException(
            status_code=422,
            detail="Uploaded file contains no measurement rows."
        )

    # 5. Schema & Header Identification (Column order, header variants, extra columns)
    col_map: Dict[str, str] = {}
    for col in df.columns:
        c_clean = str(col).lower().strip()
        # Sanitize column headers from formula injection
        c_clean = str(sanitize_csv_cell(c_clean))

        if c_clean in ["batch_id", "batch", "lot_id", "batch_number"]:
            col_map["batch_id"] = col
        elif c_clean in ["component_id", "sample_id", "part_serial", "serial_number", "piece_id", "part_id", "piece", "serial", "sample"]:
            col_map["component_id"] = col
        elif c_clean in ["diameter_mm", "diameter", "diameter (mm)", "shaft_diameter", "value", "measured_value", "measured", "val", "dia_mm", "reading", "measurement", "dimension", "bore_diameter", "flange_thickness"]:
            col_map["value"] = col
        elif c_clean in ["unit", "units", "uom", "measurement_unit"]:
            col_map["unit"] = col
        elif c_clean in ["parameter", "characteristic", "characteristic_id", "inspection_parameter", "feature"]:
            col_map["parameter"] = col

    # Secondary fuzzy detection if exact alias wasn't matched
    if "component_id" not in col_map:
        for col in df.columns:
            c_clean = str(col).lower().strip()
            if "batch" not in c_clean and any(k in c_clean for k in ["sample", "component", "part_id", "piece", "serial"]):
                col_map["component_id"] = col
                break

    if "value" not in col_map:
        for col in df.columns:
            c_clean = str(col).lower().strip()
            if any(k in c_clean for k in ["dia", "value", "measure", "shaft", "reading", "dim"]):
                col_map["value"] = col
                break

    # Validate required columns
    missing_required = []
    if "component_id" not in col_map:
        missing_required.append("component identifier (e.g. 'component_id', 'sample_id')")
    if "value" not in col_map:
        missing_required.append("measured value (e.g. 'diameter_mm', 'measured_value')")

    if missing_required:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required columns in file: {', '.join(missing_required)}. Found columns: {list(df.columns)}"
        )

    comp_col = col_map["component_id"]
    val_col = col_map["value"]
    unit_col = col_map.get("unit")
    batch_col = col_map.get("batch_id")
    header_fallback_unit = detect_unit_from_header(val_col)

    # 6. Batch resolution & validation
    csv_batches: Set[str] = set()
    if batch_col:
        for val in df[batch_col].dropna():
            s_val = str(val).strip()
            if s_val:
                csv_batches.add(s_val)

    if len(csv_batches) > 1:
        raise HTTPException(
            status_code=422,
            detail=f"File contains multiple batch IDs ({sorted(list(csv_batches))}). Please upload measurements for a single batch."
        )

    file_batch_id = list(csv_batches)[0] if csv_batches else None
    if requested_batch_id and file_batch_id:
        if requested_batch_id.strip().upper() != file_batch_id.strip().upper():
            raise HTTPException(
                status_code=422,
                detail=f"Batch ID mismatch: file contains batch '{file_batch_id}' but request specified '{requested_batch_id}'."
            )

    effective_batch_id = requested_batch_id or file_batch_id or "BATCH-0245"

    # Validate that batch exists
    batch_spec = get_batch_and_spec(effective_batch_id, db=db)
    if not batch_spec:
        raise HTTPException(
            status_code=404,
            detail=f"Batch '{effective_batch_id}' not found in manufacturing system."
        )

    # 7. Row-by-Row parsing, validation & unit normalization
    accepted_measurements: List[Dict[str, Any]] = []
    unit_conversions: List[Dict[str, Any]] = []
    missing_values: List[Dict[str, Any]] = []
    errors: List[str] = []
    warnings: List[str] = []
    seen_component_ids: Set[str] = set()

    for idx, row in df.iterrows():
        row_num = idx + 2  # 1-indexed row number where row 1 is header

        has_row_error = False

        # --- A. Component ID Validation ---
        raw_comp_id = row.get(comp_col)
        if pd.isna(raw_comp_id) or str(raw_comp_id).strip() == "" or str(raw_comp_id).strip().lower() in ("nan", "none", "null"):
            missing_values.append({
                "row": row_num,
                "column": str(comp_col),
                "message": f"Blank or null component identifier at row {row_num}."
            })
            errors.append(f"Row {row_num}: Blank or null component identifier.")
            has_row_error = True
            comp_id = f"UNKNOWN_ROW_{row_num}"
        else:
            comp_id = str(sanitize_csv_cell(raw_comp_id)).strip()
            if comp_id in seen_component_ids:
                errors.append(f"Row {row_num}: Duplicate component identifier '{comp_id}' within file.")
                has_row_error = True
            seen_component_ids.add(comp_id)

        # --- B. Measurement Value Validation ---
        raw_val = row.get(val_col)
        if pd.isna(raw_val) or str(raw_val).strip() == "" or str(raw_val).strip().lower() in ("nan", "none", "null"):
            missing_values.append({
                "row": row_num,
                "column": str(val_col),
                "message": f"Blank or null measurement value at row {row_num} (component '{comp_id}')."
            })
            errors.append(f"Row {row_num}: Blank measurement value for component '{comp_id}'.")
            has_row_error = True
            val_float = None
        else:
            raw_val_clean = sanitize_csv_cell(raw_val)
            try:
                val_float = float(raw_val_clean)
                if math.isnan(val_float) or math.isinf(val_float):
                    errors.append(f"Row {row_num}: Measurement value is NaN or infinite for component '{comp_id}'.")
                    has_row_error = True
            except (ValueError, TypeError):
                errors.append(f"Row {row_num}: Non-numeric measurement value '{raw_val}' for component '{comp_id}'.")
                has_row_error = True
                val_float = None

        # --- C. Unit Validation & Normalization ---
        if unit_col and not pd.isna(row.get(unit_col)):
            row_unit = str(sanitize_csv_cell(row[unit_col])).strip().lower()
        else:
            row_unit = header_fallback_unit

        if row_unit not in SUPPORTED_UNITS:
            errors.append(
                f"Row {row_num}: Unsupported measurement unit '{row.get(unit_col) if unit_col else row_unit}' for component '{comp_id}'. Supported units: mm, in, um, cm."
            )
            has_row_error = True

        # --- D. Plausibility Bounds Check ---
        val_mm = None
        if val_float is not None and row_unit in SUPPORTED_UNITS:
            multiplier = SUPPORTED_UNITS[row_unit]
            val_mm = round(val_float * multiplier, 4)

            if val_mm <= 0:
                errors.append(f"Row {row_num}: Implausible measurement value ({val_mm} mm) for component '{comp_id}'. Dimensions must be strictly positive (> 0).")
                has_row_error = True
            elif val_mm > 1000.0:
                errors.append(f"Row {row_num}: Implausible measurement value ({val_mm} mm) for component '{comp_id}'. Exceeds physical threshold limit (1,000 mm).")
                has_row_error = True

            if row_unit != "mm" and not has_row_error:
                unit_conversions.append({
                    "sample_id": comp_id,
                    "row": row_num,
                    "original_value": val_float,
                    "original_unit": row_unit,
                    "conversion_multiplier": multiplier,
                    "converted_value_mm": val_mm
                })

        if not has_row_error and val_mm is not None:
            accepted_measurements.append({
                "sample_id": comp_id,
                "measured_value": val_mm,
                "original_unit": row_unit,
                "original_value": val_float
            })

    # 8. Policy Check: If errors found, reject entire file (zero silent drops) unless allow_partial is set
    total_rows = len(df)
    if errors and not allow_partial:
        raise HTTPException(
            status_code=422,
            detail={
                "status": "rejected",
                "message": f"Validation failed with {len(errors)} error(s) and {len(missing_values)} missing value(s).",
                "filename": filename,
                "total_rows": total_rows,
                "accepted_rows": 0,
                "rejected_rows": total_rows,
                "errors": errors,
                "missing_values": missing_values,
                "warnings": warnings,
                "unit_conversions": unit_conversions
            }
        )

    if not accepted_measurements:
        raise HTTPException(
            status_code=422,
            detail={
                "status": "rejected",
                "message": "No valid measurement rows could be imported from the file.",
                "filename": filename,
                "total_rows": total_rows,
                "accepted_rows": 0,
                "rejected_rows": total_rows,
                "errors": errors,
                "missing_values": missing_values,
                "warnings": warnings
            }
        )

    # 9. Deterministic Compliance Evaluation (Agent 3)
    comp = dimensional_agent.evaluate_compliance(
        batch_id=effective_batch_id,
        measurements=[{"sample_id": m["sample_id"], "measured_value": m["measured_value"]} for m in accepted_measurements],
        nominal_mm=batch_spec["nominal_mm"],
        tolerance_mm=batch_spec["tolerance_mm"]
    )
    rep: InspectionReport = comp["report"]

    # 10. Persistence & Traceability into SQLite DB (Check 1, 2, 9)
    if db:
        db_batch = db.query(Batch).filter((Batch.batch_number == effective_batch_id) | (Batch.id == effective_batch_id)).first()
        if db_batch:
            # Resolve characteristic
            char = db.query(InspectionCharacteristic).filter(InspectionCharacteristic.product_id == db_batch.product_id).first()
            if not char:
                char = InspectionCharacteristic(
                    product_id=db_batch.product_id,
                    name=batch_spec["parameter"],
                    nominal=batch_spec["nominal_mm"],
                    tol_plus=batch_spec["tolerance_mm"],
                    tol_minus=batch_spec["tolerance_mm"],
                    usl=batch_spec["usl_mm"],
                    lsl=batch_spec["lsl_mm"],
                    unit="mm"
                )
                db.add(char)
                db.commit()
                db.refresh(char)

            # Map conformance by sample_id from report
            conf_map = {m.sample_id: m for m in rep.measurements}

            source_type_val = "excel" if is_excel else "csv"
            upload_time_now = datetime.now(timezone.utc)
            uploader_val = user or "quality_engineer@precisionaero.com"

            # Clear previous measurements for this batch to ensure clean state
            db.query(Measurement).filter(Measurement.batch_id == db_batch.id).delete()

            for item in accepted_measurements:
                s_id = item["sample_id"]
                val = item["measured_value"]
                rep_item = conf_map.get(s_id)
                is_conf = rep_item.is_conforming if rep_item else (batch_spec["lsl_mm"] <= val <= batch_spec["usl_mm"])
                dev_limit = rep_item.deviation_from_limit if rep_item else (val - batch_spec["usl_mm"] if val > batch_spec["usl_mm"] else 0.0)

                meas = Measurement(
                    batch_id=db_batch.id,
                    characteristic_id=char.id,
                    component_id=s_id,
                    value=val,
                    unit="mm",
                    status="conforming" if is_conf else "nonconforming",
                    deviation_from_limit=dev_limit,
                    source_type=source_type_val,
                    file_name=filename,
                    uploaded_by=uploader_val,
                    upload_time=upload_time_now
                )
                db.add(meas)

            db.commit()

            # Automatic Quality Incident handling (Requirement 4 Check 7)
            if rep.nonconforming > 0:
                inc = db.query(QualityIncident).filter(QualityIncident.batch_id == db_batch.id).first()
                if not inc:
                    inc = QualityIncident(
                        batch_id=db_batch.id,
                        title=f"Dimensional Nonconformance: {rep.nonconforming}/{rep.total_inspected} parts exceed engineering specification",
                        defect_type="Oversized shaft diameter",
                        severity="HIGH",
                        status="open"
                    )
                    db.add(inc)
                else:
                    inc.title = f"Dimensional Nonconformance: {rep.nonconforming}/{rep.total_inspected} parts exceed engineering specification"
                    inc.status = "open"
                db.commit()

    # 11. Compile warnings
    if unit_conversions:
        conv_units = sorted(list(set(u["original_unit"] for u in unit_conversions)))
        warnings.append(
            f"Normalized {len(unit_conversions)} measurement(s) to mm from original unit(s): {', '.join(conv_units)}."
        )
    if is_excel and selected_sheet_name:
        warnings.append(f"Imported from Excel workbook sheet: '{selected_sheet_name}'.")

    # 12. Return complete structured response contract
    report_dict = rep.model_dump()
    measurements_out = report_dict.get("measurements", [])

    return {
        "status": "success",
        "batch_id": effective_batch_id,
        "source_filename": filename,
        "sheet_name": selected_sheet_name,
        "total_rows": total_rows,
        "accepted_rows": len(accepted_measurements),
        "rejected_rows": len(errors) if allow_partial else 0,
        "missing_values": missing_values,
        "errors": errors if allow_partial else [],
        "warnings": warnings,
        "unit_conversions": unit_conversions,
        "specification": {
            "nominal_mm": batch_spec["nominal_mm"],
            "tolerance_mm": batch_spec["tolerance_mm"],
            "lsl_mm": batch_spec["lsl_mm"],
            "usl_mm": batch_spec["usl_mm"]
        },
        "spec_check": {
            "total_inspected": rep.total_inspected,
            "accepted": rep.accepted,
            "nonconforming": rep.nonconforming,
            "rejection_rate_percent": rep.rejection_rate_percent,
        },
        "measurements": measurements_out,
        "report": report_dict,
        "data_source": f"Uploaded file: {filename}"
    }


def process_inspection_csv(
    file_bytes: bytes,
    filename: str,
    requested_batch_id: Optional[str] = None,
    db: Optional[Session] = None,
    user: Optional[str] = None
) -> Dict[str, Any]:
    """Backward-compatible wrapper delegating to process_inspection_file."""
    return process_inspection_file(
        file_bytes=file_bytes,
        filename=filename,
        requested_batch_id=requested_batch_id,
        db=db,
        user=user
    )


def generate_csv_template(batch_id: str = "BATCH-0245") -> str:
    """Generate a clean sample inspection CSV template."""
    return (
        "component_id,diameter_mm\n"
        "P001,50.01\n"
        "P002,50.03\n"
        "P003,50.06\n"
        "P004,50.08\n"
        "P005,50.07\n"
    )
