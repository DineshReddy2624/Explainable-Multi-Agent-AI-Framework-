import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  X,
  ChevronRight,
  ChevronLeft,
  Database,
  Info,
  Sparkles,
  Loader2,
  Bot,
  BrainCircuit,
  CheckCircle2,
  ArrowLeft,
  ExternalLink,
  Sliders,
  BarChart3,
  TrendingUp,
  TrendingDown
} from 'lucide-react';
import api from '../../services/api';

const AnomalyTable = ({
  data = [],
  rawAnomalies = [],
  rawRecords = [],
  filename = 'dataset.csv',
  statsSummary = {}
}) => {
  const navigate = useNavigate();
  const [inspectIndex, setInspectIndex] = useState(null);
  const [llmExplanation, setLlmExplanation] = useState('');
  const [llmLoading, setLlmLoading] = useState(false);
  const [llmProvider, setLlmProvider] = useState('');

  // Prepare normalized list of anomalies from rawAnomalies or fallback data
  const anomaliesList = React.useMemo(() => {
    if (rawAnomalies && rawAnomalies.length > 0) {
      return rawAnomalies.map((item, idx) => {
        const rawScore = item.anomaly_score ?? item.confidence_score ?? 0.85;
        const normalizedScore = typeof rawScore === 'number'
          ? (rawScore > 1 ? rawScore / 100 : rawScore)
          : parseFloat(rawScore) || 0.85;

        return {
          row_index: item.row_index ?? idx,
          record_id: item.record_id || `Record #${(item.row_index ?? idx) + 1}`,
          column: item.column || item.primary_feature || 'Feature',
          value: item.value ?? item.feature_value ?? 'N/A',
          anomaly_score: normalizedScore,
          confidence_score: item.confidence_score ?? Math.round(normalizedScore * 100),
          threshold: item.threshold ?? 0.65,
          reason: item.reason || item.explanation || 'Flagged as an isolated outlier differing significantly from normal dataset distributions.',
          flagged_algorithms: item.flagged_algorithms || ['Isolation Forest'],
          suggested_value: item.suggested_value,
        };
      });
    }

    if (data && data.length > 0) {
      return data
        .filter(d => d.anomaly_count !== 0 && d.algorithm !== 'Isolation Forest Scan')
        .map((item, idx) => {
          const rawScore = item.anomaly_count ?? 0.85;
          const normalizedScore = typeof rawScore === 'number'
            ? (rawScore > 1 ? rawScore / 100 : rawScore)
            : parseFloat(rawScore) || 0.85;

          return {
            row_index: idx,
            record_id: `Record #${idx + 1}`,
            column: item.algorithm ? item.algorithm.replace(/^Row\s*#\d+\s*\((.+)\)$/, '$1') : 'Feature',
            value: 'Flagged Value',
            anomaly_score: normalizedScore,
            confidence_score: Math.round(normalizedScore * 100),
            threshold: 0.65,
            reason: 'Flagged by Isolation Forest model.',
            flagged_algorithms: ['Isolation Forest'],
          };
        });
    }

    return [];
  }, [rawAnomalies, data]);

  const activeAnomaly = inspectIndex !== null ? anomaliesList[inspectIndex] : null;
  const activeRecord = activeAnomaly && rawRecords && activeAnomaly.row_index !== undefined
    ? rawRecords[activeAnomaly.row_index] || null
    : null;
  const activeStats = activeAnomaly && statsSummary ? statsSummary[activeAnomaly.column] || null : null;

  // Fetch or generate rich explanation when active anomaly changes
  useEffect(() => {
    if (!activeAnomaly) {
      setLlmExplanation('');
      setLlmLoading(false);
      setLlmProvider('');
      return;
    }

    let isMounted = true;
    setLlmLoading(true);

    const fetchExplanation = async () => {
      try {
        const payload = {
          row_index: activeAnomaly.row_index,
          column: activeAnomaly.column,
          value: activeAnomaly.value,
          anomaly_score: activeAnomaly.anomaly_score,
          reason: activeAnomaly.reason,
          row_data: activeRecord || {}
        };

        const res = await api.post('/anomalies/explain', payload);
        if (isMounted && res.data?.data) {
          setLlmExplanation(res.data.data.explanation || activeAnomaly.reason);
          setLlmProvider(res.data.data.provider || 'ai-engine');
          setLlmLoading(false);
          return;
        }
      } catch (err) {
        // Fallback explanation based on statistical observation
      }

      if (isMounted) {
        const scorePct = Math.round(activeAnomaly.anomaly_score * 100);
        let fallback = `The value '${activeAnomaly.value}' in column '${activeAnomaly.column}' (Row #${activeAnomaly.row_index + 1}) was flagged with an anomaly confidence of ${scorePct}%. `;
        if (activeStats?.median !== undefined) {
          fallback += `It deviates significantly from the typical column median (${activeStats.median}) and expected normal range. `;
        }
        fallback += `Isolation Forest identified this record as an isolated multi-dimensional outlier that may require data cleaning or investigation.`;

        setLlmExplanation(fallback);
        setLlmProvider('template');
        setLlmLoading(false);
      }
    };

    fetchExplanation();

    return () => {
      isMounted = false;
    };
  }, [activeAnomaly, activeRecord, activeStats]);

  // Keyboard navigation for inspector
  useEffect(() => {
    if (inspectIndex === null) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setInspectIndex(null);
      } else if (e.key === 'ArrowLeft' && inspectIndex > 0) {
        setInspectIndex(prev => prev - 1);
      } else if (e.key === 'ArrowRight' && inspectIndex < anomaliesList.length - 1) {
        setInspectIndex(prev => prev + 1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [inspectIndex, anomaliesList.length]);

  const handleOpenInspect = (idx) => {
    setInspectIndex(idx);
  };

  const handleClose = () => {
    setInspectIndex(null);
    setLlmExplanation('');
    setLlmLoading(false);
  };

  const handlePrevious = () => {
    if (inspectIndex > 0) {
      setInspectIndex(prev => prev - 1);
    }
  };

  const handleNext = () => {
    if (inspectIndex < anomaliesList.length - 1) {
      setInspectIndex(prev => prev + 1);
    }
  };

  // Optional: Explicit user choice to explore in Explainable AI
  const handleNavigateToExplainableAI = () => {
    if (!activeAnomaly) return;
    navigate('/explainable-ai', {
      state: {
        row_index: activeAnomaly.row_index,
        column: activeAnomaly.column,
        value: activeAnomaly.value
      }
    });
  };

  // Helper for deviation text
  const getDeviationInfo = () => {
    if (!activeStats || !activeAnomaly || typeof activeAnomaly.value !== 'number') return null;
    const med = activeStats.median;
    const val = activeAnomaly.value;
    if (med === undefined || med === null) return null;

    const diff = val - med;
    const isAbove = diff > 0;
    const pct = med !== 0 ? Math.round((Math.abs(diff) / Math.abs(med)) * 100) : 0;

    return {
      isAbove,
      diff,
      pct,
      label: isAbove
        ? `Significantly above normal range (+${pct}% vs median)`
        : `Significantly below normal range (-${pct}% vs median)`
    };
  };

  const deviationInfo = getDeviationInfo();

  return (
    <>
      <div className="card p-0 overflow-hidden border border-gray-200 shadow-sm">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gray-50/50">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-600" />
            <h3 className="text-sm font-bold text-gray-900">ML Isolation Forest Anomaly Results</h3>
          </div>
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
            anomaliesList.length > 0 ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'
          }`}>
            {anomaliesList.length} {anomaliesList.length === 1 ? 'Outlier' : 'Outliers'}
          </span>
        </div>

        <div className="table-container border-0 rounded-none">
          <table>
            <thead>
              <tr>
                <th>Target Row &amp; Feature</th>
                <th>Anomaly Score</th>
                <th>Detection Method</th>
                <th>Status / Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {anomaliesList.length === 0 ? (
                <tr>
                  <td colSpan="4" className="py-8 text-center text-gray-500">
                    <div className="flex flex-col items-center justify-center gap-1.5">
                      <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                      <span className="text-xs font-bold text-gray-800">No ML Outliers Detected</span>
                      <span className="text-[11px] text-gray-400">
                        All records conform to normal multi-dimensional Isolation Forest bounds.
                      </span>
                    </div>
                  </td>
                </tr>
              ) : (
                anomaliesList.map((item, idx) => (
                  <tr key={idx} className="hover:bg-red-50/40 transition-colors">
                    <td className="font-mono text-xs font-semibold text-gray-900">
                      Row #{item.row_index + 1}{' '}
                      <span className="text-gray-500 font-normal">({item.column})</span>
                    </td>
                    <td>
                      <span className="badge badge-danger font-mono font-bold text-[11px]">
                        {typeof item.anomaly_score === 'number' ? item.anomaly_score.toFixed(2) : item.anomaly_score}
                      </span>
                    </td>
                    <td className="text-xs text-gray-600">
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-gray-700">
                        {item.flagged_algorithms?.join(', ') || 'Isolation Forest'}
                      </span>
                    </td>
                    <td>
                      <button
                        onClick={() => handleOpenInspect(idx)}
                        className="btn btn-secondary btn-sm text-[11px] py-1 px-2.5 flex items-center gap-1.5 hover:bg-red-600 hover:text-white hover:border-red-600 transition-all shadow-xs"
                      >
                        <ChevronRight className="w-3 h-3" />
                        <span>Inspect Outlier</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Outlier Inspection Modal */}
      {activeAnomaly && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-xs animate-fade-in overflow-y-auto">
          {/* Modal Card */}
          <div className="relative z-10 w-full max-w-4xl bg-white rounded-2xl shadow-2xl overflow-hidden my-auto max-h-[92vh] flex flex-col border border-gray-200">
            {/* 1. Header */}
            <div className="flex items-center justify-between p-4 sm:p-5 border-b border-red-100 bg-gradient-to-r from-red-50 via-orange-50 to-amber-50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-red-600 text-white flex items-center justify-center shadow-sm">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-gray-900">Outlier Inspection</h3>
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold text-red-700 bg-red-100 border border-red-200 rounded-full px-2.5 py-0.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-600 animate-pulse" />
                      🔴 Anomaly Detected
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Dataset: <strong className="text-gray-800">{filename}</strong> • Detection Method:{' '}
                    <strong className="text-gray-800">
                      {activeAnomaly.flagged_algorithms?.join(', ') || 'Isolation Forest'}
                    </strong>
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {/* Outlier Pagination Controls */}
                {anomaliesList.length > 1 && (
                  <div className="flex items-center gap-1 bg-white/80 border border-gray-200 rounded-lg p-1 text-xs">
                    <button
                      onClick={handlePrevious}
                      disabled={inspectIndex === 0}
                      className="p-1 rounded hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition"
                      title="Previous Outlier (Left Arrow)"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </button>
                    <span className="px-2 font-mono font-semibold text-gray-700 text-[11px]">
                      {inspectIndex + 1} of {anomaliesList.length}
                    </span>
                    <button
                      onClick={handleNext}
                      disabled={inspectIndex === anomaliesList.length - 1}
                      className="p-1 rounded hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition"
                      title="Next Outlier (Right Arrow)"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                )}

                <button
                  onClick={handleClose}
                  className="w-8 h-8 rounded-lg bg-white border border-gray-200 flex items-center justify-center text-gray-500 hover:text-gray-900 hover:bg-gray-50 transition"
                  title="Close and return to Quality Issues"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Scrollable Content */}
            <div className="p-5 overflow-y-auto space-y-5 text-xs">
              {/* 2. Record Identification & Stat Badges */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 bg-gray-50 rounded-xl border border-gray-200">
                  <p className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider">Record Identifier</p>
                  <h4 className="text-base font-bold text-gray-900 font-mono mt-0.5">
                    Row #{activeAnomaly.row_index + 1}
                  </h4>
                  <p className="text-[10px] text-gray-400 font-mono mt-0.5">
                    {activeAnomaly.record_id || `Index #${activeAnomaly.row_index}`}
                  </p>
                </div>

                <div className="p-3 bg-red-50/70 rounded-xl border border-red-200">
                  <p className="text-[11px] font-semibold text-red-600 uppercase tracking-wider">Anomalous Feature</p>
                  <h4 className="text-base font-bold text-red-900 font-mono mt-0.5 truncate" title={activeAnomaly.column}>
                    {activeAnomaly.column}
                  </h4>
                  <p className="text-[10px] text-red-500 font-bold mt-0.5 truncate" title={String(activeAnomaly.value)}>
                    Value: {String(activeAnomaly.value)}
                  </p>
                </div>

                <div className="p-3 bg-orange-50/70 rounded-xl border border-orange-200">
                  <p className="text-[11px] font-semibold text-orange-600 uppercase tracking-wider">Anomaly Score</p>
                  <h4 className="text-base font-bold text-orange-900 font-mono mt-0.5">
                    {typeof activeAnomaly.anomaly_score === 'number'
                      ? activeAnomaly.anomaly_score.toFixed(2)
                      : activeAnomaly.anomaly_score}
                  </h4>
                  <p className="text-[10px] text-orange-600 font-medium mt-0.5">
                    Threshold: {typeof activeAnomaly.threshold === 'number' ? activeAnomaly.threshold.toFixed(2) : '0.65'}
                  </p>
                </div>

                <div className="p-3 bg-amber-50/70 rounded-xl border border-amber-200">
                  <p className="text-[11px] font-semibold text-amber-700 uppercase tracking-wider">Detection Status</p>
                  <h4 className="text-base font-bold text-amber-900 mt-0.5">Outlier</h4>
                  <p className="text-[10px] text-amber-700 font-medium mt-0.5">
                    {activeAnomaly.anomaly_score >= 0.85 ? 'Critical Deviation' : 'Confirmed Anomaly'}
                  </p>
                </div>
              </div>

              {/* 3. Comparison with Normal Data */}
              <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-xs">
                <div className="flex items-center justify-between border-b border-gray-100 pb-2.5 mb-3">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-blue-600" />
                    <h4 className="text-xs font-bold text-gray-900 uppercase tracking-wider">
                      Comparison with Normal Dataset Distribution
                    </h4>
                  </div>
                  {deviationInfo && (
                    <span className="text-[11px] font-semibold text-red-600 flex items-center gap-1">
                      {deviationInfo.isAbove ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                      {deviationInfo.label}
                    </span>
                  )}
                </div>

                {activeStats ? (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-2.5 bg-red-50/60 rounded-lg border border-red-100">
                      <span className="text-[10px] text-red-500 font-bold uppercase tracking-wider block">
                        Actual Value
                      </span>
                      <span className="text-sm font-bold text-red-700 font-mono block mt-0.5">
                        {String(activeAnomaly.value)}
                      </span>
                      <span className="text-[10px] text-red-400">Flagged outlier</span>
                    </div>

                    <div className="p-2.5 bg-gray-50 rounded-lg border border-gray-100">
                      <span className="text-[10px] text-gray-500 font-semibold uppercase tracking-wider block">
                        Dataset Median
                      </span>
                      <span className="text-sm font-bold text-gray-800 font-mono block mt-0.5">
                        {activeStats.median !== undefined ? activeStats.median : 'N/A'}
                      </span>
                      <span className="text-[10px] text-gray-400">Robust 50th percentile</span>
                    </div>

                    <div className="p-2.5 bg-gray-50 rounded-lg border border-gray-100">
                      <span className="text-[10px] text-gray-500 font-semibold uppercase tracking-wider block">
                        Dataset Mean
                      </span>
                      <span className="text-sm font-bold text-gray-800 font-mono block mt-0.5">
                        {activeStats.mean !== undefined ? activeStats.mean : 'N/A'}
                      </span>
                      <span className="text-[10px] text-gray-400">Arithmetic average</span>
                    </div>

                    <div className="p-2.5 bg-gray-50 rounded-lg border border-gray-100">
                      <span className="text-[10px] text-gray-500 font-semibold uppercase tracking-wider block">
                        Normal Range
                      </span>
                      <span className="text-sm font-bold text-gray-800 font-mono block mt-0.5">
                        {activeStats.min !== undefined && activeStats.max !== undefined
                          ? `${activeStats.min} – ${activeStats.max}`
                          : 'Standard Range'}
                      </span>
                      <span className="text-[10px] text-gray-400">Dataset min – max bounds</span>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-gray-500 italic">
                    Statistical baseline metrics (mean, median, range) are not available for this non-numeric column.
                  </p>
                )}
              </div>

              {/* 4. Why Was This Record Flagged? (Separated Diagnostic Tiers) */}
              <div className="space-y-2.5">
                <div className="flex items-center gap-2">
                  <BrainCircuit className="w-4 h-4 text-violet-600" />
                  <h4 className="text-xs font-bold text-gray-900 uppercase tracking-wider">
                    Why Was This Record Flagged?
                  </h4>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {/* Tier 1: Model Detection */}
                  <div className="p-3.5 bg-gray-50 rounded-xl border border-gray-200 flex flex-col justify-between">
                    <div>
                      <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider block mb-1">
                        1. ML Model Detection
                      </span>
                      <p className="text-xs font-bold text-gray-800 mb-1">
                        {activeAnomaly.flagged_algorithms?.join(', ') || 'Isolation Forest'}
                      </p>
                      <p className="text-[11px] text-gray-600 leading-relaxed">
                        Isolated in high-dimensional feature partitioning tree with anomaly score of{' '}
                        <strong>
                          {typeof activeAnomaly.anomaly_score === 'number'
                            ? activeAnomaly.anomaly_score.toFixed(2)
                            : activeAnomaly.anomaly_score}
                        </strong>{' '}
                        (threshold: {activeAnomaly.threshold || 0.65}).
                      </p>
                    </div>
                  </div>

                  {/* Tier 2: Statistical Observation */}
                  <div className="p-3.5 bg-blue-50/50 rounded-xl border border-blue-200 flex flex-col justify-between">
                    <div>
                      <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider block mb-1">
                        2. Statistical Observation
                      </span>
                      <p className="text-xs font-bold text-blue-900 mb-1">Distribution Divergence</p>
                      <p className="text-[11px] text-blue-950 leading-relaxed">
                        {activeAnomaly.reason ||
                          `Feature '${activeAnomaly.column}' exhibits anomalous values that deviate significantly from dataset statistical expectations.`}
                      </p>
                    </div>
                  </div>

                  {/* Tier 3: AI Explanation */}
                  <div className="p-3.5 bg-violet-50/50 rounded-xl border border-violet-200 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] font-bold text-violet-600 uppercase tracking-wider">
                          3. AI Rationale
                        </span>
                        {!llmLoading && llmProvider && (
                          <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-violet-100 text-violet-700">
                            {llmProvider === 'gemini'
                              ? '✨ Gemini'
                              : llmProvider === 'groq'
                              ? '⚡ Groq'
                              : '🤖 AI Engine'}
                          </span>
                        )}
                      </div>
                      {llmLoading ? (
                        <div className="flex items-center gap-2 py-3 text-violet-600">
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span className="text-[11px] text-violet-700">Generating AI interpretation...</span>
                        </div>
                      ) : (
                        <p className="text-[11px] text-violet-950 leading-relaxed">
                          {llmExplanation}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* 5. Full Record Context (Strictly READ-ONLY) */}
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-xs">
                <div className="p-3.5 border-b border-gray-200 bg-gray-50/70 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-gray-500" />
                    <h4 className="text-xs font-bold text-gray-900 uppercase tracking-wider">
                      Full Record Context (Read-Only)
                    </h4>
                  </div>
                  <span className="text-[10px] text-gray-500 font-medium">
                    Row #{activeAnomaly.row_index + 1} • Immutable Inspection Mode
                  </span>
                </div>

                {!activeRecord ? (
                  <div className="p-6 text-center text-amber-700 bg-amber-50">
                    <AlertTriangle className="w-5 h-5 mx-auto mb-1 text-amber-600" />
                    <p className="font-semibold text-xs">
                      Unable to locate the original record for this anomaly in the active dataset.
                    </p>
                    <p className="text-[11px] text-gray-500 mt-0.5">
                      Row #{activeAnomaly.row_index + 1} could not be resolved from loaded records.
                    </p>
                  </div>
                ) : (
                  <div className="max-h-56 overflow-y-auto">
                    <table className="w-full text-xs">
                      <thead className="bg-gray-100 border-b border-gray-200 text-gray-600 sticky top-0">
                        <tr>
                          <th className="py-2 px-3 text-left font-semibold">Column / Feature</th>
                          <th className="py-2 px-3 text-left font-semibold">Value</th>
                          <th className="py-2 px-3 text-left font-semibold">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {Object.entries(activeRecord).map(([key, val]) => {
                          const isAnomalous = key === activeAnomaly.column;
                          return (
                            <tr
                              key={key}
                              className={`transition-colors ${
                                isAnomalous ? 'bg-red-50/90 font-semibold' : 'hover:bg-gray-50/50'
                              }`}
                            >
                              <td className="py-2 px-3 font-mono text-gray-700 w-1/3">
                                {key}
                              </td>
                              <td className={`py-2 px-3 font-mono ${isAnomalous ? 'text-red-700 font-bold' : 'text-gray-900'}`}>
                                {val === null || val === undefined || String(val).trim() === '' ? (
                                  <span className="text-gray-300 italic">null</span>
                                ) : (
                                  String(val)
                                )}
                              </td>
                              <td className="py-2 px-3">
                                {isAnomalous ? (
                                  <span className="inline-flex items-center gap-1 text-[10px] font-bold text-red-700 bg-red-100 border border-red-200 rounded-full px-2 py-0.5">
                                    ⚠ Anomalous Feature
                                  </span>
                                ) : (
                                  <span className="text-[10px] text-gray-400">Normal</span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>

            {/* Footer Navigation & Controls */}
            <div className="p-4 border-t border-gray-200 bg-gray-50 flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                {anomaliesList.length > 1 && (
                  <div className="flex items-center gap-1 text-xs">
                    <button
                      onClick={handlePrevious}
                      disabled={inspectIndex === 0}
                      className="btn btn-secondary btn-sm py-1.5 px-3 text-xs flex items-center gap-1 disabled:opacity-40"
                    >
                      <ChevronLeft className="w-3.5 h-3.5" />
                      <span>Previous Outlier</span>
                    </button>
                    <button
                      onClick={handleNext}
                      disabled={inspectIndex === anomaliesList.length - 1}
                      className="btn btn-secondary btn-sm py-1.5 px-3 text-xs flex items-center gap-1 disabled:opacity-40"
                    >
                      <span>Next Outlier</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                {/* Optional secondary exploration button */}
                <button
                  onClick={handleNavigateToExplainableAI}
                  className="btn btn-secondary btn-sm py-1.5 px-3 text-xs text-violet-700 hover:text-violet-900 hover:bg-violet-50 flex items-center gap-1.5"
                  title="Explore deep root-cause in Explainable AI page"
                >
                  <BrainCircuit className="w-3.5 h-3.5 text-violet-600" />
                  <span>Explainable AI</span>
                  <ExternalLink className="w-3 h-3 text-violet-400" />
                </button>

                {/* Primary Return Button */}
                <button
                  onClick={handleClose}
                  className="btn btn-primary btn-sm py-1.5 px-4 text-xs font-semibold flex items-center gap-1.5 shadow-sm"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Back to Quality Issues</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default AnomalyTable;
