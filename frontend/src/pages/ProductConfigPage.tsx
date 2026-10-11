import React, { useEffect, useState } from "react";
import { api } from "../api";
import { ProductSpec } from "../types";
import { CertaintyBadge } from "../components/CertaintyBadge";
import { Settings, Plus, Check, ShieldCheck, Cpu, Ruler } from "lucide-react";

export const ProductConfigPage: React.FC = () => {
  const [products, setProducts] = useState<ProductSpec[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState<ProductSpec | null>(null);

  useEffect(() => {
    api.getProducts().then((res) => {
      setProducts(res);
      if (res.length > 0) setSelectedProduct(res[0]);
      setLoading(false);
    });
  }, []);

  if (loading || !selectedProduct) {
    return <div className="p-8 text-center text-slate-500">Loading Product Specifications...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-900">Engineering Product & Tolerance Definitions</h2>
          <p className="text-xs text-slate-500">
            IATF 16949 / ISO 9001 master characteristic registry for deterministic dimensional compliance.
          </p>
        </div>
        <CertaintyBadge level="Observed Fact" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Product Catalog List */}
        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">Configured Parts ({products.length})</span>
            <span className="text-[10px] text-slate-400">Master List</span>
          </div>

          <div className="space-y-2">
            {products.map((p) => {
              const isSel = selectedProduct.product_id === p.product_id;
              return (
                <div
                  key={p.product_id}
                  onClick={() => setSelectedProduct(p)}
                  className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
                    isSel
                      ? "bg-blue-50/70 border-blue-400 shadow-xs"
                      : "bg-white border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900">{p.name}</span>
                    <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-700">
                      {p.part_number}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1 flex items-center justify-between">
                    <span>Machine: {p.machine_id}</span>
                    <span>Nominal: {p.nominal_mm.toFixed(2)} mm</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Product Master Specification Sheet */}
        <div className="lg:col-span-2 p-5 bg-white border border-slate-200 rounded-xl shadow-xs space-y-5">
          <div className="flex items-start justify-between border-b border-slate-100 pb-4">
            <div>
              <span className="text-xs font-mono text-blue-600 font-bold">{selectedProduct.product_id}</span>
              <h3 className="text-lg font-bold text-slate-900 mt-0.5">{selectedProduct.name} ({selectedProduct.part_number})</h3>
              <p className="text-xs text-slate-500">{selectedProduct.manufacturing_process}</p>
            </div>
            <div className="text-right space-y-1">
              <span className="inline-block px-2.5 py-1 rounded bg-slate-100 text-slate-800 text-xs font-semibold">
                Machine: {selectedProduct.machine_id}
              </span>
              <div className="text-[11px] text-slate-400">Material: {selectedProduct.material}</div>
            </div>
          </div>

          {/* Critical Quality Characteristic Specification Box */}
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Ruler className="w-4 h-4 text-blue-600" />
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                  Critical Characteristic: {selectedProduct.inspection_parameter}
                </span>
              </div>
              <CertaintyBadge level="Observed Fact" />
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <span className="text-[10px] text-slate-500 block uppercase font-medium">Nominal Value</span>
                <span className="text-lg font-bold text-slate-900 font-mono">
                  {selectedProduct.nominal_mm.toFixed(2)} {selectedProduct.unit}
                </span>
              </div>

              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <span className="text-[10px] text-slate-500 block uppercase font-medium">Bilateral Tolerance</span>
                <span className="text-lg font-bold text-blue-700 font-mono">
                  ±{selectedProduct.tolerance_mm.toFixed(2)} {selectedProduct.unit}
                </span>
              </div>

              <div className="p-3 bg-white border border-rose-200 rounded-lg bg-rose-50/30">
                <span className="text-[10px] text-rose-600 block uppercase font-bold">Upper Limit (USL)</span>
                <span className="text-lg font-bold text-rose-700 font-mono">
                  {selectedProduct.usl.toFixed(2)} {selectedProduct.unit}
                </span>
              </div>

              <div className="p-3 bg-white border border-rose-200 rounded-lg bg-rose-50/30">
                <span className="text-[10px] text-rose-600 block uppercase font-bold">Lower Limit (LSL)</span>
                <span className="text-lg font-bold text-rose-700 font-mono">
                  {selectedProduct.lsl.toFixed(2)} {selectedProduct.unit}
                </span>
              </div>
            </div>

            <div className="p-3 bg-white border border-slate-200 rounded-lg text-xs space-y-1 text-slate-600">
              <div className="flex justify-between">
                <span className="font-medium text-slate-700">Inspection Frequency:</span>
                <span>{selectedProduct.inspection_frequency}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium text-slate-700">Acceptable Range:</span>
                <span className="font-mono text-emerald-700 font-bold">
                  {selectedProduct.lsl.toFixed(2)} mm &le; Diameter &le; {selectedProduct.usl.toFixed(2)} mm
                </span>
              </div>
            </div>
          </div>

          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-900 flex items-start gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <span>
              <strong>Deterministic Calculation Guarantee:</strong> Any component measurement exceeding {selectedProduct.usl.toFixed(2)} mm
              or dropping below {selectedProduct.lsl.toFixed(2)} mm is automatically flagged as nonconforming by Agent 3 with calculated exact deviation.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
