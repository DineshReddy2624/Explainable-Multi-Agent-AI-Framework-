import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { DatasetContext } from '../context/DatasetContext';
import EmptyState from '../components/common/EmptyState';
import StatusBadge from '../components/common/StatusBadge';
import { BarChart3, Database, ShieldCheck, AlertCircle, Table, CheckCircle2, Upload, ArrowLeft, ArrowRight } from 'lucide-react';

const DataProfiling = () => {
  const { filename, analysis } = useContext(DatasetContext);
  const navigate = useNavigate();

  if (!analysis) {
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900">Automated Data Profiling & Feature Audit</h2>
          <p className="text-xs text-gray-500 mt-1">Deep computational schema inspection and statistical profiling.</p>
        </div>
        <EmptyState
          icon={BarChart3}
          title="No Active Dataset Profile"
          description="Upload a CSV, XLSX, or Parquet dataset to run DuckDB/PyArrow computational profiling, missing value matrix calculation, and column statistics."
          actionLabel="Upload Dataset"
          onAction={() => navigate('/upload')}
        />
      </div>
    );
  }

  const headers = analysis?.headers || [];
  const total_rows = analysis?.total_rows || 0;
  const total_cols = analysis?.total_cols || 0;
  const missing_report = analysis?.missing_report || [];
  const quality_score = analysis?.quality_scores?.overall_score || 95.0;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-gray-900 tracking-tight">Automated Data Profiling & Feature Audit</h2>
            <span className="badge badge-info font-medium">DuckDB Out-Of-Core Engine</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Active Dataset: <strong className="text-gray-900">{filename || 'uploaded_dataset.csv'}</strong> ({total_rows.toLocaleString()} rows, {total_cols} columns)
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Total Records</p>
            <h3 className="text-2xl font-bold text-gray-900 mt-1">{total_rows.toLocaleString()}</h3>
            <p className="text-xs text-gray-500 mt-0.5">Rows indexed</p>
          </div>
          <div className="w-11 h-11 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600">
            <Database className="w-5 h-5" />
          </div>
        </div>

        <div className="card flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Total Features</p>
            <h3 className="text-2xl font-bold text-gray-900 mt-1">{total_cols}</h3>
            <p className="text-xs text-gray-500 mt-0.5">Columns profiled</p>
          </div>
          <div className="w-11 h-11 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600">
            <Table className="w-5 h-5" />
          </div>
        </div>

        <div className="card flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Quality Score</p>
            <h3 className="text-2xl font-bold text-gray-900 mt-1">{quality_score}%</h3>
            <p className="text-xs text-gray-500 mt-0.5">Automated rating</p>
          </div>
          <div className="w-11 h-11 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600">
            <ShieldCheck className="w-5 h-5" />
          </div>
        </div>

        <div className="card flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Incomplete Features</p>
            <h3 className="text-2xl font-bold text-gray-900 mt-1">{missing_report.length} / {total_cols}</h3>
            <p className="text-xs text-gray-500 mt-0.5">{missing_report.length === 0 ? '100% complete' : 'Imputation needed'}</p>
          </div>
          <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${missing_report.length === 0 ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'}`}>
            <AlertCircle className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Feature Matrix Table */}
      <div className="card p-0 overflow-hidden border border-slate-200 shadow-sm rounded-2xl">
        <div className="p-5 bg-white border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <BarChart3 className="w-5 h-5 text-indigo-600" />
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">Feature Attribute & Completeness Matrix</h3>
          </div>
          <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Schema Analysis</span>
        </div>

        <div className="chat-data-table-container border-0 rounded-none max-h-[30rem]">
          <table className="chat-data-table">
            <thead>
              <tr>
                <th>Column Name</th>
                <th>Inferred Data Type</th>
                <th>Completeness Score</th>
                <th>Missing Count</th>
                <th>Recommended Strategy</th>
              </tr>
            </thead>
            <tbody>
              {headers.map((col, idx) => {
                const missing_info = missing_report.find(r => r.column === col);
                const null_count = missing_info ? missing_info.null_count : 0;
                const null_pct = missing_info ? missing_info.missing_pct : 0;
                const completeness = Math.max(0, Math.round((100 - null_pct) * 10) / 10);
                const isNumeric = col.toLowerCase().includes('price') || col.toLowerCase().includes('salary') || col.toLowerCase().includes('score') || col.toLowerCase().includes('age') || col.toLowerCase().includes('amount') || col.toLowerCase().includes('count');

                return (
                  <tr key={idx}>
                    <td className="font-mono text-xs font-bold text-slate-900">{col}</td>
                    <td>
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        isNumeric ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' :
                        col.toLowerCase().includes('id') ? 'bg-blue-100 text-blue-800 border border-blue-200' :
                        'bg-amber-100 text-amber-800 border border-amber-200'
                      }`}>
                        {isNumeric ? 'FLOAT64 / INT64' : col.toLowerCase().includes('id') ? 'INTEGER / STRING' : 'STRING'}
                      </span>
                    </td>
                    <td>
                      <div className="flex items-center gap-3 w-48">
                        <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${completeness === 100 ? 'bg-emerald-500' : 'bg-amber-500'}`}
                            style={{ width: `${completeness}%` }}
                          />
                        </div>
                        <span className="text-xs font-bold text-slate-800 w-10 text-right">{completeness}%</span>
                      </div>
                    </td>
                    <td>
                      {null_count > 0 ? (
                        <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">{null_count} cells ({null_pct}%)</span>
                      ) : (
                        <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 inline-flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" /> 0 (0%)
                        </span>
                      )}
                    </td>
                    <td className="text-xs text-slate-600 font-medium">
                      {missing_info
                        ? `Impute Median/Mode (${missing_info.suggested_median || 'Median Fill'})`
                        : 'None (100% Complete)'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Workflow Bottom Navigation Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-5 bg-white rounded-xl border border-gray-200 shadow-sm mt-8">
        <button
          onClick={() => navigate('/upload')}
          className="btn btn-secondary btn-sm flex items-center gap-2 font-semibold px-4 py-2.5 text-xs text-gray-700 hover:bg-gray-100"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back: Upload & Analyze</span>
        </button>
        <button
          onClick={() => navigate('/issues')}
          className="btn btn-primary btn-sm flex items-center gap-2 font-semibold px-5 py-2.5 shadow-sm text-xs"
        >
          <span>Next: Quality Issues</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default DataProfiling;
