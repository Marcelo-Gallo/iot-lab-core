import { useNavigate } from 'react-router-dom';

export default function DeviceTable({ devices, onDelete, onRestore }) {
    const navigate = useNavigate();
    
    // Ícones (SVG Nativo)
    const EyeIcon = () => (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>
    );
    
    const TrashIcon = () => (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
    );

    const RestoreIcon = () => (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"></path></svg>
    );

    if (!devices || devices.length === 0) {
        return (
            <div className="text-center p-8 bg-white rounded-lg border border-gray-200 text-gray-500">
                Nenhum dispositivo encontrado.
            </div>
        );
    }

    // Função auxiliar para definir o estilo e texto do Status
    const getStatusBadge = (device) => {
        if (device.deleted_at) {
            return (
                <span className="px-2 py-1 rounded-full text-xs font-bold bg-gray-100 text-gray-500 border border-gray-200">
                    ARQUIVADO
                </span>
            );
        }
        
        return (
            <span className={`px-2 py-1 rounded-full text-xs font-bold border ${
                device.is_active 
                ? 'bg-green-100 text-green-700 border-green-200' 
                : 'bg-red-100 text-red-700 border-red-200'
            }`}>
                {device.is_active ? 'ATIVO' : 'INATIVO'}
            </span>
        );
    };

    return (
        <div className="bg-white rounded-lg shadow-sm overflow-hidden border border-gray-100">
            <table className="w-full text-left border-collapse">
                <thead>
                    <tr className="bg-gray-50 border-b border-gray-200 text-xs uppercase text-gray-500 font-semibold">
                        <th className="p-4">Nome</th>
                        <th className="p-4">Localização</th>
                        <th className="p-4">Status</th>
                        <th className="p-4 text-right">Ações</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                    {devices.map((device) => {
                        const isArchived = !!device.deleted_at;
                        
                        return (
                            <tr key={device.id} className={`transition-colors ${isArchived ? 'bg-gray-50 opacity-60' : 'hover:bg-gray-50'}`}>
                                <td className="p-4 font-medium text-gray-800">
                                    {device.name}
                                    <br/>
                                    <span className="text-xs font-normal text-gray-400">@{device.slug}</span>
                                </td>
                                <td className="p-4 text-gray-600">{device.location || '-'}</td>
                                <td className="p-4">
                                    {getStatusBadge(device)}
                                </td>
                                <td className="p-4 text-right flex justify-end space-x-3">
                                    <button
                                        onClick={() => navigate(`/devices/${device.id}`)}
                                        className="text-iot-primary hover:text-blue-800 p-1 rounded hover:bg-blue-50 transition-colors"
                                        title="Ver Detalhes"
                                    >
                                        <EyeIcon />
                                    </button>

                                    {isArchived ? (
                                        <button
                                            onClick={() => onRestore(device.id)}
                                            className="text-green-500 hover:text-green-700 p-1 rounded hover:bg-green-50 transition-colors"
                                            title="Restaurar Dispositivo"
                                        >
                                            <RestoreIcon />
                                        </button>
                                    ) : (
                                        <button
                                            onClick={() => onDelete(device.id)}
                                            className="text-red-400 hover:text-red-700 p-1 rounded hover:bg-red-50 transition-colors"
                                            title="Arquivar Dispositivo"
                                        >
                                            <TrashIcon />
                                        </button>
                                    )}
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}