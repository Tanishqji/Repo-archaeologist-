import React from 'react';
import { Check, Loader2 } from 'lucide-react';

interface ProgressStagesProps {
  stage: string;
  progressPct: number;
}

const STAGES = [
  { key: 'validating', label: 'Validating' },
  { key: 'fetching', label: 'Fetching' },
  { key: 'scanning', label: 'Scanning' },
  { key: 'analyzing', label: 'Analyzing' },
  { key: 'diagramming', label: 'Diagramming' },
  { key: 'done', label: 'Complete' },
];

export const ProgressStages: React.FC<ProgressStagesProps> = ({ stage, progressPct }) => {
  const currentStageIndex = STAGES.findIndex((s) => s.key === stage.toLowerCase());
  const activeIndex = currentStageIndex >= 0 ? currentStageIndex : 0;

  return (
    <div className="w-full max-w-3xl mx-auto my-8 p-6 bg-surface border border-border rounded-xl shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-text uppercase tracking-wider">
            Analysis in Progress
          </h2>
          <p className="text-xs text-text-muted">
            Extracting manifests, parsing architecture, and verifying evidence...
          </p>
        </div>
        <div className="text-sm font-mono font-medium text-primary">
          {progressPct}%
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-2 bg-surface-2 rounded-full overflow-hidden mb-6">
        <div
          className="h-full bg-primary transition-all duration-500 ease-out"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Stepper items */}
      <div className="grid grid-cols-6 gap-2 text-center">
        {STAGES.map((s, idx) => {
          const isDone = idx < activeIndex || stage === 'done';
          const isCurrent = idx === activeIndex && stage !== 'done';

          return (
            <div key={s.key} className="flex flex-col items-center">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold mb-1.5 transition-colors ${
                  isDone
                    ? 'bg-success text-bg'
                    : isCurrent
                    ? 'bg-primary text-white ring-4 ring-primary/20 animate-pulse'
                    : 'bg-surface-2 text-text-muted border border-border'
                }`}
              >
                {isDone ? (
                  <Check className="w-4 h-4" />
                ) : isCurrent ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <span>{idx + 1}</span>
                )}
              </div>
              <span
                className={`text-[11px] truncate max-w-[70px] ${
                  isCurrent ? 'text-primary font-medium' : isDone ? 'text-text' : 'text-text-muted/60'
                }`}
              >
                {s.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
