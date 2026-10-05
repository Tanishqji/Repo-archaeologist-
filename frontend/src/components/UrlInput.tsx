import React, { useState } from 'react';
import { ArrowRight, Github, Sparkles, Loader2 } from 'lucide-react';

interface UrlInputProps {
  onAnalyze: (url: string) => void;
  isLoading: boolean;
}

export const UrlInput: React.FC<UrlInputProps> = ({ onAnalyze, isLoading }) => {
  const [inputVal, setInputVal] = useState('');

  // Extract owner/repo preview
  const getPreview = (val: string) => {
    const trimmed = val.trim();
    if (!trimmed) return null;
    const match = trimmed.match(/(?:github\.com\/|^)([A-Za-z0-9_.-]+)\/([A-Za-z0-9_.-]+?)(?:\.git|\/|$)/);
    if (match) {
      return `${match[1]}/${match[2]}`;
    }
    return null;
  };

  const preview = getPreview(inputVal);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputVal.trim() && !isLoading) {
      onAnalyze(inputVal.trim());
    }
  };

  const exampleRepos = ['fastapi/fastapi', 'facebook/react', 'pallets/flask'];

  return (
    <div className="w-full max-w-2xl mx-auto text-center pt-8 pb-12 px-4">
      <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-2 border border-border text-xs text-text-muted mb-6">
        <Sparkles className="w-3.5 h-3.5 text-accent" />
        <span>Accurate, evidence-grounded repo analysis</span>
      </div>

      <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-text mb-4">
        Understand any <span className="text-primary">GitHub repo</span> in seconds
      </h1>

      <p className="text-base sm:text-lg text-text-muted mb-8 max-w-xl mx-auto">
        Deep architectural breakdown, verified tech stack, data flow diagrams, and follow-up AI chat backed by static analysis.
      </p>

      <form onSubmit={handleSubmit} className="relative mb-4">
        <div className="relative flex items-center shadow-lg rounded-xl overflow-hidden border border-border bg-surface focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 transition-all">
          <div className="pl-4 text-text-muted">
            <Github className="w-5 h-5" />
          </div>

          <input
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            placeholder="Paste GitHub URL or owner/repo (e.g. fastapi/fastapi)"
            disabled={isLoading}
            className="w-full h-14 pl-3 pr-32 bg-transparent text-text placeholder:text-text-muted/60 text-sm sm:text-base outline-none font-sans"
          />

          <button
            type="submit"
            disabled={!inputVal.trim() || isLoading}
            className="absolute right-2 px-4 h-10 rounded-lg bg-primary hover:bg-primary-hover disabled:opacity-50 text-white font-medium text-sm flex items-center gap-2 transition-colors cursor-pointer"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Scanning...</span>
              </>
            ) : (
              <>
                <span>Analyze</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>

        {/* Live Repo Preview Pill */}
        {preview && (
          <div className="flex items-center justify-start mt-2 px-2 text-xs text-text-muted gap-2">
            <span>Target repository:</span>
            <span className="font-mono bg-surface-2 border border-border px-2 py-0.5 rounded text-accent font-medium">
              {preview}
            </span>
          </div>
        )}
      </form>

      {/* Example repo chips */}
      <div className="flex flex-wrap items-center justify-center gap-2 text-xs text-text-muted">
        <span>Try an example:</span>
        {exampleRepos.map((repo) => (
          <button
            key={repo}
            type="button"
            onClick={() => {
              setInputVal(repo);
              onAnalyze(repo);
            }}
            className="px-2.5 py-1 rounded-md bg-surface border border-border hover:border-primary/50 hover:text-text transition-colors font-mono cursor-pointer"
          >
            {repo}
          </button>
        ))}
      </div>
      <p className="text-xs text-text-muted/60 mt-4">Public GitHub repositories only</p>
    </div>
  );
};
