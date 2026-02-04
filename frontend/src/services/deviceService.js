import api from './api';

export const deviceService = {
  // Busca todos os dispositivos cadastrados
  getAll: async () => {
    try {
      const response = await api.get('/devices/');
      return response.data;
    } catch (error) {
      console.error("Erro ao buscar dispositivos:", error);
      throw error;
    }
  },

  restore: async (id) => {
    try {
      await api.post(`/devices/${id}/restore`);
      return true;
    } catch (error) {
      console.error("Erro ao restaurar dispositivo:", error);
      throw error;
    }
  },

  create: async (deviceData) => {
    try {
      const response = await api.post('/devices/', deviceData);
      return response.data;
    } catch (error) {
      console.error("Erro ao criar dispositivo:", error);
      throw error;
    }
  },

  delete: async (id) => {
    try {
      await api.delete(`/devices/${id}`); 
      return true;
    } catch (error) {
      console.error("Erro ao excluir dispositivo:", error);
      throw error;
    }
  },

  getById: async (id) => {
    const response = await api.get(`/devices/${id}`);
    return response.data;
  },

  // Busca os tokens (chaves de acesso) do dispositivo
  getTokens: async (deviceId) => {
    const response = await api.get(`/devices/${deviceId}/tokens`);
    return response.data;
  },

  // Gera um novo token para o dispositivo
  createToken: async (deviceId, label) => {
    const response = await api.post(`/devices/${deviceId}/tokens`, { label });
    return response.data;
  },

  // Atualiza a lista de sensores do dispositivo
  updateSensors: async (deviceId, sensorIds) => {
    // O backend espera: { sensor_ids: [1, 2, 3] }
    const response = await api.post(`/devices/${deviceId}/sensors`, { sensor_ids: sensorIds });
    return response.data;
  },

  getStats: async () => {
  }
};