import React, { useState, useEffect } from 'react';
import { 
  GitFork, 
  Layers, 
  ArrowRight, 
  Activity, 
  Sparkles,
  Search,
  Filter,
  Info
} from 'lucide-react';
import { DocumentItem, Sheet, ConnectionItem, ComponentItem } from '../types';
import { api } from '../services/api';

interface ConnectivityViewProps {
  document: DocumentItem | null;
  sheets: Sheet[];
}

export const ConnectivityView: React.FC<ConnectivityViewProps> = ({
  document,
  sheets,
}) => {
  const [connections, setConnections] = useState<ConnectionItem[]>([]);
  const [components, setComponents] = useState<ComponentItem[]>([]);
  const [selectedSheet, setSelectedSheet] = useState<string>('ALL');
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  useEffect(() => {
    if (!document) return;

    const loadData = async () => {
      try {
        const [connData, compData] = await Promise.all([
          api.getConnections(document.id),
          api.getComponents(document.id)
        ]);
        setConnections(connData);
        setComponents(compData);
      } catch (err) {
        console.error('Failed to load connectivity data:', err);
      }
    };

    loadData();
  }, [document]);

  if (!document) {
    return (
      <div className="flex flex-col items-center justify-center p-16 text-center glass-panel rounded-2xl border border-white/5 my-8">
        <GitFork className="w-12 h-12 text-slate-500 mb-3" />
        <h3 className="text-base font-semibold text-slate-200">No Document Selected</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm">
          Please select a document to inspect pipeline connectivity.
        </p>
      </div>
    );
  }

  const filteredConnections = selectedSheet === 'ALL'
    ? connections
    : connections.filter(c => c.sheet_id === selectedSheet);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header & Controls */}
      <div className="glass-panel rounded-2xl p-5 border border-white/10 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <span>Pipeline Topology & Connectivity Graph</span>
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30">
              {filteredConnections.length} Connected Segments
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Physical fluid flow lines, process equipment links, and instrumentation signal pathways
          </p>
        </div>

        {/* Sheet Filter */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-400">Sheet:</span>
          <select
            value={selectedSheet}
            onChange={(e) => setSelectedSheet(e.target.value)}
            className="bg-slate-900/90 text-xs text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500 font-mono"
          >
            <option value="ALL">All Sheets</option>
            {sheets.map(s => (
              <option key={s.id} value={s.id}>Sheet {s.sheet_number.toString().padStart(2, '0')}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Interactive Topology Graph Visualizer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Graph Visual Canvas */}
        <div className="lg:col-span-2 glass-panel rounded-2xl p-6 border border-white/10 bg-[#090d16] min-h-[500px] flex flex-col justify-between">
          <div className="flex items-center justify-between pb-3 border-b border-white/5">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Topological Flow Scheme</span>
            <span className="text-[11px] font-mono text-indigo-400">NetworkX Graph Analysis</span>
          </div>

          {filteredConnections.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 text-center">
              <Info className="w-10 h-10 text-slate-600 mb-2" />
              <p className="text-sm font-semibold text-slate-300">No Physical Connections Detected</p>
              <p className="text-xs text-slate-500 mt-1 max-w-sm">
                Pipeline line detection did not identify contiguous pipelines linking components on this sheet.
              </p>
            </div>
          ) : (
            <div className="py-8 flex flex-col gap-6 items-center overflow-x-auto">
              {filteredConnections.map((conn, idx) => (
                <div 
                  key={conn.id || idx}
                  className="flex items-center gap-3 bg-slate-900/80 p-4 rounded-xl border border-white/10 shadow-lg hover:border-indigo-500/40 transition-all max-w-xl w-full"
                >
                  {/* Source Node */}
                  <div 
                    onClick={() => setSelectedNode(conn.source_tag || '')}
                    className="flex-1 p-3 rounded-lg bg-[#0e1424] border border-emerald-500/30 hover:border-emerald-500 cursor-pointer transition-all"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400">
                        {conn.source_type || 'Component'}
                      </span>
                    </div>
                    <span className="font-mono text-sm font-bold text-white block">{conn.source_tag}</span>
                  </div>

                  {/* Flow Pipeline Edge */}
                  <div className="flex flex-col items-center px-2">
                    <span className="text-[10px] font-mono text-rose-400 font-semibold mb-1 whitespace-nowrap">
                      {conn.line_type || 'PRIMARY PIPE'}
                    </span>
                    <div className="flex items-center text-rose-500">
                      <div className="w-10 h-0.5 bg-rose-500" />
                      <ArrowRight className="w-4 h-4 -ml-1" />
                    </div>
                    <span className="text-[9px] font-mono text-slate-500 mt-1">
                      {conn.confidence ? `${Math.round(conn.confidence * 100)}% conf` : ''}
                    </span>
                  </div>

                  {/* Target Node */}
                  <div 
                    onClick={() => setSelectedNode(conn.target_tag || '')}
                    className="flex-1 p-3 rounded-lg bg-[#0e1424] border border-blue-500/30 hover:border-blue-500 cursor-pointer transition-all"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-blue-500/10 text-blue-400">
                        {conn.target_type || 'Component'}
                      </span>
                    </div>
                    <span className="font-mono text-sm font-bold text-white block">{conn.target_tag}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="pt-3 border-t border-white/5 flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span>Click any component node to view details</span>
            <span>Total Identified Routes: {filteredConnections.length}</span>
          </div>
        </div>

        {/* Node Inspector Side Panel */}
        <div className="glass-panel rounded-2xl p-6 border border-white/10 flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-400" />
              <span>Node Inspector</span>
            </h3>

            {selectedNode ? (
              (() => {
                const comp = components.find(c => c.tag === selectedNode);
                if (!comp) return <p className="text-xs text-slate-400">Component data not found</p>;
                return (
                  <div className="space-y-3 font-mono text-xs animate-in fade-in duration-150">
                    <div className="p-3 rounded-xl bg-slate-900/80 border border-white/10">
                      <span className="text-[10px] text-indigo-400 uppercase">{comp.component_type}</span>
                      <h4 className="text-base font-bold text-white mt-0.5">{comp.tag}</h4>
                      <p className="text-xs text-slate-300 font-sans mt-0.5">{comp.component_name}</p>
                    </div>

                    <div className="flex justify-between py-1 border-b border-white/5">
                      <span className="text-slate-400">Detection Confidence:</span>
                      <span className="text-emerald-400 font-bold">{Math.round(comp.confidence * 100)}%</span>
                    </div>

                    <div className="flex justify-between py-1 border-b border-white/5">
                      <span className="text-slate-400">Spatial Association:</span>
                      <span className="text-indigo-400 font-bold">{comp.association_score.toFixed(2)}</span>
                    </div>

                    <div className="flex justify-between py-1 border-b border-white/5">
                      <span className="text-slate-400">Coordinates:</span>
                      <span className="text-slate-300">({Math.round(comp.center_x)}, {Math.round(comp.center_y)})</span>
                    </div>

                    <div className="py-1">
                      <span className="text-slate-400 block mb-1">Directly Connected Pipes:</span>
                      {connections
                        .filter(c => c.source_tag === comp.tag || c.target_tag === comp.tag)
                        .map((c, i) => (
                          <div key={i} className="text-[11px] text-slate-300 bg-slate-900/60 p-2 rounded border border-white/5 mb-1">
                            {c.source_tag === comp.tag ? `&rarr; ${c.target_tag}` : `&larr; ${c.source_tag}`} ({c.line_type})
                          </div>
                        ))}
                    </div>
                  </div>
                );
              })()
            ) : (
              <div className="py-16 text-center text-xs text-slate-500 font-mono">
                Select any component in the graph above to inspect its physical connections.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
