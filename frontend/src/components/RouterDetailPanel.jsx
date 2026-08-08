import React, { useEffect, useState } from 'react';
import { getRouterDetail } from '../api/client';
import MetricChart from './MetricChart';
import ComplaintsList from './ComplaintsList';
import { Router, Cpu, Building2, User, Calendar, ShieldCheck, AlertTriangle, Activity } from 'lucide-react';

export default function RouterDetailPanel({ routerId }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!routerId) return;

    async function fetchDetail() {
      setLoading(true);
      setError(null);
      try {
        const data = await getRouterDetail(routerId);
        setDetail(data);
      } catch (err) {
        console.error('Failed to fetch router detail:', err);
        setError(`Failed to load details for router ${routerId}`);
      } finally {
        setLoading(false);
      }
    }
    fetchDetail();
  }, [routerId]);

  if (!routerId) {
    return (
      <div className="bg-[#151C28] border border-slate-800 rounded-xl p-12 text-center text-slate-400">
        <Router className="w-12 h-12 text-slate-600 mx-auto mb-3 opacity-50" />
        <p className="text-sm font-medium">Select a router from the rankings table to view details.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-[#151C28] border border-slate-800 rounded-xl p-12 text-center text-slate-400 text-sm">
        Loading details for {routerId}...
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[#151C28] border border-slate-800 rounded-xl p-8 text-center text-rose-400 text-sm">
        {error}
      </div>
    );
  }

  if (!detail) return null;

  const latencyChartData = (detail.metrics || []).map((m) => ({
    hour: m.hour,
    value: m.latency_ms,
  }));

  const packetLossChartData = (detail.metrics || []).map((m) => ({
    hour: m.hour,
    value: m.packet_loss_pct,
  }));

  const getScoreBadge = (score) => {
    if (score < 50) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
          <AlertTriangle className="w-4 h-4" />
          Health Score: {score.toFixed(1)} / 100
        </span>
      );
    } else if (score < 80) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
          <Activity className="w-4 h-4" />
          Health Score: {score.toFixed(1)} / 100
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          <ShieldCheck className="w-4 h-4" />
          Health Score: {score.toFixed(1)} / 100
        </span>
      );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Metadata Card */}
      <div className="bg-[#151C28] border border-slate-800 rounded-xl p-5 shadow-lg">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <Router className="w-5 h-5 text-cyan-400" />
              <h2 className="text-xl font-bold font-mono text-slate-100">{detail.router_id}</h2>
              <span className="text-xs px-2.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-medium">
                {detail.top_issue}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Issued on {detail.issue_date} for {detail.user_type} use
            </p>
          </div>

          <div>{getScoreBadge(detail.health_score)}</div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="bg-[#0B0F17] p-3 rounded-lg border border-slate-800">
            <span className="text-slate-400 text-[11px] block flex items-center gap-1 mb-1">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" /> Model
            </span>
            <span className="font-semibold text-slate-200">{detail.model}</span>
          </div>

          <div className="bg-[#0B0F17] p-3 rounded-lg border border-slate-800">
            <span className="text-slate-400 text-[11px] block flex items-center gap-1 mb-1">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" /> Firmware
            </span>
            <span className="font-semibold text-slate-200">{detail.firmware_version}</span>
          </div>

          <div className="bg-[#0B0F17] p-3 rounded-lg border border-slate-800">
            <span className="text-slate-400 text-[11px] block flex items-center gap-1 mb-1">
              <Building2 className="w-3.5 h-3.5 text-cyan-400" /> Location
            </span>
            <span className="font-semibold text-slate-200">
              {detail.building} (Rm {detail.room})
            </span>
          </div>

          <div className="bg-[#0B0F17] p-3 rounded-lg border border-slate-800">
            <span className="text-slate-400 text-[11px] block flex items-center gap-1 mb-1">
              <User className="w-3.5 h-3.5 text-cyan-400" /> User Type
            </span>
            <span className="font-semibold text-slate-200 capitalize">{detail.user_type}</span>
          </div>
        </div>
      </div>

      {/* Metrics Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <MetricChart
          data={latencyChartData}
          label="Latency Trend"
          unit="ms"
          color="#06b6d4"
        />
        <MetricChart
          data={packetLossChartData}
          label="Packet Loss Trend"
          unit="%"
          color="#f43f5e"
        />
      </div>

      {/* Complaints List */}
      <ComplaintsList complaints={detail.complaints} />
    </div>
  );
}

