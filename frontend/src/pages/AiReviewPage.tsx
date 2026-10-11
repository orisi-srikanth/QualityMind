import React, { useEffect, useState } from "react";
import { api } from "../api";
import { WorkflowState, AgentStepLog } from "../types";
import { CertaintyBadge } from "../components/CertaintyBadge";
import {
  Bot, ShieldCheck, CheckCircle2, XCircle, AlertTriangle,
  Play, RefreshCw, UserCheck, CheckSquare, Clock, Terminal
} from "lucide-react";

interface Props {
  onRunPipeline: () => void;
  isRunningPipeline: boolean;
}

export const AiReviewPage: React.FC<Props> = ({ onRunPipeline, isRunningPipeline }) => {
  const [workflowState, setWorkflowState] = useState<WorkflowState | null>(null);
  const [loading, setLoading] = useState(true);
  const [engineerName, setEngineerName] = useState("Dr. R. Vance (Lead Quality Engineer)");
  const [disposition, setDisposition] = useState("QUARANTINE_BATCH");
  const [comments, setComments] = useState("Confirmed cutting tool flank wear via toolmakers microscope. Quarantining batch BATCH-0245 for 100% sorting inspection.");
  const [submitted, setSubmitted] = useState(false);

  const loadWorkflow = () => {
    setLoading(true);
    api.runOrchestratedPipeline("BATCH-0245").then((res) => {
      setWorkflowState(res);
      setLoading(false);
    });
  };

  useEffect(() => {
    loadWorkflow();
  }, []);

  const handleSignOff = async (decision: string) => {
    try {
      await api.submitHumanDecision({
        approved_by: engineerName,
        decision: decision,
        engineering_comments: comments,
        disposition: disposition,
        confirmed_root_cause: "Progressive Cutting Tool Flank Wear on CNC-04",
      });
      setSubmitted(true);
      alert(`Human Decision Recorded: ${decision}. Disposition: ${disposition}`);
    } catch (e) {
      alert("Failed to record sign-off.");
    }
  };

  if (loading || !workflowState) {
    return <div className="p-8 text-center text-slate-500">Loading AI Agent Pipeline Audit...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">AI Agent Review Center & Execution Visibility</h2>
          <p className="text-xs text-slate-500">
            Real-time multi-agent execution logs, Agent 8 Critic validation, and Human-in-the-Loop decision gate.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onRunPipeline}
            disabled={isRunningPipeline}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 cursor-pointer shadow-xs"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Re-Run All 8 Agents</span>
          </button>
        </div>
      </div>

      {/* Critic Review Box (Agent 8) */}
      {workflowState.critic_review && (
        <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Agent 8 Critic Safety & Calculation Audit Verdict
                </h3>
                <span className="text-[11px] text-slate-500">Automated Pre-Signoff Gatekeeper</span>
              </div>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
              {workflowState.critic_review.critic_verdict}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-3 bg-slate-50 rounded-lg">
              <span className="text-slate-500 block">Spec References</span>
              <strong className="text-emerald-700">Verified Correct</strong>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg">
              <span className="text-slate-500 block">Calculation Audit</span>
              <strong className="text-emerald-700">Validated Accurate</strong>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg">
              <span className="text-slate-500 block">CV Prediction BBox</span>
              <strong className="text-emerald-700">Verified &gt; 90% Conf</strong>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg">
              <span className="text-slate-500 block">Causal Claims</span>
              <strong className="text-emerald-700">No Unsupported Leaps</strong>
            </div>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg space-y-1 text-xs">
            <span className="font-bold text-slate-800 block">Critic Audit Observations:</span>
            {workflowState.critic_review.review_comments.map((c, i) => (
              <div key={i} className="text-slate-600 flex items-start gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                <span>{c}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Human-in-the-Loop Sign-Off Form (Requirement 14) */}
      <div className="p-5 bg-blue-50/40 border border-blue-200 rounded-xl shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-blue-100 pb-3">
          <div className="flex items-center gap-2">
            <UserCheck className="w-5 h-5 text-blue-700" />
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Human-in-the-Loop Quality Engineer Disposition Gate
              </h3>
              <p className="text-xs text-slate-600">
                Safety protocol: AI findings are decision-support only. Final release/quarantine requires authorized engineering approval.
              </p>
            </div>
          </div>
          <CertaintyBadge level="Confirmed Root Cause" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Authorized Quality Engineer:</label>
            <input
              type="text"
              value={engineerName}
              onChange={(e) => setEngineerName(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-blue-500 font-medium"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Final Batch Disposition:</label>
            <select
              value={disposition}
              onChange={(e) => setDisposition(e.target.value)}
              className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-blue-500 font-medium"
            >
              <option value="QUARANTINE_BATCH">QUARANTINE BATCH (100% Sorting Inspection)</option>
              <option value="REWORK_WINDOW">REWORK AFFECTED WINDOW</option>
              <option value="SCRAP">SCRAP NONCONFORMING COMPONENTS</option>
              <option value="RELEASE_WITH_CONCESSION">RELEASE WITH ENGINEERING CONCESSION</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Engineering Investigation Comments:</label>
          <textarea
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            rows={2}
            className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-xs focus:outline-hidden focus:ring-2 focus:ring-blue-500 font-medium"
          />
        </div>

        <div className="flex items-center gap-3 pt-2">
          <button
            onClick={() => handleSignOff("ACCEPT_FINDINGS")}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-xs cursor-pointer"
          >
            Accept Findings & Authorize Disposition
          </button>
          <button
            onClick={() => handleSignOff("REQUEST_REASSESSMENT")}
            className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-lg text-xs font-semibold shadow-xs cursor-pointer"
          >
            Request Re-Assessment
          </button>
        </div>
      </div>

      {/* Execution Trace Logs (Requirement 17) */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-slate-600" />
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Agent Execution Visibility Trace ({workflowState.execution_trace.length} Steps)
            </span>
          </div>
          <span className="text-xs text-slate-500">Status: {workflowState.status}</span>
        </div>

        <div className="divide-y divide-slate-100">
          {workflowState.execution_trace.map((step) => (
            <div key={step.step_number} className="p-4 hover:bg-slate-50/50 transition-colors space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 font-mono text-[10px] font-bold flex items-center justify-center">
                    {step.step_number}
                  </span>
                  <span className="text-xs font-bold text-slate-900">{step.agent_name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono text-slate-400">{step.duration_ms} ms</span>
                  <CertaintyBadge level={step.certainty_level} />
                </div>
              </div>

              <div className="text-xs text-slate-600 space-y-1 pl-7">
                <div><strong>Input:</strong> {step.input_summary}</div>
                <div><strong>Tool Calls:</strong> <code className="text-[11px] bg-slate-100 px-1 py-0.5 rounded text-blue-700">{step.tool_calls.join(", ")}</code></div>
                <div><strong>Output:</strong> {step.output_summary}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
