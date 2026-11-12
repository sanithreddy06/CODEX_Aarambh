import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Activity, ShieldAlert, AlertTriangle, CheckCircle2, Info, FileCode2 } from 'lucide-react';
import { api, HealthReport } from '../lib/api';

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-rose-950/60 text-rose-400 border-rose-800/40',
  high: 'bg-amber-950/60 text-amber-400 border-amber-800/40',
  medium: 'bg-yellow-950/60 text-yellow-400 border-yellow-800/40',
  low: 'bg-blue-950/60 text-blue-400 border-blue-800/40',
  info: 'bg-neutral-800 text-neutral-300 border-neutral-700/60',
};

export const HealthPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<HealthReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      api.getHealth(id)
        .then(setReport)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) {
    return <div className="p-12 text-center text-xs text-neutral-400">Auditing code health and security vulnerabilities...</div>;
  }

  if (!report) {
    return <div className="p-8 text-neutral-400 text-xs">Health report unavailable.</div>;
  }

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Software Health & Security Audit</h1>
        <p className="text-xs text-neutral-400 mt-0.5">
          Verifiable codebase audit covering hardcoded secrets, circular dependencies, file complexity, and technical debt.
        </p>
      </div>

      {/* Health Score Summary Card */}
      <div className="p-6 rounded-xl bg-neutral-900/60 border border-neutral-800 flex flex-col sm:flex-row items-center justify-between gap-6">
        <div className="flex items-center space-x-6">
          <div className="w-20 h-20 rounded-2xl bg-neutral-950 border border-neutral-800 flex flex-col items-center justify-center">
            <span className="text-3xl font-extrabold text-white font-mono">{report.grade}</span>
            <span className="text-[10px] font-mono text-neutral-400 uppercase">Grade</span>
          </div>

          <div>
            <div className="text-xs font-mono text-neutral-400 uppercase">CALCULATED HEALTH INDEX</div>
            <div className="text-2xl font-bold text-emerald-400 mt-0.5">{report.health_score} / 100</div>
            <p className="text-xs text-neutral-400 mt-1 max-w-md">
              Score derived arithmetically from static security entropy, cyclomatic dependencies, and documentation ratio.
            </p>
          </div>
        </div>

        {/* Severity Count Tally */}
        <div className="flex items-center space-x-3 text-xs font-mono">
          {Object.entries(report.summary_by_severity || {}).map(([sev, count]) => (
            <div key={sev} className="text-center p-2 rounded-lg bg-neutral-950 border border-neutral-800 min-w-14">
              <div className="font-bold text-white">{count}</div>
              <div className="text-[10px] uppercase text-neutral-400 mt-0.5">{sev}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Findings List */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold text-white">Prioritized Findings ({report.findings.length})</h2>

        <div className="space-y-3">
          {report.findings.map((f) => {
            const badgeClass = SEVERITY_COLORS[f.severity] || 'bg-neutral-800 text-neutral-300';
            return (
              <div key={f.id} className="p-4 rounded-xl bg-neutral-900/40 border border-neutral-800 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2.5">
                    <span className={`text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded border ${badgeClass}`}>
                      {f.severity}
                    </span>
                    <span className="text-sm font-semibold text-white">{f.title}</span>
                  </div>
                  <span className="text-[11px] font-mono text-neutral-500 uppercase">{f.category}</span>
                </div>

                <p className="text-xs text-neutral-300 leading-relaxed">{f.description}</p>

                {f.affected_files && f.affected_files.length > 0 && (
                  <div className="pt-2 border-t border-neutral-800/80 flex items-center space-x-2 text-[11px] font-mono text-neutral-400">
                    <FileCode2 className="w-3.5 h-3.5 shrink-0 opacity-70" />
                    <span>Files:</span>
                    <span className="text-neutral-300 truncate">{f.affected_files.join(', ')}</span>
                  </div>
                )}
              </div>
            );
          })}

          {report.findings.length === 0 && (
            <div className="p-8 text-center text-xs text-neutral-400">
              No critical issues detected. Clean static audit!
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
