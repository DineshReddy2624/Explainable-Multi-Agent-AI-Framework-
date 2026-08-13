import React, { useContext } from 'react';
import { DatasetContext } from '../context/DatasetContext';
import EmptyState from '../components/common/EmptyState';
import StatusBadge from '../components/common/StatusBadge';
import { History as HistoryIcon, Trash2, ShieldCheck, Clock } from 'lucide-react';

const History = () => {
  const { historyLogs = [], clearHistory } = useContext(DatasetContext) || {};

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-gray-900 tracking-tight">Enterprise Audit Trail & Event Logs</h2>
            <span className="badge badge-info font-medium">Immutable Tenant History</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Real-time audit log recording dataset ingestions, quality profiling, PII masking, and user actions.
          </p>
        </div>

        {historyLogs.length > 0 && (
          <button
            onClick={clearHistory}
            className="btn btn-secondary btn-sm flex items-center gap-2 text-gray-600 hover:text-red-600"
          >
            <Trash2 className="w-4 h-4" />
            <span>Clear History</span>
          </button>
        )}
      </div>

      {/* Audit Log Table */}
      {historyLogs.length === 0 ? (
        <EmptyState
          icon={HistoryIcon}
          title="No Audit History Logged"
          description="Upload a dataset or execute quality remediation to view real-time audit event logs."
        />
      ) : (
        <div className="card p-0 overflow-hidden">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-blue-600" />
              <h3 className="text-sm font-bold text-gray-900">Audit Stream ({historyLogs.length} Events)</h3>
            </div>
            <span className="text-xs text-gray-400 font-medium">Recorded Events</span>
          </div>

          <div className="table-container border-0 rounded-none max-h-[550px] overflow-y-auto">
            <table>
              <thead className="sticky top-0 bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="w-48">Timestamp</th>
                  <th className="w-44">Action Event</th>
                  <th>Activity Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {historyLogs.map(log => (
                  <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                    <td className="text-xs text-gray-500 font-mono flex items-center gap-1.5 py-3">
                      <Clock className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                      <span>{log.timestamp}</span>
                    </td>
                    <td>
                      <StatusBadge status={log.action} label={log.action} />
                    </td>
                    <td className="text-xs text-gray-800 font-medium leading-relaxed">{log.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default History;
