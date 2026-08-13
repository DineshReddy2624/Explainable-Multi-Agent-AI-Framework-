import React from 'react';

const LiveChart = () => {
  return (
    <div className="card">
      <h3>Real-time Streaming Quality Index</h3>
      <div style={{ height: '180px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
        [ Live Streaming Telemetry Active ]
      </div>
    </div>
  );
};

export default LiveChart;
