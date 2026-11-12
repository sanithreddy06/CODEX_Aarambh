import React, { useState, useEffect } from 'react';
import { Settings, ShieldCheck, Sparkles, Check, Key, Activity, AlertCircle, RefreshCw, Server, Lock } from 'lucide-react';
import { api, SettingsData } from '../lib/api';

export const SettingsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [provider, setProvider] = useState<string>('deterministic');
  
  // API Keys (only stored when typing a new key to send, never read from backend)
  const [geminiKey, setGeminiKey] = useState('');
  const [groqKey, setGroqKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [openaiBaseUrl, setOpenaiBaseUrl] = useState('');
  const [localModelUrl, setLocalModelUrl] = useState('');

  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [saveStatus, setSaveStatus] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const data = await api.getSettings();
      setSettings(data);
      setProvider(data.provider);
      setOpenaiBaseUrl(data.openai_base_url || 'https://api.openai.com/v1');
      setLocalModelUrl(data.local_model_url || 'http://localhost:11434/v1');
    } catch (err: any) {
      setSaveStatus({ success: false, message: 'Failed to connect to backend engine: ' + err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      let activeKey: string | undefined = undefined;
      let activeBase: string | undefined = undefined;

      if (provider === 'gemini') activeKey = geminiKey || undefined;
      else if (provider === 'groq') activeKey = groqKey || undefined;
      else if (provider === 'openai') {
        activeKey = openaiKey || undefined;
        activeBase = openaiBaseUrl || undefined;
      } else if (provider === 'local') {
        activeBase = localModelUrl || undefined;
      }

      const res = await api.testProvider(provider, activeKey, activeBase);
      setTestResult(res);
    } catch (err: any) {
      setTestResult({ success: false, message: err.message || 'Connection test failed' });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveStatus(null);

    try {
      const payload: any = { provider };
      if (geminiKey.trim()) payload.gemini_api_key = geminiKey.trim();
      if (groqKey.trim()) payload.groq_api_key = groqKey.trim();
      if (openaiKey.trim()) payload.openai_api_key = openaiKey.trim();
      if (openaiBaseUrl.trim()) payload.openai_base_url = openaiBaseUrl.trim();
      if (localModelUrl.trim()) payload.local_model_url = localModelUrl.trim();

      const updated = await api.updateSettings(payload);
      setSettings(updated);
      setSaveStatus({ success: true, message: 'Settings saved and engine reloaded successfully!' });
      
      // Clear key input fields after successful save
      setGeminiKey('');
      setGroqKey('');
      setOpenaiKey('');

      setTimeout(() => setSaveStatus(null), 4000);
    } catch (err: any) {
      setSaveStatus({ success: false, message: 'Failed to save settings: ' + err.message });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-16 max-w-3xl flex flex-col items-center justify-center space-y-3">
        <RefreshCw className="w-6 h-6 text-indigo-400 animate-spin" />
        <p className="text-xs text-neutral-400">Loading engine configuration...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center space-x-2">
            <Settings className="w-5 h-5 text-indigo-400" />
            <span>Intelligence & Engine Settings</span>
          </h1>
          <p className="text-xs text-neutral-400 mt-0.5">
            Configure AI reasoning engines, deterministic AST fact verification, and security controls.
          </p>
        </div>
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-800/80 text-[11px] text-emerald-400 font-medium">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Localhost Single-User Mode</span>
        </div>
      </div>

      {saveStatus && (
        <div
          className={`p-3.5 rounded-xl border text-xs flex items-center space-x-2 ${
            saveStatus.success
              ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
              : 'bg-rose-950/40 border-rose-800 text-rose-300'
          }`}
        >
          {saveStatus.success ? <Check className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
          <span>{saveStatus.message}</span>
        </div>
      )}

      <form onSubmit={handleSave} className="p-6 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-6">
        {/* Provider Selection */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-semibold text-neutral-200">AI Reasoning Provider</label>
            <span className="text-[11px] text-indigo-400 font-mono">Current: {provider.toUpperCase()}</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              {
                id: 'deterministic',
                title: 'Deterministic Fact Engine (No API Key)',
                desc: 'Operates with strict AST factual evidence guarantees and zero hallucination.',
                status: 'Default & Offline'
              },
              {
                id: 'gemini',
                title: 'Google Gemini',
                desc: 'Fast multimodal reasoning using gemini-1.5-flash with repo evidence context.',
                status: settings?.has_gemini_key ? 'Key Configured' : 'Needs API Key'
              },
              {
                id: 'groq',
                title: 'Groq Cloud',
                desc: 'Ultra-fast Llama-3.1 inference for architectural queries.',
                status: settings?.has_groq_key ? 'Key Configured' : 'Needs API Key'
              },
              {
                id: 'openai',
                title: 'OpenAI (or Compatible)',
                desc: 'GPT-4o-mini or self-hosted OpenAI-compatible endpoint.',
                status: settings?.has_openai_key ? 'Key Configured' : 'Needs API Key'
              },
              {
                id: 'local',
                title: 'Local Ollama / LocalAI',
                desc: 'Fully air-gapped on-premise model running at localhost:11434.',
                status: 'Self-Hosted'
              }
            ].map((p) => {
              const isSelected = provider === p.id;
              return (
                <div
                  key={p.id}
                  onClick={() => {
                    setProvider(p.id);
                    setTestResult(null);
                  }}
                  className={`p-3.5 rounded-xl border cursor-pointer transition flex flex-col justify-between ${
                    isSelected
                      ? 'bg-indigo-950/40 border-indigo-500 shadow-sm ring-1 ring-indigo-500/50'
                      : 'bg-neutral-950/60 border-neutral-800 hover:border-neutral-700'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-white">{p.title}</span>
                      {isSelected && <Check className="w-3.5 h-3.5 text-indigo-400" />}
                    </div>
                    <p className="text-[11px] text-neutral-400 mt-1 leading-relaxed">{p.desc}</p>
                  </div>
                  <div className="mt-2.5 pt-2 border-t border-neutral-800/60 flex items-center justify-between text-[10px]">
                    <span className="text-neutral-500 font-mono">Status:</span>
                    <span
                      className={`font-medium ${
                        p.status.includes('Configured') || p.status.includes('Default')
                          ? 'text-emerald-400'
                          : 'text-neutral-400'
                      }`}
                    >
                      {p.status}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Dynamic Provider Configuration */}
        {provider === 'gemini' && (
          <div className="p-4 rounded-lg bg-neutral-950 border border-neutral-800 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-neutral-200">Google Gemini API Key</label>
              {settings?.has_gemini_key && (
                <span className="text-[10px] bg-emerald-950/80 text-emerald-400 px-2 py-0.5 rounded border border-emerald-800 flex items-center space-x-1">
                  <Check className="w-3 h-3" />
                  <span>Key Active on Server</span>
                </span>
              )}
            </div>
            <div className="relative">
              <Key className="w-3.5 h-3.5 text-neutral-500 absolute left-3 top-3" />
              <input
                type="password"
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                placeholder={settings?.has_gemini_key ? '•••••••••••••••• (Leave blank to keep current)' : 'AIzaSy...'}
                className="w-full pl-8 pr-3 py-2 rounded-lg bg-neutral-900 border border-neutral-800 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
            <p className="text-[11px] text-neutral-400">
              API keys are persisted locally in <code className="text-neutral-300">data/storage/settings.json</code> and never transmitted to client browsers.
            </p>
          </div>
        )}

        {provider === 'groq' && (
          <div className="p-4 rounded-lg bg-neutral-950 border border-neutral-800 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-neutral-200">Groq Cloud API Key</label>
              {settings?.has_groq_key && (
                <span className="text-[10px] bg-emerald-950/80 text-emerald-400 px-2 py-0.5 rounded border border-emerald-800 flex items-center space-x-1">
                  <Check className="w-3 h-3" />
                  <span>Key Active on Server</span>
                </span>
              )}
            </div>
            <div className="relative">
              <Key className="w-3.5 h-3.5 text-neutral-500 absolute left-3 top-3" />
              <input
                type="password"
                value={groqKey}
                onChange={(e) => setGroqKey(e.target.value)}
                placeholder={settings?.has_groq_key ? '•••••••••••••••• (Leave blank to keep current)' : 'gsk_...'}
                className="w-full pl-8 pr-3 py-2 rounded-lg bg-neutral-900 border border-neutral-800 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
          </div>
        )}

        {provider === 'openai' && (
          <div className="p-4 rounded-lg bg-neutral-950 border border-neutral-800 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-neutral-200">OpenAI API Key</label>
              {settings?.has_openai_key && (
                <span className="text-[10px] bg-emerald-950/80 text-emerald-400 px-2 py-0.5 rounded border border-emerald-800 flex items-center space-x-1">
                  <Check className="w-3 h-3" />
                  <span>Key Active on Server</span>
                </span>
              )}
            </div>
            <div className="relative">
              <Key className="w-3.5 h-3.5 text-neutral-500 absolute left-3 top-3" />
              <input
                type="password"
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                placeholder={settings?.has_openai_key ? '•••••••••••••••• (Leave blank to keep current)' : 'sk-...'}
                className="w-full pl-8 pr-3 py-2 rounded-lg bg-neutral-900 border border-neutral-800 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
            <div>
              <label className="text-[11px] font-medium text-neutral-400 mb-1 block">API Base URL</label>
              <input
                type="text"
                value={openaiBaseUrl}
                onChange={(e) => setOpenaiBaseUrl(e.target.value)}
                placeholder="https://api.openai.com/v1"
                className="w-full px-3 py-1.5 rounded-lg bg-neutral-900 border border-neutral-800 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
          </div>
        )}

        {provider === 'local' && (
          <div className="p-4 rounded-lg bg-neutral-950 border border-neutral-800 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-neutral-200">Local Model Server URL</label>
              <span className="text-[10px] text-neutral-400 font-mono">Ollama / LocalAI / vLLM</span>
            </div>
            <div className="relative">
              <Server className="w-3.5 h-3.5 text-neutral-500 absolute left-3 top-3" />
              <input
                type="text"
                value={localModelUrl}
                onChange={(e) => setLocalModelUrl(e.target.value)}
                placeholder="http://localhost:11434/v1"
                className="w-full pl-8 pr-3 py-2 rounded-lg bg-neutral-900 border border-neutral-800 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
            <p className="text-[11px] text-neutral-400">
              CODEX connects locally to any OpenAI-compatible v1 chat completions endpoint without internet connectivity.
            </p>
          </div>
        )}

        {/* Connection Test Result */}
        {testResult && (
          <div
            className={`p-3 rounded-lg border text-xs flex items-center space-x-2 ${
              testResult.success
                ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
                : 'bg-rose-950/40 border-rose-800 text-rose-300'
            }`}
          >
            {testResult.success ? <Check className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
            <span>{testResult.message}</span>
          </div>
        )}

        {/* Security Limits Info */}
        <div className="pt-4 border-t border-neutral-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-neutral-200">Archive Guard Limits & Isolation</span>
            <span className="text-[11px] text-neutral-500">Enforced during streaming upload</span>
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-lg bg-neutral-950 border border-neutral-800">
              <div className="text-neutral-400 text-[11px]">Max Archive Upload</div>
              <div className="font-mono font-bold text-white mt-1">
                {settings?.max_upload_size_mb || 200} MB
              </div>
              <div className="text-[10px] text-neutral-500 mt-0.5">Streaming chunk limit</div>
            </div>
            <div className="p-3 rounded-lg bg-neutral-950 border border-neutral-800">
              <div className="text-neutral-400 text-[11px]">Max Extracted Bytes</div>
              <div className="font-mono font-bold text-white mt-1">
                {settings?.max_uncompressed_size_mb || 1000} MB
              </div>
              <div className="text-[10px] text-neutral-500 mt-0.5">Decompressed zip-slip guard</div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="pt-2 flex items-center justify-between">
          <button
            type="button"
            onClick={handleTestConnection}
            disabled={testing}
            className="px-3.5 py-2 bg-neutral-800 hover:bg-neutral-700 disabled:opacity-50 text-xs font-medium text-neutral-200 rounded-lg transition flex items-center space-x-1.5"
          >
            <Activity className={`w-3.5 h-3.5 ${testing ? 'animate-spin text-indigo-400' : ''}`} />
            <span>{testing ? 'Testing Connection...' : `Test ${provider.toUpperCase()} Connection`}</span>
          </button>

          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-xs font-semibold text-white rounded-lg shadow-sm transition flex items-center space-x-1.5"
          >
            {saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5 text-emerald-300" />}
            <span>{saving ? 'Saving...' : 'Save Engine Settings'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
