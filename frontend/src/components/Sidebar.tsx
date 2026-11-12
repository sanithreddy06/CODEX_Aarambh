import React from 'react';
import { NavLink, useParams } from 'react-router-dom';
import {
  Layers,
  Network,
  Code2,
  Database,
  Globe2,
  Bot,
  FileText,
  TestTube2,
  Activity,
  Workflow,
  BarChart3,
  ChevronRight
} from 'lucide-react';

interface Props {
  projectName?: string;
  primaryLang?: string;
  healthScore?: number;
}

export const Sidebar: React.FC<Props> = ({ projectName, primaryLang, healthScore = 100 }) => {
  const { id } = useParams<{ id: string }>();

  const links = [
    { to: `/projects/${id}`, label: 'Overview', icon: BarChart3, exact: true },
    { to: `/projects/${id}/architecture`, label: 'Architecture Explorer', icon: Layers },
    { to: `/projects/${id}/dependencies`, label: 'Dependency Graph', icon: Network },
    { to: `/projects/${id}/code`, label: 'Code & AST Explorer', icon: Code2 },
    { to: `/projects/${id}/database`, label: 'Database Models', icon: Database },
    { to: `/projects/${id}/apis`, label: 'API Explorer', icon: Globe2 },
    { to: `/projects/${id}/workflows`, label: 'Workflows', icon: Workflow },
    { to: `/projects/${id}/health`, label: 'Software Health', icon: Activity },
    { to: `/projects/${id}/assistant`, label: 'AI Intelligence Assistant', icon: Bot },
    { to: `/projects/${id}/docs`, label: 'Documentation Report', icon: FileText },
    { to: `/projects/${id}/tests`, label: 'Test Reconstruction', icon: TestTube2 },
  ];

  return (
    <aside className="w-64 border-r border-neutral-800 bg-[#0d131f]/60 h-[calc(100vh-3.5rem)] sticky top-14 flex flex-col justify-between p-3 select-none">
      <div>
        {projectName && (
          <div className="mb-4 px-3 py-2 bg-neutral-900/80 rounded-lg border border-neutral-800/80">
            <div className="text-xs text-neutral-400 font-mono">ACTIVE PROJECT</div>
            <div className="text-sm font-semibold text-white truncate mt-0.5">{projectName}</div>
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-neutral-800 text-xs">
              <span className="text-neutral-400 font-mono">{primaryLang || 'Polyglot'}</span>
              <span className={`px-1.5 py-0.5 rounded font-mono font-medium ${
                healthScore >= 80 ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/50' :
                healthScore >= 60 ? 'bg-amber-950/60 text-amber-400 border border-amber-800/50' :
                'bg-rose-950/60 text-rose-400 border border-rose-800/50'
              }`}>
                Score: {healthScore}/100
              </span>
            </div>
          </div>
        )}

        <div className="text-[11px] font-mono uppercase tracking-wider text-neutral-400 px-3 mb-1">
          ANALYSIS MODULES
        </div>

        <nav className="space-y-0.5">
          {links.map((link) => {
            const Icon = link.icon;
            return (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.exact}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition ${
                    isActive
                      ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/20'
                      : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/40'
                  }`
                }
              >
                <div className="flex items-center space-x-2.5 truncate">
                  <Icon className="w-4 h-4 shrink-0" />
                  <span className="truncate">{link.label}</span>
                </div>
                <ChevronRight className="w-3.5 h-3.5 opacity-40 shrink-0" />
              </NavLink>
            );
          })}
        </nav>
      </div>

      <div className="p-3 bg-neutral-900/40 rounded-md border border-neutral-800/40 text-[11px] text-neutral-400">
        <div className="flex items-center space-x-1.5 text-neutral-300 font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Engine Active</span>
        </div>
        <div className="mt-1">Static AST & Topology verified</div>
      </div>
    </aside>
  );
};
