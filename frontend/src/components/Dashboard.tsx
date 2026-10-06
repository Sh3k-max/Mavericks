import React from 'react';
import { 
  FileText, 
  Upload, 
  Layers, 
  GitFork, 
  Sparkles, 
  CheckCircle2, 
  Clock, 
  Table, 
  Download, 
  ArrowRight,
  ShieldCheck,
  Activity
} from 'lucide-react';
import { DocumentItem } from '../types';
import { api } from '../services/api';

interface DashboardProps {
  documents: DocumentItem[];
  selectedDoc: DocumentItem | null;
  onSelectDoc: (doc: DocumentItem) => void;
  onOpenUpload: () => void;
  onTriggerDemo: () => void;
  onNavigateTab: (tab: string) => void;
  isDemoLoading: boolean;
}

export const Dashboard: React.FC<DashboardProps> = ({
  documents,
  selectedDoc,
  onSelectDoc,
  onOpenUpload,
  onTriggerDemo,
  onNavigateTab,
  isDemoLoading,
}) => {
  // Aggregate statistics across loaded documents
  const totalDocs = documents.length;
  const completedDocs = documents.filter(d => d.processing_status === 'completed').length;
  const totalSheets = documents.reduce((acc, d) => acc + (d.page_count || 0), 0);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Hero Welcome & Quick Action Card */}
      <div className="glass-panel rounded-3xl p-8 border border-white/10 bg-gradient-to-r from-slate-900/95 via-indigo-950/40 to-slate-900/95 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-mono mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Industrial Document Intelligence</span>
          </div>

          <h1 className="text-3xl font-extrabold text-white tracking-tight sm:text-4xl">
            P&ID Component Extraction & Topology System
          </h1>
          <p className="mt-3 text-sm text-slate-300 leading-relaxed">
            Automated intelligence pipeline for Native, Scanned, and Multi-Sheet piping and instrumentation diagrams.
            Detects transmitters, valves, pumps, tanks, traces pipeline routes, and links off-page connectors.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              onClick={onOpenUpload}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-lg shadow-indigo-600/30 hover:shadow-indigo-600/50 transition-all cursor-pointer"
            >
              <Upload className="w-4 h-4" />
              <span>Upload P&ID Document</span>
            </button>

            <button
              onClick={onTriggerDemo}
              disabled={isDemoLoading}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold text-emerald-300 bg-emerald-950/50 hover:bg-emerald-900/50 border border-emerald-500/30 transition-all cursor-pointer disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4 text-emerald-400" />
              <span>{isDemoLoading ? 'Generating Demo...' : 'Run Test Demo (Multi-Sheet)'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Overview Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Documents */}
        <div className="glass-panel rounded-2xl p-5 border border-white/10 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-mono text-slate-400 uppercase">Documents Ingested</span>
            <div className="text-2xl font-bold font-mono text-white mt-1">{totalDocs}</div>
            <p className="text-[11px] text-slate-400 mt-0.5">{completedDocs} Fully Processed</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
            <FileText className="w-6 h-6" />
          </div>
        </div>

        {/* Total P&ID Sheets */}
        <div className="glass-panel rounded-2xl p-5 border border-white/10 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-mono text-slate-400 uppercase">Total P&ID Sheets</span>
            <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">{totalSheets}</div>
            <p className="text-[11px] text-slate-400 mt-0.5">High-Res Rendered</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 border border-emerald-500/20">
            <Layers className="w-6 h-6" />
          </div>
        </div>

        {/* Active Model Engine */}
        <div className="glass-panel rounded-2xl p-5 border border-white/10 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-mono text-slate-400 uppercase">Detection Mode</span>
            <div className="text-lg font-bold font-mono text-indigo-400 mt-1">CV + Geometric</div>
            <p className="text-[11px] text-slate-400 mt-0.5">Modular YOLO Capable</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-400 border border-purple-500/20">
            <Activity className="w-6 h-6" />
          </div>
        </div>

        {/* Validation Engine */}
        <div className="glass-panel rounded-2xl p-5 border border-white/10 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-mono text-slate-400 uppercase">Self-Healing Backtracking</span>
            <div className="text-lg font-bold font-mono text-emerald-400 mt-1">Active & Ready</div>
            <p className="text-[11px] text-slate-400 mt-0.5">Autonomous Loopback</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 border border-emerald-500/20">
            <ShieldCheck className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Ingested Documents List */}
      <div className="glass-panel rounded-2xl border border-white/10 overflow-hidden shadow-xl">
        <div className="p-5 border-b border-white/5 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white">Ingested P&ID Documents</h2>
            <p className="text-xs text-slate-400">Select a document to inspect its sheets, components, and topology</p>
          </div>
          <button
            onClick={onOpenUpload}
            className="text-xs font-mono text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            + Upload Document
          </button>
        </div>

        <div className="divide-y divide-white/5">
          {documents.length === 0 ? (
            <div className="p-12 text-center">
              <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-sm font-semibold text-slate-300">No documents found</p>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                Click "Run Test Demo" above to instantly test the system with our synthetic multi-sheet P&ID drawing!
              </p>
            </div>
          ) : (
            documents.map((doc) => {
              const isSelected = selectedDoc?.id === doc.id;
              return (
                <div
                  key={doc.id}
                  onClick={() => onSelectDoc(doc)}
                  className={`p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-indigo-950/30 border-l-4 border-indigo-500'
                      : 'hover:bg-white/5'
                  }`}
                >
                  <div className="flex items-start gap-3.5">
                    <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-slate-300 border border-white/10 shrink-0">
                      <FileText className="w-5 h-5 text-indigo-400" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-bold text-white hover:text-indigo-400 transition-colors">
                          {doc.filename}
                        </h4>
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full uppercase border ${
                          doc.processing_status === 'completed'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : doc.processing_status === 'processing'
                            ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30 animate-pulse'
                            : 'bg-slate-800 text-slate-400 border-slate-700'
                        }`}>
                          {doc.processing_status}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                          {doc.doc_type.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 font-mono mt-1">
                        Pages: {doc.page_count} | Size: {(doc.file_size / (1024 * 1024)).toFixed(2)} MB
                      </p>
                    </div>
                  </div>

                  {/* Actions for this document */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectDoc(doc);
                        onNavigateTab('viewer');
                      }}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors"
                    >
                      <Layers className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Viewer</span>
                    </button>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectDoc(doc);
                        onNavigateTab('components');
                      }}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors"
                    >
                      <Table className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Components</span>
                    </button>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectDoc(doc);
                        onNavigateTab('connectivity');
                      }}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors"
                    >
                      <GitFork className="w-3.5 h-3.5 text-rose-400" />
                      <span>Topology</span>
                    </button>

                    <a
                      onClick={(e) => e.stopPropagation()}
                      href={api.getExportExcelUrl(doc.id)}
                      download
                      className="p-1.5 rounded-lg text-slate-400 hover:text-emerald-400 hover:bg-slate-800 transition-colors"
                      title="Download Excel Export"
                    >
                      <Download className="w-4 h-4" />
                    </a>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
