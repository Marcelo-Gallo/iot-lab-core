import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext'; // <--- Hook para pegar User e Token
import { deviceService } from '../services/deviceService';
import DeviceTable from '../components/DeviceTable';
import CreateDeviceModal from '../components/CreateDeviceModal';
import LiveChart from '../components/LiveChart'; // <--- Import do Gráfico

export default function Dashboard() {
    const { user, token } = useAuth(); // <--- Recupera o token para o WebSocket
    
    const [devices, setDevices] = useState([]);
    const [measurements, setMeasurements] = useState([]); // <--- Estado para dados Real-time
    const [stats, setStats] = useState({ total: 0, active: 0 });
    const [loadingData, setLoadingData] = useState(true);
    const [wsStatus, setWsStatus] = useState('disconnected');
    const [isModalOpen, setIsModalOpen] = useState(false);

    // 1. Efeito para carregar dados iniciais (HTTP)
    useEffect(() => {
        loadData();
    }, []);

    // 2. Efeito para Gerenciar o Ciclo de Vida do WebSocket
    useEffect(() => {
        if (!token) return;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host;
        
        // Conexão Segura: Passamos o token na Query String conforme implementado no backend
        const wsUrl = `${protocol}//${host}/api/v1/measurements/ws?token=${token}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            setWsStatus('connected');
            console.log("🔌 WS: Conectado na Org", user?.organization_id);
        };

        ws.onmessage = (event) => {
            try {
                const newData = JSON.parse(event.data);
                
                // Isolamento Vertical no Client: O servidor já filtra, mas confirmamos o ID da Org
                if (newData.organization_id === user?.organization_id) {
                    setMeasurements((prev) => {
                        const updated = [newData, ...prev];
                        return updated.slice(0, 50); // Mantém buffer de 50 pontos
                    });
                }
            } catch (err) {
                console.error("Erro ao processar mensagem WS:", err);
            }
        };

        ws.onclose = () => setWsStatus('disconnected');
        ws.onerror = () => setWsStatus('error');

        return () => ws.close(); // Cleanup ao sair da tela
    }, [token, user?.organization_id]);

    const loadData = async () => {
        try {
            const data = await deviceService.getAll();
            setDevices(data);
            const activeCount = data.filter(d => d.is_active).length;
            setStats({ total: data.length, active: activeCount });
        } catch (error) {
            console.error("Falha ao carregar dashboard:", error);
        } finally {
            setLoadingData(false);
        }
    };

    const handleCreateDevice = async (deviceData) => {
        try {
            const newDevice = await deviceService.create(deviceData);
            setDevices(prev => [newDevice, ...prev]);
            setStats(prev => ({ 
                total: prev.total + 1, 
                active: prev.active + (newDevice.is_active ? 1 : 0)
            }));
            alert("Dispositivo criado com sucesso!");
            setIsModalOpen(false);
        } catch (error) {
            alert("Erro ao criar: " + (error.response?.data?.detail || error.message));
        }
    };

    const handleDeleteDevice = async (id) => {
        if (!window.confirm("Tem certeza que deseja arquivar este dispositivo?")) return;
        try {
            await deviceService.delete(id);
            setDevices(prev => prev.map(d => d.id === id ? { ...d, is_active: false } : d));
            setStats(prev => ({ ...prev, active: prev.active - 1 }));
        } catch (error) { alert("Erro ao excluir."); }
    };

    const handleRestoreDevice = async (id) => {
        try {
            await deviceService.restore(id);
            setDevices(prev => prev.map(d => d.id === id ? { ...d, is_active: true } : d));
            setStats(prev => ({ ...prev, active: prev.active + 1 }));
        } catch (error) { alert("Erro ao restaurar."); }
    };

    return (
        <div className="p-6 bg-gray-50 min-h-screen">
            {/* Cards de KPIs */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                    <h3 className="text-gray-500 text-sm font-medium uppercase">Dispositivos Totais</h3>
                    <p className="text-3xl font-bold text-gray-800 mt-2">{loadingData ? '...' : stats.total}</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                    <h3 className="text-gray-500 text-sm font-medium uppercase">Ativos</h3>
                    <p className="text-3xl font-bold text-iot-primary mt-2">{loadingData ? '...' : stats.active}</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                    <h3 className="text-gray-500 text-sm font-medium uppercase">Real-time Stream</h3>
                    <p className={`text-lg font-bold mt-2 flex items-center ${wsStatus === 'connected' ? 'text-green-600' : 'text-red-500'}`}>
                        <span className={`h-3 w-3 rounded-full mr-2 ${wsStatus === 'connected' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
                        {wsStatus === 'connected' ? 'Conectado' : 'Desconectado'}
                    </p>
                </div>
            </div>

            {/* Gráfico Realtime */}
            <div className="mb-10">
                <LiveChart data={measurements} />
            </div>

            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-800">Meus Dispositivos</h2>
                <button 
                    onClick={() => setIsModalOpen(true)}
                    className="bg-iot-primary text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors shadow-sm flex items-center font-medium"
                >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M12 4v16m8-8H4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"></path></svg>
                    Adicionar Dispositivo
                </button>
            </div>

            {loadingData ? (
                <div className="text-center py-10"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-iot-primary mx-auto"></div></div>
            ) : (
                <DeviceTable devices={devices} onDelete={handleDeleteDevice} onRestore={handleRestoreDevice} />
            )}

            <CreateDeviceModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} onSave={handleCreateDevice} />
        </div>
    );
}