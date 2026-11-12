import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { TestTube2, CheckCircle2, ShieldAlert, RefreshCw, Copy, Check, Download } from 'lucide-react';
import { api, GeneratedTest } from '../lib/api';

export const TestsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [tests, setTests] = useState<GeneratedTest[]>([]);
  const [selectedTest, setSelectedTest] = useState<GeneratedTest | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (id) {
      api.getGeneratedTests(id)
        .then((res) => {
          setTests(res);
          if (res.length > 0) setSelectedTest(res[0]);
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [id]);

  const handleGenerate = async (framework: string) => {
    if (!id) return;
    try {
      setGenerating(true);
      const res = await api.generateTests(id, undefined, framework);
      setTests(res);
      if (res.length > 0) setSelectedTest(res[0]);
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = () => {
    if (selectedTest?.code) {
      navigator.clipboard.writeText(selectedTest.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadTest = () => {
    if (!selectedTest?.code) return;
    const ext = selectedTest.test_framework === 'vitest' ? 'test.ts' : 'py';
    const blob = new Blob([selectedTest.code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedTest.test_name}.${ext}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadAllTests = () => {
    if (tests.length === 0) return;
    const fw = tests[0].test_framework;
    const ext = fw === 'vitest' ? 'test.ts' : 'py';
    const fullCode = tests.map(t => `# ========================================\n# ${t.test_name} (${t.test_type})\n# Target: ${t.target_file}\n# ========================================\n${t.code}\n`).join('\n\n');
    const blob = new Blob([fullCode], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `codex_reconstructed_tests_${id?.slice(0, 8)}.${ext}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return <div className="p-12 text-center text-xs text-neutral-400">Loading test scenarios...</div>;
  }

  return (
    <div className="space-y-6 max-w-6xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Test Case Reconstruction</h1>
          <p className="text-xs text-neutral-400 mt-0.5">
            Automated generation of positive, boundary, and auth verification suites based on discovered AST endpoints and signatures.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {tests.length > 0 && (
            <button
              onClick={handleDownloadAllTests}
              className="px-3 py-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-xs font-medium text-neutral-200 border border-neutral-700 transition flex items-center space-x-1"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export All ({tests.length})</span>
            </button>
          )}
          <button
            onClick={() => handleGenerate('pytest')}
            disabled={generating}
            className="px-3 py-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-xs font-medium text-neutral-200 border border-neutral-700 transition"
          >
            {generating ? 'Reconstructing...' : 'Regenerate pytest'}
          </button>
          <button
            onClick={() => handleGenerate('vitest')}
            disabled={generating}
            className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition shadow-sm"
          >
            Regenerate vitest
          </button>
        </div>
      </div>

      {/* Safety Notice */}
      <div className="p-3.5 rounded-xl bg-amber-950/30 border border-amber-800/40 text-xs text-amber-300 flex items-start space-x-2.5">
        <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-white">Execution Safety Boundary:</span> Tests are generated for developer review and export. Uploaded untrusted code and generated tests are never automatically executed on the host backend server.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Test Cases Sidebar */}
        <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
          {tests.map((t) => {
            const isSelected = selectedTest?.id === t.id;
            return (
              <div
                key={t.id}
                onClick={() => setSelectedTest(t)}
                className={`p-3 rounded-xl border cursor-pointer transition ${
                  isSelected
                    ? 'bg-indigo-950/30 border-indigo-500 shadow-md shadow-indigo-500/10'
                    : 'bg-neutral-900/60 border-neutral-800 hover:border-neutral-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-semibold text-white truncate max-w-[180px]">
                    {t.test_name}
                  </span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-400 uppercase">
                    {t.test_type}
                  </span>
                </div>
                <div className="text-[11px] font-mono text-neutral-400 truncate mt-1">
                  Target: {t.target_file}
                </div>
              </div>
            );
          })}
          {tests.length === 0 && (
            <div className="text-xs text-neutral-400 text-center py-8">
              No test scenarios generated yet. Click 'Regenerate' above.
            </div>
          )}
        </div>

        {/* Selected Test Code Viewer */}
        <div className="lg:col-span-2">
          {selectedTest && (
            <div className="p-5 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-4">
              <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
                <div>
                  <h2 className="text-sm font-mono font-bold text-white">{selectedTest.test_name}</h2>
                  <div className="text-xs font-mono text-neutral-400 mt-0.5">
                    Framework: {selectedTest.test_framework} • Type: {selectedTest.test_type}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleCopy}
                    className="px-3 py-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-xs text-neutral-200 border border-neutral-700 transition flex items-center space-x-1"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Copied' : 'Copy'}</span>
                  </button>
                  <button
                    onClick={handleDownloadTest}
                    className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition flex items-center space-x-1 shadow-sm"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download File</span>
                  </button>
                </div>
              </div>

              <div className="bg-neutral-950 p-4 rounded-xl border border-neutral-800 overflow-x-auto font-mono text-xs text-neutral-200">
                <pre>{selectedTest.code}</pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
