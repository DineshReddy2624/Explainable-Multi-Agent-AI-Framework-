import api from './api';

export const getCorrectionSuggestions = async (datasetId) => {
  const response = await api.post(`/correction/suggest/${datasetId}`);
  return response.data;
};

export const applyCorrection = async (payload) => {
  const response = await api.post('/correction/apply', payload);
  return response.data;
};
