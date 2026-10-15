import React, { useEffect, useState } from 'react';
import { ApiClient } from '../services/api';
import { Merchant, MerchantSettingsData, AuditLog } from '../types';
import { Settings, Shield, Clock, Phone, History, Save, CheckCircle2 } from 'lucide-react';

interface SettingsPageProps {
  activeMerchant: Merchant | null;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ activeMerchant }) => {
  const [settingsData, setSettingsData] = useState<MerchantSettingsData | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  // Form states
  const [businessHours, setBusinessHours] = useState('');
  const [timezone, setTimezone] = useState('');
  const [notificationPhone, setNotificationPhone] = useState('');
  const [escalationMsg, setEscalationMsg] = useState('');
  const [welcomeMsg, setWelcomeMsg] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);

  const loadData = () => {
    setLoading(true);
    Promise.all([ApiClient.getSettings(), ApiClient.getAuditLogs()])
      .then(([settings, logs]) => {
        setSettingsData(settings);
        if (settings?.settings) {
          setBusinessHours(settings.settings.business_hours || '');
          setTimezone(settings.settings.timezone || 'UTC');
          setNotificationPhone(settings.settings.notification_phone || '');
          setEscalationMsg(settings.settings.escalation_message || '');
          setWelcomeMsg(settings.settings.welcome_message || '');
        }
        if (Array.isArray(logs)) setAuditLogs(logs);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [activeMerchant]);

  const handleSaveGeneral = async (e: React.FormEvent) => {
    e.preventDefault();
    await ApiClient.updateGeneralSettings({
      business_hours: businessHours,
      timezone: timezone,
      notification_phone: notificationPhone,
      escalation_message: escalationMsg,
      welcome_message: welcomeMsg
    });
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
    loadData();
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Settings className="w-6 h-6 text-emerald-400" />
          <span>General Settings & Security Audit Trail</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Operating hours, staff notification routing, and immutable security audit logs for {activeMerchant?.name}.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Merchant Operations Settings */}
        <div className="p-6 rounded-2xl bg-slate-800/60 border border-slate-800 space-y-5">
          <div className="flex items-center justify-between pb-4 border-b border-slate-700/80">
            <div>
              <h3 className="font-bold text-lg text-white">Merchant Operational Profile</h3>
              <p className="text-xs text-slate-400">Configure business hours and assistant responses</p>
            </div>
            {saveSuccess && (
              <span className="flex items-center gap-1 text-xs text-emerald-400 font-bold">
                <CheckCircle2 className="w-4 h-4" />
                <span>Saved</span>
              </span>
            )}
          </div>

          <form onSubmit={handleSaveGeneral} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>Store / Clinic Operating Hours</span>
              </label>
              <input
                type="text"
                value={businessHours}
                onChange={(e) => setBusinessHours(e.target.value)}
                placeholder="Mon-Sun: 8:00 AM - 9:00 PM"
                className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Timezone</label>
              <input
                type="text"
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Phone className="w-3.5 h-3.5 text-slate-400" />
                <span>Staff Support Phone Number (For Escalations)</span>
              </label>
              <input
                type="text"
                value={notificationPhone}
                onChange={(e) => setNotificationPhone(e.target.value)}
                placeholder="+15550109991"
                className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Welcome Message</label>
              <textarea
                value={welcomeMsg}
                onChange={(e) => setWelcomeMsg(e.target.value)}
                rows={2}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Escalation Message</label>
              <textarea
                value={escalationMsg}
                onChange={(e) => setEscalationMsg(e.target.value)}
                rows={2}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition flex items-center gap-1.5"
              >
                <Save className="w-4 h-4" />
                <span>Save General Settings</span>
              </button>
            </div>
          </form>
        </div>

        {/* Security Audit Trail */}
        <div className="p-6 rounded-2xl bg-slate-800/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-700/80">
            <div className="flex items-center gap-2">
              <History className="w-5 h-5 text-emerald-400" />
              <h3 className="font-bold text-lg text-white">Security & Audit Logs</h3>
            </div>
            <span className="text-xs text-slate-400">Latest 50 events</span>
          </div>

          {auditLogs.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500">No audit events recorded yet.</div>
          ) : (
            <div className="space-y-2.5 max-h-[500px] overflow-y-auto pr-1">
              {auditLogs.map((log) => (
                <div
                  key={log.id}
                  className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200">{log.action}</span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        log.status === 'success' ? 'text-emerald-400 bg-emerald-500/10' : 'text-rose-400 bg-rose-500/10'
                      }`}
                    >
                      {log.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>Target: {log.resource_type} {log.resource_id ? `(${log.resource_id})` : ''}</span>
                    <span>{new Date(log.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
