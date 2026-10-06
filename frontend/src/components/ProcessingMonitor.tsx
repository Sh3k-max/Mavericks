import React, { useEffect, useState } from 'react';
import { 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  XCircle,
  RotateCcw, 
  ArrowRight, 
  Play, 
  Cpu, 
  FileSearch, 
  Sparkles,
  Layers,
  GitBranch
} from 'lucide-react';
import { DocumentItem } from '../types';
import { api } from '../services/api';

interface ProcessingMonitorProps {
  document: DocumentItem | null;
  onRefresh: () => void;
}

const PIPELINE_STAGES = [
  { id: 'pdf_detection', label: 'PDF Type Detection', desc: 'Native / Scanned classification & DPI rasterization' },
  { id: 'page_extraction', label: 'Page Extraction', desc: 'Vector primitives, lines, rectangles, paths' },
  { id: 'preprocessing', label: 'Image Preprocessing', desc: 'Bilateral denoising, CLAHE, deskewing & thresholding' },
  { id: 'ocr', label: 'OCR & Text Recognition', desc: 'Vector text coordinates & raster bounding boxes' },
  { id: 'symbol_detection', label: 'Symbol Detection', desc: 'OpenCV contour analysis & modular YOLO interface' },
  { id: 'tag_normalization', label: 'Tag Normalization', desc: 'Contextual OCR typo correction (0/O, 1/I, S/5, B/8)' },
  { id: 'spatial_association', label: 'Spatial Association', desc: 'Multi-factor weighted geometric matching' },
  { id: 'connectivity', label: 'Pipe / Line Connectivity', desc: 'OpenCV morphology & NetworkX topology graph' },
  { id: 'cross_sheet', label: 'Cross-Sheet Matching', desc: 'Off-page continuation arrows & connector pairing' },
  { id: 'validation', label: 'Validation Engine', desc: 'Consistency verification & backtracking trigger' },
  { id: 'database', label: 'Database Storage', desc: 'Component, connection & validation persistence' },
  { id: 'visual_overlay', label: 'Visual Overlay', desc: 'High-res color-coded annotation generation' }
];

