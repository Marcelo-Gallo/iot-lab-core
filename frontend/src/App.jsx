import { useContext } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { AuthProvider, AuthContext } from './context/AuthContext';
import Login from './pages/Login';
import DeviceDetails from './pages/DeviceDetails';

// Importação das Páginas Principais
import Dashboard from './pages/Dashboard';
import SensorTypesPage from './pages/SensorTypesPage';

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

// Layout do Dashboard (Agora genérico: recebe 'children')
const DashboardLayout = ({ children }) => {
    const { logout, user } = useContext(AuthContext);
    const location = useLocation();

    // Função auxiliar para classe de link ativo
    const getLinkClass = (path) => {
        const isActive = location.pathname === path;
        return `flex items-center px-4 py-3 rounded-md transition-colors ${
            isActive 
            ? 'bg-iot-primary text-white shadow-sm' 
            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
        }`;
    };
    
    return (
        <div className="flex h-screen bg-gray-100">
            {/* Sidebar */}
            <aside className="w-64 bg-iot-dark text-white flex flex-col shadow-xl z-20">
               <div className="h-16 flex items-center justify-center border-b border-gray-700 bg-gray-900">
                    <span className="text-xl font-bold tracking-wider">📡 IoT Lab</span>
                </div>

                <nav className="flex-1 px-2 py-4 space-y-2">
                    {/* Link Dashboard */}
                    <Link to="/" className={getLinkClass('/')}>
                        <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path></svg>
                        Dashboard
                    </Link>
                    
                    {/* Link Sensores (NOVO) */}
                    <Link to="/sensors" className={getLinkClass('/sensors')}>
                        <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                        Tipos de Sensores
                    </Link>

                    {/* Link Configurações (Placeholder) */}
                    <a href="#" className="flex items-center px-4 py-3 text-gray-300 hover:bg-gray-700 hover:text-white rounded-md transition-colors">
                        <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                        Configurações
                    </a>
                </nav>
                
                <div className="p-4 border-t border-gray-700">
                    <button onClick={logout} className="flex items-center text-red-400 hover:text-red-300 transition-colors text-sm font-medium w-full">
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
                        Encerrar Sessão
                    </button>
                </div>
            </aside>

            {/* Conteúdo Principal */}
            <main className="flex-1 flex flex-col overflow-hidden">
                <header className="h-16 bg-white shadow-sm flex items-center justify-between px-6 z-10">
                    <h1 className="text-xl font-bold text-gray-800">
                        {/* Título Dinâmico baseado na rota */}
                        {location.pathname === '/sensors' ? 'Gestão de Sensores' : 'Visão Geral'}
                    </h1>
                    <div className="flex items-center space-x-4">
                        <span className="text-sm text-gray-600">
                            Logado como <strong className="text-gray-800">{user?.username || 'Admin'}</strong>
                        </span>
                        <div className="h-8 w-8 rounded-full bg-iot-secondary flex items-center justify-center text-white font-bold">
                            {(user?.username || 'A')[0].toUpperCase()}
                        </div>
                    </div>
                </header>

                {/* Área de Conteúdo Injetada (Children) */}
                <div className="flex-1 overflow-auto">
                    {children}
                </div>
            </main>
        </div>
    );
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          {/* Rota Raiz (Dashboard) */}
          <Route path="/" element={
            <PrivateRoute>
              <DashboardLayout>
                 <Dashboard />
              </DashboardLayout>
            </PrivateRoute>
          } />

          {/* Rota de Sensores */}
          <Route path="/sensors" element={
            <PrivateRoute>
              <DashboardLayout>
                 <SensorTypesPage />
              </DashboardLayout>
            </PrivateRoute>
          } />
          
          {/* Detalhes (Sem Layout ou Com? Geralmente Com) */}
          <Route path="/devices/:id" element={
            <PrivateRoute>
               <DashboardLayout>
                 <DeviceDetails />
               </DashboardLayout>
            </PrivateRoute>
          } />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;