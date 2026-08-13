import React from 'react';

const RuleEditor = ({ rule }) => {
  return (
    <div className="card">
      <h3>Edit Rule Settings</h3>
      <p style={{ color: 'var(--text-muted)' }}>Configure parameters for target rule execution.</p>
    </div>
  );
};

export default RuleEditor;
