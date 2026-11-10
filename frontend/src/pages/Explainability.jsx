import React, { useContext, useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { DatasetContext } from '../context/DatasetContext';
import { getXaiExplanations, explainRowWithLlm, getSavedDatasets } from '../services/xaiService';
import {
  BrainCircuit,
  Sparkles,
  AlertTriangle,
  AlertCircle,
  FileCode,
  ShieldAlert,
  Search,
  RefreshCw,
  X,
  HelpCircle,
  CheckCircle2,
  Cpu,
  Layers,
  FileText,
  Copy,
  Check,
  ListFilter,
  Columns,
  Grid,
  ChevronDown,
  ChevronUp,
  Wand2,
  Download,
  ArrowRight,
  Database,
  BarChart3,
  CheckSquare,
  ArrowLeft,
  Calendar,
  Shield
} from 'lucide-react';

const Explainability = () => {
  const { activeDatasetId, filename } = useContext(DatasetContext) || {};
  const location = useLocation();

  // ─── Dataset Selector State ───────────────────────────────────────────────
  const [savedDatasets, setSavedDatasets] = useState([]);
  const [loadingDatasets, setLoadingDatasets] = useState(false);
  const [selectedDatasetId, setSelectedDatasetId] = useState(null);
  const [selectedDatasetMeta, setSelectedDatasetMeta] = useState(null);

  // ─── XAI Analysis State ───────────────────────────────────────────────────
  const [explanations, setExplanations] = useState([]);
  const [groupedExplanations, setGroupedExplanations] = useState([]);
  const [masterReport, setMasterReport] = useState('');
  const [summary, setSummary] = useState({
    total_rows: 0,
    total_explanations: 0,
    ml_anomalies_count: 0,
    syntax_errors_count: 0,
    outliers_count: 0,
    total_error_groups: 0
  });

  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState('GROUPED');
  const [filterType, setFilterType] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [copiedMaster, setCopiedMaster] = useState(false);
  const [masterReportExpanded, setMasterReportExpanded] = useState(true);
  const [expandedRowGroups, setExpandedRowGroups] = useState({});

  // Modal State for Deep LLM Explanation
  const [selectedRow, setSelectedRow] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [llmResult, setLlmResult] = useState(null);
  const [loadingLlm, setLoadingLlm] = useState(false);

  // ─── Fetch saved datasets on mount ───────────────────────────────────────
  const fetchSavedDatasets = async () => {
    setLoadingDatasets(true);
    try {
      const res = await getSavedDatasets();
      const list = res.data || res || [];
      setSavedDatasets(Array.isArray(list) ? list : []);
    } catch (err) {
      console.error('Failed to fetch saved datasets:', err);
      setSavedDatasets([]);
    } finally {
      setLoadingDatasets(false);
    }
  };

  useEffect(() => {
    fetchSavedDatasets();
  }, []);

  // ─── Fetch XAI explanations for a specific dataset ───────────────────────
  const fetchExplanations = async (datasetId) => {
    setLoading(true);
    setExplanations([]);
    setGroupedExplanations([]);
    setMasterReport('');
    setSummary({ total_rows: 0, total_explanations: 0, ml_anomalies_count: 0, syntax_errors_count: 0, outliers_count: 0, total_error_groups: 0 });
    try {
      const res = await getXaiExplanations(datasetId);
      const data = res.data || res || {};
      setExplanations(data.explanations || []);
      setGroupedExplanations(data.grouped_explanations || []);
      setMasterReport(data.master_report || '');
      setSummary(data.summary || {});
    } catch (err) {
      console.error('Failed to fetch XAI explanations:', err);
    } finally {
      setLoading(false);
    }
  };

  // ─── Handle dataset selection ─────────────────────────────────────────────
  const handleSelectDataset = (ds) => {
    setSelectedDatasetId(ds.dataset_id || ds.id);
    setSelectedDatasetMeta(ds);
    setFilterType('ALL');
    setSearchQuery('');
    setExpandedRowGroups({});
    fetchExplanations(ds.dataset_id || ds.id);
  };

  const handleChangeDataset = () => {
    setSelectedDatasetId(null);
    setSelectedDatasetMeta(null);
    setExplanations([]);
    setGroupedExplanations([]);
    setMasterReport('');
    setSummary({ total_rows: 0, total_explanations: 0, ml_anomalies_count: 0, syntax_errors_count: 0, outliers_count: 0, total_error_groups: 0 });
  };

  useEffect(() => {
    if (location.state && location.state.column) {
      setSearchQuery(location.state.column);
    }
  }, [location.state]);

  const handleDeepExplainRow = async (item) => {
    setSelectedRow(item);
    setModalOpen(true);
    setLoadingLlm(true);
    setLlmResult(null);
    try {
      const res = await explainRowWithLlm({
        dataset_id: selectedDatasetId || activeDatasetId || 1,
        row_index: item.row_index,
        column_name: item.column_name,
        issue_type: item.issue_type,
        raw_value: item.raw_value
      });
      setLlmResult(res.data || res);
    } catch (err) {
      console.error('LLM Row explanation error:', err);
    } finally {
      setLoadingLlm(false);
    }
  };

  const handleCopyMasterReport = () => {
    if (!masterReport) return;
    navigator.clipboard.writeText(masterReport);
    setCopiedMaster(true);
    setTimeout(() => setCopiedMaster(false), 2000);
  };

  const toggleGroupRows = (groupId) => {
    setExpandedRowGroups(prev => ({ ...prev, [groupId]: !prev[groupId] }));
  };

  const filteredExplanations = explanations.filter((item) => {
    const matchesFilter = filterType === 'ALL' || item.issue_type === filterType;
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      !searchQuery ||
      item.column_name.toLowerCase().includes(q) ||
      String(item.row_index).includes(q) ||
      item.raw_value.toLowerCase().includes(q) ||
      item.plain_english_explanation.toLowerCase().includes(q);
    return matchesFilter && matchesSearch;
  });

  const filteredGroupedExplanations = groupedExplanations.filter((group) => {
    const matchesFilter = filterType === 'ALL' || group.issue_type === filterType;
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      !searchQuery ||
      group.group_title.toLowerCase().includes(q) ||
      group.affected_columns.some(col => col.toLowerCase().includes(q)) ||
      group.consolidated_plain_english.toLowerCase().includes(q);
    return matchesFilter && matchesSearch;
  });

  const getGroupCategoryConfig = (issueType) => {
    switch (issueType) {
      case 'ML_ANOMALY':
        return {
          gradient: 'from-purple-600 via-indigo-600 to-blue-600',
          badgeBg: 'bg-purple-100 text-purple-800 border-purple-200',
          iconBg: 'bg-purple-50 text-purple-600',
          boxBg: 'bg-purple-50/60 border-purple-100 text-purple-950',
          icon: Cpu,
          label: 'ML Model Anomaly'
        };
      case 'SYNTAX_ERROR':
        return {
          gradient: 'from-blue-600 via-cyan-600 to-teal-500',
          badgeBg: 'bg-blue-100 text-blue-800 border-blue-200',
          iconBg: 'bg-blue-50 text-blue-600',
          boxBg: 'bg-blue-50/60 border-blue-100 text-blue-950',
          icon: FileCode,
          label: 'Syntax Violation'
        };
      case 'MISSING_VALUE':
        return {
          gradient: 'from-amber-500 via-orange-500 to-amber-600',
          badgeBg: 'bg-amber-100 text-amber-800 border-amber-200',
          iconBg: 'bg-amber-50 text-amber-600',
          boxBg: 'bg-amber-50/60 border-amber-100 text-amber-950',
          icon: Grid,
          label: 'Missing Data'
        };
      default:
        return {
          gradient: 'from-rose-600 via-red-600 to-pink-600',
          badgeBg: 'bg-rose-100 text-rose-800 border-rose-200',
          iconBg: 'bg-rose-50 text-rose-600',
          boxBg: 'bg-rose-50/60 border-rose-100 text-rose-950',
          icon: ShieldAlert,
          label: 'Boundary Outlier'
        };
    }
  };

  // ─── DATASET SELECTOR PANEL ───────────────────────────────────────────────
  if (!selectedDatasetId) {
    return (
      <div className="space-y-6 max-w-7xl mx-auto pb-16">
        {/* Header */}
        <div className="relative overflow-hidden bg-white p-6 rounded-2xl border border-gray-200/80 shadow-sm">
          <div className="absolute top-0 right-0 -mt-8 -mr-8 w-48 h-48 bg-gradient-to-br from-blue-100/40 to-indigo-100/30 rounded-full blur-2xl pointer-events-none" />
          <div className="relative flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2.5 flex-wrap">
                <div className="p-2.5 bg-gradient-to-tr from-blue-600 to-indigo-600 text-white rounded-xl shadow-sm">
                  <BrainCircuit className="w-5 h-5" />
                </div>
                <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Explainable AI (XAI) Engine</h1>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700 border border-blue-200/60">
                  <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                  <span>Select a Saved Dataset to Analyze</span>
                </span>
              </div>
              <p className="text-sm text-gray-600 max-w-3xl leading-relaxed">
                Select one of your saved datasets below. The XAI engine will load the actual stored data and generate consolidated plain-English explanations from it.
              </p>
            </div>
            <button
              onClick={fetchSavedDatasets}
              disabled={loadingDatasets}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-semibold rounded-xl transition-all duration-200 flex items-center gap-2 shadow-2xs shrink-0"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingDatasets ? 'animate-spin' : ''}`} />
              <span>Refresh List</span>
            </button>
          </div>
        </div>

        {/* Saved Datasets Table */}
        <div className="bg-white rounded-2xl border border-gray-200/80 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-blue-50 text-blue-600 rounded-xl">
                <Database className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-gray-900">Saved Datasets</h3>
                <p className="text-xs text-gray-500">Choose a dataset to run the Explainable AI analysis on its actual stored data.</p>
              </div>
            </div>
            <span className="text-xs font-semibold text-gray-400 bg-gray-100 px-3 py-1 rounded-full">
              {savedDatasets.length} saved dataset{savedDatasets.length !== 1 ? 's' : ''}
            </span>
          </div>

          {loadingDatasets ? (
            <div className="p-16 text-center text-gray-500 text-sm">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-3" />
              <p className="font-semibold text-gray-800">Loading saved datasets...</p>
            </div>
          ) : savedDatasets.length === 0 ? (
            <div className="p-16 text-center">
              <Database className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <h3 className="text-base font-bold text-gray-900">No Saved Datasets Found</h3>
              <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
                Upload and analyze a dataset first using the Upload &amp; Analyze module. Once uploaded, it will appear here for XAI analysis.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-gray-700">
                <thead>
                  <tr className="border-b border-gray-100 text-xs font-semibold text-gray-500 uppercase tracking-wider bg-gray-50/60">
                    <th className="py-3.5 px-5">Dataset / Filename</th>
                    <th className="py-3.5 px-5">Rows</th>
                    <th className="py-3.5 px-5">Columns</th>
                    <th className="py-3.5 px-5">Quality Score</th>
                    <th className="py-3.5 px-5">Status</th>
                    <th className="py-3.5 px-5">Saved At</th>
                    <th className="py-3.5 px-5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {savedDatasets.map((ds) => {
                    const dsId = ds.dataset_id || ds.id;
                    const score = ds.quality_score || 0;
                    const scoreColor =
                      score >= 90 ? 'text-emerald-700 bg-emerald-50 border-emerald-200' :
                      score >= 70 ? 'text-amber-700 bg-amber-50 border-amber-200' :
                      'text-red-700 bg-red-50 border-red-200';

                    return (
                      <tr
                        key={dsId}
                        className="hover:bg-blue-50/30 transition-colors cursor-pointer group"
                        onClick={() => handleSelectDataset(ds)}
                      >
                        <td className="py-4 px-5">
                          <div className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600 shrink-0 group-hover:bg-blue-100 transition-colors">
                              <FileText className="w-4 h-4" />
                            </div>
                            <div>
                              <p className="font-semibold text-gray-900 text-xs">{ds.filename || `Dataset #${dsId}`}</p>
                              <p className="text-[11px] text-gray-400 font-mono">ID #{dsId}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-5">
                          <span className="font-mono text-xs font-bold text-gray-800">
                            {(ds.total_rows || 0).toLocaleString()}
                          </span>
                        </td>
                        <td className="py-4 px-5">
                          <span className="font-mono text-xs font-bold text-gray-800">
                            {ds.total_cols || ds.total_columns || '—'}
                          </span>
                        </td>
                        <td className="py-4 px-5">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold border ${scoreColor}`}>
                            {score}%
                          </span>
                        </td>
                        <td className="py-4 px-5">
                          <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full">
                            <Shield className="w-3 h-3" />
                            {ds.status || 'PROFILED'}
                          </span>
                        </td>
                        <td className="py-4 px-5 text-xs text-gray-500">
                          {ds.created_at ? new Date(ds.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : '—'}
                        </td>
                        <td className="py-4 px-5 text-right">
                          <button
                            onClick={(e) => { e.stopPropagation(); handleSelectDataset(ds); }}
                            className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-xl transition-colors shadow-sm"
                          >
                            <BrainCircuit className="w-3.5 h-3.5" />
                            <span>Analyze with XAI</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ─── XAI ANALYSIS VIEW (unchanged logic, now driven by selectedDatasetId) ─
  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header Banner */}
      <div className="relative overflow-hidden bg-white p-6 rounded-2xl border border-gray-200/80 shadow-sm">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-48 h-48 bg-gradient-to-br from-blue-100/40 to-indigo-100/30 rounded-full blur-2xl pointer-events-none" />
        
        <div className="relative flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5 flex-wrap">
              <div className="p-2.5 bg-gradient-to-tr from-blue-600 to-indigo-600 text-white rounded-xl shadow-sm">
                <BrainCircuit className="w-5 h-5" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Explainable AI (XAI) Engine</h1>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700 border border-blue-200/60">
                <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                <span>Consolidated Root Cause Explainer</span>
              </span>
            </div>
            {/* Active Dataset Breadcrumb */}
            <div className="flex items-center gap-2 text-xs">
              <span className="text-gray-400">Analyzing:</span>
              <span className="inline-flex items-center gap-1.5 font-semibold text-gray-800 bg-gray-100 px-2.5 py-1 rounded-lg border border-gray-200">
                <FileText className="w-3.5 h-3.5 text-blue-600" />
                {selectedDatasetMeta?.filename || `Dataset #${selectedDatasetId}`}
              </span>
              <span className="text-gray-400 hidden sm:inline">
                {selectedDatasetMeta?.total_rows ? `• ${selectedDatasetMeta.total_rows.toLocaleString()} rows` : ''}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={handleChangeDataset}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-semibold rounded-xl transition-all duration-200 flex items-center gap-2 shadow-2xs"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Change Dataset</span>
            </button>
            <button
              onClick={() => fetchExplanations(selectedDatasetId)}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-semibold rounded-xl transition-all duration-200 flex items-center gap-2 shadow-2xs"
              disabled={loading}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Re-Analyze Dataset</span>
            </button>
          </div>
        </div>
      </div>

      {/* Summary KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="group relative bg-white p-5 rounded-2xl border border-gray-200/80 shadow-2xs hover:shadow-md hover:-translate-y-0.5 transition-all duration-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Root Cause Groups</p>
              <h3 className="text-3xl font-extrabold text-blue-600 mt-1">{summary.total_error_groups || groupedExplanations.length}</h3>
              <p className="text-xs text-gray-500 mt-1 font-medium">Consolidated error clusters</p>
            </div>
            <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Layers className="w-6 h-6" />
            </div>
          </div>
        </div>

        <div className="group relative bg-white p-5 rounded-2xl border border-gray-200/80 shadow-2xs hover:shadow-md hover:-translate-y-0.5 transition-all duration-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Total Affected Rows</p>
              <h3 className="text-3xl font-extrabold text-gray-900 mt-1">{summary.total_explanations || explanations.length}</h3>
              <p className="text-xs text-gray-500 mt-1 font-medium">Across {summary.total_rows || 0} dataset records</p>
            </div>
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Grid className="w-6 h-6" />
            </div>
          </div>
        </div>

        <div className="group relative bg-white p-5 rounded-2xl border border-gray-200/80 shadow-2xs hover:shadow-md hover:-translate-y-0.5 transition-all duration-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">ML Model Anomalies</p>
              <h3 className="text-3xl font-extrabold text-purple-600 mt-1">{summary.ml_anomalies_count || 0}</h3>
              <p className="text-xs text-gray-500 mt-1 font-medium">Isolation Forest / Z-score</p>
            </div>
            <div className="w-12 h-12 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <Cpu className="w-6 h-6" />
            </div>
          </div>
        </div>

        <div className="group relative bg-white p-5 rounded-2xl border border-gray-200/80 shadow-2xs hover:shadow-md hover:-translate-y-0.5 transition-all duration-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Syntax &amp; Outliers</p>
              <h3 className="text-3xl font-extrabold text-amber-600 mt-1">
                {(summary.syntax_errors_count || 0) + (summary.outliers_count || 0)}
              </h3>
              <p className="text-xs text-gray-500 mt-1 font-medium">Regex &amp; boundary violations</p>
            </div>
            <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center group-hover:scale-105 transition-transform">
              <FileCode className="w-6 h-6" />
            </div>
          </div>
        </div>
      </div>

      {/* Main Control Strip (View Switcher + Filter Tabs + Search) */}
      <div className="bg-white p-4 rounded-2xl border border-gray-200/80 shadow-2xs flex flex-col lg:flex-row items-center justify-between gap-4">
        {/* View Switcher Buttons */}
        <div className="flex items-center p-1 bg-gray-100/80 rounded-xl w-full lg:w-auto">
          <button
            onClick={() => setViewMode('GROUPED')}
            className={`flex-1 lg:flex-initial flex items-center justify-center gap-2 px-5 py-2 rounded-lg text-xs font-bold transition-all duration-200 ${
              viewMode === 'GROUPED'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Consolidated Grouped Report View</span>
          </button>
          <button
            onClick={() => setViewMode('ROW_BY_ROW')}
            className={`flex-1 lg:flex-initial flex items-center justify-center gap-2 px-5 py-2 rounded-lg text-xs font-bold transition-all duration-200 ${
              viewMode === 'ROW_BY_ROW'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <ListFilter className="w-4 h-4" />
            <span>Row-by-Row View</span>
          </button>
        </div>

        {/* Filter Category Tabs & Search */}
        <div className="flex flex-col sm:flex-row items-center gap-3 w-full lg:w-auto">
          <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
            {[
              { id: 'ALL', label: 'All Issues' },
              { id: 'MISSING_VALUE', label: 'Missing Values' },
              { id: 'ML_ANOMALY', label: 'ML Anomalies' },
              { id: 'SYNTAX_ERROR', label: 'Syntax Errors' },
              { id: 'OUTLIER', label: 'Outliers' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setFilterType(tab.id)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 ${
                  filterType === tab.id
                    ? 'bg-gray-900 text-white font-semibold shadow-2xs'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="relative w-full sm:w-56">
            <Search className="w-3.5 h-3.5 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search columns or issues..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3.5 py-1.5 text-xs rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 bg-gray-50/50"
            />
          </div>
        </div>
      </div>

      {/* CONSOLIDATED GROUPED REPORT VIEW */}
      {viewMode === 'GROUPED' && (
        <div className="space-y-6">
          {/* Master Executive Summary Banner */}
          {masterReport && (
            <div className="relative overflow-hidden bg-slate-900 text-slate-100 rounded-2xl border border-slate-800 shadow-lg">
              <div className="h-1.5 w-full bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500" />
              
              <div className="p-6 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 bg-blue-500/10 text-blue-400 rounded-xl border border-blue-500/20">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-white tracking-tight">
                        Executive Explainable AI Master Report Summary
                      </h3>
                      <p className="text-xs text-slate-400">
                        Synthesized dataset-wide quality risk audit &amp; master remediation guidelines
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => setMasterReportExpanded(!masterReportExpanded)}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 border border-slate-700"
                    >
                      {masterReportExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      <span>{masterReportExpanded ? 'Collapse Report' : 'Expand Master Report'}</span>
                    </button>

                    <button
                      onClick={handleCopyMasterReport}
                      className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 shadow-xs"
                    >
                      {copiedMaster ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedMaster ? 'Copied Report!' : 'Copy Executive Text Report'}</span>
                    </button>
                  </div>
                </div>

                {masterReportExpanded && (
                  <div className="bg-slate-950/80 p-5 rounded-xl border border-slate-800/80 font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap max-h-80 overflow-y-auto custom-scrollbar">
                    {masterReport}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Grouped Root Cause Cards Grid */}
          {loading ? (
            <div className="p-16 text-center text-gray-500 text-sm bg-white rounded-2xl border border-gray-200/80 shadow-2xs">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-3" />
              <p className="font-semibold text-gray-800">Consolidating Dataset Root Cause Explanations...</p>
              <p className="text-xs text-gray-400 mt-1">Grouping anomalies across columns &amp; synthesizing plain-English narratives</p>
            </div>
          ) : filteredGroupedExplanations.length === 0 ? (
            <div className="p-16 text-center bg-white rounded-2xl border border-gray-200/80 shadow-2xs">
              <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
              <h3 className="text-base font-bold text-gray-900">No Consolidated Error Groups Flagged</h3>
              <p className="text-xs text-gray-500 mt-1">All columns match clean data quality rules for this filter category.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {filteredGroupedExplanations.map((group) => {
                const config = getGroupCategoryConfig(group.issue_type);
                const IconComp = config.icon;
                const isRowsExpanded = expandedRowGroups[group.group_id] || false;
                const visibleRows = isRowsExpanded ? group.affected_row_indexes : group.affected_row_indexes.slice(0, 12);
                const hasMoreRows = group.affected_row_indexes.length > 12;

                return (
                  <div
                    key={group.group_id}
                    className="relative bg-white rounded-2xl border border-gray-200/90 shadow-sm overflow-hidden hover:shadow-md transition-all duration-200"
                  >
                    {/* Color-Coded Category Top Strip */}
                    <div className={`h-1.5 w-full bg-gradient-to-r ${config.gradient}`} />

                    <div className="p-6 space-y-5">
                      {/* Group Header */}
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-gray-100">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-extrabold text-sm ${config.iconBg} shadow-2xs`}>
                            #{group.group_id}
                          </div>
                          <div>
                            <h3 className="text-base font-bold text-gray-900 leading-snug">{group.group_title}</h3>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className="text-xs font-semibold text-gray-500">{group.issue_category}</span>
                              <span className="text-gray-300">•</span>
                              <span className="text-xs text-gray-500 font-medium">Shared Root Cause Group</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200/70 shadow-2xs">
                            {group.total_affected_rows} Affected Instances
                          </span>
                          <span className={`px-3 py-1 rounded-full text-xs font-bold border shadow-2xs ${config.badgeBg}`}>
                            {group.issue_type}
                          </span>
                        </div>
                      </div>

                      {/* Affected Columns List */}
                      <div className="flex items-center gap-2 flex-wrap text-xs bg-gray-50/80 p-3.5 rounded-xl border border-gray-200/60">
                        <span className="font-bold text-gray-700 flex items-center gap-1.5 mr-1">
                          <Columns className="w-4 h-4 text-blue-600" />
                          <span>Affected Column(s):</span>
                        </span>
                        {group.affected_columns.map((col, cIdx) => (
                          <span
                            key={cIdx}
                            className="bg-white text-blue-900 px-3 py-1 rounded-lg font-mono font-bold text-xs border border-blue-200/80 shadow-2xs hover:border-blue-400 transition-colors"
                          >
                            {col}
                          </span>
                        ))}
                      </div>

                      {/* Consolidated Plain-English Explanation Box */}
                      <div className={`p-5 rounded-2xl border space-y-2 ${config.boxBg}`}>
                        <div className="flex items-center gap-2 font-bold text-xs uppercase tracking-wider text-blue-900">
                          <Sparkles className="w-4 h-4 text-blue-600" />
                          <span>Consolidated Plain-English AI Explanation:</span>
                        </div>
                        <p className="text-xs text-gray-900 leading-relaxed pt-0.5">
                          {group.consolidated_plain_english}
                        </p>
                      </div>

                      {/* Technical Root Cause & Business Risk Grid */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                        <div className="p-4 bg-gray-50/80 rounded-xl border border-gray-200/70 space-y-1.5">
                          <span className="font-bold text-gray-900 flex items-center gap-1.5">
                            <Database className="w-3.5 h-3.5 text-gray-600" />
                            <span>Technical Root Cause Diagnosis:</span>
                          </span>
                          <p className="text-gray-600 leading-relaxed">{group.technical_root_cause}</p>
                        </div>

                        <div className="p-4 bg-rose-50/60 rounded-xl border border-rose-200/60 space-y-1.5">
                          <span className="font-bold text-rose-900 flex items-center gap-1.5">
                            <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
                            <span>Business &amp; Pipeline Risk:</span>
                          </span>
                          <p className="text-rose-950 leading-relaxed">{group.business_impact}</p>
                        </div>
                      </div>

                      {/* Affected Dataset Rows List (Collapsible) */}
                      <div className="space-y-2 text-xs pt-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-gray-700 flex items-center gap-1.5">
                            <Grid className="w-3.5 h-3.5 text-gray-500" />
                            <span>Affected Dataset Rows ({group.affected_row_indexes.length} rows):</span>
                          </span>

                          {hasMoreRows && (
                            <button
                              onClick={() => toggleGroupRows(group.group_id)}
                              className="text-xs text-blue-600 hover:text-blue-800 font-bold flex items-center gap-1 transition-colors"
                            >
                              <span>{isRowsExpanded ? 'Show Less' : `+${group.affected_row_indexes.length - 12} More Rows`}</span>
                              {isRowsExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                            </button>
                          )}
                        </div>

                        <div className="flex items-center gap-1.5 flex-wrap p-3 bg-gray-50/80 rounded-xl border border-gray-200/60 font-mono text-xs">
                          {visibleRows.map((rIdx) => (
                            <span
                              key={rIdx}
                              className="bg-white text-gray-700 px-2.5 py-1 rounded-md border border-gray-200 shadow-2xs font-semibold"
                            >
                              Row #{rIdx}
                            </span>
                          ))}
                        </div>
                      </div>

                      {/* Consolidated Remediation Strategy Footer Bar */}
                      <div className="pt-4 border-t border-gray-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-xs">
                        <div className="flex items-center gap-2">
                          <span className="p-1.5 bg-emerald-100 text-emerald-700 rounded-lg">
                            <Wand2 className="w-4 h-4" />
                          </span>
                          <span className="text-gray-700">
                            Recommended AI Strategy: <strong className="text-emerald-700 font-bold">{group.consolidated_ai_remediation}</strong>
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ROW-BY-ROW VIEW */}
      {viewMode === 'ROW_BY_ROW' && (
        <div className="space-y-4">
          {loading ? (
            <div className="p-16 text-center text-gray-500 text-sm bg-white rounded-2xl border border-gray-200/80 shadow-2xs">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-3" />
              <p className="font-semibold text-gray-800">Running Row-by-Row Explainable AI Pass...</p>
            </div>
          ) : filteredExplanations.length === 0 ? (
            <div className="p-16 text-center bg-white rounded-2xl border border-gray-200/80 shadow-2xs">
              <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
              <h3 className="text-base font-bold text-gray-900">No Flagged Issues Found</h3>
              <p className="text-xs text-gray-500 mt-1">No anomalies match the selected filter criteria for this dataset.</p>
            </div>
          ) : (
            filteredExplanations.map((item) => (
              <div
                key={item.id}
                className="bg-white rounded-2xl border border-gray-200/80 shadow-2xs overflow-hidden hover:border-blue-300 transition-all p-6 space-y-4"
              >
                {/* Card Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-3.5 border-b border-gray-100">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-bold font-mono bg-gray-100 text-gray-900 px-3 py-1.5 rounded-lg border border-gray-200">
                      Row #{item.row_index}
                    </span>
                    <div>
                      <h4 className="text-sm font-bold text-gray-900">
                        Column: <span className="text-blue-600 font-mono">{item.column_name}</span>
                      </h4>
                      <p className="text-xs text-gray-500">{item.issue_category}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold font-mono border ${
                      item.issue_type === 'ML_ANOMALY'
                        ? 'bg-purple-50 text-purple-700 border-purple-200'
                        : item.issue_type === 'SYNTAX_ERROR'
                        ? 'bg-amber-50 text-amber-700 border-amber-200'
                        : 'bg-rose-50 text-rose-700 border-rose-200'
                    }`}>
                      {item.issue_type}
                    </span>

                    <span className={`px-2.5 py-0.5 rounded-md text-xs font-extrabold ${
                      item.severity === 'CRITICAL'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-orange-100 text-orange-800'
                    }`}>
                      {item.severity}
                    </span>
                  </div>
                </div>

                {/* Value Comparison Strip */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 bg-gray-50/80 p-4 rounded-xl text-xs border border-gray-200/60">
                  <div>
                    <span className="text-gray-400 font-bold uppercase text-[10px] tracking-wider block">Raw Recorded Entry:</span>
                    <span className="font-mono font-bold text-rose-600 mt-1 block text-sm">{item.raw_value}</span>
                  </div>
                  <div>
                    <span className="text-gray-400 font-bold uppercase text-[10px] tracking-wider block">Expected Format / Constraint:</span>
                    <span className="font-mono text-emerald-700 font-bold mt-1 block text-sm">{item.expected_format}</span>
                  </div>
                </div>

                {/* Explanations Section */}
                <div className="space-y-3 text-xs">
                  <div className="p-4 bg-blue-50/70 rounded-xl border border-blue-100 space-y-1">
                    <div className="flex items-center gap-1.5 text-blue-900 font-bold">
                      <Sparkles className="w-4 h-4 text-blue-600" />
                      <span>Plain English Explanation:</span>
                    </div>
                    <p className="text-blue-950 leading-relaxed pt-0.5">{item.plain_english_explanation}</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="p-3.5 bg-gray-50/80 rounded-xl border border-gray-200/70 space-y-1">
                      <span className="font-bold text-gray-900 block">Why ML Model Flagged This Row:</span>
                      <p className="text-gray-600 leading-relaxed">{item.why_flagged_ml}</p>
                    </div>
                    <div className="p-3.5 bg-gray-50/80 rounded-xl border border-gray-200/70 space-y-1">
                      <span className="font-bold text-gray-900 block">Why Syntax Error Occurred:</span>
                      <p className="text-gray-600 leading-relaxed">{item.why_flagged_syntax}</p>
                    </div>
                  </div>
                </div>

                {/* Card Footer Actions */}
                <div className="flex items-center justify-between pt-3 border-t border-gray-100 text-xs">
                  <span className="text-gray-600 font-medium">
                    Suggested Fix: <strong className="text-gray-900 font-bold">{item.ai_recommendation}</strong>
                  </span>

                  <button
                    onClick={() => handleDeepExplainRow(item)}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors flex items-center gap-1.5 shadow-2xs"
                  >
                    <BrainCircuit className="w-3.5 h-3.5" />
                    <span>Deep Explain with LLM</span>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Interactive LLM Deep Explain Modal */}
      {modalOpen && selectedRow && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full flex flex-col max-h-[85vh] overflow-hidden border border-gray-200">
            {/* Header */}
            <div className="p-5 border-b border-gray-200 flex items-center justify-between bg-gray-50/80">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-blue-100 text-blue-600 rounded-xl">
                  <BrainCircuit className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-gray-900">
                  LLM Deep-Dive Analysis for Row #{selectedRow.row_index}
                </h3>
              </div>
              <button
                onClick={() => setModalOpen(false)}
                className="text-gray-400 hover:text-gray-600 p-1.5 rounded-lg hover:bg-gray-200/60 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Body */}
            <div className="p-6 overflow-y-auto space-y-4 text-xs">
              <div className="flex items-center gap-2.5 p-3.5 bg-blue-50 text-blue-800 rounded-xl border border-blue-100">
                <HelpCircle className="w-4 h-4 text-blue-600 shrink-0" />
                <span className="font-medium">
                  Querying Generative LLM agent for context-aware root cause diagnosis...
                </span>
              </div>

              {loadingLlm ? (
                <div className="p-10 text-center text-gray-500 space-y-3">
                  <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto" />
                  <p className="font-bold text-gray-800">Synthesizing multi-layer LLM explainability report...</p>
                </div>
              ) : llmResult ? (
                <div className="space-y-3">
                  <h4 className="font-bold text-gray-900 text-sm">{llmResult.title}</h4>
                  <div className="p-5 bg-slate-900 text-slate-100 rounded-xl font-mono leading-relaxed whitespace-pre-wrap text-xs shadow-inner">
                    {llmResult.plain_english_llm_explanation}
                  </div>
                </div>
              ) : (
                <p className="text-gray-500">Failed to load LLM response.</p>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-gray-200 flex justify-end bg-gray-50/80">
              <button
                onClick={() => setModalOpen(false)}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold rounded-xl text-xs transition-colors"
              >
                Close Explanation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Explainability;
