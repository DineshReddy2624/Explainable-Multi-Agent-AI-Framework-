import React from 'react';
import { ShieldCheck } from 'lucide-react';

const ConfidenceCard = ({ score = 94.5 }) => {
  return (
    <div className="card flex items-center justify-between">
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">AI Remediation Confidence</p>
        <h2 className="text-2xl font-bold text-blue-600 mt-1">{score}%</h2>
        <p className="text-xs text-gray-500 mt-0.5">Statistical median & mode validation</p>
      </div>
      <div className="w-11 h-11 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600 shrink-0">
        <ShieldCheck className="w-5 h-5" />
      </div>
    </div>
  );
};

export default ConfidenceCard;
