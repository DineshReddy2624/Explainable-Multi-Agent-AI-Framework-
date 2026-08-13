import React from 'react';

const ActivityTimeline = ({ events = [] }) => {
  return (
    <div className="card">
      <h3 style={{ marginBottom: '1rem' }}>Audit Timeline</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {events.map((e, idx) => (
          <div key={idx} style={{ display: 'flex', gap: '1rem', borderLeft: '2px solid var(--primary)', paddingLeft: '1rem' }}>
            <div>
              <div style={{ fontSize: '0.875rem', fontWeight: '600' }}>{e.event}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{e.timestamp}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ActivityTimeline;
