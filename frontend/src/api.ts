import {
  ProductSpec, ProductionBatch, InspectionReport, VisualDefectPrediction,
  ProcessMonitoringReport, SPCReport, RCAReport, CAPAReport,
  WorkflowState, TestScenarioResult
} from "./types";

const rawApiUrl = import.meta.env.VITE_API_URL;
const API_BASE = rawApiUrl ? `${String(rawApiUrl).replace(/\/$/, "")}/api` : "/api";

export const api = {
  getDashboardSummary: async () => {
    const res = await fetch(`${API_BASE}/dashboard/summary`);
    return res.json();
  },

  getProducts: async (): Promise<ProductSpec[]> => {
    const res = await fetch(`${API_BASE}/products`);
    return res.json();
  },

  getBatches: async (): Promise<ProductionBatch[]> => {
    const res = await fetch(`${API_BASE}/batches`);
    return res.json();
  },

  evaluateMeasurements: async (data: { batch_id: string; measurements: any[] }) => {
    const res = await fetch(`${API_BASE}/inspection/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return res.json();
  },

  uploadCsvInspection: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/inspection/upload-csv`, {
      method: "POST",
      body: formData,
    });
    return res.json();
  },

  inspectSampleImage: async (sampleName: string = "IMG-001.png") => {
    const res = await fetch(`${API_BASE}/vision/inspect-sample?sample_name=${encodeURIComponent(sampleName)}`, {
      method: "POST",
    });
    return res.json();
  },

  uploadAndInspectImage: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/vision/upload`, {
      method: "POST",
      body: formData,
    });
    return res.json();
  },

  getTelemetry: async (batchId: string = "BATCH-0245"): Promise<{
    report: ProcessMonitoringReport;
    data_points: any[];
    log: any;
  }> => {
    const res = await fetch(`${API_BASE}/process/telemetry?batch_id=${encodeURIComponent(batchId)}`);
    return res.json();
  },

  getSpcAnalysis: async (batchId: string = "BATCH-0245"): Promise<{
    report: SPCReport;
    log: any;
  }> => {
    const res = await fetch(`${API_BASE}/spc/analyze?batch_id=${encodeURIComponent(batchId)}`);
    return res.json();
  },

  getIncidents: async () => {
    const res = await fetch(`${API_BASE}/incidents`);
    return res.json();
  },

  getRcaAnalysis: async (incidentId: string = "INC-2026-088", batchId: string = "BATCH-0245"): Promise<{
    report: RCAReport;
    log: any;
  }> => {
    const res = await fetch(`${API_BASE}/rca/analyze?incident_id=${encodeURIComponent(incidentId)}&batch_id=${encodeURIComponent(batchId)}`);
    return res.json();
  },

  searchHistoricalIncidents: async (query: string) => {
    const res = await fetch(`${API_BASE}/rca/rag-search?q=${encodeURIComponent(query)}`);
    return res.json();
  },

  getCapaPlan: async (incidentId: string = "INC-2026-088", batchId: string = "BATCH-0245"): Promise<{
    capa: CAPAReport;
    log: any;
  }> => {
    const res = await fetch(`${API_BASE}/capa/plan?incident_id=${encodeURIComponent(incidentId)}&batch_id=${encodeURIComponent(batchId)}`);
    return res.json();
  },

  runOrchestratedPipeline: async (batchId: string = "BATCH-0245"): Promise<WorkflowState> => {
    const res = await fetch(`${API_BASE}/orchestrator/run?batch_id=${encodeURIComponent(batchId)}`, {
      method: "POST",
    });
    return res.json();
  },

  runLangGraphPipeline: async (batchId: string = "BATCH-0245"): Promise<any> => {
    const res = await fetch(`${API_BASE}/orchestrator/langgraph-run?batch_id=${encodeURIComponent(batchId)}`, {
      method: "POST",
    });
    return res.json();
  },

  submitHumanDecision: async (decisionData: any) => {
    const res = await fetch(`${API_BASE}/review/sign-off`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(decisionData),
    });
    return res.json();
  },

  getAllTestScenarios: async (): Promise<TestScenarioResult[]> => {
    const res = await fetch(`${API_BASE}/scenarios/all`);
    return res.json();
  },

  getSingleTestScenario: async (scenarioId: string): Promise<TestScenarioResult> => {
    const res = await fetch(`${API_BASE}/scenarios/${scenarioId}`);
    return res.json();
  },

  getPdfReportUrl: (batchId: string = "BATCH-0245") => {
    return `${API_BASE}/reports/pdf?batch_id=${encodeURIComponent(batchId)}`;
  }
};
