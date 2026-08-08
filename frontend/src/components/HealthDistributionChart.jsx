import React, { useEffect, useState } from 'react';
import { getRankings } from '../api/client';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts';
import { BarChart2 } from 'lucide-react';

export default function HealthDistributionChart({ filters }) {
  const [distribution, setDistribution] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAll() {
      setLoading(true);
      try {
        const queryParams = {
          limit: -1, // All routers for fleet health score distribution histogram
          ...(filters.building && { building: filters.building }),
          ...(filters.firmware && { firmware: filters.firmware }),
          ...(filters.model && { model: filters.model }),
        };
        const data = await getRankings(queryParams);

        const buckets = [
          { range: '0-20 (Critical)', count: 0, color: '#f43f5e' },
          { range: '20-40 (Severe)', count: 0, color: '#fb923c' },
          { range: '40-60 (Poor)', count: 0, color: '#facc15' },
          { range: '60-80 (Fair)', count: 0, color: '#a3e635' },
          { range: '80-100 (Healthy)', count: 0, color: '#10b981' },
        ];

        (data.routers || []).forEach((r) => {
          const score = r.health_score;
          if (score < 20) buckets[0].count++;
          else if (score < 40) buckets[1].count++;
          else if (score < 60) buckets[2].count++;
          else if (score < 80) buckets[3].count++;
          else buckets[4].count++;
        });

        setDistribution(buckets);
      } catch (err) {
        console.error('Failed to fetch health distribution', err);
      } finally {
        setLoading(false);
      }
    }
    fetchAll();
  }, [filters]);

  return (
    <div className="bg-[#151C28] border border-slate-800 rounded-xl p-4 shadow-lg mb-6">
      <div className="flex items-center gap-2 mb-3">
        <BarChart2 className="w-4 h-4 text-cyan-400" />
        <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
          Fleet Health Score Distribution
        </h3>
      </div>

      {loading ? (
        <div className="h-32 flex items-center justify-center text-xs text-slate-500">
          Computing health distribution...
        </div>
      ) : (
        <div className="h-36 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={distribution} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis dataKey="range" stroke="#64748b" fontSize={10} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={10} tickLine={false} allowDecimals={false} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0B0F17', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                itemStyle={{ color: '#06b6d4' }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {distribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
