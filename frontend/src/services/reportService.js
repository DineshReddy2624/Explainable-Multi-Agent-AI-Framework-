import api from './api';

export const generateReport = async (datasetId, format = 'pdf') => {
  const response = await api.get(`/reports/generate/${datasetId}?format=${format}`);
  return response.data;
};

export const exportDataset = async (datasetId, format = 'csv') => {
  const response = await api.get(`/export/${datasetId}?format=${format}`);
  return response.data;
};
