import React from 'react';

const MetricCard = ({ title, value, subtitle, icon: Icon, color = 'text-blue-600', bg = 'bg-blue-50' }) => {
  return (
    <div className="card flex items-center justify-between">
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{title}</p>
        <h3 className="text-2xl font-bold text-gray-900 mt-1">{value}</h3>
        {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
      {Icon && (
        <div className={`w-11 h-11 rounded-xl ${bg} flex items-center justify-center ${color} shrink-0`}>
          <Icon className="w-5 h-5" />
        </div>
      )}
    </div>
  );
};

export default MetricCard;
