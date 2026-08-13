import React, { useState } from 'react';
import { Plus, Sliders } from 'lucide-react';

const RuleBuilder = ({ onCreateRule }) => {
  const [name, setName] = useState('');
  const [col, setCol] = useState('');
  const [type, setType] = useState('RANGE');

  const handleSubmit = (e) => {
    e.preventDefault();
    onCreateRule({ rule_name: name, target_column: col, rule_type: type });
    setName('');
    setCol('');
  };

  return (
    <form className="card p-5" onSubmit={handleSubmit}>
      <div className="flex items-center gap-2 mb-4">
        <Sliders className="w-4 h-4 text-blue-600" />
        <h3 className="text-sm font-bold text-gray-900">Define New Data Quality Rule</h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
        <div>
          <label className="block text-xs font-semibold text-gray-700 mb-1">Rule Name</label>
          <input
            type="text"
            placeholder="Age Range Boundary"
            value={name}
            onChange={e => setName(e.target.value)}
            required
            className="input"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-700 mb-1">Target Feature Column</label>
          <input
            type="text"
            placeholder="age"
            value={col}
            onChange={e => setCol(e.target.value)}
            required
            className="input"
          />
        </div>
        <div className="flex gap-2">
          <div className="flex-1">
            <label className="block text-xs font-semibold text-gray-700 mb-1">Rule Condition Type</label>
            <select
              value={type}
              onChange={e => setType(e.target.value)}
              className="input bg-white"
            >
              <option value="RANGE">RANGE</option>
              <option value="REGEX">REGEX</option>
              <option value="NOT_NULL">NOT_NULL</option>
              <option value="UNIQUE">UNIQUE</option>
            </select>
          </div>
          <button type="submit" className="btn btn-primary btn-sm flex items-center gap-1.5 font-semibold h-[38px] px-4 self-end">
            <Plus className="w-4 h-4" />
            <span>Add Rule</span>
          </button>
        </div>
      </div>
    </form>
  );
};

export default RuleBuilder;
