import React from 'react';
import { AlertCircle, RotateCcw, Home } from 'lucide-react';
import { getFriendlyErrorMessage } from '../lib/sanitize';

interface ErrorStateProps {
  error?: {
    code?: string;
    message?: string;
    retryable?: boolean;
  } | null;
  onRetry?: () => void;
  onReset: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ error, onRetry, onReset }) => {
  const friendlyMessage = getFriendlyErrorMessage(error?.code, error?.message);

  return (
    <div className="w-full max-w-lg mx-auto my-12 p-8 rounded-2xl bg-surface border border-border text-center shadow-xl">
      <div className="w-12 h-12 rounded-full bg-danger/10 text-danger flex items-center justify-center mx-auto mb-4">
        <AlertCircle className="w-6 h-6" />
      </div>

      <h3 className="text-lg font-bold text-text mb-2">Analysis Failed</h3>
      <p className="text-sm text-text-muted mb-6 leading-relaxed">
        {friendlyMessage}
      </p>

      {error?.code && (
        <div className="mb-6">
          <span className="font-mono text-xs px-2.5 py-1 rounded bg-surface-2 text-text-muted border border-border">
            Code: {error.code}
          </span>
        </div>
      )}

      <div className="flex items-center justify-center gap-3">
        {error?.retryable && onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="px-4 py-2 rounded-lg bg-primary hover:bg-primary-hover text-white text-sm font-medium flex items-center gap-2 transition-colors cursor-pointer"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Try Again</span>
          </button>
        )}
        <button
          type="button"
          onClick={onReset}
          className="px-4 py-2 rounded-lg bg-surface-2 hover:bg-border text-text text-sm font-medium flex items-center gap-2 border border-border transition-colors cursor-pointer"
        >
          <Home className="w-4 h-4" />
          <span>New Search</span>
        </button>
      </div>
    </div>
  );
};
