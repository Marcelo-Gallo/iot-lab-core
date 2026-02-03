import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { deviceService } from '../services/deviceService';
import { sensorService } from '../services/sensorService';

export default function DeviceDetails() {
    const { id } = useParams(); // Pega o ID da URL (ex: /devices/1)
    const navigate = useNavigate();

    const [device, setDevice] = useState(null);
    const [tokens, setTokens] = useState([]);
    const [loading, setLoading] = useState(true);
    const [newTokenLabel, setNewTokenLabel] = useState('');

    const [allSensors, setAllSensors] = useState([]); // Catálogo completo
    const [selectedSensors, setSelectedSensors] = useState([]); // IDs selecionados
    const [isSavingSensors, setIsSavingSensors] = useState(false);

    // Carrega dados iniciais
    useEffect(() => {
        async function loadData() {
            try {

                const measureData = await measurementService.getByDevice(id);
                setMeasurements(measureData.reverse());

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
            } catch (error) {
                console.error("Erro ao carregar:", error);
            } finally {
                setLoading(false);
            }
        }
        loadData();
    }, [id, navigate]);

    // Função para gerar token
    const handleGenerateToken = async (e) => {
        e.preventDefault();
        if (!newTokenLabel) return;

        try {
            const token = await deviceService.createToken(id, newTokenLabel);
            setTokens([...tokens, token]); // Atualiza lista
            setNewTokenLabel('');
            alert(`Token criado! Copie agora: ${token.token}`); // UX simples por enquanto
        } catch (error) {
            alert("Erro ao criar token");
        }
    };

    // Salvar
    const handleSaveSensors = async () => {
        setIsSavingSensors(true);
        try {
            await deviceService.updateSensors(id, selectedSensors);
            alert("Configuração de sensores atualizada com sucesso!");

            // Opcional: Recarregar dados para garantir sincronia
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
                ? prev.filter(id => id !== sensorId) // Remove
                : [...prev, sensorId] // Adiciona
        );
    };

    if (loading) return <div className="p-10 text-center">Carregando Central de Controle...</div>;
    if (!device) return null;

    return (
        <div className="p-6 max-w-6xl mx-auto">
            {/* Header com Botão Voltar */}
            <div className="flex items-center mb-8">
                <button onClick={() => navigate('/')} className="mr-4 text-gray-500 hover:text-iot-primary transition-colors">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
                </button>
                <div>
                    <h1 className="text-3xl font-bold text-gray-800">{device.name}</h1>
                    <p className="text-gray-500 font-mono text-sm mt-1">ID: {device.slug} • Local: {device.location}</p>
                </div>
                <div className="ml-auto">
                    <span className={`px-3 py-1 rounded-full text-sm font-bold border ${device.is_active ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-700 border-red-200'}`}>
                        {device.is_active ? 'ONLINE' : 'OFFLINE'}
                    </span>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                {/* Card 1: Gestão de Tokens (Crítico para o Hardware) */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                    <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
                        <svg className="w-5 h-5 mr-2 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"></path></svg>
                        Chaves de Acesso (API Tokens)
                    </h2>

                    <div className="mb-6 bg-blue-50 p-4 rounded-lg text-sm text-blue-800">
                        <strong>Como usar:</strong> Copie o token abaixo e cole no código C++ do seu ESP32 (`const char* TOKEN = "..."`).
                    </div>

                    {/* Lista de Tokens */}
                    <div className="space-y-3 mb-6">
                        {tokens.length === 0 ? (
                            <p className="text-gray-400 text-sm italic">Nenhum token gerado para este dispositivo.</p>
                        ) : (
                            tokens.map((t) => (
                                <div key={t.id} className="flex items-center justify-between bg-gray-50 p-3 rounded border border-gray-200">
                                    <div>
                                        <p className="font-bold text-sm text-gray-700">{t.label}</p>
                                        <p className="font-mono text-xs text-gray-500 mt-1">Criado em: {new Date(t.created_at).toLocaleDateString()}</p>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        {/* Mostramos apenas os primeiros caracteres por segurança visual */}
                                        <code className="bg-white px-2 py-1 rounded border text-xs text-gray-600">
                                            {t.token.substring(0, 8)}...
                                        </code>
                                        <button
                                            onClick={() => { navigator.clipboard.writeText(t.token); alert("Token copiado!"); }}
                                            className="text-iot-primary hover:text-blue-700 text-xs font-bold uppercase"
                                        >
                                            Copiar
                                        </button>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    {/* Gerador de Novo Token */}
                    <form onSubmit={handleGenerateToken} className="flex gap-2">
                        <input
                            type="text"
                            placeholder="Ex: ESP32 Produção"
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-iot-primary outline-none"
                            value={newTokenLabel}
                            onChange={(e) => setNewTokenLabel(e.target.value)}
                            required
                        />
                        <button type="submit" className="bg-iot-dark text-white px-4 py-2 rounded-lg text-sm hover:bg-black transition-colors">
                            Gerar Chave
                        </button>
                    </form>
                </div>

                {/* Card 2: Configuração de Sensores */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                    <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
                        <svg className="w-5 h-5 mr-2 text-iot-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"></path></svg>
                        Sensores Conectados
                    </h2>

                    <p className="text-sm text-gray-500 mb-6">
                        Selecione quais sensores físicos estão acoplados a este microcontrolador.
                        Isso permite que o sistema processe os dados corretamente.
                    </p>

                    <div className="space-y-3 mb-6 max-h-60 overflow-y-auto pr-2">
                        {allSensors.map((sensor) => {
                            const isSelected = selectedSensors.includes(sensor.id);
                            return (
                                <div
                                    key={sensor.id}
                                    onClick={() => toggleSensor(sensor.id)}
                                    className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-all
                        ${isSelected
                                            ? 'bg-blue-50 border-iot-primary ring-1 ring-iot-primary'
                                            : 'bg-white border-gray-200 hover:border-gray-300'}`}
                                >
                                    <div className="flex items-center">
                                        <div className={`w-5 h-5 rounded border flex items-center justify-center mr-3
                            ${isSelected ? 'bg-iot-primary border-iot-primary' : 'border-gray-300 bg-white'}`}>
                                            {isSelected && <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path></svg>}
                                        </div>
                                        <div>
                                            <p className="font-bold text-gray-700">{sensor.name}</p>
                                            <p className="text-xs text-gray-500">{sensor.unit} • {sensor.description}</p>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    <div className="flex justify-end pt-4 border-t border-gray-100">
                        <button
                            onClick={handleSaveSensors}
                            disabled={isSavingSensors}
                            className="bg-iot-primary text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors shadow-sm font-medium flex items-center"
                        >
                            {isSavingSensors ? 'Salvando...' : 'Salvar Configuração'}
                        </button>
                    </div>
                </div>

            </div>

        </div>
    );
}