import React, { useState } from 'react';
import { TechStackGroup } from '../types/report';
import { Layers, Server, Database, Cloud, CheckSquare, Package, Check } from 'lucide-react';
import { copyToClipboard } from '../lib/sanitize';

interface StackCardsProps {
  techStack: TechStackGroup;
}

export const StackCards: React.FC<StackCardsProps> = ({ techStack }) => {
  const [copiedPath, setCopiedPath] = useState<string | null>(null);

  const handleCopy = async (path: string) => {
    const ok = await copyToClipboard(path);
    if (ok) {
      setCopiedPath(path);
      setTimeout(() => setCopiedPath(null), 2000);
    }
  };

  const categories = [
    { title: 'Frontend', icon: Layers, items: techStack.frontend, color: 'text-sky-400' },
    { title: 'Backend', icon: Server, items: techStack.backend, color: 'text-indigo-400' },
    { title: 'Database & Storage', icon: Database, items: techStack.database, color: 'text-emerald-400' },
    { title: 'DevOps & Infra', icon: Cloud, items: techStack.devops, color: 'text-cyan-400' },
    { title: 'Testing Suite', icon: CheckSquare, items: techStack.testing, color: 'text-amber-400' },
    { title: 'Libraries & Tools', icon: Package, items: techStack.other, color: 'text-purple-400' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {categories.map(({ title, icon: Icon, items, color }) => (
        <div
          key={title}
          className="p-5 rounded-xl bg-surface border border-border flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Icon className={`w-4 h-4 ${color}`} />
              <h3 className="text-sm font-semibold text-text">{title}</h3>
              <span className="text-xs text-text-muted ml-auto font-mono">
                {items.length}
              </span>
            </div>

            {items.length === 0 ? (
              <p className="text-xs text-text-muted italic">Not detected</p>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {items.map((item) => (
                  <div
                    key={item.name}
                    className="group relative inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-2 border border-border text-xs font-mono text-text hover:border-primary/50 transition-colors"
                  >
                    <span>{item.name}</span>
                    {item.evidence.length > 0 && (
                      <button
                        type="button"
                        onClick={() => handleCopy(item.evidence[0])}
                        title={`Evidence: ${item.evidence.join(', ')} (click to copy)`}
                        className="text-text-muted hover:text-accent transition-colors"
                      >
                        {copiedPath === item.evidence[0] ? (
                          <Check className="w-3 h-3 text-success" />
                        ) : (
                          <span className="text-[10px] text-text-muted group-hover:text-accent font-sans">
                            [{item.evidence[0].split('/').pop()}]
                          </span>
                        )}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
