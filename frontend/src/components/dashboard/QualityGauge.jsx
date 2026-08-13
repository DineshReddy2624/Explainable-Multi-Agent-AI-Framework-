import React from 'react';

const QualityGauge = ({ value = 0 }) => {
  const normalizedValue = Math.min(100, Math.max(0, value));
  const strokeDashoffset = 283 - (283 * normalizedValue) / 100;

  let strokeColor = '#94a3b8';
  if (normalizedValue >= 85) strokeColor = '#10b981';
  else if (normalizedValue >= 70) strokeColor = '#f59e0b';
  else if (normalizedValue > 0) strokeColor = '#ef4444';

  return (
    <div className="card flex flex-col items-center justify-center p-6 text-center">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">Quality Index Rating</h3>
      
      <div className="relative w-36 h-36 flex items-center justify-center">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="45"
            stroke="#f1f5f9"
            strokeWidth="8"
            fill="transparent"
          />
          <circle
            cx="50"
            cy="50"
            r="45"
            stroke={strokeColor}
            strokeWidth="8"
            strokeDasharray="283"
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        <div className="absolute flex flex-col items-center">
          <span className="text-3xl font-extrabold text-gray-900">{normalizedValue}%</span>
          <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mt-0.5">Health Score</span>
        </div>
      </div>

      <p className="text-xs text-gray-500 mt-4 leading-relaxed">
        {normalizedValue >= 85
          ? 'Dataset health is optimal for downstream ML pipelines.'
          : normalizedValue >= 70
          ? 'Minor missing cells detected. Remediation recommended.'
          : normalizedValue > 0
          ? 'Critical data quality degradation. Immediate cleanup needed.'
          : 'Upload a dataset to run quality index calculation.'}
      </p>
    </div>
  );
};

export default QualityGauge;
