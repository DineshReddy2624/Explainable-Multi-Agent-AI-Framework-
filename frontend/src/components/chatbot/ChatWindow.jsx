import React from 'react';

const ChatWindow = ({ children }) => {
  return (
    <div className="card" style={{ height: '500px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
      {children}
    </div>
  );
};

export default ChatWindow;
