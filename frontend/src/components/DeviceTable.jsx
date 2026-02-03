import { useNavigate } from 'react-router-dom';

export default function DeviceTable({ devices }) {
    const navigate = useNavigate();
    if (!devices || devices.length === 0) {
        return (
            <div className="text-center p-8 bg-white rounded-lg border border-gray-200 text-gray-500">
                Nenhum dispositivo encontrado.
            </div>
        );
    }

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
                    {devices.map((device) => (
                        <tr key={device.id} className="hover:bg-gray-50 transition-colors">
                            <td className="p-4 font-medium text-gray-800">{device.name}</td>
                            <td className="p-4 text-gray-600">{device.location}</td>
                            <td className="p-4">
                                <span className={`px-2 py-1 rounded-full text-xs font-bold 
                  ${device.is_active
                                        ? 'bg-green-100 text-green-700'
                                        : 'bg-red-100 text-red-700'}`}>
                                    {device.is_active ? 'ATIVO' : 'INATIVO'}
                                </span>
                            </td>
                            <td className="p-4 text-right">
                                <button
                                    onClick={() => navigate(`/devices/${device.id}`)}
                                    className="text-iot-primary hover:text-blue-700 text-sm font-medium"
                                >
                                    Detalhes
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}