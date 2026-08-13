import React, { useContext } from 'react';
import { DatasetContext } from '../../context/DatasetContext';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { BarChart3 } from 'lucide-react';

const DashboardChart = () => {
  const { analysis } = useContext(DatasetContext) || {};

  const missingReport = analysis?.missing_report || [];
  const chartData = missingReport.length > 0
    ? missingReport.map(item => ({
        name: item.column.length > 10 ? item.column.substring(0, 10) + '...' : item.column,
        missingPct: item.missing_pct,
        nullCount: item.null_count
      }))
    : [
        { name: 'Completeness', score: analysis?.quality_scores?.completeness || 95 },
        { name: 'Validity', score: analysis?.quality_scores?.validity || 92 },
        { name: 'Consistency', score: analysis?.quality_scores?.consistency || 90 },
        { name: 'Uniqueness', score: analysis?.quality_scores?.uniqueness || 98 },
        { name: 'Accuracy', score: analysis?.quality_scores?.accuracy || 94 }
      ];

  const title = missingReport.length > 0 ? 'Column Missing Percentage Breakdown' : 'Data Quality Dimension Distribution';

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
        </div>
        <span className="text-xs text-gray-400 font-medium">Real-time Profile Analytics</span>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
            <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} domain={[0, 100]} />
            <Tooltip
              contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px', fontSize: '12px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
              itemStyle={{ color: '#0f172a' }}
            />
            <Bar dataKey={missingReport.length > 0 ? 'missingPct' : 'score'} fill="#2563eb" radius={[4, 4, 0, 0]} maxBarSize={40} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default DashboardChart;
