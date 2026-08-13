import React from 'react';

const ReportDownload = ({ onDownload }) => {
  return (
    <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div>
        <h3>Executive PDF Data Quality Audit Report</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Comprehensive breakdown of completeness, validity, and ML anomalies.</p>
      </div>
      <button className="btn btn-primary" onClick={onDownload}>Download PDF</button>
    </div>
  );
};

export default ReportDownload;
