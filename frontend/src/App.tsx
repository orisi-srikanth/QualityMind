import React, { useState, useEffect } from "react";
import { Sidebar } from "./components/Sidebar";
import { Header } from "./components/Header";
import { DashboardPage } from "./pages/DashboardPage";
import { ProductConfigPage } from "./pages/ProductConfigPage";
import { BatchesPage } from "./pages/BatchesPage";
import { InspectionPage } from "./pages/InspectionPage";
import { VisualInspectionPage } from "./pages/VisualInspectionPage";
import { ProcessMonitoringPage } from "./pages/ProcessMonitoringPage";
import { SpcDashboardPage } from "./pages/SpcDashboardPage";
import { IncidentsPage } from "./pages/IncidentsPage";
import { RcaPage } from "./pages/RcaPage";
import { CapaPage } from "./pages/CapaPage";
import { AiReviewPage } from "./pages/AiReviewPage";
import { ReportsPage } from "./pages/ReportsPage";
import { TestScenariosPage } from "./pages/TestScenariosPage";
import { api } from "./api";
import {
  CheckCircle2, Clock, Loader2, Minus, Maximize2, X
} from "lucide-react";

interface PipelineStep {
  id: number;
  label: string;
  durationEstimateMs: number;
}

const PIPELINE_STAGES: PipelineStep[] = [
  { id: 1, label: "Checking batch data and measurement intake", durationEstimateMs: 600 },
  { id: 2, label: "Inspecting surface quality and defect localization", durationEstimateMs: 900 },
  { id: 3, label: "Evaluating dimensional specification conformance", durationEstimateMs: 500 },
  { id: 4, label: "Monitoring machine telemetry and process stability", durationEstimateMs: 700 },
  { id: 5, label: "Computing statistical process control (SPC) metrics", durationEstimateMs: 600 },
  { id: 6, label: "Investigating failure modes and historical root causes", durationEstimateMs: 800 },
  { id: 7, label: "Formulating containment and corrective action plans", durationEstimateMs: 700 },
  { id: 8, label: "Preparing quality dossier for human review", durationEstimateMs: 500 }
];

