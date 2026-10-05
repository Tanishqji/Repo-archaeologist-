import { useState } from 'react';
import { UrlInput } from './components/UrlInput';
import { ProgressStages } from './components/ProgressStages';
import { ReportView } from './components/ReportView';
import { ErrorState } from './components/ErrorState';
import { useAnalyze } from './hooks/useAnalyze';
import { Compass, Moon, Sun, Github, Shield } from 'lucide-react';

export function App() {
  const { report, currentJob, isLoading, error, startAnalysis, retry, reset } = useAnalyze();
  const [isLightMode, setIsLightMode] = useState(false);

  const toggleTheme = () => {
    setIsLightMode(!isLightMode);
    document.documentElement.setAttribute('data-theme', !isLightMode ? 'light' : 'dark');
    if (!isLightMode) {
      document.documentElement.classList.remove('dark');
    } else {
      document.documentElement.classList.add('dark');
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-bg text-text selection:bg-primary/20 selection:text-primary">
      {/* Top Navbar */}
      <nav className="w-full border-b border-border/60 bg-surface/50 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <button
            type="button"
            onClick={reset}
            className="flex items-center gap-2.5 font-bold text-base sm:text-lg tracking-tight hover:opacity-90 transition-opacity cursor-pointer"
          >
            <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/30 flex items-center justify-center text-primary">
              <Compass className="w-5 h-5" />
            </div>
            <span className="font-sans">
              Repo <span className="text-primary font-mono">Archaeologist</span>
            </span>
          </button>

          <div className="flex items-center gap-2 sm:gap-4">
            <button
              type="button"
              onClick={toggleTheme}
              className="p-2 rounded-lg bg-surface border border-border text-text-muted hover:text-text hover:bg-surface-2 transition-colors cursor-pointer"
              title="Toggle Theme"
            >
              {isLightMode ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
            </button>

            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-lg bg-surface border border-border text-text-muted hover:text-text hover:bg-surface-2 transition-colors flex items-center gap-1.5 text-xs font-medium"
            >
              <Github className="w-4 h-4" />
              <span className="hidden sm:inline">GitHub</span>
            </a>
          </div>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col items-center justify-start">
        {/* If no report and not loading: show Hero & URL Input */}
        {!report && !isLoading && !error && (
          <UrlInput onAnalyze={(url) => startAnalysis(url)} isLoading={isLoading} />
        )}

        {/* Loading Progress State */}
        {isLoading && currentJob && (
          <div className="w-full px-4 pt-12 flex flex-col items-center">
            <ProgressStages
              stage={currentJob.stage}
              progressPct={currentJob.progress_pct}
            />
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="w-full px-4">
            <ErrorState error={error} onRetry={retry} onReset={reset} />
          </div>
        )}

        {/* Completed Report View */}
        {report && (
          <ReportView
            report={report}
            onReanalyze={() => startAnalysis(report.repo.url || `${report.repo.owner}/${report.repo.name}`, true)}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-border/40 py-6 text-center text-xs text-text-muted bg-surface/30 mt-auto">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-accent" />
            <span>Strict read-only analysis. Never executes untrusted repository code.</span>
          </div>
          <div>
            Built with deterministic static parsing & grounded AI
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
