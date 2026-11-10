import React, { useContext, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { DatasetContext } from '../../context/DatasetContext';
import QualityCard from './QualityCard';
import MetricCard from './MetricCard';
import QualityGauge from './QualityGauge';
import ExplanationCard from '../explainability/ExplanationCard';
import SHAPChart from '../explainability/SHAPChart';
import Loader from '../common/Loader';
import {
  ShieldCheck,
  AlertCircle,
  AlertTriangle,
  Search,
  Sparkles,
  FileSpreadsheet,
  FileText,
  RefreshCw,
  FolderOpen,
  Table,
  Columns,
  Layers,
  CheckCircle2,
  HelpCircle,
  Hash,
  Database,
  Info,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  ArrowRight,
  BarChart3,
  CopyCheck
} from 'lucide-react';

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

const UnifiedAnalysisReport = ({ onReset, fileInfo }) => {
  const {
    filename,
    originalRecords,
    rawRecords,
    analysis,
    loading
  } = useContext(DatasetContext);

  const navigate = useNavigate();

  // Diagnostics Tab: 'schema' | 'missing' | 'duplicates' | 'format' | 'anomalies' | 'statistics'
  const [activeDiagnosticTab, setActiveDiagnosticTab] = useState('schema');

  // Read-only preview state
  const [previewSearch, setPreviewSearch] = useState('');
  const [previewPage, setPreviewPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  if (loading) {
    return (
      <div className="card my-8">
        <Loader label="Executing dynamic analysis, multi-agent profiling, and calculating quality scores..." />
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="card text-center py-12 space-y-4 my-8">
        <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center text-blue-600 mx-auto">
          <FolderOpen className="w-6 h-6" />
        </div>
        <h3 className="text-base font-bold text-gray-900">No Active Analysis Payload</h3>
        <p className="text-xs text-gray-500 max-w-sm mx-auto">
          Please upload a dataset file to generate real-time AI quality and profiling findings.
        </p>
        {onReset && (
          <button onClick={onReset} className="btn btn-primary btn-sm flex items-center gap-2 mx-auto mt-2">
            <FileSpreadsheet className="w-4 h-4" />
            <span>Select & Analyze Dataset File</span>
          </button>
        )}
      </div>
    );
  }

  const {
    total_rows = 0,
    total_cols = 0,
    headers = [],
    missing_report = [],
    total_missing_cells = 0,
    duplicate_count = 0,
    format_issues = [],
    anomalies = [],
    shap_features = [],
    quality_scores = {},
    datatype_map = {},
    column_duplicates = []
  } = analysis;

  const {
    overall_score = 98.4,
    completeness = 98.4,
    uniqueness = 98.0,
    validity = 95.0,
    consistency = 94.0
  } = quality_scores || {};

  // Resolve file metadata
  const displayName = filename || fileInfo?.name || 'uploaded_dataset.csv';
  const fileExt = (displayName.split('.').pop() || 'csv').toUpperCase();
  const displaySize = fileInfo?.size
    ? formatBytes(fileInfo.size)
    : formatBytes(total_rows * total_cols * 18);

  // Original unmodified records for read-only preview and stats
  const recordsToDisplay = useMemo(() => {
    return originalRecords && originalRecords.length > 0
      ? originalRecords
      : rawRecords || [];
  }, [originalRecords, rawRecords]);

  // Compute column statistics and schema metrics from unmodified records
  const columnMetrics = useMemo(() => {
    if (!recordsToDisplay.length || !headers.length) return [];
    const rowCount = recordsToDisplay.length;

    const missingMap = {};
    (missing_report || []).forEach(m => {
      missingMap[m.column] = m;
    });

    return headers.map(col => {
      const rawVals = recordsToDisplay.map(r => r[col]);
      const nonNullVals = rawVals.filter(
        v => v !== null && v !== undefined && String(v).trim() !== '' && String(v).toLowerCase() !== 'nan'
      );
      const nullCount = rowCount - nonNullVals.length;
      const missingPct = rowCount > 0 ? Number(((nullCount / rowCount) * 100).toFixed(2)) : 0;
      const uniqueSet = new Set(nonNullVals.map(v => String(v)));
      const uniqueCount = uniqueSet.size;
      const dtype = datatype_map[col] || (typeof nonNullVals[0] === 'number' ? 'int64' : 'object');

      // Numeric stats calculation
      const numVals = nonNullVals.map(v => Number(v)).filter(v => !isNaN(v));
      const isNumeric = numVals.length > 0 && numVals.length === nonNullVals.length;

      let stats = null;
      if (isNumeric && numVals.length > 0) {
        const sorted = [...numVals].sort((a, b) => a - b);
        const count = sorted.length;
        const min = sorted[0];
        const max = sorted[count - 1];
        const sum = sorted.reduce((acc, v) => acc + v, 0);
        const mean = Number((sum / count).toFixed(2));
        const mid = Math.floor(count / 2);
        const median = count % 2 !== 0 ? sorted[mid] : Number(((sorted[mid - 1] + sorted[mid]) / 2).toFixed(2));
        const q1 = sorted[Math.floor(count * 0.25)];
        const q3 = sorted[Math.floor(count * 0.75)];
        const iqr = Number((q3 - q1).toFixed(2));
        const variance = sorted.reduce((acc, v) => acc + Math.pow(v - mean, 2), 0) / count;
        const std = Number(Math.sqrt(variance).toFixed(2));

        stats = { count, min, max, mean, median, q1, q3, iqr, std };
      } else {
        // Categorical stats calculation
        const freqMap = {};
        nonNullVals.forEach(v => {
          const s = String(v);
          freqMap[s] = (freqMap[s] || 0) + 1;
        });
        let topVal = 'N/A';
        let topFreq = 0;
        Object.entries(freqMap).forEach(([val, cnt]) => {
          if (cnt > topFreq) {
            topFreq = cnt;
            topVal = val;
          }
        });
        stats = { count: nonNullVals.length, uniqueCount, topVal, topFreq };
      }

      return {
        name: col,
        dtype,
        nonNullCount: nonNullVals.length,
        nullCount,
        missingPct,
        uniqueCount,
        isNumeric,
        stats
      };
    });
  }, [recordsToDisplay, headers, missing_report, datatype_map]);

  // Read-only Preview filtering & pagination
  const filteredRecords = useMemo(() => {
    if (!previewSearch.trim()) return recordsToDisplay;
    const q = previewSearch.toLowerCase();
    return recordsToDisplay.filter(row =>
      Object.values(row).some(val => val !== null && val !== undefined && String(val).toLowerCase().includes(q))
    );
  }, [recordsToDisplay, previewSearch]);

  const totalPages = Math.max(1, Math.ceil(filteredRecords.length / pageSize));
  const paginatedRows = useMemo(() => {
    const start = (previewPage - 1) * pageSize;
    return filteredRecords.slice(start, start + pageSize);
  }, [filteredRecords, previewPage, pageSize]);

  const startRecordIdx = filteredRecords.length === 0 ? 0 : (previewPage - 1) * pageSize + 1;
  const endRecordIdx = Math.min(filteredRecords.length, previewPage * pageSize);

  // Informational AI Findings
  const aiFindings = useMemo(() => {
    const findings = [];
    if (overall_score >= 90) {
      findings.push({
        type: 'positive',
        title: 'High Overall Baseline Quality',
        desc: `The dataset demonstrates strong health with an overall quality index of ${overall_score}/100.`
      });
    } else if (overall_score >= 75) {
      findings.push({
        type: 'warning',
        title: 'Moderate Quality Discrepancies Detected',
        desc: `The overall quality score is ${overall_score}/100. Remediation in subsequent stages will resolve detected issues.`
      });
    } else {
      findings.push({
        type: 'critical',
        title: 'Critical Hygiene Issues Flagged',
        desc: `The dataset score of ${overall_score}/100 indicates significant data cleanliness risks requiring cleaning.`
      });
    }

    if (total_missing_cells > 0) {
      findings.push({
        type: 'warning',
        title: `${total_missing_cells} Missing Values Identified`,
        desc: `Detected across ${missing_report.length} column(s). These values remain unmodified and can be imputed in Stage 5 (AI Remediation).`
      });
    } else {
      findings.push({
        type: 'positive',
        title: 'Complete Column Population',
        desc: 'Zero missing or null cells detected across all attributes.'
      });
    }

    if (duplicate_count > 0) {
      const dupPct = ((duplicate_count / (total_rows || 1)) * 100).toFixed(2);
      findings.push({
        type: 'warning',
        title: `${duplicate_count} Duplicate Records Flagged (${dupPct}%)`,
        desc: 'Duplicate rows identified. Deduplication strategies remain available later in the workflow.'
      });
    }

    if (anomalies.length > 0) {
      findings.push({
        type: 'info',
        title: `${anomalies.length} Statistical/ML Outliers Detected`,
        desc: 'Flagged via multi-algorithm Isolation Forest and Z-Score tests. Detailed record inspection is available in Stage 4.'
      });
    }

    if (format_issues.length > 0) {
      findings.push({
        type: 'info',
        title: `${format_issues.length} Format Inconsistencies Found`,
        desc: 'Identified pattern or validation deviations in string or numeric fields.'
      });
    }

    return findings;
  }, [overall_score, total_missing_cells, missing_report, duplicate_count, total_rows, anomalies, format_issues]);

  return (
    <div className="space-y-8 mt-6">
      {/* 1. DATASET SUMMARY & HEADER BANNER */}
      <div className="card bg-gradient-to-r from-blue-50/80 via-white to-indigo-50/50 border-blue-200 p-6 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold text-blue-700 uppercase tracking-wider flex items-center gap-1.5 bg-blue-100/70 px-2.5 py-0.5 rounded-md">
                <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                Stage 1 — Upload & Initial Analysis
              </span>
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-md">
                <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                Read-Only Inspection Mode
              </span>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mt-2">{displayName}</h2>
            <p className="text-xs text-gray-600 mt-1 max-w-2xl">
              Informational quality evaluation and automated diagnostics completed. The original dataset remains unmodified.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {onReset && (
              <button
                type="button"
                onClick={onReset}
                className="btn btn-secondary btn-sm flex items-center gap-2 font-medium"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Analyze Another File</span>
              </button>
            )}
            <button
              type="button"
              onClick={() => navigate('/profiling')}
              className="btn btn-primary btn-sm flex items-center gap-2 font-semibold shadow-sm"
            >
              <span>Continue to Data Profile</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Dataset Summary Attributes Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 mt-6 pt-5 border-t border-blue-100/80">
          <div className="bg-white p-3 rounded-lg border border-gray-200 shadow-2xs">
            <span className="text-[10px] font-bold uppercase text-gray-400">File Name</span>
            <p className="text-xs font-semibold text-gray-900 truncate mt-0.5" title={displayName}>
              {displayName}
            </p>
          </div>
          <div className="bg-white p-3 rounded-lg border border-gray-200 shadow-2xs">
            <span className="text-[10px] font-bold uppercase text-gray-400">File Type</span>
            <p className="text-xs font-bold text-indigo-600 font-mono mt-0.5">
              {fileExt}
            </p>
          </div>
          <div className="bg-white p-3 rounded-lg border border-gray-200 shadow-2xs">
            <span className="text-[10px] font-bold uppercase text-gray-400">File Size</span>
            <p className="text-xs font-semibold text-gray-800 font-mono mt-0.5">
              {displaySize}
            </p>
          </div>
          <div className="bg-white p-3 rounded-lg border border-gray-200 shadow-2xs">
            <span className="text-[10px] font-bold uppercase text-gray-400">Total Rows</span>
            <p className="text-xs font-bold text-gray-900 font-mono mt-0.5">
              {total_rows.toLocaleString()}
            </p>
          </div>
          <div className="bg-white p-3 rounded-lg border border-gray-200 shadow-2xs">
            <span className="text-[10px] font-bold uppercase text-gray-400">Total Columns</span>
            <p className="text-xs font-bold text-gray-900 font-mono mt-0.5">
              {total_cols}
            </p>
          </div>
          <div className="bg-white p-3 rounded-lg border border-gray-200 shadow-2xs">
            <span className="text-[10px] font-bold uppercase text-gray-400">Upload Status</span>
            <p className="text-xs font-semibold text-emerald-700 flex items-center gap-1 mt-0.5">
              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
              Completed
            </p>
          </div>
          <div className="bg-white p-3 rounded-lg border border-gray-200 shadow-2xs">
            <span className="text-[10px] font-bold uppercase text-gray-400">Analysis Status</span>
            <p className="text-xs font-semibold text-emerald-700 flex items-center gap-1 mt-0.5">
              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
              Completed
            </p>
          </div>
          <div className="bg-white p-3 rounded-lg border border-gray-200 shadow-2xs">
            <span className="text-[10px] font-bold uppercase text-gray-400">Quality Score</span>
            <p className="text-xs font-bold text-blue-700 font-mono mt-0.5">
              {overall_score}/100
            </p>
          </div>
        </div>
      </div>

      {/* 9 & 10. DATA QUALITY INFORMATION & ISSUE SUMMARY */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <ShieldCheck className="w-5 h-5 text-blue-600" />
          <h3 className="text-base font-bold text-gray-900">Quality Health & Detected Issues Summary</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
          <QualityCard
            score={overall_score}
            status={overall_score >= 85 ? 'Optimal' : overall_score >= 70 ? 'Warning' : 'Critical'}
          />
          <MetricCard
            title="Missing Values"
            value={`${total_missing_cells} cells`}
            icon={AlertCircle}
            color={total_missing_cells === 0 ? 'text-emerald-600' : 'text-amber-600'}
            bg={total_missing_cells === 0 ? 'bg-emerald-50' : 'bg-amber-50'}
          />
          <MetricCard
            title="Duplicate Rows"
            value={`${duplicate_count} rows`}
            icon={CopyCheck}
            color={duplicate_count === 0 ? 'text-emerald-600' : 'text-amber-600'}
            bg={duplicate_count === 0 ? 'bg-emerald-50' : 'bg-amber-50'}
          />
          <MetricCard
            title="Format Errors"
            value={`${format_issues.length} invalid`}
            icon={AlertTriangle}
            color={format_issues.length === 0 ? 'text-emerald-600' : 'text-indigo-600'}
            bg={format_issues.length === 0 ? 'bg-emerald-50' : 'bg-indigo-50'}
          />
          <MetricCard
            title="Potential Outliers"
            value={`${anomalies.length} detected`}
            icon={TrendingUp}
            color={anomalies.length === 0 ? 'text-emerald-600' : 'text-red-600'}
            bg={anomalies.length === 0 ? 'bg-emerald-50' : 'bg-red-50'}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <QualityGauge value={overall_score} />
          <div className="card space-y-3">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Core Quality Dimensions (Informational)
            </h4>
            <div className="flex justify-between items-center text-xs py-2 border-b border-gray-100">
              <span className="text-gray-600 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
                Completeness:
              </span>
              <strong className="text-gray-900 font-semibold font-mono">{completeness}%</strong>
            </div>
            <div className="flex justify-between items-center text-xs py-2 border-b border-gray-100">
              <span className="text-gray-600 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
                Uniqueness:
              </span>
              <strong className="text-gray-900 font-semibold font-mono">{uniqueness}%</strong>
            </div>
            <div className="flex justify-between items-center text-xs py-2 border-b border-gray-100">
              <span className="text-gray-600 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
                Validity:
              </span>
              <strong className="text-gray-900 font-semibold font-mono">{validity}%</strong>
            </div>
            <div className="flex justify-between items-center text-xs py-2">
              <span className="text-gray-600 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
                Consistency:
              </span>
              <strong className="text-gray-900 font-semibold font-mono">{consistency}%</strong>
            </div>
          </div>
        </div>
      </div>

      {/* 2. READ-ONLY DATASET PREVIEW */}
      <div className="card p-0 overflow-hidden border border-gray-200 shadow-sm">
        <div className="p-5 border-b border-gray-200 bg-gray-50/70 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Table className="w-5 h-5 text-blue-600" />
              <h3 className="text-base font-bold text-gray-900">Read-only Dataset Preview</h3>
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-gray-700 bg-gray-200/80 px-2 py-0.5 rounded">
                Immutable
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Showing raw unmodified records as uploaded. Dataset values cannot be modified in this stage.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={previewSearch}
                onChange={(e) => {
                  setPreviewSearch(e.target.value);
                  setPreviewPage(1);
                }}
                placeholder="Search preview rows..."
                className="pl-8 pr-3 py-1.5 bg-white border border-gray-200 rounded-lg text-xs text-gray-800 placeholder-gray-400 focus:outline-hidden focus:ring-1 focus:ring-blue-500 w-52"
              />
            </div>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPreviewPage(1);
              }}
              className="px-2.5 py-1.5 bg-white border border-gray-200 rounded-lg text-xs font-medium text-gray-700 focus:outline-hidden"
            >
              <option value={10}>10 / page</option>
              <option value={25}>25 / page</option>
              <option value={50}>50 / page</option>
            </select>
          </div>
        </div>

        <div className="table-container max-h-[440px] overflow-y-auto border-0 rounded-none">
          <table>
            <thead className="sticky top-0 bg-gray-50 border-b border-gray-200 z-10">
              <tr>
                <th className="w-14 text-center text-xs font-semibold text-gray-400 uppercase">#</th>
                {headers.map(h => {
                  const dtype = datatype_map[h] || 'object';
                  return (
                    <th key={h} className="text-xs font-semibold text-gray-700 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <span>{h}</span>
                        <span className="text-[10px] font-mono font-normal text-gray-400 bg-gray-100 px-1.5 py-0.2 rounded">
                          {dtype}
                        </span>
                      </div>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 font-mono text-xs">
              {paginatedRows.length === 0 ? (
                <tr>
                  <td colSpan={headers.length + 1} className="py-8 text-center text-gray-400">
                    No matching records found in preview.
                  </td>
                </tr>
              ) : (
                paginatedRows.map((row, rIdx) => (
                  <tr key={rIdx} className="hover:bg-gray-50/80 transition-colors">
                    <td className="text-center font-bold text-gray-400">
                      {startRecordIdx + rIdx}
                    </td>
                    {headers.map(h => {
                      const val = row[h];
                      const isNull = val === null || val === undefined || String(val).trim() === '' || String(val).toLowerCase() === 'nan';
                      return (
                        <td key={h} className="text-gray-800 whitespace-nowrap">
                          {isNull ? (
                            <span className="badge badge-warning text-[10px] py-0 px-1 font-semibold">
                              NULL
                            </span>
                          ) : (
                            String(val)
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        <div className="p-3.5 bg-gray-50 border-t border-gray-200 flex items-center justify-between text-xs text-gray-500">
          <span>
            Showing <strong className="text-gray-900">{startRecordIdx}</strong> to{' '}
            <strong className="text-gray-900">{endRecordIdx}</strong> of{' '}
            <strong className="text-gray-900">{filteredRecords.length.toLocaleString()}</strong> records
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={previewPage <= 1}
              onClick={() => setPreviewPage(p => Math.max(1, p - 1))}
              className="btn btn-secondary btn-sm px-2.5 py-1 text-xs disabled:opacity-40"
            >
              <ChevronLeft className="w-3.5 h-3.5 mr-1" />
              <span>Previous</span>
            </button>
            <span className="px-2 font-medium">
              Page {previewPage} of {totalPages}
            </span>
            <button
              type="button"
              disabled={previewPage >= totalPages}
              onClick={() => setPreviewPage(p => Math.min(totalPages, p + 1))}
              className="btn btn-secondary btn-sm px-2.5 py-1 text-xs disabled:opacity-40"
            >
              <span>Next</span>
              <ChevronRight className="w-3.5 h-3.5 ml-1" />
            </button>
          </div>
        </div>
      </div>

      {/* 3, 4, 5, 6, 7, 8. COMPREHENSIVE DATA DIAGNOSTICS */}
      <div className="card p-0 overflow-hidden border border-gray-200 shadow-sm">
        <div className="p-5 border-b border-gray-200 bg-white">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-indigo-600" />
                <span>Dataset Diagnostics & Analysis Findings</span>
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">
                Detailed informational breakdowns across schema, missing values, duplicates, format checks, anomalies, and statistics.
              </p>
            </div>

            {/* Diagnostic Tabs */}
            <div className="flex items-center bg-gray-100 p-1 rounded-lg text-xs font-semibold">
              <button
                type="button"
                onClick={() => setActiveDiagnosticTab('schema')}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  activeDiagnosticTab === 'schema' ? 'bg-white text-blue-600 shadow-xs' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Columns & Schema ({headers.length})
              </button>
              <button
                type="button"
                onClick={() => setActiveDiagnosticTab('missing')}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  activeDiagnosticTab === 'missing' ? 'bg-white text-blue-600 shadow-xs' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Missing Values ({total_missing_cells})
              </button>
              <button
                type="button"
                onClick={() => setActiveDiagnosticTab('duplicates')}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  activeDiagnosticTab === 'duplicates' ? 'bg-white text-blue-600 shadow-xs' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Duplicates ({duplicate_count})
              </button>
              <button
                type="button"
                onClick={() => setActiveDiagnosticTab('format')}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  activeDiagnosticTab === 'format' ? 'bg-white text-blue-600 shadow-xs' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Format Issues ({format_issues.length})
              </button>
              <button
                type="button"
                onClick={() => setActiveDiagnosticTab('anomalies')}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  activeDiagnosticTab === 'anomalies' ? 'bg-white text-blue-600 shadow-xs' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Anomalies ({anomalies.length})
              </button>
              <button
                type="button"
                onClick={() => setActiveDiagnosticTab('statistics')}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  activeDiagnosticTab === 'statistics' ? 'bg-white text-blue-600 shadow-xs' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Statistics ({columnMetrics.length})
              </button>
            </div>
          </div>
        </div>

        <div className="p-6">
          {/* TAB 1: COLUMN INFORMATION (Section 3) */}
          {activeDiagnosticTab === 'schema' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>Schema definition and basic completeness across all {headers.length} attributes.</span>
                <span className="font-semibold text-gray-700">Total Rows: {total_rows.toLocaleString()}</span>
              </div>
              <div className="table-container border border-gray-200 rounded-lg">
                <table>
                  <thead className="bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-600">
                    <tr>
                      <th>Column</th>
                      <th>Data Type</th>
                      <th>Non-Null</th>
                      <th>Null Count</th>
                      <th>Missing %</th>
                      <th>Unique Count</th>
                      <th>Completeness</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 text-xs font-mono">
                    {columnMetrics.map(col => (
                      <tr key={col.name} className="hover:bg-gray-50">
                        <td className="font-bold text-gray-900">{col.name}</td>
                        <td>
                          <span className="bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded text-[11px]">
                            {col.dtype}
                          </span>
                        </td>
                        <td className="text-gray-700">{col.nonNullCount.toLocaleString()}</td>
                        <td className={col.nullCount > 0 ? 'text-amber-600 font-bold' : 'text-gray-400'}>
                          {col.nullCount}
                        </td>
                        <td>
                          <div className="flex items-center gap-2">
                            <span className={col.missingPct > 0 ? 'text-amber-600 font-semibold' : 'text-gray-500'}>
                              {col.missingPct}%
                            </span>
                            <div className="w-16 bg-gray-100 rounded-full h-1.5 overflow-hidden">
                              <div
                                className={col.missingPct > 0 ? 'bg-amber-500 h-1.5' : 'bg-emerald-500 h-1.5'}
                                style={{ width: `${Math.min(100, col.missingPct)}%` }}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="text-gray-700">{col.uniqueCount.toLocaleString()}</td>
                        <td>
                          <span
                            className={`badge text-[10px] ${
                              col.missingPct === 0 ? 'badge-success' : col.missingPct < 5 ? 'badge-warning' : 'badge-error'
                            }`}
                          >
                            {col.missingPct === 0 ? '100% Complete' : `${(100 - col.missingPct).toFixed(1)}%`}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 2: MISSING VALUE INFORMATION (Section 4) */}
          {activeDiagnosticTab === 'missing' && (
            <div className="space-y-4">
              <div className="p-4 bg-amber-50/80 border border-amber-200 rounded-xl flex items-start gap-3 text-xs text-amber-900">
                <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-amber-900">
                    Informational Missing Value Report: {total_missing_cells} total missing cells detected
                  </p>
                  <p className="text-amber-700 mt-0.5">
                    Data is strictly observed here without modification. Mean, median, mode, or drop imputation strategies are executed during Stage 5 (AI Remediation).
                  </p>
                </div>
              </div>

              {missing_report.length === 0 ? (
                <div className="p-8 text-center bg-gray-50 rounded-xl border border-gray-200">
                  <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
                  <p className="text-sm font-bold text-gray-900">Zero Missing Values</p>
                  <p className="text-xs text-gray-500 mt-1">All columns are 100% populated with valid entries.</p>
                </div>
              ) : (
                <div className="table-container border border-gray-200 rounded-lg">
                  <table>
                    <thead className="bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-600">
                      <tr>
                        <th>Column</th>
                        <th>Missing Count</th>
                        <th>Missing %</th>
                        <th>Identified In Rows</th>
                        <th>Recommended Strategy (for Stage 5)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 text-xs font-mono">
                      {missing_report.map(m => (
                        <tr key={m.column} className="hover:bg-gray-50">
                          <td className="font-bold text-gray-900">{m.column}</td>
                          <td className="text-amber-600 font-bold">{m.null_count} missing</td>
                          <td className="text-gray-700 font-semibold">{m.missing_pct}%</td>
                          <td className="text-gray-500 text-[11px] max-w-xs truncate" title={m.null_rows?.join(', ')}>
                            {m.null_rows?.length > 10
                              ? `${m.null_rows.slice(0, 8).join(', ')}... (+${m.null_rows.length - 8} more)`
                              : m.null_rows?.join(', ') || 'N/A'}
                          </td>
                          <td className="text-gray-600">
                            {m.suggested_median !== null && m.suggested_median !== undefined ? (
                              <span className="text-indigo-600">Median Impute (~{m.suggested_median})</span>
                            ) : m.suggested_mode ? (
                              <span className="text-indigo-600">Mode Impute ("{m.suggested_mode}")</span>
                            ) : (
                              <span className="text-gray-400">Standard Fill</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: DUPLICATE INFORMATION (Section 5) */}
          {activeDiagnosticTab === 'duplicates' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl">
                  <span className="text-xs text-gray-500 font-medium">Total Rows</span>
                  <h4 className="text-xl font-bold text-gray-900 mt-1 font-mono">{total_rows.toLocaleString()}</h4>
                </div>
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl">
                  <span className="text-xs text-amber-700 font-medium">Duplicate Rows</span>
                  <h4 className="text-xl font-bold text-amber-900 mt-1 font-mono">{duplicate_count.toLocaleString()}</h4>
                </div>
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl">
                  <span className="text-xs text-blue-700 font-medium">Duplicate Percentage</span>
                  <h4 className="text-xl font-bold text-blue-900 mt-1 font-mono">
                    {((duplicate_count / (total_rows || 1)) * 100).toFixed(2)}%
                  </h4>
                </div>
                <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
                  <span className="text-xs text-emerald-700 font-medium">Unique Rows</span>
                  <h4 className="text-xl font-bold text-emerald-900 mt-1 font-mono">
                    {(total_rows - duplicate_count).toLocaleString()}
                  </h4>
                </div>
              </div>

              <div className="p-4 bg-blue-50/70 border border-blue-200 rounded-xl text-xs text-blue-900 flex items-start gap-3">
                <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <p>
                  Duplicate rows are identified for informational awareness. No rows are removed in Upload & Analyze. Automated deduplication is handled in Stage 5.
                </p>
              </div>

              {column_duplicates && column_duplicates.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase text-gray-500 mb-2">Column-Level Identifier Clashes</h4>
                  <div className="table-container border border-gray-200 rounded-lg">
                    <table>
                      <thead className="bg-gray-50 text-xs font-semibold text-gray-600">
                        <tr>
                          <th>Primary Identifier Column</th>
                          <th>Duplicate Occurrences</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody className="text-xs font-mono">
                        {column_duplicates.map((cd, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="font-bold text-gray-900">{cd.column}</td>
                            <td className="text-amber-600 font-bold">{cd.duplicate_count} clashes</td>
                            <td className="text-gray-500">Flagged for uniqueness validation</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: DATA FORMAT / VALIDATION INFORMATION (Section 6) */}
          {activeDiagnosticTab === 'format' && (
            <div className="space-y-4">
              <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl text-xs text-gray-600 flex items-start gap-3">
                <Info className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-gray-900">
                    Format & Validation Diagnostic Log: {format_issues.length} discrepancies detected
                  </p>
                  <p className="mt-0.5">
                    Scans verify phone patterns, email standards, currency characters, and categorical domain conformity without modifying the original records.
                  </p>
                </div>
              </div>

              {format_issues.length === 0 ? (
                <div className="p-8 text-center bg-gray-50 rounded-xl border border-gray-200">
                  <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
                  <p className="text-sm font-bold text-gray-900">All Formats Valid</p>
                  <p className="text-xs text-gray-500 mt-1">Zero format discrepancies or pattern validation errors detected.</p>
                </div>
              ) : (
                <div className="table-container border border-gray-200 rounded-lg max-h-[380px] overflow-y-auto">
                  <table>
                    <thead className="sticky top-0 bg-gray-50 text-xs font-semibold text-gray-600">
                      <tr>
                        <th>Row #</th>
                        <th>Column</th>
                        <th>Invalid Value Detected</th>
                        <th>Expected Format Rule</th>
                        <th>Diagnostic Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 text-xs font-mono">
                      {format_issues.map((issue, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="text-gray-400 font-bold">#{issue.row_index + 1}</td>
                          <td className="font-bold text-gray-900">{issue.column}</td>
                          <td className="text-rose-600 font-semibold bg-rose-50/50 px-2 py-0.5 rounded">
                            "{issue.invalid_value}"
                          </td>
                          <td className="text-gray-700">{issue.expected_format}</td>
                          <td className="text-indigo-600">
                            {issue.suggested_correction ? `Remediable to "${issue.suggested_correction}" in Stage 5` : 'Standardize format in Stage 5'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 5: DATA ANOMALY INFORMATION (Section 7) */}
          {activeDiagnosticTab === 'anomalies' && (
            <div className="space-y-4">
              <div className="p-4 bg-red-50/70 border border-red-200 rounded-xl text-xs text-red-900 flex items-start gap-3">
                <AlertTriangle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-red-900">
                    Anomaly Detection Summary: {anomalies.length} outliers flagged
                  </p>
                  <p className="text-red-700 mt-0.5">
                    Calculated using multi-model Isolation Forest & statistical boundary analysis. Detailed deep-dive inspection and record-level actions are preserved in Stage 4 (Anomaly Detection).
                  </p>
                </div>
              </div>

              {anomalies.length === 0 ? (
                <div className="p-8 text-center bg-gray-50 rounded-xl border border-gray-200">
                  <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
                  <p className="text-sm font-bold text-gray-900">Zero Outliers Detected</p>
                  <p className="text-xs text-gray-500 mt-1">Multi-model Isolation Forest analysis found no anomalous distributions.</p>
                </div>
              ) : (
                <div className="table-container border border-gray-200 rounded-lg max-h-[380px] overflow-y-auto">
                  <table>
                    <thead className="sticky top-0 bg-gray-50 text-xs font-semibold text-gray-600">
                      <tr>
                        <th>Record Row #</th>
                        <th>Primary Feature</th>
                        <th>Flagged Value</th>
                        <th>Confidence / Score</th>
                        <th>Explanation</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 text-xs font-mono">
                      {anomalies.map((anom, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="text-gray-400 font-bold">#{anom.row_index + 1}</td>
                          <td className="font-bold text-gray-900">{anom.column}</td>
                          <td className="text-red-600 font-semibold bg-red-50/50 px-2 py-0.5 rounded">
                            {String(anom.value)}
                          </td>
                          <td className="text-gray-700 font-semibold">
                            {typeof anom.anomaly_score === 'number'
                              ? `${(anom.anomaly_score * 100).toFixed(1)}%`
                              : String(anom.anomaly_score || 'High')}
                          </td>
                          <td className="text-gray-600 font-sans text-xs max-w-sm">
                            {anom.reason || 'Statistical outlier exceeding distribution bounds.'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 6: STATISTICAL INFORMATION (Section 8) */}
          {activeDiagnosticTab === 'statistics' && (
            <div className="space-y-6">
              <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl text-xs text-gray-600 flex items-start gap-3">
                <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                <p>
                  Descriptive summary statistics computed directly from raw uploaded records. Data remains 100% immutable during Stage 1.
                </p>
              </div>

              {/* Numerical Attributes Statistics */}
              <div>
                <h4 className="text-xs font-bold uppercase text-gray-500 mb-3 flex items-center gap-1.5">
                  <Hash className="w-3.5 h-3.5 text-blue-600" />
                  Numerical Attributes (Min, Max, Quartiles, Mean, Median, IQR)
                </h4>
                <div className="table-container border border-gray-200 rounded-lg">
                  <table>
                    <thead className="bg-gray-50 text-xs font-semibold text-gray-600">
                      <tr>
                        <th>Feature</th>
                        <th>Count</th>
                        <th>Mean</th>
                        <th>Median</th>
                        <th>Std Dev</th>
                        <th>Min</th>
                        <th>Q1 (25%)</th>
                        <th>Q3 (75%)</th>
                        <th>Max</th>
                        <th>IQR</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 text-xs font-mono">
                      {columnMetrics.filter(c => c.isNumeric && c.stats).length === 0 ? (
                        <tr>
                          <td colSpan={10} className="py-4 text-center text-gray-400">
                            No numeric columns available.
                          </td>
                        </tr>
                      ) : (
                        columnMetrics
                          .filter(c => c.isNumeric && c.stats)
                          .map(col => {
                            const s = col.stats;
                            return (
                              <tr key={col.name} className="hover:bg-gray-50">
                                <td className="font-bold text-gray-900">{col.name}</td>
                                <td className="text-gray-700">{s.count.toLocaleString()}</td>
                                <td className="text-blue-700 font-semibold">{s.mean}</td>
                                <td className="text-gray-900 font-semibold">{s.median}</td>
                                <td className="text-gray-600">{s.std}</td>
                                <td className="text-gray-700">{s.min}</td>
                                <td className="text-gray-500">{s.q1}</td>
                                <td className="text-gray-500">{s.q3}</td>
                                <td className="text-gray-700">{s.max}</td>
                                <td className="text-indigo-600 font-bold">{s.iqr}</td>
                              </tr>
                            );
                          })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Categorical Attributes Statistics */}
              <div>
                <h4 className="text-xs font-bold uppercase text-gray-500 mb-3 flex items-center gap-1.5">
                  <Columns className="w-3.5 h-3.5 text-indigo-600" />
                  Categorical & Text Attributes
                </h4>
                <div className="table-container border border-gray-200 rounded-lg">
                  <table>
                    <thead className="bg-gray-50 text-xs font-semibold text-gray-600">
                      <tr>
                        <th>Feature</th>
                        <th>Non-Null Count</th>
                        <th>Unique Values (Cardinality)</th>
                        <th>Most Frequent Value (Mode)</th>
                        <th>Top Value Frequency</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 text-xs font-mono">
                      {columnMetrics.filter(c => !c.isNumeric && c.stats).length === 0 ? (
                        <tr>
                          <td colSpan={5} className="py-4 text-center text-gray-400">
                            No categorical columns found.
                          </td>
                        </tr>
                      ) : (
                        columnMetrics
                          .filter(c => !c.isNumeric && c.stats)
                          .map(col => {
                            const s = col.stats;
                            return (
                              <tr key={col.name} className="hover:bg-gray-50">
                                <td className="font-bold text-gray-900">{col.name}</td>
                                <td className="text-gray-700">{s.count.toLocaleString()}</td>
                                <td className="text-indigo-600 font-semibold">{s.uniqueCount.toLocaleString()}</td>
                                <td className="text-gray-900 font-semibold">"{s.topVal}"</td>
                                <td className="text-gray-600">
                                  {s.topFreq} occurrences ({((s.topFreq / (s.count || 1)) * 100).toFixed(1)}%)
                                </td>
                              </tr>
                            );
                          })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 11. AI ANALYSIS & INSIGHTS (Purely Informational — ZERO automated remediation) */}
      <div className="space-y-6">
        <div className="card bg-gradient-to-r from-indigo-50/60 via-white to-blue-50/40 border-indigo-200 p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-5 h-5 text-indigo-600" />
            <h3 className="text-base font-bold text-gray-900">AI Diagnostic Observations & Insights</h3>
            <span className="badge badge-info text-[10px]">Informational</span>
          </div>
          <p className="text-xs text-gray-500 mb-5">
            Automated reasoning answering <em>"What did the analysis find?"</em> without mutating any dataset records.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {aiFindings.map((finding, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-xl border text-xs space-y-1 ${
                  finding.type === 'positive'
                    ? 'bg-emerald-50/60 border-emerald-200 text-emerald-950'
                    : finding.type === 'critical'
                    ? 'bg-rose-50/60 border-rose-200 text-rose-950'
                    : finding.type === 'warning'
                    ? 'bg-amber-50/60 border-amber-200 text-amber-950'
                    : 'bg-blue-50/60 border-blue-200 text-blue-950'
                }`}
              >
                <div className="flex items-center gap-1.5 font-bold">
                  {finding.type === 'positive' ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  ) : finding.type === 'critical' ? (
                    <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                  )}
                  <span>{finding.title}</span>
                </div>
                <p className="text-gray-600 leading-relaxed pt-0.5">{finding.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* SHAP Feature Contribution Explainability (Informational only) */}
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-600" />
              <h3 className="text-base font-bold text-gray-900">SHAP Feature Contribution Explainability</h3>
            </div>
            <span className="text-xs text-gray-400 font-medium">Variance & Feature Weight Analysis</span>
          </div>
          <ExplanationCard
            summary={
              shap_features.length > 0
                ? `SHAP feature importance identified '${shap_features[0].feature}' as the primary contributing metric to overall dataset variance.`
                : 'No numeric features available for SHAP tree explainer.'
            }
          />
          <SHAPChart features={shap_features} />
        </div>
      </div>
    </div>
  );
};

export default UnifiedAnalysisReport;
