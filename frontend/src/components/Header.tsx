import React from "react";
import { CertaintyBadge } from "./CertaintyBadge";
import { Activity, ShieldAlert, Cpu, Download, Sparkles, CheckCircle2 } from "lucide-react";
import { api } from "../api";

interface Props {
  activePage: string;
  onRunPipeline: () => void;
  isRunningPipeline: boolean;
}

export const Header: React.FC<Props> = ({ activePage, onRunPipeline, isRunningPipeline }) => {
  const getPageTitle = (page: string) => {
    switch (page) {
      case "dashboard": return "Quality Executive Dashboard";
      case "product-config": return "Product & Specification Configuration";
      case "batches": return "Production Batch Operations";
      case "inspection": return "Dimensional Inspection Center";
      case "visual-inspection": return "Computer Vision Defect Inspection";
      case "process-monitoring": return "Machine Telemetry & Anomaly Detection";
      case "spc-dashboard": return "Statistical Process Control (SPC) & Capability";
      case "incidents": return "Quality Non-Conformance Reports (NCR)";
      case "rca": return "Root Cause Analysis (5-Whys, Fishbone & RAG)";
      case "capa": return "CAPA Framework & Effectiveness Tracking";
      case "ai-review": return "AI Agent Review & Human-in-the-Loop Gate";
      case "reports": return "Audit Dossier & Quality Reports";
      case "test-scenarios": return "Mandated Scenario Evaluation Suite (TC-01..08)";
      default: return "Quality Intelligence Platform";
    }
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 px-6 py-3.5">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-slate-500 uppercase tracking-wider">
            <span>Plant 01</span>
            <span>/</span>
            <span>Precision Machining Cell CNC-04</span>
            <span>/</span>
            <span className="text-blue-600 font-semibold">{activePage}</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight mt-0.5">
            {getPageTitle(activePage)}
          </h1>
        </div>

        {/* Legend for 5 Certainty Levels & Action Controls */}
        <div className="flex items-center flex-wrap gap-2.5">
          <div className="hidden xl:flex items-center gap-1.5 px-3 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs">
            <span className="text-slate-500 font-medium mr-1">Certainty Legend:</span>
            <CertaintyBadge level="Observed Fact" showIcon={false} />
            <CertaintyBadge level="Model Prediction" showIcon={false} />
            <CertaintyBadge level="Statistical Finding" showIcon={false} />
            <CertaintyBadge level="Hypothesis" showIcon={false} />
            <CertaintyBadge level="Confirmed Root Cause" showIcon={false} />
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onRunPipeline}
              disabled={isRunningPipeline}
              className={`inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold shadow-xs transition-all ${
                isRunningPipeline
                  ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700 text-white cursor-pointer"
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              {isRunningPipeline ? "Agents Orchestrating..." : "Execute 8-Agent Pipeline"}
            </button>

            <a
              href={api.getPdfReportUrl("BATCH-0245")}
              download="Quality_Audit_Report_BATCH-0245.pdf"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-lg text-xs font-semibold shadow-xs transition-all cursor-pointer"
            >
              <Download className="w-3.5 h-3.5 text-slate-500" />
              Download Audit PDF
            </a>
          </div>
        </div>
      </div>
    </header>
  );
};
