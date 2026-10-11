"""
Database Seeding Script for QualityMind Platform
Creates demo users, machines, products, tolerances, baselines, and historical knowledge base.
"""
from datetime import datetime, timezone
from backend.app.db.session import engine, SessionLocal, Base
from backend.app.db.models import (
    User, Product, Machine, InspectionCharacteristic, ProcessBaseline,
    HistoricalIncident, MaintenanceRecord
)
from backend.app.core.security import hash_password, UserRole

def seed_database():
    """Initializes tables and seeds initial data if not already present."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Seed Users
        if db.query(User).count() == 0:
            users = [
                User(
                    id="usr-admin-01",
                    name="Alex Administrator",
                    email="admin@precisionaero.com",
                    password_hash=hash_password("Admin123!"),
                    role=UserRole.ADMIN.value
                ),
                User(
                    id="usr-qe-01",
                    name="Sarah Chen, Lead Quality Engineer",
                    email="engineer@precisionaero.com",
                    password_hash=hash_password("Engineer123!"),
                    role=UserRole.QUALITY_ENGINEER.value
                ),
                User(
                    id="usr-op-01",
                    name="Dave Miller, CNC Operator",
                    email="operator@precisionaero.com",
                    password_hash=hash_password("Operator123!"),
                    role=UserRole.OPERATOR.value
                ),
            ]
            db.add_all(users)

        # 2. Seed Machines
        if db.query(Machine).count() == 0:
            machines = [
                Machine(id="mach-01", code="CNC-01", type="Haas VF-2 3-Axis Mill", location="Cell A - Roughing"),
                Machine(id="mach-02", code="CNC-02", type="Mori Seiki NLX-2500 CNC Lathe", location="Cell A - Turning"),
                Machine(id="mach-03", code="CNC-03", type="Mazak Quick Turn 250MSY", location="Cell B - Finishing"),
                Machine(id="mach-04", code="CNC-04", type="Okuma LB3000-EX II CNC Lathe", location="Cell B - Turning & Grinding"),
            ]
            db.add_all(machines)

        # 3. Seed Products
        if db.query(Product).count() == 0:
            products = [
                Product(
                    id="prod-ps-101",
                    name="Precision Ground Shaft",
                    part_number="PS-2026-101",
                    process="CNC Lathe Turning & Cylindrical Grinding",
                    material="Carbon Steel AISI 1045",
                    family="Precision Shafts"
                ),
                Product(
                    id="prod-bh-202",
                    name="Bearing Housing",
                    part_number="BH-2026-202",
                    process="CNC Milling & Boring",
                    material="Ductile Cast Iron 65-45-12",
                    family="Bearings"
                ),
                Product(
                    id="prod-fb-303",
                    name="Flanged Bushing",
                    part_number="FB-2026-303",
                    process="CNC Turning & Facing",
                    material="Phosphor Bronze C54400",
                    family="Bushings"
                ),
            ]
            db.add_all(products)
            db.commit()

        # 4. Seed Inspection Characteristics
        if db.query(InspectionCharacteristic).count() == 0:
            chars = [
                InspectionCharacteristic(
                    id="char-ps-01",
                    product_id="prod-ps-101",
                    name="shaft_diameter",
                    unit="mm",
                    nominal=50.00,
                    tol_plus=0.05,
                    tol_minus=0.05,
                    lsl=49.95,
                    usl=50.05,
                    inspection_frequency="100% Critical Feature",
                    sample_size=5
                ),
                InspectionCharacteristic(
                    id="char-bh-01",
                    product_id="prod-bh-202",
                    name="bore_inner_diameter",
                    unit="mm",
                    nominal=85.00,
                    tol_plus=0.03,
                    tol_minus=0.03,
                    lsl=84.97,
                    usl=85.03,
                    inspection_frequency="Subgroup n=5 per hour",
                    sample_size=5
                ),
                InspectionCharacteristic(
                    id="char-fb-01",
                    product_id="prod-fb-303",
                    name="flange_thickness",
                    unit="mm",
                    nominal=12.50,
                    tol_plus=0.08,
                    tol_minus=0.08,
                    lsl=12.42,
                    usl=12.58,
                    inspection_frequency="100%",
                    sample_size=5
                ),
            ]
            db.add_all(chars)

        # 5. Seed Process Baselines for CNC-04
        if db.query(ProcessBaseline).count() == 0:
            baselines = [
                ProcessBaseline(id="base-01", machine_id="mach-04", parameter="spindle_speed", mean=1200.0, std=5.0, p01=1185.0, p99=1215.0, lower_threshold=1150.0, upper_threshold=1250.0, computed_from="Certified Baseline 10-Day Run"),
                ProcessBaseline(id="base-02", machine_id="mach-04", parameter="feed_rate", mean=0.20, std=0.005, p01=0.185, p99=0.215, lower_threshold=0.17, upper_threshold=0.23, computed_from="Certified Baseline 10-Day Run"),
                ProcessBaseline(id="base-03", machine_id="mach-04", parameter="coolant_temp", mean=24.0, std=0.8, p01=22.0, p99=26.0, lower_threshold=18.0, upper_threshold=28.0, computed_from="Certified Baseline 10-Day Run"),
                ProcessBaseline(id="base-04", machine_id="mach-04", parameter="vibration", mean=2.1, std=0.2, p01=1.6, p99=2.6, lower_threshold=1.0, upper_threshold=3.5, computed_from="Certified Baseline 10-Day Run"),
                ProcessBaseline(id="base-05", machine_id="mach-04", parameter="tool_usage_cycles", mean=450.0, std=120.0, p01=50.0, p99=800.0, lower_threshold=0.0, upper_threshold=1000.0, computed_from="Certified Baseline 10-Day Run"),
                ProcessBaseline(id="base-06", machine_id="mach-04", parameter="motor_current", mean=14.5, std=0.5, p01=13.0, p99=16.0, lower_threshold=10.0, upper_threshold=18.0, computed_from="Certified Baseline 10-Day Run"),
                ProcessBaseline(id="base-07", machine_id="mach-04", parameter="cycle_time", mean=45.0, std=1.2, p01=42.0, p99=48.0, lower_threshold=38.0, upper_threshold=52.0, computed_from="Certified Baseline 10-Day Run"),
                ProcessBaseline(id="base-08", machine_id="mach-04", parameter="pressure", mean=5.5, std=0.2, p01=5.0, p99=6.0, lower_threshold=4.5, upper_threshold=6.5, computed_from="Certified Baseline 10-Day Run"),
            ]
            db.add_all(baselines)

        # 6. Seed Historical Incidents for RAG
        if db.query(HistoricalIncident).count() == 0:
            incidents = [
                HistoricalIncident(
                    id="hist-01",
                    ncr_id="NCR-019",
                    title="Dimensional increase associated with confirmed tool wear",
                    defect_type="Oversized shaft diameter",
                    part_number="PS-2026-101",
                    machine="CNC-02",
                    description="Shaft outer diameter drifted positive toward and past USL (50.05 mm) during latter half of high-volume night shift batch. Machine telemetry showed tool cycle counter exceeded recommended threshold of 600 cycles, reaching 1,180 cycles before detection.",
                    confirmed_root_cause="Progressive tool flank wear (VB > 0.35 mm) on carbide finish turning insert due to tool usage exceeding the scheduled preventive replacement threshold.",
                    resolution="Replaced indexable carbide insert with coated grade Kennametal CNMG432-RP. Recalibrated tool setter offset register Z and X. Updated SOP-044 to mandate tool change alarm at 650 cycles.",
                    date="2026-03-14"
                ),
                HistoricalIncident(
                    id="hist-02",
                    ncr_id="NCR-024",
                    title="Bore dimension undersized due to thermal contraction",
                    defect_type="Undersized bore diameter",
                    part_number="BH-2026-202",
                    machine="CNC-01",
                    description="Bearing housing bore was measured immediately after heavy roughing cut while workpiece temperature was 48°C. Part contracted by 0.04 mm upon cooling to room temperature (20°C).",
                    confirmed_root_cause="Measurement error: failure to allow workpiece thermal stabilization prior to final inspection micrometer verification.",
                    resolution="Implemented mandatory 15-minute thermal soaking rack before final dimensional check.",
                    date="2026-04-02"
                ),
                HistoricalIncident(
                    id="hist-03",
                    ncr_id="NCR-031",
                    title="Chatter marks and surface roughness out of specification",
                    defect_type="Surface chatter / finish waviness",
                    part_number="PS-2026-101",
                    machine="CNC-04",
                    description="High-frequency surface marks observed on precision shaft finish. Vibration sensor recorded peak 4.2 mm/s in radial direction.",
                    confirmed_root_cause="Loose clamping collet sleeve and worn tailstock live center bearing causing harmonic vibration.",
                    resolution="Replaced tailstock live center and adjusted hydraulic chuck pressure to 28 bar.",
                    date="2026-05-19"
                ),
            ]
            db.add_all(incidents)

        # 7. Seed Maintenance Records for CNC-04
        if db.query(MaintenanceRecord).count() == 0:
            records = [
                MaintenanceRecord(
                    id="maint-01",
                    machine_id="mach-04",
                    date="2026-10-01",
                    type="preventive",
                    description="Monthly spindle lubrication, hydraulic fluid top-up, and axis backlash laser check. All parameters within specification.",
                    tool_change_flag=False
                ),
                MaintenanceRecord(
                    id="maint-02",
                    machine_id="mach-04",
                    date="2026-10-05",
                    type="tool_change",
                    description="Replaced roughing tool station T01 insert. Finish turning tool T03 inspected with 200 cycles logged.",
                    tool_change_flag=True
                )
            ]
            db.add_all(records)

        # 8. Seed Quality Incidents & CAPA Actions from capa_records.json
        import os, json
        from backend.app.db.models import QualityIncident, CAPAAction, Batch, Measurement
        
        # Ensure anchor batch BATCH-0245 exists or get first batch
        b245 = db.query(Batch).filter_by(batch_number="BATCH-0245").first()
        b_id = b245.id if b245 else "batch-0245"

        if db.query(QualityIncident).count() == 0:
            # Create representative quality incidents for historical and active NCRs
            incidents_to_add = [
                QualityIncident(
                    id="inc-ncr-019",
                    batch_id=b_id,
                    title="NCR-019: Dimensional increase associated with confirmed tool wear",
                    defect_type="Oversized shaft diameter",
                    severity="HIGH",
                    status="closed",
                    created_at=datetime(2026, 3, 14, tzinfo=timezone.utc)
                ),
                QualityIncident(
                    id="inc-ncr-011",
                    batch_id=b_id,
                    title="NCR-011: Excessive tool wear and dimensional drift",
                    defect_type="Oversized shaft diameter",
                    severity="HIGH",
                    status="closed",
                    created_at=datetime(2026, 8, 22, tzinfo=timezone.utc)
                ),
                QualityIncident(
                    id="inc-ncr-012",
                    batch_id=b_id,
                    title="NCR-012: Spindle vibration chatter on turning pass",
                    defect_type="Surface scratch / score",
                    severity="MEDIUM",
                    status="closed",
                    created_at=datetime(2026, 8, 24, tzinfo=timezone.utc)
                ),
                QualityIncident(
                    id="inc-ncr-014",
                    batch_id=b_id,
                    title="NCR-014: Spindle vibration chatter and bearing harmonic",
                    defect_type="Machine vibration chatter",
                    severity="HIGH",
                    status="closed",
                    created_at=datetime(2026, 9, 1, tzinfo=timezone.utc)
                )
            ]
            db.add_all(incidents_to_add)
            db.commit()

        if db.query(CAPAAction).count() == 0:
            capa_file = os.path.join(os.path.dirname(__file__), "..", "..", "data", "capa_records.json")
            if os.path.exists(capa_file):
                with open(capa_file, "r", encoding="utf-8") as f:
                    capa_items = json.load(f)
                
                # Fetch a valid incident ID
                inc_default = db.query(QualityIncident).first()
                inc_id = inc_default.id if inc_default else "inc-ncr-011"
                
                capas_to_add = []
                for item in capa_items:
                    capas_to_add.append(
                        CAPAAction(
                            incident_id=inc_id,
                            action_code=item["action_code"],
                            type=item["type"],
                            description=item["description"],
                            responsible_role=item.get("responsible_role", "Lead Quality Engineer"),
                            due_date=item.get("due_date", "2026-11-15"),
                            status=item.get("status", "completed"),
                            completion_date=item.get("completion_date", "2026-10-01"),
                            effectiveness_result=item.get("effectiveness_result", "Statistically confirmed defect reduction.")
                        )
                    )
                db.add_all(capas_to_add)
                db.commit()

        # 9. Seed Pre- and Post-Intervention Batches for Two-Proportion Effectiveness Verification
        b_pre = db.query(Batch).filter_by(batch_number="BATCH-PRE-01").first()
        if not b_pre:
            b_pre = Batch(
                id="batch-pre-capa-01",
                batch_number="BATCH-PRE-01",
                product_id="prod-ps-101",
                machine_id="mach-04",
                shift="Night Shift",
                quantity=500,
                material_lot="LOT-PRE-881",
                operator_ref="OP-44",
                start_time=datetime(2026, 9, 20, 2, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 9, 20, 6, 0, tzinfo=timezone.utc),
                status="QUALITY_HOLD",
                scenario_label="PRE_CORRECTIVE_BASELINE"
            )
            db.add(b_pre)
            db.commit()

            # Add 500 measurements: exactly 41 nonconforming (8.2%)
            meas_pre = []
            for i in range(500):
                is_defect = (i < 41)
                meas_pre.append(
                    Measurement(
                        batch_id=b_pre.id,
                        characteristic_id="char-ps-01",
                        component_id=f"P-PRE-{i+1:03d}",
                        value=50.07 if is_defect else 50.01,
                        unit="mm",
                        measured_at=datetime(2026, 9, 20, 3, 0, tzinfo=timezone.utc),
                        subgroup=(i // 5) + 1,
                        status="nonconforming" if is_defect else "conforming",
                        deviation_from_limit=0.02 if is_defect else 0.0
                    )
                )
            db.bulk_save_objects(meas_pre)
            db.commit()

        b_post = db.query(Batch).filter_by(batch_number="BATCH-POST-01").first()
        if not b_post:
            b_post = Batch(
                id="batch-post-capa-01",
                batch_number="BATCH-POST-01",
                product_id="prod-ps-101",
                machine_id="mach-04",
                shift="Night Shift",
                quantity=500,
                material_lot="LOT-POST-882",
                operator_ref="OP-44",
                start_time=datetime(2026, 10, 5, 2, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 10, 5, 6, 0, tzinfo=timezone.utc),
                status="CONFORMING",
                scenario_label="POST_CORRECTIVE_VERIFIED"
            )
            db.add(b_post)
            db.commit()

            # Add 500 measurements: exactly 6 nonconforming (1.2%, with relative reduction -85.4% ~ -86%)
            meas_post = []
            for i in range(500):
                is_defect = (i < 6)
                meas_post.append(
                    Measurement(
                        batch_id=b_post.id,
                        characteristic_id="char-ps-01",
                        component_id=f"P-POST-{i+1:03d}",
                        value=50.06 if is_defect else 50.01,
                        unit="mm",
                        measured_at=datetime(2026, 10, 5, 3, 0, tzinfo=timezone.utc),
                        subgroup=(i // 5) + 1,
                        status="nonconforming" if is_defect else "conforming",
                        deviation_from_limit=0.01 if is_defect else 0.0
                    )
                )
            db.bulk_save_objects(meas_post)
            db.commit()

        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
    print("Database seeding completed successfully.")
