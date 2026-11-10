import React, { useContext } from 'react';
import { DatasetContext } from '../../context/DatasetContext';

const ReportDownload = ({ onDownload }) => {
  const { hasDatasetChanges } = useContext(DatasetContext) || {};

  return (
    <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div>
        <h3 className="font-bold text-gray-900 text-sm">Executive PDF Data Quality Audit Report</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Comprehensive breakdown of completeness, validity, and ML anomalies.</p>
      </div>
      <button
        className={`btn ${hasDatasetChanges ? 'btn-primary' : 'bg-gray-200 text-gray-400 border border-gray-300 cursor-not-allowed shadow-none'}`}
        disabled={!hasDatasetChanges}
        title={!hasDatasetChanges ? "No changes made to dataset yet" : "Download Executive PDF Audit Report"}
        onClick={onDownload}
      >
        Download PDF {!hasDatasetChanges && '(Disabled)'}
      </button>
    </div>
  );
};

export default ReportDownload;
