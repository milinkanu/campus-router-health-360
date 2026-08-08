import React, { useEffect, useState } from 'react';
import { getRankings } from '../api/client';
import { ArrowUpDown, AlertTriangle, ShieldCheck, Activity } from 'lucide-react';

export default function RankingsTable({ filters, selectedRouterId, onSelectRouter }) {
  const [data, setData] = useState({ total_routers: 0, routers: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortField, setSortField] = useState('health_score');
  const [sortAsc, setSortAsc] = useState(true); // ascending = worst score first

  useEffect(() => {
    async function fetchRankings() {
      setLoading(true);
      setError(null);
      try {
        const queryParams = {
          limit: 10, // Worst 10 routers as specified in spec
          ...(filters.building && { building: filters.building }),
          ...(filters.firmware && { firmware: filters.firmware }),
          ...(filters.model && { model: filters.model }),
        };
        const result = await getRankings(queryParams);
        setData(result);
        if (result.routers.length > 0 && !selectedRouterId) {
          onSelectRouter(result.routers[0].router_id);
        }
      } catch (err) {
        setError('Failed to fetch router rankings');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchRankings();
  }, [filters]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  const sortedRouters = [...data.routers].sort((a, b) => {
    let valA = a[sortField];
    let valB = b[sortField];
    if (typeof valA === 'string') {
      return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
    }
    return sortAsc ? valA - valB : valB - valA;
  });

  const getScoreBadge = (score) => {
    if (score < 50) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <AlertTriangle className="w-3 h-3" />
          {score.toFixed(1)}
        </span>
      );
    } else if (score < 80) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <Activity className="w-3 h-3" />
          {score.toFixed(1)}
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <ShieldCheck className="w-3 h-3" />
          {score.toFixed(1)}
        </span>
      );
    }
  };

  return (
    <div className="bg-[#151C28] border border-slate-800 rounded-xl overflow-hidden shadow-lg flex flex-col h-full">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
            <span>Worst-10 Routers Ranking</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Ranked by health score (lowest health score = worst performance)
          </p>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700 font-medium">
          {data.total_routers} routers found
        </span>
      </div>

      <div className="overflow-x-auto flex-1">
        {loading ? (
          <div className="p-8 text-center text-slate-400 text-sm">Loading fleet rankings...</div>
        ) : error ? (
          <div className="p-8 text-center text-rose-400 text-sm">{error}</div>
        ) : sortedRouters.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-sm">
            No routers match the selected filters.
          </div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0B0F17] text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
              <tr>
                <th
                  className="px-4 py-3 cursor-pointer hover:text-slate-200 transition-colors"
                  onClick={() => handleSort('router_id')}
                >
                  <div className="flex items-center gap-1">
                    <span>Router ID</span>
                    <ArrowUpDown className="w-3 h-3 opacity-50" />
                  </div>
                </th>
                <th
                  className="px-4 py-3 cursor-pointer hover:text-slate-200 transition-colors"
                  onClick={() => handleSort('building')}
                >
                  <div className="flex items-center gap-1">
                    <span>Building</span>
                    <ArrowUpDown className="w-3 h-3 opacity-50" />
                  </div>
                </th>
                <th
                  className="px-4 py-3 cursor-pointer hover:text-slate-200 transition-colors"
                  onClick={() => handleSort('health_score')}
                >
                  <div className="flex items-center gap-1">
                    <span>Health Score</span>
                    <ArrowUpDown className="w-3 h-3 opacity-50" />
                  </div>
                </th>
                <th
                  className="px-4 py-3 cursor-pointer hover:text-slate-200 transition-colors"
                  onClick={() => handleSort('top_issue')}
                >
                  <div className="flex items-center gap-1">
                    <span>Top Primary Issue</span>
                    <ArrowUpDown className="w-3 h-3 opacity-50" />
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {sortedRouters.map((router) => {
                const isSelected = router.router_id === selectedRouterId;
                return (
                  <tr
                    key={router.router_id}
                    onClick={() => onSelectRouter(router.router_id)}
                    className={`cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-cyan-950/40 border-l-4 border-l-cyan-500'
                        : 'hover:bg-slate-800/40'
                    }`}
                  >
                    <td className="px-4 py-3 font-semibold text-slate-200 font-mono">
                      {router.router_id}
                    </td>
                    <td className="px-4 py-3 text-slate-300">{router.building}</td>
                    <td className="px-4 py-3">{getScoreBadge(router.health_score)}</td>
                    <td className="px-4 py-3 text-slate-300">{router.top_issue}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
