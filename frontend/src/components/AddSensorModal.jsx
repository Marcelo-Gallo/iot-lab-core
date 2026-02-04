import { useState, useEffect } from 'react';
import { sensorService } from '../services/sensorService';

export default function AddSensorModal({ isOpen, onClose, onSave }) {
    const [sensors, setSensors] = useState([]);
    const [selectedSensor, setSelectedSensor] = useState('');
    const [formula, setFormula] = useState('');
    const [loading, setLoading] = useState(false);
    const [loadingSensors, setLoadingSensors] = useState(true);

    // Carrega sensores ao abrir o modal
    useEffect(() => {
        if (isOpen) {
            loadSensors();
            setFormula('');
            setSelectedSensor('');
        }
    }, [isOpen]);

    const loadSensors = async () => {
        setLoadingSensors(true);
        try {
            const data = await sensorService.getAll();
            // Filtra apenas os ativos para novas vinculações
            setSensors(data.filter(s => s.is_active));
        } catch (error) {
            console.error("Erro ao carregar sensores", error);
        } finally {
            setLoadingSensors(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!selectedSensor) return;

        setLoading(true);
        try {
            // Envia o objeto completo para o pai
            await onSave({ 
                sensor_type_id: parseInt(selectedSensor), 
                calibration_formula: formula.trim() || null 
            });
            onClose();
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6 animate-fade-in relative">
                <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>

                <h2 className="text-xl font-bold text-gray-800 mb-4">Adicionar Sensor</h2>
                
                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Seleção de Sensor */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Sensor</label>
                        {loadingSensors ? (
                            <div className="animate-pulse h-10 bg-gray-100 rounded"></div>
                        ) : (
                            <select
                                required
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                value={selectedSensor}
                                onChange={(e) => setSelectedSensor(e.target.value)}
                            >
                                <option value="">Selecione um tipo...</option>
                                {sensors.map(s => (
                                    <option key={s.id} value={s.id}>{s.name} ({s.unit})</option>
                                ))}
                            </select>
                        )}
                    </div>

                    {/* Campo de Fórmula */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Fórmula de Calibração (Opcional)
                        </label>
                        <div className="relative">
                            <input
                                type="text"
                                placeholder="Ex: x * 0.1 + 5"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                                value={formula}
                                onChange={(e) => setFormula(e.target.value)}
                            />
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                            Use <b>x</b> como o valor bruto recebido do dispositivo.
                        </p>
                    </div>

                    <div className="flex justify-end pt-4">
                        <button
                            type="submit"
                            disabled={loading || !selectedSensor}
                            className="bg-iot-primary text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 font-medium"
                        >
                            {loading ? 'Salvando...' : 'Vincular Sensor'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}