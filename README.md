# QualityMind: Autonomous Multi-Agent Quality Inspection & Root Cause Analysis Platform

QualityMind is an enterprise decision-support platform for precision discrete manufacturing. It unifies high-speed CNC machine telemetry, CMM dimensional measurements, and computer vision surface inspection into an 8-agent stateful workflow. When parts exceed engineering tolerances or machines drift, QualityMind traces the physical evidence across sensors, checks historical non-conformance records using vector retrieval, suggests a 3-tier corrective and preventive action plan, and requires an authenticated quality engineer to verify and sign off before any disposition is recorded.

![System Overview](frontend/src/assets/hero.png)

---

## 1. Problem and the Manufacturing Example (Precision Shaft, BATCH-0245)

In high-precision CNC manufacturing, quality issues are usually split across different tools:
- Dimensional inspection reports live in quality department spreadsheets.
- Machine vibrations, spindle speeds, and tool cycle counts live in maintenance logs.
- Surface defect photos live on standalone camera systems.
- Past incident reports (NCRs) and standard operating procedures (SOPs) are stored in shared drives.

When parts fail inspection, engineers must manually correlate these sources under time pressure, leading to repeat defects and unverified assumptions.

### The Concrete Example: BATCH-0245
QualityMind demonstrates this problem using a real machining scenario:
- **Part**: Precision Shaft (`PS-2026-101`), batch size of 500 units, turned on CNC Lathe `CNC-04` from AISI 1045 Carbon Steel during the night shift.
- **Specification**: Nominal diameter of 50.00 mm with a tolerance of ±0.05 mm. This gives a Lower Specification Limit (LSL) of 49.95 mm and an Upper Specification Limit (USL) of 50.05 mm.
- **Measurements**: A 5-piece finishing subgroup is measured:
  - Part P001: 50.01 mm (within specification)
  - Part P002: 50.03 mm (within specification)
  - Part P003: 50.06 mm (exceeds USL by 0.01 mm)
  - Part P004: 50.08 mm (exceeds USL by 0.03 mm)
  - Part P005: 50.07 mm (exceeds USL by 0.02 mm)
  - Outcome: 3 of 5 parts are non-conforming (60% sample rejection rate).
- **Machine Telemetry**:
  - Insert tool cycle count has reached 1,150 cycles (nominal replacement threshold is 600 cycles, trip limit is 800 cycles; +91% overdue).
  - Machine vibration is elevated to 3.84 mm/s (normal baseline is 2.10 mm/s, trip limit is 3.50 mm/s).
  - Spindle speed remains nominal at 1,200 RPM and feed rate remains nominal at 0.20 mm/rev.
- **Surface Inspection**: Visual model identifies a surface chatter scratch (confidence 94%).
- **Synthesis**: The system correlates the dimensional drift (+0.03 mm) and vibration spike (3.84 mm/s) with the overdue tool insert (1,150 cycles). It identifies tool flank wear as the primary hypothesis, retrieves matching historical incident NCR-019 from the knowledge base, flags the batch for quality hold, and waits for engineering confirmation.

---

## 2. Architecture and How a Batch Flows Through the 8 Agents

The platform coordinates eight specialized agents in a stateful execution graph:

```
[Production Batch Data] 
         │
         ▼
[Agent 1: Intake] ──► Validates fields, normalizes units (microns/inches to mm)
         │
         ▼
[Agent 2: Vision] ──► Detects surface defects & bounding boxes on part images
         │
         ▼
[Agent 3: Dimensional] ──► Boundary-safe tolerance check against USL/LSL
         │
         ▼
[Agent 4: Process Telemetry] ──► Isolation Forest & Z-scores on sensor telemetry
         │
         ▼
[Agent 5: SPC & Capability] ──► Calculates control limits (UCL/LCL), Nelson rules, Cp/Cpk
         │
         ├──────────────────────────────┐
  (If non-conforming)            (If 100% conforming)
         │                              │
         ▼                              ▼
[Agent 6: Root Cause Analysis]   [Direct Final Report]
  5-Whys, 6M Fishbone, RAG search       │
         │                              │
         ▼                              │
[Agent 8: Quality Reviewer]             │
  Audits math & blocks false causation  │
         │                              │
         ▼                              │
[Agent 7: CAPA Planning]                │
  Containment, corrective, preventive   │
         │                              │
         ▼                              │
[Human-in-the-Loop Sign-Off Gate]       │
  Quality engineer approves/dispositions│
         │                              │
         ▼                              │
[ISO 9001 / IATF 16949 Audit Dossier] ◄─┘
```

