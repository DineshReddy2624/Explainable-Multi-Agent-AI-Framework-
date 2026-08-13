import api from './api';

export const getMonitoringMetrics = async (datasetId) => {
  const response = await api.get(`/monitoring/metrics/${datasetId}`);
  return response.data;
};

export const getActivityTimeline = async (datasetId) => {
  const response = await api.get(`/monitoring/timeline/${datasetId}`);
  return response.data;
};
