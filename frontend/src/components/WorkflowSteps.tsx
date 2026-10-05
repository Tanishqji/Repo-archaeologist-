import React, { useState } from 'react';
import { WorkflowStep } from '../types/report';
import { Check } from 'lucide-react';
import { copyToClipboard } from '../lib/sanitize';

interface WorkflowStepsProps {
  workflow: WorkflowStep[];
  dataFlow?: string;
}

export const WorkflowSteps: React.FC<WorkflowStepsProps> = ({ workflow, dataFlow }) => {
  const [copiedPath, setCopiedPath] = useState<string | null>(null);

  const handleCopy = async (path: string) => {
    const ok = await copyToClipboard(path);
    if (ok) {
      setCopiedPath(path);
      setTimeout(() => setCopiedPath(null), 2000);
    }
  };

  if (!workflow || workflow.length === 0) {
    return (
      <div className="p-6 rounded-xl bg-surface border border-border text-center text-text-muted text-sm italic">
        Workflow data flow not detected.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {dataFlow && (
        <div className="p-4 rounded-xl bg-surface-2/40 border border-border text-xs text-text-muted leading-relaxed">
          <span className="font-semibold text-text uppercase tracking-wider text-[11px] block mb-1">
            Data Flow Overview
          </span>
          {dataFlow}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {workflow.map((item) => (
          <div
            key={item.step}
            className="p-4 rounded-xl bg-surface border border-border flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="w-5 h-5 rounded-full bg-primary/20 border border-primary/40 text-primary font-mono text-xs flex items-center justify-center font-bold">
                  {item.step}
                </span>
                <span className="text-xs font-semibold text-text">Phase {item.step}</span>
              </div>
              <p className="text-xs text-text-muted leading-relaxed mb-3">
                {item.description}
              </p>
            </div>

            {item.evidence && item.evidence.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-auto pt-2 border-t border-border/50">
                {item.evidence.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => handleCopy(p)}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-2 text-[11px] font-mono text-text hover:border-primary/40 border border-border transition-colors cursor-pointer"
                    title={`Click to copy: ${p}`}
                  >
                    {copiedPath === p ? (
                      <Check className="w-3 h-3 text-success" />
                    ) : (
                      <span className="truncate max-w-[150px]">{p}</span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
