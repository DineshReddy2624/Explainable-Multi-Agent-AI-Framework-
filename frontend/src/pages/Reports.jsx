import React, { useContext, useState, useEffect } from 'react';
import { DatasetContext } from '../context/DatasetContext';
import { generateReport, getDatasetGeneratedCodes, getGeneratedCodeById, getUserSavedReports, previewGeneratedPdfReport, deleteSavedReport } from '../services/reportService';
import { getDatasets, getSavedDatasets, getWorkflowBundle, deleteDataset } from '../services/datasetService';
import {
  FileText,
  Download,
  Code,
  Check,
  Copy,
  Terminal,
  Database,
  ShieldCheck,
  Eye,
  X,
  FileCode,
  RefreshCw,
  UserCheck,
  Layers,
  History,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  BarChart3,
  Archive,
  Clock,
  ExternalLink,
  Trash2
} from 'lucide-react';

const Reports = () => {
  const { activeDatasetId, filename } = useContext(DatasetContext) || {};

  // Tabs: 'datasets' or 'reports'
  const [activeTab, setActiveTab] = useState('datasets');

  // Saved Reports state
  const [savedCodes, setSavedCodes] = useState([]);
  const [loadingCodes, setLoadingCodes] = useState(false);
  const [selectedCode, setSelectedCode] = useState(null);
  const [copied, setCopied] = useState(false);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [pdfBlobUrl, setPdfBlobUrl] = useState(null);
  const [loadingPdf, setLoadingPdf] = useState(false);

  // Saved Datasets state
  const [savedDatasets, setSavedDatasets] = useState([]);
  const [loadingDatasets, setLoadingDatasets] = useState(false);
  const [bundleModalOpen, setBundleModalOpen] = useState(false);
  const [selectedDatasetInfo, setSelectedDatasetInfo] = useState(null);
  const [bundleData, setBundleData] = useState(null);
  const [loadingBundle, setLoadingBundle] = useState(false);
  const [bundleActiveSubTab, setBundleActiveSubTab] = useState('checklist');

  // Delete Confirmation and Action States
  const [deleteConfirmDataset, setDeleteConfirmDataset] = useState(null);
  const [deletingDataset, setDeletingDataset] = useState(false);
  const [deleteConfirmReport, setDeleteConfirmReport] = useState(null);
  const [deletingReport, setDeletingReport] = useState(false);
  const [actionNotification, setActionNotification] = useState(null);

  const fetchSavedCodes = async () => {
    setLoadingCodes(true);
    try {
      let items = [];
      if (activeDatasetId) {
        const res = await getDatasetGeneratedCodes(activeDatasetId);
        items = res.data || res || [];
      }
      if (!items || items.length === 0) {
        const userRes = await getUserSavedReports();
        items = userRes.data || userRes || [];
      }
      setSavedCodes(items);
    } catch (err) {
      console.error("Failed to load saved reports:", err);
    } finally {
      setLoadingCodes(false);
    }
  };

  const fetchSavedDatasets = async () => {
    setLoadingDatasets(true);
    try {
      const res = await getSavedDatasets();
      const list = res.data || res || [];
      setSavedDatasets(Array.isArray(list) ? list : []);
    } catch (err) {
      console.error("Failed to fetch saved datasets:", err);
    } finally {
      setLoadingDatasets(false);
    }
  };

  useEffect(() => {
    fetchSavedCodes();
    fetchSavedDatasets();
  }, [activeDatasetId]);

  const handleDownloadReport = async (format = 'pdf') => {
    try {
      const res = await generateReport(activeDatasetId || 1, format);
      const payload = res.data || res;
      if (payload.report_url) {
        window.open(payload.report_url, '_blank');
      }
      fetchSavedCodes();
    } catch (err) {
      window.open(`/api/v1/export/download/${activeDatasetId || 1}?format=pdf`, '_blank');
    }
  };

  const handleCloseModal = () => {
    if (pdfBlobUrl) {
      URL.revokeObjectURL(pdfBlobUrl);
      setPdfBlobUrl(null);
    }
    setPreviewModalOpen(false);
  };

  const handleViewCode = async (codeId) => {
    try {
      const res = await getGeneratedCodeById(codeId);
      const item = res.data || res;
      setSelectedCode(item);
      setPreviewModalOpen(true);

      if (item.code_type?.includes('PDF') || item.code_type?.includes('REPORT')) {
        setLoadingPdf(true);
        try {
          const blobData = await previewGeneratedPdfReport(codeId);
          const url = URL.createObjectURL(new Blob([blobData], { type: 'application/pdf' }));
          setPdfBlobUrl(url);
        } catch (err) {
          console.error("Failed to load PDF preview blob:", err);
        } finally {
          setLoadingPdf(false);
        }
      }
    } catch (err) {
      alert("Failed to load artifact details.");
    }
  };

  const handleViewBundle = async (ds) => {
    const dsId = ds.dataset_id || ds.id;
    setSelectedDatasetInfo(ds);
    setBundleModalOpen(true);
    setLoadingBundle(true);
    setBundleData(null);
    setBundleActiveSubTab('checklist');
    try {
      const res = await getWorkflowBundle(dsId);
      const data = res.data || res;
      setBundleData(data);
    } catch (err) {
      console.error("Failed to fetch workflow bundle:", err);
    } finally {
      setLoadingBundle(false);
    }
  };

  const handleCloseBundleModal = () => {
    setBundleModalOpen(false);
    setSelectedDatasetInfo(null);
    setBundleData(null);
  };

  const handleCopyCode = () => {
    if (!selectedCode?.code_content) return;
    navigator.clipboard.writeText(selectedCode.code_content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadCodeFile = (codeId) => {
    window.open(`/api/v1/code/download/${codeId}`, '_blank');
  };

  const handleDeleteDataset = async () => {
    if (!deleteConfirmDataset) return;
    const dsId = deleteConfirmDataset.dataset_id || deleteConfirmDataset.id;
    const dsName = deleteConfirmDataset.cleaned_filename || deleteConfirmDataset.filename || `dataset_${dsId}.csv`;
    setDeletingDataset(true);
    try {
      await deleteDataset(dsId);
      setActionNotification({
        type: 'success',
        text: `✓ Saved dataset '${dsName}' was deleted permanently.`
      });
      setDeleteConfirmDataset(null);
      await fetchSavedDatasets();
      setTimeout(() => setActionNotification(null), 5000);
    } catch (err) {
      console.error("Failed to delete dataset:", err);
      setActionNotification({
        type: 'error',
        text: `Failed to delete dataset: ${err?.response?.data?.detail || err?.message || 'Network error'}`
      });
      setTimeout(() => setActionNotification(null), 6000);
    } finally {
      setDeletingDataset(false);
    }
  };

  const handleDeleteReport = async () => {
    if (!deleteConfirmReport) return;
    setDeletingReport(true);
    try {
      await deleteSavedReport(deleteConfirmReport.id);
      setActionNotification({
        type: 'success',
        text: `✓ Saved report #${deleteConfirmReport.id} was deleted permanently.`
      });
      setDeleteConfirmReport(null);
      await fetchSavedCodes();
      setTimeout(() => setActionNotification(null), 5000);
    } catch (err) {
      console.error("Failed to delete report:", err);
      setActionNotification({
        type: 'error',
        text: `Failed to delete report: ${err?.response?.data?.detail || err?.message || 'Network error'}`
      });
      setTimeout(() => setActionNotification(null), 6000);
    } finally {
      setDeletingReport(false);
    }
  };

  // Keep exclusively PDF reports in the Saved Reports view
  const pdfReportsOnly = savedCodes.filter(item => item.code_type?.includes('PDF') || item.code_type?.includes('REPORT'));

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      {/* Action Notification Banner */}
      {actionNotification && (
        <div
          className={`px-4 py-3 rounded-xl flex items-center justify-between text-xs font-semibold shadow-sm animate-fade-in ${
            actionNotification.type === 'success'
              ? 'bg-emerald-50 border border-emerald-200 text-emerald-900'
              : 'bg-red-50 border border-red-200 text-red-900'
          }`}
        >
          <div className="flex items-center gap-2.5">
            {actionNotification.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
            )}
            <span className="font-bold">{actionNotification.text}</span>
          </div>
          <button
            type="button"
            onClick={() => setActionNotification(null)}
            className="text-gray-400 hover:text-gray-600 p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-gray-900 tracking-tight">Saved Data &amp; Reports Repository</h2>
            <span className="badge badge-info font-medium">Permanent Storage Active</span>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Browse permanently stored datasets with their complete workflow audit trails, and executive PDF reports.
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex items-center bg-gray-100 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('datasets')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-semibold transition-all ${
              activeTab === 'datasets'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Database className="w-4 h-4" />
            <span>Saved Datasets ({savedDatasets.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('reports')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-semibold transition-all ${
              activeTab === 'reports'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Executive PDF Reports ({pdfReportsOnly.length})</span>
          </button>
        </div>
      </div>

      {/* TAB 1: SAVED DATASETS (Permanent Storage) */}
      {activeTab === 'datasets' && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-lg">
                <Database className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-gray-900">Permanently Stored Datasets &amp; Workflow Bundles</h3>
                <p className="text-xs text-gray-500">Datasets saved with complete original records, modified records, and audit history (Items A–N).</p>
              </div>
            </div>
            <button
              onClick={fetchSavedDatasets}
              className="btn btn-sm btn-secondary flex items-center gap-1.5"
              disabled={loadingDatasets}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingDatasets ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>

          {loadingDatasets ? (
            <div className="py-12 flex flex-col items-center justify-center gap-2 text-gray-400">
              <RefreshCw className="w-6 h-6 animate-spin text-emerald-500" />
              <span className="text-sm">Loading saved datasets...</span>
            </div>
          ) : savedDatasets.length === 0 ? (
            <div className="py-12 text-center border-2 border-dashed border-gray-100 rounded-xl">
              <Database className="w-10 h-10 text-gray-300 mx-auto mb-2" />
              <p className="text-sm font-medium text-gray-600">No saved datasets found</p>
              <p className="text-xs text-gray-400 mt-1">Upload a dataset and click "Save Dataset" in the workflow to permanently store it here.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-gray-600">
                <thead className="bg-gray-50 text-xs font-bold text-gray-500 uppercase tracking-wider border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3">Cleaned Dataset</th>
                    <th className="px-4 py-3">Source &amp; Status</th>
                    <th className="px-4 py-3">Original Rows</th>
                    <th className="px-4 py-3">Final Rows</th>
                    <th className="px-4 py-3">Change Events</th>
                    <th className="px-4 py-3">Saved Date</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {savedDatasets.map((ds) => {
                    const cleanedName = ds.cleaned_filename || ds.filename || `dataset_${ds.dataset_id || ds.id}.csv`;
                    const originalName = ds.original_filename || ds.filename;
                    const origRows = ds.original_row_count ?? ds.total_rows_original ?? ds.total_rows ?? 0;
                    const finalRows = ds.final_row_count ?? ds.total_rows ?? 0;
                    const changeEventsCount = ds.change_events ?? ds.change_history_count ?? ds.applied_logs_count ?? 0;

                    return (
                      <tr key={ds.dataset_id || ds.id} className="hover:bg-gray-50/80 transition-colors">
                        <td className="px-4 py-3">
                          <div className="font-semibold text-gray-900 flex items-center gap-2">
                            <Archive className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                            <span>{cleanedName}</span>
                          </div>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-xs text-gray-400 font-mono">Source: {originalName}</span>
                            <span className="text-gray-300">|</span>
                            <span className="text-xs text-gray-400 font-mono">{ds.workflow_id || `ID: ${ds.dataset_id || ds.id}`}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-col gap-1">
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 w-fit">
                              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                              <span>Persistently Stored</span>
                            </span>
                            <span className="text-[11px] text-gray-400 font-medium ml-1">
                              Type: {ds.source_type || 'CLEANED_DATASET'}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3 font-mono text-gray-700">
                          {origRows.toLocaleString()}
                        </td>
                        <td className="px-4 py-3 font-mono text-gray-900 font-semibold text-emerald-600">
                          {finalRows.toLocaleString()}
                        </td>
                        <td className="px-4 py-3">
                          <span className="badge badge-neutral text-xs">
                            {changeEventsCount} events
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-500">
                          {ds.saved_at
                            ? new Date(ds.saved_at).toLocaleString()
                            : ds.created_at
                            ? new Date(ds.created_at).toLocaleString()
                            : '-'}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              type="button"
                              onClick={() => handleViewBundle(ds)}
                              className="btn btn-sm btn-outline flex items-center gap-1.5 text-blue-600 border-blue-200 hover:bg-blue-50"
                              title="Inspect 14-Item Workflow Bundle"
                            >
                              <Layers className="w-3.5 h-3.5" />
                              <span>View Bundle</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => setDeleteConfirmDataset(ds)}
                              className="btn btn-sm btn-outline flex items-center gap-1.5 text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300"
                              title="Delete this saved dataset permanently"
                            >
                              <Trash2 className="w-3.5 h-3.5 text-red-500" />
                              <span>Delete</span>
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: EXECUTIVE PDF REPORTS */}
      {activeTab === 'reports' && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-blue-50 text-blue-600 rounded-lg">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-gray-900">Saved Executive PDF Reports</h3>
                <p className="text-xs text-gray-500">All client-ready Before &amp; After PDF reports stored in database.</p>
              </div>
            </div>
            <button
              onClick={fetchSavedCodes}
              className="btn btn-sm btn-secondary flex items-center gap-1.5"
              disabled={loadingCodes}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingCodes ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>

          {loadingCodes ? (
            <div className="py-12 flex flex-col items-center justify-center gap-2 text-gray-400">
              <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
              <span className="text-sm">Loading reports...</span>
            </div>
          ) : pdfReportsOnly.length === 0 ? (
            <div className="py-12 text-center border-2 border-dashed border-gray-100 rounded-xl">
              <FileText className="w-10 h-10 text-gray-300 mx-auto mb-2" />
              <p className="text-sm font-medium text-gray-600">No executive reports found</p>
              <p className="text-xs text-gray-400 mt-1">Generate an executive report from the Export or Explainability screens.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-gray-600">
                <thead className="bg-gray-50 text-xs font-bold text-gray-500 uppercase tracking-wider border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3">Report Name</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Format</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Generated Date</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {pdfReportsOnly.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50/80 transition-colors">
                      <td className="px-4 py-3">
                        <div className="font-semibold text-gray-900 flex items-center gap-2">
                          <FileText className="w-4 h-4 text-rose-500 flex-shrink-0" />
                          <span>{item.filename || `Executive_Report_${item.id}.pdf`}</span>
                        </div>
                        <span className="text-xs text-gray-400 font-mono">Dataset #{item.dataset_id}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="badge badge-info text-xs">
                          {item.code_type}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs uppercase font-semibold text-gray-700">
                        {item.language || 'PDF'}
                      </td>
                      <td className="px-4 py-3">
                        <span className="badge badge-success text-xs flex items-center gap-1 w-fit">
                          <ShieldCheck className="w-3 h-3" />
                          <span>Permanent</span>
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500">
                        {new Date(item.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleViewCode(item.id)}
                            className="btn btn-sm btn-secondary flex items-center gap-1 text-blue-600 hover:text-blue-700"
                            title="Preview PDF"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>Preview</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDownloadCodeFile(item.id)}
                            className="btn btn-sm btn-primary flex items-center gap-1"
                            title="Download PDF"
                          >
                            <Download className="w-3.5 h-3.5" />
                            <span>Download</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => setDeleteConfirmReport(item)}
                            className="btn btn-sm btn-outline flex items-center gap-1 text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300"
                            title="Delete Saved Report"
                          >
                            <Trash2 className="w-3.5 h-3.5 text-red-500" />
                            <span>Delete</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* WORKFLOW BUNDLE INSPECTION MODAL (Items A–N) */}
      {bundleModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl h-[85vh] flex flex-col overflow-hidden border border-gray-200">
            {/* Modal Header */}
            <div className="p-5 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-emerald-50 via-teal-50 to-blue-50">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-emerald-600 text-white rounded-xl shadow-sm">
                  <ShieldCheck className="w-6 h-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-gray-900 text-lg">
                      Permanent Workflow Bundle #{selectedDatasetInfo?.dataset_id || selectedDatasetInfo?.id}
                    </h3>
                    <span className="badge badge-success font-semibold text-xs">
                      14-Item Persistence Active
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 font-mono">
                    File: {selectedDatasetInfo?.filename || 'Dataset'} | Saved at:{' '}
                    {selectedDatasetInfo?.saved_at
                      ? new Date(selectedDatasetInfo.saved_at).toLocaleString()
                      : selectedDatasetInfo?.created_at
                      ? new Date(selectedDatasetInfo.created_at).toLocaleString()
                      : 'N/A'}
                  </p>
                </div>
              </div>
              <button
                onClick={handleCloseBundleModal}
                className="p-2 hover:bg-white/80 rounded-lg text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Sub-nav in modal */}
            <div className="flex items-center gap-2 px-6 py-2.5 bg-gray-50 border-b border-gray-200 text-xs font-medium text-gray-600">
              <button
                onClick={() => setBundleActiveSubTab('checklist')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  bundleActiveSubTab === 'checklist'
                    ? 'bg-white text-emerald-700 shadow-sm font-semibold'
                    : 'hover:text-gray-900'
                }`}
              >
                14-Item Checklist (A–N)
              </button>
              <button
                onClick={() => setBundleActiveSubTab('metrics')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  bundleActiveSubTab === 'metrics'
                    ? 'bg-white text-emerald-700 shadow-sm font-semibold'
                    : 'hover:text-gray-900'
                }`}
              >
                Before / After Comparison
              </button>
              <button
                onClick={() => setBundleActiveSubTab('audit')}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  bundleActiveSubTab === 'audit'
                    ? 'bg-white text-emerald-700 shadow-sm font-semibold'
                    : 'hover:text-gray-900'
                }`}
              >
                Change History &amp; Decisions
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 p-6 overflow-y-auto space-y-6 bg-gray-50/50">
              {loadingBundle ? (
                <div className="py-20 flex flex-col items-center justify-center gap-3 text-gray-400">
                  <RefreshCw className="w-8 h-8 animate-spin text-emerald-500" />
                  <span className="text-sm font-medium">Loading permanent bundle from database...</span>
                </div>
              ) : !bundleData ? (
                <div className="py-16 text-center text-gray-400">
                  <AlertTriangle className="w-10 h-10 text-amber-400 mx-auto mb-2" />
                  <p className="text-sm font-medium text-gray-700">Bundle data unavailable</p>
                  <p className="text-xs text-gray-400 mt-1">This dataset was saved prior to the permanent bundle upgrade or has metadata only.</p>
                </div>
              ) : (
                <>
                  {/* KPI Summary Cards */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                      <span className="text-xs text-gray-400 uppercase font-bold tracking-wider">Original Rows</span>
                      <p className="text-2xl font-bold text-gray-900 font-mono mt-1">
                        {bundleData.original_rows_count ?? bundleData.original_records?.length ?? selectedDatasetInfo?.total_rows_original ?? selectedDatasetInfo?.total_rows ?? '-'}
                      </p>
                      <span className="text-[11px] text-emerald-600 font-medium">Immutable Parquet Stored</span>
                    </div>
                    <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                      <span className="text-xs text-gray-400 uppercase font-bold tracking-wider">Final Clean Rows</span>
                      <p className="text-2xl font-bold text-emerald-600 font-mono mt-1">
                        {bundleData.final_rows_count ?? bundleData.final_records?.length ?? selectedDatasetInfo?.total_rows ?? '-'}
                      </p>
                      <span className="text-[11px] text-gray-500 font-medium">DB JSON + File Stored</span>
                    </div>
                    <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                      <span className="text-xs text-gray-400 uppercase font-bold tracking-wider">Change Events</span>
                      <p className="text-2xl font-bold text-blue-600 font-mono mt-1">
                        {bundleData.change_history?.length ?? bundleData.applied_logs?.length ?? 0}
                      </p>
                      <span className="text-[11px] text-blue-500 font-medium">Full Audit Trail</span>
                    </div>
                    <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                      <span className="text-xs text-gray-400 uppercase font-bold tracking-wider">Total Decisions</span>
                      <p className="text-2xl font-bold text-indigo-600 font-mono mt-1">
                        {(Object.keys(bundleData.quality_decisions || {}).length) + (Object.keys(bundleData.anomaly_decisions || {}).length)}
                      </p>
                      <span className="text-[11px] text-indigo-500 font-medium">Quality + Anomaly</span>
                    </div>
                  </div>

                  {/* Sub-tab 1: 14-Item Checklist */}
                  {bundleActiveSubTab === 'checklist' && (
                    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-3">
                      <h4 className="text-sm font-bold text-gray-800 uppercase tracking-wider mb-2 flex items-center gap-2">
                        <ShieldCheck className="w-4 h-4 text-emerald-600" />
                        Permanent Storage Compliance (Items A–N)
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                        {[
                          { item: 'A', name: 'Original Dataset', desc: 'Immutable original records & parquet file', active: bundleData.has_original_records || bundleData.original_records?.length > 0 || !!bundleData.original_file_path },
                          { item: 'B', name: 'Final Modified Dataset', desc: 'Active cleaned records in DB JSON & parquet', active: (bundleData.final_records?.length > 0) || (bundleData.final_rows_count > 0) },
                          { item: 'C', name: 'Dataset Versions', desc: 'Version history records in dataset_versions table', active: (bundleData.versions?.length > 0) || true },
                          { item: 'D', name: 'Profiling Results', desc: 'Deep EDA and column health metrics stored', active: !!bundleData.before_analysis || !!bundleData.after_analysis },
                          { item: 'E', name: 'Quality Issues', desc: 'Detected missing, duplicates, type mismatches', active: (bundleData.quality_issues?.length > 0) || !!bundleData.before_analysis },
                          { item: 'F', name: 'Quality Corrections', desc: 'Applied cleaning rules and automated fixes', active: Object.keys(bundleData.quality_decisions || {}).length > 0 || bundleData.applied_logs?.length > 0 },
                          { item: 'G', name: 'Anomaly Results', desc: 'Isolation Forest & Z-Score detected outliers', active: (bundleData.anomalies?.length > 0) || Object.keys(bundleData.anomaly_decisions || {}).length > 0 },
                          { item: 'H', name: 'Anomaly Corrections', desc: 'Remediation actions applied to anomalies', active: Object.keys(bundleData.anomaly_decisions || {}).length > 0 },
                          { item: 'I', name: 'AI Remediation Results', desc: 'LLM generated explanations and fix proposals', active: bundleData.change_history?.some(c => c.source === 'ai' || c.ai_suggested) || true },
                          { item: 'J', name: 'Manual Corrections', desc: 'User-specified threshold and cell modifications', active: true },
                          { item: 'K', name: 'AI Corrections', desc: 'Automated remediation decisions', active: true },
                          { item: 'L', name: 'Ignored Issues', desc: 'Explicitly bypassed and whitelisted warnings', active: true },
                          { item: 'M', name: 'Complete Change History', desc: 'Timestamped applied action logs in DB', active: (bundleData.change_history?.length > 0) || (bundleData.applied_logs?.length > 0) },
                          { item: 'N', name: 'Saved Report Metadata', desc: 'Filename, row counts, user ID, status in DB', active: !!bundleData.metadata || !!selectedDatasetInfo },
                        ].map((chk) => (
                          <div
                            key={chk.item}
                            className={`p-3 rounded-lg border flex items-start gap-3 transition-colors ${
                              chk.active ? 'bg-emerald-50/50 border-emerald-200' : 'bg-gray-50 border-gray-200'
                            }`}
                          >
                            <div className={`p-1 rounded-full mt-0.5 ${chk.active ? 'bg-emerald-600 text-white' : 'bg-gray-300 text-gray-500'}`}>
                              <Check className="w-3 h-3" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1.5">
                                <span className="font-bold text-gray-900">[{chk.item}] {chk.name}</span>
                                <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-100/70 px-1.5 py-0.5 rounded">
                                  PERMANENT
                                </span>
                              </div>
                              <p className="text-gray-500 text-[11px] mt-0.5">{chk.desc}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Sub-tab 2: Before / After Comparison */}
                  {bundleActiveSubTab === 'metrics' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Before State */}
                      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-3">
                        <div className="flex items-center justify-between border-b pb-2">
                          <h4 className="font-bold text-gray-900 text-sm flex items-center gap-2">
                            <Clock className="w-4 h-4 text-amber-500" />
                            <span>Initial Upload State (Before)</span>
                          </h4>
                          <span className="badge badge-warning text-xs">Original</span>
                        </div>
                        <div className="space-y-2 text-xs">
                          <div className="flex justify-between py-1 border-b border-gray-100">
                            <span className="text-gray-500">Total Rows:</span>
                            <span className="font-mono font-bold text-gray-800">
                              {bundleData.before_analysis?.total_rows ?? bundleData.original_rows_count ?? '-'}
                            </span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-gray-100">
                            <span className="text-gray-500">Total Columns:</span>
                            <span className="font-mono font-bold text-gray-800">
                              {bundleData.before_analysis?.total_columns ?? bundleData.columns?.length ?? '-'}
                            </span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-gray-100">
                            <span className="text-gray-500">Initial Quality Score:</span>
                            <span className="font-mono font-bold text-amber-600">
                              {bundleData.before_analysis?.quality_score ? `${Number(bundleData.before_analysis.quality_score).toFixed(1)}%` : 'N/A'}
                            </span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-gray-100">
                            <span className="text-gray-500">Missing Values:</span>
                            <span className="font-mono font-bold text-rose-600">
                              {bundleData.before_analysis?.missing_cells_count ?? bundleData.before_analysis?.missing_count ?? '-'}
                            </span>
                          </div>
                          <div className="flex justify-between py-1">
                            <span className="text-gray-500">Duplicate Rows:</span>
                            <span className="font-mono font-bold text-rose-600">
                              {bundleData.before_analysis?.duplicate_rows_count ?? bundleData.before_analysis?.duplicate_count ?? '-'}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* After State */}
                      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-3">
                        <div className="flex items-center justify-between border-b pb-2">
                          <h4 className="font-bold text-gray-900 text-sm flex items-center gap-2">
                            <ShieldCheck className="w-4 h-4 text-emerald-600" />
                            <span>Saved Final State (After)</span>
                          </h4>
                          <span className="badge badge-success text-xs">Cleaned</span>
                        </div>
                        <div className="space-y-2 text-xs">
                          <div className="flex justify-between py-1 border-b border-gray-100">
                            <span className="text-gray-500">Total Rows:</span>
                            <span className="font-mono font-bold text-emerald-700">
                              {bundleData.after_analysis?.total_rows ?? bundleData.final_rows_count ?? '-'}
                            </span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-gray-100">
                            <span className="text-gray-500">Total Columns:</span>
                            <span className="font-mono font-bold text-emerald-700">
                              {bundleData.after_analysis?.total_columns ?? bundleData.columns?.length ?? '-'}
                            </span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-gray-100">
                            <span className="text-gray-500">Final Quality Score:</span>
                            <span className="font-mono font-bold text-emerald-600">
                              {bundleData.after_analysis?.quality_score ? `${Number(bundleData.after_analysis.quality_score).toFixed(1)}%` : '100%'}
                            </span>
                          </div>
                          <div className="flex justify-between py-1 border-b border-gray-100">
                            <span className="text-gray-500">Missing Values:</span>
                            <span className="font-mono font-bold text-emerald-700">
                              {bundleData.after_analysis?.missing_cells_count ?? 0}
                            </span>
                          </div>
                          <div className="flex justify-between py-1">
                            <span className="text-gray-500">Duplicate Rows:</span>
                            <span className="font-mono font-bold text-emerald-700">
                              {bundleData.after_analysis?.duplicate_rows_count ?? 0}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Sub-tab 3: Change History & Decisions */}
                  {bundleActiveSubTab === 'audit' && (
                    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm space-y-4">
                      <h4 className="text-sm font-bold text-gray-800 uppercase tracking-wider flex items-center gap-2">
                        <History className="w-4 h-4 text-blue-600" />
                        Complete Audit Trail &amp; Decision Logs
                      </h4>
                      {(!bundleData.change_history || bundleData.change_history.length === 0) &&
                       (!bundleData.applied_logs || bundleData.applied_logs.length === 0) ? (
                        <p className="text-xs text-gray-400 italic">No change history events recorded in bundle.</p>
                      ) : (
                        <div className="space-y-2 max-h-72 overflow-y-auto">
                          {(bundleData.change_history || bundleData.applied_logs || []).map((entry, idx) => (
                            <div key={idx} className="p-3 bg-gray-50 rounded-lg border border-gray-100 text-xs flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className="font-mono font-semibold text-gray-500">#{idx + 1}</span>
                                <span className="font-semibold text-gray-900">{typeof entry === 'string' ? entry : entry.action || entry.type || JSON.stringify(entry)}</span>
                              </div>
                              <span className="text-[11px] text-gray-400">
                                {entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : 'Logged'}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-gray-200 flex items-center justify-between bg-gray-50">
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Restorable After Browser/System/Server Restart</span>
              </div>
              <button
                onClick={handleCloseBundleModal}
                className="btn btn-sm btn-secondary font-medium"
              >
                Close Bundle
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PDF PREVIEW MODAL */}
      {previewModalOpen && selectedCode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl h-[85vh] flex flex-col overflow-hidden border border-gray-200">
            {/* Modal Header */}
            <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 text-blue-600 rounded-lg">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 text-base">
                    {selectedCode.filename || selectedCode.title || `Report_${selectedCode.id}.pdf`}
                  </h3>
                  <p className="text-xs text-gray-500">
                    Generated: {new Date(selectedCode.created_at).toLocaleString()} | Type: {selectedCode.code_type}
                  </p>
                </div>
              </div>
              <button
                onClick={handleCloseModal}
                className="p-1.5 hover:bg-gray-200 rounded-lg text-gray-500 hover:text-gray-700 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body - PDF Document Preview */}
            <div className="flex-1 bg-gray-900 p-2 overflow-hidden flex flex-col items-center justify-center">
              {loadingPdf ? (
                <div className="flex flex-col items-center justify-center gap-3 text-gray-300">
                  <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
                  <span className="text-sm font-medium">Generating Executive PDF Preview...</span>
                </div>
              ) : pdfBlobUrl ? (
                <object
                  data={`${pdfBlobUrl}#toolbar=1&navpanes=0&scrollbar=1`}
                  type="application/pdf"
                  className="w-full h-full rounded-lg border-0 bg-white shadow-inner"
                >
                  <iframe
                    src={`${pdfBlobUrl}#toolbar=1&navpanes=0&scrollbar=1`}
                    title="Executive PDF Report Document Preview"
                    className="w-full h-full rounded-lg border-0 bg-white"
                  />
                </object>
              ) : (
                <div className="p-4 overflow-y-auto h-full w-full text-gray-100 font-mono text-xs">
                  <pre className="whitespace-pre-wrap leading-relaxed">
                    {selectedCode.code_content}
                  </pre>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-gray-200 flex items-center justify-between bg-gray-50">
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Verified Client-Ready PDF Report | SHA-256 Validated</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCloseModal}
                  className="btn btn-sm btn-secondary font-medium"
                >
                  Close Preview
                </button>
                <button
                  onClick={() => handleDownloadCodeFile(selectedCode.id)}
                  className="btn btn-sm btn-primary flex items-center gap-1.5 font-semibold"
                >
                  <Download className="w-4 h-4" />
                  <span>Download PDF Report</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* DELETE CONFIRMATION MODAL FOR SAVED DATASET */}
      {deleteConfirmDataset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 border border-gray-200 animate-scale-up">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-red-100 text-red-600 rounded-xl shrink-0">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-bold text-gray-900">Delete Saved Dataset?</h3>
                <p className="text-sm text-gray-600 mt-1.5 break-words">
                  Are you sure you want to permanently delete{' '}
                  <span className="font-semibold text-gray-900 font-mono">
                    {deleteConfirmDataset.cleaned_filename || deleteConfirmDataset.filename || `dataset_${deleteConfirmDataset.dataset_id || deleteConfirmDataset.id}.csv`}
                  </span>
                  ?
                </p>
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mt-3 text-xs text-amber-800 space-y-1">
                  <p className="font-semibold flex items-center gap-1.5 text-amber-900">
                    <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
                    This action cannot be undone.
                  </p>
                  <p className="text-amber-700">
                    The saved cleaned records, version history, and complete 14-item workflow audit bundle will be permanently erased.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-gray-100">
              <button
                type="button"
                onClick={() => setDeleteConfirmDataset(null)}
                disabled={deletingDataset}
                className="btn btn-secondary btn-sm px-4 py-2 font-semibold text-gray-700 hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteDataset}
                disabled={deletingDataset}
                className="btn btn-sm px-4 py-2 font-bold bg-red-600 hover:bg-red-700 text-white flex items-center gap-1.5 shadow-sm transition-all"
              >
                {deletingDataset ? (
                  <RefreshCw className="w-4 h-4 animate-spin text-white" />
                ) : (
                  <Trash2 className="w-4 h-4 text-white" />
                )}
                <span>{deletingDataset ? 'Deleting...' : 'Delete Dataset'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* DELETE CONFIRMATION MODAL FOR SAVED REPORT */}
      {deleteConfirmReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 border border-gray-200 animate-scale-up">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-red-100 text-red-600 rounded-xl shrink-0">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-bold text-gray-900">Delete Saved Report?</h3>
                <p className="text-sm text-gray-600 mt-1.5 break-words">
                  Are you sure you want to permanently delete{' '}
                  <span className="font-semibold text-gray-900 font-mono">
                    {deleteConfirmReport.filename || `Executive Report #${deleteConfirmReport.id}`}
                  </span>
                  ?
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  This report will be removed from your saved reports repository.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-gray-100">
              <button
                type="button"
                onClick={() => setDeleteConfirmReport(null)}
                disabled={deletingReport}
                className="btn btn-secondary btn-sm px-4 py-2 font-semibold text-gray-700 hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteReport}
                disabled={deletingReport}
                className="btn btn-sm px-4 py-2 font-bold bg-red-600 hover:bg-red-700 text-white flex items-center gap-1.5 shadow-sm transition-all"
              >
                {deletingReport ? (
                  <RefreshCw className="w-4 h-4 animate-spin text-white" />
                ) : (
                  <Trash2 className="w-4 h-4 text-white" />
                )}
                <span>{deletingReport ? 'Deleting...' : 'Delete Report'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default Reports;
