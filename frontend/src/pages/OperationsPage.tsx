import React, { useEffect, useState } from 'react';
import { ApiClient } from '../services/api';
import { OperationRecord, Merchant } from '../types';
import { ShoppingBag, Calendar, CheckCircle2, Clock, XCircle, Search, Filter, AlertCircle } from 'lucide-react';

interface OperationsPageProps {
  activeMerchant: Merchant | null;
}

export const OperationsPage: React.FC<OperationsPageProps> = ({ activeMerchant }) => {
  const [records, setRecords] = useState<OperationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');
  const [selectedRecord, setSelectedRecord] = useState<OperationRecord | null>(null);
  const [cancelReason, setCancelReason] = useState('');
  const [showCancelModal, setShowCancelModal] = useState(false);

  const isAppointment = activeMerchant?.business_type === 'salon' || activeMerchant?.business_type === 'dental';

  const loadRecords = () => {
    setLoading(true);
    ApiClient.getOperations(statusFilter || undefined)
      .then((data) => {
        if (Array.isArray(data)) setRecords(data);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadRecords();
  }, [activeMerchant, statusFilter]);

  const handleUpdateStatus = async (ref: string, newStatus: string) => {
    await ApiClient.updateOperationStatus(ref, newStatus);
    loadRecords();
    setSelectedRecord(null);
  };

  const handleCancel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRecord) return;
    await ApiClient.updateOperationStatus(selectedRecord.reference, 'cancelled', cancelReason);
    setShowCancelModal(false);
    setSelectedRecord(null);
    setCancelReason('');
    loadRecords();
  };

  const filtered = records.filter((r) => {
    const s = search.toLowerCase();
    return (
      r.reference.toLowerCase().includes(s) ||
      (r.service_name && r.service_name.toLowerCase().includes(s))
    );
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'confirmed':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Confirmed</span>;
      case 'delivered':
      case 'completed':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">{status.toUpperCase()}</span>;
      case 'cancelled':
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">Cancelled</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-700 text-slate-300">{status}</span>;
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            {isAppointment ? <Calendar className="w-6 h-6 text-emerald-400" /> : <ShoppingBag className="w-6 h-6 text-emerald-400" />}
            <span>{isAppointment ? 'Appointment Management' : 'Orders & Fulfillment'}</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Authoritative transactional business records placed by customers through WhatsApp.
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by reference number or service..."
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Status Filter:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs font-semibold focus:outline-none"
          >
            <option value="">All Records</option>
            <option value="confirmed">Confirmed</option>
            <option value="completed">Completed / Delivered</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="py-12 flex justify-center text-slate-400">Loading operations records...</div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-slate-800/30 border border-slate-800/60">
          <Clock className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-300">No {isAppointment ? 'appointments' : 'orders'} found</h3>
          <p className="text-sm text-slate-500 mt-1">Orders or bookings placed through Nexa will be listed here.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-800/40 text-xs font-semibold uppercase tracking-wider text-slate-400">
                <th className="py-3.5 px-6">Reference</th>
                <th className="py-3.5 px-6">{isAppointment ? 'Service & Practitioner' : 'Details / Address'}</th>
                <th className="py-3.5 px-6">{isAppointment ? 'Schedule' : 'Total Amount'}</th>
                <th className="py-3.5 px-6">Status</th>
                <th className="py-3.5 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-sm">
              {filtered.map((r) => (
                <tr key={r.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-4 px-6">
                    <span className="font-mono font-bold text-white">{r.reference}</span>
                  </td>

                  <td className="py-4 px-6">
                    {isAppointment ? (
                      <div>
                        <p className="font-semibold text-white">{r.service_name}</p>
                        <p className="text-xs text-slate-400">{r.staff_name || r.dentist_name || 'Staff'}</p>
                      </div>
                    ) : (
                      <div>
                        <p className="text-xs text-slate-300 line-clamp-1">{r.delivery_address || 'Pickup / In-Store'}</p>
                        {r.gift_packaging && (
                          <span className="inline-block text-[10px] text-amber-400 font-semibold mt-0.5">
                            ★ Gift Wrapped
                          </span>
                        )}
                      </div>
                    )}
                  </td>

                  <td className="py-4 px-6">
                    {isAppointment ? (
                      <div>
                        <p className="font-medium text-white">{r.date}</p>
                        <p className="text-xs text-slate-400">{r.time}</p>
                      </div>
                    ) : (
                      <span className="font-bold text-white">₹{r.total?.toFixed(2) || '0.00'}</span>
                    )}
                  </td>

                  <td className="py-4 px-6">{getStatusBadge(r.status)}</td>

                  <td className="py-4 px-6 text-right space-x-2">
                    {r.status !== 'cancelled' && (
                      <button
                        onClick={() => {
                          setSelectedRecord(r);
                          setShowCancelModal(true);
                        }}
                        className="px-2.5 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-xs font-semibold transition"
                      >
                        Cancel
                      </button>
                    )}
                    {r.status === 'confirmed' && (
                      <button
                        onClick={() => handleUpdateStatus(r.reference, isAppointment ? 'completed' : 'delivered')}
                        className="px-2.5 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 text-xs font-semibold transition"
                      >
                        Mark Complete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Cancel Confirmation Modal */}
      {showCancelModal && selectedRecord && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-rose-400">
              <AlertCircle className="w-6 h-6" />
              <h3 className="text-lg font-bold text-white">Confirm Cancellation</h3>
            </div>
            <p className="text-xs text-slate-300">
              Are you sure you want to cancel <strong className="text-white">{selectedRecord.reference}</strong>? 
              This will automatically release slots or restock inventory and notify the customer.
            </p>

            <form onSubmit={handleCancel} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Reason (Optional)</label>
                <input
                  type="text"
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  placeholder="e.g. Customer requested via phone call"
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-rose-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCancelModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-semibold transition"
                >
                  Back
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-sm font-semibold transition"
                >
                  Cancel Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
