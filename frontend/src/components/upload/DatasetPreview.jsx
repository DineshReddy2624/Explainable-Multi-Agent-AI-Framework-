import React from 'react';
import { Table, Sparkles, Columns, Layers } from 'lucide-react';

const DatasetPreview = ({ data = [], fileName = 'Dataset', onAnalyze, isAnalyzing }) => {
  if (!data || data.length === 0) return null;
  const headers = Object.keys(data[0]);

  return (
    <div className="card mt-6 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            <Table className="w-5 h-5 text-blue-600" />
            <span>Dataset Workspace Preview: {fileName}</span>
          </h3>
          <div className="flex items-center gap-4 mt-1 text-xs text-gray-500 font-medium">
            <span className="flex items-center gap-1">
              <Layers className="w-3.5 h-3.5 text-gray-400" />
              <strong>{data.length}</strong> Sample Records
            </span>
            <span className="flex items-center gap-1">
              <Columns className="w-3.5 h-3.5 text-gray-400" />
              <strong>{headers.length}</strong> Columns
            </span>
          </div>
        </div>

        {onAnalyze && (
          <button
            onClick={onAnalyze}
            disabled={isAnalyzing}
            className="btn btn-primary btn-md flex items-center gap-2 font-semibold shadow-sm"
          >
            <Sparkles className="w-4 h-4" />
            <span>{isAnalyzing ? 'Executing AI Multi-Agent Analysis...' : 'Run AI Multi-Agent Analysis'}</span>
          </button>
        )}
      </div>

      <div className="table-container max-h-[420px] overflow-y-auto border border-gray-200 rounded-lg">
        <table>
          <thead className="sticky top-0 z-10 bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="w-12 text-center text-xs font-semibold text-gray-500 uppercase">#</th>
              {headers.map(h => (
                <th key={h} className="text-xs font-semibold text-gray-700 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {data.map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50 transition-colors">
                <td className="text-center text-xs text-gray-400 font-mono">{idx + 1}</td>
                {headers.map(h => (
                  <td key={h} className="text-xs text-gray-800 font-mono">
                    {row[h] !== undefined && row[h] !== null && String(row[h]).trim() !== '' ? (
                      String(row[h])
                    ) : (
                      <span className="badge badge-warning text-[10px] py-0.5 px-1.5">NULL</span>
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DatasetPreview;
