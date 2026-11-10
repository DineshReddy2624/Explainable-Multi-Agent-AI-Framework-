import React, { useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DatasetContext } from '../context/DatasetContext';
import EmptyState from '../components/common/EmptyState';
import {
  AlertTriangle,
  Layers,
  ShieldAlert,
  Wand2,
  Filter,
  CheckCircle2,
  X,
  Edit3,
  Trash2,
  EyeOff,
  Sparkles,
  Zap,
  ArrowLeft,
  ArrowRight,
  ShieldCheck,
  Info
} from 'lucide-react';

const Anomalies = () => {
  const {
    filename,
    analysis,
    currentDataset,
    anomalyDecisions,
    anomalyStageSummary,
    applyAnomalyManualFix,
    applyAnomalyAiFix,
    applyAnomalyAiFixAll,
    applyAnomalyIgnore,
    applyAnomalyRemoveRecord
  } = useContext(DatasetContext);

  const [selectedAlgoFilter, setSelectedAlgoFilter] = useState('ALL');
  const [notification, setNotification] = useState(null);
  const navigate = useNavigate();

  // Manual Fix Modal State
  const [manualModal, setManualModal] = useState({
    isOpen: false,
    rowIdx: null,
    column: '',
    currentValue: '',
    inputValue: ''
  });

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
  const executedAlgos = adaptive?.executed_algorithms || ['Isolation Forest', 'IQR', 'LOF', 'Z-Score'];
  const algoDetectionCounts = adaptive?.algo_detection_counts || {};

  // All anomalies currently detected in currentDataset
  const rawEnsemble = adaptive?.ensemble_results || analysis?.anomalies || [];

  const filteredResults = selectedAlgoFilter === 'ALL'
    ? rawEnsemble
    : rawEnsemble.filter(item => (item.flagged_algorithms || []).includes(selectedAlgoFilter));

  const pendingAnomalies = filteredResults.filter((item, idx) => {
    const rowIdx = item.row_index !== undefined ? item.row_index : idx;
    const colName = item.primary_feature || item.column || 'Feature';
    return !anomalyDecisions[`${rowIdx}_${colName}`];
  });

  const handleOpenManualModal = (rowIdx, colName, currVal) => {
    setManualModal({
      isOpen: true,
      rowIdx,
      column: colName,
      currentValue: currVal,
      inputValue: ''
    });
  };

  const handleApplyManualModal = () => {
    const { rowIdx, column, inputValue } = manualModal;
    if (inputValue === undefined || inputValue === null || inputValue.trim() === '') {
      alert('Please provide a replacement value.');
      return;
    }

    applyAnomalyManualFix(rowIdx, column, inputValue.trim());
    setNotification({
      type: 'success',
      text: `Manually corrected Record #${rowIdx + 1} (${column} = ${inputValue.trim()}). Dataset updated.`
    });
    setManualModal({ isOpen: false, rowIdx: null, column: '', currentValue: '', inputValue: '' });
    setTimeout(() => setNotification(null), 5000);
  };

  const handleAiFix = (rowIdx, colName, item) => {
    const res = applyAnomalyAiFix(rowIdx, colName, item);
    if (res?.success) {
      setNotification({
        type: 'success',
        text: `AI replaced outlier in Row #${rowIdx + 1} (${colName} -> ${res.replacementVal}). Continuous dataset updated.`
      });
    } else {
      setNotification({
        type: 'warning',
        text: 'AI cannot safely determine a correction. Manual review required.'
      });
    }
    setTimeout(() => setNotification(null), 5000);
  };

  // AI Fix All — applies AI median/bounding fix to all pending outliers at once
  const handleAiFixAll = (items) => {
    if (!items || items.length === 0) return;

    if (applyAnomalyAiFixAll) {
      const { fixedCount, reviewCount } = applyAnomalyAiFixAll(items);
      const msg = fixedCount > 0
        ? `AI Fix All successfully corrected ${fixedCount} outlier record${fixedCount !== 1 ? 's' : ''}.${reviewCount > 0 ? ` ${reviewCount} record(s) need manual review.` : ''}`
        : `${reviewCount} record(s) require manual review — AI cannot safely infer those values.`;
      setNotification({ type: fixedCount > 0 ? 'success' : 'warning', text: msg });
      setTimeout(() => setNotification(null), 6000);
      return;
    }

    let fixedCount = 0;
    let reviewCount = 0;
    items.forEach((item, idx) => {
      const rowIdx = item.row_index !== undefined ? item.row_index : idx;
      const colName = item.primary_feature || item.column || 'Feature';
      const res = applyAnomalyAiFix(rowIdx, colName, item);
      if (res?.success) fixedCount++;
      else reviewCount++;
    });
    const msg = fixedCount > 0
      ? `AI Fix All successfully corrected ${fixedCount} outlier record${fixedCount !== 1 ? 's' : ''}.${reviewCount > 0 ? ` ${reviewCount} record(s) need manual review.` : ''}`
      : `${reviewCount} record(s) require manual review — AI cannot safely infer those values.`;
    setNotification({ type: fixedCount > 0 ? 'success' : 'warning', text: msg });
    setTimeout(() => setNotification(null), 6000);
  };

  const handleIgnore = (rowIdx, colName, item) => {
    applyAnomalyIgnore(rowIdx, colName, item);
    setNotification({
      type: 'info',
      text: `Outlier at Row #${rowIdx + 1} (${colName}) ignored. Value remains intact in dataset.`
    });
    setTimeout(() => setNotification(null), 5000);
  };

  const handleRemoveRecord = (rowIdx, colName, item) => {
    if (window.confirm(`Are you sure you want to permanently delete outlier Record #${rowIdx + 1} from the current dataset?`)) {
      applyAnomalyRemoveRecord(rowIdx, colName, item);
      setNotification({
        type: 'warning',
        text: `Record #${rowIdx + 1} was removed from the continuous dataset. Total rows decremented.`
      });
      setTimeout(() => setNotification(null), 5000);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      {/* Toast Notification */}
      {notification && (
        <div
          className={`px-4 py-3 rounded-xl flex items-center justify-between text-xs font-semibold shadow-sm animate-fade-in ${
            notification.type === 'success'
              ? 'bg-emerald-50 border border-emerald-200 text-emerald-900'
              : notification.type === 'warning'
              ? 'bg-amber-50 border border-amber-200 text-amber-900'
              : 'bg-blue-50 border border-blue-200 text-blue-900'
          }`}
        >
          <div className="flex items-center gap-2.5">
            {notification.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            ) : notification.type === 'warning' ? (
              <AlertTriangle className="w-4 h-4 text-amber-600" />
            ) : (
              <Info className="w-4 h-4 text-blue-600" />
            )}
            <span className="font-bold">{notification.text}</span>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="p-1 rounded-md hover:bg-black/5 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-gray-900 tracking-tight">Step 4: Anomaly Detection & Remediation</h2>
            <span className="badge badge-danger font-medium flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 text-red-600" />
              <span>Multi-Algorithm Ensemble</span>
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Running against <strong>qualityCorrectedDataset</strong> across <strong className="text-gray-900">{filename || 'dataset'}</strong>.
          </p>
        </div>

        <button
          onClick={() => navigate('/corrections')}
          className="btn btn-primary btn-sm flex items-center gap-2 font-semibold text-xs"
        >
          <span>Next: AI Remediation</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Anomaly Completion Status Tracker */}
      <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
        <div className="flex items-center justify-between border-b border-gray-100 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-red-600" />
            <h3 className="text-sm font-bold text-gray-900">Anomaly Remediation Status Tracker</h3>
          </div>
          <span className="text-xs text-gray-500 font-medium">
            Active Records: <strong className="text-gray-900">{(currentDataset || []).length}</strong> rows
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-6 gap-3 text-center">
          <div className="p-3 bg-red-50 rounded-xl border border-red-100">
            <p className="text-[11px] font-semibold text-red-700 uppercase tracking-wider">Total Anomalies</p>
            <h4 className="text-xl font-bold text-red-700 mt-1">{anomalyStageSummary.total}</h4>
            <span className="text-[10px] text-red-600">Ensemble Flagged</span>
          </div>
          <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-100">
            <p className="text-[11px] font-semibold text-emerald-700 uppercase tracking-wider">Manually Fixed</p>
            <h4 className="text-xl font-bold text-emerald-700 mt-1">{anomalyStageSummary.manualFixed}</h4>
            <span className="text-[10px] text-emerald-600">User Override</span>
          </div>
          <div className="p-3 bg-blue-50 rounded-xl border border-blue-100">
            <p className="text-[11px] font-semibold text-blue-700 uppercase tracking-wider">AI Fixed</p>
            <h4 className="text-xl font-bold text-blue-700 mt-1">{anomalyStageSummary.aiFixed}</h4>
            <span className="text-[10px] text-blue-600">Median / Bounding</span>
          </div>
          <div className="p-3 bg-gray-100 rounded-xl border border-gray-200">
            <p className="text-[11px] font-semibold text-gray-600 uppercase tracking-wider">Ignored</p>
            <h4 className="text-xl font-bold text-gray-700 mt-1">{anomalyStageSummary.ignored}</h4>
            <span className="text-[10px] text-gray-500">Maintained As-Is</span>
          </div>
          <div className="p-3 bg-rose-50 rounded-xl border border-rose-100">
            <p className="text-[11px] font-semibold text-rose-700 uppercase tracking-wider">Removed</p>
            <h4 className="text-xl font-bold text-rose-700 mt-1">{anomalyStageSummary.removed}</h4>
            <span className="text-[10px] text-rose-600">Rows Deleted</span>
          </div>
          <div className="p-3 bg-amber-50 rounded-xl border border-amber-100">
            <p className="text-[11px] font-semibold text-amber-700 uppercase tracking-wider">Requires Review</p>
            <h4 className="text-xl font-bold text-amber-700 mt-1">{anomalyStageSummary.reviewNeeded}</h4>
            <span className="text-[10px] text-amber-600">Manual Check</span>
          </div>
        </div>
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
              {(currentDataset || []).length || analysis?.total_rows || 0} Rows | {characteristics.total_cols || analysis?.total_cols || 0} Cols
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
              Avg Skewness: {characteristics.avg_skewness || 0.42}
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
              {rawEnsemble.length} Flagged Outliers
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
              All Models ({rawEnsemble.length})
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

      {/* 3. Ensemble Voting Decision Table with 4 Actions */}
      <div className="card p-0 overflow-hidden">
        <div className="p-4 border-b border-gray-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-gradient-to-r from-red-50/40 to-transparent">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-red-600" />
            <h3 className="text-sm font-bold text-gray-900">
              Ensemble Voting Outlier Matrix ({filteredResults.length} Outlier Records)
            </h3>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-400 font-medium hidden md:inline">Actions directly alter continuous dataset</span>
            {pendingAnomalies.length > 0 && (
              <button
                onClick={() => handleAiFixAll(pendingAnomalies)}
                className="btn btn-primary btn-sm flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 shadow-sm"
                title="Apply AI median/bounding fix to all outlier records at once"
              >
                <Zap className="w-3.5 h-3.5" />
                <span>AI Fix All ({pendingAnomalies.length})</span>
              </button>
            )}
            {pendingAnomalies.length === 0 && filteredResults.length > 0 && (
              <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                All Anomalies Addressed
              </span>
            )}
          </div>
        </div>

        <div className="table-container border-0 rounded-none max-h-[500px] overflow-y-auto">
          <table>
            <thead className="sticky top-0 bg-gray-50 border-b border-gray-200">
              <tr>
                <th>Record ID</th>
                <th>Feature</th>
                <th>Value</th>
                <th>Flagged Models</th>
                <th>Confidence</th>
                <th>Rationale</th>
                <th className="text-center">Remediation Choices</th>
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
                  const colName = item.primary_feature || item.column || 'Feature';
                  const algos = item.flagged_algorithms || ['Isolation Forest'];
                  const conf = item.confidence_score || item.anomaly_score || 85.0;
                  const currVal = item.feature_value !== undefined ? String(item.feature_value) : String(item.value || '');

                  const key = `${rowIdx}_${colName}`;
                  const decision = anomalyDecisions[key];

                  return (
                    <tr key={idx} className="hover:bg-red-50/20 transition-colors">
                      <td className="font-mono text-xs font-semibold text-gray-900">#{rowIdx + 1}</td>
                      <td className="font-mono text-xs font-bold text-gray-800">{colName}</td>
                      <td className="font-mono text-xs font-bold text-red-600">
                        {currVal}
                      </td>
                      <td>
                        <div className="flex items-center gap-1 flex-wrap">
                          {algos.map(a => (
                            <span key={a} className="badge badge-danger text-[10px] py-0.5 px-1.5 font-semibold">
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
                        {decision ? (
                          <div className="flex items-center justify-center gap-1.5">
                            <span
                              className={`px-2.5 py-1 rounded-md text-xs font-bold ${
                                decision.status === 'AI Fixed'
                                  ? 'bg-blue-100 text-blue-800 border border-blue-300'
                                  : decision.status === 'Manually Fixed'
                                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                  : decision.status === 'Removed'
                                  ? 'bg-rose-100 text-rose-800 border border-rose-300'
                                  : 'bg-gray-100 text-gray-700 border border-gray-300'
                              }`}
                            >
                              {decision.status} {decision.fixedValue !== undefined ? `(${decision.fixedValue})` : ''}
                            </span>
                          </div>
                        ) : (
                          <div className="flex items-center justify-center gap-1.5">
                            {/* Manual Fix */}
                            <button
                              onClick={() => handleOpenManualModal(rowIdx, colName, currVal)}
                              className="btn btn-secondary btn-xs text-[11px] py-1 px-2 text-emerald-700 font-semibold hover:bg-emerald-50 hover:border-emerald-300 flex items-center gap-1"
                              title="Enter custom correction value"
                            >
                              <Edit3 className="w-3 h-3" />
                              <span>Manual</span>
                            </button>

                            {/* AI Fix */}
                            <button
                              onClick={() => handleAiFix(rowIdx, colName, item)}
                              className="btn btn-primary btn-xs text-[11px] py-1 px-2 font-semibold flex items-center gap-1"
                              title="Apply AI median/bounding correction"
                            >
                              <Sparkles className="w-3 h-3" />
                              <span>AI Fix</span>
                            </button>

                            {/* Ignore */}
                            <button
                              onClick={() => handleIgnore(rowIdx, colName, item)}
                              className="btn btn-secondary btn-xs text-[11px] py-1 px-1.5 text-gray-500 hover:text-gray-800"
                              title="Keep anomaly unmodified"
                            >
                              <EyeOff className="w-3 h-3" />
                              <span>Ignore</span>
                            </button>

                            {/* Remove Record */}
                            <button
                              onClick={() => handleRemoveRecord(rowIdx, colName, item)}
                              className="btn btn-secondary btn-xs text-[11px] py-1 px-1.5 text-rose-600 hover:bg-rose-50 hover:border-rose-300"
                              title="Delete this entire row from dataset"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Manual Anomaly Fix Modal */}
      {manualModal.isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 border border-gray-200">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100 mb-4">
              <div className="flex items-center gap-2">
                <Edit3 className="w-4 h-4 text-emerald-600" />
                <h3 className="text-sm font-bold text-gray-900">Manual Anomaly Correction</h3>
              </div>
              <button
                onClick={() => setManualModal({ isOpen: false, rowIdx: null, column: '', currentValue: '', inputValue: '' })}
                className="p-1 text-gray-400 hover:text-gray-700 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 flex justify-between items-center">
                <span className="text-gray-500">Record ID:</span>
                <span className="font-mono font-bold text-gray-900">Row #{manualModal.rowIdx + 1}</span>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 flex justify-between items-center">
                <span className="text-gray-500">Outlier Feature:</span>
                <span className="font-mono font-bold text-gray-900">{manualModal.column}</span>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 flex justify-between items-center">
                <span className="text-gray-500">Current Outlier Value:</span>
                <span className="font-mono text-red-600 font-bold">{String(manualModal.currentValue)}</span>
              </div>

              <div className="pt-2">
                <label className="block text-xs font-bold text-gray-700 mb-1">
                  Enter Corrected Value:
                </label>
                <input
                  type="text"
                  value={manualModal.inputValue}
                  onChange={(e) => setManualModal(m => ({ ...m, inputValue: e.target.value }))}
                  placeholder={`e.g. 90000`}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs font-mono focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleApplyManualModal();
                  }}
                />
                <p className="text-[11px] text-gray-400 mt-1">
                  The value will be applied to the continuous dataset and recorded in the audit trail.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-5 border-t border-gray-100 mt-5">
              <button
                onClick={() => setManualModal({ isOpen: false, rowIdx: null, column: '', currentValue: '', inputValue: '' })}
                className="btn btn-secondary btn-sm text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleApplyManualModal}
                className="btn btn-primary btn-sm text-xs font-semibold px-4"
              >
                Apply Manual Correction
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Workflow Bottom Navigation Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-5 bg-white rounded-xl border border-gray-200 shadow-sm mt-8">
        <button
          onClick={() => navigate('/issues')}
          className="btn btn-secondary btn-sm flex items-center gap-2 font-semibold px-4 py-2.5 text-xs text-gray-700 hover:bg-gray-100"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back: Quality Issues</span>
        </button>
        <button
          onClick={() => navigate('/corrections')}
          className="btn btn-primary btn-sm flex items-center gap-2 font-semibold px-5 py-2.5 shadow-sm text-xs"
        >
          <span>Next: AI Remediation</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default Anomalies;
