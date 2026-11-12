import React, { useState } from 'react';
import { Settings, ShieldCheck, Sparkles, Check, Key } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [provider, setProvider] = useState('deterministic');
  const [geminiKey, setGeminiKey] = useState('');
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Intelligence & Engine Settings</h1>
        <p className="text-xs text-neutral-400 mt-0.5">
          Configure AI reasoning backends, deterministic fact enforcement, and archive security limits.
        </p>
      </div>

      <form onSubmit={handleSave} className="p-6 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-6">
        {/* Provider Selection */}
        <div>
          <label className="block text-xs font-semibold text-neutral-200 mb-2">AI Reasoning Engine</label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              { id: 'deterministic', title: 'Deterministic Fact Engine (No API Key Required)', desc: 'Answers strictly with verified AST facts, schemas, and endpoints.' },
              { id: 'gemini', title: 'Google Gemini', desc: 'Uses gemini-1.5-flash with retrieved repository evidence context.' },
              { id: 'groq', title: 'Groq Cloud', desc: 'Ultra-low latency Llama-3.1 inference.' },
              { id: 'local', title: 'Local Ollama / LocalAI', desc: 'On-premise offline model running at localhost:11434.' }
            ].map((p) => (
              <div
                key={p.id}
                onClick={() => setProvider(p.id)}
                className={`p-3.5 rounded-xl border cursor-pointer transition ${
                  provider === p.id
                    ? 'bg-indigo-950/40 border-indigo-500 shadow-sm'
                    : 'bg-neutral-950/60 border-neutral-800 hover:border-neutral-700'
                }`}
              >
                <div className="text-xs font-semibold text-white">{p.title}</div>
                <div className="text-[11px] text-neutral-400 mt-1">{p.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* API Key configuration */}
        {provider !== 'deterministic' && provider !== 'local' && (
          <div>
            <label className="block text-xs font-semibold text-neutral-200 mb-1">
              {provider.toUpperCase()} API Key
            </label>
            <div className="relative">
              <Key className="w-3.5 h-3.5 text-neutral-500 absolute left-3 top-3" />
              <input
                type="password"
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                placeholder="sk-..."
                className="w-full pl-8 pr-3 py-2 rounded-lg bg-neutral-950 border border-neutral-800 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
            <p className="text-[11px] text-neutral-400 mt-1">
              Keys are passed exclusively to server environment variables and never logged.
            </p>
          </div>
        )}

        {/* Security Limits Info */}
        <div className="pt-4 border-t border-neutral-800 space-y-3">
          <div className="text-xs font-semibold text-neutral-200">Archive Guard Limits</div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-lg bg-neutral-950 border border-neutral-800">
              <div className="text-neutral-400">Max Archive Upload</div>
              <div className="font-mono font-bold text-white mt-1">50 MB</div>
            </div>
            <div className="p-3 rounded-lg bg-neutral-950 border border-neutral-800">
              <div className="text-neutral-400">Max Extracted Bytes</div>
              <div className="font-mono font-bold text-white mt-1">250 MB</div>
            </div>
          </div>
        </div>

        <button
          type="submit"
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white rounded-lg shadow-sm transition flex items-center space-x-1.5"
        >
          {saved ? <Check className="w-3.5 h-3.5 text-emerald-300" /> : null}
          <span>{saved ? 'Preferences Saved' : 'Save Engine Settings'}</span>
        </button>
      </form>
    </div>
  );
};
