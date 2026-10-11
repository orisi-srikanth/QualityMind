import React, { useState } from "react";
import { Sparkles, Download, MoreHorizontal, FileText, UserCheck } from "lucide-react";
import { api } from "../api";

interface Props {
  activePage: string;
  onRunPipeline: () => void;
  isRunningPipeline: boolean;
  onNavigate?: (page: string) => void;
  userRole?: "admin" | "quality_engineer" | "operator";
  onRoleChange?: (role: "admin" | "quality_engineer" | "operator") => void;
}

export const Header: React.FC<Props> = ({
  activePage,
  onRunPipeline,
  isRunningPipeline,
  onNavigate,
  userRole = "quality_engineer",
  onRoleChange
}) => {
  const [showMoreMenu, setShowMoreMenu] = useState(false);

  const getPageInfo = (page: string) => {
    switch (page) {
      case "dashboard":
        return { title: "Quality Dashboard", purpose: "Overall manufacturing quality status" };
      case "product-config":
        return { title: "Product Configuration", purpose: "Manage products, tolerances, and specification limits" };
      case "batches":
        return { title: "Production Batches", purpose: "Create, track and review production batches with full traceability" };
      case "inspection":
        return { title: "Inspection Center", purpose: "Measurement intake, data validation, and specification conformance" };
      case "visual-inspection":
        return { title: "Visual Inspection", purpose: "Automated defect localization and quality review" };
      case "process-monitoring":
        return { title: "Process Monitoring", purpose: "Real-time machine telemetry and anomaly detection" };
      case "spc-dashboard":
        return { title: "SPC Dashboard", purpose: "Control charts and process capability analysis" };
      case "incidents":
        return { title: "Quality Incidents", purpose: "Manage detected quality deviations and containment" };
      case "rca":
        return { title: "Root Cause Analysis", purpose: "Structured failure mode and root cause investigation" };
      case "capa":
        return { title: "CAPA Management", purpose: "Track corrective and preventive action workflows" };
      case "ai-review":
        return { title: "AI Review Center", purpose: "Automated analysis audit and human disposition sign-off" };
      case "reports":
        return { title: "Reports", purpose: "Generate and export official quality compliance dossiers" };
      case "test-scenarios":
        return { title: "Test Scenarios", purpose: "Automated end-to-end quality validation test suite" };
      default:
        return { title: "Quality Minds", purpose: "Industrial Decision Support" };
    }
  };

  const pageInfo = getPageInfo(activePage);

  return (
    <header className="bg-white border-b border-[#E3E8EF] sticky top-0 z-30 px-7 py-3.5">
      <div className="flex items-center justify-between gap-4">
        {/* Left: Page Title & Subtitle */}
        <div className="min-w-0">
          <div className="flex items-baseline gap-3 flex-wrap">
            <h1 className="text-[24px] font-bold text-[#101828] tracking-tight leading-tight whitespace-nowrap">
              {pageInfo.title}
            </h1>
            <span className="text-[13.5px] text-[#475467] font-normal hidden sm:inline truncate">
              — {pageInfo.purpose}
            </span>
          </div>
        </div>

        {/* Right: Persona Switcher + Primary action button + Overflow */}
        <div className="flex items-center gap-3 shrink-0">
          {/* Persona Switcher */}
          <div className="flex items-center gap-2 bg-[#F4F6FA] border border-[#E3E8EF] rounded-lg px-2.5 py-1.5 shadow-2xs">
            <UserCheck className="w-3.5 h-3.5 text-blue-600 shrink-0" />
            <span className="text-[11.5px] font-semibold text-slate-500 uppercase tracking-wider">Role:</span>
            <select
              value={userRole}
              onChange={(e) => onRoleChange?.(e.target.value as any)}
              className="bg-transparent text-[13px] font-bold text-slate-800 focus:outline-hidden cursor-pointer"
            >
              <option value="quality_engineer">Quality Engineer</option>
              <option value="operator">Operator (Read-Only)</option>
              <option value="admin">Administrator</option>
            </select>
          </div>

          {activePage === "batches" && (
            <button
              onClick={onRunPipeline}
              disabled={isRunningPipeline}
              title="Runs the complete AI review for the selected batches"
              className={`inline-flex items-center gap-2 px-4 h-[38px] rounded-[8px] text-[14px] font-semibold transition-all duration-150 cursor-pointer shadow-xs whitespace-nowrap ${
                isRunningPipeline
                  ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                  : "bg-[#2563EB] hover:bg-[#1D4ED8] text-white active:bg-[#1E40AF]"
              }`}
            >
              <Sparkles className={`w-4 h-4 ${isRunningPipeline ? "animate-spin text-blue-400" : ""}`} />
              <span>{isRunningPipeline ? "Analyzing..." : "Run Full Analysis"}</span>
            </button>
          )}

          {/* Small overflow menu for secondary actions */}
          <div className="relative">
            <button
              onClick={() => setShowMoreMenu(!showMoreMenu)}
              title="More actions"
              className="w-[36px] h-[36px] rounded-[8px] border border-[#D0D5DD] bg-white hover:bg-[#F3F6FA] text-[#475467] flex items-center justify-center cursor-pointer transition-colors"
            >
              <MoreHorizontal className="w-4 h-4" />
            </button>

            {showMoreMenu && (
              <div
                className="absolute right-0 mt-1 w-56 bg-white border border-[#E3E8EF] rounded-[8px] shadow-lg py-1 z-50 animate-in fade-in"
                onMouseLeave={() => setShowMoreMenu(false)}
              >
                <a
                  href={api.getPdfReportUrl("BATCH-0245")}
                  download="Quality_Audit_Report_BATCH-0245.pdf"
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-2 px-3 py-2 text-[13px] text-[#101828] hover:bg-[#F3F6FA] cursor-pointer"
                  onClick={() => setShowMoreMenu(false)}
                >
                  <Download className="w-4 h-4 text-[#475467]" />
                  <span>Download Audit PDF</span>
                </a>
                {onNavigate && (
                  <button
                    onClick={() => {
                      onNavigate("reports");
                      setShowMoreMenu(false);
                    }}
                    className="w-full text-left flex items-center gap-2 px-3 py-2 text-[13px] text-[#101828] hover:bg-[#F3F6FA] cursor-pointer"
                  >
                    <FileText className="w-4 h-4 text-[#475467]" />
                    <span>Go to Reports</span>
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
