import api from './api';

export const measurementService = {
  getByDevice: async (deviceId, params = {}) => {
    try {
      const { limit = 100, startDate = null } = params;
      
      const queryParams = new URLSearchParams();
      queryParams.append('device_id', deviceId);
      queryParams.append('limit', limit);
      
      if (startDate) {
        queryParams.append('start_date', startDate.toISOString());
      }

      const response = await api.get(`/measurements/?${queryParams.toString()}`);
      return response.data;
    } catch (error) {
      console.error("Erro ao buscar medições:", error);
      return [];
    }
  },

  getAnalytics: async (period = '1d') => {
    const response = await api.get(`/measurements/analytics/?period=${period}`);
    return response.data;
  }
};