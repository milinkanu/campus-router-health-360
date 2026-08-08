import React, { useEffect, useState } from 'react';
import { getFilters } from '../api/client';
import { Filter, RotateCcw } from 'lucide-react';

export default function FilterBar({ filters, onFilterChange, onReset }) {
  const [filterOptions, setFilterOptions] = useState({
    buildings: [],
    firmware_versions: [],
    models: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadOptions() {
      try {
        const data = await getFilters();
        setFilterOptions(data);
      } catch (err) {
        console.error('Failed to load filters', err);
      } finally {
        setLoading(false);
      }
    }
    loadOptions();
  }, []);

  const handleChange = (key, value) => {
    onFilterChange({
      ...filters,
      [key]: value === 'ALL' ? '' : value
    });
  };

  const hasActiveFilters = Boolean(filters.building || filters.firmware || filters.model);

  return (
    <div className="bg-[#151C28] border border-slate-800 rounded-xl p-4 shadow-lg mb-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-cyan-400 font-semibold text-sm">
          <Filter className="w-4 h-4" />
          <span>Fleet Filters</span>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Building Dropdown */}
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-400 font-medium">Building:</label>
            <select
              value={filters.building || 'ALL'}
              onChange={(e) => handleChange('building', e.target.value)}
              disabled={loading}
              className="bg-[#0B0F17] text-slate-200 text-xs border border-slate-700 rounded-lg px-3 py-1.5 focus:outline-none focus:border-cyan-500 transition-colors"
            >
              <option value="ALL">All Buildings</option>
              {filterOptions.buildings.map((b) => (
                <option key={b} value={b}>{b}</option>
              ))}
            </select>
          </div>

          {/* Firmware Dropdown */}
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-400 font-medium">Firmware:</label>
            <select
              value={filters.firmware || 'ALL'}
              onChange={(e) => handleChange('firmware', e.target.value)}
              disabled={loading}
              className="bg-[#0B0F17] text-slate-200 text-xs border border-slate-700 rounded-lg px-3 py-1.5 focus:outline-none focus:border-cyan-500 transition-colors"
            >
              <option value="ALL">All Versions</option>
              {filterOptions.firmware_versions.map((f) => (
                <option key={f} value={f}>{f}</option>
              ))}
            </select>
          </div>

          {/* Model Dropdown */}
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-400 font-medium">Model:</label>
            <select
              value={filters.model || 'ALL'}
              onChange={(e) => handleChange('model', e.target.value)}
              disabled={loading}
              className="bg-[#0B0F17] text-slate-200 text-xs border border-slate-700 rounded-lg px-3 py-1.5 focus:outline-none focus:border-cyan-500 transition-colors"
            >
              <option value="ALL">All Models</option>
              {filterOptions.models.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          {/* Reset Button */}
          {hasActiveFilters && (
            <button
              onClick={onReset}
              className="flex items-center gap-1 text-xs text-rose-400 hover:text-rose-300 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 px-3 py-1.5 rounded-lg transition-all"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Clear</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
