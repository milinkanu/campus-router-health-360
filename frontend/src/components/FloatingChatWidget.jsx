import React, { useState, useEffect } from 'react';
import { askCopilot, getRankings } from '../api/client';
import {
  Bot,
  Send,
  Sparkles,
  AlertCircle,
  Wrench,
  CheckCircle2,
  X,
  MessageSquare,
  ChevronDown,
  RefreshCw,
  ShieldCheck,
  AlertTriangle,
  Activity
} from 'lucide-react';

export default function FloatingChatWidget({ selectedRouterId, onSelectRouter }) {
  const [isOpen, setIsOpen] = useState(false);
  const [routerId, setRouterId] = useState(selectedRouterId || 'R-1010');
  const [routersList, setRoutersList] = useState([]);
  const [question, setQuestion] = useState('Why is this router performing poorly and what is the recommended fix?');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Sync selected router from props if changed
  useEffect(() => {
    if (selectedRouterId) {
      setRouterId(selectedRouterId);
    }
  }, [selectedRouterId]);

  // Load routers on mount
  useEffect(() => {
    async function fetchRouters() {
      try {
        const data = await getRankings();
        if (data && data.routers) {
          setRoutersList(data.routers);
          if (!selectedRouterId && data.routers.length > 0) {
            setRouterId(data.routers[0].router_id);
          }
        }
      } catch (err) {
        console.error('Failed to load routers for chat widget dropdown:', err);
      }
    }
    fetchRouters();
  }, []);

  const handleSelectRouter = (newId) => {
    setRouterId(newId);
    if (onSelectRouter) {
      onSelectRouter(newId);
    }
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!routerId || !question.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await askCopilot({
        router_id: routerId,
        question: question.trim(),
      });
      setResponse(res);
    } catch (err) {
      console.error('Copilot query error:', err);
      const msg =
        err.response?.data?.detail || 'Failed to contact AI Copilot service. Please verify backend service.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const presetQuestions = [
    'Why is this router performing poorly and what is the recommended fix?',
    'Are recent disconnect complaints caused by hardware or user setup?',
    'What action should campus IT admins take immediately for this router?',
  ];

  const getFixBadge = (fix) => {
    const labels = {
      firmware_update: { text: 'Firmware Update', style: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' },
      relocate: { text: 'Relocate Router', style: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
      replace: { text: 'Hardware Replacement', style: 'bg-rose-500/10 text-rose-400 border-rose-500/20' },
      user_education: { text: 'User Education', style: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
      none: { text: 'No Action Needed', style: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
    };
    const item = labels[fix] || { text: fix, style: 'bg-slate-500/10 text-slate-400 border-slate-500/20' };
    return (
      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${item.style}`}>
        <Wrench className="w-3 h-3" />
        {item.text}
      </span>
    );
  };

  const getConfidenceBadge = (conf) => {
    const styles = {
      high: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      medium: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      low: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    };
    return (
      <span className={`px-2 py-0.5 rounded text-[10px] font-mono border uppercase tracking-wider ${styles[conf] || styles.medium}`}>
        Confidence: {conf}
      </span>
    );
  };

  return (
    <>
      {/* Floating Chat Trigger Button fixed on the right side */}
      <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3">
        {!isOpen && (
          <div className="hidden sm:flex items-center gap-2 bg-[#151C28]/95 backdrop-blur border border-cyan-500/30 text-xs text-slate-200 px-3 py-1.5 rounded-full shadow-lg animate-bounce">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-medium">AI Admin Copilot Chat</span>
          </div>
        )}

        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`group relative p-4 rounded-full shadow-2xl transition-all duration-300 flex items-center justify-center ${
            isOpen
              ? 'bg-rose-600 hover:bg-rose-500 text-white rotate-90 scale-105'
              : 'bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 text-white hover:scale-110 shadow-cyan-500/30'
          }`}
          aria-label="Open AI Copilot Chat"
          title="Admin AI Copilot Chat"
        >
          {isOpen ? (
            <X className="w-6 h-6" />
          ) : (
            <>
              <Bot className="w-6 h-6" />
              <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-cyan-500 border-2 border-[#0B0F17]"></span>
              </span>
            </>
          )}
        </button>
      </div>

      {/* Floating Chat Window Modal */}
      {isOpen && (
        <div className="fixed bottom-24 right-4 sm:right-6 z-50 w-[92vw] sm:w-[440px] max-h-[82vh] bg-[#151C28] border border-cyan-500/30 rounded-2xl shadow-2xl flex flex-col overflow-hidden backdrop-blur-xl animate-in fade-in slide-in-from-bottom-5 duration-200">
          {/* Header */}
          <div className="bg-[#0B0F17] px-4 py-3.5 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 text-white shadow-md">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                  <span>AI Copilot Chat</span>
                  <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
                </h3>
                <p className="text-[11px] text-slate-400">Admin Telemetry Diagnostic Assistant</p>
              </div>
            </div>

            <button
              onClick={() => setIsOpen(false)}
              className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              aria-label="Close Chat"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Chat Body */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4 max-h-[calc(82vh-130px)]">
            {/* Router Selector Dropdown */}
            <div className="bg-[#0B0F17] p-2.5 rounded-xl border border-slate-800 space-y-1">
              <label className="text-[11px] font-semibold text-slate-400 block uppercase tracking-wider">
                Select Router to Diagnose:
              </label>
              <div className="relative">
                <select
                  value={routerId}
                  onChange={(e) => handleSelectRouter(e.target.value)}
                  className="w-full bg-[#151C28] text-cyan-300 font-mono font-bold text-xs border border-slate-700 rounded-lg px-3 py-2 pr-8 appearance-none focus:outline-none focus:border-cyan-500 cursor-pointer"
                >
                  {routersList.map((r) => (
                    <option key={r.router_id} value={r.router_id}>
                      {r.router_id} ({r.building}) — Score: {r.health_score.toFixed(1)} [{r.top_issue}]
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-4 h-4 text-slate-400 absolute right-2.5 top-2.5 pointer-events-none" />
              </div>
            </div>

            {/* Quick Prompt Chips */}
            <div className="space-y-1.5">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                Quick Questions:
              </span>
              <div className="flex flex-col gap-1.5">
                {presetQuestions.map((pq, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setQuestion(pq)}
                    className="text-left text-[11px] text-slate-300 hover:text-cyan-300 bg-[#0B0F17] hover:bg-[#0B0F17]/80 border border-slate-800 hover:border-cyan-500/40 p-2 rounded-lg transition-colors flex items-center justify-between group"
                  >
                    <span className="line-clamp-1">{pq}</span>
                    <Sparkles className="w-3 h-3 text-slate-600 group-hover:text-cyan-400 shrink-0 ml-1" />
                  </button>
                ))}
              </div>
            </div>

            {/* Error Banner */}
            {error && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {/* Response Card */}
            {response && (
              <div className="bg-[#0B0F17] border border-cyan-500/30 rounded-xl p-3.5 space-y-3 shadow-inner">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[11px] text-slate-400">Fix:</span>
                    {getFixBadge(response.recommended_fix)}
                  </div>
                  {getConfidenceBadge(response.confidence)}
                </div>

                <div>
                  <h4 className="text-[11px] font-semibold text-cyan-400 uppercase tracking-wide mb-1">
                    Diagnosis for {response.router_id}
                  </h4>
                  <p className="text-xs text-slate-200 leading-relaxed bg-[#151C28] p-2.5 rounded-lg border border-slate-800">
                    {response.diagnosis}
                  </p>
                </div>

                {response.evidence && response.evidence.length > 0 && (
                  <div>
                    <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide mb-1">
                      Evidence Cites
                    </h4>
                    <ul className="space-y-1 text-xs text-slate-300">
                      {response.evidence.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-1.5 bg-[#151C28]/60 p-1.5 rounded border border-slate-800/80 text-[11px]">
                          <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Footer Input */}
          <div className="bg-[#0B0F17] p-3 border-t border-slate-800">
            <form onSubmit={handleSubmit} className="flex gap-2">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder={`Ask AI about ${routerId}...`}
                disabled={loading}
                className="flex-1 bg-[#151C28] text-slate-100 text-xs border border-slate-700 rounded-lg px-3 py-2 focus:outline-none focus:border-cyan-500 transition-colors"
              />
              <button
                type="submit"
                disabled={loading || !question.trim()}
                className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-semibold text-xs px-3.5 py-2 rounded-lg flex items-center gap-1.5 transition-all shadow-md shrink-0"
              >
                {loading ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    <span>Send</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
