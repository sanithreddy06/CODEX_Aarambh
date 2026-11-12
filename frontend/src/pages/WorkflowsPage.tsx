import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Workflow, ArrowRight, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { api, WorkflowSequence } from '../lib/api';

export const WorkflowsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [workflows, setWorkflows] = useState<WorkflowSequence[]>([]);
  const [selectedWf, setSelectedWf] = useState<WorkflowSequence | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      api.getWorkflows(id)
        .then((res) => {
          setWorkflows(res.workflows);
          if (res.workflows.length > 0) {
            setSelectedWf(res.workflows[0]);
          }
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) {
    return <div className="p-12 text-center text-xs text-neutral-400">Reconstructing operational workflows...</div>;
  }

  if (workflows.length === 0) {
    return (
      <div className="p-12 text-center text-xs text-neutral-400">
        No execution workflows reconstructed from endpoints.
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Execution Workflow Reconstruction</h1>
        <p className="text-xs text-neutral-400 mt-0.5">
          End-to-end transaction sequences tracing from client triggers through controllers, domain services, and database layers.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Workflows List */}
        <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
          {workflows.map((wf) => {
            const isSelected = selectedWf?.id === wf.id;
            return (
              <div
                key={wf.id}
                onClick={() => setSelectedWf(wf)}
                className={`p-3.5 rounded-xl border cursor-pointer transition ${
                  isSelected
                    ? 'bg-indigo-950/30 border-indigo-500 shadow-md shadow-indigo-500/10'
                    : 'bg-neutral-900/60 border-neutral-800 hover:border-neutral-700'
                }`}
              >
                <div className="text-xs font-semibold text-white">{wf.name}</div>
                <div className="text-[11px] font-mono text-indigo-400 mt-1">Trigger: `{wf.trigger}`</div>
                <div className="text-[10px] text-neutral-400 font-mono mt-2">
                  {wf.steps?.length || 0} execution steps
                </div>
              </div>
            );
          })}
        </div>

        {/* Selected Workflow Steps Sequence */}
        <div className="lg:col-span-2">
          {selectedWf && (
            <div className="p-5 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-5">
              <div className="border-b border-neutral-800 pb-3">
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-indigo-950/80 text-indigo-400 border border-indigo-800/40">
                  {selectedWf.trigger}
                </span>
                <h2 className="text-base font-bold text-white mt-2">{selectedWf.name}</h2>
              </div>

              {/* Execution Steps */}
              <div className="space-y-4">
                {selectedWf.steps.map((s, idx) => (
                  <div key={idx} className="relative flex items-start space-x-3">
                    <div className="w-7 h-7 rounded-full bg-neutral-800 border border-neutral-700 flex items-center justify-center text-xs font-mono font-bold text-indigo-400 shrink-0 z-10">
                      {s.order}
                    </div>

                    <div className="flex-1 p-3.5 rounded-lg bg-neutral-950 border border-neutral-800 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-white">{s.component}</span>
                        {s.layer && (
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-neutral-900 text-neutral-400">
                            {s.layer}
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-neutral-300">{s.action}</div>
                      <div className="text-[10px] font-mono text-neutral-500 truncate pt-1">
                        Source: {s.file}:{s.line}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Evidence Footer */}
              <div className="p-3 rounded-lg bg-neutral-950 border border-neutral-800 text-[11px] text-neutral-400 flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Sequence reconstructed from static AST route handlers and call traces.</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
