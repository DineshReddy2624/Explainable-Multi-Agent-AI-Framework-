import api from './api';

export const uploadDataset = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/upload/analyze-file', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getDatasets = async (savedOnly = false) => {
  const response = await api.get(`/upload/datasets${savedOnly ? '?saved_only=true' : ''}`);
  return response.data;
};

export const getSavedDatasets = async () => {
  const response = await api.get('/upload/saved-datasets');
  return response.data;
};

export const profileDataset = async (datasetId) => {
  const response = await api.post(`/profiling/profile/${datasetId}`);
  return response.data;
};

/**
 * Permanently save the complete dataset workflow state to the backend.
 * Sends all 14 required items (original records, final records, change history,
 * quality decisions, anomaly decisions, before/after analysis, applied logs).
 *
 * @param {number} datasetId - The dataset ID to save
 * @param {Object} bundle - The complete workflow bundle
 * @param {Array}  bundle.records             - Final (modified) dataset rows
 * @param {Array}  bundle.original_records    - Original uploaded rows (immutable)
 * @param {Array}  bundle.change_history      - Every cell-level change
 * @param {Object} bundle.quality_decisions   - Per-issue status decisions
 * @param {Object} bundle.anomaly_decisions   - Per-anomaly status decisions
 * @param {Object} bundle.before_analysis     - Profiling at upload time
 * @param {Object} bundle.after_analysis      - Profiling at save time
 * @param {Array}  bundle.applied_logs        - Remediation log entries
 */
export const saveWorkflowDataset = async (datasetId, bundle) => {
  const response = await api.post(`/upload/save-workflow-dataset/${datasetId}`, bundle);
  return response.data;
};

/**
 * Retrieve the complete persisted workflow state for a saved dataset.
 * Returns all 14 items so the frontend can fully restore any saved session.
 *
 * @param {number} datasetId - The dataset ID to retrieve
 */
export const getWorkflowBundle = async (datasetId) => {
  const response = await api.get(`/upload/workflow-bundle/${datasetId}`);
  return response.data;
};

/**
 * Permanently delete a saved dataset and its workflow bundle.
 *
 * @param {number} datasetId - The dataset ID to delete
 */
export const deleteDataset = async (datasetId) => {
  const response = await api.delete(`/upload/datasets/${datasetId}`);
  return response.data;
};


