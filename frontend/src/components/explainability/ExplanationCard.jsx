import React from 'react';

const ExplanationCard = ({ summary }) => {
  return (
    <div className="card">
      <h3 style={{ marginBottom: '0.5rem' }}>Model Explainability (SHAP)</h3>
      <p style={{ color: 'var(--text-muted)' }}>{summary || "Income and Age are the top predictors influencing anomaly classifications."}</p>
    </div>
  );
};

export default ExplanationCard;
