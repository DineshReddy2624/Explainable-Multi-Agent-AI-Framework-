import React from 'react';
import StatusBadge from '../common/StatusBadge';
import { Sliders } from 'lucide-react';

const RuleTable = ({ rules = [] }) => {
  return (
    <div className="card p-0 overflow-hidden">
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-bold text-gray-900">Active Quality Policy Matrix</h3>
        </div>
        <span className="text-xs text-gray-400 font-medium">{rules.length} Rules Enforced</span>
      </div>

      <div className="table-container border-0 rounded-none">
        <table>
          <thead>
            <tr>
              <th>Rule Name</th>
              <th>Target Feature Column</th>
              <th>Rule Condition Type</th>
              <th>Enforcement Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {rules.map((r, idx) => (
              <tr key={idx} className="hover:bg-gray-50 transition-colors">
                <td className="font-semibold text-xs text-gray-900">{r.rule_name}</td>
                <td className="font-mono text-xs text-gray-800">{r.target_column}</td>
                <td>
                  <span className="badge badge-info font-mono text-[10px]">{r.rule_type}</span>
                </td>
                <td>
                  <StatusBadge status={r.is_active ? 'SUCCESS' : 'QUEUED'} label={r.is_active ? 'Active Enforced' : 'Disabled'} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RuleTable;
