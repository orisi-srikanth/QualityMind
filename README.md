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
| **Req 9** | Process Capability Analysis (Cp, Cpk, Pp, Ppk) | [`backend/app/services/capability.py`](file:///d:/Projects%20Local/QT/backend/app/services/capability.py), [`backend/app/routers/spc.py`](file:///d:/Projects%20Local/QT/backend/app/routers/spc.py) | `python -m pytest backend/tests/test_requirement_9_capability.py` |
| **Req 8** | Root Cause Analysis & 6M Fishbone (Agent 6) | [`backend/app/agents/rca_agent.py`](file:///d:/Projects%20Local/QT/backend/app/agents/rca_agent.py), [`backend/app/services/rag_search.py`](file:///d:/Projects%20Local/QT/backend/app/services/rag_search.py) | `python -m pytest backend/tests/test_phase6.py -k test_full_agent` |
| **Req 9 (CAPA)** | CAPA Management & Efficacy Test (Agent 7) | [`backend/app/agents/capa_agent.py`](file:///d:/Projects%20Local/QT/backend/app/agents/capa_agent.py), [`backend/app/services/effectiveness.py`](file:///d:/Projects%20Local/QT/backend/app/services/effectiveness.py) | `python -m pytest backend/tests/test_phase3.py -k test_effectiveness` |
| **Req 10** | Quality Reviewer & Causal Interceptor (Agent 8)| [`backend/app/agents/reviewer_agent.py`](file:///d:/Projects%20Local/QT/backend/app/agents/reviewer_agent.py) | `python -m pytest backend/tests/test_phase6.py -k test_critic` |
| **Req 11** | Stateful Multi-Agent Orchestration | [`backend/app/agents/workflow.py`](file:///d:/Projects%20Local/QT/backend/app/agents/workflow.py), [`backend/app/orchestrator/engine.py`](file:///d:/Projects%20Local/QT/backend/app/orchestrator/engine.py) | `python -m pytest backend/tests/test_langgraph_and_intake.py -k langgraph` |
| **Req 12** | Vector Knowledge Base Retrieval (RAG) | [`backend/app/agents/quality_knowledge_agent.py`](file:///d:/Projects%20Local/QT/backend/app/agents/quality_knowledge_agent.py), [`backend/app/services/document_loader.py`](file:///d:/Projects%20Local/QT/backend/app/services/document_loader.py) | `python -m pytest backend/tests/test_rag_pipeline.py` |
| **Req 13** | Quality Executive Dashboard & Pareto | [`backend/app/routers/reports.py`](file:///d:/Projects%20Local/QT/backend/app/routers/reports.py), [`frontend/src/pages/Dashboard.tsx`](file:///d:/Projects%20Local/QT/frontend/src/pages/Dashboard.tsx) | `npm --prefix frontend run build` |
| **Req 14** | ISO 9001 / IATF 16949 Audit PDF Dossier | [`backend/app/services/pdf_report.py`](file:///d:/Projects%20Local/QT/backend/app/services/pdf_report.py) | `python -m pytest backend/tests/test_phase7.py` |
| **Req 15** | Mandated Scenarios Suite (TC-01..TC-08) | [`backend/app/scenarios/test_scenarios.py`](file:///d:/Projects%20Local/QT/backend/app/scenarios/test_scenarios.py), [`scripts/run_test_cases.py`](file:///d:/Projects%20Local/QT/scripts/run_test_cases.py) | `python scripts/run_test_cases.py` |

---

## 6. Data and Model Performance

### What Data is Real vs Synthetic
- **Primary Vision Dataset (Synthetic)**: 2,820 synthetic machined cylindrical steel shaft images (512x512 RGB) generated procedurally via `data/generate_shaft_images.py` with directional lathe brushing, specular highlights, chamfers, keyways, and grooves across 6 classes: `no_defect`, `surface_scratch`, `dent`, `crack`, `missing_feature`, and `incorrect_assembly`. Group-stratified into 70/15/15 splits (train: 1,764, val: 378, test: 378) with zero hash leakage, plus 300 unseen Hard Test images.
- **Process & Quality Data (Synthetic)**: CNC process telemetry time series (780 records of vibration, spindle speed, feed rate, motor current, coolant temperature), 365 CMM shaft diameter measurements, and 40 Non-Conformance Reports (NCR-001 through NCR-158). These are calibrated to realistic physical machining limits for 50 mm AISI 1045 precision shafts turned on CNC lathes.
- **External Benchmark (Real)**: MVTec Anomaly Detection (AD) benchmark dataset (`metal_nut` and `screw`) retained strictly as a read-only external benchmark.

### Real Model Performance Numbers
- **Vision Model (MobileNetV3-Small Transfer Learning + Grad-CAM Localizer)**:
  - CPU Inference Latency: **7.46 ms** per image (ONNX runtime / PyTorch, well under the 2,000 ms constraint).
  - **Normal Test Split (378 images, in-distribution)**:
    - Overall Accuracy: **96.83%**
    - Macro-F1: **0.9678** (Macro Precision: 0.9702, Macro Recall: 0.9683)
    - Per-Class F1: `no_defect` (0.9688), `surface_scratch` (0.9060), `dent` (1.0000), `crack` (0.9323), `missing_feature` (1.0000), `incorrect_assembly` (1.0000)
    - Mean Localization IoU (Grad-CAM vs Ground Truth Mask): **0.2437**
    - Bounding Boxes with IoU >= 0.5: **16.4%** (mAP@0.5: **0.1640**)
  - **Hard Test Split (300 images, severe unseen lighting / contrast / blur / noise)**:
    - Overall Accuracy: **40.67%**
    - Macro-F1: **0.3908** (Macro Precision: 0.7649, Macro Recall: 0.4067)
    - Mean Localization IoU: **0.2068** (Boxes IoU >= 0.5: 16.67%, mAP@0.5: **0.1667**)
    - Performance Drop: Macro-F1 dropped by **+0.5770** (-59.6% relative), Accuracy dropped by **+0.5616** (-58.0% relative).
  - **External Real-Image Sanity Check (MVTec AD `metal_nut` & `screw`)**:
    - 60 held-out real images evaluated out-of-distribution without retraining.
    - Binary anomaly accuracy: **50.0%** (30/60). Fastener threads and hex corners trigger out-of-domain defect responses, illustrating real-world sim-to-real transfer boundaries.
- **Process Anomaly Detection (Isolation Forest + Robust Z-Score)**:
  - Precision on synthetic drift events: **96.0%**
  - Recall on sudden tool wear vibration spikes: **100.0%**
- **Vector Retrieval (RAG Search + Cosine Similarity)**:
  - Top-1 retrieval accuracy for anchor query against historical incident NCR-019: **100.0%** (cosine similarity 0.253, top ranked among 47 indexed engineering documents).

### Honest Engineering Disclosure & Stated Limitations
1. **Synthetic Training Origin**: The vision model is trained strictly on synthetic shaft images generated by our procedural script. Metrics are optimistic compared to real factory conditions with variable lens contamination, oil mist, ambient vibration, and lighting fluctuations.
2. **Not Production-Grade**: The model has not been validated on physical factory shaft photographs and is not production-grade.
3. **Uncalibrated Model Confidence**: Softmax output scores represent uncalibrated network confidence, not calibrated Bayesian posterior probabilities.
4. **Mandatory Human Review**: Automated disposition is strictly prohibited. Every flagged defect carries `data_source: "synthetic"` and routes to the quality engineering review queue.

### Process Capability Sufficiency Thresholds & Statistical Guardrails (Requirement 9)
QualityMind enforces rigorous sample size sufficiency and assumption guardrails adhering to AIAG SPC Reference Manual (2nd Edition) and IATF 16949:2016 Section 8.5.1:

| Sample Size Window | Capability Status | Numeric Output | Statistical Guardrail & Warning Behavior |
|:---|:---:|:---:|:---|
| **$n < 5$** (n = 1, 2, 4) | `insufficient_data` | **Suppressed** (`None`) | Strict refusal; capability indices suppressed. Mandatory warning issued: *"INSUFFICIENT DATA: Sample size too small for statistical capability estimation."* |
| **$5 \le n < 30$** (n = 5..29) | `preliminary` | **Computed** | Numeric results accompanied by prominent amber warning banner: *"PRELIMINARY SAMPLE SIZE: Below guideline ($n \ge 30$). Indices exhibit wide confidence intervals; do not use for long-term certification."* |
| **$n \ge 30$** (n = 30+) | `sufficient` | **Computed** | Standard industrial capability estimation conforming to AIAG benchmarks. |

#### Formula Reference & Sigma Distinction
- **Short-Term Capability ($C_p, C_{pk}$)**: Uses within-subgroup variation $\sigma_{\text{within}}$ ($MR\text{-bar}/d_2, d_2=1.128$ for individuals; $R\text{-bar}/d_2$ for rational subgroups).
  $$C_p = \frac{\text{USL} - \text{LSL}}{6 \sigma_{\text{within}}}, \quad C_{pk} = \min\left[\frac{\text{USL} - \mu}{3 \sigma_{\text{within}}}, \frac{\mu - \text{LSL}}{3 \sigma_{\text{within}}}\right]$$
- **Long-Term Performance ($P_p, P_{pk}$)**: Uses total sample standard deviation $s$ ($\text{ddof}=1$).
  $$P_p = \frac{\text{USL} - \text{LSL}}{6 s}, \quad P_{pk} = \min\left[\frac{\text{USL} - \mu}{3 s}, \frac{\mu - \text{LSL}}{3 s}\right]$$
- **Golden Dataset Anchor (BATCH-0245, n=5: 50.01, 50.03, 50.06, 50.08, 50.07 mm against USL 50.05, LSL 49.95)**:
  - $\mu = 50.0500\text{ mm}$, $s = 0.029155\text{ mm}$, $\sigma_{\text{within}} = 0.017730\text{ mm}$
  - $P_p = 0.5717$, $P_{pk} = 0.0000$, $C_p = 0.9400$, $C_{pk} = 0.0000$ (discrepancy vs independent NumPy $< 10^{-4}$).
- **Assumption Checks**: Evaluates statistical control (Nelson rules), distribution normality (Shapiro-Wilk, $\alpha=0.05$), zero/near-zero variance ($\sigma < 10^{-7}$ avoidance of division by zero), progressive linear drift, 3-sigma outliers, and heterogeneous machines/batches.

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
