import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  ShieldCheck, 
  RotateCcw, 
  GitBranch, 
  Layers, 
  Filter,
  Info
} from 'lucide-react';
import { DocumentItem, ValidationSummary, ValidationIssue } from '../types';
import { api } from '../services/api';

interface ValidationViewProps {
  document: DocumentItem | null;
}

export const ValidationView: React.FC<ValidationViewProps> = ({
  document,
}) => {
  const [validation, setValidation] = useState<ValidationSummary | null>(null);
  const [statusData, setStatusData] = useState<any>(null);
  const [severityFilter, setSeverityFilter] = useState<'ALL' | 'ERROR' | 'WARNING' | 'VALID'>('ALL');

  useEffect(() => {
    if (!document) return;

    const loadValidationData = async () => {
      try {
        const [valData, statData] = await Promise.all([
          api.getValidation(document.id),
          api.getDocumentStatus(document.id)
        ]);
        setValidation(valData);
        setStatusData(statData);
      } catch (err) {
        console.error('Failed to load validation data:', err);
      }
    };

    loadValidationData();
  }, [document]);

  if (!document) {
    return (
      <div className="flex flex-col items-center justify-center p-16 text-center glass-panel rounded-2xl border border-white/5 my-8">
        <ShieldCheck className="w-12 h-12 text-slate-500 mb-3" />
        <h3 className="text-base font-semibold text-slate-200">No Document Selected</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm">
          Please select a document to inspect the engineering validation report.
        </p>
      </div>
    );
  }

  const validCount = validation?.valid_count || 0;
  const warningCount = validation?.warning_count || 0;
  const errorCount = validation?.error_count || 0;
  const total = validation?.total_components || 0;
  const healthRate = total > 0 ? Math.round((validCount / total) * 100) : 100;

  const backtrackHistory = statusData?.backtrack_history || [];

  const filteredIssues = (validation?.issues || []).filter((issue) => {
    if (severityFilter === 'ALL') return true;
    return issue.severity === severityFilter;
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Health Metrics Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Health Score */}
        <div className="glass-panel rounded-2xl p-5 border border-white/10 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-mono text-slate-400 uppercase">Extraction Health Rate</span>
            <div className="text-2xl font-bold font-mono text-white mt-1 flex items-baseline gap-1">
              <span>{healthRate}%</span>
              <span className="text-xs font-normal text-emerald-400">Score</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">Based on ISA-5.1 consistency rules</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 border border-emerald-500/20">
            <ShieldCheck className="w-6 h-6" />
          </div>
        </div>

        {/* Valid Components */}
        <div className="glass-panel rounded-2xl p-5 border border-white/10 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-mono text-slate-400 uppercase">Valid Components</span>
            <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">{validCount}</div>
            <p className="text-[11px] text-slate-400 mt-0.5">All verification checks passed</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>

        {/* Warnings */}
        <div className="glass-panel rounded-2xl p-5 border border-white/10 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-mono text-slate-400 uppercase">Anomalies / Warnings</span>
            <div className="text-2xl font-bold font-mono text-amber-400 mt-1">{warningCount}</div>
            <p className="text-[11px] text-slate-400 mt-0.5">Low confidence or isolated nodes</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400 border border-amber-500/20">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>

        {/* Errors / Backtrack Events */}
        <div className="glass-panel rounded-2xl p-5 border border-white/10 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-mono text-slate-400 uppercase">Backtracks Executed</span>
            <div className="text-2xl font-bold font-mono text-indigo-400 mt-1">{statusData?.backtrack_count || 0}</div>
            <p className="text-[11px] text-slate-400 mt-0.5">Autonomous self-correcting reruns</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
            <GitBranch className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Backtrack History Log if applicable */}
      {backtrackHistory.length > 0 && (
        <div className="glass-panel rounded-2xl p-5 border border-indigo-500/30 bg-indigo-950/20 shadow-lg">
          <div className="flex items-center gap-2 text-indigo-400 text-sm font-semibold mb-3">
            <RotateCcw className="w-4 h-4" />
            <span>Autonomous Pipeline Backtrack History</span>
          </div>
          <div className="space-y-2">
            {backtrackHistory.map((b: any, idx: number) => (
              <div key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between text-xs font-mono bg-slate-900/80 p-3 rounded-xl border border-white/10">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-bold">
                    {b.from_stage} &rarr; {b.to_stage}
                  </span>
                  <span className="text-slate-300">{b.reason}</span>
                </div>
                <span className="text-slate-500 text-[11px] mt-1 sm:mt-0">{b.timestamp}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Issues Table & Filter Bar */}
      <div className="glass-panel rounded-2xl border border-white/10 overflow-hidden shadow-xl">
        <div className="p-4 border-b border-white/5 flex flex-wrap items-center justify-between gap-3 bg-slate-900/80">
          <div>
            <h3 className="text-sm font-semibold text-white">Rule Verification Diagnostics</h3>
            <p className="text-xs text-slate-400">Detailed list of checks, violations, and recommended remediations</p>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-lg border border-slate-800">
            <button
              onClick={() => setSeverityFilter('ALL')}
              className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
                severityFilter === 'ALL' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All ({validation?.issues.length || 0})
            </button>
            <button
              onClick={() => setSeverityFilter('WARNING')}
              className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
                severityFilter === 'WARNING' ? 'bg-amber-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Warnings ({warningCount})
            </button>
            <button
              onClick={() => setSeverityFilter('ERROR')}
              className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
                severityFilter === 'ERROR' ? 'bg-rose-600 text-white font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Errors ({errorCount})
            </button>
          </div>
        </div>

        {/* Issue Cards */}
        <div className="p-4 space-y-3">
          {filteredIssues.length === 0 ? (
            <div className="text-center py-12">
              <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-2" />
              <p className="text-sm font-semibold text-white">All Active Checks Passed</p>
              <p className="text-xs text-slate-400 mt-1">No validation errors or warnings found matching this filter.</p>
            </div>
          ) : (
            filteredIssues.map((issue) => (
              <div 
                key={issue.id}
                className={`p-4 rounded-xl border transition-all ${
                  issue.severity === 'ERROR'
                    ? 'bg-rose-950/20 border-rose-500/30'
                    : 'bg-amber-950/20 border-amber-500/30'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                      issue.severity === 'ERROR'
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    }`}>
                      {issue.rule_name}
                    </span>
                    {issue.component_tag && (
                      <span className="font-mono text-xs font-bold text-white bg-slate-900 px-2 py-0.5 rounded border border-white/10">
                        {issue.component_tag}
                      </span>
                    )}
                  </div>

                  {issue.backtrack_suggested && (
                    <span className="text-[11px] font-mono text-indigo-400 flex items-center gap-1">
                      <span>Target stage:</span>
                      <span className="bg-indigo-500/10 px-1.5 py-0.5 rounded border border-indigo-500/20 font-bold">
                        {issue.backtrack_suggested}
                      </span>
                    </span>
                  )}
                </div>

                <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                  {issue.message}
                </p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
