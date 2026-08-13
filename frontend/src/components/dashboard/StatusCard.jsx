import React from 'react';

const StatusCard = ({ title = "System Status", status = "Optimal", details = "All background workers running" }) => {
  return (
    <div className="card">
      <h4 style={{ marginBottom: '0.5rem' }}>{title}</h4>
      <div style={{ color: 'var(--success)', fontWeight: '600', marginBottom: '0.25rem' }}>● {status}</div>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>{details}</p>
    </div>
  );
};

export default StatusCard;
