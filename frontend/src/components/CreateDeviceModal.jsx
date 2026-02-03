import { useState, useEffect } from 'react';

export default function CreateDeviceModal({ isOpen, onClose, onSave }) {
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [location, setLocation] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSlugEdited, setIsSlugEdited] = useState(false);

  // ✅ CORREÇÃO: O useEffect agora está ANTES do return condicional.
  // Ele sempre será registrado pelo React, independente do modal estar aberto ou não.
  useEffect(() => {
    // Só executamos a lógica interna se o modal estiver aberto e o usuário não tiver editado manualmente
    if (isOpen && !isSlugEdited && name) {
      const generatedSlug = name
        .toLowerCase()
        .normalize("NFD").replace(/[\u0300-\u036f]/g, "") 
        .replace(/[^a-z0-9]/g, "-") 
        .replace(/-+/g, "-") 
        .replace(/^-|-$/g, ""); 
      
      setSlug(generatedSlug);
    }
  }, [name, isSlugEdited, isOpen]); // Adicionado isOpen nas dependências por boa prática

  // ✅ Agora sim, podemos abortar a renderização visual se estiver fechado
  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    await onSave({ 
      name, 
      slug, 
      location,
      is_battery_powered: false,
      sensor_ids: [] 
    });
    
    setName('');
    setSlug('');
    setLocation('');
    setIsSlugEdited(false);
    setIsSubmitting(false);
    onClose();
  };

  return (
    // Adicionei a animação 'animate-fade-in-down' que configuramos no tailwind.config.js
    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-auto bg-black bg-opacity-50 backdrop-blur-sm">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-md mx-4 transform transition-all animate-fade-in-down">
        
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-100 flex justify-between items-center">
          <h3 className="text-lg font-bold text-gray-800">Novo Dispositivo</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nome Identificador</label>
            <input 
              type="text" 
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: Sensor Estufa 01"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-iot-primary focus:border-transparent outline-none transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Slug (ID do Sistema)
              <span className="text-xs text-gray-400 ml-2 font-normal">Único e sem espaços</span>
            </label>
            <div className="relative">
              <input 
                type="text" 
                required
                value={slug}
                onChange={(e) => {
                  setSlug(e.target.value);
                  setIsSlugEdited(true);
                }}
                placeholder="sensor-estufa-01"
                className="w-full px-4 py-2 border border-gray-300 bg-gray-50 rounded-lg focus:ring-2 focus:ring-iot-primary focus:border-transparent outline-none transition-all font-mono text-sm text-gray-600"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Localização Física</label>
            <input 
              type="text" 
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Ex: Bloco B - Laboratório 3"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-iot-primary focus:border-transparent outline-none transition-all"
            />
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button 
              type="button" 
              onClick={onClose}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
            >
              Cancelar
            </button>
            <button 
              type="submit" 
              disabled={isSubmitting}
              className="px-4 py-2 bg-iot-primary text-white rounded-lg hover:bg-blue-600 transition-colors font-medium shadow-md flex items-center"
            >
              {isSubmitting ? 'Salvando...' : 'Criar Dispositivo'}
            </button>
          </div>
        </form>

      </div>
    </div>
  );
}