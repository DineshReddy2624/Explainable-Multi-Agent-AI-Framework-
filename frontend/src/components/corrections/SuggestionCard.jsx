import React from 'react';
import { Wand2, CheckCircle2 } from 'lucide-react';

const SuggestionCard = ({ suggestion, onApply }) => {
  return (
    <div className="card p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 hover:border-gray-300 transition-colors">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600 shrink-0 mt-0.5">
          <Wand2 className="w-4 h-4" />
        </div>
        <div>
          <h4 className="text-xs font-bold text-gray-900">
            {suggestion.column} — <span className="text-amber-700 font-medium">{suggestion.issue}</span>
          </h4>
          <p className="text-xs text-gray-500 mt-0.5">{suggestion.action}</p>
        </div>
      </div>

      <button
        onClick={onApply}
        className="btn btn-primary btn-sm flex items-center gap-1.5 font-semibold shrink-0"
      >
        <CheckCircle2 className="w-3.5 h-3.5" />
        <span>Apply Strategy</span>
      </button>
    </div>
  );
};

export default SuggestionCard;
