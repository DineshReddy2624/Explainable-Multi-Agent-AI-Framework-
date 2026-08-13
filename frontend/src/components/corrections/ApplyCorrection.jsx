import React from 'react';
import { Sparkles, ArrowRight } from 'lucide-react';

const ApplyCorrection = ({ onApplyAll, disabled = false }) => {
  return (
    <div className="card p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-gradient-to-r from-blue-50/50 to-indigo-50/50 border-blue-200">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shrink-0 shadow-sm">
          <Sparkles className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-gray-900">Auto-Remediate All Detected Dataset Issues</h3>
          <p className="text-xs text-gray-600 mt-0.5">
            Executes AI Imputation, Outlier Isolation, and Format Standardizer while creating an immutable new dataset version.
          </p>
        </div>
      </div>

      <button
        onClick={onApplyAll}
        disabled={disabled}
        className="btn btn-primary btn-sm flex items-center gap-2 font-semibold shrink-0"
      >
        <span>Execute All Fixes</span>
        <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
};

export default ApplyCorrection;
