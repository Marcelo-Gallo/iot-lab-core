import { useState, useEffect } from 'react';
import { deviceService } from '../services/deviceService';
import DeviceTable from '../components/DeviceTable';
import CreateDeviceModal from '../components/CreateDeviceModal';

export default function Dashboard() {
    // Estados para armazenar dados reais
    const [devices, setDevices] = useState([]);
    const [stats, setStats] = useState({ total: 0, active: 0 });
    const [loadingData, setLoadingData] = useState(true);

    // Estado do Modal
    const [isModalOpen, setIsModalOpen] = useState(false);

    // Efeito para carregar dados ao abrir a tela (Read)
    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const data = await deviceService.getAll();
            setDevices(data);
            
            // Calcula estatísticas
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
    };

    // Lógica de criação (Create)
    const handleCreateDevice = async (deviceData) => {
        try {
            const newDevice = await deviceService.create(deviceData);
            
            setDevices(prev => [newDevice, ...prev]);
            
            setStats(prev => ({ 
                total: prev.total + 1, 
                active: prev.active + (newDevice.is_active ? 1 : 0)
            }));

            alert("Dispositivo criado com sucesso!"); 
        } catch (error) {
            alert("Erro ao criar dispositivo: " + (error.response?.data?.detail || error.message));
        }
    };

    // Lógica de Exclusão (Soft Delete)
    const handleDeleteDevice = async (id) => {
        if (!window.confirm("Tem certeza que deseja arquivar este dispositivo?")) return;
        
        try {
            await deviceService.delete(id);
            
            setDevices(prev => prev.map(device => 
                device.id === id 
                ? { ...device, is_active: false, deleted_at: new Date().toISOString() } 
                : device
            ));
            
            setStats(prev => ({
                ...prev,
                active: prev.active - (devices.find(d => d.id === id)?.is_active ? 1 : 0)
            }));
        } catch (error) {
            alert("Erro ao excluir.");
        }
    };

    // Lógica de Restauração (Restore)
    const handleRestoreDevice = async (id) => {
        try {
            await deviceService.restore(id);
            setDevices(prev => prev.map(dev => 
                dev.id === id 
                ? { ...dev, deleted_at: null, is_active: true } 
                : dev
            ));
            setStats(prev => ({ ...prev, active: prev.active + 1 }));
        } catch (error) {
            alert("Erro ao restaurar.");
        }
    };

    return (
        <div className="p-6">
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

            {/* Cabeçalho da Tabela + Botão */}
            <div className="flex justify-between items-center mb-4 mt-8">
                <h2 className="text-xl font-bold text-gray-800">Meus Dispositivos</h2>
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
                <DeviceTable 
                    devices={devices} 
                    onDelete={handleDeleteDevice} 
                    onRestore={handleRestoreDevice}
                />
            )}

            {/* Modal */}
            <CreateDeviceModal 
                isOpen={isModalOpen} 
                onClose={() => setIsModalOpen(false)} 
                onSave={handleCreateDevice} 
            />
        </div>
    );
}