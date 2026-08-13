import React from 'react';

const MessageBubble = ({ role, content }) => {
  const isUser = role === 'user';

  return (
    <div style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', marginBottom: '0.75rem' }}>
      <div
        style={{
          maxWidth: '75%',
          padding: '0.75rem 1rem',
          borderRadius: 'var(--radius)',
          background: isUser ? 'var(--primary)' : 'var(--bg-card-hover)',
          color: '#fff',
          fontSize: '0.875rem'
        }}
      >
        {content}
      </div>
    </div>
  );
};

export default MessageBubble;
