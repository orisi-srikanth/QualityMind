import React, { useEffect, useState } from "react";
import { api } from "../api";
import { InspectionReport, MeasurementItem } from "../types";
import { CertaintyBadge } from "../components/CertaintyBadge";
import {
  Ruler, Upload, FileSpreadsheet, CheckCircle2, AlertTriangle,
  ArrowUpRight, ArrowDownRight, RefreshCw, BarChart2
} from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ReferenceLine, Cell
} from "recharts";

export const InspectionPage: React.FC = () => {
  const [report, setReport] = useState<InspectionReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [activeTab, setActiveTab] = useState<"table" | "distribution">("table");

  // Manual entry sample inputs matching assignment: P001..P005
  const defaultSamples = [
    { sample_id: "P001", measured_value: 50.01 },
    { sample_id: "P002", measured_value: 50.03 },
    { sample_id: "P003", measured_value: 50.06 },
    { sample_id: "P004", measured_value: 50.08 },
    { sample_id: "P005", measured_value: 50.07 },
  ];

  const loadBenchmark = () => {
    setLoading(true);
    api.evaluateMeasurements({
      batch_id: "BATCH-0245",
      measurements: defaultSamples,
    }).then((res) => {
      setReport(res.report);
      setLoading(false);
    });
  };

  useEffect(() => {
    loadBenchmark();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setUploading(true);
    try {
      const res = await api.uploadCsvInspection(e.target.files[0]);
      setReport(res.report);
    } catch (err) {
      alert("Failed to upload and parse CSV inspection file.");
    } finally {
      setUploading(false);
    }
  };

  if (loading || !report) {
    return <div className="p-8 text-center text-slate-500">Loading Inspection Data...</div>;
  }

  // Distribution histogram data
  const chartData = report.measurements.map((m) => ({
    sample_id: m.sample_id,
    measured: m.measured_value,
    usl: report.usl,
    lsl: report.lsl,
    nominal: report.nominal_mm,
    is_conforming: m.is_conforming,
    deviation: m.deviation_from_limit,
  }));

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">Dimensional Inspection Center</h2>
          <p className="text-xs text-slate-500">
            Deterministic tolerance checking against engineering limits (USL = {report.usl} mm, LSL = {report.lsl} mm).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-lg text-xs font-semibold cursor-pointer shadow-xs">
            <Upload className="w-3.5 h-3.5 text-slate-500" />
            <span>{uploading ? "Uploading..." : "Upload Inspection CSV"}</span>
            <input type="file" accept=".csv" onChange={handleFileUpload} className="hidden" />
          </label>
          <button
            onClick={loadBenchmark}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg text-xs font-semibold cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reset Benchmark</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Tiles */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
          <span className="text-xs text-slate-500 font-medium block">Total Inspected</span>
          <span className="text-2xl font-bold text-slate-900 font-mono">{report.total_inspected}</span>
          <span className="text-[10px] text-slate-400 block mt-1">Batch BATCH-0245</span>
        </div>

        <div className="p-4 bg-white border border-emerald-200 rounded-xl shadow-xs bg-emerald-50/20">
          <span className="text-xs text-emerald-700 font-medium block">Accepted (In-Spec)</span>
          <span className="text-2xl font-bold text-emerald-700 font-mono">{report.accepted}</span>
          <span className="text-[10px] text-emerald-600 block mt-1">
            {((report.accepted / report.total_inspected) * 100).toFixed(1)}% yield
          </span>
        </div>

        <div className="p-4 bg-white border border-rose-200 rounded-xl shadow-xs bg-rose-50/20">
          <span className="text-xs text-rose-700 font-medium block">Nonconforming (Out-of-Spec)</span>
          <span className="text-2xl font-bold text-rose-700 font-mono">{report.nonconforming}</span>
          <span className="text-[10px] text-rose-600 block mt-1">
            Exceeding USL boundary
          </span>
        </div>

        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
          <span className="text-xs text-slate-500 font-medium block">Rejection Rate</span>
          <span className="text-2xl font-bold text-rose-600 font-mono">{report.rejection_rate_percent}%</span>
          <span className="text-[10px] text-rose-500 block mt-1">Exceeds 2.0% threshold</span>
        </div>
      </div>

      {/* Main Table / Distribution Tab Box */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab("table")}
              className={`px-3 py-1 rounded-md text-xs font-semibold cursor-pointer transition-colors ${
                activeTab === "table" ? "bg-white text-blue-700 shadow-2xs border border-slate-200" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Measurements Table ({report.measurements.length})
            </button>
            <button
              onClick={() => setActiveTab("distribution")}
              className={`px-3 py-1 rounded-md text-xs font-semibold cursor-pointer transition-colors ${
                activeTab === "distribution" ? "bg-white text-blue-700 shadow-2xs border border-slate-200" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Distribution Chart
            </button>
          </div>
          <CertaintyBadge level="Observed Fact" />
        </div>

        {activeTab === "table" ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-4 py-3">Sample ID</th>
                  <th className="px-4 py-3">Measured Diameter</th>
                  <th className="px-4 py-3">Nominal (50.00 mm) Dev.</th>
                  <th className="px-4 py-3">Spec Limit (USL 50.05) Dev.</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Certainty Attribution</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {report.measurements.map((m) => (
                  <tr key={m.sample_id} className={`hover:bg-slate-50/80 transition-colors ${!m.is_conforming ? "bg-rose-50/30" : ""}`}>
                    <td className="px-4 py-3 font-mono font-bold text-slate-900">
                      {m.sample_id}
                    </td>
                    <td className="px-4 py-3 font-mono font-bold text-slate-900 text-sm">
                      {m.measured_value.toFixed(2)} mm
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-600">
                      {m.deviation_from_nominal > 0 ? `+${m.deviation_from_nominal.toFixed(2)}` : m.deviation_from_nominal.toFixed(2)} mm
                    </td>
                    <td className="px-4 py-3 font-mono">
                      {!m.is_conforming ? (
                        <span className="text-rose-600 font-bold">
                          +{m.deviation_from_limit.toFixed(2)} mm (OUT OF SPEC)
                        </span>
                      ) : (
                        <span className="text-slate-400">0.00 mm (Within Bounds)</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold ${
                        m.is_conforming
                          ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                          : "bg-rose-100 text-rose-800 border border-rose-300"
                      }`}>
                        {m.is_conforming ? <CheckCircle2 className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
                        <span>{m.status}</span>
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <CertaintyBadge level="Observed Fact" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-6">
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="sample_id" tick={{ fontSize: 12 }} />
                  <YAxis domain={[49.92, 50.10]} tick={{ fontSize: 11 }} />
                  <Tooltip
                    formatter={(val: any) => [`${val} mm`, "Diameter"]}
                    contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", fontSize: "12px", borderRadius: "8px" }}
                  />
                  <ReferenceLine y={report.usl} label="USL 50.05 mm" stroke="#dc2626" strokeDasharray="4 4" />
                  <ReferenceLine y={report.lsl} label="LSL 49.95 mm" stroke="#dc2626" strokeDasharray="4 4" />
                  <ReferenceLine y={report.nominal_mm} label="Nominal 50.00 mm" stroke="#16a34a" strokeDasharray="2 2" />
                  <Bar dataKey="measured" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.is_conforming ? "#3b82f6" : "#ef4444"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="text-xs text-slate-500 text-center mt-2">
              Red horizontal line indicates Upper Specification Limit (50.05 mm). Samples P003, P004, P005 clearly violate specification.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
