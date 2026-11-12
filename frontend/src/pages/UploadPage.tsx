import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileArchive, CheckCircle2, AlertCircle, Loader2, Sparkles, ShieldCheck } from 'lucide-react';
import { api } from '../lib/api';

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressMsg, setProgressMsg] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (!selected.name.endsWith('.zip')) {
        setError('Only .zip archives are supported.');
        return;
      }
      setFile(selected);
      setError(null);
      if (!name) {
        setName(selected.name.replace('.zip', '').replace(/[-_]/g, ' '));
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selected = e.dataTransfer.files[0];
      if (!selected.name.endsWith('.zip')) {
        setError('Only .zip archives are supported.');
        return;
      }
      setFile(selected);
      setError(null);
      if (!name) {
        setName(selected.name.replace('.zip', '').replace(/[-_]/g, ' '));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a ZIP file to upload.');
      return;
    }
    if (!name.trim()) {
      setError('Please provide a project name.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setProgressMsg('Uploading archive and verifying Zip security signatures...');

      const project = await api.uploadProject(name, description, file);

      setProgressMsg('Extracting AST nodes, mapping dependency graph, and discovering APIs...');
      navigate(`/projects/${project.id}`);
    } catch (err: any) {
      setError(err.message || 'Upload failed');
      setLoading(false);
      setProgressMsg(null);
    }
  };

  // Demo Project One-Click Action
  const handleLoadSampleProject = async () => {
    try {
      setLoading(true);
      setError(null);
      setProgressMsg('Fetching bundled sample e-commerce repository...');

      // Fetch sample_project.zip from root or create a Blob
      const response = await fetch('/sample_project.zip');
      let blob: Blob;
      if (response.ok) {
        blob = await response.blob();
      } else {
        // Fallback: request from api or create synthetic zip
        throw new Error('Bundled sample zip could not be retrieved from static root.');
      }

      const sampleFile = new File([blob], 'sample_ecommerce_store.zip', { type: 'application/zip' });
      setProgressMsg('Ingesting sample repository and executing AST reverse engineering...');

      const project = await api.uploadProject(
        'NovaCommerce E-Commerce Store',
        'Full-stack retail application with React frontend, FastAPI controllers, and SQLAlchemy models.',
        sampleFile
      );

      navigate(`/projects/${project.id}`);
    } catch (err: any) {
      setError('Could not auto-load sample project. Please select a local .zip file manually.');
      setLoading(false);
      setProgressMsg(null);
    }
  };

  return (
    <div className="container mx-auto px-4 py-12 max-w-2xl">
      <div className="text-center mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Ingest & Reverse Engineer</h1>
        <p className="text-xs text-neutral-400 mt-2 max-w-md mx-auto">
          Upload any software repository archive. CODEX scans configurations, parses syntax trees, graphs dependencies, and reconstructs the architecture.
        </p>
      </div>

      {/* Demo Project Shortcut Banner */}
      <div className="mb-6 p-4 rounded-xl bg-gradient-to-r from-indigo-950/40 via-purple-950/30 to-indigo-950/40 border border-indigo-800/40 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-semibold text-white">Live Hackathon Demonstration?</div>
            <div className="text-[11px] text-neutral-400">Instantly test with the bundled multi-tier E-commerce store repo.</div>
          </div>
        </div>
        <button
          type="button"
          onClick={handleLoadSampleProject}
          disabled={loading}
          className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition shadow-sm shrink-0"
        >
          {loading ? 'Processing...' : 'Load Demo Repo'}
        </button>
      </div>

      <form onSubmit={handleSubmit} className="p-6 rounded-xl bg-neutral-900/60 border border-neutral-800 space-y-6">
        {error && (
          <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Drag & Drop Box */}
        <div>
          <label className="block text-xs font-medium text-neutral-300 mb-2">Repository Archive (.ZIP)</label>
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-8 text-center transition cursor-pointer relative ${
              isDragging
                ? 'border-indigo-500 bg-indigo-950/20'
                : file
                ? 'border-emerald-600/60 bg-emerald-950/10'
                : 'border-neutral-700/80 hover:border-neutral-600 bg-neutral-950/40'
            }`}
          >
            <input
              type="file"
              accept=".zip"
              onChange={handleFileChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            {file ? (
              <div className="flex flex-col items-center">
                <FileArchive className="w-10 h-10 text-emerald-400 mb-2" />
                <span className="text-sm font-semibold text-white">{file.name}</span>
                <span className="text-xs text-neutral-400 mt-0.5">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB • Ready to analyze
                </span>
                <span className="text-[11px] text-emerald-400 mt-2 flex items-center space-x-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>ZIP format verified</span>
                </span>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <UploadCloud className="w-10 h-10 text-neutral-500 mb-2" />
                <span className="text-sm font-medium text-neutral-300">
                  Drop your project ZIP here, or <span className="text-indigo-400 underline">browse</span>
                </span>
                <span className="text-xs text-neutral-400 mt-1">
                  Supports Python, JS, TS, Java, Go, Rust up to 50MB
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Project Name */}
        <div>
          <label className="block text-xs font-medium text-neutral-300 mb-1">Project Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Acme Billing Engine"
            className="w-full px-3 py-2 rounded-lg bg-neutral-950 border border-neutral-700/80 text-white text-xs placeholder:text-neutral-600 focus:outline-none focus:border-indigo-500 transition"
          />
        </div>

        {/* Project Description */}
        <div>
          <label className="block text-xs font-medium text-neutral-300 mb-1">Description (Optional)</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            placeholder="Provide architectural context, legacy details, or objectives..."
            className="w-full px-3 py-2 rounded-lg bg-neutral-950 border border-neutral-700/80 text-white text-xs placeholder:text-neutral-600 focus:outline-none focus:border-indigo-500 transition"
          />
        </div>

        {/* Security Assurance */}
        <div className="p-3 rounded-lg bg-neutral-950/60 border border-neutral-800 text-[11px] text-neutral-400 flex items-start space-x-2.5">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <span className="text-neutral-300 font-medium">Safe Extraction Policy:</span> Archives are inspected for Zip bombs, directory traversal (`..` Zip Slip), and code is analyzed via static AST without arbitrary runtime execution.
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading || !file}
          className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-md shadow-indigo-600/20 transition flex items-center justify-center space-x-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>{progressMsg || 'Processing Codebase...'}</span>
            </>
          ) : (
            <span>Start Autonomous Analysis</span>
          )}
        </button>
      </form>
    </div>
  );
};
