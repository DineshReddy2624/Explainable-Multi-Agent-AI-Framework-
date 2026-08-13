import React, { useState, useCallback } from 'react';
import { AlertTriangle, X, ChevronRight, TrendingUp, Database, Info, Sparkles, Loader2, Bot } from 'lucide-react';
import api from '../../services/api';

const AnomalyTable = ({ data = [], rawAnomalies = [], rawRecords = [] }) => {
  const [inspecting, setInspecting] = useState(null);
  const [llmExplanation, setLlmExplanation] = useState('');
  const [llmLoading, setLlmLoading] = useState(false);
  const [llmProvider, setLlmProvider] = useState('');

  const enriched = data.map((item, idx) => ({
    ...item,
    raw: rawAnomalies[idx] || null,
  }));

  const handleInspect = useCallback(async (item) => {
    if (!item.raw) return;
    const rowData = rawRecords[item.raw.row_index] || null;
    const anomaly = { ...item.raw, rowData };
    setInspecting(anomaly);
    setLlmExplanation('');
    setLlmProvider('');
    setLlmLoading(true);

    try {
      const res = await api.post('/anomalies/explain', {
        row_index: item.raw.row_index,
        column: item.raw.column,
        value: item.raw.value,
        anomaly_score: item.raw.anomaly_score,
        reason: item.raw.reason || null,
        row_data: rowData || null,
      });
      const d = res.data?.data;
      setLlmExplanation(d?.explanation || '');
      setLlmProvider(d?.provider || '');
    } catch (err) {
      setLlmExplanation(
        `The value '${item.raw.value}' in column '${item.raw.column}' deviates significantly from the expected distribution, ` +
        `flagged with an anomaly score of ${item.raw.anomaly_score}. This likely indicates a data entry error or an extreme edge case that should be reviewed.`
      );
      setLlmProvider('template');
    } finally {
      setLlmLoading(false);
    }
  }, [rawRecords]);

  const handleClose = () => {
    setInspecting(null);
    setLlmExplanation('');
    setLlmLoading(false);
  };

  return (
    <>
      <div className="card p-0 overflow-hidden">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-600" />
            <h3 className="text-sm font-bold text-gray-900">ML Isolation Forest Anomaly Results</h3>
          </div>
          <span className="text-xs text-gray-400 font-medium">{data.length} Outliers</span>
        </div>

        <div className="table-container border-0 rounded-none">
          <table>
            <thead>
              <tr>
                <th>Target Row &amp; Feature</th>
                <th>Anomaly Score / Count</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {enriched.map((item, idx) => (
                <tr key={idx} className="hover:bg-red-50 transition-colors">
                  <td className="font-mono text-xs font-semibold text-gray-900">{item.algorithm}</td>
                  <td>
                    <span className="badge badge-danger font-mono">{item.anomaly_count}</span>
                  </td>
                  <td>
                    <button
                      onClick={() => handleInspect(item)}
                      className="btn btn-secondary btn-sm text-[11px] py-1 px-2 flex items-center gap-1 hover:bg-red-600 hover:text-white hover:border-red-600 transition-all"
                    >
                      <ChevronRight className="w-3 h-3" />
                      Inspect Outlier
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Inspect Outlier Panel */}
      {inspecting && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={handleClose}
          />

          {/* Panel */}
          <div className="relative z-10 w-full max-w-xl mx-4 bg-white rounded-2xl shadow-2xl overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-5 border-b border-red-100 bg-gradient-to-r from-red-50 to-orange-50">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-red-100 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-red-600" />
                </div>
                <div>
                  <p className="text-sm font-bold text-gray-900">Outlier Inspection</p>
                  <p className="text-xs text-red-500 font-mono">
                    Row #{(inspecting.row_index ?? 0) + 1} — {inspecting.column}
                  </p>
                </div>
              </div>
              <button
                onClick={handleClose}
                className="w-8 h-8 rounded-full bg-white shadow-sm flex items-center justify-center hover:bg-red-50 transition"
              >
                <X className="w-4 h-4 text-gray-500" />
              </button>
            </div>

            {/* Score Cards */}
            <div className="p-5 border-b border-gray-100">
              <div className="flex gap-3 mb-4">
                <div className="flex-1 bg-red-50 rounded-xl p-3 text-center border border-red-100">
                  <p className="text-xs text-red-400 font-semibold uppercase tracking-wide mb-1">Outlier Value</p>
                  <p className="text-xl font-bold text-red-700 font-mono">{inspecting.value}</p>
                </div>
                <div className="flex-1 bg-orange-50 rounded-xl p-3 text-center border border-orange-100">
                  <p className="text-xs text-orange-400 font-semibold uppercase tracking-wide mb-1">Anomaly Score</p>
                  <p className="text-xl font-bold text-orange-700 font-mono">
                    {typeof inspecting.anomaly_score === 'number' ? inspecting.anomaly_score.toFixed(2) : inspecting.anomaly_score}
                  </p>
                </div>
                <div className="flex-1 bg-amber-50 rounded-xl p-3 text-center border border-amber-100">
                  <p className="text-xs text-amber-400 font-semibold uppercase tracking-wide mb-1">Severity</p>
                  <p className="text-xl font-bold text-amber-700">
                    {inspecting.anomaly_score >= 0.9 ? 'Critical' : inspecting.anomaly_score >= 0.75 ? 'High' : 'Medium'}
                  </p>
                </div>
              </div>

              {/* LLM Explanation Box */}
              <div className="rounded-xl border overflow-hidden">
                <div className="flex items-center gap-2 px-4 py-2.5 border-b bg-gradient-to-r from-violet-50 to-indigo-50">
                  <Bot className="w-4 h-4 text-violet-600" />
                  <span className="text-xs font-bold text-violet-700 uppercase tracking-wide">AI Analysis</span>
                  {!llmLoading && llmProvider && (
                    <span className={`ml-auto text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      llmProvider === 'gemini' ? 'bg-blue-100 text-blue-700'
                      : llmProvider === 'groq' ? 'bg-green-100 text-green-700'
                      : llmProvider === 'openai' ? 'bg-purple-100 text-purple-700'
                      : 'bg-gray-100 text-gray-500'
                    }`}>
                      {llmProvider === 'gemini' ? '✨ Gemini Flash'
                        : llmProvider === 'groq' ? '⚡ Groq LLaMA 3.3'
                        : llmProvider === 'openai' ? '🧠 GPT-4o'
                        : '📋 Template'}
                    </span>
                  )}
                </div>
                <div className="px-4 py-3 bg-white min-h-[80px] flex items-start gap-3">
                  {llmLoading ? (
                    <div className="flex items-center gap-3 py-2 w-full">
                      <Loader2 className="w-4 h-4 text-violet-500 animate-spin flex-shrink-0" />
                      <div className="flex-1 space-y-2">
                        <div className="h-3 bg-violet-100 rounded animate-pulse w-full" />
                        <div className="h-3 bg-violet-50 rounded animate-pulse w-4/5" />
                        <div className="h-3 bg-violet-50 rounded animate-pulse w-3/5" />
                      </div>
                    </div>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 text-violet-500 mt-0.5 flex-shrink-0" />
                      <p className="text-sm text-gray-700 leading-relaxed">{llmExplanation}</p>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Full Row Data */}
            {inspecting.rowData && (
              <div className="p-5 max-h-64 overflow-y-auto">
                <div className="flex items-center gap-2 mb-3">
                  <Database className="w-4 h-4 text-gray-400" />
                  <p className="text-xs font-bold text-gray-700 uppercase tracking-wide">Full Row Context</p>
                </div>
                <div className="rounded-xl border border-gray-200 overflow-hidden">
                  <table className="w-full text-xs">
                    <tbody>
                      {Object.entries(inspecting.rowData).map(([key, val], i) => (
                        <tr
                          key={key}
                          className={`border-b border-gray-100 last:border-0 ${key === inspecting.column ? 'bg-red-50' : i % 2 === 0 ? 'bg-gray-50' : 'bg-white'}`}
                        >
                          <td className="py-2 px-3 font-semibold text-gray-500 w-1/3 font-mono">{key}</td>
                          <td className={`py-2 px-3 font-mono ${key === inspecting.column ? 'text-red-700 font-bold' : 'text-gray-800'}`}>
                            {val === null || val === undefined || String(val).trim() === '' ? (
                              <span className="text-gray-300 italic">null</span>
                            ) : String(val)}
                          </td>
                          {key === inspecting.column && (
                            <td className="py-2 px-3">
                              <span className="inline-flex items-center gap-1 text-[10px] font-bold text-red-600 bg-red-50 border border-red-200 rounded-full px-2 py-0.5">
                                ⚠ Outlier
                              </span>
                            </td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <div className="p-5 pt-0">
              <button
                onClick={handleClose}
                className="w-full btn btn-primary btn-sm py-2 font-semibold"
              >
                Close Inspection
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default AnomalyTable;
