import api from './api';

export const getXaiExplanations = async (datasetId) => {
  const response = await api.get(`/explainability/xai-explanations/${datasetId}`);
  return response.data;
};

export const explainRowWithLlm = async (payload) => {
  const response = await api.post('/explainability/explain-row', payload);
  return response.data;
};

export const getSavedDatasets = async () => {
  const response = await api.get('/upload/saved-datasets');
  return response.data;
};

/**
 * Retrieve the complete persisted workflow bundle for a saved dataset.
 * Includes original records, final records, change history, decisions, and analysis.
 */
export const getWorkflowBundle = async (datasetId) => {
  const response = await api.get(`/upload/workflow-bundle/${datasetId}`);
  return response.data;
};

