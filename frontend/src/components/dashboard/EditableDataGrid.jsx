import React, { useState } from 'react';
import { Edit3, CheckCircle2, AlertTriangle, AlertCircle, Wand2, HelpCircle } from 'lucide-react';

const EditableDataGrid = ({ records = [], headers = [], missingReport = [], formatIssues = [], anomalies = [], onCellEdit, onStrategySelect }) => {
  const [editingCell, setEditingCell] = useState(null); // { row: 0, col: "Age" }
  const [tempVal, setTempVal] = useState("");
  const [selectedStrategies, setSelectedStrategies] = useState({});

  if (!records || records.length === 0) return null;

  // Build lookup maps for fast cell styling & issue detection
  const missingMap = new Set();
  missingReport.forEach(item => {
    (item.null_rows || []).forEach(r => missingMap.add(`${r}-${item.column}`));
  });

  const formatMap = new Map();
  formatIssues.forEach(item => {
    formatMap.set(`${item.row_index}-${item.column}`, item);
  });

  const anomalyMap = new Map();
  anomalies.forEach(item => {
    anomalyMap.set(`${item.row_index}-${item.column}`, item);
  });

  const handleCellClick = (rIdx, cName, currentVal) => {
    setEditingCell({ row: rIdx, col: cName });
    setTempVal(currentVal !== undefined && currentVal !== null ? String(currentVal) : "");
  };

  const handleCellBlur = (rIdx, cName) => {
    onCellEdit(rIdx, cName, tempVal);
    setEditingCell(null);
  };

  const handleStrategyChange = (col, strat) => {
    setSelectedStrategies(prev => ({ ...prev, [col]: strat }));
    onStrategySelect(col, strat);
  };

  return (
    <div className="card bg-white border border-slate-200 shadow-sm rounded-2xl p-6 space-y-4">
      {/* Title & Legend Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <Edit3 className="w-5 h-5 text-indigo-600" />
            <h3 className="text-base font-extrabold text-slate-900 tracking-tight">
              Interactive Editable Dataset Grid & User Control Panel
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Click any cell to edit manually, or select column-level AI remediation strategies directly in column headers below.
          </p>
        </div>

        {/* Legend Pills */}
        <div className="flex items-center gap-3 text-[11px] font-semibold flex-wrap">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
            <span className="w-2 h-2 rounded-full bg-amber-500"></span> Missing Value
          </span>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-cyan-50 text-cyan-800 border border-cyan-200">
            <span className="w-2 h-2 rounded-full bg-cyan-500"></span> Format Error
          </span>
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-50 text-red-800 border border-red-200">
            <span className="w-2 h-2 rounded-full bg-red-500"></span> ML Anomaly (Isolation Forest)
          </span>
        </div>
      </div>

      {/* Integrated Sticky Header Table */}
      <div className="chat-data-table-container max-h-[32rem]">
        <table className="chat-data-table">
          <thead>
            <tr>
              <th className="w-12 text-center">#</th>
              {headers.map(h => {
                const missInfo = missingReport.find(m => m.column === h);
                return (
                  <th key={h} className="min-w-[160px]">
                    <div className="flex flex-col gap-1">
                      <span className="font-bold text-white tracking-wider uppercase text-[11px]">{h}</span>
                      <select
                        value={selectedStrategies[h] || "KEEP_ORIGINAL"}
                        onChange={e => handleStrategyChange(h, e.target.value)}
                        className="w-full text-[10px] font-semibold bg-slate-800 text-slate-200 border border-slate-700 rounded-lg px-2 py-1 focus:outline-none focus:border-indigo-400 cursor-pointer shadow-xs"
                      >
                        <option value="KEEP_ORIGINAL" className="bg-slate-900 text-slate-200">Keep Original</option>
                        {missInfo && missInfo.suggested_median !== null && (
                          <option value="FILL_MEDIAN" className="bg-slate-900 text-slate-200">Fill Median ({missInfo.suggested_median})</option>
                        )}
                        {missInfo && missInfo.suggested_mean !== null && (
                          <option value="FILL_MEAN" className="bg-slate-900 text-slate-200">Fill Mean ({missInfo.suggested_mean})</option>
                        )}
                        {missInfo && missInfo.suggested_mode !== null && (
                          <option value="FILL_MODE" className="bg-slate-900 text-slate-200">Fill Mode ({missInfo.suggested_mode})</option>
                        )}
                        <option value="DROP_COLUMN" className="bg-slate-900 text-slate-200">Drop Column</option>
                        <option value="DROP_DUPLICATES" className="bg-slate-900 text-slate-200">Drop Duplicates</option>
                      </select>
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {records.map((row, rIdx) => (
              <tr key={rIdx}>
                <td className="text-center font-mono text-[11px] text-slate-400 font-semibold">{rIdx + 1}</td>
                {headers.map(cName => {
                  const key = `${rIdx}-${cName}`;
                  const isMissing = missingMap.has(key) || row[cName] === undefined || row[cName] === null || String(row[cName]).trim() === '';
                  const formatErr = formatMap.get(key);
                  const anomalyErr = anomalyMap.get(key);
                  const isEditing = editingCell?.row === rIdx && editingCell?.col === cName;

                  let cellBgClass = "hover:bg-slate-50";
                  let tooltip = "Click to edit value";

                  if (anomalyErr) {
                    cellBgClass = "bg-red-50 border border-red-300 text-red-900 font-semibold";
                    tooltip = `🚨 Isolation Forest Anomaly (Score: ${anomalyErr.anomaly_score}) - ${anomalyErr.reason}`;
                  } else if (formatErr) {
                    cellBgClass = "bg-cyan-50 border border-cyan-300 text-cyan-900 font-semibold";
                    tooltip = `🔧 Wrong Format: Value '${formatErr.invalid_value}' does not match expected format. AI Suggestion: '${formatErr.suggested_correction}'`;
                  } else if (isMissing) {
                    cellBgClass = "bg-amber-50 border border-amber-300 text-amber-900 font-semibold";
                    tooltip = `❓ Missing Value (Null/Empty)`;
                  }

                  return (
                    <td
                      key={cName}
                      className={`cursor-pointer transition-colors px-3 py-2 text-xs font-mono ${cellBgClass}`}
                      title={tooltip}
                      onClick={() => handleCellClick(rIdx, cName, row[cName])}
                    >
                      {isEditing ? (
                        <input
                          autoFocus
                          type="text"
                          value={tempVal}
                          onChange={e => setTempVal(e.target.value)}
                          onBlur={() => handleCellBlur(rIdx, cName)}
                          onKeyDown={e => { if (e.key === 'Enter') handleCellBlur(rIdx, cName); }}
                          className="w-full px-2 py-1 bg-white border border-indigo-500 rounded text-xs font-mono text-slate-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                        />
                      ) : (
                        <span>
                          {row[cName] !== undefined && row[cName] !== null && String(row[cName]).trim() !== '' ? (
                            String(row[cName])
                          ) : (
                            <span className="text-amber-700 font-bold italic">[NULL]</span>
                          )}
                        </span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default EditableDataGrid;
