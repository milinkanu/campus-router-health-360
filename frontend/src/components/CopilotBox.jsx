import React, { useState } from 'react';
import { askCopilot } from '../api/client';
import { Bot, Send, Sparkles, AlertCircle, Wrench, CheckCircle2 } from 'lucide-react';

export default function CopilotBox({ routerId }) {
  const [question, setQuestion] = useState('Why is this router performing poorly and what is the recommended fix?');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
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
      const msg = err.response?.data?.detail || 'Failed to contact AI Copilot service. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const getFixBadge = (fix) => {
    const labels = {
      firmware_update: { text: 'Firmware Update', style: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' },
      relocate: { text: 'Relocate Router', style: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
      replace: { text: 'Hardware Replacement', style: 'bg-rose-500/10 text-rose-400 border-rose-500/20' },
      user_education: { text: 'User Education', style: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
      none: { text: 'No Action Needed', style: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' }
    };
    const item = labels[fix] || { text: fix, style: 'bg-slate-500/10 text-slate-400 border-slate-500/20' };
    return (
      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold border ${item.style}`}>
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
      <span className={`px-2.5 py-0.5 rounded text-[11px] font-mono border uppercase tracking-wider ${styles[conf] || styles.medium}`}>
        Confidence: {conf}
      </span>
    );
  };

  return (
    <div className="bg-[#151C28] border border-slate-800 rounded-xl p-5 shadow-xl">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <span>AI Copilot Diagnostics</span>
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            </h3>
            <p className="text-xs text-slate-400">Ask why {routerId} is failing and get grounded evidence + fixes</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about this router..."
            disabled={loading}
            className="flex-1 bg-[#0B0F17] text-slate-200 text-xs border border-slate-700 rounded-lg px-3.5 py-2.5 focus:outline-none focus:border-cyan-500 transition-colors"
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-medium text-xs px-4 py-2.5 rounded-lg flex items-center gap-1.5 transition-all shadow-md"
          >
            {loading ? (
              <span>Diagnosing...</span>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>Ask AI</span>
              </>
            )}
          </button>
        </div>
      </form>

      {error && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400 text-xs flex items-start gap-2 mb-4">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {response && (
        <div className="bg-[#0B0F17] border border-cyan-500/30 rounded-xl p-4 space-y-4 shadow-inner">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-medium">Recommended Fix:</span>
              {getFixBadge(response.recommended_fix)}
            </div>
            {getConfidenceBadge(response.confidence)}
          </div>

          <div>
            <h4 className="text-xs font-semibold text-cyan-400 uppercase tracking-wide mb-1.5">
              Diagnosis
            </h4>
            <p className="text-xs text-slate-200 leading-relaxed bg-[#151C28] p-3 rounded-lg border border-slate-800">
              {response.diagnosis}
            </p>
          </div>

          {response.evidence && response.evidence.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">
                Supporting Evidence Cites
              </h4>
              <ul className="space-y-1.5 text-xs text-slate-300">
                {response.evidence.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-[#151C28]/60 p-2 rounded border border-slate-800">
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
  );
}
