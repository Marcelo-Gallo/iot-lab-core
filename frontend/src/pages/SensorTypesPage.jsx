import { useState, useEffect } from 'react';
import { sensorService } from '../services/sensorService';
import SensorTable from '../components/SensorTable';
import CreateSensorTypeModal from '../components/CreateSensorTypeModal';

export default function SensorTypesPage() {
    const [sensors, setSensors] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);

    // Carregar dados
    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const data = await sensorService.getAll();
            setSensors(data);
        } catch (error) {
            console.error("Falha ao carregar sensores:", error);
        } finally {
            setLoading(false);
        }
    };

    // Lógica de Criação (NOVA)
    const handleCreate = async (sensorData) => {
        try {
            const newSensor = await sensorService.create(sensorData);
            
            // Atualiza a lista localmente (adiciona no topo ou fim)
            setSensors(prev => [...prev, newSensor]);
            
            alert("Tipo de sensor criado com sucesso!");
        } catch (error) {
            const msg = error.response?.data?.detail || error.message;
            alert("Erro ao criar sensor: " + msg);
            throw error; // Lança erro para o modal saber que falhou e não fechar (se quiser)
        }
    };

    // Lógica de Soft Delete (Otimista)
    const handleDelete = async (id) => {
        if (!window.confirm("Deseja arquivar este tipo de sensor?")) return;

        try {
            await sensorService.delete(id);
            setSensors(prev => prev.map(s => 
                s.id === id 
                ? { ...s, is_active: false, deleted_at: new Date().toISOString() } 
                : s
            ));
        } catch (error) {
            alert("Erro ao arquivar.");
        }
    };

    // Lógica de Restore (Otimista)
    const handleRestore = async (id) => {
        try {
            await sensorService.restore(id);
            setSensors(prev => prev.map(s => 
                s.id === id 
                ? { ...s, is_active: true, deleted_at: null } 
                : s
            ));
        } catch (error) {
            alert("Erro ao restaurar.");
        }
    };

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">Tipos de Sensores</h1>
                
                {/* Botão abre o Modal */}
                <button 
                    onClick={() => setIsModalOpen(true)}
                    className="bg-iot-primary text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors shadow-sm font-medium flex items-center"
                >
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"></path></svg>
                    Novo Tipo
                </button>
            </div>

            {loading ? (
                <div className="text-center py-10">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-iot-primary mx-auto"></div>
                </div>
            ) : (
                <SensorTable 
                    sensors={sensors} 
                    onDelete={handleDelete} 
                    onRestore={handleRestore}
                />
            )}

            {/* Modal de Criação */}
            <CreateSensorTypeModal 
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSave={handleCreate}
            />
        </div>
    );
}