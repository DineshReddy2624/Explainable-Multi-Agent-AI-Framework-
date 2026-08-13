import React from 'react';

const SHAPChart = ({ features = [] }) => {
  return (
    <div className="card" style={{ marginTop: '1.5rem' }}>
      <h3 style={{ marginBottom: '1rem' }}>Feature Importance Impact</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {features.map((item, idx) => (
          <div key={idx}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
              <span>{item.feature}</span>
              <span>{item.shap_value}</span>
            </div>
            <div style={{ width: '100%', height: '8px', background: 'var(--border)', borderRadius: '4px' }}>
              <div style={{ width: `${item.shap_value * 100}%`, height: '100%', background: 'var(--primary)', borderRadius: '4px' }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SHAPChart;
