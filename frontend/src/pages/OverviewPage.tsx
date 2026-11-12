import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Layers,
  Code2,
  Database,
  Globe2,
  Activity,
  ArrowRight,
  FileCode2,
  RefreshCw,
  ShieldCheck,
  CheckCircle2
} from 'lucide-react';
import { api, ProjectOverview } from '../lib/api';

export const OverviewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [overview, setOverview] = useState<ProjectOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchOverview = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const data = await api.getProjectOverview(id);
      setOverview(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
    const interval = setInterval(async () => {
      if (overview?.project.status === 'analyzing' || overview?.project.status === 'scanning') {
        const status = await api.getAnalysisStatus(id!);
        if (status.status === 'completed' || status.status === 'failed') {
          fetchOverview();
        }
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [id, overview?.project.status]);

  const handleReanalyze = async () => {
    if (!id) return;
    try {
      setRefreshing(true);
      await api.triggerAnalysis(id);
      await fetchOverview();
    } catch (e) {
      console.error(e);
    } finally {
      setRefreshing(false);
    }
  };

  if (loading && !overview) {
    return (
      <div className="p-12 text-center text-xs text-neutral-400">
        <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-indigo-400" />
        Extracting repository metrics...
      </div>
    );
  }

  if (!overview) {
    return <div className="p-8 text-neutral-400 text-xs">Project overview unavailable.</div>;
  }

  const { project } = overview;
  const isAnalyzing = project.status === 'analyzing' || project.status === 'scanning';

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Top Header Card */}
      <div className="p-6 rounded-xl bg-neutral-900/60 border border-neutral-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <h1 className="text-xl font-bold text-white tracking-tight">{project.name}</h1>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
              project.status === 'completed' ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800/40' :
              project.status === 'failed' ? 'bg-rose-950/60 text-rose-400 border-rose-800/40' :
              'bg-amber-950/60 text-amber-400 border-amber-800/40 animate-pulse'
            }`}>
              {project.status.toUpperCase()}
            </span>
          </div>
          <p className="text-xs text-neutral-400 mt-1 max-w-2xl">
            {project.description || `Ingested archive: ${project.original_archive_name}`}
          </p>
        </div>

        <div className="flex items-center space-x-3 shrink-0">
          <button
            onClick={handleReanalyze}
            disabled={isAnalyzing || refreshing}
            className="px-3 py-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-200 text-xs font-medium border border-neutral-700 flex items-center space-x-1.5 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isAnalyzing || refreshing ? 'animate-spin' : ''}`} />
            <span>{isAnalyzing ? 'Analyzing...' : 'Re-Run Analysis'}</span>
          </button>
          <Link
            to={`/projects/${id}/docs`}
            className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow-sm transition"
          >
            View Full Report
          </Link>
        </div>
      </div>

      {isAnalyzing && (
        <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-800/50 flex items-center space-x-3">
          <RefreshCw className="w-5 h-5 text-indigo-400 animate-spin shrink-0" />
          <div className="text-xs">
            <div className="font-semibold text-white">Reverse Engineering Pipeline Running</div>
            <div className="text-neutral-400 mt-0.5">Extracting AST definitions, mapping import dependencies, and reconstructing API routing table...</div>
          </div>
        </div>
      )}

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-neutral-900/40 border border-neutral-800">
          <div className="text-xs font-mono text-neutral-400">SOURCE CODE</div>
          <div className="text-2xl font-bold text-white mt-1">{overview.files_count} files</div>
          <div className="text-[11px] text-neutral-400 mt-0.5">{overview.lines_count.toLocaleString()} total lines</div>
        </div>

        <div className="p-4 rounded-xl bg-neutral-900/40 border border-neutral-800">
          <div className="text-xs font-mono text-neutral-400">REST ENDPOINTS</div>
          <div className="text-2xl font-bold text-indigo-400 mt-1">{overview.endpoints_count}</div>
          <div className="text-[11px] text-neutral-400 mt-0.5">Identified via AST decorators</div>
        </div>

        <div className="p-4 rounded-xl bg-neutral-900/40 border border-neutral-800">
          <div className="text-xs font-mono text-neutral-400">DATABASE ENTITIES</div>
          <div className="text-2xl font-bold text-purple-400 mt-1">{overview.models_count}</div>
          <div className="text-[11px] text-neutral-400 mt-0.5">ORM schemas & relational tables</div>
        </div>

        <div className="p-4 rounded-xl bg-neutral-900/40 border border-neutral-800">
          <div className="text-xs font-mono text-neutral-400">HEALTH SCORE</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{overview.health_score}/100</div>
          <div className="text-[11px] text-neutral-400 mt-0.5">Evidence-based safety score</div>
        </div>
      </div>

      {/* Two Column Section: Languages & Frameworks + Architecture Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Technologies */}
        <div className="p-5 rounded-xl bg-neutral-900/40 border border-neutral-800 space-y-4">
          <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
            <Code2 className="w-4 h-4 text-indigo-400" />
            <span>Languages & Frameworks</span>
          </h2>

          <div className="space-y-2">
            {project.languages?.map((lang) => (
              <div key={lang.language} className="flex items-center justify-between text-xs">
                <span className="text-neutral-300 font-medium">{lang.language}</span>
                <div className="flex items-center space-x-3">
                  <span className="text-neutral-400 font-mono">{lang.file_count} files</span>
                  <span className="text-neutral-400 font-mono w-10 text-right">{lang.percentage}%</span>
                </div>
              </div>
            ))}
          </div>

          <div className="pt-3 border-t border-neutral-800/80">
            <div className="text-[11px] font-mono text-neutral-400 uppercase mb-2">Detected Frameworks</div>
            <div className="flex flex-wrap gap-2">
              {project.frameworks?.map((fw) => (
                <span
                  key={fw.name}
                  className="px-2 py-1 rounded bg-neutral-800 text-neutral-200 border border-neutral-700/60 text-xs font-medium"
                >
                  {fw.name} {fw.version ? `(${fw.version})` : ''}
                </span>
              ))}
              {(!project.frameworks || project.frameworks.length === 0) && (
                <span className="text-xs text-neutral-400">Standard library implementation</span>
              )}
            </div>
          </div>
        </div>

        {/* Architecture Tier Distribution */}
        <div className="p-5 rounded-xl bg-neutral-900/40 border border-neutral-800 space-y-4">
          <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
            <Layers className="w-4 h-4 text-purple-400" />
            <span>Reconstructed Architecture Tiers</span>
          </h2>

          <div className="space-y-3">
            {Object.entries(overview.layers_breakdown || {}).map(([layer, count]) => (
              <div key={layer} className="text-xs">
                <div className="flex justify-between text-neutral-300 mb-1">
                  <span className="capitalize">{layer.replace('_', ' ')}</span>
                  <span className="font-mono text-neutral-400">{count} files</span>
                </div>
                <div className="w-full bg-neutral-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-indigo-500 h-1.5 rounded-full"
                    style={{ width: `${Math.min(100, (count / overview.files_count) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="pt-2">
            <Link
              to={`/projects/${id}/architecture`}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center space-x-1"
            >
              <span>Explore Interactive Architecture Graph</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
