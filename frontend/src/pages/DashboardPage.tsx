import React, { useEffect, useState } from "react";
import { api } from "../api";
import { CertaintyBadge } from "../components/CertaintyBadge";
import {
  Activity, AlertTriangle, CheckCircle2, ShieldCheck,
  TrendingDown, TrendingUp, Cpu, Wrench, ArrowRight, Sparkles
} from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell
} from "recharts";

interface Props {
  onNavigate: (page: string) => void;
  onRunPipeline: () => void;
}

export const DashboardPage: React.FC<Props> = ({ onNavigate, onRunPipeline }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDashboardSummary().then((res) => {
      setData(res);
      setLoading(false);
    });
  }, []);

  if (loading || !data) {
    return (
      <div className="p-8 flex items-center justify-center text-slate-500">
        <Activity className="w-5 h-5 animate-spin mr-2 text-blue-600" />
        Loading Executive Dashboard...
      </div>
    );
  }

  const kpis = [
    {
      label: "Acceptance Rate",
      value: `${data.acceptance_rate_percent}%`,
      sub: "Target: >= 98.0%",
      status: "warning",
      certainty: "Observed Fact",
      icon: CheckCircle2,
      color: "text-emerald-600 bg-emerald-50"
    },
    {
      label: "Rejection Rate",
      value: `${data.rejection_rate_percent}%`,
      sub: "Batch BATCH-0245 held",
      status: "danger",
      certainty: "Observed Fact",
      icon: AlertTriangle,
      color: "text-rose-600 bg-rose-50"
    },
    {
      label: "Active Machine Anomalies",
      value: `${data.machine_anomalies_detected}`,
      sub: "CNC-04 Spindle Vibration 3.8 mm/s",
      status: "danger",
      certainty: "Statistical Finding",
      icon: Activity,
      color: "text-amber-600 bg-amber-50"
    },
    {
      label: "Process Centering (Cpk)",
      value: `${data.spc_status.process_capability_cpk}`,
      sub: "Incapable (Mean shifted high)",
      status: "danger",
      certainty: "Statistical Finding",
      icon: TrendingDown,
      color: "text-blue-600 bg-blue-50"
    }
  ];

  return (
    <div className="space-y-6">
      {/* Critical Incident Alert Banner */}
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-amber-100 text-amber-800 rounded-lg shrink-0">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-amber-900">
                ACTIVE QUALITY HOLD: Batch BATCH-0245 (Precision Shaft PS-2026-101)
              </span>
              <CertaintyBadge level="Observed Fact" />
            </div>
            <p className="text-xs text-amber-800 mt-0.5">
              Dimensional inspection flagged 3 nonconforming components exceeding USL (50.05 mm) with max diameter 50.08 mm (+0.03 mm deviation).
              Telemetry detected tool usage at 1,150 cycles and machine vibration spike to 3.8 mm/s.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={onRunPipeline}
            className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5 cursor-pointer transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Load Demo Scenario</span>
          </button>
          <button
            onClick={() => onNavigate("rca")}
            className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-semibold shadow-xs cursor-pointer"
          >
            Investigate Root Cause
          </button>
          <button
            onClick={() => onNavigate("ai-review")}
            className="px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-lg text-xs font-semibold shadow-xs cursor-pointer"
          >
            Review AI Audit
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div key={idx} className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">{kpi.label}</span>
                <div className={`p-1.5 rounded-lg ${kpi.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-bold text-slate-900 tracking-tight">{kpi.value}</span>
                <CertaintyBadge level={kpi.certainty} showIcon={false} />
              </div>
              <div className="text-[11px] text-slate-500 pt-1 border-t border-slate-100 flex items-center justify-between">
                <span>{kpi.sub}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Two-Column Middle Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Machine Status & Telemetry Card */}
        <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-slate-600" />
              <h2 className="text-sm font-bold text-slate-900">Machine Cell Health (CNC-04)</h2>
            </div>
            <span className="px-2 py-0.5 rounded text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
              {data.primary_machine_status.status}
            </span>
          </div>

          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs font-medium mb-1">
                <span className="text-slate-600">Cutting Tool Usage Cycles</span>
                <span className="text-rose-600 font-bold">
                  {data.primary_machine_status.tool_cycles} / {data.primary_machine_status.tool_cycle_limit} cycles (+43%)
                </span>
              </div>
              <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-rose-500 rounded-full" style={{ width: "100%" }} />
              </div>
              <p className="text-[10px] text-slate-400 mt-0.5">Threshold: 800 cycles | Severe flank wear risk</p>
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium mb-1">
                <span className="text-slate-600">Machine Vibration Amplitude</span>
                <span className="text-rose-600 font-bold">
                  {data.primary_machine_status.vibration_mms} mm/s (Trip: 3.5 mm/s)
                </span>
              </div>
              <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-rose-500 rounded-full" style={{ width: "95%" }} />
              </div>
              <p className="text-[10px] text-slate-400 mt-0.5">Baseline: 2.1 mm/s (+81% elevation)</p>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
            <span className="text-xs text-slate-500">Overall Cell Health Index</span>
            <span className="text-sm font-bold text-slate-800">{data.primary_machine_status.health_index}</span>
          </div>

          <button
            onClick={() => onNavigate("process-monitoring")}
            className="w-full py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-lg text-xs font-medium flex items-center justify-center gap-1 cursor-pointer transition-colors"
          >
            <span>Inspect Live Machine Telemetry</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Top Defect Pareto Distribution */}
        <div className="lg:col-span-2 p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Pareto Defect Distribution</h2>
              <p className="text-xs text-slate-500">Rejection root categories by frequency across active run</p>
            </div>
            <CertaintyBadge level="Observed Fact" />
          </div>

          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.top_defect_categories} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis dataKey="defect" type="category" tick={{ fontSize: 11, width: 140 }} width={140} />
                <Tooltip
                  formatter={(value: any) => [`${value} incidents`, "Frequency"]}
                  contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", fontSize: "12px", borderRadius: "8px" }}
                />
                <Bar dataKey="count" fill="#2563eb" radius={[0, 4, 4, 0]}>
                  {data.top_defect_categories.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={index === 0 ? "#dc2626" : index === 1 ? "#f59e0b" : "#3b82f6"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Primary 80% contributor: Dimensional diameter expansion (+0.03 mm)</span>
            <button
              onClick={() => onNavigate("inspection")}
              className="text-blue-600 font-semibold hover:underline flex items-center gap-1 cursor-pointer"
            >
              <span>View Measurement Log</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      {/* 8-Agent Pipeline Architecture Status */}
      <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Multi-Agent Quality Orchestration Network</h2>
            <p className="text-xs text-slate-500">Autonomous inspection, anomaly detection, RCA, and CAPA decision-support</p>
          </div>
          <button
            onClick={() => onNavigate("ai-review")}
            className="text-xs text-blue-600 font-semibold hover:underline flex items-center gap-1 cursor-pointer"
          >
            <span>View Full Agent Execution Trace</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { num: "1", name: "Data Intake", role: "Normalize Units & CSV/Excel", cert: "Observed Fact", status: "Active" },
            { num: "2", name: "Visual Quality", role: "PyTorch CV BBox & Defect Detection", cert: "Model Prediction", status: "Active" },
            { num: "3", name: "Specification Compliance", role: "Deterministic USL/LSL Deviation", cert: "Observed Fact", status: "Active" },
            { num: "4", name: "Process Monitoring", role: "Isolation Forest Anomaly & Drift", cert: "Statistical Finding", status: "Alert" },
            { num: "5", name: "Statistical Process Control", role: "Nelson Rules, I-MR, Cp/Cpk", cert: "Statistical Finding", status: "Active" },
            { num: "6", name: "Root Cause (RCA)", role: "5-Whys, 6M Fishbone & RAG Search", cert: "Hypothesis", status: "Active" },
            { num: "7", name: "CAPA Management", role: "Containment, Corrective, Preventive", cert: "Statistical Finding", status: "Active" },
            { num: "8", name: "Quality Critic", role: "Safety Verification & HITL Gate", cert: "Statistical Finding", status: "Gatekeeper" },
          ].map((agent, i) => (
            <div key={i} className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-blue-600 uppercase">Agent {agent.num}</span>
                <span className={`text-[9px] font-bold px-1.5 py-0.2 rounded ${agent.status === "Alert" ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-800"}`}>
                  {agent.status}
                </span>
              </div>
              <div className="text-xs font-bold text-slate-800">{agent.name}</div>
              <p className="text-[11px] text-slate-500 leading-tight">{agent.role}</p>
              <div className="pt-1">
                <CertaintyBadge level={agent.cert} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