export const ProcessingMonitor: React.FC<ProcessingMonitorProps> = ({
  document,
  onRefresh
}) => {
  const [statusData, setStatusData] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    if (!document) return;

    const fetchStatus = async () => {
      try {
        const data = await api.getDocumentStatus(document.id);
        setStatusData(data);
        if (data.status === 'processing') {
          setIsProcessing(true);
        } else {
          setIsProcessing(false);
        }
      } catch (err) {
        console.error('Error fetching status:', err);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, [document]);

  const handleTriggerProcess = async () => {
    if (!document) return;
    setIsProcessing(true);
    try {
      await api.processDocument(document.id);
      onRefresh();
    } catch (err) {
      console.error('Failed to trigger process:', err);
      setIsProcessing(false);
    }
  };

  if (!document) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center glass-panel rounded-2xl border border-white/5 my-8">
        <FileSearch className="w-12 h-12 text-slate-500 mb-3" />
        <h3 className="text-base font-semibold text-slate-200">No Document Selected</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm">
          Please select a P&ID document from the top bar or upload a new engineering drawing.
        </p>
      </div>
    );
  }

  const stageStatuses = statusData?.stage_statuses || {};
  const progressPct = statusData?.progress_percentage || (document.processing_status === 'completed' ? 100 : 0);
  const backtrackCount = statusData?.backtrack_count || 0;
  const backtrackHistory = statusData?.backtrack_history || [];

  const isDocFailed = document.processing_status === 'failed' || statusData?.status === 'failed';
  const errorMessage = statusData?.error_message;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="glass-panel rounded-2xl p-6 border border-white/10 bg-gradient-to-r from-slate-900/90 via-indigo-950/20 to-slate-900/90 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 text-indigo-400">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-white tracking-tight">{document.filename}</h1>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full uppercase border ${
                  document.processing_status === 'completed'
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : document.processing_status === 'processing'
                    ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30 animate-pulse'
                    : isDocFailed
                    ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                    : 'bg-slate-800 text-slate-400 border-slate-700'
                }`}>
                  {document.processing_status}
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                  {document.doc_type ? document.doc_type.toUpperCase() : 'UNKNOWN'} PDF
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1 font-mono">
                Doc ID: {document.id} | Size: {(document.file_size / (1024 * 1024)).toFixed(2)} MB | Pages: {document.page_count}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              id="btn-reprocess"
              onClick={handleTriggerProcess}
              disabled={isProcessing}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 transition-all shadow-md shadow-indigo-600/30"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${isProcessing ? 'animate-spin' : ''}`} />
              <span>{isProcessing ? 'Processing Pipeline...' : 'Re-run Pipeline'}</span>
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-6">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-1.5">
            <span>PIPELINE PROGRESS</span>
            <span className={isDocFailed ? "text-rose-400 font-bold" : "text-indigo-400 font-bold"}>
              {Math.round(progressPct)}% {isDocFailed ? '(HALTED ON ERROR)' : ''}
            </span>
          </div>
          <div className="w-full h-2.5 bg-slate-800/80 rounded-full overflow-hidden p-0.5 border border-white/5">
            <div
              className={`h-full rounded-full transition-all duration-500 shadow-sm ${
                isDocFailed
                  ? 'bg-rose-500 shadow-rose-500/50'
                  : 'bg-gradient-to-r from-blue-500 via-indigo-500 to-emerald-400 shadow-emerald-500/50'
              }`}
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Failure Alert Banner */}
      {isDocFailed && (
        <div className="glass-panel rounded-xl p-4 border border-rose-500/30 bg-rose-500/10 shadow-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="text-sm font-semibold text-rose-300">Pipeline Execution Encountered An Error</div>
            <p className="text-xs text-rose-200/80 font-mono bg-black/30 p-2 rounded border border-rose-500/20">
              {errorMessage || 'Pipeline terminated unexpectedly during processing.'}
            </p>
            <p className="text-xs text-slate-300 mt-2">
              The root cause has been addressed. Click <strong>"Re-run Pipeline"</strong> above to re-execute extraction.
            </p>
          </div>
        </div>
      )}

      {/* Backtracking Notice (if triggered) */}
      {backtrackCount > 0 && (
        <div className="glass-panel rounded-xl p-4 border border-amber-500/30 bg-amber-500/5 shadow-lg">
          <div className="flex items-center gap-2 text-amber-400 text-sm font-semibold mb-2">
            <GitBranch className="w-4 h-4" />
            <span>Autonomous Pipeline Backtracking Activated ({backtrackCount} events)</span>
          </div>
          <p className="text-xs text-slate-300">
            The validation engine detected anomalies and autonomously sent the pipeline back to upstream modules with adaptive parameters:
          </p>
          <div className="mt-3 space-y-1.5">
            {backtrackHistory.map((bh: any, idx: number) => (
              <div key={idx} className="flex items-center gap-2 text-xs font-mono bg-slate-900/60 p-2 rounded-lg border border-amber-500/20 text-slate-300">
                <span className="text-amber-400 font-bold">[{bh.from_stage} &rarr; {bh.to_stage}]</span>
                <span className="text-slate-400">{bh.reason}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pipeline Stages Grid */}
      <div className="glass-panel rounded-2xl p-6 border border-white/10">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <span>Execution Stages</span>
          <span className="text-xs text-slate-400 font-normal">({PIPELINE_STAGES.length} Modular Micro-Services)</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {PIPELINE_STAGES.map((stage, idx) => {
            const stageInfo = stageStatuses[stage.id];
            const isDone = stageInfo?.status === 'done' || document.processing_status === 'completed';
            const isFailedStage = stageInfo?.status === 'failed' || (isDocFailed && stageInfo?.status === 'running');
            const isRunning = stageInfo?.status === 'running' && !isDocFailed;

            return (
              <div
                key={stage.id}
                className={`p-3.5 rounded-xl border transition-all ${
                  isDone
                    ? 'bg-emerald-950/20 border-emerald-500/30'
                    : isFailedStage
                    ? 'bg-rose-950/30 border-rose-500/40 ring-1 ring-rose-500/30'
                    : isRunning
                    ? 'bg-indigo-950/30 border-indigo-500/40 ring-1 ring-indigo-500/30'
                    : 'bg-slate-900/30 border-white/5 opacity-70'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold font-mono ${
                      isDone
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : isFailedStage
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        : isRunning
                        ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 animate-pulse'
                        : 'bg-slate-800 text-slate-500'
                    }`}>
                      {idx + 1}
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold text-white">{stage.label}</h4>
                      <p className="text-[11px] text-slate-400 leading-tight mt-0.5">{stage.desc}</p>
                    </div>
                  </div>

                  <div>
                    {isDone ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : isFailedStage ? (
                      <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                    ) : isRunning ? (
                      <div className="w-3.5 h-3.5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin shrink-0" />
                    ) : (
                      <Clock className="w-4 h-4 text-slate-600 shrink-0" />
                    )}
                  </div>
                </div>

                {stageInfo?.matches_found !== undefined && (
                  <div className="mt-2 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    Matches: {stageInfo.matches_found}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
