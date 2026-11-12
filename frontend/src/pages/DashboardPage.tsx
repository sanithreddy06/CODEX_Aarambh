import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FolderGit2,
  FileCode2,
  Globe2,
  Layers,
  ArrowUpRight,
  Trash2,
  PlusCircle,
  Activity,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import { api, Project } from '../lib/api';

export const DashboardPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await api.getProjects();
      setProjects(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this analyzed project?')) return;
    try {
      setDeletingId(id);
      await api.deleteProject(id);
      setProjects((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      alert('Failed to delete project');
    } finally {
      setDeletingId(null);
    }
  };

  // Calculate actual statistics across all analyzed projects
  const totalProjects = projects.length;
  const totalFiles = projects.reduce((acc, p) => acc + (p.total_files || 0), 0);
  const totalLines = projects.reduce((acc, p) => acc + (p.total_lines || 0), 0);
  const languagesSet = new Set(projects.map((p) => p.primary_language).filter(Boolean));

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Intelligence Dashboard</h1>
          <p className="text-xs text-neutral-400 mt-1">
            Real-time status of scanned repositories and extracted architectural intelligence.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={loadProjects}
            className="p-2 rounded-lg bg-neutral-800/80 hover:bg-neutral-700 text-neutral-300 border border-neutral-700 text-xs transition flex items-center space-x-1.5"
            title="Refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <Link
            to="/upload"
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow-sm transition flex items-center space-x-1.5"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Analysis</span>
          </Link>
        </div>
      </div>

      {/* Aggregate Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="p-4 rounded-xl bg-neutral-900/60 border border-neutral-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-neutral-400">TOTAL REPOSITORIES</span>
            <FolderGit2 className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{totalProjects}</div>
          <div className="text-[11px] text-neutral-400 mt-1">Ingested via safe ZIP extraction</div>
        </div>

        <div className="p-4 rounded-xl bg-neutral-900/60 border border-neutral-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-neutral-400">FILES PARSED</span>
            <FileCode2 className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{totalFiles}</div>
          <div className="text-[11px] text-neutral-400 mt-1">{totalLines.toLocaleString()} total lines of code</div>
        </div>

        <div className="p-4 rounded-xl bg-neutral-900/60 border border-neutral-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-neutral-400">PRIMARY LANGUAGES</span>
            <Layers className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{languagesSet.size}</div>
          <div className="text-[11px] text-neutral-400 mt-1">Multi-language AST support</div>
        </div>

        <div className="p-4 rounded-xl bg-neutral-900/60 border border-neutral-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-neutral-400">ENGINE STATUS</span>
            <Activity className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2">Operational</div>
          <div className="text-[11px] text-neutral-400 mt-1">Static AST & Network Topology</div>
        </div>
      </div>

      {/* Projects List */}
      <div className="rounded-xl border border-neutral-800 bg-[#0d131f]/40 overflow-hidden">
        <div className="p-4 border-b border-neutral-800 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">Analyzed Projects</h2>
          <span className="text-xs text-neutral-400 font-mono">{projects.length} repository archives</span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-xs text-neutral-400">Loading projects...</div>
        ) : projects.length === 0 ? (
          <div className="p-12 text-center">
            <FolderGit2 className="w-10 h-10 text-neutral-600 mx-auto mb-3" />
            <p className="text-sm text-neutral-300 font-medium">No projects analyzed yet</p>
            <p className="text-xs text-neutral-400 mt-1 max-w-sm mx-auto">
              Upload an existing software project ZIP archive to generate full multi-tier architecture, API discovery, and AST intelligence.
            </p>
            <Link
              to="/upload"
              className="mt-4 inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Upload First Project</span>
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-neutral-800/80">
            {projects.map((proj) => (
              <div
                key={proj.id}
                className="p-4 flex items-center justify-between hover:bg-neutral-800/30 transition group"
              >
                <div className="flex items-center space-x-4 min-w-0">
                  <div className="w-10 h-10 rounded-lg bg-neutral-900 border border-neutral-800 flex items-center justify-center text-indigo-400 group-hover:border-indigo-500/50 transition">
                    <FolderGit2 className="w-5 h-5" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center space-x-2">
                      <Link
                        to={`/projects/${proj.id}`}
                        className="text-sm font-semibold text-white hover:text-indigo-400 transition truncate"
                      >
                        {proj.name}
                      </Link>
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                        proj.status === 'completed' ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/40' :
                        proj.status === 'failed' ? 'bg-rose-950/60 text-rose-400 border border-rose-800/40' :
                        'bg-amber-950/60 text-amber-400 border border-amber-800/40 animate-pulse'
                      }`}>
                        {proj.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="text-xs text-neutral-400 truncate mt-0.5 max-w-md">
                      {proj.description || proj.original_archive_name}
                    </div>
                    <div className="flex items-center space-x-3 mt-1.5 text-[11px] text-neutral-400 font-mono">
                      <span>{proj.primary_language || 'Polyglot'}</span>
                      <span>•</span>
                      <span>{proj.total_files} files</span>
                      <span>•</span>
                      <span>{proj.total_lines.toLocaleString()} lines</span>
                      <span>•</span>
                      <span className="text-emerald-400">Score: {proj.health_score}/100</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  <Link
                    to={`/projects/${proj.id}`}
                    className="px-3 py-1.5 rounded bg-neutral-800 hover:bg-neutral-700 text-xs font-medium text-neutral-200 transition flex items-center space-x-1"
                  >
                    <span>Inspect</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </Link>
                  <button
                    onClick={(e) => handleDelete(proj.id, e)}
                    disabled={deletingId === proj.id}
                    className="p-1.5 rounded hover:bg-rose-950/40 text-neutral-400 hover:text-rose-400 transition"
                    title="Delete Project"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
