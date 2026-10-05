import { useState, useEffect, useRef, useCallback } from 'react';
import { AnalysisReport, JobResponse } from '../types/report';
import { analyzeRepo, getJobStatus } from '../lib/api';

export function useAnalyze() {
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [currentJob, setCurrentJob] = useState<JobResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<{ code: string; message: string; retryable: boolean } | null>(null);

  const pollIntervalRef = useRef<number | null>(null);
  const activeUrlRef = useRef<string>('');

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      window.clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  }, []);

  const pollJob = useCallback(
    (jobId: string) => {
      stopPolling();
      pollIntervalRef.current = window.setInterval(async () => {
        try {
          const job = await getJobStatus(jobId);
          setCurrentJob(job);

          if (job.status === 'completed' && job.report) {
            setReport(job.report);
            setIsLoading(false);
            stopPolling();
          } else if (job.status === 'failed') {
            setError(job.error || { code: 'INTERNAL', message: 'Analysis failed.', retryable: true });
            setIsLoading(false);
            stopPolling();
          }
        } catch (err: any) {
          setError(err);
          setIsLoading(false);
          stopPolling();
        }
      }, 1500);
    },
    [stopPolling]
  );

  const startAnalysis = useCallback(
    async (url: string, forceRefresh: boolean = false) => {
      setIsLoading(true);
      setError(null);
      setReport(null);
      activeUrlRef.current = url;

      // Update URL query param to preserve state on reload
      try {
        const u = new URL(window.location.href);
        u.searchParams.set('repo', url);
        window.history.replaceState({}, '', u.toString());
      } catch (e) {}

      try {
        const initJob = await analyzeRepo(url, forceRefresh);
        setCurrentJob(initJob);

        if (initJob.status === 'completed' && initJob.report) {
          setReport(initJob.report);
          setIsLoading(false);
        } else {
          pollJob(initJob.job_id);
        }
      } catch (err: any) {
        setError(err);
        setIsLoading(false);
      }
    },
    [pollJob]
  );

  const retry = () => {
    if (activeUrlRef.current) {
      startAnalysis(activeUrlRef.current, false);
    }
  };

  const reset = () => {
    stopPolling();
    setReport(null);
    setCurrentJob(null);
    setIsLoading(false);
    setError(null);
    try {
      const u = new URL(window.location.href);
      u.searchParams.delete('repo');
      window.history.replaceState({}, '', u.toString());
    } catch (e) {}
  };

  // Auto-load repo if ?repo=... query param is present on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const repoParam = params.get('repo');
    if (repoParam && !report && !isLoading) {
      startAnalysis(repoParam);
    }
    return () => stopPolling();
  }, []);

  return {
    report,
    currentJob,
    isLoading,
    error,
    startAnalysis,
    retry,
    reset,
  };
}
