import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Terminal, Layers, PlusCircle, Settings, LayoutDashboard, Cpu } from 'lucide-react';

export const Navbar: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <header className="h-14 border-b border-neutral-800 bg-[#0d131f]/90 backdrop-blur sticky top-0 z-40 px-4 flex items-center justify-between">
      <div className="flex items-center space-x-6">
        <Link to="/" className="flex items-center space-x-2 text-white font-bold text-lg tracking-tight group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-transform">
            <Cpu className="w-5 h-5 text-indigo-100" />
          </div>
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-white via-neutral-200 to-neutral-400">CODEX</span>
          <span className="text-xs font-mono font-medium px-1.5 py-0.5 rounded bg-indigo-950/80 text-indigo-400 border border-indigo-800/40">PS06</span>
        </Link>

        <nav className="hidden md:flex items-center space-x-1">
          <Link
            to="/dashboard"
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition flex items-center space-x-1.5 ${
              isActive('/dashboard') ? 'bg-neutral-800 text-white' : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/50'
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </Link>
          <Link
            to="/upload"
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition flex items-center space-x-1.5 ${
              isActive('/upload') ? 'bg-neutral-800 text-white' : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/50'
            }`}
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>New Analysis</span>
          </Link>
        </nav>
      </div>

      <div className="flex items-center space-x-3">
        <Link
          to="/settings"
          className="p-1.5 text-neutral-400 hover:text-white rounded-md hover:bg-neutral-800 transition"
          title="Engine Settings"
        >
          <Settings className="w-4 h-4" />
        </Link>
        <Link
          to="/upload"
          className="text-xs font-semibold px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md shadow-sm transition flex items-center space-x-1.5"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          <span>Upload ZIP</span>
        </Link>
      </div>
    </header>
  );
};
