import React, { useState } from 'react';
import { AnalysisReport } from '../types/report';
import {
  Star,
  GitBranch,
  Scale,
  Hash,
  Download,
  Copy,
  RotateCcw,
  MessageSquare,
  Check,
  ShieldAlert,
  ShieldCheck,
  Zap,
  Terminal,
  FileCode,
  Globe,
  Key,
} from 'lucide-react';
import { copyToClipboard } from '../lib/sanitize';
import { WarningsBanner } from './WarningsBanner';
import { StackCards } from './StackCards';
import { ArchitectureDiagram } from './ArchitectureDiagram';
import { WorkflowSteps } from './WorkflowSteps';
import { MetricsPanel } from './MetricsPanel';
import { ChatPanel } from './ChatPanel';

interface ReportViewProps {
  report: AnalysisReport;
  onReanalyze: () => void;
}

export const ReportView: React.FC<ReportViewProps> = ({ report, onReanalyze }) => {
  const [copiedMd, setCopiedMd] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [endpointSearch, setEndpointSearch] = useState('');
  const [copiedCodeIndex, setCopiedCodeIndex] = useState<number | null>(null);

  const handleCopyMarkdown = async () => {
    const md = `# Repository Analysis: ${report.repo.owner}/${report.repo.name}
${report.summary}

## Project Type
${report.project_type}

## Architecture Pattern
${report.architecture.pattern}

## Tech Stack
${JSON.stringify(report.tech_stack, null, 2)}

## Metrics
- Files: ${report.metrics.files}
- Approximate LOC: ${report.metrics.loc}
- Has Tests: ${report.metrics.has_tests}
- Has CI: ${report.metrics.has_ci}

## How to Run
\`\`\`bash
${report.how_to_run.steps.join('\n')}
\`\`\`
`;
    const ok = await copyToClipboard(md);
    if (ok) {
      setCopiedMd(true);
      setTimeout(() => setCopiedMd(false), 2000);
    }
  };

  const handleDownloadJson = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${report.repo.owner}-${report.repo.name}-analysis.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleCopyCodeStep = async (step: string, idx: number) => {
    const ok = await copyToClipboard(step);
    if (ok) {
      setCopiedCodeIndex(idx);
      setTimeout(() => setCopiedCodeIndex(null), 2000);
    }
  };

  const filteredEndpoints = report.api_endpoints.filter(
    (ep) =>
      ep.path.toLowerCase().includes(endpointSearch.toLowerCase()) ||
      ep.method.toLowerCase().includes(endpointSearch.toLowerCase()) ||
      ep.file.toLowerCase().includes(endpointSearch.toLowerCase())
  );

  return (
    <div className="w-full max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Sticky Header */}
      <header className="sticky top-0 z-30 p-4 rounded-xl bg-surface/90 backdrop-blur-md border border-border flex flex-wrap items-center justify-between gap-4 shadow-lg">
        <div className="flex items-center gap-3 flex-wrap">
          <h2 className="text-xl font-bold text-text font-sans">
            <span className="text-text-muted">{report.repo.owner} /</span> {report.repo.name}
          </h2>

          <div className="flex items-center gap-2 text-xs text-text-muted font-mono">
            {report.repo.stars > 0 && (
              <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-surface-2 border border-border text-amber-400">
                <Star className="w-3.5 h-3.5 fill-amber-400" />
                {report.repo.stars.toLocaleString()}
              </span>
            )}
            <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-surface-2 border border-border">
              <GitBranch className="w-3.5 h-3.5 text-primary" />
              {report.repo.default_branch}
            </span>
            {report.repo.license && (
              <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-surface-2 border border-border">
                <Scale className="w-3.5 h-3.5 text-accent" />
                {report.repo.license}
              </span>
            )}
            {report.repo.commit_sha && (
              <span className="hidden sm:flex items-center gap-1 px-2 py-0.5 rounded bg-surface-2 border border-border">
                <Hash className="w-3 h-3 text-text-muted" />
                {report.repo.commit_sha.substring(0, 7)}
              </span>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCopyMarkdown}
            className="px-3 py-1.5 rounded-lg bg-surface-2 hover:bg-border text-xs font-medium text-text flex items-center gap-1.5 border border-border transition-colors cursor-pointer"
            title="Copy Report as Markdown"
          >
            {copiedMd ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline">Copy MD</span>
          </button>

          <button
            type="button"
            onClick={handleDownloadJson}
            className="px-3 py-1.5 rounded-lg bg-surface-2 hover:bg-border text-xs font-medium text-text flex items-center gap-1.5 border border-border transition-colors cursor-pointer"
            title="Download JSON Report"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">JSON</span>
          </button>

          <button
            type="button"
            onClick={onReanalyze}
            className="px-3 py-1.5 rounded-lg bg-surface-2 hover:bg-border text-xs font-medium text-text flex items-center gap-1.5 border border-border transition-colors cursor-pointer"
            title="Force re-analyze repository"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Re-scan</span>
          </button>

          <button
            type="button"
            onClick={() => setIsChatOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-primary hover:bg-primary-hover text-xs font-medium text-white flex items-center gap-1.5 transition-colors cursor-pointer shadow-md"
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Repo Chat</span>
          </button>
        </div>
      </header>

      {/* Warnings & Confidence */}
      <WarningsBanner
        warnings={report.warnings}
        confidence={report.confidence}
        llmStatus={report.llm_status}
      />

      {/* Summary Card */}
      <section className="p-6 rounded-2xl bg-surface border border-border shadow-md">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-bold text-accent uppercase tracking-wider">
            Executive Summary
          </span>
          <span className="px-2.5 py-0.5 rounded-full bg-primary/10 border border-primary/30 text-primary font-mono text-xs capitalize">
            {report.project_type}
          </span>
        </div>
        <p className="text-base sm:text-lg text-text leading-relaxed">
          {report.summary}
        </p>
      </section>

      {/* Tech Stack Grid */}
      <section className="space-y-3">
        <h3 className="text-sm font-bold text-text uppercase tracking-wider">
          Detected Tech Stack
        </h3>
        <StackCards techStack={report.tech_stack} />
      </section>

      {/* Architecture & Flowchart */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-text uppercase tracking-wider">
            System Architecture
          </h3>
          <span className="text-xs font-mono text-text-muted">
            Pattern: {report.architecture.pattern}
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Components List */}
          <div className="lg:col-span-4 space-y-2">
            <div className="p-4 rounded-xl bg-surface border border-border">
              <span className="text-xs font-semibold text-text uppercase tracking-wider block mb-3">
                Key Components
              </span>
              <div className="space-y-3">
                {report.architecture.components.map((c, i) => (
                  <div key={i} className="text-xs border-b border-border/50 pb-2.5 last:border-0 last:pb-0">
                    <div className="font-semibold text-text">{c.name}</div>
                    <div className="text-text-muted mt-0.5">{c.role}</div>
                    {c.evidence.length > 0 && (
                      <div className="mt-1 font-mono text-[10px] text-accent truncate">
                        {c.evidence.join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Mermaid Diagram */}
          <div className="lg:col-span-8">
            <ArchitectureDiagram mermaidCode={report.architecture.mermaid} />
          </div>
        </div>
      </section>

      {/* Workflow Steps */}
      <section className="space-y-3">
        <h3 className="text-sm font-bold text-text uppercase tracking-wider">
          Request & Execution Flow
        </h3>
        <WorkflowSteps
          workflow={report.workflow}
          dataFlow={report.architecture.data_flow}
        />
      </section>

      {/* Metrics Panel */}
      <section className="space-y-3">
        <h3 className="text-sm font-bold text-text uppercase tracking-wider">
          Repo Metrics & Health
        </h3>
        <MetricsPanel metrics={report.metrics} />
      </section>

      {/* Run Instructions & Key Files */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* How to run */}
        <div className="p-6 rounded-2xl bg-surface border border-border flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Terminal className="w-4 h-4 text-primary" />
              <h3 className="text-sm font-bold text-text uppercase tracking-wider">
                How to Run Locally
              </h3>
              <span className="text-[11px] text-text-muted ml-auto font-mono">
                source: {report.how_to_run.source}
              </span>
            </div>

            {report.how_to_run.prerequisites.length > 0 && (
              <div className="mb-4">
                <span className="text-xs text-text-muted font-medium block mb-1.5">
                  Prerequisites:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {report.how_to_run.prerequisites.map((prereq, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 rounded bg-surface-2 border border-border font-mono text-xs text-text"
                    >
                      {prereq}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="space-y-2">
              <span className="text-xs text-text-muted font-medium block mb-1">
                Commands:
              </span>
              {report.how_to_run.steps.map((step, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 rounded-lg bg-surface-2 border border-border font-mono text-xs text-text group"
                >
                  <code className="text-accent truncate pr-2">{step}</code>
                  <button
                    type="button"
                    onClick={() => handleCopyCodeStep(step, idx)}
                    className="p-1 rounded hover:bg-surface text-text-muted hover:text-text cursor-pointer"
                    title="Copy command"
                  >
                    {copiedCodeIndex === idx ? (
                      <Check className="w-3.5 h-3.5 text-success" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Key Files */}
        <div className="p-6 rounded-2xl bg-surface border border-border">
          <div className="flex items-center gap-2 mb-4">
            <FileCode className="w-4 h-4 text-accent" />
            <h3 className="text-sm font-bold text-text uppercase tracking-wider">
              Key Entry & Anchor Files
            </h3>
          </div>

          <div className="space-y-2.5 max-h-[340px] overflow-y-auto pr-1">
            {report.key_files.map((kf, i) => (
              <div
                key={i}
                className="p-2.5 rounded-lg bg-surface-2 border border-border text-xs flex flex-col gap-0.5"
              >
                <div className="font-mono text-text font-medium truncate">{kf.path}</div>
                <div className="text-text-muted text-[11px]">{kf.why_important}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* API Endpoints & Environment Variables */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Endpoints */}
        <div className="lg:col-span-8 p-6 rounded-2xl bg-surface border border-border space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-indigo-400" />
              <h3 className="text-sm font-bold text-text uppercase tracking-wider">
                API Surface ({report.api_endpoints.length})
              </h3>
            </div>
            {report.api_endpoints.length > 5 && (
              <input
                type="text"
                placeholder="Filter endpoints..."
                value={endpointSearch}
                onChange={(e) => setEndpointSearch(e.target.value)}
                className="px-2.5 py-1 rounded-lg bg-surface-2 border border-border text-xs text-text placeholder:text-text-muted/60 outline-none"
              />
            )}
          </div>

          {report.api_endpoints.length === 0 ? (
            <p className="text-xs text-text-muted italic py-4">
              No API route definitions detected in source files.
            </p>
          ) : (
            <div className="overflow-x-auto max-h-[300px]">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border text-text-muted">
                    <th className="pb-2 font-medium">Method</th>
                    <th className="pb-2 font-medium">Route Path</th>
                    <th className="pb-2 font-medium">File</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40 font-mono">
                  {filteredEndpoints.slice(0, 30).map((ep, idx) => (
                    <tr key={idx} className="hover:bg-surface-2/40">
                      <td className="py-2 pr-3">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            ep.method === 'GET'
                              ? 'bg-emerald-500/10 text-emerald-400'
                              : ep.method === 'POST'
                              ? 'bg-sky-500/10 text-sky-400'
                              : ep.method === 'DELETE'
                              ? 'bg-red-500/10 text-red-400'
                              : 'bg-amber-500/10 text-amber-400'
                          }`}
                        >
                          {ep.method}
                        </span>
                      </td>
                      <td className="py-2 pr-3 text-text truncate max-w-[200px]">{ep.path}</td>
                      <td className="py-2 text-text-muted truncate max-w-[180px]">{ep.file}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filteredEndpoints.length > 30 && (
                <div className="text-[11px] text-text-muted text-center pt-2">
                  Showing first 30 of {filteredEndpoints.length} endpoints
                </div>
              )}
            </div>
          )}
        </div>

        {/* Env Variables */}
        <div className="lg:col-span-4 p-6 rounded-2xl bg-surface border border-border space-y-3">
          <div className="flex items-center gap-2">
            <Key className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-bold text-text uppercase tracking-wider">
              Environment Variables
            </h3>
          </div>

          {report.env_variables.length === 0 ? (
            <p className="text-xs text-text-muted italic py-4">
              No .env.example or template variables detected.
            </p>
          ) : (
            <div className="space-y-1.5 max-h-[300px] overflow-y-auto">
              {report.env_variables.map((env, i) => (
                <div
                  key={i}
                  className="px-2.5 py-1.5 rounded-lg bg-surface-2 border border-border font-mono text-xs text-accent truncate"
                >
                  {env}
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Strengths / Weaknesses / Risks */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Strengths */}
        <div className="p-5 rounded-xl bg-surface border border-border">
          <div className="flex items-center gap-2 mb-3 text-success">
            <ShieldCheck className="w-4 h-4" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-text">Strengths</h4>
          </div>
          <ul className="space-y-2 text-xs text-text-muted">
            {report.strengths.map((s, i) => (
              <li key={i} className="flex items-start gap-1.5">
                <span className="text-success mt-0.5">•</span>
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Weaknesses */}
        <div className="p-5 rounded-xl bg-surface border border-border">
          <div className="flex items-center gap-2 mb-3 text-warning">
            <ShieldAlert className="w-4 h-4" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-text">Weaknesses</h4>
          </div>
          <ul className="space-y-2 text-xs text-text-muted">
            {report.weaknesses.map((w, i) => (
              <li key={i} className="flex items-start gap-1.5">
                <span className="text-warning mt-0.5">•</span>
                <span>{w}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Risks */}
        <div className="p-5 rounded-xl bg-surface border border-border">
          <div className="flex items-center gap-2 mb-3 text-danger">
            <Zap className="w-4 h-4" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-text">Risks</h4>
          </div>
          <ul className="space-y-2 text-xs text-text-muted">
            {report.risks.map((r, i) => (
              <li key={i} className="flex items-start gap-1.5">
                <span className="text-danger mt-0.5">•</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Chat Drawer */}
      <ChatPanel
        owner={report.repo.owner}
        repo={report.repo.name}
        sha={report.repo.commit_sha}
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
      />
    </div>
  );
};
