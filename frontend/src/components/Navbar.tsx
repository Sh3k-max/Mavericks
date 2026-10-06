import React from 'react';
import { 
  FileText, 
  Upload, 
  Play, 
  Layers, 
  CheckCircle2, 
  Activity, 
  Table, 
  GitFork, 
  FileSpreadsheet,
  AlertTriangle,
  Sparkles
} from 'lucide-react';
import { DocumentItem } from '../types';

interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  documents: DocumentItem[];
  selectedDoc: DocumentItem | null;
  onSelectDoc: (doc: DocumentItem) => void;
  onOpenUpload: () => void;
  onTriggerDemo: () => void;
  isDemoLoading: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  documents,
  selectedDoc,
  onSelectDoc,
  onOpenUpload,
  onTriggerDemo,
  isDemoLoading,
}) => {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'viewer', label: 'Sheet Viewer', icon: Layers },
    { id: 'components', label: 'Components', icon: Table },
    { id: 'connectivity', label: 'Pipeline Graph', icon: GitFork },
    { id: 'validation', label: 'Validation', icon: AlertTriangle },
    { id: 'monitor', label: 'Pipeline Monitor', icon: CheckCircle2 },
  ];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-white/10 bg-[#0a0f1d]/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-blue-600 to-emerald-400 p-[1.5px] shadow-lg shadow-indigo-500/20">
              <div className="w-full h-full bg-[#0a0f1d] rounded-[10px] flex items-center justify-center">
                <FileText className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold tracking-tight text-white text-base">P&ID INTELLIGENCE</span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">v1.0</span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono">Component Extraction & Graph Engine</p>
            </div>
          </div>

          {/* Document Selector */}
          <div className="hidden md:flex items-center gap-2">
            <span className="text-xs text-slate-400 font-mono">Active Doc:</span>
            <select
              id="doc-selector"
              className="bg-slate-900/90 text-sm text-slate-200 border border-slate-700/80 rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 font-mono max-w-[220px] truncate"
              value={selectedDoc?.id || ''}
              onChange={(e) => {
                const found = documents.find((d) => d.id === e.target.value);
                if (found) onSelectDoc(found);
              }}
            >
              {documents.length === 0 ? (
                <option value="">No documents loaded</option>
              ) : (
                documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.filename} ({doc.processing_status})
                  </option>
                ))
              )}
            </select>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2.5">
            <button
              id="btn-run-demo"
              onClick={onTriggerDemo}
              disabled={isDemoLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-emerald-300 bg-emerald-950/40 border border-emerald-500/30 hover:bg-emerald-900/50 transition-all shadow-sm shadow-emerald-950 disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
              <span>{isDemoLoading ? 'Running Demo...' : 'Run Test Demo'}</span>
            </button>

            <button
              id="btn-upload-modal"
              onClick={onOpenUpload}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 transition-all shadow-md shadow-indigo-600/30 hover:shadow-indigo-600/50"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Upload P&ID</span>
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex space-x-1 py-1.5 border-t border-white/5 overflow-x-auto scrollbar-none">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = currentTab === tab.id;
            return (
              <button
                key={tab.id}
                id={`nav-tab-${tab.id}`}
                onClick={() => setCurrentTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-medium transition-all whitespace-nowrap ${
                  isActive
                    ? 'text-white bg-white/10 shadow-sm border border-white/15'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
