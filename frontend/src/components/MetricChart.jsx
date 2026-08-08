import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';

export default function MetricChart({ data, label, unit, color = '#06b6d4' }) {
  const formattedData = (data || []).map((item) => ({
    hour: item.hour ? item.hour.replace(/.*T/, '') : '',
    value: item.value ?? 0,
  }));

  const CustomTooltip = ({ active, payload, label: xLabel }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#0B0F17] border border-slate-700 p-2.5 rounded-lg shadow-xl text-xs">
          <p className="text-slate-400 font-mono mb-1">Time: {xLabel}</p>
          <p className="font-semibold" style={{ color }}>
            {label}: {payload[0].value} {unit}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-[#0B0F17] border border-slate-800 rounded-xl p-4 shadow-inner">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wide">
          {label}
        </h4>
        <span className="text-[11px] font-mono text-slate-500">Unit: {unit}</span>
      </div>
      <div className="h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="hour"
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: '#1e293b' }}
            />
            <YAxis
              stroke="#64748b"
              fontSize={10}
              tickLine={false}
              axisLine={{ stroke: '#1e293b' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              dot={{ r: 2, fill: color }}
              activeDot={{ r: 5, stroke: '#fff', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
