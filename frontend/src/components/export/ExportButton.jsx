import React from 'react';

const ExportButton = ({ onExport, format = "CSV" }) => {
  return (
    <button className="btn btn-secondary" onClick={() => onExport(format.toLowerCase())}>
      📥 Export as {format}
    </button>
  );
};

export default ExportButton;
