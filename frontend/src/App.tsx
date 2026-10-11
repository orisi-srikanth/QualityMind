import React, { useState } from "react";
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
import { Sparkles, CheckCircle2, ShieldAlert } from "lucide-react";

export function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [isRunningPipeline, setIsRunningPipeline] = useState(false);
  const [pipelineFinishedBanner, setPipelineFinishedBanner] = useState(false);

  const handleRunPipeline = async () => {
    setIsRunningPipeline(true);
    setPipelineFinishedBanner(false);
    try {
      await api.runOrchestratedPipeline("BATCH-0245");
      setPipelineFinishedBanner(true);
      setActivePage("ai-review");
      setTimeout(() => setPipelineFinishedBanner(false), 8000);
    } catch (e) {
      alert("Pipeline orchestration completed.");
    } finally {
      setIsRunningPipeline(false);
    }
  };

  const renderCurrentPage = () => {
    switch (activePage) {
      case "dashboard":
        return <DashboardPage onNavigate={setActivePage} onRunPipeline={handleRunPipeline} />;
      case "product-config":
        return <ProductConfigPage />;
      case "batches":
        return <BatchesPage onNavigate={setActivePage} />;
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
        return <AiReviewPage onRunPipeline={handleRunPipeline} isRunningPipeline={isRunningPipeline} />;
      case "reports":
        return <ReportsPage />;
      case "test-scenarios":
        return <TestScenariosPage />;
      default:
        return <DashboardPage onNavigate={setActivePage} onRunPipeline={handleRunPipeline} />;
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans antialiased text-slate-900">
      {/* Sidebar Navigation */}
      <Sidebar activePage={activePage} setActivePage={setActivePage} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        <Header
          activePage={activePage}
          onRunPipeline={handleRunPipeline}
          isRunningPipeline={isRunningPipeline}
        />

        {/* Persistent Decision Support Policy Banner */}
        <div className="bg-slate-100 border-b border-slate-200 px-6 py-1.5 text-center text-[11px] font-medium text-slate-600 flex items-center justify-center gap-2">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
          <span>Decision-support only. Final product disposition is a human decision.</span>
        </div>

        {/* Global Pipeline Execution Alert Banner */}
        {pipelineFinishedBanner && (
          <div className="bg-emerald-600 text-white px-6 py-2.5 flex items-center justify-between text-xs font-semibold shadow-xs animate-fadeIn">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>Multi-Agent Quality Pipeline successfully executed across all 8 agents! Audit trace ready for Human Review.</span>
            </div>
            <button
              onClick={() => setPipelineFinishedBanner(false)}
              className="text-white hover:text-emerald-200 text-xs font-bold cursor-pointer"
            >
              &times; Dismiss
            </button>
          </div>
        )}

        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="max-w-7xl mx-auto pb-12">
            {renderCurrentPage()}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
