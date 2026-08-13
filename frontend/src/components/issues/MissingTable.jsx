import React from 'react';
import { AlertCircle } from 'lucide-react';

const MissingTable = ({ data = [] }) => {
  return (
    <div className="card p-0 overflow-hidden">
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-600" />
          <h3 className="text-sm font-bold text-gray-900">Missing Values Audit</h3>
        </div>
        <span className="text-xs text-gray-400 font-medium">{data.length} Column Issues</span>
      </div>

      <div className="table-container border-0 rounded-none">
        <table>
          <thead>
            <tr>
              <th>Column</th>
              <th>Missing Count</th>
              <th>Percentage</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {data.map((item, idx) => (
              <tr key={idx} className="hover:bg-gray-50 transition-colors">
                <td className="font-mono text-xs font-semibold text-gray-900">{item.column}</td>
                <td>
                  <span className={item.missing_count > 0 ? 'badge badge-warning' : 'badge badge-success'}>
                    {item.missing_count} cells
                  </span>
                </td>
                <td className="text-xs text-gray-600 font-medium">{item.percentage}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default MissingTable;
