import React, { useState } from 'react';

const ChatInput = ({ onSend }) => {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    onSend(text);
    setText('');
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
      <input
        type="text"
        placeholder="Ask a question about your dataset..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        style={{ flex: 1, padding: '0.75rem', borderRadius: 'var(--radius)', border: '1px solid var(--border)', background: 'var(--bg-dark)', color: '#fff' }}
      />
      <button type="submit" className="btn btn-primary">Send</button>
    </form>
  );
};

export default ChatInput;
