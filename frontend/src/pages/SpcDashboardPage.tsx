import React, { useEffect, useState } from "react";
import { api } from "../api";
import { SPCReport } from "../types";
import { CertaintyBadge } from "../components/CertaintyBadge";
import {
  LineChart as LineChartIcon, AlertTriangle, CheckCircle2,
  Info, TrendingDown, Gauge, RefreshCw, AlertCircle
} from "lucide-react";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ReferenceLine
} from "recharts";

export const SpcDashboardPage: React.FC = () => {
  const [report, setReport] = useState<SPCReport | null>(null);
  const [loading, setLoading] = useState(true);

  const loadSpc = () => {
    setLoading(true);
    api.getSpcAnalysis("BATCH-0245").then((res) => {
      setReport(res.report);
      setLoading(false);
    });
  };

  useEffect(() => {
    loadSpc();
  }, []);

  if (loading || !report) {
    return <div className="p-8 text-center text-slate-500">Loading SPC Calculations...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">Statistical Process Control (SPC) & Capability Analysis</h2>
          <p className="text-xs text-slate-500">
            Control limits (UCL/LCL), Nelson Rule violation checks, and capability indices (Cp, Cpk, Pp, Ppk).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadSpc}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg text-xs font-semibold cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Recalculate SPC</span>
          </button>
        </div>
      </div>

      {/* Mandatory Distinction Warning Banner */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl space-y-1">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-blue-700 shrink-0" />
          <span className="text-xs font-bold text-blue-900 uppercase tracking-wider">
            Mandatory Engineering Distinction: Spec Limits vs Statistical Control Limits
          </span>
          <CertaintyBadge level="Statistical Finding" />
        </div>
        <p className="text-xs text-blue-800 leading-relaxed">
          {report.distinction_warning}
        </p>
      </div>

      {/* Process Capability Indices Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
          <span className="text-xs text-slate-500 font-medium block">Process Potential (Cp)</span>
          <span className="text-2xl font-bold text-slate-900 font-mono">{report.cp.toFixed(2)}</span>
          <span className="text-[10px] text-slate-400 block mt-1">Tolerance / 6&sigma; (Target &ge; 1.33)</span>
        </div>

        <div className="p-4 bg-white border border-rose-200 rounded-xl shadow-xs bg-rose-50/20">
          <span className="text-xs text-rose-700 font-medium block">Centering Capability (Cpk)</span>
          <span className="text-2xl font-bold text-rose-700 font-mono">{report.cpk.toFixed(2)}</span>
          <span className="text-[10px] text-rose-600 font-semibold block mt-1">
            CRITICAL: Negative Cpk (Process mean shifted beyond USL)
          </span>
        </div>

        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
          <span className="text-xs text-slate-500 font-medium block">Process Performance (Pp)</span>
          <span className="text-2xl font-bold text-slate-900 font-mono">{report.pp.toFixed(2)}</span>
          <span className="text-[10px] text-slate-400 block mt-1">Total process variation</span>
        </div>

        <div className="p-4 bg-white border border-rose-200 rounded-xl shadow-xs bg-rose-50/20">
          <span className="text-xs text-rose-700 font-medium block">Performance Index (Ppk)</span>
          <span className="text-2xl font-bold text-rose-700 font-mono">{report.ppk.toFixed(2)}</span>
          <span className="text-[10px] text-rose-600 block mt-1">Target &ge; 1.33</span>
        </div>
      </div>

      {/* Control Chart Card */}
      <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              Individuals Control Chart (I-Chart) with Engineering vs Control Boundaries
            </h3>
            <p className="text-xs text-slate-500">
              Center Line (CL) = {report.cl.toFixed(4)} mm | Natural 3-Sigma Limits = [{report.lcl.toFixed(4)}, {report.ucl.toFixed(4)}] mm
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-0.5 bg-red-600 inline-block" />
              <strong className="text-slate-700">Spec Limits (USL/LSL)</strong>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-0.5 bg-purple-600 border-dashed inline-block" />
              <strong className="text-slate-700">Control Limits (UCL/LCL)</strong>
            </span>
          </div>
        </div>

        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={report.chart_data} margin={{ top: 15, right: 30, left: 20, bottom: 15 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="sample_id" tick={{ fontSize: 11 }} />
              <YAxis domain={[49.92, 50.10]} tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(val: any) => [`${val} mm`, "Shaft Diameter"]}
                contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", fontSize: "12px", borderRadius: "8px" }}
              />

              {/* Engineering Specification Limits (Solid Red) */}
              <ReferenceLine y={report.usl} label="USL (50.05 mm)" stroke="#dc2626" strokeWidth={1.5} />
              <ReferenceLine y={report.lsl} label="LSL (49.95 mm)" stroke="#dc2626" strokeWidth={1.5} />

              {/* Statistical Control Limits (Dashed Purple) */}
              <ReferenceLine y={report.ucl} label={`UCL (${report.ucl.toFixed(3)} mm)`} stroke="#9333ea" strokeDasharray="4 4" strokeWidth={1.5} />
              <ReferenceLine y={report.lcl} label={`LCL (${report.lcl.toFixed(3)} mm)`} stroke="#9333ea" strokeDasharray="4 4" strokeWidth={1.5} />
              <ReferenceLine y={report.cl} label={`CL (${report.cl.toFixed(3)} mm)`} stroke="#2563eb" strokeDasharray="2 2" strokeWidth={1} />

              <Line
                type="linear"
                dataKey="value"
                stroke="#0f172a"
                strokeWidth={2}
                dot={(props: any) => {
                  const { cx, cy, payload } = props;
                  const isFail = payload.is_out_of_spec || payload.is_out_of_control;
                  return (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={isFail ? 5 : 3.5}
                      fill={isFail ? "#ef4444" : "#2563eb"}
                      stroke="#ffffff"
                      strokeWidth={1.5}
                      key={props.key}
                    />
                  );
                }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Nelson Rules Violation Register */}
      <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <h3 className="text-sm font-bold text-slate-900">
              Nelson Rules Process Stability Audit ({report.nelson_violations.length} Violations)
            </h3>
          </div>
          <CertaintyBadge level="Statistical Finding" />
        </div>

        <div className="space-y-2">
          {report.nelson_violations.map((v, i) => (
            <div key={i} className="p-3 bg-rose-50/50 border border-rose-200 rounded-lg flex items-start justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-rose-100 text-rose-800 text-xs font-bold font-mono">
                    Rule {v.rule_number}
                  </span>
                  <span className="text-xs font-bold text-slate-900">{v.rule_name}</span>
                </div>
                <p className="text-xs text-slate-600">{v.description}</p>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-100 text-rose-700 shrink-0">
                {v.severity} Severity
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
