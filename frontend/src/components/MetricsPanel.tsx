import React from 'react';
import { Metrics } from '../types/report';
import { FileCode, Activity, CheckCircle, XCircle, Container, BookOpen } from 'lucide-react';

interface MetricsPanelProps {
  metrics: Metrics;
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({ metrics }) => {
  const items = [
    {
      label: 'Repository Files',
      value: metrics.files.toLocaleString(),
      icon: FileCode,
      sub: 'Tracked source files',
    },
    {
      label: 'Lines of Code',
      value: `~${metrics.loc.toLocaleString()}`,
      icon: Activity,
      sub: 'Approximate LOC',
    },
    {
      label: 'Automated Tests',
      value: metrics.has_tests ? 'Present' : 'Not detected',
      icon: metrics.has_tests ? CheckCircle : XCircle,
      color: metrics.has_tests ? 'text-success' : 'text-text-muted',
      sub: metrics.has_tests ? 'Test suites found' : 'No tests detected',
    },
    {
      label: 'CI / CD Workflows',
      value: metrics.has_ci ? 'Configured' : 'None',
      icon: metrics.has_ci ? CheckCircle : XCircle,
      color: metrics.has_ci ? 'text-success' : 'text-text-muted',
      sub: metrics.has_ci ? 'Automated pipelines' : 'No CI configuration',
    },
    {
      label: 'Containerization',
      value: metrics.has_docker ? 'Docker Ready' : 'None',
      icon: Container,
      color: metrics.has_docker ? 'text-cyan-400' : 'text-text-muted',
      sub: metrics.has_docker ? 'Dockerfile / Compose' : 'No container config',
    },
    {
      label: 'README Quality',
      value: `${metrics.readme_score} / 100`,
      icon: BookOpen,
      color: metrics.readme_score > 60 ? 'text-accent' : 'text-warning',
      sub: 'Structure & setup docs',
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {items.map((it) => {
        const Icon = it.icon;
        return (
          <div
            key={it.label}
            className="p-4 rounded-xl bg-surface border border-border flex flex-col justify-between"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
                {it.label}
              </span>
              <Icon className={`w-4 h-4 ${it.color || 'text-text-muted'}`} />
            </div>
            <div>
              <div className="text-lg font-bold text-text font-mono">{it.value}</div>
              <div className="text-[11px] text-text-muted/70">{it.sub}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