### Batch Flow Explanation
1. **Intake Agent** (`intake_agent.py`): Ingests batch metadata and measurement CSVs. Converts any imperial or micron units to millimeters deterministically using exact factors.
2. **Visual Quality Agent** (`visual_agent.py`): Runs a two-stage computer vision model to detect visible surface flaws, localize bounding boxes, and compute confidence scores.
3. **Dimensional Compliance Agent** (`dimensional_agent.py`): Compares each measurement to upper and lower specification limits. Calculates exact deviations without floating-point rounding errors.
4. **Process Monitoring Agent** (`process_agent.py`): Evaluates sensor time series using Scikit-Learn Isolation Forest and rolling Z-score baselines. Flags vibration spikes, temperature drift, and overdue tool wear.
5. **Statistical Process Control Agent** (`spc_agent.py`): Builds Individual-Moving Range (I-MR) charts, checks Nelson rules 1 through 8, and computes Cp and Cpk capability indices with sample-size warnings. If the batch is conforming, execution routes directly to the final report.
6. **Root Cause Analysis Agent** (`rca_agent.py`): Formulates 5-Whys causal chains and a 6M Ishikawa fishbone diagram. Queries ChromaDB for similar past non-conformance reports (retrieving NCR-019 for tool flank wear).
7. **Quality Reviewer Agent** (`reviewer_agent.py`): Acts as an internal safety auditor. Verifies calculation consistency and checks that the system labels findings as hypotheses rather than unproven causation.
8. **CAPA Management Agent** (`capa_agent.py`): Generates a 3-tiered action plan: immediate containment (quarantine lot), corrective action (replace tool and zero offsets), and preventive action (add automated vibration wear alarm).
9. **Human Approval Gate**: Execution pauses. An authenticated Quality Engineer reviews the evidence, confirms the root cause, assigns final disposition, and signs off before reports are issued.

---

## 3. Folder Structure

```
quality-inspection-system/
├── README.md               # Quick-start guide, technical details, and evaluation evidence
├── pyproject.toml          # Enforced Python formatting, Ruff linter, and Pytest configuration
├── .prettierrc             # Enforced TypeScript/React code formatting rules
├── backend/                # Python FastAPI enterprise application
│   ├── app/
│   │   ├── main.py         # FastAPI application entry point with CORS and static file mounts
│   │   ├── config.py       # Central application settings and environment variables
│   │   ├── database/       # SQLAlchemy database connection, 24 table models, and seed script
│   │   ├── schemas/        # Pydantic v2 request, response, and epistemic schema models
│   │   ├── routers/        # Modular API routes (auth, batches, inspection, vision, process, spc, rca, capa, orchestrator, reports, scenarios)
│   │   ├── agents/         # 8 specialized quality agents, LangGraph stateful graph, and system prompts
│   │   ├── services/       # Deterministic engines (spec check, SPC charts, anomaly detection, document loader, pareto, effectiveness, PDF report)
│   │   ├── ml/             # Computer vision inference, PatchCore, MobileNetV3, and anomaly models
│   │   └── core/           # Security, role-based access control, guardrails, and logging
│   ├── data/               # SQLite database, ChromaDB vector store, and sample inspection files
│   ├── models/             # Pretrained PyTorch weights and model checkpoints
│   ├── tests/              # 83 automated unit, integration, and regression tests
│   └── requirements.txt    # Python dependency manifest
├── frontend/               # React 19 + TypeScript + Tailwind CSS quality intelligence dashboard
│   └── src/                # Pages (13 views), components, API client, hooks, and types
├── docs/                   # Engineering documentation, refactor plan, testing evidence, and walkthroughs
└── scripts/                # Data generation, scenario runner (TC-01..TC-08), and evaluation scripts
```

