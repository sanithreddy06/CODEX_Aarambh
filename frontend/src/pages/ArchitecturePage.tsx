import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Layers,
  ArrowRight,
  ShieldCheck,
  FileCode2,
  CheckCircle2,
  Info,
  ChevronRight
} from 'lucide-react';
import { api, ArchitectureData, ArchitectureComponent } from '../lib/api';

export const ArchitecturePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [arch, setArch] = useState<ArchitectureData | null>(null);
  const [selectedComp, setSelectedComp] = useState<ArchitectureComponent | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      api.getArchitecture(id)
        .then((data) => {
          setArch(data);
          if (data.components.length > 0) {
            setSelectedComp(data.components[0]);
          }
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) {
    return <div className="p-12 text-center text-xs text-neutral-400">Reconstructing architecture hierarchy...</div>;
  }

  if (!arch || arch.components.length === 0) {
    return <div className="p-8 text-neutral-400 text-xs">No architecture components reconstructed.</div>;
  }

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Architecture Explorer</h1>
        <p className="text-xs text-neutral-400 mt-1">
          Multi-tier operational decomposition synthesized from static AST imports, route decorators, and data models.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Interactive Architecture Flow Diagram */}
        <div className="lg:col-span-2 space-y-4">
          <div className="p-5 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-4">
            <div className="text-xs font-mono text-neutral-400 uppercase tracking-wider flex items-center justify-between">
              <span>RECONSTRUCTED APPLICATION TIERS</span>
              <span className="text-indigo-400">{arch.layers.length} Layers Verified</span>
            </div>

            <div className="space-y-3">
              {arch.layers.map((layerName, idx) => {
                const comp = arch.components.find((c) => c.layer === layerName);
                const isSelected = selectedComp?.layer === layerName;

                return (
                  <div key={layerName} className="space-y-2">
                    <div
                      onClick={() => comp && setSelectedComp(comp)}
                      className={`p-4 rounded-xl border transition cursor-pointer ${
                        isSelected
                          ? 'bg-indigo-950/40 border-indigo-500 shadow-md shadow-indigo-500/10'
                          : 'bg-neutral-950/60 border-neutral-800 hover:border-neutral-700'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <span className="w-6 h-6 rounded-full bg-neutral-800 border border-neutral-700 text-neutral-300 text-xs font-mono flex items-center justify-center">
                            {idx + 1}
                          </span>
                          <div>
                            <div className="text-xs font-semibold text-white">{layerName}</div>
                            <div className="text-[11px] text-neutral-400 truncate mt-0.5">
                              {comp?.name || 'Logical Application Layer'}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-[11px] font-mono text-neutral-400">
                            {comp?.files.length || 0} files
                          </span>
                          <ChevronRight className="w-4 h-4 text-neutral-500" />
                        </div>
                      </div>
                    </div>

                    {/* Flow arrow connecting to next layer */}
                    {idx < arch.layers.length - 1 && (
                      <div className="flex justify-center py-0.5">
                        <div className="w-px h-4 bg-indigo-500/40" />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Selected Component Detail Inspector */}
        <div className="p-5 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-5 h-fit sticky top-20">
          <div className="border-b border-neutral-800 pb-3">
            <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-indigo-950/80 text-indigo-400 border border-indigo-800/40">
              {selectedComp?.layer}
            </span>
            <h3 className="text-base font-bold text-white mt-2">{selectedComp?.name}</h3>
          </div>

          <div>
            <h4 className="text-xs font-semibold text-neutral-300 mb-2">Core Responsibilities</h4>
            <ul className="space-y-1.5">
              {selectedComp?.responsibilities.map((resp, i) => (
                <li key={i} className="text-xs text-neutral-400 flex items-start space-x-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <span>{resp}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-semibold text-neutral-300 mb-2">
              Associated Files ({selectedComp?.files.length})
            </h4>
            <div className="max-h-40 overflow-y-auto space-y-1 pr-1">
              {selectedComp?.files.map((file) => (
                <div
                  key={file}
                  className="p-1.5 rounded bg-neutral-950/80 border border-neutral-800 text-[11px] font-mono text-neutral-300 truncate"
                  title={file}
                >
                  {file}
                </div>
              ))}
            </div>
          </div>

          {/* Verifiable Evidence */}
          <div className="p-3 rounded-lg bg-neutral-950/80 border border-neutral-800/80 space-y-1.5">
            <div className="text-[10px] font-mono uppercase text-neutral-400 flex items-center space-x-1">
              <ShieldCheck className="w-3 h-3 text-emerald-400" />
              <span>Verifiable Evidence</span>
            </div>
            <div className="text-xs text-neutral-300">
              Confidence:{' '}
              <span className="text-emerald-400 font-mono font-medium">
                {selectedComp?.evidence?.confidence?.toUpperCase() || 'HIGH'}
              </span>
            </div>
            <div className="text-[11px] text-neutral-400">
              Method: {selectedComp?.evidence?.detection_method || 'AST Topology Discovery'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
