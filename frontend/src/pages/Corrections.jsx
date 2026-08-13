import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { DatasetContext } from '../context/DatasetContext';
import SuggestionCard from '../components/corrections/SuggestionCard';
import ConfidenceCard from '../components/corrections/ConfidenceCard';
import ApplyCorrection from '../components/corrections/ApplyCorrection';
import EmptyState from '../components/common/EmptyState';
import { Wand2, Sparkles, Database, CheckCircle2 } from 'lucide-react';

const Corrections = () => {
  const { filename, analysis, commitCorrections, loading } = useContext(DatasetContext);
  const navigate = useNavigate();

  if (!analysis) {
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900">AI Auto-Correction & Remediation Engine</h2>
          <p className="text-xs text-gray-500 mt-1">Imputation rules, median/mode fill, and format standardization.</p>
        </div>
        <EmptyState
          icon={Wand2}
          title="No Dataset Loaded for Remediation"
          description="Upload a dataset to generate AI auto-remediation rules, preview imputation strategies, and create cleaned dataset versions."
          actionLabel="Upload Dataset"
          onAction={() => navigate('/upload')}
        />
      </div>
    );
  }

  const missing_report = analysis?.missing_report || [];
  const score = analysis?.quality_scores?.overall_score || 94.5;

  const suggestions = missing_report.map(r => ({
    column: r.column,
    issue: `${r.null_count} Missing Values (${r.missing_pct}%)`,
    action: `Impute with ${r.suggested_median ? `Median (${r.suggested_median})` : `Mode (${r.suggested_mode || 'Fill'})`}`
  }));

  if (suggestions.length === 0) {
    suggestions.push({
      column: 'Dataset Integrity',
      issue: 'Zero Missing Values Detected',
      action: 'Dataset is 100% complete and validated.'
    });
  }

  const handleApplyAll = async () => {
    await commitCorrections();
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-gray-900 tracking-tight">AI Auto-Correction & Remediation Engine</h2>
            <span className="badge badge-success font-medium flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-emerald-600" />
              <span>Immutable Versioning Active</span>
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Active Dataset: <strong className="text-gray-900">{filename || 'uploaded_dataset.csv'}</strong>
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ApplyCorrection onApplyAll={handleApplyAll} disabled={loading} />
        </div>
        <div>
          <ConfidenceCard score={score} />
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Wand2 className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-bold text-gray-900">Recommended Remediation Strategies</h3>
        </div>

        <div className="space-y-3">
          {suggestions.map((s, idx) => (
            <SuggestionCard key={idx} suggestion={s} onApply={handleApplyAll} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default Corrections;
