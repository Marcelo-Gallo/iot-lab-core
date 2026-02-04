import api from './api';

export const adminService = {
  // Lista todas as organizações (Apenas SuperUser)
  getAllOrganizations: async () => {
    const response = await api.get('/organizations/');
    return response.data;
  },

  // Executa o Onboarding (Cria Org + Admin atômico)
  onboardTenant: async (payload) => {
    // payload: { org_name, org_slug, org_description, admin_email, admin_name, admin_password }
    const response = await api.post('/onboarding/', payload);
    return response.data;
  },

  // Soft Delete de uma organização
  deleteOrganization: async (id) => {
    await api.delete(`/organizations/${id}`);
  }
};