import React, { useState } from 'react';
import { Settings as SettingsIcon, Sliders, ShieldCheck, Save, CheckCircle2 } from 'lucide-react';

const Settings = () => {
  const [contamination, setContamination] = useState(0.05);
  const [imputationStrategy, setImputationStrategy] = useState('median');
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-gray-900 tracking-tight">Enterprise Platform Settings</h2>
            <span className="badge badge-info font-medium">Tenant Preferences</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Configure machine learning model thresholds, auto-remediation rules, and data privacy policies.
          </p>
        </div>
      </div>

      {saved && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-700 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>Platform configuration updated successfully!</span>
        </div>
      )}

      <form onSubmit={handleSave} className="card space-y-6">
        <div className="flex items-center gap-2 border-b border-gray-200 pb-4">
          <Sliders className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-bold text-gray-900">AI Agent Threshold Preferences</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Isolation Forest Contamination Ratio
            </label>
            <input
              type="number"
              value={contamination}
              onChange={e => setContamination(Number(e.target.value))}
              step={0.01}
              min={0.01}
              max={0.2}
              className="input"
            />
            <p className="text-[11px] text-gray-400 mt-1">Expected proportion of outliers in the dataset (default: 0.05).</p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Auto-Imputation Default Strategy
            </label>
            <select
              value={imputationStrategy}
              onChange={e => setImputationStrategy(e.target.value)}
              className="input bg-white"
            >
              <option value="median">Median Imputation</option>
              <option value="mean">Mean Imputation</option>
              <option value="mode">Mode / Most Frequent</option>
              <option value="knn">KNN Imputation</option>
            </select>
            <p className="text-[11px] text-gray-400 mt-1">Default mathematical rule for missing null cell imputation.</p>
          </div>
        </div>

        <div className="pt-4 border-t border-gray-200 flex justify-end">
          <button type="submit" className="btn btn-primary btn-sm flex items-center gap-2 font-semibold">
            <Save className="w-4 h-4" />
            <span>Save Preferences</span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default Settings;
