import api from './api';

export const uploadDataset = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/upload/analyze-file', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getDatasets = async () => {
  const response = await api.get('/upload/datasets');
  return response.data;
};

export const profileDataset = async (datasetId) => {
  const response = await api.post(`/profiling/profile/${datasetId}`);
  return response.data;
};
