import React from 'react';
import { Confidence } from '../types/report';
import { AlertTriangle, ShieldCheck, ShieldAlert, Info } from 'lucide-react';

interface WarningsBannerProps {
  warnings: string[];
  confidence: Confidence;
  llmStatus: 'ok' | 'degraded';
}

export const WarningsBanner: React.FC<WarningsBannerProps> = ({
  warnings,
  confidence,
  llmStatus,
}) => {
  const getConfidenceBadge = (score: number) => {
    const pct = Math.round(score * 100);
    if (score >= 0.8) {
      return {
        label: `High Confidence (${pct}%)`,
        color: 'bg-success/10 text-success border-success/30',
        icon: ShieldCheck,
      };
    }
    if (score >= 0.5) {
      return {
        label: `Medium Confidence (${pct}%)`,
        color: 'bg-warning/10 text-warning border-warning/30',
        icon: ShieldAlert,
      };
    }
    return {
      label: `Low Confidence (${pct}%)`,
      color: 'bg-danger/10 text-danger border-danger/30',
      icon: AlertTriangle,
    };
  };

  const badge = getConfidenceBadge(confidence.score);
  const BadgeIcon = badge.icon;

  return (
    <div className="space-y-3 mb-6">
      {/* Top Confidence & Mode Pill */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2">
          <div
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-medium ${badge.color}`}
          >
            <BadgeIcon className="w-3.5 h-3.5" />
            <span>{badge.label}</span>
          </div>
          {confidence.notes && (
            <span className="text-text-muted text-xs hidden sm:inline">
              — {confidence.notes}
            </span>
          )}
        </div>

        {llmStatus === 'degraded' && (
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-warning/10 border border-warning/30 text-warning font-mono text-[11px]">
            <Info className="w-3.5 h-3.5" />
            <span>Static-facts mode (AI degraded)</span>
          </div>
        )}
      </div>

      {/* Warnings List */}
      {warnings.length > 0 && (
        <div className="p-4 rounded-xl bg-warning/5 border border-warning/20 space-y-1.5">
          {warnings.map((w, i) => (
            <div key={i} className="flex items-start gap-2 text-xs text-warning">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{w}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
