import api from './api';

export const generateReport = async (datasetId, format = 'pdf') => {
  const response = await api.get(`/reports/generate/${datasetId}?format=${format}`);
  return response.data;
};

export const exportDataset = async (datasetId, format = 'csv') => {
  const response = await api.get(`/export/${datasetId}?format=${format}`);
  return response.data;
};

export const generateBeforeAfterPdf = async (payload) => {
  const response = await api.post('/reports/before-after-pdf', payload, {
    responseType: 'blob'
  });
  return response.data;
};

export const getDatasetGeneratedCodes = async (datasetId) => {
  const response = await api.get(`/code/dataset/${datasetId}`);
  return response.data;
};

export const getGeneratedCodeById = async (codeId) => {
  const response = await api.get(`/code/${codeId}`);
  return response.data;
};

export const getUserSavedReports = async () => {
  const response = await api.get('/code/user/saved-reports');
  return response.data;
};

export const previewGeneratedPdfReport = async (codeId) => {
  const response = await api.get(`/code/preview/${codeId}`, {
    responseType: 'blob'
  });
  return response.data;
};

export const deleteSavedReport = async (codeId) => {
  const response = await api.delete(`/code/${codeId}`);
  return response.data;
};





