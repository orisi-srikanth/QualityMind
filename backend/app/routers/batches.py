"""
Products, Machines & Manufacturing Batches Endpoints
Catalog of parts, nominal tolerances, CNC machining cells, and batch records.
"""
from fastapi import APIRouter
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from backend.app.schemas.schemas import ProductSpec

router = APIRouter()

class CreateBatchPayload(BaseModel):
    batch_id: str = Field("BATCH-0245", json_schema_extra={"example": "BATCH-0245"})
    product_id: str = Field("PROD-PS-101", json_schema_extra={"example": "PROD-PS-101"})
    part_number: str = Field("PS-2026-101", json_schema_extra={"example": "PS-2026-101"})
    machine: str = Field("CNC-04", json_schema_extra={"example": "CNC-04"})
    material: str = Field("Carbon Steel (AISI 1045)", json_schema_extra={"example": "Carbon Steel (AISI 1045)"})
    material_lot: str = Field("LOT-CS-9842", json_schema_extra={"example": "LOT-CS-9842"})
    shift: str = Field("Night Shift", json_schema_extra={"example": "Night Shift"})
    quantity: int = Field(500, json_schema_extra={"example": 500})

@router.get("/products", tags=["Products & Machines"], summary="List registered product specifications", description="Retrieves catalog of manufactured products, nominal dimensions, tolerances, and inspection parameters.")
def get_products():
    return [
        ProductSpec(
            product_id="PROD-PS-101",
            name="Precision Shaft",
            part_number="PS-2026-101",
            machine_id="CNC-04",
            material="Carbon Steel (AISI 1045)",
            manufacturing_process="CNC Lathe Turning & Precision Grinding",
            inspection_parameter="shaft_diameter",
            unit="mm",
            nominal_mm=50.00,
            tolerance_mm=0.05,
            usl=50.05,
            lsl=49.95,
            inspection_frequency="100% finishing inspection + 5-piece hourly subgroup"
        ),
        ProductSpec(
            product_id="PROD-HB-202",
            name="Hydraulic Bushing",
            part_number="HB-2026-088",
            machine_id="CNC-02",
            material="Alloy Steel 4140",
            manufacturing_process="CNC Boring & Honing",
            inspection_parameter="inner_diameter",
            unit="mm",
            nominal_mm=32.00,
            tolerance_mm=0.03,
            usl=32.03,
            lsl=31.97,
            inspection_frequency="5-piece hourly subgroup"
        )
    ]

@router.get("/products/{product_id}/characteristics", tags=["Products & Machines"], summary="Get product inspection characteristics and tolerance limits", description="Retrieves dimensional tolerances, nominal values, and engineering limits for specified product ID.")
def get_product_characteristics(product_id: str):
    return [
        {
            "characteristic_id": "CHAR-001",
            "product_id": product_id,
            "name": "Shaft Outer Diameter",
            "parameter": "shaft_diameter",
            "unit": "mm",
            "nominal": 50.00,
            "tolerance": 0.05,
            "lsl": 49.95,
            "usl": 50.05,
            "method": "Digital Micrometer / Precision CMM"
        }
    ]

@router.get("/machines", tags=["Products & Machines"], summary="List factory floor CNC machine cells", description="Retrieves registered CNC machining cells, assigned lines, and active health indicators.")
def get_machines():
    return [
        {"machine_id": "CNC-01", "name": "Mazak Quick Turn 250", "cell": "Cell-A", "status": "OPERATIONAL", "vibration_baseline_mms": 2.1},
        {"machine_id": "CNC-02", "name": "Haas ST-20Y Turning Center", "cell": "Cell-A", "status": "OPERATIONAL", "vibration_baseline_mms": 2.0},
        {"machine_id": "CNC-03", "name": "Okuma LB3000 EX II", "cell": "Cell-B", "status": "OPERATIONAL", "vibration_baseline_mms": 1.9},
        {"machine_id": "CNC-04", "name": "DMG Mori NLX 2500/700", "cell": "Cell-B", "status": "ATTENTION_REQUIRED", "vibration_baseline_mms": 2.1, "tool_cycles": 1150}
    ]

@router.get("/batches", tags=["Batches"], summary="List production manufacturing batches", description="Retrieves active and historical batches with shift, quantity, material lot, and quality hold disposition.")
def get_batches():
    return [
        {
            "batch_id": "BATCH-0245",
            "product_id": "PROD-PS-101",
            "part_number": "PS-2026-101",
            "machine": "CNC-04",
            "material": "Carbon Steel",
            "material_lot": "LOT-CS-9842",
            "shift": "Night Shift",
            "quantity": 500,
            "start_time": "2026-10-10 02:00:00",
            "end_time": "2026-10-10 06:30:00",
            "status": "QUALITY_HOLD",
            "operator": "J. Smith (OP-44)",
            "rejection_rate": "8.2%",
            "nonconforming_count": 3
        },
        {
            "batch_id": "BATCH-0246",
            "product_id": "PROD-PS-101",
            "part_number": "PS-2026-101",
            "machine": "CNC-04",
            "material": "Carbon Steel",
            "material_lot": "LOT-CS-9843",
            "shift": "Day Shift",
            "quantity": 500,
            "start_time": "2026-10-10 08:00:00",
            "end_time": "2026-10-10 12:30:00",
            "status": "APPROVED",
            "operator": "M. Davis (OP-12)",
            "rejection_rate": "1.1%",
            "nonconforming_count": 0
        }
    ]

@router.post("/batches", tags=["Batches"], summary="Register new manufacturing batch", description="Ingests new batch record with material lot and process parameters.")
def create_batch(payload: CreateBatchPayload):
    return {
        "status": "CREATED",
        "batch_id": payload.batch_id,
        "product_id": payload.product_id,
        "part_number": payload.part_number,
        "machine": payload.machine,
        "material_lot": payload.material_lot,
        "quantity": payload.quantity,
        "created_at": "2026-10-10T02:00:00Z"
    }
