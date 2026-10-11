import React, { useEffect, useState } from "react";
import { api } from "../api";
import { CertaintyBadge } from "../components/CertaintyBadge";
import { AlertTriangle, CheckCircle, Clock, ArrowRight, ShieldAlert } from "lucide-react";

interface Props {
  onNavigate: (page: string) => void;
}

export const IncidentsPage: React.FC<Props> = ({ onNavigate }) => {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getIncidents().then((res) => {
      setIncidents(res);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading Quality Incidents...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-900">Non-Conformance Reports (NCR) Registry</h2>
          <p className="text-xs text-slate-500">
            Formal registry of active and historical manufacturing non-conformances with safety isolation.
          </p>
        </div>
        <CertaintyBadge level="Observed Fact" />
      </div>

      <div className="space-y-4">
        {incidents.map((inc) => {
          const isOpen = inc.status === "OPEN";
          return (
            <div
              key={inc.incident_id}
              className={`p-5 bg-white border rounded-xl shadow-xs space-y-4 ${
                isOpen ? "border-amber-300 ring-1 ring-amber-100" : "border-slate-200"
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${isOpen ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-800"}`}>
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-blue-600">{inc.incident_id}</span>
                      <span className="text-slate-300">&bull;</span>
                      <span className="font-mono text-xs text-slate-600">Batch {inc.batch_id}</span>
                      <span className="text-slate-300">&bull;</span>
                      <span className="text-xs text-slate-500">Machine: {inc.machine}</span>
                    </div>
                    <h3 className="text-base font-bold text-slate-900 mt-0.5">{inc.title}</h3>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                    isOpen ? "bg-rose-100 text-rose-800 border border-rose-200" : "bg-slate-100 text-slate-700"
                  }`}>
                    {inc.status}
                  </span>
                  <span className="px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700">
                    Severity: {inc.severity}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                <div className="p-3 bg-slate-50 rounded-lg">
                  <span className="text-slate-500 block">Containment Disposition</span>
                  <strong className="text-slate-900 font-semibold">{inc.impacted_quantity}</strong>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <span className="text-slate-500 block">Primary AI Hypothesis</span>
                  <strong className="text-amber-800 font-semibold">{inc.primary_hypothesis}</strong>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <span className="text-slate-500 block">Critic Audit Verdict</span>
                  <strong className="text-emerald-700 font-semibold">{inc.critic_verdict} (Verified)</strong>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                <span className="text-xs text-slate-400">Created: {inc.created_at} UTC</span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onNavigate("rca")}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs cursor-pointer flex items-center gap-1"
                  >
                    <span>View RCA Hypotheses</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => onNavigate("capa")}
                    className="px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-lg text-xs font-semibold shadow-xs cursor-pointer"
                  >
                    Manage CAPA
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
