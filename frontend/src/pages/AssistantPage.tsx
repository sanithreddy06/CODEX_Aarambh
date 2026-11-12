import React, { useState, useRef, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Bot,
  Send,
  Sparkles,
  ShieldCheck,
  FileCode2,
  Cpu,
  Loader2,
  HelpCircle
} from 'lucide-react';
import { api } from '../lib/api';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<{ file: string; line: number; type: string; label: string; confidence: string }>;
  confidence?: string;
  provider_used?: string;
}

export const AssistantPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        'Hello! I am your CODEX Autonomous Code Intelligence Assistant.\n\nI answer queries strictly grounded in the verified static AST, dependency graphs, and schema definitions extracted from this repository. How can I assist you with understanding this application?',
      sources: [],
      provider_used: 'CODEX Knowledge Engine'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const query = textToSend || input;
    if (!query.trim() || !id || loading) return;

    const userMsg: ChatMessage = { role: 'user', content: query };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const historyPayload = messages.slice(-6).map((m) => ({ role: m.role, content: m.content }));
      const res = await api.sendChatMessage(id, query, historyPayload);

      const aiMsg: ChatMessage = {
        role: 'assistant',
        content: res.message,
        sources: res.sources,
        confidence: res.confidence,
        provider_used: res.provider_used
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Error communicating with intelligence engine: ${err.message || 'Unknown error'}`,
          sources: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const sampleQuestions = [
    'Explain how authentication works in this repository.',
    'Where is user registration implemented?',
    'Which APIs interact with the database models?',
    'Explain the complete order-placement workflow.',
    'What happens if the order service changes?'
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-6.5rem)] max-w-5xl mx-auto space-y-4">
      {/* Top Bar */}
      <div className="flex items-center justify-between pb-3 border-b border-neutral-800">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center space-x-2">
            <Bot className="w-5 h-5 text-indigo-400" />
            <span>AI Code Intelligence Assistant</span>
          </h1>
          <p className="text-xs text-neutral-400 mt-0.5">
            Evidence-backed technical answers grounded directly in discovered AST symbols and route topologies.
          </p>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-neutral-300">Deterministic & LLM Fallback Active</span>
        </div>
      </div>

      {/* Suggested Questions */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-1 text-xs">
        <span className="text-neutral-400 font-mono text-[11px] shrink-0">Try asking:</span>
        {sampleQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(q)}
            className="px-2.5 py-1 rounded-full bg-neutral-900 hover:bg-neutral-800 text-neutral-300 border border-neutral-800 text-[11px] shrink-0 transition"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4 rounded-xl bg-neutral-950/60 border border-neutral-800">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-2xl p-4 rounded-xl text-xs leading-relaxed space-y-3 ${
                m.role === 'user'
                  ? 'bg-indigo-600 text-white font-medium'
                  : 'bg-neutral-900 border border-neutral-800 text-neutral-200'
              }`}
            >
              <div className="whitespace-pre-line">{m.content}</div>

              {/* Citations & Evidence Sources */}
              {m.sources && m.sources.length > 0 && (
                <div className="pt-3 border-t border-neutral-800/80 space-y-1.5">
                  <div className="text-[10px] font-mono uppercase text-neutral-400 flex items-center space-x-1">
                    <ShieldCheck className="w-3 h-3 text-emerald-400" />
                    <span>VERIFIED CODE SOURCES ({m.sources.length})</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {m.sources.map((s, sIdx) => (
                      <span
                        key={sIdx}
                        className="px-2 py-0.5 rounded bg-neutral-950 text-indigo-300 font-mono text-[10px] border border-neutral-800"
                      >
                        {s.file}:{s.line}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {m.provider_used && (
                <div className="text-[10px] font-mono text-neutral-400 pt-1">
                  Engine: {m.provider_used}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center space-x-2 text-neutral-400 text-xs py-2">
            <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
            <span>Consulting static AST index and formulating evidence-based response...</span>
          </div>
        )}
        <div ref={scrollRef} />
      </div>

      {/* Input Box */}
      <div className="flex items-center space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask anything about the architecture, endpoints, database, or workflow logic..."
          className="flex-1 px-4 py-2.5 rounded-xl bg-neutral-900 border border-neutral-800 text-xs text-white placeholder:text-neutral-500 focus:outline-none focus:border-indigo-500 transition"
        />
        <button
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
          className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold shadow-sm transition flex items-center space-x-1.5"
        >
          <Send className="w-3.5 h-3.5" />
          <span>Send</span>
        </button>
      </div>
    </div>
  );
};
