import React from 'react';
import { 
  LayoutDashboard, 
  BookOpen, 
  Package, 
  Users, 
  ShoppingBag, 
  Headset, 
  Tag, 
  Cpu, 
  Settings, 
  MessageSquare
} from 'lucide-react';

export type PageId = 
  | 'overview' 
  | 'knowledge' 
  | 'products' 
  | 'customers' 
  | 'operations' 
  | 'escalations' 
  | 'offers' 
  | 'integrations' 
  | 'settings' 
  | 'simulator';

interface SidebarProps {
  currentPage: PageId;
  onSelectPage: (page: PageId) => void;
  pendingEscalationsCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentPage, onSelectPage, pendingEscalationsCount = 0 }) => {
  const navItems = [
    { id: 'overview' as PageId, label: 'Overview', icon: LayoutDashboard },
    { id: 'knowledge' as PageId, label: 'Knowledge Base', icon: BookOpen },
    { id: 'products' as PageId, label: 'Products & Services', icon: Package },
    { id: 'customers' as PageId, label: 'Customers', icon: Users },
    { id: 'operations' as PageId, label: 'Orders & Bookings', icon: ShoppingBag },
    { 
      id: 'escalations' as PageId, 
      label: 'Human Assistant', 
      icon: Headset, 
      badge: pendingEscalationsCount > 0 ? String(pendingEscalationsCount) : undefined 
    },
    { id: 'offers' as PageId, label: 'Offers & Campaigns', icon: Tag },
    { id: 'integrations' as PageId, label: 'AI & Integrations', icon: Cpu },
    { id: 'settings' as PageId, label: 'General Settings', icon: Settings },
    { id: 'simulator' as PageId, label: 'WhatsApp Simulator', icon: MessageSquare, highlight: true }
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/50 flex flex-col shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="p-4 space-y-1">
        <p className="px-3 py-2 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
          Merchant Console
        </p>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onSelectPage(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all ${
                item.highlight
                  ? isActive
                    ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/30 font-semibold'
                    : 'bg-emerald-950/40 text-emerald-400 hover:bg-emerald-900/40 border border-emerald-800/40'
                  : isActive
                  ? 'bg-slate-800 text-white shadow-sm font-semibold border border-slate-700/80'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>

              {item.badge && (
                <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-rose-500 text-white">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="mt-auto p-4 border-t border-slate-800/80">
        <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-semibold text-slate-200">Nexa Engine Live</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Multi-tenant isolation active</p>
        </div>
      </div>
    </aside>
  );
};
