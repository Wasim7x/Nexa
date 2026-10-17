import React, { useEffect, useState } from 'react';
import { ApiClient } from '../services/api';
import { Offer, Merchant } from '../types';
import { Tag, Plus, Send, CheckCircle2, MessageSquare, Eye, Users } from 'lucide-react';

interface OffersPageProps {
  activeMerchant: Merchant | null;
}

export const OffersPage: React.FC<OffersPageProps> = ({ activeMerchant }) => {
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Form states
  const [offerTitle, setOfferTitle] = useState('');
  const [offerDetails, setOfferDetails] = useState('');
  const [broadcastNow, setBroadcastNow] = useState(false);
  const [messagePreview, setMessagePreview] = useState('');
  const [campaignResult, setCampaignResult] = useState<string | null>(null);

  const loadOffers = () => {
    setLoading(true);
    ApiClient.getOffers()
      .then((data) => {
        if (Array.isArray(data)) setOffers(data);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadOffers();
  }, [activeMerchant]);

  // Live preview generator
  useEffect(() => {
    if (offerTitle && offerDetails) {
      ApiClient.previewOffer(offerTitle, offerDetails).then((res) => {
        setMessagePreview(res.formatted_whatsapp_message);
      });
    } else {
      setMessagePreview('');
    }
  }, [offerTitle, offerDetails]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!offerTitle || !offerDetails) return;

    const res = await ApiClient.createOffer(offerTitle, offerDetails, broadcastNow);
    if (res.campaign_dispatched_count !== undefined) {
      setCampaignResult(`Offer published! Dispatched notifications to ${res.campaign_dispatched_count} opted-in customers.`);
    }

    setShowCreateModal(false);
    setOfferTitle('');
    setOfferDetails('');
    setBroadcastNow(false);
    loadOffers();
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Tag className="w-6 h-6 text-emerald-400" />
            <span>Promotional Offers & WhatsApp Campaigns</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Create store offers, preview WhatsApp message formatting, and broadcast to consented customers.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm shadow-lg shadow-emerald-600/20 transition self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Create New Offer</span>
        </button>
      </div>

      {campaignResult && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center justify-between">
          <span>{campaignResult}</span>
          <button onClick={() => setCampaignResult(null)} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Offer Cards */}
      {loading ? (
        <div className="py-12 flex justify-center text-slate-400">Loading offers...</div>
      ) : offers.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-slate-800/30 border border-slate-800/60">
          <Tag className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-300">No active promotional offers</h3>
          <p className="text-sm text-slate-500 mt-1">Create offers to answer customer queries about discounts and sales.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {offers.map((off) => (
            <div
              key={off.id}
              className="p-6 rounded-2xl bg-slate-800/60 border border-slate-800 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-3">
                  <h4 className="font-bold text-white text-base">{off.title}</h4>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Active
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-3 leading-relaxed whitespace-pre-line">
                  {off.details}
                </p>
              </div>

              <div className="mt-5 pt-3 border-t border-slate-800/60 text-xs text-slate-500 flex items-center justify-between">
                <span>Created {new Date(off.created_at).toLocaleDateString()}</span>
                <span className="text-emerald-400 font-medium">Synced with Nexa AI</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl p-6 shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-white">Create Offer & Campaign</h3>
            <p className="text-xs text-slate-400">
              Configure promotional details and preview the exact WhatsApp message that will be delivered.
            </p>

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Offer Title</label>
                <input
                  type="text"
                  value={offerTitle}
                  onChange={(e) => setOfferTitle(e.target.value)}
                  placeholder="e.g. Weekend Festive Box 20% Off"
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Offer Details & Terms</label>
                <textarea
                  value={offerDetails}
                  onChange={(e) => setOfferDetails(e.target.value)}
                  rows={3}
                  placeholder="Details of the discount, valid dates, minimum order value..."
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              {/* WhatsApp Live Preview */}
              {messagePreview && (
                <div>
                  <label className="block text-xs font-semibold text-emerald-400 mb-1.5 flex items-center gap-1.5">
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>WhatsApp Delivery Preview</span>
                  </label>
                  <div className="p-4 rounded-xl bg-[#0c1317] border border-slate-800 text-xs text-slate-200 font-sans whitespace-pre-wrap leading-relaxed shadow-inner">
                    {messagePreview}
                  </div>
                </div>
              )}

              <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-800 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-white">Broadcast to Consented Customers</p>
                  <p className="text-[11px] text-slate-400">Delivers WhatsApp message only to customers who opted in.</p>
                </div>
                <input
                  type="checkbox"
                  checked={broadcastNow}
                  onChange={(e) => setBroadcastNow(e.target.checked)}
                  className="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500 border-slate-700 bg-slate-800"
                />
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-semibold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold transition flex items-center gap-2"
                >
                  <Send className="w-4 h-4" />
                  <span>Publish Offer</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
