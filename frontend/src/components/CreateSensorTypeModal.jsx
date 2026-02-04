import { useState, useEffect } from 'react';

export default function CreateSensorTypeModal({ isOpen, onClose, onSave }) {
    const [formData, setFormData] = useState({
        name: '',
        unit: '',
        description: ''
    });
    const [loading, setLoading] = useState(false);

    // Limpa o formulário sempre que o modal abre
    useEffect(() => {
        if (isOpen) {
            setFormData({ name: '', unit: '', description: '' });
        }
    }, [isOpen]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await onSave(formData);
            onClose(); // Fecha apenas se der sucesso
        } catch (error) {
            // O erro é tratado no pai (Page), mas aqui garantimos que o loading pare
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6 relative animate-fade-in">
                {/* Botão Fechar (X) */}
                <button 
                    onClick={onClose}
                    className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
                >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>

                <h2 className="text-xl font-bold text-gray-800 mb-4">Novo Tipo de Sensor</h2>
                
                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Nome */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Nome do Sensor</label>
                        <input
                            type="text"
                            required
                            placeholder="Ex: Temperatura, Umidade, CO2"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                            value={formData.name}
                            onChange={(e) => setFormData({...formData, name: e.target.value})}
                        />
                    </div>

                    {/* Unidade */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Unidade de Medida</label>
                        <input
                            type="text"
                            required
                            placeholder="Ex: °C, %, PPM, V"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                            value={formData.unit}
                            onChange={(e) => setFormData({...formData, unit: e.target.value})}
                        />
                    </div>

                    {/* Descrição */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Descrição (Opcional)</label>
                        <textarea
                            rows="3"
                            placeholder="Detalhes técnicos sobre este tipo de sensor..."
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all resize-none"
                            value={formData.description}
                            onChange={(e) => setFormData({...formData, description: e.target.value})}
                        />
                    </div>

                    {/* Footer com Ações */}
                    <div className="flex justify-end space-x-3 mt-6 pt-4 border-t border-gray-100">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors font-medium"
                            disabled={loading}
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            className="px-4 py-2 text-white bg-iot-primary rounded-lg hover:bg-blue-600 transition-colors font-medium flex items-center shadow-sm disabled:opacity-70 disabled:cursor-not-allowed"
                            disabled={loading}
                        >
                            {loading ? (
                                <>
                                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                    Salvando...
                                </>
                            ) : 'Criar Sensor'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}