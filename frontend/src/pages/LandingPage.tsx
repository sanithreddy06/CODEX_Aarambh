import React from 'react';
import { Link } from 'react-router-dom';
import {
  Cpu,
  Layers,
  Network,
  Database,
  Globe2,
  FileText,
  ShieldCheck,
  Bot,
  ArrowRight,
  Terminal,
  CheckCircle2,
  Sparkles
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#0b0f17] text-neutral-200">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-24 border-b border-neutral-800/80">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(99,102,241,0.15),rgba(255,255,255,0))] pointer-events-none" />

        <div className="container mx-auto px-4 max-w-5xl text-center relative z-10">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-950/60 border border-indigo-800/50 text-indigo-400 text-xs font-mono mb-6">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Autonomous Software Reverse Engineering & Intelligence</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-tight sm:leading-none">
            Turn Any Codebase Into <br />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-300 to-indigo-200">
              Interactive Architectural Intelligence
            </span>
          </h1>

          <p className="mt-6 text-base sm:text-lg text-neutral-400 max-w-2xl mx-auto leading-relaxed">
            CODEX parses ASTs, graphs internal module topologies, discovers API endpoints, reconstructs database schemas, and reconstructs execution workflows without relying on missing documentation.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <Link
              to="/upload"
              className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-lg shadow-lg shadow-indigo-600/25 transition flex items-center space-x-2"
            >
              <span>Analyze a Repository</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/dashboard"
              className="px-6 py-3 bg-neutral-800/80 hover:bg-neutral-700/80 text-neutral-200 border border-neutral-700 font-medium rounded-lg transition"
            >
              View Analyzed Projects
            </Link>
          </div>

          {/* Principle Bar */}
          <div className="mt-12 inline-flex items-center space-x-4 px-4 py-2 rounded-lg bg-neutral-900/60 border border-neutral-800 text-xs font-mono text-neutral-400">
            <span className="text-indigo-400 font-semibold">CORE PRINCIPLE:</span>
            <span>CODE</span>
            <span className="text-neutral-600">→</span>
            <span>UNDERSTANDING</span>
            <span className="text-neutral-600">→</span>
            <span className="text-emerald-400">INTELLIGENCE</span>
          </div>
        </div>
      </section>

      {/* Core Capabilities */}
      <section className="py-20 border-b border-neutral-800/80 bg-[#0d131f]/30">
        <div className="container mx-auto px-4 max-w-6xl">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Engineered For Complex & Legacy Software
            </h2>
            <p className="text-sm text-neutral-400 mt-2">
              Verifiable static evidence powering dynamic architecture and AI reasoning.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-xl bg-neutral-900/40 border border-neutral-800 hover:border-indigo-500/40 transition">
              <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4">
                <Layers className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-white text-base">Multi-Tier Architecture Reconstruction</h3>
              <p className="text-xs text-neutral-400 mt-2 leading-relaxed">
                Autonomously classifies Presentation, API, Business Logic, Data Access, and Database tiers directly from import topologies and decorators.
              </p>
            </div>

            <div className="p-6 rounded-xl bg-neutral-900/40 border border-neutral-800 hover:border-indigo-500/40 transition">
              <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-4">
                <Network className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-white text-base">Dependency Graph & Blast Radius</h3>
              <p className="text-xs text-neutral-400 mt-2 leading-relaxed">
                Uncovers circular dependencies, module hubs, isolated modules, and calculates transitive impact before you touch any code.
              </p>
            </div>

            <div className="p-6 rounded-xl bg-neutral-900/40 border border-neutral-800 hover:border-indigo-500/40 transition">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-4">
                <Database className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-white text-base">Database Reverse Engineering</h3>
              <p className="text-xs text-neutral-400 mt-2 leading-relaxed">
                Extracts persistent tables, field constraints, primary/foreign keys, and renders interactive ER diagrams across SQLAlchemy, Prisma, and SQL.
              </p>
            </div>

            <div className="p-6 rounded-xl bg-neutral-900/40 border border-neutral-800 hover:border-indigo-500/40 transition">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-4">
                <Globe2 className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-white text-base">Automated API Discovery</h3>
              <p className="text-xs text-neutral-400 mt-2 leading-relaxed">
                Detects FastAPI, Express, Flask, and Spring routes, extracting HTTP verbs, parameters, auth middleware, and generates OpenAPI 3.0 specs.
              </p>
            </div>

            <div className="p-6 rounded-xl bg-neutral-900/40 border border-neutral-800 hover:border-indigo-500/40 transition">
              <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-4">
                <Bot className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-white text-base">Evidence-Grounded AI Assistant</h3>
              <p className="text-xs text-neutral-400 mt-2 leading-relaxed">
                Answers repository questions citing exact file paths and line ranges, with a deterministic factual engine fallback when no API key is set.
              </p>
            </div>

            <div className="p-6 rounded-xl bg-neutral-900/40 border border-neutral-800 hover:border-indigo-500/40 transition">
              <div className="w-10 h-10 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400 mb-4">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-white text-base">Security & Health Auditing</h3>
              <p className="text-xs text-neutral-400 mt-2 leading-relaxed">
                Protected against Zip Slip attacks; flags hardcoded credentials, API keys, high-complexity hotspots, and legacy tech debt.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-20 border-b border-neutral-800/80">
        <div className="container mx-auto px-4 max-w-5xl">
          <div className="text-center mb-16">
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">How CODEX Operates</h2>
            <p className="text-sm text-neutral-400 mt-2">Zero hallucinations. 100% deterministic code intelligence.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="p-5 rounded-lg bg-neutral-900/30 border border-neutral-800 text-center">
              <div className="text-indigo-400 font-mono font-bold text-xl mb-2">01</div>
              <h4 className="font-semibold text-white text-sm">Safe Ingestion</h4>
              <p className="text-xs text-neutral-400 mt-1">Upload ZIP archive; validated against Zip bombs and directory traversal.</p>
            </div>
            <div className="p-5 rounded-lg bg-neutral-900/30 border border-neutral-800 text-center">
              <div className="text-indigo-400 font-mono font-bold text-xl mb-2">02</div>
              <h4 className="font-semibold text-white text-sm">AST Parsing</h4>
              <p className="text-xs text-neutral-400 mt-1">Multi-language abstract syntax tree extraction for classes, routines, and calls.</p>
            </div>
            <div className="p-5 rounded-lg bg-neutral-900/30 border border-neutral-800 text-center">
              <div className="text-indigo-400 font-mono font-bold text-xl mb-2">03</div>
              <h4 className="font-semibold text-white text-sm">Topology Graphing</h4>
              <p className="text-xs text-neutral-400 mt-1">Constructs directed graph for dependencies, routes, and database entities.</p>
            </div>
            <div className="p-5 rounded-lg bg-neutral-900/30 border border-neutral-800 text-center">
              <div className="text-indigo-400 font-mono font-bold text-xl mb-2">04</div>
              <h4 className="font-semibold text-white text-sm">Actionable Report</h4>
              <p className="text-xs text-neutral-400 mt-1">Export full markdown, JSON, or PDF specs with reconstructed unit & integration tests.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 bg-[#090d14] text-center text-xs text-neutral-400 border-t border-neutral-800">
        <p>Project CODEX — PS06 • Aarambh Hackathon — Orion, School of Computer Science & Engineering</p>
      </footer>
    </div>
  );
};
