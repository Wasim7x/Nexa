import React, { useEffect, useState } from 'react';
import { ApiClient } from '../services/api';
import { EscalationRecord, Merchant } from '../types';
import { Headset, CheckCircle2, Clock, AlertTriangle, Phone, MessageSquare, ShieldAlert } from 'lucide-react';

interface EscalationsPageProps {
  activeMerchant: Merchant | null;
}

export const EscalationsPage: React.FC<EscalationsPageProps> = ({ activeMerchant }) => {
  const [escalations, setEscalations] = useState<EscalationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedEsc, setSelectedEsc] = useState<EscalationRecord | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');

  const loadEscalations = () => {
    setLoading(true);
    ApiClient.getEscalations(statusFilter || undefined)
      .then((data) => {
        if (Array.isArray(data)) setEscalations(data);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadEscalations();
  }, [activeMerchant, statusFilter]);

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEsc || !resolutionNotes) return;

    await ApiClient.resolveEscalation(selectedEsc.id, resolutionNotes);
    setSelectedEsc(null);
    setResolutionNotes('');
    loadEscalations();
  };

  const getUrgencyBadge = (urgency: string) => {
    switch (urgency) {
      case 'emergency':
      case 'high':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">High Urgency</span>;
      case 'medium':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">Medium</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-700 text-slate-300">Low</span>;
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Headset className="w-6 h-6 text-emerald-400" />
          <span>Human Support & Conversation Takeover</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          When Vera escalates disputes, complex queries, or dental safety flags, they are queued here for staff resolution.
        </p>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        {[
          { id: '', label: 'All Escalations' },
          { id: 'pending', label: 'Pending Review' },
          { id: 'resolved', label: 'Resolved Tickets' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setStatusFilter(tab.id)}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
              statusFilter === tab.id
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Ticket List */}
      {loading ? (
        <div className="py-12 flex justify-center text-slate-400">Loading support queue...</div>
      ) : escalations.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-slate-800/30 border border-slate-800/60">
          <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-200">No active escalations</h3>
          <p className="text-sm text-slate-500 mt-1">All customer conversations are operating normally via AI assistant.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {escalations.map((esc) => (
            <div
              key={esc.id}
              className={`p-6 rounded-2xl border transition flex flex-col md:flex-row md:items-center justify-between gap-5 ${
                esc.status === 'pending'
                  ? 'bg-slate-800/80 border-rose-500/30 shadow-lg shadow-rose-950/20'
                  : 'bg-slate-900/40 border-slate-800 text-slate-400'
              }`}
            >
              <div className="space-y-2 flex-1">
                <div className="flex items-center gap-3">
                  {getUrgencyBadge(esc.urgency)}
                  <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">
                    Category: {esc.category}
                  </span>
                  <span className="text-xs text-slate-500">
                    {new Date(esc.created_at).toLocaleString()}
                  </span>
                </div>

                <p className="font-semibold text-base text-white">{esc.reason}</p>

                {esc.resolution_notes && (
                  <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-emerald-400 mt-2">
                    <strong>Resolution by {esc.assigned_to || 'Staff'}:</strong> {esc.resolution_notes}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-3 shrink-0">
                {esc.status === 'pending' ? (
                  <button
                    onClick={() => setSelectedEsc(esc)}
                    className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs shadow-md transition"
                  >
                    Resolve & Resume AI
                  </button>
                ) : (
                  <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Resolved</span>
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Resolve Modal */}
      {selectedEsc && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-white">Resolve Ticket & Resume AI Assistant</h3>
            <p className="text-xs text-slate-400">
              Provide resolution notes. Once submitted, human takeover mode will end and Vera will resume assisting the customer.
            </p>

            <form onSubmit={handleResolve} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Resolution Notes</label>
                <textarea
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  rows={4}
                  placeholder="e.g. Contacted customer via phone. Scheduled emergency evaluation with Dr. Vance."
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setSelectedEsc(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-semibold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold transition"
                >
                  Complete Resolution
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
