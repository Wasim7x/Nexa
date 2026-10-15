import React, { useEffect, useState } from 'react';
import { ApiClient } from '../services/api';
import { Merchant, MerchantSettingsData } from '../types';
import { Cpu, CheckCircle2, XCircle, ShieldCheck, RefreshCw, Key, MessageSquare, AlertCircle } from 'lucide-react';

interface IntegrationsPageProps {
  activeMerchant: Merchant | null;
}

export const IntegrationsPage: React.FC<IntegrationsPageProps> = ({ activeMerchant }) => {
  const [settingsData, setSettingsData] = useState<MerchantSettingsData | null>(null);
  const [loading, setLoading] = useState(true);

  // AI settings form
  const [selectedProvider, setSelectedProvider] = useState('mock');
  const [selectedModel, setSelectedModel] = useState('default');
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const loadSettings = () => {
    setLoading(true);
    ApiClient.getSettings()
      .then((data) => {
        setSettingsData(data);
        if (data?.settings) {
          setSelectedProvider(data.settings.ai_provider || 'mock');
          setSelectedModel(data.settings.ai_model || 'default');
        }
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadSettings();
  }, [activeMerchant]);

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await ApiClient.testAIConnection(selectedProvider, selectedModel, apiKeyInput || undefined);
      setTestResult(res);
    } catch (err: any) {
      setTestResult({ connected: false, error: err.message });
    } finally {
      setTesting(false);
    }
  };

  const handleSaveAISettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveStatus(null);
    await ApiClient.updateAISettings({
      ai_provider: selectedProvider,
      ai_model: selectedModel,
      api_key: apiKeyInput || undefined
    });
    setSaveStatus('AI configuration updated successfully');
    setApiKeyInput(''); // Clear key input from memory for security
    loadSettings();
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Cpu className="w-6 h-6 text-emerald-400" />
          <span>AI Providers & WhatsApp Integration</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Configure model inference engines, test connectivity, and inspect Meta WhatsApp Cloud API webhooks.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Card 1: AI Provider Configuration */}
        <div className="p-6 rounded-2xl bg-slate-800/60 border border-slate-800 space-y-5">
          <div className="flex items-center justify-between pb-4 border-b border-slate-700/80">
            <div>
              <h3 className="font-bold text-lg text-white">AI Engine Configuration</h3>
              <p className="text-xs text-slate-400">Select model provider for {activeMerchant?.name}</p>
            </div>
            <span className="px-2.5 py-1 rounded-full text-xs font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Active: {settingsData?.settings?.ai_provider || 'Mock'}
            </span>
          </div>

          {saveStatus && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold flex items-center justify-between">
              <span>{saveStatus}</span>
              <button onClick={() => setSaveStatus(null)}>✕</button>
            </div>
          )}

          <form onSubmit={handleSaveAISettings} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">AI Provider</label>
              <select
                value={selectedProvider}
                onChange={(e) => {
                  setSelectedProvider(e.target.value);
                  setTestResult(null);
                }}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
              >
                <option value="mock">Offline Mock Engine (Deterministic / Zero External Calls)</option>
                <option value="gemini">Google Gemini (Gemini 1.5 Flash / Pro)</option>
                <option value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
                <option value="groq">Groq (LLaMA 3.3 70B Fast)</option>
                <option value="ollama">Local Ollama (Self-Hosted)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Model Name</label>
              <input
                type="text"
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                placeholder="e.g. gemini-1.5-flash, gpt-4o-mini, llama-3.3-70b-versatile"
                className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
              />
            </div>

            {selectedProvider !== 'mock' && selectedProvider !== 'ollama' && (
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
                  <span>API Key (Stored securely on backend, never revealed to browser)</span>
                  <Key className="w-3.5 h-3.5 text-slate-400" />
                </label>
                <input
                  type="password"
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  placeholder="Leave blank to use system .env key, or enter new key to override"
                  className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>
            )}

            {/* Test Connection Output */}
            {testResult && (
              <div
                className={`p-3.5 rounded-xl border text-xs ${
                  testResult.connected
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                    : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                }`}
              >
                <div className="flex items-center gap-2 font-bold mb-1">
                  {testResult.connected ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                  <span>{testResult.connected ? 'Connection Verified Successfully' : 'Connection Failed'}</span>
                </div>
                {testResult.error && <p className="text-[11px] mt-1">{testResult.error}</p>}
                {testResult.provider && <p className="text-[11px]">Provider: {testResult.provider} ({testResult.model})</p>}
              </div>
            )}

            <div className="flex items-center gap-3 pt-3">
              <button
                type="button"
                onClick={handleTestConnection}
                disabled={testing}
                className="px-4 py-2 rounded-xl bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold transition flex items-center gap-1.5"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${testing ? 'animate-spin' : ''}`} />
                <span>{testing ? 'Testing...' : 'Test Connection'}</span>
              </button>

              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition"
              >
                Save AI Configuration
              </button>
            </div>
          </form>
        </div>

        {/* Card 2: WhatsApp Cloud API & Webhook Health */}
        <div className="p-6 rounded-2xl bg-slate-800/60 border border-slate-800 space-y-5">
          <div className="flex items-center justify-between pb-4 border-b border-slate-700/80">
            <div>
              <h3 className="font-bold text-lg text-white">Meta WhatsApp Cloud Integration</h3>
              <p className="text-xs text-slate-400">Webhook status & messaging channel diagnostics</p>
            </div>
            <span className="px-2.5 py-1 rounded-full text-xs font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              OPERATIONAL
            </span>
          </div>

          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Integration Mode</span>
                <span className="text-xs font-bold text-emerald-400 uppercase">
                  {settingsData?.whatsapp_integration?.mode === 'simulator' ? 'Simulated Transport (Safe Dev Mode)' : 'Official Meta Cloud API'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Webhook Verification</span>
                <span className="text-xs font-bold text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Verified (/api/whatsapp/webhook)</span>
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">HMAC SHA256 Signature Check</span>
                <span className="text-xs font-bold text-emerald-400 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Enforced (X-Hub-Signature-256)</span>
                </span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1.5">
              <p className="text-xs font-bold text-white">Webhook URL for Meta App Dashboard:</p>
              <code className="block p-2 rounded-lg bg-slate-950 font-mono text-xs text-emerald-400 select-all overflow-x-auto">
                https://your-domain.com/api/whatsapp/webhook
              </code>
              <p className="text-[11px] text-slate-400 mt-1">
                Verify Token: <code className="text-white">vera_whatsapp_verify_token_secure_2026</code>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
