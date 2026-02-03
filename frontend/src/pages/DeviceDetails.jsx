import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { deviceService } from '../services/deviceService';
import { sensorService } from '../services/sensorService';
import { measurementService } from '../services/measurementService'; 
import LiveChart from '../components/LiveChart'; 

export default function DeviceDetails() {
    const { id } = useParams();
    const navigate = useNavigate();

    // --- Estados Principais ---
    const [device, setDevice] = useState(null);
    const [tokens, setTokens] = useState([]);
    const [loading, setLoading] = useState(true);
    
    // --- Estados da Telemetria ---
    const [measurements, setMeasurements] = useState([]);
    const [timeRange, setTimeRange] = useState('realtime'); // realtime, 1h, 24h, 7d

    // --- Estados de UI/Formulários ---
    const [newTokenLabel, setNewTokenLabel] = useState('');
    const [allSensors, setAllSensors] = useState([]); 
    const [selectedSensors, setSelectedSensors] = useState([]); 
    const [isSavingSensors, setIsSavingSensors] = useState(false);

    // Função de Polling (Busca dados periodicamente)
    const fetchTelemetry = useCallback(async () => {
        try {
            let params = { limit: 100 };
            
            // Calcula a data de início baseada no filtro selecionado
            if (timeRange !== 'realtime') {
                const now = new Date();
                let past = new Date();
                
                if (timeRange === '1h') past.setHours(now.getHours() - 1);
                if (timeRange === '24h') past.setHours(now.getHours() - 24);
                if (timeRange === '7d') past.setDate(now.getDate() - 7);
                
                params.startDate = past;
                params.limit = 1000; // Aumenta limite para trazer histórico detalhado
            }

            const data = await measurementService.getByDevice(id, params);
            
            // Ordenação Cronológica (Antigo -> Novo) para o gráfico desenhar da esq -> dir
            const sortedData = data.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
            setMeasurements(sortedData);
        } catch (error) {
            console.error("Erro no polling:", error);
        }
    }, [id, timeRange]);

    // Carga Inicial de Dados (Roda 1 vez)
    useEffect(() => {
        async function loadData() {
            try {
                const [deviceData, tokenData, sensorTypesData] = await Promise.all([
                    deviceService.getById(id),
                    deviceService.getTokens(id),
                    sensorService.getAllTypes()
                ]);

                setDevice(deviceData);
                setTokens(tokenData);
                setAllSensors(sensorTypesData);

                if (deviceData.sensors) {
                    setSelectedSensors(deviceData.sensors.map(s => s.id));
                }

                // Busca inicial do gráfico
                await fetchTelemetry();

            } catch (error) {
                console.error("Erro ao carregar:", error);
                alert("Erro ao carregar detalhes do dispositivo.");
            } finally {
                setLoading(false);
            }
        }
        loadData();
    }, [id, fetchTelemetry]);

    // Configuração do Polling (Intervalo)
    useEffect(() => {
        if (timeRange === 'realtime') {
            fetchTelemetry(); // Chama imediatamente ao entrar no modo
            const interval = setInterval(fetchTelemetry, 5000); // Roda a cada 5s
            return () => clearInterval(interval);
        } else {
            // Se for histórico (ex: 24h), busca só uma vez e para (não gasta banda)
            fetchTelemetry();
        }
    }, [fetchTelemetry, timeRange]);

    // --- Ações de UI ---
    const handleGenerateToken = async (e) => {
        e.preventDefault();
        if (!newTokenLabel) return;
        try {
            const token = await deviceService.createToken(id, newTokenLabel);
            setTokens([...tokens, token]);
            setNewTokenLabel('');
            alert(`Token criado! Copie agora: ${token.token}`);
        } catch (error) {
            alert("Erro ao criar token");
        }
    };

    const handleSaveSensors = async () => {
        setIsSavingSensors(true);
        try {
            await deviceService.updateSensors(id, selectedSensors);
            alert("Configuração de sensores atualizada com sucesso!");
            const updatedDevice = await deviceService.getById(id);
            setDevice(updatedDevice);
        } catch (error) {
            alert("Erro ao salvar sensores.");
        } finally {
            setIsSavingSensors(false);
        }
    };

    const toggleSensor = (sensorId) => {
        setSelectedSensors(prev =>
            prev.includes(sensorId)
                ? prev.filter(id => id !== sensorId)
                : [...prev, sensorId]
        );
    };

    if (loading) return (
        <div className="flex flex-col items-center justify-center min-h-screen text-gray-500">
             <div className="animate-spin h-8 w-8 border-4 border-blue-500 rounded-full border-t-transparent mb-4"></div>
             <p>Carregando Central de Controle...</p>
        </div>
    );
    
    if (!device) return null;

    return (
        <div className="p-6 max-w-6xl mx-auto space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-gray-100 pb-6">
                <div className="flex items-center">
                    <button onClick={() => navigate('/')} className="mr-4 p-2 hover:bg-gray-100 rounded-full transition-colors text-gray-500">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
                    </button>
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800">{device.name}</h1>
                        <p className="text-gray-500 font-mono text-sm mt-1">ID: {device.slug} • Local: {device.location}</p>
                    </div>
                </div>
                <span className={`px-4 py-1.5 rounded-full text-sm font-bold border ${device.is_active ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-700 border-red-200'}`}>
                    {device.is_active ? 'ONLINE' : 'OFFLINE'}
                </span>
            </div>

            {/* 🛠️ ÁREA DO GRÁFICO COM BOTÕES (O que faltava) */}
            <div>
                 {/* Barra de Ferramentas do Gráfico */}
                <div className="flex items-center justify-end space-x-2 mb-2">
                    <span className="text-xs text-gray-500 font-bold uppercase mr-2">Visualização:</span>
                    
                    {['realtime', '1h', '24h', '7d'].map((range) => (
                        <button
                            key={range}
                            onClick={() => setTimeRange(range)}
                            className={`px-3 py-1 text-xs font-bold rounded-md transition-all 
                                ${timeRange === range 
                                    ? 'bg-blue-600 text-white shadow-md' 
                                    : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                                }`}
                        >
                            {range === 'realtime' ? '🔴 Ao Vivo' : range.toUpperCase()}
                        </button>
                    ))}
                </div>

                {/* Componente Gráfico */}
                <LiveChart 
                    data={measurements} 
                    sensorName={timeRange === 'realtime' ? 'Últimas Leituras (Ao Vivo)' : 'Histórico Consolidado'} 
                />
            </div>

            {/* Grid de Configuração */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                {/* Card 1: Tokens */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                    <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
                        <svg className="w-5 h-5 mr-2 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"></path></svg>
                        Chaves de Acesso
                    </h2>
                    
                    <div className="space-y-3 mb-6">
                        {tokens.length === 0 ? (
                            <p className="text-gray-400 text-sm italic">Nenhum token gerado.</p>
                        ) : (
                            tokens.map((t) => (
                                <div key={t.id} className="flex items-center justify-between bg-gray-50 p-3 rounded border border-gray-200">
                                    <span className="font-bold text-sm text-gray-700">{t.label}</span>
                                    <div className="flex items-center space-x-2">
                                        <code className="bg-white px-2 py-1 rounded border text-xs text-gray-600">{t.token.substring(0, 8)}...</code>
                                        <button onClick={() => {navigator.clipboard.writeText(t.token); alert("Copiado!")}} className="text-blue-600 text-xs font-bold hover:underline">COPIAR</button>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    <form onSubmit={handleGenerateToken} className="flex gap-2">
                        <input
                            type="text"
                            placeholder="Nome da chave (Ex: ESP32 Lab)"
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500"
                            value={newTokenLabel}
                            onChange={(e) => setNewTokenLabel(e.target.value)}
                            required
                        />
                        <button type="submit" className="bg-gray-900 text-white px-4 py-2 rounded-lg text-sm hover:bg-black font-medium">
                            Gerar
                        </button>
                    </form>
                </div>

                {/* Card 2: Sensores */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                    <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
                        <svg className="w-5 h-5 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path></svg>
                        Sensores Conectados
                    </h2>

                    <div className="space-y-2 mb-6 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                        {allSensors.map((sensor) => {
                            const isSelected = selectedSensors.includes(sensor.id);
                            return (
                                <div
                                    key={sensor.id}
                                    onClick={() => toggleSensor(sensor.id)}
                                    className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-all ${isSelected ? 'bg-blue-50 border-blue-500 ring-1 ring-blue-500' : 'bg-white border-gray-200 hover:border-gray-300'}`}
                                >
                                    <span className="font-bold text-gray-700 text-sm">{sensor.name} <span className="font-normal text-gray-400 text-xs">({sensor.unit})</span></span>
                                    <div className={`w-4 h-4 rounded border flex items-center justify-center ${isSelected ? 'bg-blue-500 border-blue-500' : 'border-gray-300 bg-white'}`}>
                                        {isSelected && <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path></svg>}
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    <div className="flex justify-end pt-4 border-t border-gray-100">
                        <button
                            onClick={handleSaveSensors}
                            disabled={isSavingSensors}
                            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium shadow-sm disabled:opacity-50"
                        >
                            {isSavingSensors ? 'Salvando...' : 'Salvar Sensores'}
                        </button>
                    </div>
                </div>

            </div>
        </div>
    );
}