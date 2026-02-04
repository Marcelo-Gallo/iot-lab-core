import api from './api';

export const sensorService = {
  // Listar todos (agora inclui arquivados)
  getAll: async () => {
    const response = await api.get('/sensor-types/');
    return response.data;
  },

  // Criar novo
  create: async (data) => {
    const response = await api.post('/sensor-types/', data);
    return response.data;
  },

  // Atualizar
  update: async (id, data) => {
    const response = await api.put(`/sensor-types/${id}`, data);
    return response.data;
  },

  // Soft Delete (Arquivar)
  delete: async (id) => {
    try {
      await api.delete(`/sensor-types/${id}`);
      return true;
    } catch (error) {
      console.error("Erro ao arquivar sensor:", error);
      throw error;
    }
  },

  // Restore (Desarquivar)
  restore: async (id) => {
    try {
      await api.post(`/sensor-types/${id}/restore`);
      return true;
    } catch (error) {
      console.error("Erro ao restaurar sensor:", error);
      throw error;
    }
  }
};