import React, { useState } from "react";
import { api } from "../api";
import { FileText, Download, Printer, CheckCircle2, ShieldCheck, Check, Loader2 } from "lucide-react";

export const ReportsPage: React.FC = () => {
  const pdfUrl = api.getPdfReportUrl("BATCH-0245");
  const [generating, setGenerating] = useState(false);
  const [ready, setReady] = useState(false);

  const handleDownload = (e: React.MouseEvent) => {
    e.preventDefault();
    if (generating || ready) return;
    setGenerating(true);
    setTimeout(() => {
      setGenerating(false);
      setReady(true);
      setTimeout(() => {
        setReady(false);
        const link = document.createElement("a");
        link.href = pdfUrl;
        link.target = "_blank";
        link.rel = "noreferrer";
        link.download = "Quality_Audit_Report_BATCH-0245.pdf";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }, 1500);
    }, 1200);
  };

  const reportSections = [
    { num: 1, name: "Product Specifications", detail: "Nominal 50.00 mm, Bilateral Tolerance ±0.05 mm, Carbon Steel" },
    { num: 2, name: "Batch Information", detail: "Batch BATCH-0245, Quantity 500 pcs, Night Shift, CNC-04" },
    { num: 3, name: "Inspection Summary", detail: "5 samples tested, 3 nonconforming, 60.0% sample rejection rate" },
    { num: 4, name: "Visual Inspection Results", detail: "Automated vision detected surface scratch with 94.0% confidence" },
    { num: 5, name: "Dimensional Analysis", detail: "P004 measured at 50.08 mm (+0.03 mm beyond USL)" },
    { num: 6, name: "SPC Analysis", detail: "UCL=50.082, LCL=50.034, Cp=0.68, Cpk=-0.18" },
    { num: 7, name: "Process Monitoring", detail: "Spindle vibration spike 3.8 mm/s; Tool cycles 1,150 / 800" },
    { num: 8, name: "Root-Cause Analysis", detail: "Tool Flank Wear (88% confidence) & Spindle Harmonics (62%)" },
    { num: 9, name: "Supporting Evidence", detail: "1,150 cycles, gradual upward drift, historical match NCR-019" },
    { num: 10, name: "Containment Actions", detail: "Batch quarantine, micrometer calibration, spindle stop & inspection" },
    { num: 11, name: "Corrective Actions", detail: "Replace insert, revalidate offset, PLC 850-cycle lockout" },
    { num: 12, name: "Human Disposition Sign-off", detail: "Authorized by Lead Quality Engineer: Quarantine Disposition" },
    { num: 13, name: "Effectiveness Monitoring", detail: "Rejection rate reduction from 8.2% baseline to 1.1% verified" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-[26px] font-bold text-slate-900 leading-tight">Reports & Audit Dossiers</h2>
          <p className="text-[14px] text-slate-500 mt-1">
            Generate and download official quality inspection dossiers and audit summaries.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => window.print()}
            className="btn-secondary !h-[40px]"
          >
            <Printer className="w-4 h-4 text-slate-500" />
            <span>Print Dossier</span>
          </button>
          <button
            onClick={handleDownload}
            disabled={generating}
            className="btn-primary !h-[40px]"
          >
            {generating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Generating PDF...</span>
              </>
            ) : ready ? (
              <>
                <Check className="w-4 h-4 text-white" />
                <span>Ready</span>
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                <span>Download Audit PDF</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* PDF Download Action Banner */}
      <div className="p-5 bg-white border border-[#E3E8EF] rounded-xl shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="p-3 bg-[#EAF2FF] text-[#2563EB] rounded-lg shrink-0">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[16px] font-bold text-slate-900">
                Audit Dossier: QA-RPT-BATCH-0245.pdf
              </span>
              <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-bold">
                Ready for Export
              </span>
            </div>
            <p className="text-[13.5px] text-[#475467] mt-1 max-w-2xl">
              Complete dossier containing all 13 standard quality audit sections with statistical evaluations,
              visual inspection findings, process parameters, and human engineering sign-off.
            </p>
          </div>
        </div>

        <button
          onClick={handleDownload}
          disabled={generating}
          className="btn-primary !h-[42px] whitespace-nowrap shrink-0"
        >
          {generating ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Generating PDF...</span>
            </>
          ) : ready ? (
            <>
              <Check className="w-4 h-4 text-white" />
              <span>Ready</span>
            </>
          ) : (
            <>
              <span>Generate & Download PDF</span>
              <Download className="w-4 h-4" />
            </>
          )}
        </button>
      </div>

      {/* Audit Verification Checklist */}
      <div className="table-container">
        <div className="px-5 py-3.5 border-b border-[#E3E8EF] bg-[#F4F6FA] flex items-center justify-between">
          <span className="text-[15px] font-bold text-[#101828]">
            Audit Dossier Structure (13 Standard Sections)
          </span>
          <span className="text-[13px] font-semibold text-emerald-700 flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4" />
            <span>All Sections Validated</span>
          </span>
        </div>

        <div className="divide-y divide-[#EEF1F5]">
          {reportSections.map((sec) => (
            <div key={sec.num} className="p-3.5 hover:bg-[#F3F6FA] transition-colors flex items-center justify-between gap-4 text-[13.5px]">
              <div className="flex items-center gap-3">
                <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 font-mono font-bold flex items-center justify-center text-[12px] font-tabular shrink-0">
                  {sec.num}
                </span>
                <div>
                  <span className="font-semibold text-slate-900">{sec.name}</span>
                  <p className="text-[#475467] text-[12.5px] mt-0.5">{sec.detail}</p>
                </div>
              </div>
              <span className="status-pill success shrink-0">
                Validated
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
