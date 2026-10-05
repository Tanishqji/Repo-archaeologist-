export interface RepoInfo {
  owner: string;
  name: string;
  url: string;
  default_branch: string;
  commit_sha: string;
  stars: number;
  license?: string | null;
  last_pushed?: string | null;
}

export interface LanguageInfo {
  name: string;
  percent: number;
}

export interface TechStackItem {
  name: string;
  evidence: string[];
}

export interface TechStackGroup {
  languages: LanguageInfo[];
  frontend: TechStackItem[];
  backend: TechStackItem[];
  database: TechStackItem[];
  devops: TechStackItem[];
  testing: TechStackItem[];
  other: TechStackItem[];
}

export interface ArchitectureComponent {
  name: string;
  role: string;
  evidence: string[];
}

export interface ArchitectureInfo {
  pattern: string;
  components: ArchitectureComponent[];
  data_flow: string;
  mermaid: string;
}

export interface WorkflowStep {
  step: number;
  description: string;
  evidence: string[];
}

export interface ApiEndpoint {
  method: string;
  path: string;
  file: string;
}

export interface KeyFile {
  path: string;
  why_important: string;
}

export interface HowToRun {
  prerequisites: string[];
  steps: string[];
  source: string;
}

export interface Metrics {
  files: number;
  loc: number;
  has_tests: boolean;
  has_ci: boolean;
  has_docker: boolean;
  readme_score: number;
}

export interface Confidence {
  score: number;
  notes: string;
}

export interface AnalysisReport {
  repo: RepoInfo;
  summary: string;
  project_type: string;
  tech_stack: TechStackGroup;
  architecture: ArchitectureInfo;
  workflow: WorkflowStep[];
  api_endpoints: ApiEndpoint[];
  key_files: KeyFile[];
  env_variables: string[];
  how_to_run: HowToRun;
  metrics: Metrics;
  strengths: string[];
  weaknesses: string[];
  risks: string[];
  confidence: Confidence;
  warnings: string[];
  llm_status: 'ok' | 'degraded';
}

export interface JobResponse {
  job_id: string;
  repo_key: string;
  status: 'running' | 'completed' | 'failed';
  stage: 'queued' | 'validating' | 'fetching' | 'scanning' | 'analyzing' | 'diagramming' | 'done' | 'failed';
  progress_pct: number;
  report?: AnalysisReport | null;
  error?: {
    code: string;
    message: string;
    retryable: boolean;
  } | null;
}

export interface ChatCitation {
  file_path: string;
  start_line: number;
  end_line: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: ChatCitation[];
}
