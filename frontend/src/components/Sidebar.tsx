import React from "react";
import {
  LayoutDashboard, Settings, Layers, Ruler, Camera,
  Activity, LineChart, AlertTriangle, GitFork, ShieldCheck,
  Bot, FileText, CheckSquare, Sparkles, Terminal
} from "lucide-react";

interface Props {
  activePage: string;
  setActivePage: (page: string) => void;
}

export const Sidebar: React.FC<Props> = ({ activePage, setActivePage }) => {
  const navSections = [
    {
      title: "OPERATIONS",
      items: [
        { id: "dashboard", label: "Quality Dashboard", icon: LayoutDashboard },
        { id: "product-config", label: "Product Config", icon: Settings },
        { id: "batches", label: "Production Batches", icon: Layers, badge: "3" },
        { id: "inspection", label: "Inspection Center", icon: Ruler },
        { id: "visual-inspection", label: "Visual Inspection", icon: Camera, badge: "PyTorch CV" },
      ]
    },
    {
      title: "ANALYTICS & SPC",
      items: [
        { id: "process-monitoring", label: "Process Monitoring", icon: Activity, alert: true },
        { id: "spc-dashboard", label: "SPC Dashboard", icon: LineChart },
        { id: "incidents", label: "Quality Incidents", icon: AlertTriangle, badge: "2 Active", badgeColor: "bg-rose-100 text-rose-700" },
        { id: "rca", label: "Root Cause (RCA)", icon: GitFork, badge: "5-Whys" },
      ]
    },
    {
      title: "GOVERNANCE & AUDIT",
      items: [
        { id: "capa", label: "CAPA Management", icon: ShieldCheck, badge: "3 Open" },
        { id: "ai-review", label: "AI Review & HITL", icon: Bot, badge: "Gatekeeper" },
        { id: "reports", label: "Quality Reports", icon: FileText, badge: "PDF" },
        { id: "test-scenarios", label: "Test Scenarios (TC-01..08)", icon: Terminal, badge: "8 Tests", badgeColor: "bg-emerald-100 text-emerald-800" },
      ]
    }
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-screen sticky top-0 shrink-0 select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-200 flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white font-black text-lg shadow-sm">
          AG
        </div>
        <div>
          <div className="text-sm font-bold text-slate-900 tracking-tight leading-tight flex items-center gap-1.5">
            <span>Antigravity Quality</span>
          </div>
          <p className="text-[11px] text-slate-500 font-medium">
            Industrial Decision Support
          </p>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {navSections.map((sec, idx) => (
          <div key={idx}>
            <div className="px-3 mb-2 text-[10px] font-bold text-slate-400 tracking-wider uppercase">
              {sec.title}
            </div>
            <div className="space-y-0.5">
              {sec.items.map((item) => {
                const Icon = item.icon;
                const isActive = activePage === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActivePage(item.id)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                      isActive
                        ? "bg-blue-50 text-blue-700 font-semibold shadow-xs"
                        : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className={`w-4 h-4 ${isActive ? "text-blue-600" : "text-slate-400"}`} />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${item.badgeColor || "bg-slate-100 text-slate-600"}`}>
                        {item.badge}
                      </span>
                    )}
                    {item.alert && !item.badge && (
                      <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Safety & Protocol Footer */}
      <div className="p-3 border-t border-slate-200 bg-slate-50/70 text-xs">
        <div className="p-2.5 bg-white border border-slate-200 rounded-lg shadow-2xs space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-700">Multi-Agent Protocol</span>
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
          </div>
          <p className="text-[10px] text-slate-500 leading-tight">
            8 Specialized AI Agents active. Human-in-the-Loop decision gateway enforced.
          </p>
        </div>
      </div>
    </aside>
  );
};
