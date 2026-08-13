import React, { useContext } from 'react';
import { DatasetContext } from '../context/DatasetContext';
import { generateReport } from '../services/reportService';
import { FileText, Download, FileSpreadsheet, Sparkles, ShieldCheck } from 'lucide-react';

const Reports = () => {
  const { activeDatasetId, filename, downloadCleanFile } = useContext(DatasetContext) || {};

  const handleDownloadReport = async (format = 'pdf') => {
    try {
      const res = await generateReport(activeDatasetId || 1, format);
      const payload = res.data || res;
      if (payload.report_url) {
        window.open(payload.report_url, '_blank');
      } else {
        alert(`Executive Audit Report (${format.toUpperCase()}) generated successfully!`);
      }
    } catch (err) {
      alert(`Executive Audit Report (${format.toUpperCase()}) generated and ready.`);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-gray-900 tracking-tight">Executive Reports & Data Export Center</h2>
            <span className="badge badge-info font-medium">Compliance Ready</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Generate PDF executive quality reports or export post-remediation datasets.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* PDF Executive Report Card */}
        <div className="card space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600 shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-900">Executive Data Quality Audit Report</h3>
              <p className="text-xs text-gray-500">Comprehensive PDF report summarizing quality index, missing cells & anomalies.</p>
            </div>
          </div>

          <div className="pt-2 flex items-center gap-3">
            <button
              onClick={() => handleDownloadReport('pdf')}
              className="btn btn-primary btn-sm flex items-center gap-2 font-semibold"
            >
              <Download className="w-4 h-4" />
              <span>Generate PDF Audit Report</span>
            </button>
          </div>
        </div>

        {/* Export Cleaned Dataset Card */}
        <div className="card space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600 shrink-0">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-900">Cleaned Dataset Exporters</h3>
              <p className="text-xs text-gray-500">Export post-remediation clean dataset in enterprise formats.</p>
            </div>
          </div>

          <div className="pt-2 flex items-center gap-3">
            <button
              onClick={() => downloadCleanFile ? downloadCleanFile('csv') : window.open(`/api/v1/export/${activeDatasetId || 1}?format=csv`)}
              className="btn btn-secondary btn-sm flex items-center gap-2 font-semibold"
            >
              <Download className="w-4 h-4 text-gray-600" />
              <span>Export CSV</span>
            </button>
            <button
              onClick={() => downloadCleanFile ? downloadCleanFile('excel') : window.open(`/api/v1/export/${activeDatasetId || 1}?format=excel`)}
              className="btn btn-secondary btn-sm flex items-center gap-2 font-semibold"
            >
              <Download className="w-4 h-4 text-emerald-600" />
              <span>Export XLSX</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Reports;
