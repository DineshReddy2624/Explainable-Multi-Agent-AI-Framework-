import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { DatasetContext } from '../context/DatasetContext';
import MissingTable from '../components/issues/MissingTable';
import FormatTable from '../components/issues/FormatTable';
import AnomalyTable from '../components/issues/AnomalyTable';
import EmptyState from '../components/common/EmptyState';
import { AlertCircle, Wand2, Upload } from 'lucide-react';

const Issues = () => {
  const { analysis } = useContext(DatasetContext);
  const navigate = useNavigate();

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

  const missingData = (analysis?.missing_report || []).map(r => ({
    column: r.column,
    missing_count: r.null_count,
    percentage: r.missing_pct
  }));

  const formatData = (analysis?.format_issues || []).map(r => ({
    column: r.column,
    expected_format: r.expected_format || 'Standard Format',
    invalid_count: 1
  }));

  const anomalyData = (analysis?.anomalies || []).map(a => ({
    algorithm: `Row #${a.row_index + 1} (${a.column})`,
    anomaly_count: a.anomaly_score
  }));

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-gray-900 tracking-tight">Detected Quality Issues & Format Errors</h2>
            <span className="badge badge-warning font-medium">Auto-Audited</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Real-time multi-agent scan across completeness, format consistency, and statistical outliers.
          </p>
        </div>
        <button
          onClick={() => navigate('/corrections')}
          className="btn btn-primary btn-sm flex items-center gap-2 font-semibold"
        >
          <Wand2 className="w-4 h-4" />
          <span>Remediate All Issues</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <MissingTable data={missingData.length > 0 ? missingData : [{ column: 'None', missing_count: 0, percentage: 0 }]} />
        <FormatTable data={formatData.length > 0 ? formatData : [{ column: 'None', expected_format: 'Verified', invalid_count: 0 }]} />
        <AnomalyTable data={anomalyData.length > 0 ? anomalyData : [{ algorithm: 'Isolation Forest Scan', anomaly_count: 0 }]} />
      </div>
    </div>
  );
};

export default Issues;
