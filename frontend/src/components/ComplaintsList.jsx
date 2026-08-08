import React from 'react';
import { MessageSquareText, Calendar } from 'lucide-react';

export default function ComplaintsList({ complaints = [] }) {
  if (!complaints || complaints.length === 0) {
    return (
      <div className="bg-[#0B0F17] border border-slate-800 rounded-xl p-6 text-center">
        <MessageSquareText className="w-8 h-8 text-slate-600 mx-auto mb-2 opacity-50" />
        <p className="text-xs text-slate-400 font-medium">No complaints logged for this router.</p>
      </div>
    );
  }

  return (
    <div className="bg-[#0B0F17] border border-slate-800 rounded-xl p-4 flex flex-col h-full">
      <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wide flex items-center gap-1.5">
          <MessageSquareText className="w-3.5 h-3.5 text-amber-400" />
          <span>User Complaints ({complaints.length})</span>
        </h4>
      </div>

      <div className="space-y-2.5 overflow-y-auto max-h-48 pr-1">
        {complaints.map((item) => (
          <div
            key={item.ticket_id}
            className="bg-[#151C28] border border-slate-800 rounded-lg p-3 text-xs"
          >
            <div className="flex items-center justify-between mb-1 text-[11px] text-slate-400 font-mono">
              <span className="font-semibold text-cyan-400">{item.ticket_id}</span>
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3 text-slate-500" />
                {item.date}
              </span>
            </div>
            <p className="text-slate-200 leading-relaxed font-normal">{item.complaint_text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
