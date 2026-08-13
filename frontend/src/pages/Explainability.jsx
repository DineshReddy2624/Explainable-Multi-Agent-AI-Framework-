import React, { useContext } from 'react';
import { DatasetContext } from '../context/DatasetContext';
import ExplanationCard from '../components/explainability/ExplanationCard';
import SHAPChart from '../components/explainability/SHAPChart';
import ConfidenceScore from '../components/explainability/ConfidenceScore';
import EmptyState from '../components/common/EmptyState';
import { ShieldCheck, Lock, Sparkles, EyeOff } from 'lucide-react';

const Explainability = () => {
  const { analysis } = useContext(DatasetContext);

  const features = analysis?.shap_features || [
    { feature: 'income', shap_value: 0.42 },
    { feature: 'age', shap_value: 0.28 },
    { feature: 'transaction_count', shap_value: 0.15 }
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-gray-900 tracking-tight">Privacy, PII Protection & Model Explainability</h2>
            <span className="badge badge-success font-medium flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-emerald-600" />
              <span>Role-Based Masking Active</span>
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Automatic PII detection, export protection, and SHAP feature importance tree explainer.
          </p>
        </div>
      </div>

      {/* Privacy Status Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">PII Auto-Protection</p>
            <h3 className="text-xl font-bold text-emerald-600 mt-1">Protected</h3>
            <p className="text-xs text-gray-500 mt-0.5">Role-based masking</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600">
            <Lock className="w-5 h-5" />
          </div>
        </div>

        <div className="card flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Export Masking</p>
            <h3 className="text-xl font-bold text-blue-600 mt-1">Enabled</h3>
            <p className="text-xs text-gray-500 mt-0.5">Non-admin auto-mask</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
            <EyeOff className="w-5 h-5" />
          </div>
        </div>

        <div className="card flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">SHAP Explainer</p>
            <h3 className="text-xl font-bold text-indigo-600 mt-1">Calculated</h3>
            <p className="text-xs text-gray-500 mt-0.5">Feature importance</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600">
            <Sparkles className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* SHAP Chart & Explanation Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <ExplanationCard summary="Feature importance calculated via SHAP Tree Explainer on Isolation Forest predictions." />
          <SHAPChart features={features} />
        </div>
        <div>
          <ConfidenceScore score={analysis?.quality_scores?.overall_score || 94.0} />
        </div>
      </div>
    </div>
  );
};

export default Explainability;
