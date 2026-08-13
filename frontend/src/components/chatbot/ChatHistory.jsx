import React from 'react';

const ChatHistory = ({ history = [] }) => {
  return (
    <div style={{ flex: 1, overflowY: 'auto', paddingRight: '0.5rem' }}>
      {history.map((msg, idx) => (
        <div key={idx} style={{ marginBottom: '0.5rem' }}>
          <strong>{msg.role}:</strong> {msg.content}
        </div>
      ))}
    </div>
  );
};

export default ChatHistory;
