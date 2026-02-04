import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { deviceService } from '../services/deviceService';
import { measurementService } from '../services/measurementService'; 
import LiveChart from '../components/LiveChart'; 
import AddSensorModal from '../components/AddSensorModal'; // <--- IMPORTADO

export default function DeviceDetails() {
    const { id } = useParams();
    const navigate = useNavigate();

    // --- Estados ---
    const [device, setDevice] = useState(null);
    const [tokens, setTokens] = useState([]);
    const [loading, setLoading] = useState(true);
    const [measurements, setMeasurements] = useState([]);
    const [timeRange, setTimeRange] = useState('realtime');
    
    // UI
    const [newTokenLabel, setNewTokenLabel] = useState('');
    const [isSensorModalOpen, setIsSensorModalOpen] = useState(false); // Modal state

    // --- Polling de Telemetria ---
    const fetchTelemetry = useCallback(async () => {
        try {
            let params = { limit: 100 };
            if (timeRange !== 'realtime') {
                const now = new Date();
                let past = new Date();
                if (timeRange === '1h') past.setHours(now.getHours() - 1);
                if (timeRange === '24h') past.setHours(now.getHours() - 24);
                if (timeRange === '7d') past.setDate(now.getDate() - 7);
                params.startDate = past;
                params.limit = 1000; 
            }
            const data = await measurementService.getByDevice(id, params);
            const sortedData = data.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
            setMeasurements(sortedData);
        } catch (error) {
            console.error("Erro no polling:", error);
        }
    }, [id, timeRange]);

    // --- Carga Inicial ---
    const loadData = useCallback(async () => {
        try {
            const [deviceData, tokenData] = await Promise.all([
                deviceService.getById(id),
                deviceService.getTokens(id)
            ]);
            setDevice(deviceData);
            setTokens(tokenData);
            await fetchTelemetry();
        } catch (error) {
            console.error("Erro ao carregar:", error);
            alert("Erro ao carregar detalhes.");
        } finally {
            setLoading(false);
        }
    }, [id, fetchTelemetry]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    // Polling Effect
    useEffect(() => {
        if (timeRange === 'realtime') {
            const interval = setInterval(fetchTelemetry, 5000);
            return () => clearInterval(interval);
        }
    }, [fetchTelemetry, timeRange]);

    // --- Handlers ---
    const handleGenerateToken = async (e) => {
        e.preventDefault();
        if (!newTokenLabel) return;
        try {
            const token = await deviceService.createToken(id, newTokenLabel);
            setTokens([...tokens, token]);
            setNewTokenLabel('');
            alert(`Token criado: ${token.token}`);
        } catch (error) {
            alert("Erro ao criar token");
        }
    };

    // Adicionar Sensor via Modal (com fórmula)
    const handleAddSensor = async (sensorData) => {
        try {
            // Pega os sensores atuais e adiciona o novo
            // Nota: O backend apaga e recria, então precisamos mandar TUDO o que queremos manter + o novo
            const currentSensors = device.sensors || [];
            
            // Verifica se já existe para evitar duplicação
            if (currentSensors.find(s => s.id === sensorData.sensor_type_id)) {
                alert("Este sensor já está vinculado. Para editar a fórmula, remova e adicione novamente.");
                return;
            }

            // Monta o payload misturando os existentes (IDs) com o novo (Objeto)
            const payload = [
                ...currentSensors.map(s => s.id), // Mantém os antigos
                sensorData // Adiciona o novo { sensor_type_id, calibration_formula }
            ];

            await deviceService.updateSensors(id, payload);
            
            // Recarrega os dados para atualizar a lista
            const updatedDevice = await deviceService.getById(id);
            setDevice(updatedDevice);
            alert("Sensor vinculado com sucesso!");
        } catch (error) {
            alert("Erro ao vincular sensor: " + error.response?.data?.detail || error.message);
        }
    };

    // Remover Sensor
    const handleRemoveSensor = async (sensorId) => {
        if (!window.confirm("Remover este sensor do dispositivo?")) return;
        try {
            const currentSensors = device.sensors || [];
            // Filtra removendo o ID selecionado
            const payload = currentSensors
                .filter(s => s.id !== sensorId)
                .map(s => s.id);

            await deviceService.updateSensors(id, payload);
            
            // Atualiza UI
            const updatedDevice = await deviceService.getById(id);
            setDevice(updatedDevice);
        } catch (error) {
            alert("Erro ao remover sensor.");
        }
    };

    if (loading) return <div className="p-10 text-center">Carregando...</div>;
    if (!device) return null;

    return (
        <div className="p-6 max-w-6xl mx-auto space-y-8 animate-fade-in">
            {/* Cabeçalho */}
            <div className="flex items-center justify-between border-b border-gray-100 pb-6">
                <div className="flex items-center">
                    <button onClick={() => navigate('/')} className="mr-4 p-2 hover:bg-gray-100 rounded-full transition-colors text-gray-500">
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
                    </button>
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800">{device.name}</h1>
                        <p className="text-gray-500 font-mono text-sm mt-1">ID: {device.slug} • {device.location}</p>
                    </div>
                </div>
                <span className={`px-4 py-1.5 rounded-full text-sm font-bold border ${device.is_active ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-700 border-red-200'}`}>
                    {device.is_active ? 'ONLINE' : 'OFFLINE'}
                </span>
            </div>

            {/* Gráfico */}
            <div className="bg-white p-1 rounded-xl">
                 <div className="flex justify-end space-x-2 mb-2">
                    {['realtime', '1h', '24h', '7d'].map((range) => (
                        <button key={range} onClick={() => setTimeRange(range)} className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${timeRange === range ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'}`}>
                            {range === 'realtime' ? 'Ao Vivo' : range.toUpperCase()}
                        </button>
                    ))}
                </div>
                <LiveChart data={measurements} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* Card Sensores (Atualizado) */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-bold text-gray-800 flex items-center">
                            <svg className="w-5 h-5 mr-2 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" /></svg>
                            Sensores
                        </h2>
                        <button 
                            onClick={() => setIsSensorModalOpen(true)}
                            className="text-sm bg-blue-50 text-blue-600 px-3 py-1.5 rounded-lg hover:bg-blue-100 font-medium transition-colors"
                        >
                            + Adicionar
                        </button>
                    </div>

                    <div className="space-y-3">
                        {(!device.sensors || device.sensors.length === 0) ? (
                            <p className="text-gray-400 text-sm italic text-center py-4">Nenhum sensor vinculado.</p>
                        ) : (
                            device.sensors.map((sensor) => (
                                <div key={sensor.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100">
                                    <div>
                                        <p className="font-bold text-gray-700 text-sm">{sensor.name}</p>
                                        <p className="text-xs text-gray-500 font-mono">
                                            {sensor.unit} 
                                            {/* Aqui futuramente podemos mostrar a fórmula se o backend retornar no GET */}
                                        </p>
                                    </div>
                                    <button 
                                        onClick={() => handleRemoveSensor(sensor.id)}
                                        className="text-red-400 hover:text-red-600 p-1 rounded hover:bg-red-50"
                                        title="Desvincular"
                                    >
                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                    </button>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Card Tokens */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                    <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
                        <svg className="w-5 h-5 mr-2 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" /></svg>
                        Chaves de Acesso
                    </h2>
                    <div className="space-y-3 mb-6">
                        {tokens.map((t) => (
                            <div key={t.id} className="flex items-center justify-between bg-gray-50 p-3 rounded border border-gray-200">
                                <span className="font-bold text-sm text-gray-700">{t.label}</span>
                                <div className="flex space-x-2">
                                    <code className="text-xs bg-white px-1 py-0.5 rounded border">{t.token.substring(0,6)}...</code>
                                    <button onClick={() => navigator.clipboard.writeText(t.token)} className="text-xs text-blue-600 font-bold">COPIAR</button>
                                </div>
                            </div>
                        ))}
                         {tokens.length === 0 && <p className="text-gray-400 text-sm italic">Nenhum token.</p>}
                    </div>
                    <form onSubmit={handleGenerateToken} className="flex gap-2">
                        <input type="text" placeholder="Nome da chave" className="flex-1 px-3 py-2 border rounded-lg text-sm" value={newTokenLabel} onChange={e => setNewTokenLabel(e.target.value)} required />
                        <button className="bg-gray-800 text-white px-4 py-2 rounded-lg text-sm">Gerar</button>
                    </form>
                </div>
            </div>

            {/* Modal de Sensores */}
            <AddSensorModal 
                isOpen={isSensorModalOpen} 
                onClose={() => setIsSensorModalOpen(false)} 
                onSave={handleAddSensor} 
            />
        </div>
    );
}