import { useContext, useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom';
import { AuthProvider, AuthContext } from './context/AuthContext';
import Login from './pages/Login';
import { deviceService } from './services/deviceService';
import DeviceTable from './components/DeviceTable';
import CreateDeviceModal from './components/CreateDeviceModal';
import DeviceDetails from './pages/DeviceDetails';

// Componente Wrapper para Rotas Privadas
const PrivateRoute = ({ children }) => {
  const { authenticated, loading } = useContext(AuthContext);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-iot-primary"></div>
      </div>
    );
  }

  if (!authenticated) {
    return <Navigate to="/login" />;
  }

  return children;
};

// Layout do Dashboard (Sidebar + Header + Content)
const DashboardLayout = () => {
    const { logout, user } = useContext(AuthContext);
    
    // Estados para armazenar dados reais
    const [devices, setDevices] = useState([]);
    const [stats, setStats] = useState({ total: 0, active: 0 });
    const [loadingData, setLoadingData] = useState(true);

    // Estado do Modal
    const [isModalOpen, setIsModalOpen] = useState(false);

    // Lógica de criação (Create do CRUD)
    const handleCreateDevice = async (deviceData) => {
        try {
            const newDevice = await deviceService.create(deviceData);
            
            // Atualiza a lista localmente (Optimistic UI update)
            setDevices(prev => [...prev, newDevice]);

            // Atualiza os contadores
            setStats(prev => ({ ...prev, total: prev.total + 1 }));

            alert("Dispositivo criado com sucesso!"); 
        } catch (error) {
            alert("Erro ao criar dispositivo: " + (error.response?.data?.detail || error.message));
        }
    };

    // Efeito para carregar dados ao abrir a tela (Read do CRUD)
    useEffect(() => {
        async function loadData() {
            try {
                const data = await deviceService.getAll();
                setDevices(data);
                
                // Calcula estatísticas simples no front
                const activeCount = data.filter(d => d.is_active).length;
                setStats({
                    total: data.length,
                    active: activeCount
                });
            } catch (error) {
                console.error("Falha ao carregar dashboard:", error);
            } finally {
                setLoadingData(false);
            }
        }

        loadData();
    }, []);

    return (
        <div className="flex h-screen bg-gray-100">
            {/* Sidebar (Lateral Esquerda) */}
            <aside className="w-64 bg-iot-dark text-white flex flex-col shadow-xl z-20">
               <div className="h-16 flex items-center justify-center border-b border-gray-700 bg-gray-900">
                    <span className="text-xl font-bold tracking-wider">📡 IoT Lab</span>
                </div>

                <nav className="flex-1 px-2 py-4 space-y-2">
                    {/* Link Ativo (Dashboard) */}
                    <Link to="/" className="flex items-center px-4 py-3 bg-iot-primary text-white rounded-md transition-colors shadow-sm">
                        <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path></svg>
                        Dashboard
                    </Link>
                    
                    {/* Links Secundários (Placeholders) */}
                    <a href="#" className="flex items-center px-4 py-3 text-gray-300 hover:bg-gray-700 hover:text-white rounded-md transition-colors">
                        <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path></svg>
                        Dispositivos
                    </a>
                    <a href="#" className="flex items-center px-4 py-3 text-gray-300 hover:bg-gray-700 hover:text-white rounded-md transition-colors">
                        <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                        Configurações
                    </a>
                </nav>
                
                {/* Botão de Logout */}
                <div className="p-4 border-t border-gray-700">
                    <button onClick={logout} className="flex items-center text-red-400 hover:text-red-300 transition-colors text-sm font-medium w-full">
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
                        Encerrar Sessão
                    </button>
                </div>
            </aside>

            {/* Conteúdo Principal */}
            <main className="flex-1 flex flex-col overflow-hidden">
                {/* Header Superior */}
                <header className="h-16 bg-white shadow-sm flex items-center justify-between px-6 z-10">
                    <h1 className="text-xl font-bold text-gray-800">Visão Geral</h1>
                    <div className="flex items-center space-x-4">
                        <span className="text-sm text-gray-600">
                            Logado como <strong className="text-gray-800">{user?.username || 'Admin'}</strong>
                        </span>
                        <div className="h-8 w-8 rounded-full bg-iot-secondary flex items-center justify-center text-white font-bold">
                            {(user?.username || 'A')[0].toUpperCase()}
                        </div>
                    </div>
                </header>

                {/* Área de Scroll do Conteúdo */}
                <div className="flex-1 overflow-auto p-6">
                    
                    {/* Cards de KPIs */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                            <h3 className="text-gray-500 text-sm font-medium uppercase">Dispositivos Totais</h3>
                            <p className="text-3xl font-bold text-gray-800 mt-2">
                                {loadingData ? '...' : stats.total}
                            </p>
                        </div>
                        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                            <h3 className="text-gray-500 text-sm font-medium uppercase">Online Agora</h3>
                            <p className="text-3xl font-bold text-iot-primary mt-2">
                                {loadingData ? '...' : stats.active}
                            </p>
                        </div>
                        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                            <h3 className="text-gray-500 text-sm font-medium uppercase">Status da API</h3>
                            <p className="text-lg font-bold text-green-600 mt-2 flex items-center">
                                <span className="h-3 w-3 bg-green-500 rounded-full mr-2"></span>
                                Conectado
                            </p>
                        </div>
                    </div>

                    {/* Cabeçalho da Tabela + Botão de Ação */}
                    <div className="flex justify-between items-center mb-4 mt-8">
                        <h2 className="text-xl font-bold text-gray-800">Meus Dispositivos</h2>
                        
                        {/* 🚀 AQUI ESTÁ O BOTÃO QUE FALTAVA */}
                        <button 
                            onClick={() => setIsModalOpen(true)}
                            className="bg-iot-primary text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors shadow-sm flex items-center font-medium"
                        >
                            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"></path></svg>
                            Adicionar Dispositivo
                        </button>
                    </div>

                    {/* Tabela */}
                    {loadingData ? (
                        <div className="text-center py-10"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-iot-primary mx-auto"></div></div>
                    ) : (
                        <DeviceTable devices={devices} />
                    )}
                </div>
            </main>

            {/* 🚀 MODAL INJETADO AQUI (Fora do fluxo principal, controlado por state) */}
            <CreateDeviceModal 
                isOpen={isModalOpen} 
                onClose={() => setIsModalOpen(false)} 
                onSave={handleCreateDevice} 
            />
        </div>
    );
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          {/* Rota Raiz Protegida */}
          <Route path="/" element={<PrivateRoute><DashboardLayout /></PrivateRoute>} />
          
          <Route 
            path="/devices/:id" 
            element={
              <PrivateRoute>
                <DeviceDetails />
              </PrivateRoute>
            } 
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;