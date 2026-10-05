import { AnalysisReport, JobResponse, ChatCitation } from '../types/report';

const BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
const API_BASE = `${BASE_URL}/api`;

export async function analyzeRepo(url: string, forceRefresh: boolean = false): Promise<JobResponse> {
  const resp = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, force_refresh: forceRefresh }),
  });

  const data = await resp.json();
  if (!resp.ok) {
    const error = data.error || { code: 'INTERNAL', message: 'Failed to start analysis.' };
    throw error;
  }

  return data;
}

export async function getJobStatus(jobId: string): Promise<JobResponse> {
  const resp = await fetch(`${API_BASE}/jobs/${jobId}`);
  const data = await resp.json();
  if (!resp.ok) {
    const error = data.error || { code: 'INTERNAL', message: 'Failed to fetch job status.' };
    throw error;
  }
  return data;
}

export async function getCachedReport(owner: string, repo: string): Promise<AnalysisReport> {
  const resp = await fetch(`${API_BASE}/report/${owner}/${repo}`);
  const data = await resp.json();
  if (!resp.ok) {
    const error = data.error || { code: 'REPO_NOT_FOUND', message: 'Cached report not found.' };
    throw error;
  }
  return data;
}

export async function streamChat(
  owner: string,
  repo: string,
  sha: string,
  question: string,
  history: { role: string; content: string }[],
  onToken: (text: string) => void,
  onCitations: (citations: ChatCitation[]) => void,
): Promise<void> {
  const resp = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ owner, repo, sha, question, history }),
  });

  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}));
    const error = data.error || { code: 'INTERNAL', message: 'Chat request failed.' };
    throw error;
  }

  const reader = resp.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const payload = line.replace('data: ', '').trim();
        if (payload === '[DONE]') {
          return;
        }
        try {
          const parsed = JSON.parse(payload);
          if (parsed.type === 'token') {
            onToken(parsed.text);
          } else if (parsed.type === 'citations') {
            onCitations(parsed.citations);
          }
        } catch (e) {
          // Non-JSON line or chunk
        }
      }
    }
  }
}
