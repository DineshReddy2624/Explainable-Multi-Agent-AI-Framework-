import React from 'react';
import { ShieldCheck, AlertCircle, AlertTriangle, HelpCircle } from 'lucide-react';
import StatusBadge from '../common/StatusBadge';

const QualityCard = ({ score = 0, status = 'N/A' }) => {
  let color = 'text-gray-400';
  let bg = 'bg-gray-50';
  let Icon = HelpCircle;

  if (status === 'Optimal' || score >= 85) {
    color = 'text-emerald-600';
    bg = 'bg-emerald-50';
    Icon = ShieldCheck;
  } else if (status === 'Warning' || score >= 70) {
    color = 'text-amber-600';
    bg = 'bg-amber-50';
    Icon = AlertTriangle;
  } else if (status === 'Critical') {
    color = 'text-red-600';
    bg = 'bg-red-50';
    Icon = AlertCircle;
  }

  return (
    <div className="card flex items-center justify-between">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Overall Quality Score</p>
          {status !== 'N/A' && <StatusBadge status={status === 'Optimal' ? 'SUCCESS' : (status === 'Warning' ? 'WARNING' : 'FAILED')} label={status} />}
        </div>
        <h3 className="text-2xl font-bold text-gray-900">{score ? `${score}%` : 'N/A'}</h3>
        <p className="text-xs text-gray-500 mt-0.5">Automated Multi-Agent Assessment</p>
      </div>
      <div className={`w-11 h-11 rounded-xl ${bg} flex items-center justify-center ${color} shrink-0`}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
  );
};

export default QualityCard;
