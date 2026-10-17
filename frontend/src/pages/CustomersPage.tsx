import React, { useEffect, useState } from 'react';
import { ApiClient } from '../services/api';
import { Customer, Merchant } from '../types';
import { Users, Search, Download, Shield, MessageCircle, Phone, Clock, FileSpreadsheet } from 'lucide-react';

interface CustomersPageProps {
  activeMerchant: Merchant | null;
}

export const CustomersPage: React.FC<CustomersPageProps> = ({ activeMerchant }) => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [optedInFilter, setOptedInFilter] = useState<'all' | 'true' | 'false'>('all');
  const [selectedCust, setSelectedCust] = useState<Customer | null>(null);

  const loadCustomers = () => {
    setLoading(true);
    const optedParam = optedInFilter === 'all' ? undefined : optedInFilter === 'true';
    ApiClient.getCustomers(search, optedParam)
      .then((data) => {
        if (Array.isArray(data)) setCustomers(data);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadCustomers();
  }, [activeMerchant, optedInFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadCustomers();
  };

  const handleExportCsv = () => {
    window.location.href = ApiClient.getCustomerExportUrl();
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Users className="w-6 h-6 text-emerald-400" />
            <span>Customer Directory & Privacy Scope</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Displaying only customer interactions and profiles scoped to {activeMerchant?.name}.
          </p>
        </div>

        <button
          onClick={handleExportCsv}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-sm border border-slate-700 transition self-start sm:self-auto"
        >
          <Download className="w-4 h-4 text-emerald-400" />
          <span>Export CSV (Audit Logged)</span>
        </button>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name or WhatsApp phone..."
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
          />
        </form>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Promotions:</span>
          <select
            value={optedInFilter}
            onChange={(e: any) => setOptedInFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs font-semibold focus:outline-none"
          >
            <option value="all">All Statuses</option>
            <option value="true">Opted In Only</option>
            <option value="false">Opted Out</option>
          </select>
        </div>
      </div>

      {/* Customer Table */}
      {loading ? (
        <div className="py-12 flex justify-center text-slate-400">Loading customers...</div>
      ) : customers.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-slate-800/30 border border-slate-800/60">
          <Users className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-300">No customers registered for this merchant</h3>
          <p className="text-sm text-slate-500 mt-1">Customers who contact Nexa via WhatsApp will appear here automatically.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-800/40 text-xs font-semibold uppercase tracking-wider text-slate-400">
                <th className="py-3.5 px-6">Customer Name</th>
                <th className="py-3.5 px-6">WhatsApp Number</th>
                <th className="py-3.5 px-6">Interactions</th>
                <th className="py-3.5 px-6">Marketing Consent</th>
                <th className="py-3.5 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-sm">
              {customers.map((c) => (
                <tr key={c.customer_id} className="hover:bg-slate-800/40 transition">
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-emerald-500/10 text-emerald-400 font-bold flex items-center justify-center text-xs">
                        {c.display_name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-semibold text-white">{c.display_name}</p>
                        {c.notes && <p className="text-xs text-slate-400 line-clamp-1">{c.notes}</p>}
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <span className="font-mono text-xs text-slate-300 flex items-center gap-1.5">
                      <Phone className="w-3.5 h-3.5 text-slate-500" />
                      <span>{c.whatsapp_phone}</span>
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 text-xs font-medium text-slate-300">
                      <MessageCircle className="w-3 h-3 text-emerald-400" />
                      <span>{c.interaction_count} messages</span>
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-bold ${
                        c.opt_in_promotions
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : 'bg-slate-700 text-slate-400'
                      }`}
                    >
                      {c.opt_in_promotions ? 'Opted In' : 'Opted Out'}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-right">
                    <button
                      onClick={() => setSelectedCust(c)}
                      className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition"
                    >
                      View Profile
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Customer Detail Modal */}
      {selectedCust && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-lg font-bold text-white">Customer Profile</h3>
              <button
                onClick={() => setSelectedCust(null)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <div>
                <p className="text-xs text-slate-400">Display Name</p>
                <p className="font-semibold text-white mt-0.5">{selectedCust.display_name}</p>
              </div>
              <div>
                <p className="text-xs text-slate-400">Verified WhatsApp Phone</p>
                <p className="font-mono text-white mt-0.5">{selectedCust.whatsapp_phone}</p>
              </div>
              <div>
                <p className="text-xs text-slate-400">Merchant Notes & Preferences</p>
                <p className="text-slate-300 mt-0.5 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                  {selectedCust.notes || 'No specific notes recorded.'}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-400">Total Interactions with {activeMerchant?.name}</p>
                <p className="font-semibold text-white mt-0.5">{selectedCust.interaction_count} inbound messages</p>
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-800">
              <button
                onClick={() => setSelectedCust(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-sm font-semibold transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
