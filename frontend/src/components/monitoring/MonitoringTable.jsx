import React from 'react';

const MonitoringTable = ({ metrics = [] }) => {
  return (
    <div className="card">
      <h3 style={{ marginBottom: '1rem' }}>Active Quality Monitors</h3>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Metric</th>
              <th>Value</th>
              <th>Status</th>
              <th>Last Checked</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((m, idx) => (
              <tr key={idx}>
                <td>{m.metric_name}</td>
                <td>{m.metric_value}%</td>
                <td><span style={{ color: m.status === 'HEALTHY' ? 'var(--success)' : 'var(--warning)' }}>{m.status}</span></td>
                <td>{new Date(m.timestamp).toLocaleTimeString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default MonitoringTable;
