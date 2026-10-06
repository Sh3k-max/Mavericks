import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  FileSpreadsheet, 
  FileText, 
  Download, 
  CheckCircle2, 
  AlertTriangle, 
  Layers, 
  Sparkles,
  SlidersHorizontal
} from 'lucide-react';
import { ComponentItem, DocumentItem, Sheet } from '../types';
import { api } from '../services/api';

interface ComponentExplorerProps {
  document: DocumentItem | null;
  sheets: Sheet[];
  onSelectComponentForViewer?: (comp: ComponentItem) => void;
}

export const ComponentExplorer: React.FC<ComponentExplorerProps> = ({
  document,
  sheets,
  onSelectComponentForViewer,
}) => {
  const [components, setComponents] = useState<ComponentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedType, setSelectedType] = useState('ALL');
  const [selectedSheet, setSelectedSheet] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [sortBy, setSortBy] = useState<'tag' | 'confidence' | 'type'>('tag');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    if (!document) return;

    const loadComponents = async () => {
      setLoading(true);
      try {
        const data = await api.getComponents(document.id);
        setComponents(data);
      } catch (err) {
        console.error('Failed to load components:', err);
      } finally {
        setLoading(false);
      }
    };

    loadComponents();
  }, [document]);

  if (!document) {
    return (
      <div className="flex flex-col items-center justify-center p-16 text-center glass-panel rounded-2xl border border-white/5 my-8">
        <Layers className="w-12 h-12 text-slate-500 mb-3" />
        <h3 className="text-base font-semibold text-slate-200">No Document Selected</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm">
          Please select a document to inspect the extracted component database.
        </p>
      </div>
    );
  }

  // Filter & Search
  const filtered = components.filter((comp) => {
    const matchesSearch =
      comp.tag.toLowerCase().includes(search.toLowerCase()) ||
      comp.component_name.toLowerCase().includes(search.toLowerCase());

    const matchesType = selectedType === 'ALL' || comp.component_type === selectedType;
    const matchesSheet = selectedSheet === 'ALL' || comp.sheet_id === selectedSheet;
    const matchesStatus = selectedStatus === 'ALL' || comp.validation_status === selectedStatus;

    return matchesSearch && matchesType && matchesSheet && matchesStatus;
  });

  // Sort
  filtered.sort((a, b) => {
    let cmp = 0;
    if (sortBy === 'tag') cmp = a.tag.localeCompare(b.tag);
    else if (sortBy === 'type') cmp = a.component_type.localeCompare(b.component_type);
    else if (sortBy === 'confidence') cmp = a.confidence - b.confidence;
    return sortOrder === 'asc' ? cmp : -cmp;
  });

  const getSheetNumber = (sheetId: string) => {
    const s = sheets.find(sh => sh.id === sheetId);
    return s ? `Sheet ${s.sheet_number.toString().padStart(2, '0')}` : 'Sheet 01';
  };

  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      {/* Top Header & Export Toolbar */}
      <div className="glass-panel rounded-2xl p-5 border border-white/10 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <span>Component Database</span>
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              {filtered.length} {filtered.length === 1 ? 'Record' : 'Records'}
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Structured P&ID engineering component catalog with coordinates and spatial mappings
          </p>
        </div>

        {/* Real Export Actions */}
        <div className="flex items-center gap-2">
          <a
            id="btn-export-excel"
            href={api.getExportExcelUrl(document.id)}
            download
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-emerald-300 bg-emerald-950/40 border border-emerald-500/30 hover:bg-emerald-900/50 transition-colors shadow-sm"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
            <span>Excel (.xlsx)</span>
          </a>

          <a
            id="btn-export-csv"
            href={api.getExportCsvUrl(document.id)}
            download
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-blue-300 bg-blue-950/40 border border-blue-500/30 hover:bg-blue-900/50 transition-colors shadow-sm"
          >
            <FileText className="w-3.5 h-3.5 text-blue-400" />
            <span>CSV</span>
          </a>

          <a
            id="btn-export-json"
            href={api.getExportJsonUrl(document.id)}
            download
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-purple-300 bg-purple-950/40 border border-purple-500/30 hover:bg-purple-900/50 transition-colors shadow-sm"
          >
            <Download className="w-3.5 h-3.5 text-purple-400" />
            <span>JSON</span>
          </a>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel rounded-xl p-3.5 border border-white/10 flex flex-wrap items-center justify-between gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-[220px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            id="search-component-input"
            type="text"
            placeholder="Search by tag (e.g. PT-101) or component name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-900/90 text-xs text-white pl-9 pr-3 py-2 rounded-lg border border-slate-700 focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>

        {/* Filter Dropdowns */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Type Filter */}
          <select
            id="filter-type"
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="bg-slate-900/90 text-xs text-slate-200 border border-slate-700 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500 font-mono"
          >
            <option value="ALL">All Types</option>
            <option value="Instrument">Instrument</option>
            <option value="Valve">Valve</option>
            <option value="Equipment">Equipment</option>
            <option value="Connector">Connector</option>
          </select>

          {/* Sheet Filter */}
          <select
            id="filter-sheet"
            value={selectedSheet}
            onChange={(e) => setSelectedSheet(e.target.value)}
            className="bg-slate-900/90 text-xs text-slate-200 border border-slate-700 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500 font-mono"
          >
            <option value="ALL">All Sheets</option>
            {sheets.map(s => (
              <option key={s.id} value={s.id}>Sheet {s.sheet_number.toString().padStart(2, '0')}</option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            id="filter-status"
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="bg-slate-900/90 text-xs text-slate-200 border border-slate-700 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500 font-mono"
          >
            <option value="ALL">All Statuses</option>
            <option value="VALID">Valid</option>
            <option value="WARNING">Warning</option>
            <option value="ERROR">Error</option>
          </select>
        </div>
      </div>

      {/* Component Table */}
      <div className="glass-panel rounded-2xl border border-white/10 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 font-mono uppercase text-[10px] tracking-wider border-b border-white/5">
              <tr>
                <th className="px-4 py-3 cursor-pointer hover:text-white" onClick={() => { setSortBy('tag'); setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc'); }}>
                  Tag {sortBy === 'tag' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th className="px-4 py-3">Component Name</th>
                <th className="px-4 py-3 cursor-pointer hover:text-white" onClick={() => { setSortBy('type'); setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc'); }}>
                  Type {sortBy === 'type' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th className="px-4 py-3">Sheet</th>
                <th className="px-4 py-3">Coordinates</th>
                <th className="px-4 py-3 cursor-pointer hover:text-white" onClick={() => { setSortBy('confidence'); setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc'); }}>
                  Confidence {sortBy === 'confidence' && (sortOrder === 'asc' ? '↑' : '↓')}
                </th>
                <th className="px-4 py-3">Association</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-slate-400 font-mono">
                    Loading components...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-slate-400 font-mono">
                    No components match the selected filters.
                  </td>
                </tr>
              ) : (
                filtered.map((comp) => (
                  <tr 
                    key={comp.id} 
                    className="hover:bg-white/5 transition-colors group cursor-default"
                  >
                    <td className="px-4 py-3 font-mono font-bold text-white group-hover:text-indigo-400 transition-colors">
                      {comp.tag}
                    </td>
                    <td className="px-4 py-3 text-slate-200">
                      {comp.component_name}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono border ${
                        comp.component_type === 'Instrument' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
                        comp.component_type === 'Valve' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' :
                        comp.component_type === 'Equipment' ? 'bg-purple-500/10 text-purple-400 border-purple-500/30' :
                        'bg-blue-500/10 text-blue-400 border-blue-500/30'
                      }`}>
                        {comp.component_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400 font-mono">
                      {getSheetNumber(comp.sheet_id)}
                    </td>
                    <td className="px-4 py-3 text-slate-400 font-mono text-[11px]">
                      ({Math.round(comp.center_x)}, {Math.round(comp.center_y)})
                    </td>
                    <td className="px-4 py-3 font-mono font-semibold">
                      <div className="flex items-center gap-1.5">
                        <div className="w-12 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-emerald-400 rounded-full" 
                            style={{ width: `${Math.round(comp.confidence * 100)}%` }} 
                          />
                        </div>
                        <span className="text-slate-300">{Math.round(comp.confidence * 100)}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-400 text-[11px]">
                      {comp.association_score.toFixed(2)}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono ${
                        comp.validation_status === 'VALID'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      }`}>
                        {comp.validation_status === 'VALID' ? (
                          <CheckCircle2 className="w-3 h-3" />
                        ) : (
                          <AlertTriangle className="w-3 h-3" />
                        )}
                        <span>{comp.validation_status}</span>
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
