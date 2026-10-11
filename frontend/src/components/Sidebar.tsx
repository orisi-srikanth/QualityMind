import React from "react";
import {
  LayoutDashboard, Settings, Layers, Ruler, Camera,
  Activity, LineChart, AlertTriangle, GitFork, ShieldCheck,
  Bot, FileText, Terminal
} from "lucide-react";

interface Props {
  activePage: string;
  setActivePage: (page: string) => void;
  userRole?: string;
}

export const Sidebar: React.FC<Props> = ({ activePage, setActivePage, userRole = "quality_engineer" }) => {
  const isAdmin = userRole === "admin";

  const navSections = [
    {
      title: "OPERATIONS",
      items: [
        { id: "dashboard", label: "Quality Dashboard", icon: LayoutDashboard, purpose: "Overall manufacturing quality status" },
        { id: "product-config", label: "Product Configuration", icon: Settings, purpose: "Manage products/specifications" },
        { id: "batches", label: "Production Batches", icon: Layers, badge: "3", badgeColor: "bg-slate-100 text-slate-700", purpose: "Manage batch information" },
        { id: "inspection", label: "Inspection Center", icon: Ruler, purpose: "Review measurement data" },
        { id: "visual-inspection", label: "Visual Inspection", icon: Camera, purpose: "Upload/review product images" },
      ]
    },
    {
      title: "ANALYTICS & SPC",
      items: [
        { id: "process-monitoring", label: "Process Monitoring", icon: Activity, alert: true, purpose: "Monitor machine parameters" },
        { id: "spc-dashboard", label: "SPC Dashboard", icon: LineChart, purpose: "Control charts and process capability" },
        { id: "incidents", label: "Quality Incidents", icon: AlertTriangle, badge: "2 Active", badgeColor: "bg-rose-100 text-rose-700", purpose: "Manage detected quality problems" },
        { id: "rca", label: "Root Cause Analysis", icon: GitFork, purpose: "Review RCA hypotheses/evidence" },
      ]
    },
    {
      title: "GOVERNANCE & AUDIT",
      items: [
        { id: "capa", label: "CAPA Management", icon: ShieldCheck, badge: "3 Open", badgeColor: "bg-amber-100 text-amber-800", purpose: "Track corrective/preventive actions" },
        { id: "ai-review", label: "AI Review Center", icon: Bot, purpose: "Review agent recommendations" },
        { id: "reports", label: "Reports", icon: FileText, badge: "PDF", badgeColor: "bg-slate-100 text-slate-700", purpose: "Generate/download quality reports" },
        // Show Test Scenarios only for Admin
        ...(isAdmin ? [{ id: "test-scenarios", label: "Test Scenarios", icon: Terminal, purpose: "Audit test evaluation suite" }] : [])
      ]
    }
  ];

  return (
    <aside className="w-[272px] bg-white border-r border-[#E3E8EF] flex flex-col h-screen sticky top-0 shrink-0 select-none z-20">
      {/* Brand Header */}
      <div className="px-5 py-[18px] border-b border-[#E3E8EF] flex items-center gap-3 shrink-0">
        <div className="w-[36px] h-[36px] rounded-[8px] bg-[#2563EB] flex items-center justify-center text-white font-extrabold text-[15px] shadow-xs shrink-0">
          QM
        </div>
        <div className="min-w-0">
          <div className="text-[17px] font-bold text-[#101828] tracking-tight leading-tight truncate">
            Quality Minds
          </div>
          <p className="text-[13px] text-[#475467] font-medium leading-normal truncate">
            Industrial Decision Support
          </p>
        </div>
      </div>

      {/* Navigation Links with Full Height Flow */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {navSections.map((sec, idx) => (
          <div key={idx} className={idx > 0 ? "mt-6" : ""}>
            <div className="px-3 mb-2 text-[12px] font-semibold text-[#475467] tracking-[0.06em] uppercase">
              {sec.title}
            </div>
            <div className="space-y-1">
              {sec.items.map((item) => {
                const Icon = item.icon;
                const isActive = activePage === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActivePage(item.id)}
                    className={`w-full h-[42px] flex items-center justify-between px-3 rounded-[8px] text-[14px] transition-colors duration-150 cursor-pointer relative group text-left ${
                      isActive
                        ? "bg-[#EAF2FF] text-[#2563EB] font-semibold before:absolute before:left-0 before:top-2 before:bottom-2 before:w-[3px] before:bg-[#2563EB] before:rounded-r"
                        : "text-[#475467] hover:text-[#101828] hover:bg-[#F3F6FA] font-medium"
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0 pr-2">
                      <Icon className={`w-5 h-5 shrink-0 transition-colors ${isActive ? "text-[#2563EB]" : "text-[#475467] group-hover:text-[#101828]"}`} />
                      <span className="truncate whitespace-nowrap">{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className={`h-[22px] px-2 flex items-center justify-center text-[12px] font-semibold rounded-full shrink-0 ${item.badgeColor || "bg-slate-100 text-slate-700"}`}>
                        {item.badge}
                      </span>
                    )}
                    {item.alert && !item.badge && (
                      <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse shrink-0" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
};
