import React from 'react';

const DuplicateTable = ({ data = [] }) => {
  return (
    <div className="card">
      <h3 style={{ marginBottom: '1rem' }}>Duplicate Records</h3>
      <p style={{ color: 'var(--text-muted)' }}>Identified duplicates across dataset key columns.</p>
    </div>
  );
};

export default DuplicateTable;
