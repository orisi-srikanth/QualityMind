import React, { useEffect, useState } from "react";
import { api } from "../api";
import { VisualDefectPrediction } from "../types";
import { CertaintyBadge } from "../components/CertaintyBadge";
import { Camera, Upload, CheckCircle2, XCircle, AlertTriangle, Crosshair, Sparkles, Info } from "lucide-react";

export const VisualInspectionPage: React.FC = () => {
  const [selectedSample, setSelectedSample] = useState("IMG-001.png");
  const [prediction, setPrediction] = useState<VisualDefectPrediction | null>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [activeView, setActiveView] = useState<"annotated" | "raw">("annotated");
  const [reviewStatus, setReviewStatus] = useState<"PENDING" | "CONFIRMED" | "REJECTED">("PENDING");

  const runSample = async (sampleName: string) => {
    setSelectedSample(sampleName);
    setReviewStatus("PENDING");
    setLoading(true);
    try {
      const res = await api.inspectSampleImage(sampleName);
      setPrediction(res.prediction);
      setMetrics(res.metrics);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runSample("IMG-001.png");
  }, []);

  const handleCustomUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setReviewStatus("PENDING");
    setLoading(true);
    try {
      const res = await api.uploadAndInspectImage(e.target.files[0]);
      setPrediction(res.prediction);
      setMetrics(res.metrics);
      setSelectedSample(e.target.files[0].name);
    } catch (err) {
      alert("Failed to inspect uploaded image.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Permanent Notice Banner */}
      <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start gap-2.5 shadow-2xs">
        <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
        <div>
          <strong className="font-semibold">Dataset & Prototype Notice:</strong> Proxy-part images from MVTec AD (screws, nuts, transistors, cables), not precision shafts. Academic prototype, not production-grade.
        </div>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">Two-Stage Computer Vision Defect Inspection</h2>
          <p className="text-xs text-slate-500">
            Stage A PatchCore anomaly localization + Stage B MobileNetV3 unified defect classification.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-lg text-xs font-semibold cursor-pointer shadow-xs">
            <Upload className="w-3.5 h-3.5 text-slate-500" />
            <span>Upload Test Image</span>
            <input type="file" accept="image/*" onChange={handleCustomUpload} className="hidden" />
          </label>
        </div>
      </div>

      {/* Preset Dataset Samples Selector */}
      <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs space-y-2">
        <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
          Select Standard Held-Out Benchmark Inspection Images:
        </span>
        <div className="flex flex-wrap gap-2">
          {[
            { id: "IMG-001.png", label: "IMG-001: Metal Nut Scratch (Held-Out Test)", tag: "Defect" },
            { id: "metal_nut_scratch.png", label: "Metal Nut: Surface Scratch", tag: "Defect" },
            { id: "metal_nut_bent.png", label: "Metal Nut: Dent Deformation", tag: "Defect" },
            { id: "screw_thread.png", label: "Screw: Thread Damage", tag: "Defect" },
            { id: "transistor_damaged.png", label: "Transistor: Damaged Case", tag: "Defect" },
            { id: "cable_missing.png", label: "Cable: Missing Conductor Wire", tag: "Defect" },
            { id: "metal_nut_normal.png", label: "Metal Nut: Conforming Surface", tag: "Normal" },
            { id: "screw_normal.png", label: "Screw: Conforming Thread", tag: "Normal" },
          ].map((sample) => (
            <button
              key={sample.id}
              onClick={() => runSample(sample.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-2 border cursor-pointer transition-all ${
                selectedSample === sample.id
                  ? "bg-blue-50 border-blue-500 text-blue-700 shadow-xs"
                  : "bg-white border-slate-200 text-slate-600 hover:border-slate-300"
              }`}
            >
              <span>{sample.label}</span>
              <span className={`text-[10px] px-1 rounded ${sample.tag === "Normal" ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"}`}>
                {sample.tag}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Inspection Canvas and Inference Results */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Image Viewer */}
        <div className="lg:col-span-2 p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Camera className="w-4 h-4 text-blue-600" />
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Inspection Image: {selectedSample}
              </span>
            </div>

            <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-lg text-xs font-medium">
              <button
                onClick={() => setActiveView("annotated")}
                className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                  activeView === "annotated" ? "bg-white text-blue-700 shadow-2xs font-semibold" : "text-slate-600"
                }`}
              >
                Model Overlay & BBox
              </button>
              <button
                onClick={() => setActiveView("raw")}
                className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                  activeView === "raw" ? "bg-white text-blue-700 shadow-2xs font-semibold" : "text-slate-600"
                }`}
              >
                Raw Surface
              </button>
            </div>
          </div>

          <div className="relative bg-slate-900 rounded-xl overflow-hidden flex items-center justify-center min-h-[320px] max-h-[440px] border border-slate-800">
            {loading ? (
              <div className="text-white text-xs flex items-center gap-2">
                <Sparkles className="w-4 h-4 animate-spin text-blue-400" />
                <span>Running PatchCore & MobileNetV3 Inference...</span>
              </div>
            ) : prediction ? (
              <img
                src={activeView === "annotated" && prediction.annotated_image_url ? prediction.annotated_image_url : prediction.image_url}
                alt="Product Inspection"
                className="max-h-[420px] w-auto object-contain rounded-lg"
              />
            ) : null}
          </div>

          {/* Human Review Status Banner & Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 border-t border-slate-100">
            <div className="flex items-center gap-2 text-xs text-slate-600">
              <Info className="w-3.5 h-3.5 text-blue-600" />
              <span>Human-in-the-Loop Review:</span>
              <span className={`px-2 py-0.5 rounded font-bold ${
                reviewStatus === "CONFIRMED" ? "bg-rose-100 text-rose-800" :
                reviewStatus === "REJECTED" ? "bg-slate-100 text-slate-800" :
                "bg-amber-100 text-amber-800"
              }`}>
                {reviewStatus}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setReviewStatus("CONFIRMED")}
                className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 cursor-pointer shadow-xs transition-colors"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Confirm Defect</span>
              </button>
              <button
                onClick={() => setReviewStatus("REJECTED")}
                className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 cursor-pointer border border-slate-200 transition-colors"
              >
                <XCircle className="w-3.5 h-3.5" />
                <span>Reject (False Alarm)</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right Col: Model Prediction Metrics & BBox Data */}
        <div className="p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-5">
          <div className="border-b border-slate-100 pb-3">
            <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Two-Stage Inferred Results</span>
            <h3 className="text-base font-bold text-slate-900 mt-0.5">Defect Classification & BBox</h3>
          </div>

          {prediction && (
            <div className="space-y-4">
              <div className="p-3.5 rounded-lg border space-y-2 bg-slate-50 border-slate-200">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-medium">Data Source:</span>
                  <span className="text-xs font-semibold text-slate-800 bg-white px-2 py-0.5 rounded border border-slate-200">
                    {prediction.source || "MVTec AD (proxy part)"}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-medium">Proxy Category:</span>
                  <span className="text-xs font-mono font-bold text-slate-800">
                    {prediction.category}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-medium">Defect Classification:</span>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                    prediction.defect_detected ? "bg-rose-100 text-rose-800" : "bg-emerald-100 text-emerald-800"
                  }`}>
                    {prediction.defect_type.toUpperCase()}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-medium">Raw Defect Folder:</span>
                  <span className="text-xs font-mono text-slate-700">
                    {prediction.raw_class}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-medium">PatchCore Anomaly Score:</span>
                  <span className="text-xs font-mono font-bold text-amber-700">
                    {prediction.anomaly_score !== undefined ? prediction.anomaly_score.toFixed(4) : "N/A"}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-medium">Classifier Confidence:</span>
                  <span className="text-sm font-bold font-mono text-blue-700">
                    {(prediction.confidence * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-medium">Surface Location:</span>
                  <span className="text-xs font-mono text-slate-700">
                    {prediction.location}
                  </span>
                </div>
              </div>

              {prediction.bounding_box && (
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                    <Crosshair className="w-3.5 h-3.5 text-rose-600" />
                    <span>Localized Bounding Box [ROI]</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                    <div className="p-1.5 bg-white rounded border border-slate-200 text-slate-600">
                      X: <strong className="text-slate-900">{prediction.bounding_box.x} px</strong>
                    </div>
                    <div className="p-1.5 bg-white rounded border border-slate-200 text-slate-600">
                      Y: <strong className="text-slate-900">{prediction.bounding_box.y} px</strong>
                    </div>
                    <div className="p-1.5 bg-white rounded border border-slate-200 text-slate-600">
                      Width: <strong className="text-slate-900">{prediction.bounding_box.width} px</strong>
                    </div>
                    <div className="p-1.5 bg-white rounded border border-slate-200 text-slate-600">
                      Height: <strong className="text-slate-900">{prediction.bounding_box.height} px</strong>
                    </div>
                  </div>
                </div>
              )}

              {/* Verified Metrics Sheet */}
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                  Model Architecture & Protocol
                </span>
                <div className="space-y-1 text-xs text-slate-600">
                  <div className="flex justify-between">
                    <span>Stage A Detector:</span>
                    <strong className="text-slate-900">PatchCore (ResNet18)</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Stage B Classifier:</span>
                    <strong className="text-slate-900">MobileNetV3-Small</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Target Latency:</span>
                    <strong className="text-emerald-700 font-mono">&lt; 200 ms (CPU)</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>Confidence Threshold:</span>
                    <strong className="text-slate-900 font-mono">0.70 (Uncertain fallback)</strong>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
