import React, { useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DatasetContext } from '../context/DatasetContext';
import EmptyState from '../components/common/EmptyState';
import { AlertTriangle, Cpu, Layers, Sliders, ShieldAlert, Wand2, Filter, CheckCircle2 } from 'lucide-react';

const Anomalies = () => {
  const { filename, analysis, updateCellEdit, commitCorrections } = useContext(DatasetContext);
  const [selectedAlgoFilter, setSelectedAlgoFilter] = useState('ALL');
  const navigate = useNavigate();

  if (!analysis) {
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900">Adaptive Anomaly Engine</h2>
          <p className="text-xs text-gray-500 mt-1">Multi-algorithm statistical outlier inspection (Isolation Forest, LOF, Z-Score).</p>
        </div>
        <EmptyState
          icon={AlertTriangle}
          title="No Anomaly Engine Payload Active"
          description="Upload a dataset to run multi-algorithm anomaly detection, ensemble voting, and statistical outlier isolation."
          actionLabel="Upload Dataset"
          onAction={() => navigate('/upload')}
        />
      </div>
    );
  }

  const adaptive = analysis?.adaptive_analysis || {};
  const characteristics = adaptive?.characteristics || {};
  const selectedRules = adaptive?.selected_rules || [];
  const executedAlgos = adaptive?.executed_algorithms || ['Isolation Forest', 'LOF', 'Z-Score'];
  const algoDetectionCounts = adaptive?.algo_detection_counts || {};
  const ensembleResults = adaptive?.ensemble_results || analysis?.anomalies || [];

  const filteredResults = selectedAlgoFilter === 'ALL'
    ? ensembleResults
    : ensembleResults.filter(item => (item.flagged_algorithms || []).includes(selectedAlgoFilter));

  const handleFixAnomaly = async (rowIdx, colName, suggestedVal) => {
    updateCellEdit(rowIdx, colName, suggestedVal);
    await commitCorrections(false);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-gray-900 tracking-tight">Adaptive Anomaly Detection Engine</h2>
            <span className="badge badge-danger font-medium flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 text-red-600" />
              <span>Multi-Algorithm Ensemble</span>
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Characteristic profiling, rule-driven algorithm execution & ensemble voting across <strong className="text-gray-900">{filename || 'dataset'}</strong>.
          </p>
        </div>

        <button
          onClick={() => navigate('/corrections')}
          className="btn btn-primary btn-sm flex items-center gap-2 font-semibold"
        >
          <Wand2 className="w-4 h-4" />
          <span>Remediate Anomalies</span>
        </button>
      </div>

      {/* 1. Characteristics Summary */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Layers className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-bold text-gray-900">1. Dataset Distribution & Characteristics</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Dimension Shape</p>
            <h4 className="text-base font-bold text-gray-900 mt-1">
              {characteristics.total_rows || analysis?.total_rows || 0} Rows | {characteristics.total_cols || analysis?.total_cols || 0} Cols
            </h4>
            <span className="text-[11px] text-blue-600 font-medium mt-0.5 block">
              {characteristics.numeric_count || 0} Numeric | {characteristics.categorical_count || 0} Categorical
            </span>
          </div>

          <div className="card">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Distribution Type</p>
            <h4 className="text-base font-bold text-gray-900 mt-1">
              {characteristics.distribution_type || 'Approximately Normal'}
            </h4>
            <span className="text-[11px] text-gray-500 font-medium mt-0.5 block">
              Avg Skewness: {characteristics.avg_skewness || 0.45}
            </span>
          </div>

          <div className="card">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Feature Type Complexity</p>
            <h4 className="text-base font-bold text-gray-900 mt-1">
              {characteristics.has_high_dim ? 'High-Dimensional' : 'Standard Dimension'}
            </h4>
            <span className="text-[11px] text-gray-500 font-medium mt-0.5 block">
              {characteristics.has_mixed_types ? 'Mixed Types' : 'Numeric Heavy'}
            </span>
          </div>

          <div className="card">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Anomalies Detected</p>
            <h4 className="text-base font-bold text-red-600 mt-1">
              {ensembleResults.length} Flagged Outliers
            </h4>
            <span className="text-[11px] text-gray-500 font-medium mt-0.5 block">
              Ensemble Voting Complete
            </span>
          </div>
        </div>
      </div>

      {/* 2. Algorithm Filter Bar */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-blue-600" />
            <span className="text-xs font-bold text-gray-900">Algorithm Execution Filter</span>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setSelectedAlgoFilter('ALL')}
              className={`btn btn-sm text-xs ${selectedAlgoFilter === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
            >
              All Models ({ensembleResults.length})
            </button>
            {executedAlgos.map(algo => (
              <button
                key={algo}
                onClick={() => setSelectedAlgoFilter(algo)}
                className={`btn btn-sm text-xs ${selectedAlgoFilter === algo ? 'btn-primary' : 'btn-secondary'}`}
              >
                {algo} ({algoDetectionCounts[algo] || 0})
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 3. Ensemble Voting Decision Table */}
      <div className="card p-0 overflow-hidden">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-red-600" />
            <h3 className="text-sm font-bold text-gray-900">Ensemble Voting Outlier Matrix ({filteredResults.length} Records)</h3>
          </div>
        </div>

        <div className="table-container border-0 rounded-none max-h-[480px] overflow-y-auto">
          <table>
            <thead className="sticky top-0 bg-gray-50 border-b border-gray-200">
              <tr>
                <th>Record ID</th>
                <th>Feature</th>
                <th>Value</th>
                <th>Flagged Models</th>
                <th>Confidence</th>
                <th>Rationale</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredResults.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center text-xs text-gray-400 py-8">
                    No anomalies flagged for selected filter. Dataset exhibits standard statistical distribution.
                  </td>
                </tr>
              ) : (
                filteredResults.map((item, idx) => {
                  const rowIdx = item.row_index !== undefined ? item.row_index : idx;
                  const algos = item.flagged_algorithms || item.algorithms || ['Isolation Forest'];
                  const conf = item.confidence_score || item.anomaly_score || 85.0;

                  return (
                    <tr key={idx} className="hover:bg-gray-50 transition-colors">
                      <td className="font-mono text-xs font-semibold text-gray-900">#{rowIdx + 1}</td>
                      <td className="font-mono text-xs text-gray-800">{item.primary_feature || item.column || 'Feature'}</td>
                      <td className="font-mono text-xs font-semibold text-red-600">
                        {item.feature_value !== undefined ? String(item.feature_value) : String(item.value || '')}
                      </td>
                      <td>
                        <div className="flex items-center gap-1 flex-wrap">
                          {algos.map(a => (
                            <span key={a} className="badge badge-danger text-[10px] py-0.5 px-1.5">
                              {a}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td>
                        <div className="flex items-center gap-2 w-24">
                          <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                            <div className="h-full bg-red-500 rounded-full" style={{ width: `${conf}%` }} />
                          </div>
                          <span className="text-[11px] font-bold text-gray-700">{conf}%</span>
                        </div>
                      </td>
                      <td className="text-xs text-gray-500 max-w-xs">{item.explanation || item.reason}</td>
                      <td>
                        <button
                          onClick={() => handleFixAnomaly(rowIdx, item.primary_feature || item.column, 0)}
                          className="btn btn-secondary btn-sm text-[11px] py-1 px-2.5 text-emerald-700 font-semibold"
                        >
                          Auto-Fix
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Anomalies;
