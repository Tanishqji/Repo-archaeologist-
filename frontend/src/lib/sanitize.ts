import DOMPurify from 'dompurify';

export function sanitizeHtml(dirty: string): string {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'code', 'span', 'p'],
    ALLOWED_ATTR: ['class'],
  });
}

export const ERROR_MESSAGES: Record<string, string> = {
  INVALID_URL: "That doesn't look like a GitHub repository URL. Try 'owner/repo'.",
  REPO_NOT_FOUND: "We couldn't find this repo. It may be private or misspelled. Only public repos are supported.",
  REPO_PRIVATE: "We couldn't find this repo. It may be private or misspelled. Only public repos are supported.",
  REPO_EMPTY: "This repository is empty.",
  REPO_TOO_LARGE: "This repo is very large. We analyzed a partial view.",
  GITHUB_RATE_LIMITED: "GitHub is limiting requests. Try again in a few minutes.",
  LLM_FAILED: "AI analysis is unavailable. Showing detected facts only.",
  TIMEOUT: "This took too long. Try again.",
  RATE_LIMITED: "You've reached the hourly limit. Try again later.",
  INTERNAL: "Something went wrong on our side. Try again.",
};

export function getFriendlyErrorMessage(code?: string, defaultMsg?: string): string {
  if (code && ERROR_MESSAGES[code]) {
    return ERROR_MESSAGES[code];
  }
  return defaultMsg || "An unexpected error occurred. Please try again.";
}

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error('Failed to copy to clipboard', err);
    return false;
  }
}
