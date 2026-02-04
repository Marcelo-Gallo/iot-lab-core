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
  // Agora suporta tanto lista de IDs simples quanto objetos com fórmula
  updateSensors: async (deviceId, sensorIdsOrObjects) => {
    // ADAPTAÇÃO: O backend novo espera uma lista de objetos:
    // [{ sensor_type_id: 1, calibration_formula: null }, ...]
    
    const payload = sensorIdsOrObjects.map(item => {
        // Se for número ou string (apenas ID), converte para objeto padrão
        if (typeof item === 'number' || typeof item === 'string') {
            return { 
                sensor_type_id: parseInt(item), 
                calibration_formula: null 
            };
        }
        // Se já for objeto (do futuro modal de fórmulas), mantém como está
        return item;
    });

    // Envia o array diretamente (não envelopado em objeto json)
    const response = await api.post(`/devices/${deviceId}/sensors`, payload);
    return response.data;
  },

  getStats: async () => {
      // Placeholder para futura implementação
  }
};