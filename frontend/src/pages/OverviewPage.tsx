import React, { useEffect, useState } from 'react';
import { ApiClient } from '../services/api';
import { DashboardStats, Merchant } from '../types';
import { 
  Users, 
  ShoppingBag, 
  DollarSign, 
  AlertCircle, 
  BookOpen, 
  Bell, 
  ArrowUpRight, 
  Clock, 
  ShieldCheck, 
  Store 
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts';

interface OverviewPageProps {
  activeMerchant: Merchant | null;
  onNavigate: (page: any) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ activeMerchant, onNavigate }) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    ApiClient.getDashboardStats()
      .then((data) => setStats(data))
      .finally(() => setLoading(false));
  }, [activeMerchant]);

  // Sample analytics chart data
  const revenueTrendData = [
    { day: 'Mon', revenue: 420, orders: 12 },
    { day: 'Tue', revenue: 680, orders: 18 },
    { day: 'Wed', revenue: 540, orders: 15 },
    { day: 'Thu', revenue: 890, orders: 24 },
    { day: 'Fri', revenue: 1250, orders: 35 },
    { day: 'Sat', revenue: 1680, orders: 48 },
    { day: 'Sun', revenue: 1420, orders: 41 },
  ];

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3 text-slate-400">
          <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm">Loading merchant dashboard...</p>
        </div>
      </div>
    );
  }

  const isAppointmentType = activeMerchant?.business_type === 'salon' || activeMerchant?.business_type === 'dental';

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-800 p-8 shadow-xl">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold mb-3">
              <Store className="w-3.5 h-3.5" />
              <span>{activeMerchant?.name}</span>
            </div>
            <h2 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Merchant Management Overview
            </h2>
            <p className="text-slate-400 text-sm mt-1 max-w-2xl">
              Real-time multi-merchant monitoring, WhatsApp conversation status, and authoritative transactional operations.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => onNavigate('operations')}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold border border-slate-700 transition"
            >
              View {isAppointmentType ? 'Appointments' : 'Orders'}
            </button>
            <button
              onClick={() => onNavigate('simulator')}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold shadow-lg shadow-emerald-600/30 transition"
            >
              Open Live Simulator
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Metric 1 */}
        <div className="p-6 rounded-2xl bg-slate-800/60 border border-slate-800 shadow-sm hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-400">Total Customers</p>
            <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400">
              <Users className="w-5 h-5" />
            </div>
          </div>
          <p className="text-3xl font-bold text-white mt-3">{stats?.customers_count || 0}</p>
          <p className="text-xs text-emerald-400 flex items-center gap-1 mt-2 font-medium">
            <ArrowUpRight className="w-3.5 h-3.5" />
            <span>Active WhatsApp profiles</span>
          </p>
        </div>

        {/* Metric 2 */}
        <div className="p-6 rounded-2xl bg-slate-800/60 border border-slate-800 shadow-sm hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-400">
              {isAppointmentType ? 'Appointments' : 'Total Orders'}
            </p>
            <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400">
              <ShoppingBag className="w-5 h-5" />
            </div>
          </div>
          <p className="text-3xl font-bold text-white mt-3">{stats?.orders_or_appointments_count || 0}</p>
          <p className="text-xs text-slate-400 flex items-center gap-1 mt-2">
            <Clock className="w-3.5 h-3.5" />
            <span>Verified in PostgreSQL</span>
          </p>
        </div>

        {/* Metric 3 */}
        <div className="p-6 rounded-2xl bg-slate-800/60 border border-slate-800 shadow-sm hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-400">Gross Volume</p>
            <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400">
              <DollarSign className="w-5 h-5" />
            </div>
          </div>
          <p className="text-3xl font-bold text-white mt-3">${(stats?.total_revenue || 0).toFixed(2)}</p>
          <p className="text-xs text-emerald-400 flex items-center gap-1 mt-2 font-medium">
            <ArrowUpRight className="w-3.5 h-3.5" />
            <span>Authoritative sales</span>
          </p>
        </div>

        {/* Metric 4 */}
        <div className="p-6 rounded-2xl bg-slate-800/60 border border-slate-800 shadow-sm hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-slate-400">Pending Escalations</p>
            <div className="p-2.5 rounded-xl bg-rose-500/10 text-rose-400">
              <AlertCircle className="w-5 h-5" />
            </div>
          </div>
          <p className="text-3xl font-bold text-white mt-3">{stats?.pending_escalations || 0}</p>
          <p className="text-xs text-rose-400 mt-2 font-medium">
            {stats?.pending_escalations ? 'Requires human staff review' : 'No open escalations'}
          </p>
        </div>
      </div>

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-800/60 border border-slate-800">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-bold text-lg text-white">7-Day Transaction Activity</h3>
              <p className="text-xs text-slate-400">Authoritative orders and bookings volume</p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-slate-700 text-slate-300">
              Weekly
            </span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={revenueTrendData}>
                <defs>
                  <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="day" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '0.75rem' }} 
                  itemStyle={{ color: '#f8fafc' }}
                />
                <Area type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorRev)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Quick Diagnostics */}
        <div className="p-6 rounded-2xl bg-slate-800/60 border border-slate-800 space-y-4">
          <h3 className="font-bold text-lg text-white">Vera System Health</h3>
          <p className="text-xs text-slate-400">Core assistant status and guardrail metrics</p>

          <div className="space-y-3 pt-2">
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <div>
                  <p className="text-sm font-semibold text-white">AI Guardrails</p>
                  <p className="text-xs text-slate-400">Injection & Dental safety</p>
                </div>
              </div>
              <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                ACTIVE
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <BookOpen className="w-5 h-5 text-cyan-400" />
                <div>
                  <p className="text-sm font-semibold text-white">Knowledge Docs</p>
                  <p className="text-xs text-slate-400">{stats?.knowledge_docs_count || 0} indexed documents</p>
                </div>
              </div>
              <span className="px-2 py-0.5 rounded text-xs font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                READY
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Bell className="w-5 h-5 text-purple-400" />
                <div>
                  <p className="text-sm font-semibold text-white">Notification Jobs</p>
                  <p className="text-xs text-slate-400">{stats?.notifications_count || 0} alerts processed</p>
                </div>
              </div>
              <span className="px-2 py-0.5 rounded text-xs font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20">
                OPERATIONAL
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