export function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [userRole, setUserRole] = useState<"admin" | "quality_engineer" | "operator">("quality_engineer");
  const [activeWorkflowId, setActiveWorkflowId] = useState<string>("WF-C038A990");
  const [isRunningPipeline, setIsRunningPipeline] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [pipelineFinishedBanner, setPipelineFinishedBanner] = useState(false);

  // Timer while running
  useEffect(() => {
    let interval: any = null;
    if (isRunningPipeline) {
      interval = setInterval(() => {
        setElapsedSeconds((s) => s + 1);
      }, 1000);
    } else {
      if (interval) clearInterval(interval);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRunningPipeline]);

  const handleRunPipeline = async () => {
    setIsRunningPipeline(true);
    setShowProgressModal(true);
    setIsMinimized(false);
    setCurrentStepIndex(0);
    setElapsedSeconds(0);
    setCompletedSteps([]);
    setPipelineFinishedBanner(false);

    try {
      const res = await api.runOrchestratedPipeline("BATCH-0245");
      if (res?.workflow_id) {
        setActiveWorkflowId(res.workflow_id);
      }
      setCompletedSteps(PIPELINE_STAGES.map((s) => s.id));
      setCurrentStepIndex(PIPELINE_STAGES.length - 1);
      setTimeout(() => {
        setShowProgressModal(false);
        setPipelineFinishedBanner(true);
        setActivePage("ai-review");
        setTimeout(() => setPipelineFinishedBanner(false), 8000);
      }, 900);
    } catch (e) {
      alert("Analysis could not be completed. Please try again.");
    } finally {
      setIsRunningPipeline(false);
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const renderCurrentPage = () => {
    switch (activePage) {
      case "dashboard":
        return <DashboardPage onNavigate={setActivePage} onRunPipeline={handleRunPipeline} />;
      case "product-config":
        return <ProductConfigPage />;
      case "batches":
        return (
          <BatchesPage
            onNavigate={setActivePage}
            onSelectWorkflow={(wfId: string) => {
              setActiveWorkflowId(wfId);
              setActivePage("ai-review");
            }}
          />
        );
      case "inspection":
        return <InspectionPage />;
      case "visual-inspection":
        return <VisualInspectionPage />;
      case "process-monitoring":
        return <ProcessMonitoringPage />;
      case "spc-dashboard":
        return <SpcDashboardPage />;
      case "incidents":
        return <IncidentsPage onNavigate={setActivePage} />;
      case "rca":
        return <RcaPage />;
      case "capa":
        return <CapaPage />;
      case "ai-review":
        return (
          <AiReviewPage
            onRunPipeline={handleRunPipeline}
            isRunningPipeline={isRunningPipeline}
            userRole={userRole}
            workflowId={activeWorkflowId}
          />
        );
      case "reports":
        return <ReportsPage />;
      case "test-scenarios":
        return <TestScenariosPage />;
      default:
        return <DashboardPage onNavigate={setActivePage} onRunPipeline={handleRunPipeline} />;
    }
  };

  return (
    <div className="flex h-screen bg-[#F6F8FB] overflow-hidden font-sans antialiased text-[#101828]">
      {/* Sidebar Navigation */}
      <Sidebar activePage={activePage} setActivePage={setActivePage} userRole={userRole} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        {/* Top Header */}
        <Header
          activePage={activePage}
          onRunPipeline={handleRunPipeline}
          isRunningPipeline={isRunningPipeline}
          onNavigate={setActivePage}
          userRole={userRole}
          onRoleChange={setUserRole}
        />



        {/* Pipeline Success Toast Banner */}
        {pipelineFinishedBanner && (
          <div className="bg-[#E7F6EE] border-b border-[#A9DFC1] text-[#067647] px-6 py-2.5 flex items-center justify-between text-[14px] font-semibold shadow-2xs animate-in fade-in duration-200">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#067647]" />
              <span>Full quality analysis completed successfully. Results ready for human review.</span>
            </div>
            <button
              onClick={() => setPipelineFinishedBanner(false)}
              className="text-[#067647] hover:text-[#055a36] text-[13px] font-bold cursor-pointer"
            >
              &times; Dismiss
            </button>
          </div>
        )}

        {/* Main Page View */}
        <main className="flex-1 overflow-y-auto p-7">
          <div className="max-w-[1500px] mx-auto pb-12">
            {renderCurrentPage()}
          </div>
        </main>
      </div>

      {/* Full Analysis Stepper Modal / Floating Panel */}
      {showProgressModal && (
        <div
          role="region"
          aria-live="polite"
          aria-busy={isRunningPipeline}
          className={`fixed z-50 transition-all duration-200 ${
            isMinimized
              ? "bottom-5 right-5 w-80 bg-white border border-[#E3E8EF] rounded-[12px] shadow-xl p-3"
              : "inset-0 bg-slate-900/40 backdrop-blur-[2px] flex items-center justify-center p-4"
          }`}
        >
          <div
            className={`bg-white rounded-[12px] border border-[#E3E8EF] shadow-2xl flex flex-col ${
              isMinimized ? "w-full border-none shadow-none" : "w-full max-w-lg overflow-hidden"
            }`}
          >
            {/* Modal Header */}
            <div className="px-5 py-4 border-b border-[#EEF1F5] flex items-center justify-between bg-[#F4F6FA]">
              <div className="flex items-center gap-2.5">
                <div className="w-2.5 h-2.5 rounded-full bg-[#2563EB] animate-pulse" />
                <h3 className="text-[15px] font-bold text-[#101828]">
                  {isRunningPipeline ? "Running Full Analysis" : "Analysis Completed"}
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-tabular text-[13px] font-medium text-[#475467] bg-white px-2 py-0.5 rounded border border-[#E3E8EF]">
                  <Clock className="w-3.5 h-3.5 inline mr-1 text-[#475467]" />
                  {formatTime(elapsedSeconds)}
                </span>
                <button
                  onClick={() => setIsMinimized(!isMinimized)}
                  title={isMinimized ? "Expand" : "Minimize"}
                  className="p-1 hover:bg-[#EEF1F5] text-[#475467] rounded cursor-pointer"
                >
                  {isMinimized ? <Maximize2 className="w-4 h-4" /> : <Minus className="w-4 h-4" />}
                </button>
                <button
                  onClick={() => setShowProgressModal(false)}
                  title="Close panel"
                  className="p-1 hover:bg-[#EEF1F5] text-[#475467] rounded cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Stepper Content */}
            {!isMinimized && (
              <div className="p-6 space-y-5">
                {/* Progress Bar & Counter */}
                <div className="space-y-1.5">
                  <div className="flex justify-between text-[13px] font-medium text-[#475467]">
                    <span>Step {Math.min(currentStepIndex + 1, 8)} of 8</span>
                    <span className="font-tabular font-semibold text-[#101828]">
                      {Math.round(((currentStepIndex + 1) / 8) * 100)}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-[#EEF1F5] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#2563EB] transition-all duration-300 rounded-full"
                      style={{ width: `${((currentStepIndex + 1) / 8) * 100}%` }}
                    />
                  </div>
                </div>

                {/* Vertical Stepper */}
                <div className="space-y-3 pt-2">
                  {PIPELINE_STAGES.map((st, idx) => {
                    const isDone = completedSteps.includes(st.id);
                    const isCurrent = currentStepIndex === idx && isRunningPipeline;
                    const isPending = !isDone && !isCurrent;

                    return (
                      <div key={st.id} className="flex items-center gap-3">
                        <div className="w-6 flex items-center justify-center shrink-0">
                          {isDone ? (
                            <CheckCircle2 className="w-5 h-5 text-[#067647]" />
                          ) : isCurrent ? (
                            <Loader2 className="w-5 h-5 text-[#2563EB] animate-spin" />
                          ) : (
                            <div className="w-2.5 h-2.5 rounded-full bg-[#CBD5E1]" />
                          )}
                        </div>
                        <div className="flex-1 text-[14px] flex items-center justify-between">
                          <span
                            className={
                              isCurrent
                                ? "font-semibold text-[#101828]"
                                : isDone
                                ? "text-[#475467]"
                                : "text-[#94A3B8]"
                            }
                          >
                            {st.label}
                            {isCurrent && <span className="inline-block w-1.5 h-3.5 bg-[#2563EB] ml-1.5 animate-pulse" />}
                          </span>
                          {isDone && (
                            <span className="text-[12px] font-tabular text-[#067647] font-medium">Done</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
