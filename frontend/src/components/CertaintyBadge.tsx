import React from "react";
import { CertaintyLevel } from "../types";
import { CheckCircle2, Eye, LineChart, HelpCircle, ShieldCheck } from "lucide-react";

interface Props {
  level: CertaintyLevel | string;
  className?: string;
  showIcon?: boolean;
}

export const CertaintyBadge: React.FC<Props> = ({ level, className = "", showIcon = true }) => {
  switch (level) {
    case "Observed Fact":
      return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-800 border border-slate-300 ${className}`}>
          {showIcon && <CheckCircle2 className="w-3 h-3 text-slate-600" />}
          <span>Observed Fact</span>
        </span>
      );
    case "Model Prediction":
      return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-purple-50 text-purple-800 border border-purple-200 ${className}`}>
          {showIcon && <Eye className="w-3 h-3 text-purple-600" />}
          <span>Model Prediction</span>
        </span>
      );
    case "Statistical Finding":
      return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-800 border border-blue-200 ${className}`}>
          {showIcon && <LineChart className="w-3 h-3 text-blue-600" />}
          <span>Statistical Finding</span>
        </span>
      );
    case "Hypothesis":
      return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-800 border border-amber-300 ${className}`}>
          {showIcon && <HelpCircle className="w-3 h-3 text-amber-600" />}
          <span>Hypothesis</span>
        </span>
      );
    case "Confirmed Root Cause":
      return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-300 font-semibold ${className}`}>
          {showIcon && <ShieldCheck className="w-3 h-3 text-emerald-600" />}
          <span>Confirmed Root Cause</span>
        </span>
      );
    default:
      return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700 ${className}`}>
          {level}
        </span>
      );
  }
};
