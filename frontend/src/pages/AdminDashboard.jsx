import React, { useState, useEffect } from 'react';
import { adminService } from '../services/adminService';
import { useAuth } from '../context/AuthContext';

export default function AdminDashboard() {
  const { user } = useAuth();
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Form State para Onboarding
  const [formData, setFormData] = useState({
    org_name: '',
    org_slug: '',
    org_description: '',
    admin_name: '',
    admin_email: '',
    admin_password: ''
  });

  useEffect(() => {
    loadOrgs();
  }, []);

  const loadOrgs = async () => {
    try {
      const data = await adminService.getAllOrganizations();
      setOrgs(data);
    } catch (error) {
      console.error("Falha ao carregar organizações", error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleOnboard = async (e) => {
    e.preventDefault();
    try {
      await adminService.onboardTenant(formData);
      alert("Laboratório criado com sucesso!");
      setIsModalOpen(false);
      loadOrgs(); // Recarrega a lista
      setFormData({ // Limpa form
        org_name: '', org_slug: '', org_description: '',
        admin_name: '', admin_email: '', admin_password: ''
      });
    } catch (error) {
      alert("Erro ao criar: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleDelete = async (id) => {
    if(!window.confirm("ATENÇÃO: Isso pode apagar dados históricos. Continuar?")) return;
    try {
      await adminService.deleteOrganization(id);
      setOrgs(orgs.filter(o => o.id !== id));
    } catch (error) {
      alert("Erro ao remover organização.");
    }
  };

  if (!user?.is_superuser) {
    return <div className="p-10 text-center text-red-600">Acesso Negado. Área restrita a Superusuários.</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <header className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Gestão de Laboratórios</h1>
          <p className="text-gray-500 text-sm">Painel do Super Administrador</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg shadow-sm font-medium transition-colors"
        >
          + Novo Laboratório
        </button>
      </header>

      {loading ? (
        <div className="text-center py-10">Carregando...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {orgs.map(org => (
            <div key={org.id} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-bold text-gray-800">{org.name}</h3>
                <span className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded font-mono">
                  {org.slug}
                </span>
              </div>
              <p className="text-gray-500 text-sm mb-6 h-10 overflow-hidden text-ellipsis">
                {org.description || "Sem descrição."}
              </p>
              <div className="border-t pt-4 flex justify-between items-center">
                <span className="text-xs text-gray-400">Criado em: {new Date(org.created_at).toLocaleDateString()}</span>
                <button 
                  onClick={() => handleDelete(org.id)}
                  className="text-red-500 hover:text-red-700 text-sm font-medium"
                >
                  Remover
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* MODAL DE ONBOARDING */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-6 text-gray-800">Provisionar Novo Tenant</h2>
            <form onSubmit={handleOnboard}>
              
              <div className="mb-6">
                <h3 className="text-sm font-bold text-gray-500 uppercase mb-3 border-b pb-1">Dados da Organização</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Nome do Lab</label>
                    <input name="org_name" required value={formData.org_name} onChange={handleInputChange} className="w-full p-2 border rounded focus:ring-2 focus:ring-purple-500 outline-none" placeholder="Ex: Lab de Física" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Slug (URL)</label>
                    <input name="org_slug" required value={formData.org_slug} onChange={handleInputChange} className="w-full p-2 border rounded focus:ring-2 focus:ring-purple-500 outline-none" placeholder="Ex: lab-fisica-01" />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
                    <input name="org_description" value={formData.org_description} onChange={handleInputChange} className="w-full p-2 border rounded focus:ring-2 focus:ring-purple-500 outline-none" />
                  </div>
                </div>
              </div>

              <div className="mb-6">
                <h3 className="text-sm font-bold text-gray-500 uppercase mb-3 border-b pb-1">Administrador Inicial</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Nome do Professor</label>
                    <input name="admin_name" required value={formData.admin_name} onChange={handleInputChange} className="w-full p-2 border rounded focus:ring-2 focus:ring-purple-500 outline-none" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email (Login)</label>
                    <input type="email" name="admin_email" required value={formData.admin_email} onChange={handleInputChange} className="w-full p-2 border rounded focus:ring-2 focus:ring-purple-500 outline-none" />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Senha Inicial</label>
                    <input type="password" name="admin_password" required value={formData.admin_password} onChange={handleInputChange} className="w-full p-2 border rounded focus:ring-2 focus:ring-purple-500 outline-none" />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button type="button" onClick={() => setIsModalOpen(false)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">Cancelar</button>
                <button type="submit" className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium">Confirmar Criação</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}