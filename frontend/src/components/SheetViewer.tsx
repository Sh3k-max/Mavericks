import React, { useState, useEffect, useRef } from 'react';
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  Eye, 
  EyeOff, 
  Sliders, 
  Download, 
  Info, 
  CheckCircle2, 
  AlertTriangle, 
  X,
  Layers,
  Sparkles,
  ExternalLink
} from 'lucide-react';
import { Sheet, ComponentItem, ConnectionItem, CrossSheetConnectorItem, DocumentItem } from '../types';
import { api } from '../services/api';

interface SheetViewerProps {
  document: DocumentItem | null;
  sheets: Sheet[];
  selectedSheet: Sheet | null;
  onSelectSheet: (sheet: Sheet) => void;
}

export const SheetViewer: React.FC<SheetViewerProps> = ({
  document,
  sheets,
  selectedSheet,
  onSelectSheet,
}) => {
  const [components, setComponents] = useState<ComponentItem[]>([]);
  const [connections, setConnections] = useState<ConnectionItem[]>([]);
  const [connectors, setConnectors] = useState<CrossSheetConnectorItem[]>([]);
  const [selectedComp, setSelectedComp] = useState<ComponentItem | null>(null);

  // Overlay layer toggles
  const [showOverlayImage, setShowOverlayImage] = useState(true);
  const [showComponents, setShowComponents] = useState(true);
  const [showPipelines, setShowPipelines] = useState(true);
  const [showConnectors, setShowConnectors] = useState(true);
  const [minConfidence, setMinConfidence] = useState(0.0);

  // Zoom & Pan state
  const [zoom, setZoom] = useState(1.0);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!document || !selectedSheet) return;

    const loadSheetData = async () => {
      try {
        const [compData, connData, crossData] = await Promise.all([
          api.getComponents(document.id, { sheet_id: selectedSheet.id }),
          api.getConnections(document.id, selectedSheet.id),
          api.getCrossSheetConnectors(document.id)
        ]);
        setComponents(compData);
        setConnections(connData);
        setConnectors(crossData.filter(c => c.sheet_id === selectedSheet.id));
      } catch (err) {
        console.error('Failed to load sheet data:', err);
      }
    };

    loadSheetData();
  }, [document, selectedSheet]);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleResetZoom = () => {
    setZoom(1.0);
    setPan({ x: 0, y: 0 });
  };

  if (!document || !selectedSheet) {
    return (
      <div className="flex flex-col items-center justify-center p-16 text-center glass-panel rounded-2xl border border-white/5 my-8">
        <Layers className="w-12 h-12 text-slate-500 mb-3" />
        <h3 className="text-base font-semibold text-slate-200">No Sheet Selected</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm">
          Please select a document and sheet to view the annotated P&ID drawing.
        </p>
      </div>
    );
  }

  // Filter components by confidence threshold
  const filteredComponents = components.filter(c => c.confidence >= minConfidence);

  const imageUrl = showOverlayImage && selectedSheet.overlay_url
    ? selectedSheet.overlay_url
    : api.getSheetImageUrl(selectedSheet.id);

  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      {/* Control Bar */}
      <div className="glass-panel rounded-xl p-3 border border-white/10 flex flex-wrap items-center justify-between gap-3">
        {/* Sheet Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-400">Sheet:</span>
          <div className="flex items-center gap-1.5">
            {sheets.map(s => (
              <button
                key={s.id}
                onClick={() => onSelectSheet(s)}
                className={`px-3 py-1 rounded-lg text-xs font-mono transition-all ${
                  s.id === selectedSheet.id
                    ? 'bg-indigo-600 text-white font-semibold shadow-sm'
                    : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'
                }`}
              >
                Sheet {s.sheet_number.toString().padStart(2, '0')}
              </button>
            ))}
          </div>
        </div>

        {/* View & Layer Toggles */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowOverlayImage(!showOverlayImage)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs border transition-all ${
              showOverlayImage
                ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                : 'bg-slate-900/60 text-slate-400 border-slate-700 hover:text-slate-200'
            }`}
          >
            {showOverlayImage ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
            <span>Overlay Visualizer</span>
          </button>

          <button
            onClick={() => setShowComponents(!showComponents)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs border transition-all ${
              showComponents
                ? 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30'
                : 'bg-slate-900/60 text-slate-400 border-slate-700 hover:text-slate-200'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Components ({filteredComponents.length})</span>
          </button>

          <button
            onClick={() => setShowPipelines(!showPipelines)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs border transition-all ${
              showPipelines
                ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                : 'bg-slate-900/60 text-slate-400 border-slate-700 hover:text-slate-200'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-rose-500" />
            <span>Lines ({connections.length})</span>
          </button>
        </div>

        {/* Confidence Filter & Zoom Controls */}
        <div className="flex items-center gap-4">
          <div className="hidden lg:flex items-center gap-2">
            <span className="text-[11px] font-mono text-slate-400">Min Conf:</span>
            <input
              type="range"
              min="0"
              max="0.95"
              step="0.05"
              value={minConfidence}
              onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
              className="w-20 accent-indigo-500 cursor-pointer"
            />
            <span className="text-[11px] font-mono text-indigo-400 font-bold">{Math.round(minConfidence * 100)}%</span>
          </div>

          <div className="flex items-center gap-1 bg-slate-900/80 p-0.5 rounded-lg border border-slate-700">
            <button
              onClick={() => setZoom(prev => Math.min(prev + 0.25, 4.0))}
              className="p-1.5 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition-colors"
              title="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <span className="text-[11px] font-mono text-slate-300 px-1">{Math.round(zoom * 100)}%</span>
            <button
              onClick={() => setZoom(prev => Math.max(prev - 0.25, 0.4))}
              className="p-1.5 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition-colors"
              title="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleResetZoom}
              className="p-1.5 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition-colors"
              title="Reset View"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>

          <a
            href={imageUrl}
            download={`sheet_${selectedSheet.sheet_number}_annotated.png`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download</span>
          </a>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div className="relative flex gap-4">
        <div
          ref={containerRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          className="relative flex-1 h-[650px] overflow-hidden rounded-2xl glass-panel border border-white/10 bg-[#070a10] cursor-grab active:cursor-grabbing select-none"
        >
          {/* Legend Banner */}
          <div className="absolute top-3 left-3 z-20 flex items-center gap-3 px-3 py-1.5 rounded-xl bg-slate-900/90 backdrop-blur border border-white/10 text-[11px] font-mono">
            <span className="flex items-center gap-1.5 text-emerald-400">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50" />
              <span>Instrument</span>
            </span>
            <span className="flex items-center gap-1.5 text-amber-400">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-sm shadow-amber-500/50" />
              <span>Valve</span>
            </span>
            <span className="flex items-center gap-1.5 text-purple-400">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-500 shadow-sm shadow-purple-500/50" />
              <span>Equipment</span>
            </span>
            <span className="flex items-center gap-1.5 text-rose-400">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-sm shadow-rose-500/50" />
              <span>Pipeline</span>
            </span>
            <span className="flex items-center gap-1.5 text-blue-400">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 shadow-sm shadow-blue-500/50" />
              <span>Off-Page</span>
            </span>
          </div>

          {/* Interactive Transform Container */}
          <div
            className="absolute origin-top-left transition-transform duration-75"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              width: `${selectedSheet.width}px`,
              height: `${selectedSheet.height}px`
            }}
          >
            {/* Sheet Render / Overlay Image */}
            <img
              src={imageUrl}
              alt={`P&ID Sheet ${selectedSheet.sheet_number}`}
              className="w-full h-full object-contain pointer-events-none"
            />

            {/* Interactive Component Clickable Highlights */}
            {showComponents && filteredComponents.map((comp) => {
              const isSelected = selectedComp?.id === comp.id;
              const colorClass = 
                comp.component_type === 'Instrument' ? 'border-emerald-400/80 hover:bg-emerald-500/20' :
                comp.component_type === 'Valve' ? 'border-amber-400/80 hover:bg-amber-500/20' :
                comp.component_type === 'Equipment' ? 'border-purple-400/80 hover:bg-purple-500/20' :
                'border-blue-400/80 hover:bg-blue-500/20';

              return (
                <div
                  key={comp.id}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedComp(comp);
                  }}
                  className={`absolute cursor-pointer border-2 transition-all group ${colorClass} ${
                    isSelected ? 'ring-4 ring-indigo-400 shadow-lg z-30' : 'z-10'
                  }`}
                  style={{
                    left: `${comp.x1}px`,
                    top: `${comp.y1}px`,
                    width: `${comp.x2 - comp.x1}px`,
                    height: `${comp.y2 - comp.y1}px`,
                  }}
                  title={`${comp.tag} - ${comp.component_name} (${Math.round(comp.confidence * 100)}%)`}
                >
                  {/* Floating Tag Badge */}
                  <div className="absolute -top-6 left-0 bg-slate-900/90 text-white font-mono text-[10px] px-1.5 py-0.5 rounded shadow border border-white/10 whitespace-nowrap pointer-events-none group-hover:scale-110 transition-transform">
                    {comp.tag}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Component Inspection Drawer */}
        {selectedComp && (
          <div className="w-80 glass-panel rounded-2xl p-5 border border-white/10 flex flex-col justify-between animate-in slide-in-from-right duration-200">
            <div>
              <div className="flex items-start justify-between pb-3 border-b border-white/10">
                <div>
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                    {selectedComp.component_type}
                  </span>
                  <h3 className="text-base font-bold text-white font-mono mt-1.5">{selectedComp.tag}</h3>
                  <p className="text-xs text-slate-300 font-medium">{selectedComp.component_name}</p>
                </div>
                <button
                  onClick={() => setSelectedComp(null)}
                  className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/5"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="mt-4 space-y-3 text-xs font-mono">
                <div className="flex justify-between py-1 border-b border-white/5">
                  <span className="text-slate-400">Class:</span>
                  <span className="text-white font-bold">{selectedComp.symbol_class || 'Standard'}</span>
                </div>

                <div className="flex justify-between py-1 border-b border-white/5">
                  <span className="text-slate-400">Confidence:</span>
                  <span className="text-emerald-400 font-bold">{Math.round(selectedComp.confidence * 100)}%</span>
                </div>

                <div className="flex justify-between py-1 border-b border-white/5">
                  <span className="text-slate-400">Association Score:</span>
                  <span className="text-indigo-400 font-bold">{selectedComp.association_score.toFixed(2)}</span>
                </div>

                <div className="flex justify-between py-1 border-b border-white/5">
                  <span className="text-slate-400">Distance to Tag:</span>
                  <span className="text-slate-300">{selectedComp.distance_to_tag.toFixed(1)} px</span>
                </div>

                <div className="flex justify-between py-1 border-b border-white/5">
                  <span className="text-slate-400">Coordinates:</span>
                  <span className="text-slate-300">({Math.round(selectedComp.center_x)}, {Math.round(selectedComp.center_y)})</span>
                </div>

                <div className="py-1 border-b border-white/5">
                  <span className="text-slate-400">Validation Status:</span>
                  <div className="mt-1 flex items-center gap-1.5">
                    {selectedComp.validation_status === 'VALID' ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                    )}
                    <span className={selectedComp.validation_status === 'VALID' ? 'text-emerald-400' : 'text-amber-400'}>
                      {selectedComp.validation_status}
                    </span>
                  </div>
                </div>

                {selectedComp.validation_notes && (
                  <div className="p-2.5 rounded-lg bg-slate-900/70 border border-white/5 text-[11px] text-slate-300 font-sans">
                    <span className="text-slate-400 block font-mono text-[10px] uppercase mb-0.5">Notes:</span>
                    {selectedComp.validation_notes}
                  </div>
                )}
              </div>
            </div>

            <button
              onClick={() => setSelectedComp(null)}
              className="mt-6 w-full py-2 rounded-lg text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 transition-colors"
            >
              Close Inspector
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
