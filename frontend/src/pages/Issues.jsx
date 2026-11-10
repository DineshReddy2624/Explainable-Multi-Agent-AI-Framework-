import React, { useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DatasetContext } from '../context/DatasetContext';
import MissingTable from '../components/issues/MissingTable';
import FormatTable from '../components/issues/FormatTable';
import AnomalyTable from '../components/issues/AnomalyTable';
import EmptyState from '../components/common/EmptyState';
import {
  AlertCircle,
  Wand2,
  CheckCircle2,
  ArrowLeft,
  ArrowRight,
  ShieldCheck,
  HelpCircle,
  X,
  Edit3,
  EyeOff,
  Sparkles,
  Info,
  Check,
  Zap
} from 'lucide-react';

const Issues = () => {
  const {
    analysis,
    filename,
    rawRecords,
    originalRecords,
    qualityIssueDecisions,
    qualityStageSummary,
    applyQualityManualFix,
    applyQualityAiFix,
    applyQualityAiFixBatch,
    applyQualityIgnore
  } = useContext(DatasetContext);

  const navigate = useNavigate();

  // Manual Fix Modal State
  const [manualModal, setManualModal] = useState({
    isOpen: false,
    column: '',
    rowIdx: null,
    oldValue: '',
    inputValue: ''
  });

  // Action Notification Banner
  const [notification, setNotification] = useState(null);

  if (!analysis) {
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900">Detected Quality Issues & Formatting Errors</h2>
          <p className="text-xs text-gray-500 mt-1">Multi-agent detection report for null cells, invalid formats, and anomalies.</p>
        </div>
        <EmptyState
          icon={AlertCircle}
          title="No Dataset Quality Issues Active"
          description="Upload a CSV or XLSX dataset to run real-time issue detection, format validation, and automated quality auditing."
          actionLabel="Upload Dataset"
          onAction={() => navigate('/upload')}
        />
      </div>
    );
  }

  const missingReport = analysis?.missing_report || [];
  const formatIssues = analysis?.format_issues || [];

  const handleOpenManualModal = (column, rowIdx = null, sampleVal = '') => {
    let oldVal = sampleVal;
    if (oldVal === '' && rowIdx !== null && rawRecords[rowIdx]) {
      oldVal = rawRecords[rowIdx][column];
    }
    setManualModal({
      isOpen: true,
      column,
      rowIdx,
      oldValue: oldVal ?? '[NULL]',
      inputValue: ''
    });
  };

  const handleApplyManualModal = () => {
    const { column, rowIdx, inputValue } = manualModal;
    if (inputValue === undefined || inputValue === null || inputValue.trim() === '') {
      alert('Please provide a replacement value.');
      return;
    }

    if (rowIdx !== null) {
      applyQualityManualFix(rowIdx, column, inputValue.trim());
      setNotification({
        type: 'success',
        text: `Manually updated Row #${rowIdx + 1} (${column} = "${inputValue.trim()}"). Dataset updated.`
      });
    } else {
      // Find all rows that need fix in this column
      const nullRows = missingReport.find(m => m.column === column)?.null_rows || [];
      const targetIndices = nullRows.length > 0 ? nullRows : [0];
      targetIndices.forEach(idx => {
        applyQualityManualFix(idx, column, inputValue.trim());
      });
      setNotification({
        type: 'success',
        text: `Manually applied "${inputValue.trim()}" across ${targetIndices.length} missing cells in ${column}. Dataset updated.`
      });
    }

    setManualModal({ isOpen: false, column: '', rowIdx: null, oldValue: '', inputValue: '' });
    setTimeout(() => setNotification(null), 5000);
  };

  const handleAiFix = (column, rowIdx = null, issueType = 'missing') => {
    const res = applyQualityAiFix(column, rowIdx, issueType);
    if (res?.strategy === 'Manual review required' || res?.success === false) {
      setNotification({
        type: 'warning',
        text: `AI cannot safely infer "${column}". Manual review required to avoid hallucinating data.`
      });
    } else {
      setNotification({
        type: 'success',
        text: `AI applied ${res?.strategy || 'Correction'} on ${column}. Dataset updated and stats recalculated.`
      });
    }
    setTimeout(() => setNotification(null), 5000);
  };

  // Format items display limit for smooth UI rendering with high item counts
  const [formatDisplayLimit, setFormatDisplayLimit] = useState(20);

  // AI Fix All — applies AI fix to every item in the given list atomically in one pass
  const handleAiFixAll = (items, issueType = 'missing') => {
    if (!items || items.length === 0) return;
    try {
      const res = applyQualityAiFixBatch(items, issueType);
      const fixedCount = res?.fixedCount || 0;
      const reviewCount = res?.reviewCount || 0;

      const msg = fixedCount > 0
        ? `AI Fix All successfully resolved ${fixedCount} ${issueType === 'format' ? 'formatting irregularities' : 'missing values'}.${reviewCount > 0 ? ` ${reviewCount} item(s) require manual review.` : ''}`
        : `${reviewCount} item(s) require manual review — AI cannot safely infer those values.`;

      setNotification({ type: fixedCount > 0 ? 'success' : 'warning', text: msg });
      setTimeout(() => setNotification(null), 6000);
    } catch (err) {
      console.error("AI Fix All error:", err);
      setNotification({ type: 'warning', text: 'Error applying AI Fix All. Please try individual fixes.' });
      setTimeout(() => setNotification(null), 5000);
    }
  };

  const handleIgnore = (column, rowIdx = null, issueType = 'missing') => {
    applyQualityIgnore(column, rowIdx, issueType);
    setNotification({
      type: 'info',
      text: `Marked issue in ${column} as Ignored. Value remains unchanged in dataset.`
    });
    setTimeout(() => setNotification(null), 5000);
  };

  // Build legacy tables data
  const missingData = missingReport.map(r => ({
    column: r.column,
    missing_count: r.null_count,
    percentage: r.missing_pct
  }));

  const formatData = formatIssues.map(r => ({
    column: r.column,
    expected_format: r.expected_format || 'Standard Format',
    invalid_count: 1,
    invalid_value: r.invalid_value,
    row_index: r.row_index
  }));

  const anomalyData = (analysis?.anomalies || []).map(a => {
    const rawScore = a.anomaly_score ?? a.confidence_score ?? 0.85;
    const scoreVal = typeof rawScore === 'number'
      ? (rawScore > 1 ? (rawScore / 100).toFixed(2) : rawScore.toFixed(2))
      : String(rawScore);
    return {
      algorithm: `Row #${a.row_index + 1} (${a.column})`,
      anomaly_count: scoreVal
    };
  });

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
              <AlertCircle className="w-4 h-4 text-amber-600" />
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

      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-gray-900 tracking-tight">Step 3: Quality Issues Remediation</h2>
            <span className="badge badge-warning font-medium">Interactive Engine</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Choose remediation action for each detected issue: <strong>Manual Fix</strong>, <strong>AI Fix</strong>, or <strong>Ignore</strong>.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/anomalies')}
            className="btn btn-primary btn-sm flex items-center gap-2 font-semibold text-xs"
          >
            <span>Proceed to Anomalies</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Quality Completion Summary Metrics Bar */}
      <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
        <div className="flex items-center justify-between border-b border-gray-100 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm font-bold text-gray-900">Quality Remediation Status Tracker</h3>
          </div>
          <span className="text-xs text-gray-500 font-medium">
            Dataset: <strong className="text-gray-900">{filename || 'dataset.csv'}</strong>
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">
          <div className="p-3 bg-gray-50 rounded-xl border border-gray-100">
            <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider">Total Issues</p>
            <h4 className="text-xl font-bold text-gray-900 mt-1">{qualityStageSummary?.total ?? 0}</h4>
            <span className="text-[10px] text-gray-400">Detected Quality Flaws</span>
          </div>
          <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-100">
            <p className="text-[11px] font-semibold text-emerald-700 uppercase tracking-wider">Manually Fixed</p>
            <h4 className="text-xl font-bold text-emerald-700 mt-1">{qualityStageSummary?.manualFixed ?? 0}</h4>
            <span className="text-[10px] text-emerald-600">User Specified</span>
          </div>
          <div className="p-3 bg-blue-50 rounded-xl border border-blue-100">
            <p className="text-[11px] font-semibold text-blue-700 uppercase tracking-wider">AI Fixed</p>
            <h4 className="text-xl font-bold text-blue-700 mt-1">{qualityStageSummary?.aiFixed ?? 0}</h4>
            <span className="text-[10px] text-blue-600">Statistical Imputation</span>
          </div>
          <div className="p-3 bg-gray-100 rounded-xl border border-gray-200">
            <p className="text-[11px] font-semibold text-gray-600 uppercase tracking-wider">Ignored</p>
            <h4 className="text-xl font-bold text-gray-700 mt-1">{qualityStageSummary?.ignored ?? 0}</h4>
            <span className="text-[10px] text-gray-500">Left Unmodified</span>
          </div>
          <div className="p-3 bg-amber-50 rounded-xl border border-amber-100">
            <p className="text-[11px] font-semibold text-amber-700 uppercase tracking-wider">Requires Review</p>
            <h4 className="text-xl font-bold text-amber-700 mt-1">{qualityStageSummary?.reviewNeeded ?? 0}</h4>
            <span className="text-[10px] text-amber-600">Manual Check Required</span>
          </div>
        </div>
      </div>

      {/* Interactive Quality Issues Remediation Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Wand2 className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm font-bold text-gray-900">Missing Values Remediation Controls</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Select Manual Fix, AI Fix, or Ignore per feature</span>
            {missingReport.length > 0 && (
              <button
                onClick={() => handleAiFixAll(missingReport, 'missing')}
                className="btn btn-primary btn-sm flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 shadow-sm"
                title="Apply AI fix to all missing value columns at once"
              >
                <Zap className="w-3.5 h-3.5" />
                <span>AI Fix All ({missingReport.length})</span>
              </button>
            )}
          </div>
        </div>

        {missingReport.length === 0 ? (
          <div className="card p-6 text-center text-gray-500 text-xs flex flex-col items-center justify-center gap-2">
            <CheckCircle2 className="w-8 h-8 text-emerald-500" />
            <p className="font-bold text-gray-800 text-sm">No Missing Values in Dataset!</p>
            <p className="text-gray-400">All features are 100% complete and validated.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {missingReport.map((item, idx) => {
              const col = item.column;
              const decision = Object.values(qualityIssueDecisions).find(d => d.column === col);
              const status = decision?.status || (item.null_count === 0 ? 'Resolved' : 'Detected');

              return (
                <div key={idx} className="card p-5 border border-gray-200 hover:border-blue-300 transition-all shadow-xs flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-xs font-bold text-gray-900 bg-gray-100 px-2 py-0.5 rounded border border-gray-200">
                        {col}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          status === 'AI Fixed'
                            ? 'bg-blue-100 text-blue-800 border border-blue-200'
                            : status === 'Manually Fixed'
                            ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                            : status === 'Ignored'
                            ? 'bg-gray-100 text-gray-600 border border-gray-300'
                            : status === 'Requires Manual Review'
                            ? 'bg-amber-100 text-amber-800 border border-amber-200'
                            : 'bg-red-50 text-red-700 border border-red-200'
                        }`}
                      >
                        {status}
                      </span>
                    </div>

                    <div className="my-2">
                      <p className="text-sm font-bold text-gray-800">{item.null_count} missing values</p>
                      <p className="text-xs text-gray-500">{item.missing_pct}% of total rows</p>
                    </div>

                    <div className="bg-blue-50/60 p-2 rounded-lg border border-blue-100 text-[11px] text-gray-600 mb-4">
                      <span className="font-semibold text-blue-900 block mb-0.5">Recommended Strategy:</span>
                      <span>
                        {item.suggested_median !== undefined
                          ? `Median Imputation (${item.suggested_median})`
                          : `Mode Imputation (${item.suggested_mode || 'Active'})`}
                      </span>
                    </div>
                  </div>

                  {/* Remediation Action Controls */}
                  <div className="flex items-center gap-2 pt-2 border-t border-gray-100">
                    <button
                      onClick={() => handleOpenManualModal(col, item.null_rows?.[0] ?? 0)}
                      className="btn btn-secondary btn-sm flex-1 text-xs py-1.5 flex items-center justify-center gap-1 font-medium hover:bg-emerald-50 hover:text-emerald-700 hover:border-emerald-300 transition-colors"
                    >
                      <Edit3 className="w-3 h-3" />
                      <span>Manual Fix</span>
                    </button>
                    <button
                      onClick={() => handleAiFix(col, null, 'missing')}
                      className="btn btn-primary btn-sm flex-1 text-xs py-1.5 flex items-center justify-center gap-1 font-medium shadow-xs"
                    >
                      <Sparkles className="w-3 h-3" />
                      <span>AI Fix</span>
                    </button>
                    <button
                      onClick={() => handleIgnore(col, null, 'missing')}
                      className="btn btn-secondary btn-sm text-xs py-1.5 px-2.5 text-gray-500 hover:text-gray-800 hover:bg-gray-100 transition-colors"
                      title="Keep original values without modification"
                    >
                      <EyeOff className="w-3 h-3" />
                      <span>Ignore</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Format Inconsistencies Remediation Section */}
      {formatIssues.length > 0 && (
        <div className="space-y-4 pt-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-cyan-600" />
              <h3 className="text-sm font-bold text-gray-900">Format &amp; Range Inconsistencies</h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">{formatIssues.length} Formatting Irregularities Flagged</span>
              <button
                onClick={() => handleAiFixAll(formatIssues, 'format')}
                className="btn btn-primary btn-sm flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 shadow-sm"
                title="Apply AI fix to all format issues at once"
              >
                <Zap className="w-3.5 h-3.5" />
                <span>AI Fix All ({formatIssues.length})</span>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {formatIssues.slice(0, formatDisplayLimit).map((item, idx) => {
              const col = item.column;
              const rowIdx = item.row_index ?? 0;
              const key = `${rowIdx}_${col}`;
              const decision = qualityIssueDecisions[key];
              const status = decision?.status || 'Detected';

              return (
                <div key={idx} className="card p-4 border border-gray-200 hover:border-cyan-300 transition-all flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-gray-900">{col}</span>
                        <span className="text-[10px] font-mono text-gray-400">Row #{rowIdx + 1}</span>
                      </div>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          status === 'AI Fixed'
                            ? 'bg-blue-100 text-blue-800 border border-blue-200'
                            : status === 'Manually Fixed'
                            ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                            : status === 'Ignored'
                            ? 'bg-gray-100 text-gray-600 border border-gray-300'
                            : 'bg-cyan-100 text-cyan-800 border border-cyan-200'
                        }`}
                      >
                        {status}
                      </span>
                    </div>

                    <div className="text-xs text-gray-600 space-y-1 mb-3">
                      <div>
                        <span className="text-gray-400">Current Value: </span>
                        <span className="font-mono text-red-600 font-bold bg-red-50 px-1.5 py-0.5 rounded">
                          {String(item.invalid_value)}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">Expected Format: </span>
                        <span className="font-semibold text-gray-800">{item.expected_format}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-2 border-t border-gray-100">
                    <button
                      onClick={() => handleOpenManualModal(col, rowIdx, item.invalid_value)}
                      className="btn btn-secondary btn-sm flex-1 text-xs py-1.5 flex items-center justify-center gap-1 font-medium hover:bg-emerald-50 hover:text-emerald-700"
                    >
                      <Edit3 className="w-3 h-3" />
                      <span>Manual Fix</span>
                    </button>
                    <button
                      onClick={() => handleAiFix(col, rowIdx, 'format')}
                      className="btn btn-primary btn-sm flex-1 text-xs py-1.5 flex items-center justify-center gap-1 font-medium"
                    >
                      <Wand2 className="w-3 h-3" />
                      <span>AI Fix</span>
                    </button>
                    <button
                      onClick={() => handleIgnore(col, rowIdx, 'format')}
                      className="btn btn-secondary btn-sm text-xs py-1.5 px-2.5 text-gray-500 hover:text-gray-800"
                    >
                      <EyeOff className="w-3 h-3" />
                      <span>Ignore</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {formatIssues.length > formatDisplayLimit && (
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-200 text-xs text-gray-600 mt-2">
              <span>
                Showing <strong>{formatDisplayLimit}</strong> of <strong>{formatIssues.length}</strong> format irregularities
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setFormatDisplayLimit(prev => Math.min(prev + 50, formatIssues.length))}
                  className="btn btn-secondary btn-sm text-xs py-1 px-3"
                >
                  Show More (+50)
                </button>
                <button
                  onClick={() => setFormatDisplayLimit(formatIssues.length)}
                  className="btn btn-secondary btn-sm text-xs py-1 px-3"
                >
                  Show All ({formatIssues.length})
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Multi-Agent Audit Summary Tables */}
      <div className="pt-4">
        <div className="flex items-center gap-2 mb-3">
          <Info className="w-4 h-4 text-gray-400" />
          <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Multi-Agent Quality Audit Logs</h4>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <MissingTable data={missingData.length > 0 ? missingData : [{ column: 'None', missing_count: 0, percentage: 0 }]} />
          <FormatTable data={formatData.length > 0 ? formatData : [{ column: 'None', expected_format: 'Verified', invalid_count: 0 }]} />
          <AnomalyTable
            data={anomalyData}
            rawAnomalies={analysis?.anomalies || []}
            rawRecords={rawRecords && rawRecords.length > 0 ? rawRecords : (originalRecords || [])}
            filename={filename || analysis?.filename || 'dataset.csv'}
            statsSummary={analysis?.stats_summary || {}}
          />
        </div>
      </div>

      {/* Manual Fix Input Modal */}
      {manualModal.isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 border border-gray-200">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100 mb-4">
              <div className="flex items-center gap-2">
                <Edit3 className="w-4 h-4 text-emerald-600" />
                <h3 className="text-sm font-bold text-gray-900">Manual Quality Correction</h3>
              </div>
              <button
                onClick={() => setManualModal({ isOpen: false, column: '', rowIdx: null, oldValue: '', inputValue: '' })}
                className="p-1 text-gray-400 hover:text-gray-700 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 flex justify-between items-center">
                <span className="text-gray-500">Target Feature / Column:</span>
                <span className="font-mono font-bold text-gray-900">{manualModal.column}</span>
              </div>
              {manualModal.rowIdx !== null && (
                <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 flex justify-between items-center">
                  <span className="text-gray-500">Record Number:</span>
                  <span className="font-mono font-bold text-gray-900">Row #{manualModal.rowIdx + 1}</span>
                </div>
              )}
              <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 flex justify-between items-center">
                <span className="text-gray-500">Current Value:</span>
                <span className="font-mono text-red-600 font-semibold">{String(manualModal.oldValue)}</span>
              </div>

              <div className="pt-2">
                <label className="block text-xs font-bold text-gray-700 mb-1">
                  Enter Corrected Value:
                </label>
                <input
                  type="text"
                  value={manualModal.inputValue}
                  onChange={(e) => setManualModal(m => ({ ...m, inputValue: e.target.value }))}
                  placeholder={`e.g. 42 or customer@example.com`}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs font-mono focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleApplyManualModal();
                  }}
                />
                <p className="text-[11px] text-gray-400 mt-1">
                  This value will be applied to the continuous dataset and recorded in the audit trail.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-5 border-t border-gray-100 mt-5">
              <button
                onClick={() => setManualModal({ isOpen: false, column: '', rowIdx: null, oldValue: '', inputValue: '' })}
                className="btn btn-secondary btn-sm text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleApplyManualModal}
                className="btn btn-primary btn-sm text-xs font-semibold px-4"
              >
                Apply Manual Fix
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Workflow Bottom Navigation Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-5 bg-white rounded-xl border border-gray-200 shadow-sm mt-8">
        <button
          onClick={() => navigate('/profiling')}
          className="btn btn-secondary btn-sm flex items-center gap-2 font-semibold px-4 py-2.5 text-xs text-gray-700 hover:bg-gray-100"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back: Data Profiling</span>
        </button>
        <button
          onClick={() => navigate('/anomalies')}
          className="btn btn-primary btn-sm flex items-center gap-2 font-semibold px-5 py-2.5 shadow-sm text-xs"
        >
          <span>Next: Anomaly Detection</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default Issues;
