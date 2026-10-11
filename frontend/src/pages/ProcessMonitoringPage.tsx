import React, { useEffect, useState } from "react";
import { api } from "../api";
import { ProcessMonitoringReport, TelemetryDataPoint } from "../types";
import { CertaintyBadge } from "../components/CertaintyBadge";
import {
  Activity, AlertTriangle, TrendingUp, Cpu, Gauge, RefreshCw, Zap
} from "lucide-react";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ReferenceLine
} from "recharts";

export const ProcessMonitoringPage: React.FC = () => {
  const [report, setReport] = useState<ProcessMonitoringReport | null>(null);
  const [dataPoints, setDataPoints] = useState<TelemetryDataPoint[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = () => {
    setLoading(true);
    api.getTelemetry("BATCH-0245").then((res) => {
      setReport(res.report);
      setDataPoints(res.data_points);
      setLoading(false);
    });
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading || !report) {
    return <div className="p-8 text-center text-slate-500">Loading Telemetry & Anomaly Analysis...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">Process Monitoring & Machine Telemetry</h2>
          <p className="text-xs text-slate-500">
            Real-time IoT telemetry, baseline monitoring, and Scikit-Learn Isolation Forest anomaly detection.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg text-xs font-semibold cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh Telemetry Stream</span>
          </button>
        </div>
      </div>

      {/* Anomaly Callout Banner */}
      <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-3">
        <div className="p-2 bg-rose-100 text-rose-700 rounded-lg shrink-0 mt-0.5">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-rose-900">
              MULTIPLE CRITICAL ANOMALIES DETECTED ON CNC-04
            </span>
            <CertaintyBadge level="Statistical Finding" />
          </div>
          <p className="text-xs text-rose-800">
            1. <strong>Spindle Vibration:</strong> Rose from baseline 2.1 mm/s to 3.8 mm/s (Trip limit: 3.5 mm/s, +81% elevation).<br />
            2. <strong>Cutting Tool Usage:</strong> Reached 1,150 cycles (nominal threshold: 600 cycles, lockout: 800 cycles).<br />
            3. <strong>Isolation Forest Anomaly Score:</strong> -0.32 (Negative value confirms multi-parameter statistical outlier).
          </p>
        </div>
      </div>

      {/* Parameter Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 bg-white border border-rose-200 rounded-xl shadow-xs bg-rose-50/20">
          <span className="text-xs text-slate-500 font-medium block">Machine Vibration</span>
          <span className="text-2xl font-bold text-rose-700 font-mono">
            {report.vibration_current.toFixed(1)} mm/s
          </span>
          <span className="text-[10px] text-rose-600 font-semibold block mt-1">
            Baseline: {report.vibration_baseline} mm/s (CRITICAL)
          </span>
        </div>

        <div className="p-4 bg-white border border-rose-200 rounded-xl shadow-xs bg-rose-50/20">
          <span className="text-xs text-slate-500 font-medium block">Tool Cycle Count</span>
          <span className="text-2xl font-bold text-rose-700 font-mono">
            {report.tool_cycles_current}
          </span>
          <span className="text-[10px] text-rose-600 font-semibold block mt-1">
            Baseline limit: {report.tool_cycles_baseline} cycles (EXCEEDED)
          </span>
        </div>

        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
          <span className="text-xs text-slate-500 font-medium block">Coolant Temperature</span>
          <span className="text-2xl font-bold text-slate-900 font-mono">
            {report.temperature_current.toFixed(1)} &deg;C
          </span>
          <span className="text-[10px] text-slate-500 block mt-1">
            Baseline: {report.temperature_baseline} &deg;C (+1.0 &deg;C drift)
          </span>
        </div>

        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs">
          <span className="text-xs text-slate-500 font-medium block">Spindle Speed & Feed</span>
          <span className="text-2xl font-bold text-slate-900 font-mono">
            1,200 RPM
          </span>
          <span className="text-[10px] text-emerald-600 block mt-1 font-semibold">
            Feed: 0.20 mm/rev (Normal)
          </span>
        </div>
      </div>

      {/* Two Telemetry Trend Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Vibration vs Trip Threshold */}
        <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Machine Vibration Amplitude Over Batch Time</h3>
              <p className="text-xs text-slate-500">Trip limit: 3.5 mm/s | Baseline: 2.1 mm/s</p>
            </div>
            <CertaintyBadge level="Statistical Finding" />
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dataPoints} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} />
                <YAxis domain={[1.5, 4.5]} tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(val: any) => [`${val} mm/s`, "Vibration"]}
                  contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", fontSize: "12px", borderRadius: "8px" }}
                />
                <ReferenceLine y={3.5} label="Trip Limit 3.5 mm/s" stroke="#dc2626" strokeDasharray="4 4" />
                <ReferenceLine y={2.1} label="Baseline 2.1 mm/s" stroke="#16a34a" strokeDasharray="2 2" />
                <Line
                  type="monotone"
                  dataKey="machine_vibration_mms"
                  stroke="#ef4444"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: "#ef4444" }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Tool Usage Cycles vs Limit */}
        <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Cutting Tool Cycle Count Accumulation</h3>
              <p className="text-xs text-slate-500">Max limit: 800 cycles | Current: 1,150 cycles</p>
            </div>
            <CertaintyBadge level="Observed Fact" />
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dataPoints} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} />
                <YAxis domain={[500, 1300]} tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(val: any) => [`${val} cycles`, "Tool Cycles"]}
                  contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", fontSize: "12px", borderRadius: "8px" }}
                />
                <ReferenceLine y={800} label="Safe Limit 800 cycles" stroke="#dc2626" strokeDasharray="4 4" />
                <ReferenceLine y={600} label="Nominal 600 cycles" stroke="#16a34a" strokeDasharray="2 2" />
                <Line
                  type="monotone"
                  dataKey="tool_usage_cycles"
                  stroke="#3b82f6"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: "#3b82f6" }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