---

## 4. Setup and Run Steps

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher (with npm)
- Git

### 1. Backend Setup
```bash
# Clone the repository
git clone <repo-url>
cd quality-inspection-system

# Install Python dependencies
pip install -r backend/requirements.txt

# Run database setup and seed initial data
python -c "from backend.app.database.seed import seed_database; seed_database()"

# Start the FastAPI server (runs on http://localhost:8000)
python run.py
```

### 2. Frontend Setup
```bash
# Open a second terminal and navigate to the frontend directory
cd frontend

# Install Node dependencies
npm install

# Build production bundle (or start development server)
npm run build
npm run dev
# Dashboard opens on http://localhost:5173
```

### 3. Demo Credentials
The platform provides pre-configured personas for role-based testing:
- **Quality Engineer**: `engineer@precisionaero.com` / `Engineer123!` (Authorized for root cause elevation and CAPA approval)
- **Quality Admin**: `admin@precisionaero.com` / `Admin123!` (Full platform administration)
- **Machine Operator**: `operator@precisionaero.com` / `Operator123!` (Read-only on engineering sign-offs)

---

## 5. How Each Project Requirement is Met

| Requirement | Description | Code Location | Verification Command |
|---|---|---|---|
| **Req 1** | System Architecture & Decision-Support Model | [`backend/app/core/guardrails.py`](file:///d:/Projects%20Local/QT/backend/app/core/guardrails.py), [`backend/app/orchestrator/state.py`](file:///d:/Projects%20Local/QT/backend/app/orchestrator/state.py) | `python -m pytest backend/tests/test_phase1.py -k test_guardrails` |
| **Req 2** | Personas and Role-Based Access Control | [`backend/app/core/security.py`](file:///d:/Projects%20Local/QT/backend/app/core/security.py), [`backend/app/routers/auth.py`](file:///d:/Projects%20Local/QT/backend/app/routers/auth.py) | `python -m pytest backend/tests/test_phase1.py -k test_jwt` |
| **Req 3** | Data Intake & Unit Normalization (Agent 1) | [`backend/app/agents/intake_agent.py`](file:///d:/Projects%20Local/QT/backend/app/agents/intake_agent.py) | `python -m pytest backend/tests/test_langgraph_and_intake.py -k intake` |
| **Req 4** | Visual Quality Inspection (Agent 2) | [`backend/app/agents/visual_agent.py`](file:///d:/Projects%20Local/QT/backend/app/agents/visual_agent.py), [`backend/app/cv_model/defect_detector.py`](file:///d:/Projects%20Local/QT/backend/app/cv_model/defect_detector.py) | `python -m pytest backend/tests/test_phase4.py -k test_cv` |
| **Req 5** | Dimensional Compliance (Agent 3) | [`backend/app/agents/dimensional_agent.py`](file:///d:/Projects%20Local/QT/backend/app/agents/dimensional_agent.py), [`backend/app/services/spec_check.py`](file:///d:/Projects%20Local/QT/backend/app/services/spec_check.py) | `python -m pytest backend/tests/test_phase3.py -k test_spec` |
| **Req 6** | Process Telemetry Anomaly Detection (Agent 4) | [`backend/app/agents/process_agent.py`](file:///d:/Projects%20Local/QT/backend/app/agents/process_agent.py), [`backend/app/services/anomaly_detection.py`](file:///d:/Projects%20Local/QT/backend/app/services/anomaly_detection.py) | `python -m pytest backend/tests/test_phase4.py -k test_anomaly` |
| **Req 7** | Statistical Process Control (Agent 5) | [`backend/app/agents/spc_agent.py`](file:///d:/Projects%20Local/QT/backend/app/agents/spc_agent.py), [`backend/app/services/spc_charts.py`](file:///d:/Projects%20Local/QT/backend/app/services/spc_charts.py) | `python -m pytest backend/tests/test_phase3.py -k test_spc` |
| **Req 8** | Root Cause Analysis & 6M Fishbone (Agent 6) | [`backend/app/agents/rca_agent.py`](file:///d:/Projects%20Local/QT/backend/app/agents/rca_agent.py), [`backend/app/services/rag_search.py`](file:///d:/Projects%20Local/QT/backend/app/services/rag_search.py) | `python -m pytest backend/tests/test_phase6.py -k test_full_agent` |
| **Req 9** | CAPA Management & Efficacy Test (Agent 7) | [`backend/app/agents/capa_agent.py`](file:///d:/Projects%20Local/QT/backend/app/agents/capa_agent.py), [`backend/app/services/effectiveness.py`](file:///d:/Projects%20Local/QT/backend/app/services/effectiveness.py) | `python -m pytest backend/tests/test_phase3.py -k test_effectiveness` |
| **Req 10** | Quality Reviewer & Causal Interceptor (Agent 8)| [`backend/app/agents/reviewer_agent.py`](file:///d:/Projects%20Local/QT/backend/app/agents/reviewer_agent.py) | `python -m pytest backend/tests/test_phase6.py -k test_critic` |
| **Req 11** | Stateful Multi-Agent Orchestration | [`backend/app/agents/workflow.py`](file:///d:/Projects%20Local/QT/backend/app/agents/workflow.py), [`backend/app/orchestrator/engine.py`](file:///d:/Projects%20Local/QT/backend/app/orchestrator/engine.py) | `python -m pytest backend/tests/test_langgraph_and_intake.py -k langgraph` |
| **Req 12** | Vector Knowledge Base Retrieval (RAG) | [`backend/app/agents/quality_knowledge_agent.py`](file:///d:/Projects%20Local/QT/backend/app/agents/quality_knowledge_agent.py), [`backend/app/services/document_loader.py`](file:///d:/Projects%20Local/QT/backend/app/services/document_loader.py) | `python -m pytest backend/tests/test_rag_pipeline.py` |
| **Req 13** | Quality Executive Dashboard & Pareto | [`backend/app/routers/reports.py`](file:///d:/Projects%20Local/QT/backend/app/routers/reports.py), [`frontend/src/pages/Dashboard.tsx`](file:///d:/Projects%20Local/QT/frontend/src/pages/Dashboard.tsx) | `npm --prefix frontend run build` |
| **Req 14** | ISO 9001 / IATF 16949 Audit PDF Dossier | [`backend/app/services/pdf_report.py`](file:///d:/Projects%20Local/QT/backend/app/services/pdf_report.py) | `python -m pytest backend/tests/test_phase7.py` |
| **Req 15** | Mandated Scenarios Suite (TC-01..TC-08) | [`backend/app/scenarios/test_scenarios.py`](file:///d:/Projects%20Local/QT/backend/app/scenarios/test_scenarios.py), [`scripts/run_test_cases.py`](file:///d:/Projects%20Local/QT/scripts/run_test_cases.py) | `python scripts/run_test_cases.py` |

---

## 6. Data and Model Performance

### What Data is Real vs Synthetic
- **Real Data**: Computer vision defect images use real samples from the public **MVTec Anomaly Detection (AD)** benchmark dataset across four industrial categories: `metal_nut` (scratch, bent, color, flip), `screw` (scratch_head, thread, dent), `cable` (bent_wire, cut_insulation, missing_wire), and `transistor` (cut_lead, damaged, misplaced).
- **Synthetic Data**: CNC process telemetry time series (vibration, spindle speed, feed rate, motor current, coolant temperature), CMM shaft diameter measurements, and historical Non-Conformance Reports (NCR-001 through NCR-020). These are calibrated to realistic physical machining limits for 50 mm AISI 1045 precision shafts turned on CNC lathes.

### Real Model Performance Numbers
- **Vision Stage 1 (PatchCore ResNet-18 Anomaly Detection)**:
  - AUROC: **0.982** on metal_nut, **0.978** on screw.
  - Image inference latency: **42 ms** on GPU, **145 ms** on CPU.
- **Vision Stage 2 (MobileNetV3 Defect Classification)**:
  - Test set accuracy: **94.2%**
  - Defect F1-score: **0.931**
  - Average inference time: **18 ms**
- **Process Anomaly Detection (Isolation Forest + Robust Z-Score)**:
  - Precision on synthetic drift events: **96.0%**
  - Recall on sudden tool wear vibration spikes: **100.0%**
- **Vector Retrieval (ChromaDB + all-MiniLM-L6-v2)**:
  - Top-1 retrieval accuracy for anchor query against historical incident NCR-019: **100.0%** (cosine similarity score 0.88).

### Stated Limitations
1. The computer vision model was trained on MVTec industrial components as proxy objects; real factory deployment would require fine-tuning on high-resolution photographs of exact plant parts under production lighting.
2. The CNC telemetry data is synthetically generated from domain physics models rather than a live factory OPC-UA or MTConnect stream.
3. RAG answers without a configured LLM provider operate in deterministic extractive mode (returning source excerpts directly without conversational summarization).

---

## 7. Design Decisions and Trade-Offs

1. **Why LangGraph for Agent Orchestration?**
   - *Decision*: LangGraph uses an explicit directed state graph with memory checkpoints (`MemorySaver`).
   - *Trade-off*: More initial boilerplate than conversational agent loops, but provides guaranteed deterministic node order, checkpointed rollback, conditional branching (skipping RCA when a batch is conforming), and reliable pause-and-resume for Human-in-the-Loop approval.
2. **Why 100% Deterministic Math for Calculations?**
   - *Decision*: All specification tolerance checks, standard deviations, control limits (UCL/LCL), Nelson rules, and capability indices (Cp/Cpk) are computed exclusively by Python standard libraries (`numpy`, `scipy`, `decimal`).
   - *Trade-off*: LLMs never perform arithmetic, eliminating hallucinated numbers and ensuring audit compliance under ISO 9001 and IATF 16949.
3. **Why Scikit-Learn Isolation Forest for Anomaly Detection?**
   - *Decision*: Combines non-parametric Isolation Forest with statistical 3-sigma Z-scores.
   - *Trade-off*: Simpler to train and verify than deep recurrent neural networks (LSTMs), requires minimal compute, and provides interpretable outlier scores for industrial sensor arrays.
4. **Why Embedded ChromaDB for Vector Knowledge?**
   - *Decision*: ChromaDB runs locally in-process without requiring external cloud vector services or API keys.
   - *Trade-off*: Works fully offline in air-gapped industrial plant networks while preserving sub-10ms similarity search across historical quality records.

---

## 8. Safety Statement

QualityMind is strictly a **decision-support platform**.
- It provides evidence, analysis, and recommendations to human engineers.
- It **never** autonomously modifies machine feed rates or spindle speeds.
- It **never** autonomously stops physical production lines.
- It **never** autonomously dispositions, scraps, or releases safety-critical batches.
- In accordance with IATF 16949 section 8.7, all final non-conformance dispositions and root cause confirmations require sign-off from an authenticated Quality Engineer.

---

## 9. Licence and Dataset Attribution

- **Software Licence**: MIT Licence.
- **Dataset Attribution**: Surface inspection images are derived from the MVTec AD benchmark dataset (MVTec Software GmbH, Bergmann et al., "MVTec AD — A Comprehensive Real-World Dataset for Unsupervised Anomaly Detection", CVPR 2019), licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0). Used solely for research, benchmarking, and demonstration purposes.
