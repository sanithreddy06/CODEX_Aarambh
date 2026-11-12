import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Network,
  AlertTriangle,
  Zap,
  ShieldAlert,
  ArrowRight,
  Filter,
  CheckCircle2,
  RefreshCw,
  Search
} from 'lucide-react';
import { api, DependencyGraphData, ImpactAnalysis } from '../lib/api';

export const DependenciesPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<DependencyGraphData | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [impact, setImpact] = useState<ImpactAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [impactLoading, setImpactLoading] = useState(false);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (id) {
      api.getDependencies(id)
        .then((res) => {
          setData(res);
          if (res.nodes.length > 0) {
            setSelectedNode(res.nodes[0].id);
            runImpact(res.nodes[0].id);
          }
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [id]);

  const runImpact = async (nodeId: string) => {
    if (!id) return;
    try {
      setImpactLoading(true);
      const res = await api.analyzeImpact(id, nodeId);
      setImpact(res);
    } catch (e) {
      console.error(e);
    } finally {
      setImpactLoading(false);
    }
  };

  const handleSelectNode = (nodeId: string) => {
    setSelectedNode(nodeId);
    runImpact(nodeId);
  };

  if (loading) {
    return <div className="p-12 text-center text-xs text-neutral-400">Computing dependency matrix...</div>;
  }

  if (!data) {
    return <div className="p-8 text-neutral-400 text-xs">Dependency graph unavailable.</div>;
  }

  const filteredNodes = data.nodes.filter((n) =>
    n.id.toLowerCase().includes(search.toLowerCase()) || n.label.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Dependency Graph & Blast Radius</h1>
        <p className="text-xs text-neutral-400 mt-1">
          Static import topologies, cyclic dependency detection, and change impact blast-radius analysis.
        </p>
      </div>

      {/* Circular Dependencies Alert if any */}
      {data.circular_dependencies && data.circular_dependencies.length > 0 && (
        <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-800/60 text-amber-300">
          <div className="flex items-center space-x-2 font-semibold text-xs">
            <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
            <span>Circular Dependency Warning ({data.circular_dependencies.length} cycles detected)</span>
          </div>
          <div className="mt-2 space-y-1 text-xs font-mono">
            {data.circular_dependencies.map((cycle, i) => (
              <div key={i} className="text-amber-200/80">
                Cycle {i + 1}: {cycle.join(' → ')}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Two-Column View: Graph Matrix + Impact Analysis Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Node Explorer & Edge Relationships */}
        <div className="lg:col-span-2 space-y-4">
          <div className="p-4 rounded-xl bg-neutral-900/60 border border-neutral-800">
            <div className="flex items-center justify-between gap-4 mb-4">
              <div className="relative flex-1">
                <Search className="w-3.5 h-3.5 text-neutral-500 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Filter modules by name or path..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-neutral-950 border border-neutral-800 text-xs text-white placeholder:text-neutral-600 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <span className="text-xs font-mono text-neutral-400 shrink-0">
                {data.nodes.length} nodes • {data.edges.length} edges
              </span>
            </div>

            {/* Nodes Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-[460px] overflow-y-auto pr-1">
              {filteredNodes.map((n) => {
                const isSelected = selectedNode === n.id;
                const edgeCount = data.edges.filter((e) => e.source === n.id || e.target === n.id).length;

                return (
                  <div
                    key={n.id}
                    onClick={() => handleSelectNode(n.id)}
                    className={`p-3 rounded-lg border text-left cursor-pointer transition ${
                      isSelected
                        ? 'bg-indigo-950/40 border-indigo-500 shadow-sm'
                        : 'bg-neutral-950/60 border-neutral-800 hover:border-neutral-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-white truncate max-w-[160px]">{n.label}</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-400">
                        {n.language || 'Module'}
                      </span>
                    </div>
                    <div className="text-[11px] font-mono text-neutral-400 truncate mt-1">{n.id}</div>
                    <div className="flex items-center justify-between mt-2 pt-2 border-t border-neutral-800/80 text-[10px] text-neutral-400 font-mono">
                      <span>{n.layer || 'core'}</span>
                      <span>{edgeCount} connections</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* High Centrality Hubs */}
          <div className="p-4 rounded-xl bg-neutral-900/60 border border-neutral-800">
            <h3 className="text-xs font-semibold text-white mb-3">High-Degree Module Hubs (Architectural Hotspots)</h3>
            <div className="divide-y divide-neutral-800/80">
              {data.high_dependency_modules.map((hub) => (
                <div key={hub.node_id} className="py-2 flex items-center justify-between text-xs">
                  <div className="font-mono text-neutral-300">{hub.label}</div>
                  <div className="flex items-center space-x-3 text-neutral-400 font-mono">
                    <span className="text-indigo-400">In: {hub.in_degree}</span>
                    <span className="text-purple-400">Out: {hub.out_degree}</span>
                    <span className="text-neutral-400">({hub.centrality_role})</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Col: Interactive Blast-Radius Impact Analysis */}
        <div className="p-5 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-4 h-fit sticky top-20">
          <div className="flex items-center space-x-2 border-b border-neutral-800 pb-3">
            <Zap className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-bold text-white">Impact Analysis Engine</h3>
          </div>

          {impactLoading ? (
            <div className="py-8 text-center text-xs text-neutral-400">Traversing reverse dependency tree...</div>
          ) : impact ? (
            <div className="space-y-4">
              <div>
                <div className="text-[10px] font-mono text-neutral-400 uppercase">TARGET MODULE UNDER TEST</div>
                <div className="text-xs font-mono font-semibold text-white break-all mt-0.5">{impact.target_node}</div>
              </div>

              {/* Severity Gauge */}
              <div className="p-3 rounded-lg bg-neutral-950 border border-neutral-800">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-neutral-400">Change Severity Risk:</span>
                  <span className={`font-mono font-bold uppercase ${
                    impact.severity === 'critical' ? 'text-rose-400' :
                    impact.severity === 'high' ? 'text-amber-400' :
                    impact.severity === 'medium' ? 'text-yellow-400' : 'text-emerald-400'
                  }`}>
                    {impact.severity}
                  </span>
                </div>
                <div className="text-[11px] text-neutral-400 mt-1">
                  Modifying this file directly impacts {impact.direct_dependents.length} direct modules and {impact.indirect_dependents.length} downstream components.
                </div>
              </div>

              {/* Direct Dependents */}
              <div>
                <div className="text-xs font-semibold text-neutral-300 mb-1.5">
                  Direct Dependents ({impact.direct_dependents.length})
                </div>
                <div className="max-h-36 overflow-y-auto space-y-1 pr-1">
                  {impact.direct_dependents.map((dep) => (
                    <div key={dep} className="p-1.5 rounded bg-neutral-950 border border-neutral-800 text-[11px] font-mono text-neutral-300 truncate">
                      {dep}
                    </div>
                  ))}
                  {impact.direct_dependents.length === 0 && (
                    <div className="text-xs text-neutral-400 italic">No direct dependents.</div>
                  )}
                </div>
              </div>

              {/* Downstream Transitive */}
              <div>
                <div className="text-xs font-semibold text-neutral-300 mb-1.5">
                  Transitive Dependents ({impact.indirect_dependents.length})
                </div>
                <div className="max-h-36 overflow-y-auto space-y-1 pr-1">
                  {impact.indirect_dependents.map((dep) => (
                    <div key={dep} className="p-1.5 rounded bg-neutral-950 border border-neutral-800 text-[11px] font-mono text-neutral-400 truncate">
                      {dep}
                    </div>
                  ))}
                  {impact.indirect_dependents.length === 0 && (
                    <div className="text-xs text-neutral-400 italic">No transitive dependents.</div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-xs text-neutral-400">Select any module to compute blast radius.</div>
          )}
        </div>
      </div>
    </div>
  );
};
