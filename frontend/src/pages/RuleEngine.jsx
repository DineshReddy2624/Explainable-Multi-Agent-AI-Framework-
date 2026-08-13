import React, { useState } from 'react';
import RuleBuilder from '../components/rules/RuleBuilder';
import RuleTable from '../components/rules/RuleTable';
import { Sliders, Plus, ShieldCheck } from 'lucide-react';

const RuleEngine = () => {
  const [rules, setRules] = useState([
    { rule_name: 'Age Range Validation', target_column: 'age', rule_type: 'RANGE', is_active: true },
    { rule_name: 'Email Format Check', target_column: 'email', rule_type: 'REGEX', is_active: true }
  ]);

  const handleCreateRule = (newRule) => {
    setRules(prev => [...prev, { ...newRule, is_active: true }]);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-gray-900 tracking-tight">Custom Quality Rule Engine Configurator</h2>
            <span className="badge badge-info font-medium">Active Policy Matrix</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Define custom validation constraints, regex patterns, and range checks for automated data auditing.
          </p>
        </div>
      </div>

      <div className="space-y-6">
        <RuleBuilder onCreateRule={handleCreateRule} />
        <RuleTable rules={rules} />
      </div>
    </div>
  );
};

export default RuleEngine;
