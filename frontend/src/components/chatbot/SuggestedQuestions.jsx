import React from 'react';

const SuggestedQuestions = ({ questions = [], onSelect }) => {
  return (
    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', margin: '0.5rem 0' }}>
      {questions.map((q, idx) => (
        <button
          key={idx}
          onClick={() => onSelect(q)}
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border)', color: 'var(--text-muted)', padding: '0.4rem 0.8rem', borderRadius: '16px', fontSize: '0.75rem', cursor: 'pointer' }}
        >
          💡 {q}
        </button>
      ))}
    </div>
  );
};

export default SuggestedQuestions;
