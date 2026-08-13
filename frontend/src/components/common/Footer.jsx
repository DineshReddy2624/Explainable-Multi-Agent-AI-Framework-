import React from 'react';

const Footer = () => {
  return (
    <footer className="h-10 bg-white border-t border-gray-200 px-6 flex items-center justify-between text-xs text-gray-500 shrink-0">
      <div>
        <span>Enterprise Data Intelligence & Quality Platform</span>
      </div>
      <div className="flex items-center gap-4">
        <span>Version 1.0.0</span>
        <span>•</span>
        <span className="text-emerald-600 font-medium flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
          System Operational
        </span>
      </div>
    </footer>
  );
};

export default Footer;
