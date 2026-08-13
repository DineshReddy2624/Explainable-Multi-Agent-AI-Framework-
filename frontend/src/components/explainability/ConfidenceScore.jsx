import React from 'react';

const ConfidenceScore = ({ score = 94.0 }) => {
  return (
    <div className="card">
      <h4>Prediction Confidence</h4>
      <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--accent)', marginTop: '0.25rem' }}>{score}%</div>
    </div>
  );
};

export default ConfidenceScore;
