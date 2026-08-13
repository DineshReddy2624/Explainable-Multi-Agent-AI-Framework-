import React, { useMemo, useState } from 'react';
import { Wand2, AlertTriangle, ChevronRight, Info, CheckCircle2 } from 'lucide-react';

const FormatTable = ({ data = [] }) => {
  const [selectedIssue, setSelectedIssue] = useState(null);

  // Group raw format issues by column and issue type
  const aggregated = useMemo(() => {
    if (!data || data.length === 0) return [];

    const groups = {};
    data.forEach(item => {
      if (!item) return;
      const col = item.column || 'Unknown';
      const fmt = item.expected_format || item.expected_pattern || 'Format Inconsistency';
      const key = `${col}__${fmt}`;

      if (!groups[key]) {
        groups[key] = {
          column: col,
          expected_format: fmt,
          invalid_count: 0,
          samples: new Set(),
          suggested_correction: item.suggested_correction || null,
          rows: []
        };
      }

      if (item.invalid_count) {
        groups[key].invalid_count += item.invalid_count;
      } else {
        groups[key].invalid_count += 1;
      }

      if (item.invalid_value !== undefined && item.invalid_value !== null && String(item.invalid_value).trim() !== '') {
        groups[key].samples.add(String(item.invalid_value));
      }

      if (item.row_index !== undefined) {
        groups[key].rows.push(item.row_index + 1);
      }
    });

    return Object.values(groups).map(g => ({
      ...g,
      sampleList: Array.from(g.samples).slice(0, 4).join(', ')
    }));
  }, [data]);

  const totalRawIssues = data.reduce((acc, curr) => acc + (curr.invalid_count || 1), 0);

  return (
    <>
      <div className="card p-0 overflow-hidden shadow-xs border border-gray-200">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-cyan-50/50 to-blue-50/30">
          <div className="flex items-center gap-2">
            <Wand2 className="w-4 h-4 text-cyan-600" />
            <h3 className="text-sm font-bold text-gray-900">Format Inconsistencies Audit</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-cyan-100 text-cyan-800 border border-cyan-200">
              {aggregated.length} Issue {aggregated.length === 1 ? 'Type' : 'Types'}
            </span>
            <span className="text-xs text-gray-400 font-medium">({totalRawIssues} Pattern Instances)</span>
          </div>
        </div>

        <div className="table-container border-0 rounded-none overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-gray-50/80 border-b border-gray-200">
                <th className="py-2.5 px-3 text-left font-bold text-gray-700 uppercase tracking-wider text-[11px]">Column</th>
                <th className="py-2.5 px-3 text-left font-bold text-gray-700 uppercase tracking-wider text-[11px]">Expected Pattern</th>
                <th className="py-2.5 px-3 text-center font-bold text-gray-700 uppercase tracking-wider text-[11px]">Affected Cells</th>
                <th className="py-2.5 px-3 text-left font-bold text-gray-700 uppercase tracking-wider text-[11px]">Sample Invalid Values</th>
                <th className="py-2.5 px-3 text-center font-bold text-gray-700 uppercase tracking-wider text-[11px]">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {aggregated.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-gray-400 font-medium text-xs">
                    <CheckCircle2 className="w-5 h-5 text-emerald-500 mx-auto mb-1" />
                    No format inconsistencies detected across all columns.
                  </td>
                </tr>
              ) : (
                aggregated.map((item, idx) => (
                  <tr key={idx} className="hover:bg-cyan-50/40 transition-colors">
                    <td className="py-2.5 px-3 font-mono font-bold text-gray-900">{item.column}</td>
                    <td className="py-2.5 px-3">
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-cyan-50 text-cyan-800 border border-cyan-200">
                        {item.expected_format}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-red-50 text-red-700 border border-red-200 font-mono">
                        {item.invalid_count} {item.invalid_count === 1 ? 'cell' : 'cells'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-[11px] text-gray-600 truncate max-w-[200px]" title={item.sampleList}>
                      {item.sampleList ? (
                        <span className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded border border-gray-200">
                          {item.sampleList}
                        </span>
                      ) : (
                        <span className="text-gray-400 italic">Invalid format</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <button
                        onClick={() => setSelectedIssue(item)}
                        className="btn btn-secondary btn-sm text-[11px] py-1 px-2 flex items-center gap-1 mx-auto hover:bg-cyan-600 hover:text-white hover:border-cyan-600 transition-all font-medium"
                      >
                        <Info className="w-3 h-3" />
                        Details
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Details Modal / Drawer */}
      {selectedIssue && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50 backdrop-blur-xs" onClick={() => setSelectedIssue(null)} />
          <div className="relative z-10 w-full max-w-lg max-h-[85vh] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-gray-200">
            {/* Modal Header */}
            <div className="p-5 border-b border-gray-100 bg-gradient-to-r from-cyan-50 to-blue-50 flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-cyan-100 flex items-center justify-center text-cyan-700">
                  <Wand2 className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-gray-900">Format Issue Details — {selectedIssue.column}</h4>
                  <p className="text-xs text-cyan-700 font-mono">{selectedIssue.expected_format}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedIssue(null)}
                className="w-7 h-7 rounded-full bg-white flex items-center justify-center text-gray-400 hover:text-gray-700 shadow-xs"
              >
                ✕
              </button>
            </div>

            {/* Modal Scrollable Body */}
            <div className="p-5 space-y-4 overflow-y-auto flex-1">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="bg-gray-50 p-3 rounded-xl border border-gray-100">
                  <span className="text-gray-500 font-medium block mb-0.5">Total Affected Cells</span>
                  <span className="text-base font-bold text-gray-900 font-mono">{selectedIssue.invalid_count}</span>
                </div>
                <div className="bg-cyan-50 p-3 rounded-xl border border-cyan-100">
                  <span className="text-cyan-700 font-medium block mb-0.5">AI Recommended Action</span>
                  <span className="text-xs font-bold text-cyan-900 font-mono">Regex Normalization</span>
                </div>
              </div>

              {selectedIssue.samples.size > 0 && (
                <div>
                  <h5 className="text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">
                    Sample Invalid Entries ({selectedIssue.samples.size} unique pattern values)
                  </h5>
                  <div className="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto p-2 bg-gray-50 rounded-xl border border-gray-200">
                    {Array.from(selectedIssue.samples).slice(0, 12).map((val, idx) => (
                      <span key={idx} className="bg-red-50 text-red-800 border border-red-200 px-2 py-1 rounded-md font-mono text-xs font-semibold">
                        {val}
                      </span>
                    ))}
                    {selectedIssue.samples.size > 12 && (
                      <span className="bg-gray-200 text-gray-700 border border-gray-300 px-2 py-1 rounded-md font-mono text-xs font-bold">
                        +{selectedIssue.samples.size - 12} more...
                      </span>
                    )}
                  </div>
                </div>
              )}

              {selectedIssue.rows.length > 0 && (
                <div>
                  <h5 className="text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Affected Row Numbers</h5>
                  <p className="text-xs text-gray-600 font-mono bg-gray-50 p-2.5 rounded-xl border border-gray-200 max-h-24 overflow-y-auto leading-relaxed">
                    Rows: {selectedIssue.rows.slice(0, 50).join(', ')}{selectedIssue.rows.length > 50 ? `... (+${selectedIssue.rows.length - 50} more)` : ''}
                  </p>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-gray-100 bg-gray-50 text-right shrink-0">
              <button
                onClick={() => setSelectedIssue(null)}
                className="btn btn-primary btn-sm px-4 py-1.5 font-semibold text-xs"
              >
                Close Details
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default FormatTable;
