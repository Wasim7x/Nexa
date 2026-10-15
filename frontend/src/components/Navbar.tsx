import React, { useEffect, useState } from 'react';
import { ApiClient } from '../services/api';
import { Merchant } from '../types';
import { 
  Building2, 
  Store, 
  Sparkles, 
  Activity, 
  MessageSquare, 
  ShieldCheck, 
  ChevronDown
} from 'lucide-react';

interface NavbarProps {
  activeMerchant: Merchant | null;
  onSelectMerchant: (merchant: Merchant) => void;
  onOpenSimulator: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeMerchant, onSelectMerchant, onOpenSimulator }) => {
  const [merchants, setMerchants] = useState<Merchant[]>([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  useEffect(() => {
    ApiClient.getMerchants().then((data) => {
      if (Array.isArray(data)) {
        setMerchants(data);
      }
    });
  }, []);

  const getMerchantIcon = (type?: string) => {
    switch (type) {
      case 'grocery':
        return <Store className="w-5 h-5 text-emerald-400" />;
      case 'sweets':
        return <Sparkles className="w-5 h-5 text-amber-400" />;
      case 'salon':
        return <Sparkles className="w-5 h-5 text-pink-400" />;
      case 'dental':
        return <Activity className="w-5 h-5 text-cyan-400" />;
      default:
        return <Building2 className="w-5 h-5 text-slate-400" />;
    }
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40 px-6 flex items-center justify-between">
      {/* Brand & Active Merchant Selector */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <span className="font-extrabold text-white text-lg tracking-wider">V</span>
          </div>
          <div>
            <h1 className="font-bold text-lg text-white leading-none tracking-tight">Vera</h1>
            <p className="text-[10px] text-emerald-400 font-medium tracking-wide uppercase">Multi-Merchant AI</p>
          </div>
        </div>

        <div className="h-6 w-px bg-slate-800" />

        {/* Merchant Dropdown */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-3 px-3.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 transition-all text-left shadow-sm"
          >
            <div className="p-1.5 rounded-md bg-slate-900/60">
              {getMerchantIcon(activeMerchant?.business_type)}
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-sm font-semibold text-white">{activeMerchant?.name || 'Select Merchant'}</span>
                <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {activeMerchant?.business_type || 'Tenant'}
                </span>
              </div>
              <p className="text-xs text-slate-400">Context: {activeMerchant?.slug || 'none'}</p>
            </div>
            <ChevronDown className="w-4 h-4 text-slate-400 ml-2" />
          </button>

          {dropdownOpen && (
            <div className="absolute left-0 mt-2 w-72 rounded-xl bg-slate-800 border border-slate-700 shadow-2xl py-2 z-50">
              <div className="px-3 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Switch Business Context
              </div>
              {merchants.map((m) => (
                <button
                  key={m.id}
                  onClick={() => {
                    onSelectMerchant(m);
                    setDropdownOpen(false);
                  }}
                  className={`w-full px-3 py-2.5 flex items-center gap-3 hover:bg-slate-700/60 transition text-left ${
                    activeMerchant?.id === m.id ? 'bg-emerald-500/10 text-emerald-300' : 'text-slate-200'
                  }`}
                >
                  <div className="p-1.5 rounded-lg bg-slate-900/80">
                    {getMerchantIcon(m.business_type)}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">{m.name}</p>
                    <p className="text-xs text-slate-400 capitalize">{m.business_type} • {m.slug}</p>
                  </div>
                  {activeMerchant?.id === m.id && (
                    <div className="w-2 h-2 rounded-full bg-emerald-400" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right side controls */}
      <div className="flex items-center gap-4">
        {/* Guardrail Status Badge */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Guardrails Enforced</span>
        </div>

        {/* WhatsApp Live Simulator Button */}
        <button
          onClick={onOpenSimulator}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm transition shadow-lg shadow-emerald-600/20 hover:scale-[1.02]"
        >
          <MessageSquare className="w-4 h-4" />
          <span>WhatsApp Simulator</span>
        </button>
      </div>
    </header>
  );
};
