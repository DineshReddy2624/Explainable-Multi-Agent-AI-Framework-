import api from './api';

export const sendChatQuery = async (datasetId, message, history = []) => {
  const response = await api.post('/chat/message', { dataset_id: datasetId, message, history });
  return response.data;
};
