import React, { useEffect, useState } from "react";
import { api } from "../api";
import { CAPAReport, ActionItem } from "../types";
import { CertaintyBadge } from "../components/CertaintyBadge";
import {
  ShieldCheck, CheckCircle2, Clock, AlertTriangle,
  TrendingDown, User, Calendar, FileCheck, ArrowRight
} from "lucide-react";

export const CapaPage: React.FC = () => {
  const [capa, setCapa] = useState<CAPAReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getCapaPlan().then((res) => {
      setCapa(res.capa);
      setLoading(false);
    });
  }, []);

  if (loading || !capa) {
    return <div className="p-8 text-center text-slate-500">Loading CAPA Framework...</div>;
  }

  const renderActionTier = (title: string, actions: ActionItem[], badgeColor: string) => (
    <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden space-y-0">
      <div className="px-5 py-3 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
        <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${badgeColor}`} />
          <span>{title} ({actions.length})</span>
        </span>
        <span className="text-[11px] text-slate-500">IATF 16949 Section 10.2</span>
      </div>

      <div className="divide-y divide-slate-100">
        {actions.map((act) => (
          <div key={act.action_id} className="p-4 hover:bg-slate-50/50 transition-colors space-y-2">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-blue-600">{act.action_id}</span>
                <span className="text-xs font-bold text-slate-900">{act.description}</span>
              </div>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold self-start sm:self-auto ${
                act.status === "APPROVED" ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
              }`}>
                {act.status}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs text-slate-600">
              <div className="flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-slate-400" />
                <span>Assigned: <strong>{act.assigned_role}</strong></span>
              </div>
              <div className="flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>Due Date: <strong>{act.due_date}</strong></span>
              </div>
              <div className="flex items-center gap-1.5">
                <FileCheck className="w-3.5 h-3.5 text-slate-400" />
                <span>Evidence: <em>{act.evidence_required}</em></span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">Corrective & Preventive Action (CAPA)</h2>
          <p className="text-xs text-slate-500">
            3-Tier quality improvement plan: Immediate Containment, Corrective Actions, and Long-Term Prevention.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-lg text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
            {capa.approval_status}
          </span>
          <CertaintyBadge level="Statistical Finding" />
        </div>
      </div>

      {/* Effectiveness Monitoring Highlight Card (Requirement 15) */}
      <div className="p-5 bg-emerald-50 border border-emerald-200 rounded-xl space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingDown className="w-5 h-5 text-emerald-700" />
            <h3 className="text-sm font-bold text-emerald-900 uppercase tracking-wider">
              Post-Implementation Effectiveness Monitoring (Requirement 15)
            </h3>
          </div>
          <CertaintyBadge level="Observed Fact" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-3 bg-white border border-emerald-200 rounded-lg">
            <span className="text-[10px] text-slate-500 uppercase block font-medium">Pre-Replacement Baseline</span>
            <span className="text-xl font-bold text-rose-600 font-mono">8.2%</span>
            <span className="text-[10px] text-slate-400 block mt-0.5">Worn tool (1,150 cycles)</span>
          </div>

          <div className="p-3 bg-white border border-emerald-200 rounded-lg">
            <span className="text-[10px] text-slate-500 uppercase block font-medium">Post-Replacement Verified</span>
            <span className="text-xl font-bold text-emerald-700 font-mono">1.1%</span>
            <span className="text-[10px] text-emerald-600 block mt-0.5">Fresh carbide insert & offset reset</span>
          </div>

          <div className="p-3 bg-white border border-emerald-200 rounded-lg">
            <span className="text-[10px] text-slate-500 uppercase block font-medium">Target Conformance</span>
            <span className="text-xl font-bold text-blue-700 font-mono">&lt; 1.5%</span>
            <span className="text-[10px] text-emerald-600 font-semibold block mt-0.5">Status: VERIFIED EFFECTIVE</span>
          </div>
        </div>

        <p className="text-xs text-emerald-800">
          {capa.effectiveness_result}
        </p>
      </div>

      {/* 3 Action Tiers */}
      <div className="space-y-4">
        {renderActionTier("1. Immediate Containment Actions", capa.containment_actions, "bg-rose-500")}
        {renderActionTier("2. Potential Corrective Actions", capa.corrective_actions, "bg-amber-500")}
        {renderActionTier("3. Long-Term Preventive Actions", capa.preventive_actions, "bg-blue-500")}
      </div>
    </div>
  );
};
