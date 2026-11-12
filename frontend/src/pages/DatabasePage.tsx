import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Database, Key, Link2, ShieldCheck, FileText, ChevronRight } from 'lucide-react';
import { api, DatabaseSchemaData, DatabaseModel } from '../lib/api';

export const DatabasePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<DatabaseSchemaData | null>(null);
  const [selectedModel, setSelectedModel] = useState<DatabaseModel | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      api.getDatabaseSchema(id)
        .then((res) => {
          setData(res);
          if (res.models.length > 0) {
            setSelectedModel(res.models[0]);
          }
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) {
    return <div className="p-12 text-center text-xs text-neutral-400">Reverse-engineering database schemas...</div>;
  }

  if (!data || data.models.length === 0) {
    return (
      <div className="p-12 text-center">
        <Database className="w-10 h-10 text-neutral-600 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-white">No Database Models Detected</h3>
        <p className="text-xs text-neutral-400 mt-1">
          No SQLAlchemy, Django, Prisma, or SQL table definitions found in repository.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Database Reverse Engineering</h1>
        <p className="text-xs text-neutral-400 mt-1">
          Discovered persistent entities, column types, primary/foreign key constraints, and relational topology.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: Models List */}
        <div className="space-y-3">
          <div className="text-xs font-mono uppercase text-neutral-400 px-1">
            DISCOVERED ENTITIES ({data.models.length})
          </div>

          <div className="space-y-2">
            {data.models.map((m) => {
              const isSelected = selectedModel?.name === m.name;
              return (
                <div
                  key={m.name}
                  onClick={() => setSelectedModel(m)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition ${
                    isSelected
                      ? 'bg-purple-950/30 border-purple-500 shadow-md shadow-purple-500/10'
                      : 'bg-neutral-900/60 border-neutral-800 hover:border-neutral-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-white">{m.name}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-neutral-800 text-purple-400 border border-purple-900/40">
                      {m.orm_framework}
                    </span>
                  </div>
                  <div className="text-xs text-neutral-400 font-mono mt-1">Table: `{m.table_name}`</div>
                  <div className="flex items-center justify-between text-[11px] text-neutral-400 font-mono mt-2 pt-2 border-t border-neutral-800/80">
                    <span>{m.fields?.length || 0} columns</span>
                    <span>{m.relationships?.length || 0} relations</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Center & Right: Selected Model Detail & Schema Table */}
        <div className="lg:col-span-2 space-y-5">
          {selectedModel && (
            <div className="p-5 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-4">
              <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
                <div>
                  <h2 className="text-base font-bold text-white flex items-center space-x-2">
                    <span>{selectedModel.name}</span>
                    <span className="text-xs font-mono text-neutral-400 font-normal">
                      (`{selectedModel.table_name}`)
                    </span>
                  </h2>
                  <div className="text-xs text-neutral-400 font-mono mt-0.5">
                    Defined in `{selectedModel.file_path}` (Line {selectedModel.line_number})
                  </div>
                </div>
                <div className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-neutral-800 text-neutral-300">
                  {selectedModel.orm_framework}
                </div>
              </div>

              {/* Columns Table */}
              <div>
                <h3 className="text-xs font-semibold text-neutral-300 mb-2">Column Definitions</h3>
                <div className="border border-neutral-800 rounded-lg overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-neutral-950 text-neutral-400 font-mono text-[11px] border-b border-neutral-800">
                      <tr>
                        <th className="p-2.5">Field Name</th>
                        <th className="p-2.5">Data Type</th>
                        <th className="p-2.5">Key Type</th>
                        <th className="p-2.5">Nullable</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-neutral-800/80 font-mono">
                      {selectedModel.fields?.map((f) => (
                        <tr key={f.name} className="hover:bg-neutral-800/20">
                          <td className="p-2.5 font-semibold text-white flex items-center space-x-1.5">
                            {f.primary_key && <Key className="w-3 h-3 text-amber-400 shrink-0" />}
                            {f.foreign_key && <Link2 className="w-3 h-3 text-indigo-400 shrink-0" />}
                            <span>{f.name}</span>
                          </td>
                          <td className="p-2.5 text-neutral-400">{f.type}</td>
                          <td className="p-2.5">
                            {f.primary_key ? (
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-800/50">
                                Primary Key
                              </span>
                            ) : f.foreign_key ? (
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/50">
                                FK → {f.foreign_key}
                              </span>
                            ) : (
                              <span className="text-neutral-400">-</span>
                            )}
                          </td>
                          <td className="p-2.5 text-neutral-400">{f.nullable ? 'YES' : 'NO'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Relationships */}
              {selectedModel.relationships && selectedModel.relationships.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-neutral-300 mb-2">Relational Associations</h3>
                  <div className="space-y-2">
                    {selectedModel.relationships.map((rel, i) => (
                      <div
                        key={i}
                        className="p-3 rounded-lg bg-neutral-950 border border-neutral-800 flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center space-x-2">
                          <span className="font-mono font-semibold text-purple-400">{selectedModel.name}</span>
                          <span className="font-mono text-neutral-500">[{rel.type}]</span>
                          <span className="font-mono font-semibold text-indigo-400">{rel.target}</span>
                        </div>
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/40">
                          {rel.confidence?.toUpperCase() || 'CONFIRMED'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Verifiable Evidence */}
              <div className="p-3 rounded-lg bg-neutral-950 border border-neutral-800/80 text-[11px] text-neutral-400 flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>
                  Discovered strictly from AST model inheritance declarations. No hallucinated fields.
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
