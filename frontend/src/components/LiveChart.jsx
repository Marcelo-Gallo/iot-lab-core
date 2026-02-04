import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 border border-gray-200 shadow-lg rounded text-sm">
        <p className="font-bold text-gray-700">{format(new Date(label), 'HH:mm:ss')}</p>
        <p className="text-iot-primary">
          Valor: <span className="font-mono font-bold">{payload[0].value}</span>
        </p>
      </div>
    );
  }
  return null;
};

export default function LiveChart({ data, sensorName }) {
  if (!data || data.length === 0) {
    return (
      <div className="h-72 w-full flex items-center justify-center bg-gray-50 rounded-xl border border-dashed border-gray-300 text-gray-400">
        <div className="text-center">
          <p className="text-lg">📡 Aguardando dados...</p>
          <p className="text-xs mt-2">O dispositivo ainda não enviou medições.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-80 w-full bg-white p-4 rounded-xl border border-gray-100 shadow-sm mb-6">
      <h3 className="text-sm font-bold text-gray-500 mb-4 uppercase tracking-wider flex justify-between">
        <span>Telemetria em Tempo Real</span>
        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">Ao Vivo</span>
      </h3>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
          <XAxis 
            dataKey="created_at" 
            tickFormatter={(str) => format(new Date(str), 'HH:mm')}
            stroke="#9ca3af"
            fontSize={12}
            tickMargin={10}
            minTickGap={30}
          />
          <YAxis 
            stroke="#9ca3af" 
            fontSize={12}
            width={40}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line 
            type="monotone" 
            dataKey="value" 
            stroke="#2563eb" 
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6, strokeWidth: 0 }}
            animationDuration={300}
            isAnimationActive={true}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}