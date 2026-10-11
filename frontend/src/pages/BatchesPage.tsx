import React, { useEffect, useState } from "react";
import { api } from "../api";
import { ProductionBatch } from "../types";
import { CertaintyBadge } from "../components/CertaintyBadge";
import { Layers, AlertCircle, CheckCircle, Clock, Plus, ArrowRight, User } from "lucide-react";

interface Props {
  onNavigate: (page: string) => void;
}

export const BatchesPage: React.FC<Props> = ({ onNavigate }) => {
  const [batches, setBatches] = useState<ProductionBatch[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getBatches().then((res) => {
      setBatches(res);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading Production Batches...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-900">Production Batch Registry & Lot Traceability</h2>
          <p className="text-xs text-slate-500">
            End-to-end manufacturing lot tracking with material certificates and disposition status.
          </p>
        </div>
        <CertaintyBadge level="Observed Fact" />
      </div>

      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        <div className="px-5 py-3.5 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-slate-600" />
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Active Production Batches ({batches.length})
            </span>
          </div>
          <span className="text-xs text-slate-500">Plant: Machining Cell 04</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[10px] tracking-wider">
              <tr>
                <th className="px-4 py-3">Batch ID</th>
                <th className="px-4 py-3">Part Number</th>
                <th className="px-4 py-3">Machine</th>
                <th className="px-4 py-3">Shift & Operator</th>
                <th className="px-4 py-3">Material Lot</th>
                <th className="px-4 py-3">Quantity</th>
                <th className="px-4 py-3">Quality Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {batches.map((b) => {
                const isHold = b.status === "QUALITY_HOLD";
                return (
                  <tr key={b.batch_id} className={`hover:bg-slate-50/80 transition-colors ${isHold ? "bg-amber-50/20" : ""}`}>
                    <td className="px-4 py-3 font-mono font-bold text-blue-600">
                      {b.batch_id}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-900">
                      {b.part_number}
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      <span className="px-2 py-0.5 rounded bg-slate-100 font-mono text-[11px]">
                        {b.machine}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-700">
                      <div>{b.shift}</div>
                      <div className="text-[10px] text-slate-400 flex items-center gap-1 mt-0.5">
                        <User className="w-2.5 h-2.5" />
                        <span>{b.operator}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono text-[11px] text-slate-600">
                      {b.material_lot}
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-800">
                      {b.quantity} pcs
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold ${
                        isHold
                          ? "bg-rose-100 text-rose-800 border border-rose-300"
                          : "bg-emerald-100 text-emerald-800 border border-emerald-300"
                      }`}>
                        {isHold ? <AlertCircle className="w-3 h-3" /> : <CheckCircle className="w-3 h-3" />}
                        <span>{b.status}</span>
                      </span>
                      {b.rejection_rate && (
                        <div className="text-[10px] text-slate-500 mt-0.5">Rejection: {b.rejection_rate}</div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => onNavigate("inspection")}
                        className="px-2.5 py-1 bg-white hover:bg-slate-50 text-blue-600 border border-slate-200 rounded text-xs font-semibold cursor-pointer shadow-2xs"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
