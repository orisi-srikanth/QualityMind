import React, { useEffect, useState } from "react";
import { api } from "../api";
import { RCAReport, HypothesisEvidence, HistoricalIncident } from "../types";
import { CertaintyBadge } from "../components/CertaintyBadge";
import {
  GitFork, HelpCircle, ShieldCheck, Database, Search,
  CheckCircle2, XCircle, AlertTriangle, Layers, BookOpen, ArrowRight
} from "lucide-react";

export const RcaPage: React.FC = () => {
  const [report, setReport] = useState<RCAReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"hypotheses" | "five_whys" | "fishbone" | "rag">("hypotheses");
  const [ragQuery, setRagQuery] = useState("Oversized shaft diameter tool wear CNC-04");
  const [ragResults, setRagResults] = useState<HistoricalIncident[]>([]);
  const [searchingRag, setSearchingRag] = useState(false);

  useEffect(() => {
    api.getRcaAnalysis().then((res) => {
      setReport(res.report);
      setRagResults(res.report.historical_matches);
      setLoading(false);
    });
  }, []);

  const handleRagSearch = async () => {
    setSearchingRag(true);
    try {
      const res = await api.searchHistoricalIncidents(ragQuery);
      setRagResults(res.matches);
    } catch (e) {
      console.error(e);
    } finally {
      setSearchingRag(false);
    }
  };

  if (loading || !report) {
    return <div className="p-8 text-center text-slate-500">Loading Root Cause Analysis...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">Root Cause Analysis (RCA) Decision Engine</h2>
          <p className="text-xs text-slate-500">
            Systematic investigation using 5-Whys, Ishikawa 6M, Evidence Weighting, and Vector RAG Retrieval.
          </p>
        </div>
        <CertaintyBadge level="Hypothesis" />
      </div>

      {/* Mandatory Safety Notice: Correlation vs Causation */}
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
        <div className="space-y-0.5 text-xs text-amber-900">
          <span className="font-bold block uppercase tracking-wider">
            Mandatory Engineering Caution: Correlation &ne; Proven Causation
          </span>
          <p>{report.correlation_vs_causation_note}</p>
        </div>
      </div>

      {/* Tabs Bar */}
      <div className="border-b border-slate-200 flex items-center gap-4 text-xs font-semibold">
        {[
          { id: "hypotheses", label: `Evidence-Ranked Hypotheses (${report.ranked_hypotheses.length})` },
          { id: "five_whys", label: "5-Whys Sequential Interrogation" },
          { id: "fishbone", label: "Ishikawa Fishbone (6M Matrix)" },
          { id: "rag", label: `Historical Incident RAG Retrieval (${ragResults.length})` },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`pb-2.5 pt-1 border-b-2 cursor-pointer transition-all ${
              activeTab === tab.id
                ? "border-blue-600 text-blue-700 font-bold"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: Evidence-Ranked Hypotheses */}
      {activeTab === "hypotheses" && (
        <div className="space-y-4">
          {report.ranked_hypotheses.map((hyp, idx) => (
            <div key={hyp.hypothesis_id} className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm ${
                    idx === 0 ? "bg-amber-100 text-amber-900 border border-amber-300" : "bg-slate-100 text-slate-700"
                  }`}>
                    #{idx + 1}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-blue-600">{hyp.hypothesis_id}</span>
                      <span className="text-slate-300">&bull;</span>
                      <span className="text-xs font-semibold text-slate-600">Category: {hyp.category}</span>
                    </div>
                    <h3 className="text-base font-bold text-slate-900 mt-0.5">{hyp.title}</h3>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 block uppercase font-medium">Confidence Weight</span>
                    <span className="text-base font-bold text-blue-700 font-mono">
                      {(hyp.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <CertaintyBadge level="Hypothesis" />
                </div>
              </div>

              <p className="text-xs text-slate-600 leading-relaxed">{hyp.description}</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                {/* Supporting Evidence */}
                <div className="p-3 bg-emerald-50/40 border border-emerald-200 rounded-lg space-y-2">
                  <div className="flex items-center gap-1.5 font-bold text-emerald-800">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Supporting Evidence ({hyp.supporting_evidence.length})</span>
                  </div>
                  <ul className="space-y-1 text-slate-700 list-disc list-inside">
                    {hyp.supporting_evidence.map((ev, i) => (
                      <li key={i}>{ev}</li>
                    ))}
                  </ul>
                </div>

                {/* Contradicting Evidence */}
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                  <div className="flex items-center gap-1.5 font-bold text-slate-700">
                    <XCircle className="w-3.5 h-3.5 text-slate-500" />
                    <span>Contradicting / Missing Evidence ({hyp.contradicting_evidence.length})</span>
                  </div>
                  <ul className="space-y-1 text-slate-600 list-disc list-inside">
                    {hyp.contradicting_evidence.map((ev, i) => (
                      <li key={i}>{ev}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Physical Verification Required */}
              <div className="p-3 bg-blue-50/50 border border-blue-200 rounded-lg flex items-start gap-2 text-xs text-blue-900">
                <ShieldCheck className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <span>
                  <strong>Required Engineering Confirmation:</strong> {hyp.required_confirmation}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* TAB 2: 5-Whys Interrogation */}
      {activeTab === "five_whys" && (
        <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900">5-Whys Sequential Root Cause Interrogation</h3>
            <p className="text-xs text-slate-500">Root-level deduction tracing dimensional expansion to tooling lockout gaps</p>
          </div>

          <div className="space-y-4 relative before:absolute before:left-4 before:top-4 before:bottom-4 before:w-0.5 before:bg-blue-200">
            {report.five_whys.map((w) => (
              <div key={w.level} className="relative pl-10 space-y-1.5">
                <div className="absolute left-2.5 top-1 -translate-x-1/2 w-4 h-4 rounded-full bg-blue-600 text-white text-[10px] font-bold flex items-center justify-center">
                  {w.level}
                </div>
                <div className="text-xs font-bold text-slate-800">
                  Why {w.level}: {w.question}
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
                  <div className="text-slate-900 font-medium">{w.answer}</div>
                  <div className="text-[11px] text-blue-700 font-medium">Evidence: {w.evidence}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: Ishikawa 6M Matrix */}
      {activeTab === "fishbone" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {report.fishbone_diagram.map((cat, i) => (
            <div key={i} className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  {cat.category}
                </span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-mono">
                  6M Branch
                </span>
              </div>
              <ul className="space-y-2 text-xs text-slate-600">
                {cat.factors.map((f, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-600 shrink-0 mt-1.5" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      {/* TAB 4: RAG Vector Search & Historical Incidents */}
      {activeTab === "rag" && (
        <div className="space-y-4">
          <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs space-y-3">
            <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
              Vector Semantic Query (Embeddings & Cosine Similarity)
            </span>
            <div className="flex gap-2">
              <input
                type="text"
                value={ragQuery}
                onChange={(e) => setRagQuery(e.target.value)}
                placeholder="Search historical NCRs, SOPs, and manuals..."
                className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-xs focus:outline-hidden focus:ring-2 focus:ring-blue-500 font-medium text-slate-800"
              />
              <button
                onClick={handleRagSearch}
                disabled={searchingRag}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 cursor-pointer shadow-xs"
              >
                <Search className="w-3.5 h-3.5" />
                <span>{searchingRag ? "Searching Vector Store..." : "Vector Search"}</span>
              </button>
            </div>
          </div>

          <div className="space-y-3">
            {ragResults.map((m) => (
              <div key={m.incident_id} className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-blue-600">{m.incident_id}</span>
                    <span className="text-xs font-bold text-slate-900">{m.title}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      Similarity: {(m.similarity_score * 100).toFixed(1)}%
                    </span>
                    <CertaintyBadge level="Confirmed Root Cause" />
                  </div>
                </div>

                <div className="text-xs text-slate-600 space-y-1">
                  <div><strong>Confirmed Cause:</strong> {m.confirmed_root_cause}</div>
                  <div><strong>Action Taken:</strong> {m.action_taken}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
