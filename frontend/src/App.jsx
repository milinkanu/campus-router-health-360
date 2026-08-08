import React, { useState } from 'react';
import FilterBar from './components/FilterBar';
import RankingsTable from './components/RankingsTable';
import RouterDetailPanel from './components/RouterDetailPanel';
import HealthDistributionChart from './components/HealthDistributionChart';
import FloatingChatWidget from './components/FloatingChatWidget';
import { Activity, ShieldAlert, Radio } from 'lucide-react';

export default function App() {
  const [selectedRouterId, setSelectedRouterId] = useState(null);
  const [filters, setFilters] = useState({
    building: '',
    firmware: '',
    model: '',
  });

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
  };

  const handleResetFilters = () => {
    setFilters({ building: '', firmware: '', model: '' });
  };

  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-100 flex flex-col relative">
      {/* Top Navbar */}
      <header className="bg-[#151C28] border-b border-slate-800 sticky top-0 z-40 backdrop-blur bg-opacity-90">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 shadow-lg text-white">
              <Radio className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                <span>Campus Router Health 360</span>
                <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  AI Copilot
                </span>
              </h1>
              <p className="text-xs text-slate-400">
                Automated Wi-Fi Fleet Telemetry, Health Scoring & AI Diagnostic Agent
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs font-medium text-slate-300">
            <div className="flex items-center gap-2 bg-[#0B0F17] px-3 py-1.5 rounded-lg border border-slate-800">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              <span>Backend Connected</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Body Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Filter Toolbar */}
        <FilterBar
          filters={filters}
          onFilterChange={handleFilterChange}
          onReset={handleResetFilters}
        />

        {/* Fleet Distribution Histogram (Bonus) */}
        <HealthDistributionChart filters={filters} />

        {/* Grid Layout: Left Rankings Table, Right Detail Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          <div className="lg:col-span-5 h-full">
            <RankingsTable
              filters={filters}
              selectedRouterId={selectedRouterId}
              onSelectRouter={setSelectedRouterId}
            />
          </div>

          <div className="lg:col-span-7">
            <RouterDetailPanel routerId={selectedRouterId} />
          </div>
        </div>
      </main>

      {/* Floating Chat Widget fixed on right side */}
      <FloatingChatWidget
        selectedRouterId={selectedRouterId}
        onSelectRouter={setSelectedRouterId}
      />

      {/* Footer */}
      <footer className="bg-[#151C28] border-t border-slate-800 py-4 text-center text-xs text-slate-500 mt-12">
        <p>Campus Router Health 360 • DigiPlus IT Agentic AI Platform</p>
      </footer>
    </div>
  );
}

