import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  FileCode2,
  Folder,
  Code2,
  FunctionSquare,
  Search,
  ChevronRight,
  Terminal,
  FileText
} from 'lucide-react';
import { api, FileRecord, AstEntity, AstTree } from '../lib/api';

export const CodeExplorerPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [selectedFile, setSelectedFile] = useState<FileRecord | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [astEntities, setAstEntities] = useState<AstEntity[]>([]);
  const [astTree, setAstTree] = useState<AstTree | null>(null);
  const [loading, setLoading] = useState(true);
  const [contentLoading, setContentLoading] = useState(false);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (id) {
      api.getProjectFiles(id)
        .then((fList) => {
          setFiles(fList);
          if (fList.length > 0) {
            handleSelectFile(fList[0]);
          }
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [id]);

  const handleSelectFile = async (file: FileRecord) => {
    setSelectedFile(file);
    if (!id) return;
    try {
      setContentLoading(true);
      const [contentData, astData] = await Promise.all([
        api.getFileContent(id, file.relative_path),
        api.getAst(id, file.relative_path)
      ]);
      setFileContent(contentData.content);
      setAstEntities(astData.entities || []);
      setAstTree(astData.ast_tree || null);
    } catch (e) {
      console.error(e);
      setFileContent('// Could not load file content.');
    } finally {
      setContentLoading(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-xs text-neutral-400">Loading codebase file tree...</div>;
  }

  const filteredFiles = files.filter((f) =>
    f.relative_path.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-4 max-w-7xl">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Code & AST Explorer</h1>
        <p className="text-xs text-neutral-400 mt-0.5">
          Inspect source files and explore parsed Abstract Syntax Tree definitions, declarations, and call graphs.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-5 gap-4 h-[calc(100vh-12rem)]">
        {/* File Tree Left Column */}
        <div className="p-3 rounded-xl bg-neutral-900/60 border border-neutral-800 flex flex-col h-full overflow-hidden">
          <div className="relative mb-2">
            <Search className="w-3 h-3 text-neutral-500 absolute left-2.5 top-2" />
            <input
              type="text"
              placeholder="Filter files..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-7 pr-2 py-1 rounded bg-neutral-950 border border-neutral-800 text-[11px] text-white placeholder:text-neutral-600 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex-1 overflow-y-auto space-y-0.5 pr-1">
            {filteredFiles.map((f) => {
              const isSelected = selectedFile?.id === f.id;
              return (
                <button
                  key={f.id}
                  onClick={() => handleSelectFile(f)}
                  className={`w-full text-left px-2 py-1.5 rounded text-xs transition flex items-center space-x-2 ${
                    isSelected
                      ? 'bg-indigo-600/20 text-indigo-300 font-medium border border-indigo-500/30'
                      : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/40'
                  }`}
                >
                  <FileCode2 className="w-3.5 h-3.5 shrink-0 opacity-70" />
                  <span className="truncate font-mono text-[11px]">{f.relative_path}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Center: Source Code Viewer */}
        <div className="md:col-span-2 lg:col-span-3 p-4 rounded-xl bg-neutral-950 border border-neutral-800 flex flex-col h-full overflow-hidden">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-neutral-800 text-xs">
            <span className="font-mono text-neutral-300 truncate">{selectedFile?.relative_path}</span>
            <span className="font-mono text-neutral-400 text-[11px]">
              {selectedFile?.line_count || 0} lines • {selectedFile?.language}
            </span>
          </div>

          {contentLoading ? (
            <div className="flex-1 flex items-center justify-center text-xs text-neutral-400">
              Loading source content...
            </div>
          ) : (
            <div className="flex-1 overflow-auto font-mono text-xs text-neutral-300 bg-neutral-950 p-2 rounded">
              <pre className="leading-relaxed">
                {fileContent.split('\n').map((line, idx) => (
                  <div key={idx} className="table-row">
                    <span className="table-cell select-none text-neutral-400 text-right pr-4 text-[10px] w-8">
                      {idx + 1}
                    </span>
                    <span className="table-cell whitespace-pre">{line || ' '}</span>
                  </div>
                ))}
              </pre>
            </div>
          )}
        </div>

        {/* Right Column: AST Entities Explorer */}
        <div className="p-3 rounded-xl bg-neutral-900/60 border border-neutral-800 flex flex-col h-full overflow-hidden">
          <div className="pb-2 mb-2 border-b border-neutral-800 flex items-center justify-between">
            <span className="text-xs font-semibold text-white">Parsed AST Nodes</span>
            <span className="text-[10px] font-mono text-neutral-400">{astEntities.length} symbols</span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {astEntities.map((ent, i) => (
              <div
                key={i}
                className="p-2 rounded-lg bg-neutral-950 border border-neutral-800/80 space-y-1 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-semibold text-indigo-400 text-[11px] truncate">
                    {ent.name}
                  </span>
                  <span className="text-[9px] uppercase px-1 rounded bg-neutral-800 text-neutral-400 font-mono">
                    {ent.entity_type}
                  </span>
                </div>
                <div className="text-[10px] font-mono text-neutral-400">
                  Lines {ent.start_line} - {ent.end_line}
                </div>
                {ent.signature && (
                  <div className="text-[10px] font-mono text-neutral-300 bg-neutral-900 p-1 rounded truncate">
                    {ent.signature}
                  </div>
                )}
                {ent.calls && ent.calls.length > 0 && (
                  <div className="text-[10px] text-neutral-400 font-mono">
                    Calls: {ent.calls.slice(0, 3).join(', ')}
                  </div>
                )}
              </div>
            ))}

            {astEntities.length === 0 && (
              <div className="text-center py-8 text-neutral-400 text-xs">
                No function or class definitions extracted in this file.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
