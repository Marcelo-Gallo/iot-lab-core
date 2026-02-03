import api from './api';

export const sensorService = {
  // Lista todos os tipos de sensores disponíveis no sistema
  getAllTypes: async () => {
    const response = await api.get('/sensor-types/');
    return response.data;
  }
};