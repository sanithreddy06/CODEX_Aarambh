import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { FileText, Download, Copy, Check, RefreshCw } from 'lucide-react';
import { api } from '../lib/api';

export const DocumentationPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [markdown, setMarkdown] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      api.getDocumentation(id)
        .then((res) => setMarkdown(res.markdown))
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [id]);

  const handleCopy = () => {
    navigator.clipboard.writeText(markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = async (format: 'markdown' | 'json' | 'pdf') => {
    if (!id) return;
    try {
      setDownloading(format);
      const ext = format === 'pdf' ? 'pdf' : format === 'json' ? 'json' : 'md';
      const url = `/api/projects/${id}/documentation/export?export_format=${format}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Download failed: ' + res.statusText);
      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = `codex_report_${id.slice(0, 8)}.${ext}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error(err);
      window.location.href = `/api/projects/${id}/documentation/export?export_format=${format}`;
    } finally {
      setDownloading(null);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-xs text-neutral-400">Compiling 14-section architectural report...</div>;
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Technical Specification Report</h1>
          <p className="text-xs text-neutral-400 mt-0.5">
            Evidence-backed software documentation generated autonomously from static analysis facts.
          </p>
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
            onClick={() => handleDownload('markdown')}
            disabled={downloading !== null}
            className="px-3 py-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-xs text-neutral-200 border border-neutral-700 transition flex items-center space-x-1 disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{downloading === 'markdown' ? 'Saving...' : '.MD'}</span>
          </button>
          <button
            onClick={() => handleDownload('json')}
            disabled={downloading !== null}
            className="px-3 py-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-xs text-neutral-200 border border-neutral-700 transition flex items-center space-x-1 disabled:opacity-50"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{downloading === 'json' ? 'Saving...' : '.JSON'}</span>
          </button>
          <button
            onClick={() => handleDownload('pdf')}
            disabled={downloading !== null}
            className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition flex items-center space-x-1 shadow-sm disabled:opacity-50"
          >
            {downloading === 'pdf' ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
            <span>{downloading === 'pdf' ? 'Generating PDF...' : 'Export PDF'}</span>
          </button>
        </div>
      </div>

      <div className="p-8 rounded-xl bg-neutral-900/60 border border-neutral-800 text-xs text-neutral-300 font-mono leading-relaxed whitespace-pre-wrap select-text overflow-x-auto">
        {markdown}
      </div>
    </div>
  );
};
