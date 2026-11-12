import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Globe2,
  Lock,
  Search,
  FileCode2,
  Download,
  ShieldCheck,
  ChevronRight,
  Code
} from 'lucide-react';
import { api, ApiExplorerData, ApiEndpoint } from '../lib/api';

const METHOD_COLORS: Record<string, string> = {
  GET: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/40',
  POST: 'bg-blue-950/60 text-blue-400 border-blue-800/40',
  PUT: 'bg-amber-950/60 text-amber-400 border-amber-800/40',
  DELETE: 'bg-rose-950/60 text-rose-400 border-rose-800/40',
  PATCH: 'bg-purple-950/60 text-purple-400 border-purple-800/40',
};

export const ApiExplorerPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<ApiExplorerData | null>(null);
  const [selectedEp, setSelectedEp] = useState<ApiEndpoint | null>(null);
  const [methodFilter, setMethodFilter] = useState<string>('ALL');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [showOpenApi, setShowOpenApi] = useState(false);

  useEffect(() => {
    if (id) {
      api.getApis(id)
        .then((res) => {
          setData(res);
          if (res.endpoints.length > 0) {
            setSelectedEp(res.endpoints[0]);
          }
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [id]);

  const handleDownloadOpenApi = () => {
    if (!data?.openapi_spec) return;
    const blob = new Blob([JSON.stringify(data.openapi_spec, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `openapi_spec_${id?.slice(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return <div className="p-12 text-center text-xs text-neutral-400">Discovering API routes...</div>;
  }

  if (!data || data.endpoints.length === 0) {
    return (
      <div className="p-12 text-center">
        <Globe2 className="w-10 h-10 text-neutral-600 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-white">No API Routes Discovered</h3>
        <p className="text-xs text-neutral-400 mt-1">
          No FastAPI, Flask, Express, or Django route definitions identified.
        </p>
      </div>
    );
  }

  const filteredEndpoints = data.endpoints.filter((ep) => {
    const matchesMethod = methodFilter === 'ALL' || ep.method === methodFilter;
    const matchesSearch =
      ep.path.toLowerCase().includes(search.toLowerCase()) ||
      ep.handler_name.toLowerCase().includes(search.toLowerCase());
    return matchesMethod && matchesSearch;
  });

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">API Interface Explorer</h1>
          <p className="text-xs text-neutral-400 mt-1">
            Autonomously discovered REST endpoints, route schemas, authentication constraints, and OpenAPI specification.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowOpenApi(!showOpenApi)}
            className="px-3 py-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-xs font-medium text-neutral-200 border border-neutral-700 transition"
          >
            {showOpenApi ? 'Hide OpenAPI Spec' : 'View OpenAPI 3.0'}
          </button>
          <button
            onClick={handleDownloadOpenApi}
            className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition flex items-center space-x-1.5 shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export OpenAPI</span>
          </button>
        </div>
      </div>

      {showOpenApi && (
        <div className="p-4 rounded-xl bg-neutral-950 border border-neutral-800 space-y-2">
          <div className="text-xs font-mono text-neutral-400 uppercase">AUTONOMOUSLY GENERATED OPENAPI 3.0 SPEC</div>
          <pre className="p-3 rounded bg-neutral-900 font-mono text-xs text-neutral-300 max-h-64 overflow-y-auto">
            {JSON.stringify(data.openapi_spec, null, 2)}
          </pre>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3 rounded-xl bg-neutral-900/60 border border-neutral-800">
        <div className="flex items-center space-x-1 w-full sm:w-auto overflow-x-auto">
          {['ALL', 'GET', 'POST', 'PUT', 'DELETE', 'PATCH'].map((met) => (
            <button
              key={met}
              onClick={() => setMethodFilter(met)}
              className={`px-3 py-1 rounded text-xs font-mono font-medium transition ${
                methodFilter === met
                  ? 'bg-neutral-800 text-white'
                  : 'text-neutral-400 hover:text-neutral-200'
              }`}
            >
              {met} {met !== 'ALL' && data.methods[met] ? `(${data.methods[met]})` : ''}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-neutral-500 absolute left-2.5 top-2.5" />
          <input
            type="text"
            placeholder="Search path or handler..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-neutral-950 border border-neutral-800 text-xs text-white placeholder:text-neutral-600 focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Endpoints List */}
        <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
          {filteredEndpoints.map((ep) => {
            const isSelected = selectedEp?.id === ep.id;
            const badgeClass = METHOD_COLORS[ep.method] || 'bg-neutral-800 text-neutral-300';

            return (
              <div
                key={ep.id}
                onClick={() => setSelectedEp(ep)}
                className={`p-3 rounded-xl border cursor-pointer transition ${
                  isSelected
                    ? 'bg-indigo-950/30 border-indigo-500 shadow-md shadow-indigo-500/10'
                    : 'bg-neutral-900/60 border-neutral-800 hover:border-neutral-700'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${badgeClass}`}>
                    {ep.method}
                  </span>
                  <span className="text-xs font-mono font-semibold text-white truncate">{ep.path}</span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-neutral-400 font-mono mt-2 pt-2 border-t border-neutral-800/80">
                  <span className="truncate">{ep.handler_name}()</span>
                  {ep.auth_middleware ? (
                    <span className="text-amber-400 flex items-center space-x-1" title="Protected">
                      <Lock className="w-3 h-3" />
                      <span className="text-[10px]">Auth</span>
                    </span>
                  ) : (
                    <span className="text-neutral-400 text-[10px]">Public</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Selected Endpoint Inspector */}
        <div className="lg:col-span-2">
          {selectedEp && (
            <div className="p-5 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-5">
              <div className="border-b border-neutral-800 pb-4">
                <div className="flex items-center space-x-2">
                  <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded border ${METHOD_COLORS[selectedEp.method]}`}>
                    {selectedEp.method}
                  </span>
                  <h2 className="text-base font-bold font-mono text-white">{selectedEp.path}</h2>
                </div>
                <div className="flex items-center space-x-3 text-xs text-neutral-400 font-mono mt-2">
                  <span>Handler: `{selectedEp.handler_name}()`</span>
                  <span>•</span>
                  <span>Source: `{selectedEp.file_path}:{selectedEp.line_number}`</span>
                </div>
              </div>

              {/* Authentication */}
              <div>
                <h3 className="text-xs font-semibold text-neutral-300 mb-1.5">Authentication Policy</h3>
                {selectedEp.auth_middleware ? (
                  <div className="p-2.5 rounded-lg bg-amber-950/20 border border-amber-800/40 text-xs text-amber-300 flex items-center space-x-2">
                    <Lock className="w-4 h-4 shrink-0 text-amber-400" />
                    <span>Protected Route: Requires {selectedEp.auth_middleware}</span>
                  </div>
                ) : (
                  <div className="p-2.5 rounded-lg bg-neutral-950 border border-neutral-800 text-xs text-neutral-400">
                    Public Endpoint: No authentication dependency detected.
                  </div>
                )}
              </div>

              {/* Parameters */}
              <div>
                <h3 className="text-xs font-semibold text-neutral-300 mb-2">Request Parameters</h3>
                {selectedEp.parameters && selectedEp.parameters.length > 0 ? (
                  <div className="border border-neutral-800 rounded-lg overflow-hidden">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-neutral-950 text-neutral-400 font-mono text-[11px] border-b border-neutral-800">
                        <tr>
                          <th className="p-2.5">Parameter</th>
                          <th className="p-2.5">Location</th>
                          <th className="p-2.5">Type</th>
                          <th className="p-2.5">Required</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-neutral-800/80 font-mono">
                        {selectedEp.parameters.map((p) => (
                          <tr key={p.name}>
                            <td className="p-2.5 font-semibold text-white">{p.name}</td>
                            <td className="p-2.5 text-neutral-400">{p.in}</td>
                            <td className="p-2.5 text-indigo-400">{p.type || 'string'}</td>
                            <td className="p-2.5">{p.required ? 'YES' : 'NO'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-xs text-neutral-400 italic">No path or query parameters defined.</div>
                )}
              </div>

              {/* Request Payload Schema */}
              {selectedEp.request_schema && Object.keys(selectedEp.request_schema).length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-neutral-300 mb-1.5">Request Body Schema</h3>
                  <div className="p-3 rounded-lg bg-neutral-950 border border-neutral-800 font-mono text-xs text-indigo-300">
                    Validated Type: {selectedEp.request_schema.type || 'JSON Payload'}
                    {selectedEp.request_schema.description && (
                      <div className="text-neutral-400 text-[11px] mt-1">{selectedEp.request_schema.description}</div>
                    )}
                  </div>
                </div>
              )}

              {/* Verifiable Evidence */}
              <div className="p-3 rounded-lg bg-neutral-950 border border-neutral-800 text-[11px] text-neutral-400 flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>
                  Confirmed via static AST route decorator inspection at line {selectedEp.line_number}.
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
